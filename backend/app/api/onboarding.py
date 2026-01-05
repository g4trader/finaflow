"""
API de Onboarding para novas empresas
Permite importação de dados de planilha Excel/Google Sheets em etapas
"""

from fastapi import APIRouter, HTTPException, Depends, Body, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
import os
import sys
from pathlib import Path
import requests
import tempfile
import json

from app.services.dependencies import get_current_active_user
from app.models.auth import User, Tenant, BusinessUnit
from app.database import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import and_

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])

# Adicionar backend ao path para importar scripts (apenas quando necessário)
backend_path = Path(__file__).parent.parent.parent
# Não adicionar ao sys.path no nível do módulo - fazer apenas quando necessário

class SpreadsheetUrlRequest(BaseModel):
    url: HttpUrl
    tenant_id: str
    business_unit_id: str

class ImportRequest(BaseModel):
    tenant_id: str
    business_unit_id: str
    spreadsheet_url: HttpUrl
    reset_data: bool = False

class ClearDataRequest(BaseModel):
    tenant_id: str
    business_unit_id: str
    year: Optional[int] = None

class OnboardingStatus(BaseModel):
    tenant_id: str
    business_unit_id: str
    status: str  # not_started, validating, importing_plan, importing_transactions, reconciling, completed, error
    current_step: Optional[str] = None
    progress: int = 0  # 0-100
    message: Optional[str] = None
    errors: List[str] = []
    stats: Optional[Dict[str, Any]] = None

# Armazenamento temporário do status (em produção, usar Redis ou banco)
onboarding_status: Dict[str, OnboardingStatus] = {}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/clear-data")
async def clear_data(
    request: ClearDataRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Limpa dados financeiros de uma empresa/BU (mantém estrutura de contas se necessário)
    """
    try:
        # Verificar se tenant e BU existem
        tenant = db.query(Tenant).filter(Tenant.id == request.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant não encontrado")
        
        business_unit = db.query(BusinessUnit).filter(
            BusinessUnit.id == request.business_unit_id,
            BusinessUnit.tenant_id == request.tenant_id
        ).first()
        if not business_unit:
            raise HTTPException(status_code=404, detail="Business Unit não encontrada")
        
        from app.models.lancamento_diario import LancamentoDiario
        from app.models.lancamento_previsto import LancamentoPrevisto
        from datetime import date
        
        deleted_counts = {
            "lancamentos_diarios": 0,
            "lancamentos_previstos": 0
        }
        
        # Deletar lançamentos diários
        if request.year:
            start_date = date(request.year, 1, 1)
            end_date = date(request.year, 12, 31)
            deleted_diarios = db.query(LancamentoDiario).filter(
                and_(
                    LancamentoDiario.tenant_id == request.tenant_id,
                    LancamentoDiario.business_unit_id == request.business_unit_id,
                    LancamentoDiario.data_movimentacao >= start_date,
                    LancamentoDiario.data_movimentacao <= end_date
                )
            ).delete(synchronize_session=False)
            deleted_counts["lancamentos_diarios"] = deleted_diarios
            
            deleted_previstos = db.query(LancamentoPrevisto).filter(
                and_(
                    LancamentoPrevisto.tenant_id == request.tenant_id,
                    LancamentoPrevisto.business_unit_id == request.business_unit_id,
                    LancamentoPrevisto.data_prevista >= start_date,
                    LancamentoPrevisto.data_prevista <= end_date
                )
            ).delete(synchronize_session=False)
            deleted_counts["lancamentos_previstos"] = deleted_previstos
        else:
            # Deletar todos os lançamentos
            deleted_diarios = db.query(LancamentoDiario).filter(
                and_(
                    LancamentoDiario.tenant_id == request.tenant_id,
                    LancamentoDiario.business_unit_id == request.business_unit_id
                )
            ).delete(synchronize_session=False)
            deleted_counts["lancamentos_diarios"] = deleted_diarios
            
            deleted_previstos = db.query(LancamentoPrevisto).filter(
                and_(
                    LancamentoPrevisto.tenant_id == request.tenant_id,
                    LancamentoPrevisto.business_unit_id == request.business_unit_id
                )
            ).delete(synchronize_session=False)
            deleted_counts["lancamentos_previstos"] = deleted_previstos
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Dados limpos com sucesso",
            "deleted": deleted_counts,
            "year": request.year
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao limpar dados: {str(e)}")

@router.post("/validate-spreadsheet")
async def validate_spreadsheet(
    request: SpreadsheetUrlRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Valida se a URL da planilha é acessível e contém as abas necessárias
    """
    try:
        # Verificar se tenant e BU existem
        tenant = db.query(Tenant).filter(Tenant.id == request.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant não encontrado")
        
        business_unit = db.query(BusinessUnit).filter(
            BusinessUnit.id == request.business_unit_id,
            BusinessUnit.tenant_id == request.tenant_id
        ).first()
        if not business_unit:
            raise HTTPException(status_code=404, detail="Business Unit não encontrada")
        
        # Baixar planilha temporariamente
        try:
            # Converter Google Sheets URL para formato de download
            spreadsheet_url = str(request.url)
            if "docs.google.com/spreadsheets" in spreadsheet_url:
                # Converter para formato de exportação Excel
                if "/edit" in spreadsheet_url:
                    spreadsheet_url = spreadsheet_url.replace("/edit", "/export?format=xlsx")
                elif "/view" in spreadsheet_url:
                    spreadsheet_url = spreadsheet_url.replace("/view", "/export?format=xlsx")
                else:
                    # Adicionar /export?format=xlsx se não tiver
                    if "export" not in spreadsheet_url:
                        spreadsheet_url = spreadsheet_url.rstrip("/") + "/export?format=xlsx"
            
            response = requests.get(spreadsheet_url, timeout=30)
            response.raise_for_status()
            
            # Salvar temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                tmp_file.write(response.content)
                tmp_file_path = tmp_file.name
            
            # Validar estrutura da planilha
            import pandas as pd
            
            try:
                excel_file = pd.ExcelFile(tmp_file_path)
                required_sheets = ["Plano de contas", "Lançamento Diário", "Lançamentos Previstos"]
                available_sheets = excel_file.sheet_names
                
                # Verificar variações de nomes
                found_sheets = {}
                for req_sheet in required_sheets:
                    for avail_sheet in available_sheets:
                        if req_sheet.lower() in avail_sheet.lower() or avail_sheet.lower() in req_sheet.lower():
                            found_sheets[req_sheet] = avail_sheet
                            break
                
                missing_sheets = [s for s in required_sheets if s not in found_sheets]
                
                # Limpar arquivo temporário
                os.unlink(tmp_file_path)
                
                if missing_sheets:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "valid": False,
                            "error": f"Abas faltantes: {', '.join(missing_sheets)}",
                            "available_sheets": available_sheets,
                            "found_sheets": found_sheets
                        }
                    )
                
                return {
                    "valid": True,
                    "message": "Planilha válida",
                    "available_sheets": available_sheets,
                    "found_sheets": found_sheets
                }
                
            except Exception as e:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                raise HTTPException(status_code=400, detail=f"Erro ao validar planilha: {str(e)}")
                
        except requests.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Erro ao acessar planilha: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao validar planilha: {str(e)}")

@router.post("/import")
async def import_data(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Inicia processo de importação de dados em etapas
    """
    try:
        # Verificar se tenant e BU existem
        tenant = db.query(Tenant).filter(Tenant.id == request.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant não encontrado")
        
        business_unit = db.query(BusinessUnit).filter(
            BusinessUnit.id == request.business_unit_id,
            BusinessUnit.tenant_id == request.tenant_id
        ).first()
        
        # Se não encontrou BU, criar automaticamente
        if not business_unit:
            # Verificar se o business_unit_id é igual ao tenant_id (indicando que precisa criar)
            if request.business_unit_id == request.tenant_id:
                # Criar BU padrão
                from uuid import uuid4
                business_unit = BusinessUnit(
                    id=str(uuid4()),
                    tenant_id=request.tenant_id,
                    name="Matriz",
                    code="MAT",
                    status="active"
                )
                db.add(business_unit)
                db.commit()
                db.refresh(business_unit)
                # Atualizar request com o ID real da BU
                request.business_unit_id = str(business_unit.id)
            else:
                # Tentar buscar qualquer BU do tenant
                business_unit = db.query(BusinessUnit).filter(
                    BusinessUnit.tenant_id == request.tenant_id
                ).first()
                
                if not business_unit:
                    # Criar BU padrão
                    from uuid import uuid4
                    business_unit = BusinessUnit(
                        id=str(uuid4()),
                        tenant_id=request.tenant_id,
                        name="Matriz",
                        code="MAT",
                        status="active"
                    )
                    db.add(business_unit)
                    db.commit()
                    db.refresh(business_unit)
                    # Atualizar request com o ID real da BU
                    request.business_unit_id = str(business_unit.id)
                else:
                    # Usar a BU encontrada
                    request.business_unit_id = str(business_unit.id)
        
        status_key = f"{request.tenant_id}_{request.business_unit_id}"
        
        # Inicializar status
        onboarding_status[status_key] = OnboardingStatus(
            tenant_id=request.tenant_id,
            business_unit_id=request.business_unit_id,
            status="validating",
            current_step="Validando planilha",
            progress=0,
            message="Iniciando validação da planilha..."
        )
        
        # Executar importação em background
        background_tasks.add_task(
            execute_import,
            request.tenant_id,
            request.business_unit_id,
            str(request.spreadsheet_url),
            request.reset_data,
            current_user.id
        )
        
        return {
            "success": True,
            "message": "Importação iniciada",
            "status_key": status_key
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar importação: {str(e)}")

@router.get("/status/{tenant_id}/{business_unit_id}")
async def get_onboarding_status(
    tenant_id: str,
    business_unit_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retorna status atual do onboarding
    """
    status_key = f"{tenant_id}_{business_unit_id}"
    status = onboarding_status.get(status_key)
    
    if not status:
        return {
            "status": "not_started",
            "progress": 0,
            "message": "Onboarding não iniciado"
        }
    
    return status.dict()

@router.get("/reconciliation/{tenant_id}/{business_unit_id}")
async def get_reconciliation(
    tenant_id: str,
    business_unit_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retorna relatório de conciliação entre planilha e sistema
    """
    try:
        # Buscar última planilha importada para este tenant/BU
        data_dir = backend_path / "data"
        excel_files = sorted(
            [f for f in data_dir.glob(f"onboarding_{tenant_id}_{business_unit_id}_*.xlsx")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if not excel_files:
            return {
                "tenant_id": tenant_id,
                "business_unit_id": business_unit_id,
                "reconciliation_date": datetime.now().isoformat(),
                "status": "no_data",
                "message": "Nenhuma planilha importada encontrada"
            }
        
        excel_file_path = excel_files[0]
        
        # Importar funções de conciliação
        from scripts.reconcile_fluxo_caixa import extract_fluxo_caixa_totals
        import requests
        import os
        
        # Extrair totais da planilha
        excel_totals_dict = extract_fluxo_caixa_totals(excel_file_path)
        
        # Converter para formato esperado
        excel_totals = {
            "receita_total": sum(float(excel_totals_dict.get(m, {}).get("receita", 0)) for m in range(1, 13)),
            "despesa_total": sum(float(excel_totals_dict.get(m, {}).get("despesa", 0)) for m in range(1, 13)),
            "custo_total": sum(float(excel_totals_dict.get(m, {}).get("custo", 0)) for m in range(1, 13)),
            "saldo_total": sum(float(excel_totals_dict.get(m, {}).get("saldo", 0)) for m in range(1, 13)),
            "mensal": {
                str(m): {
                    "receita": float(excel_totals_dict.get(m, {}).get("receita", 0)),
                    "despesa": float(excel_totals_dict.get(m, {}).get("despesa", 0)),
                    "custo": float(excel_totals_dict.get(m, {}).get("custo", 0)),
                    "saldo": float(excel_totals_dict.get(m, {}).get("saldo", 0))
                }
                for m in range(1, 13)
            }
        }
        
        # Buscar totais da API
        BACKEND_URL = os.getenv("BACKEND_URL", "https://finaflow-backend-staging-556803510516.us-central1.run.app")
        QA_USERNAME = os.getenv("QA_USERNAME", "qa@finaflow.test")
        QA_PASSWORD = os.getenv("QA_PASSWORD", "QaFinaflow123!")
        
        login_resp = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"username": QA_USERNAME, "password": QA_PASSWORD},
            timeout=30
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        api_resp = requests.get(
            f"{BACKEND_URL}/api/v1/financial/annual-summary?year=2025",
            headers=headers,
            timeout=30
        )
        api_data = api_resp.json()
        
        # Calcular diferenças
        totals = {
            "revenue": {
                "excel": float(excel_totals.get("receita_total", 0)),
                "system": float(api_data.get("totals", {}).get("revenue", 0)),
                "diff": float(excel_totals.get("receita_total", 0)) - float(api_data.get("totals", {}).get("revenue", 0))
            },
            "expense": {
                "excel": float(excel_totals.get("despesa_total", 0)),
                "system": float(api_data.get("totals", {}).get("expense", 0)),
                "diff": float(excel_totals.get("despesa_total", 0)) - float(api_data.get("totals", {}).get("expense", 0))
            },
            "cost": {
                "excel": float(excel_totals.get("custo_total", 0)),
                "system": float(api_data.get("totals", {}).get("cost", 0)),
                "diff": float(excel_totals.get("custo_total", 0)) - float(api_data.get("totals", {}).get("cost", 0))
            },
            "balance": {
                "excel": float(excel_totals.get("saldo_total", 0)),
                "system": float(api_data.get("totals", {}).get("balance", 0)),
                "diff": float(excel_totals.get("saldo_total", 0)) - float(api_data.get("totals", {}).get("balance", 0))
            }
        }
        
        # Calcular mensais
        monthly = []
        for month in range(1, 13):
            month_data: Dict[str, Any] = {"month": month}
            
            excel_month = excel_totals.get("mensal", {}).get(str(month), {})
            api_month = api_data.get("monthly", {}).get(str(month), {})
            
            if excel_month.get("receita") is not None:
                month_data["revenue"] = {
                    "excel": float(excel_month.get("receita", 0)),
                    "system": float(api_month.get("revenue", 0)),
                    "diff": float(excel_month.get("receita", 0)) - float(api_month.get("revenue", 0))
                }
            
            if excel_month.get("despesa") is not None:
                month_data["expense"] = {
                    "excel": float(excel_month.get("despesa", 0)),
                    "system": float(api_month.get("expense", 0)),
                    "diff": float(excel_month.get("despesa", 0)) - float(api_month.get("expense", 0))
                }
            
            if excel_month.get("custo") is not None:
                month_data["cost"] = {
                    "excel": float(excel_month.get("custo", 0)),
                    "system": float(api_month.get("cost", 0)),
                    "diff": float(excel_month.get("custo", 0)) - float(api_month.get("cost", 0))
                }
            
            if excel_month.get("saldo") is not None:
                month_data["balance"] = {
                    "excel": float(excel_month.get("saldo", 0)),
                    "system": float(api_month.get("balance", 0)),
                    "diff": float(excel_month.get("saldo", 0)) - float(api_month.get("balance", 0))
                }
            
            monthly.append(month_data)
        
        # Verificar se está 100% conciliado
        all_reconciled = all(
            abs(t["diff"]) < 0.01
            for t in totals.values()
        ) and all(
            all(abs(v.get("diff", 0)) < 0.01 for v in m.values() if isinstance(v, dict) and "diff" in v)
            for m in monthly
        )
        
        return {
            "tenant_id": tenant_id,
            "business_unit_id": business_unit_id,
            "reconciliation_date": datetime.now().isoformat(),
            "status": "completed" if all_reconciled else "differences_found",
            "totals": totals,
            "monthly": monthly,
            "all_reconciled": all_reconciled
        }
        
    except Exception as e:
        import traceback
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar conciliação: {str(e)}\n{traceback.format_exc()}"
        )

def execute_import(
    tenant_id: str,
    business_unit_id: str,
    spreadsheet_url: str,
    reset_data: bool,
    user_id: str
):
    """
    Executa importação em etapas (background task)
    """
    status_key = f"{tenant_id}_{business_unit_id}"
    
    try:
        # Etapa 1: Baixar planilha
        onboarding_status[status_key].status = "validating"
        onboarding_status[status_key].current_step = "Baixando planilha"
        onboarding_status[status_key].progress = 10
        onboarding_status[status_key].message = "Baixando planilha da URL..."
        
        # Converter Google Sheets URL para formato de download
        if "docs.google.com/spreadsheets" in spreadsheet_url:
            # Extrair o ID da planilha
            import re
            match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', spreadsheet_url)
            if match:
                sheet_id = match.group(1)
                # Criar URL de exportação limpa
                spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
            else:
                # Fallback: tentar substituir edit/view
                if "/edit" in spreadsheet_url:
                    # Remover tudo após /edit incluindo #gid
                    base_url = spreadsheet_url.split("/edit")[0]
                    spreadsheet_url = f"{base_url}/export?format=xlsx"
                elif "/view" in spreadsheet_url:
                    base_url = spreadsheet_url.split("/view")[0]
                    spreadsheet_url = f"{base_url}/export?format=xlsx"
                else:
                    if "export" not in spreadsheet_url:
                        # Remover fragmentos (#gid=...) e adicionar export
                        clean_url = spreadsheet_url.split("#")[0].split("?")[0].rstrip("/")
                        spreadsheet_url = f"{clean_url}/export?format=xlsx"
        
        response = requests.get(spreadsheet_url, timeout=60)
        response.raise_for_status()
        
        # Salvar planilha temporariamente
        data_dir = backend_path / "data"
        data_dir.mkdir(exist_ok=True)
        excel_file_path = data_dir / f"onboarding_{tenant_id}_{business_unit_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with open(excel_file_path, "wb") as f:
            f.write(response.content)
        
        # Etapa 2: Importar Plano de Contas
        onboarding_status[status_key].status = "importing_plan"
        onboarding_status[status_key].current_step = "Importando Plano de Contas"
        onboarding_status[status_key].progress = 30
        onboarding_status[status_key].message = "Importando estrutura de contas..."
        
        # Executar seed do plano de contas
        from scripts.seed_from_client_sheet import seed_plano_contas
        from app.database import SessionLocal
        from app.models.auth import Tenant, BusinessUnit
        from app.models.lancamento_diario import LancamentoDiario
        from app.models.lancamento_previsto import LancamentoPrevisto
        
        db = SessionLocal()
        try:
            # Buscar tenant, BU e user existentes
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                raise Exception(f"Tenant {tenant_id} não encontrado")
            
            business_unit = db.query(BusinessUnit).filter(
                BusinessUnit.id == business_unit_id,
                BusinessUnit.tenant_id == tenant_id
            ).first()
            if not business_unit:
                raise Exception(f"Business Unit {business_unit_id} não encontrada")
            
            grupos_map, subgrupos_map, contas_map = seed_plano_contas(db, tenant, excel_file_path)
            
            onboarding_status[status_key].progress = 50
            onboarding_status[status_key].message = f"Plano de contas importado: {len(contas_map)} contas"
            
        except Exception as e:
            onboarding_status[status_key].status = "error"
            onboarding_status[status_key].message = f"Erro ao importar plano de contas: {str(e)}"
            onboarding_status[status_key].errors.append(str(e))
            return
        finally:
            db.close()
        
        # Etapa 3: Importar Lançamentos
        onboarding_status[status_key].status = "importing_transactions"
        onboarding_status[status_key].current_step = "Importando Lançamentos Financeiros"
        onboarding_status[status_key].progress = 60
        onboarding_status[status_key].message = "Importando lançamentos diários e previstos..."
        
        # Executar seed diretamente (sem subprocess para evitar timeout)
        # Adicionar backend ao path para importar scripts
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))
        from scripts.seed_from_client_sheet import seed_lancamentos_previstos, seed_lancamentos_diarios
        
        db = SessionLocal()
        try:
            # Buscar tenant e BU novamente
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                raise Exception(f"Tenant {tenant_id} não encontrado")
            
            business_unit = db.query(BusinessUnit).filter(
                BusinessUnit.id == business_unit_id,
                BusinessUnit.tenant_id == tenant_id
            ).first()
            if not business_unit:
                raise Exception(f"Business Unit {business_unit_id} não encontrada")
            
            # Resetar dados se solicitado
            if reset_data:
                from datetime import date
                from sqlalchemy import and_
                
                deleted_diarios = db.query(LancamentoDiario).filter(
                    and_(
                        LancamentoDiario.tenant_id == tenant.id,
                        LancamentoDiario.data_movimentacao >= date(2025, 1, 1),
                        LancamentoDiario.data_movimentacao <= date(2025, 12, 31)
                    )
                ).delete(synchronize_session=False)
                
                deleted_prev = db.query(LancamentoPrevisto).filter(
                    and_(
                        LancamentoPrevisto.tenant_id == tenant.id,
                        LancamentoPrevisto.data_prevista >= date(2025, 1, 1),
                        LancamentoPrevisto.data_prevista <= date(2025, 12, 31)
                    )
                ).delete(synchronize_session=False)
                
                db.commit()
                onboarding_status[status_key].message = f"Dados resetados: {deleted_diarios} diários, {deleted_prev} previstos"
            
            # Importar lançamentos previstos
            onboarding_status[status_key].progress = 65
            onboarding_status[status_key].message = "Importando lançamentos previstos..."
            seed_lancamentos_previstos(db, tenant, business_unit, excel_file_path, grupos_map, subgrupos_map, contas_map)
            
            # Importar lançamentos diários
            onboarding_status[status_key].progress = 80
            onboarding_status[status_key].message = "Importando lançamentos diários..."
            seed_lancamentos_diarios(db, tenant, business_unit, excel_file_path, grupos_map, subgrupos_map, contas_map)
            
            db.commit()
            onboarding_status[status_key].progress = 90
            onboarding_status[status_key].message = "Lançamentos importados com sucesso"
                
        except Exception as e:
            db.rollback()
            onboarding_status[status_key].status = "error"
            onboarding_status[status_key].message = f"Erro ao importar lançamentos: {str(e)}"
            onboarding_status[status_key].errors.append(str(e))
            import traceback
            onboarding_status[status_key].errors.append(traceback.format_exc())
            return
        finally:
            db.close()
        
        # Etapa 4: Conciliação
        onboarding_status[status_key].status = "reconciling"
        onboarding_status[status_key].current_step = "Conciliação"
        onboarding_status[status_key].progress = 95
        onboarding_status[status_key].message = "Gerando relatório de conciliação..."
        
        # TODO: Executar conciliação
        
        # Finalizar
        onboarding_status[status_key].status = "completed"
        onboarding_status[status_key].current_step = "Concluído"
        onboarding_status[status_key].progress = 100
        onboarding_status[status_key].message = "Onboarding concluído com sucesso!"
        onboarding_status[status_key].stats = {
            "contas_importadas": len(contas_map),
            "grupos_importados": len(grupos_map),
            "subgrupos_importados": len(subgrupos_map)
        }
        
    except Exception as e:
        onboarding_status[status_key].status = "error"
        onboarding_status[status_key].message = f"Erro durante onboarding: {str(e)}"
        onboarding_status[status_key].errors.append(str(e))
