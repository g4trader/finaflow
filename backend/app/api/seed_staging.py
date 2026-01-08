"""
Endpoint temporário para executar seed no STAGING
ATENÇÃO: Remover após execução do seed
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import os
from typing import Dict, Any, Optional
import traceback

from app.services.dependencies import get_current_active_user
from app.models.auth import User

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.post("/run-migration-liquidation")
async def run_migration_liquidation(
    # Temporariamente sem autenticação para poder executar antes do login funcionar
    # TODO: Adicionar autenticação após migration
):
    """
    Executa a migration para adicionar liquidation_account_id à tabela lancamentos_diarios
    ATENÇÃO: Endpoint temporário sem autenticação - remover após uso
    """
    
    from sqlalchemy import text
    from app.database import engine
    
    # Executar migration diretamente via engine (sem usar modelos)
    try:
        # SQL da migration (inline para evitar problemas de arquivo)
        with engine.connect() as conn:
            # 0. Criar tabela liquidation_accounts se não existir
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS liquidation_accounts (
                        id VARCHAR(36) PRIMARY KEY,
                        tenant_id VARCHAR(36) NOT NULL,
                        business_unit_id VARCHAR(36),
                        code VARCHAR(20) NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        account_type VARCHAR(50) NOT NULL,
                        bank_name VARCHAR(100),
                        account_number VARCHAR(50),
                        current_balance NUMERIC(15, 2) DEFAULT 0,
                        initial_balance NUMERIC(15, 2) DEFAULT 0,
                        currency VARCHAR(10) DEFAULT 'BRL',
                        is_active BOOLEAN DEFAULT TRUE,
                        is_default BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_liquidation_accounts_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                        CONSTRAINT fk_liquidation_accounts_bu FOREIGN KEY (business_unit_id) REFERENCES business_units(id)
                    )
                """))
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    raise
            
            # 1. Adicionar coluna se não existir
            try:
                conn.execute(text("""
                    ALTER TABLE lancamentos_diarios 
                    ADD COLUMN IF NOT EXISTS liquidation_account_id VARCHAR(36)
                """))
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    raise
            
            # 2. Adicionar foreign key se não existir (bloco DO completo)
            try:
                conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'fk_lancamentos_diarios_liquidation_account'
                        ) THEN
                            ALTER TABLE lancamentos_diarios
                            ADD CONSTRAINT fk_lancamentos_diarios_liquidation_account
                            FOREIGN KEY (liquidation_account_id) 
                            REFERENCES liquidation_accounts(id);
                        END IF;
                    END $$;
                """))
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    raise
            
            # 3. Criar índice para performance
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_lancamentos_diarios_liquidation_account 
                    ON lancamentos_diarios(liquidation_account_id)
                """))
                conn.commit()
            except Exception as e:
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    raise
            
            # Verificar se a coluna foi criada
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'lancamentos_diarios'
                AND column_name = 'liquidation_account_id'
            """))
            
            if result.fetchone():
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "Migration executada com sucesso",
                        "timestamp": datetime.now().isoformat()
                    }
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": "Coluna não encontrada após migration",
                        "timestamp": datetime.now().isoformat()
                    }
                )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Erro ao executar migration: {str(e)}",
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            }
        )

@router.post("/init-database")
async def init_database():
    """
    Inicializa o banco de dados - cria tabelas e usuário inicial
    ATENÇÃO: Endpoint temporário sem autenticação - remover após uso
    """
    from app.database import SessionLocal, create_tables
    from app.models.auth import User, UserStatus
    from app.services.security import SecurityService
    from uuid import uuid4
    from datetime import datetime
    
    try:
        # Criar tabelas
        print("🔄 Criando tabelas...")
        create_tables()
        print("✅ Tabelas criadas")
        
        db = SessionLocal()
        try:
            from app.models.auth import Tenant, BusinessUnit, UserRole
            
            # Verificar se usuário já existe
            existing_user = db.query(User).filter(User.email == "qa@finaflow.test").first()
            if existing_user:
                return {"message": "Banco já inicializado", "user_id": existing_user.id}
            
            # Criar tenant padrão se não existir
            tenant = db.query(Tenant).filter(Tenant.domain == "finaflow.test").first()
            if not tenant:
                tenant = Tenant(
                    id=str(uuid4()),
                    name="FinaFlow Default",
                    domain="finaflow.test",
                    status="active"
                )
                db.add(tenant)
                db.commit()
                db.refresh(tenant)
                print(f"✅ Tenant criado: {tenant.name}")
            
            # Criar Business Unit padrão se não existir
            bu = db.query(BusinessUnit).filter(
                BusinessUnit.tenant_id == tenant.id,
                BusinessUnit.name == "Matriz"
            ).first()
            if not bu:
                bu = BusinessUnit(
                    id=str(uuid4()),
                    tenant_id=tenant.id,
                    name="Matriz",
                    code="MAT",
                    status="active"
                )
                db.add(bu)
                db.commit()
                db.refresh(bu)
                print(f"✅ Business Unit criada: {bu.name}")
            
            # Criar usuário
            print("👤 Criando usuário qa@finaflow.test...")
            security_service = SecurityService()
            hashed_password = security_service.hash_password("QaFinaflow123!")
            
            user = User(
                id=str(uuid4()),
                tenant_id=tenant.id,
                business_unit_id=bu.id,
                username="qa",
                email="qa@finaflow.test",
                hashed_password=hashed_password,
                first_name="QA",
                last_name="User",
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return {
                "message": "Banco inicializado com sucesso",
                "user_id": user.id,
                "email": user.email,
                "tenant_id": tenant.id,
                "business_unit_id": bu.id
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Erro ao criar usuário: {str(e)}")
        finally:
            db.close()
    except Exception as e:
        import traceback
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao inicializar banco: {str(e)}\n{traceback.format_exc()}"
        )

@router.post("/seed-staging")
async def execute_seed_staging(
    reset_data: Optional[bool] = Body(False, description="Resetar dados antes do seed"),
    cost_debug: Optional[bool] = Body(False, description="Ativar debug de classificação de CUSTO"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Executa o seed do STAGING
    ATENÇÃO: Endpoint temporário - remover após uso
    """
    # Verificar se é super_admin
    user_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    if user_role != "super_admin":
        raise HTTPException(status_code=403, detail="Apenas super_admin pode executar seed")
    
    # Verificar se está em STAGING
    if os.getenv("ENVIRONMENT") != "staging":
        raise HTTPException(status_code=400, detail="Seed só pode ser executado em STAGING")
    
    backend_dir = Path(__file__).parent.parent.parent
    script_path = backend_dir / "scripts" / "seed_from_client_sheet.py"
    excel_file = backend_dir / "data" / "fluxo_caixa_2025.xlsx"
    
    # Diagnóstico
    script_exists = script_path.exists()
    excel_exists = excel_file.exists()
    backend_dir_exists = backend_dir.exists()
    
    # Listar arquivos para diagnóstico
    data_dir = backend_dir / "data"
    data_dir_exists = data_dir.exists()
    data_files = []
    if data_dir_exists:
        try:
            data_files = [f.name for f in data_dir.iterdir() if f.is_file()]
        except:
            pass
    
    if not script_exists:
        raise HTTPException(
            status_code=404, 
            detail=f"Script de seed não encontrado: {script_path}\nBackend dir existe: {backend_dir_exists}\nBackend dir: {backend_dir}"
        )
    
    if not excel_exists:
        raise HTTPException(
            status_code=404, 
            detail=f"Arquivo Excel não encontrado: {excel_file}\nData dir existe: {data_dir_exists}\nArquivos em data/: {data_files}"
        )
    
    try:
        # Verificar caminhos
        script_exists = script_path.exists()
        excel_exists = excel_file.exists()
        
        # Importar e executar seed diretamente
        import importlib.util
        import io
        import contextlib
        
        # Adicionar backend ao path se necessário
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        
        # Capturar stdout/stderr
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        # Usar subprocess de forma mais simples e robusta
        cmd = [
            sys.executable,
            "-m", "scripts.seed_from_client_sheet",
            "--file", str(excel_file.relative_to(backend_dir))
        ]
        
        if reset_data:
            cmd.append("--reset-data")
        
        env = os.environ.copy()
        env["PYTHONPATH"] = str(backend_dir)
        # Permitir COST_DEBUG via parâmetro ou env var
        if cost_debug:
            env["COST_DEBUG"] = "1"
        elif os.getenv("COST_DEBUG"):
            env["COST_DEBUG"] = os.getenv("COST_DEBUG")
        
        try:
            process = subprocess.run(
                cmd,
                cwd=str(backend_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=600,  # 10 minutos
                check=False
            )
            
            output = process.stdout
            success = process.returncode == 0 and ("✅ SEED CONCLUÍDO COM SUCESSO!" in output or "SEED CONCLUÍDO" in output)
            
        except subprocess.TimeoutExpired:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Timeout ao executar seed (mais de 10 minutos)",
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": f"Erro ao executar subprocess: {str(e)}",
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        full_output = output
        
        return JSONResponse(
            status_code=200 if success else 500,
            content={
                "success": success,
                "output": full_output[-3000:],  # Últimas 3000 caracteres
                "timestamp": datetime.now().isoformat(),
                "script_path": str(script_path),
                "excel_path": str(excel_file),
                "script_exists": script_exists,
                "excel_exists": excel_exists
            }
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao executar seed: {str(e)}\n\nDetalhes:\n{error_details}"
        )

@router.post("/clean-duplicate-business-units", summary="Remove Business Units duplicadas (APENAS STAGING)", status_code=200)
async def clean_duplicate_business_units():
    """
    Remove Business Units duplicadas, mantendo apenas uma por tenant (a mais antiga).
    Migra usuários e acessos para a BU mantida.
    ATENÇÃO: Endpoint temporário sem autenticação - remover após uso
    """
    from app.database import SessionLocal
    from app.models.auth import Tenant, BusinessUnit, User, UserBusinessUnitAccess
    from collections import defaultdict
    from datetime import datetime
    
    db = SessionLocal()
    
    try:
        print("🔍 Analisando Business Units duplicadas...")
        
        # Agrupar BUs por tenant_id e name
        all_bus = db.query(BusinessUnit).order_by(BusinessUnit.created_at).all()
        
        # Agrupar por (tenant_id, name)
        groups = defaultdict(list)
        for bu in all_bus:
            key = (bu.tenant_id, bu.name)
            groups[key].append(bu)
        
        # Identificar e remover duplicatas
        deleted_count = 0
        migrated_users = 0
        migrated_accesses = 0
        details = []
        
        for (tenant_id, name), bus in groups.items():
            if len(bus) > 1:
                tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                tenant_name = tenant.name if tenant else "Desconhecido"
                
                # Ordenar por data de criação (mais antiga primeiro)
                bus_sorted = sorted(bus, key=lambda x: x.created_at if x.created_at else datetime.min)
                
                # Manter a primeira (mais antiga)
                keep_bu = bus_sorted[0]
                to_delete = bus_sorted[1:]
                
                detail = {
                    "tenant": tenant_name,
                    "bu_name": name,
                    "kept_bu_id": str(keep_bu.id),
                    "deleted_bu_ids": []
                }
                
                for bu in to_delete:
                    # Verificar e migrar dados relacionados
                    users_count = db.query(User).filter(User.business_unit_id == bu.id).count()
                    access_count = db.query(UserBusinessUnitAccess).filter(
                        UserBusinessUnitAccess.business_unit_id == bu.id
                    ).count()
                    
                    # Migrar lançamentos previstos
                    from app.models.lancamento_previsto import LancamentoPrevisto
                    previstos_count = db.query(LancamentoPrevisto).filter(
                        LancamentoPrevisto.business_unit_id == bu.id
                    ).count()
                    
                    # Migrar lançamentos diários
                    from app.models.lancamento_diario import LancamentoDiario
                    diarios_count = db.query(LancamentoDiario).filter(
                        LancamentoDiario.business_unit_id == bu.id
                    ).count()
                    
                    if users_count > 0:
                        # Migrar usuários
                        db.query(User).filter(User.business_unit_id == bu.id).update({
                            User.business_unit_id: keep_bu.id
                        })
                        migrated_users += users_count
                    
                    if access_count > 0:
                        # Migrar acessos
                        db.query(UserBusinessUnitAccess).filter(
                            UserBusinessUnitAccess.business_unit_id == bu.id
                        ).update({
                            UserBusinessUnitAccess.business_unit_id: keep_bu.id
                        })
                        migrated_accesses += access_count
                    
                    if previstos_count > 0:
                        # Migrar lançamentos previstos
                        db.query(LancamentoPrevisto).filter(
                            LancamentoPrevisto.business_unit_id == bu.id
                        ).update({
                            LancamentoPrevisto.business_unit_id: keep_bu.id
                        })
                    
                    if diarios_count > 0:
                        # Migrar lançamentos diários
                        db.query(LancamentoDiario).filter(
                            LancamentoDiario.business_unit_id == bu.id
                        ).update({
                            LancamentoDiario.business_unit_id: keep_bu.id
                        })
                    
                    # Deletar BU (agora que todos os dados foram migrados)
                    db.delete(bu)
                    deleted_count += 1
                    detail["deleted_bu_ids"].append(str(bu.id))
                
                details.append(detail)
        
        db.commit()
        
        return JSONResponse(content={
            "success": True,
            "message": f"Limpeza concluída! {deleted_count} Business Units removidas.",
            "deleted_count": deleted_count,
            "migrated_users": migrated_users,
            "migrated_accesses": migrated_accesses,
            "details": details
        })
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
    finally:
        db.close()

@router.post("/clean-duplicate-tenants", summary="Remove Tenants duplicados por nome (APENAS STAGING)", status_code=200)
async def clean_duplicate_tenants():
    """
    Remove Tenants duplicados, mantendo apenas um por nome (o que tem mais dados).
    Migra dados relacionados para o tenant mantido.
    ATENÇÃO: Endpoint temporário sem autenticação - remover após uso
    """
    from app.database import SessionLocal
    from app.models.auth import Tenant, BusinessUnit, User, UserBusinessUnitAccess
    from collections import defaultdict
    from sqlalchemy import func
    
    db = SessionLocal()
    
    try:
        print("🔍 Analisando Tenants duplicados...")
        
        # Buscar todos os tenants
        all_tenants = db.query(Tenant).all()
        
        # Agrupar por nome
        groups = defaultdict(list)
        for tenant in all_tenants:
            groups[tenant.name].append(tenant)
        
        # Identificar e remover duplicatas
        deleted_count = 0
        details = []
        
        for tenant_name, tenants in groups.items():
            if len(tenants) > 1:
                print(f"\n📋 Encontrados {len(tenants)} tenants com nome '{tenant_name}'")
                
                # Para cada tenant, contar quantos dados tem
                tenant_scores = []
                for tenant in tenants:
                    # Contar BUs
                    bu_count = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant.id).count()
                    
                    # Contar usuários
                    user_count = db.query(User).filter(User.tenant_id == tenant.id).count()
                    
                    # Contar lançamentos
                    from app.models.lancamento_previsto import LancamentoPrevisto
                    from app.models.lancamento_diario import LancamentoDiario
                    previstos_count = db.query(LancamentoPrevisto).filter(
                        LancamentoPrevisto.tenant_id == tenant.id
                    ).count()
                    diarios_count = db.query(LancamentoDiario).filter(
                        LancamentoDiario.tenant_id == tenant.id
                    ).count()
                    
                    total_data = bu_count + user_count + previstos_count + diarios_count
                    tenant_scores.append((tenant, total_data))
                    print(f"   Tenant {tenant.id[:8]}...: {total_data} registros (BUs: {bu_count}, Users: {user_count}, Previstos: {previstos_count}, Diários: {diarios_count})")
                
                # Ordenar por quantidade de dados (mais dados = manter)
                tenant_scores.sort(key=lambda x: x[1], reverse=True)
                
                # Manter o que tem mais dados
                keep_tenant = tenant_scores[0][0]
                to_delete = [t[0] for t in tenant_scores[1:]]
                
                print(f"   ✅ Mantendo tenant: {keep_tenant.id[:8]}... ({tenant_scores[0][1]} registros)")
                print(f"   ❌ Removendo {len(to_delete)} tenant(s) duplicado(s)")
                
                detail = {
                    "tenant_name": tenant_name,
                    "kept_tenant_id": str(keep_tenant.id),
                    "deleted_tenant_ids": []
                }
                
                for tenant in to_delete:
                    # Verificar se tem dados importantes antes de deletar
                    user_count = db.query(User).filter(User.tenant_id == tenant.id).count()
                    
                    # Contar lançamentos do tenant
                    from app.models.lancamento_previsto import LancamentoPrevisto
                    from app.models.lancamento_diario import LancamentoDiario
                    previstos_count = db.query(LancamentoPrevisto).filter(
                        LancamentoPrevisto.tenant_id == tenant.id
                    ).count()
                    diarios_count = db.query(LancamentoDiario).filter(
                        LancamentoDiario.tenant_id == tenant.id
                    ).count()
                    
                    # Se tem lançamentos ou usuários, não deletar
                    if previstos_count > 0 or diarios_count > 0 or user_count > 0:
                        print(f"   ⚠️  Tenant {tenant.id[:8]}... tem dados (Users: {user_count}, Previstos: {previstos_count}, Diários: {diarios_count}) - pulando remoção")
                        continue
                    
                    # Deletar BUs do tenant (só se não tiverem dados)
                    bus_to_delete = db.query(BusinessUnit).filter(BusinessUnit.tenant_id == tenant.id).all()
                    for bu in bus_to_delete:
                        # Verificar se BU tem dados
                        bu_previstos = db.query(LancamentoPrevisto).filter(
                            LancamentoPrevisto.business_unit_id == bu.id
                        ).count()
                        bu_diarios = db.query(LancamentoDiario).filter(
                            LancamentoDiario.business_unit_id == bu.id
                        ).count()
                        bu_users = db.query(User).filter(User.business_unit_id == bu.id).count()
                        
                        if bu_previstos > 0 or bu_diarios > 0 or bu_users > 0:
                            print(f"   ⚠️  BU {bu.id[:8]}... tem dados - pulando remoção")
                            continue
                        
                        db.delete(bu)
                    
                    # Deletar tenant
                    db.delete(tenant)
                    deleted_count += 1
                    detail["deleted_tenant_ids"].append(str(tenant.id))
                    print(f"   ✅ Tenant {tenant.id[:8]}... removido")
                
                if detail["deleted_tenant_ids"]:
                    details.append(detail)
        
        db.commit()
        
        return JSONResponse(content={
            "success": True,
            "message": f"Limpeza concluída! {deleted_count} Tenants removidos.",
            "deleted_count": deleted_count,
            "details": details
        })
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
    finally:
        db.close()

@router.post("/test-seed-direct", summary="Testa seed diretamente com logging detalhado (APENAS STAGING)", status_code=200)
async def test_seed_direct():
    """
    Testa o seed diretamente para diagnosticar problemas de importação.
    Retorna logs detalhados de cada etapa.
    ATENÇÃO: Endpoint temporário sem autenticação - remover após uso
    """
    import io
    import sys
    from contextlib import redirect_stdout, redirect_stderr
    
    TENANT_ID = 'ed987f9e-8a32-440e-a7fc-ffeb56368d7c'
    BU_ID = 'b365bbaa-7796-47a8-a8e3-a0812c694c85'
    SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ/edit?gid=1158090564#gid=1158090564'
    
    logs = []
    
    def log_capture(msg):
        logs.append(msg)
        print(msg, flush=True)
    
    try:
        from app.database import SessionLocal
        from app.models.auth import Tenant, BusinessUnit, User
        from scripts.seed_from_client_sheet import (
            seed_plano_contas,
            seed_lancamentos_previstos,
            seed_lancamentos_diarios,
            logger
        )
        import requests
        import re
        from pathlib import Path
        
        log_capture("="*80)
        log_capture("🧪 TESTE DIRETO DO SEED")
        log_capture("="*80)
        
        # Baixar planilha
        log_capture("\n📥 Baixando planilha...")
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9_-]+)', SPREADSHEET_URL)
        if match:
            sheet_id = match.group(1)
            export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        else:
            export_url = SPREADSHEET_URL.replace("/edit", "/export?format=xlsx")
        
        response = requests.get(export_url, timeout=60)
        response.raise_for_status()
        
        data_dir = Path(__file__).parent.parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        excel_file = data_dir / "test_onboarding_direct.xlsx"
        
        with open(excel_file, "wb") as f:
            f.write(response.content)
        
        log_capture(f"✅ Planilha salva: {excel_file} ({len(response.content)} bytes)")
        
        # Conectar ao banco
        db = SessionLocal()
        try:
            # Buscar tenant, BU e user
            tenant = db.query(Tenant).filter(Tenant.id == TENANT_ID).first()
            if not tenant:
                return JSONResponse(status_code=404, content={"error": f"Tenant {TENANT_ID} não encontrado", "logs": logs})
            
            business_unit = db.query(BusinessUnit).filter(BusinessUnit.id == BU_ID).first()
            if not business_unit:
                return JSONResponse(status_code=404, content={"error": f"Business Unit {BU_ID} não encontrado", "logs": logs})
            
            user = db.query(User).filter(User.email == "qa@finaflow.test").first()
            if not user:
                return JSONResponse(status_code=404, content={"error": "Usuário qa@finaflow.test não encontrado", "logs": logs})
            
            log_capture(f"\n✅ Tenant: {tenant.name}")
            log_capture(f"✅ Business Unit: {business_unit.name}")
            log_capture(f"✅ User: {user.email}")
            
            # Resetar stats
            logger.stats = {
                'grupos_criados': 0, 'grupos_existentes': 0,
                'subgrupos_criados': 0, 'subgrupos_existentes': 0,
                'contas_criadas': 0, 'contas_existentes': 0,
                'lancamentos_diarios_criados': 0, 'lancamentos_diarios_existentes': 0,
                'lancamentos_previstos_criados': 0, 'lancamentos_previstos_existentes': 0,
                'linhas_ignoradas': 0, 'erros': []
            }
            
            # 1. Plano de contas
            log_capture("\n1️⃣ Importando Plano de Contas...")
            grupos_map, subgrupos_map, contas_map = seed_plano_contas(db, tenant, excel_file)
            log_capture(f"   ✅ Grupos: {len(grupos_map)}, Subgrupos: {len(subgrupos_map)}, Contas: {len(contas_map)}")
            
            # 2. Lançamentos previstos
            log_capture("\n2️⃣ Importando Lançamentos Previstos...")
            previstos_before = logger.stats['lancamentos_previstos_criados']
            seed_lancamentos_previstos(db, tenant, business_unit, user, grupos_map, subgrupos_map, contas_map, excel_file)
            db.commit()
            previstos_after = logger.stats['lancamentos_previstos_criados']
            previstos_count = previstos_after - previstos_before
            log_capture(f"   ✅ Lançamentos Previstos criados: {previstos_count}")
            log_capture(f"   📊 Erros: {len(logger.stats['erros'])}")
            if logger.stats['erros']:
                for err in logger.stats['erros'][:5]:
                    log_capture(f"      - {str(err)[:200]}")
            
            # 3. Lançamentos diários
            log_capture("\n3️⃣ Importando Lançamentos Diários...")
            diarios_before = logger.stats['lancamentos_diarios_criados']
            seed_lancamentos_diarios(db, tenant, business_unit, user, grupos_map, subgrupos_map, contas_map, excel_file)
            db.commit()
            diarios_after = logger.stats['lancamentos_diarios_criados']
            diarios_count = diarios_after - diarios_before
            log_capture(f"   ✅ Lançamentos Diários criados: {diarios_count}")
            log_capture(f"   📊 Linhas ignoradas: {logger.stats['linhas_ignoradas']}")
            log_capture(f"   📊 Erros: {len(logger.stats['erros'])}")
            if logger.stats['erros']:
                for err in logger.stats['erros'][:10]:
                    log_capture(f"      - {str(err)[:300]}")
            
            # Verificar no banco
            from app.models.lancamento_diario import LancamentoDiario
            from app.models.lancamento_previsto import LancamentoPrevisto
            
            db_diarios = db.query(LancamentoDiario).filter(
                LancamentoDiario.tenant_id == tenant.id,
                LancamentoDiario.business_unit_id == business_unit.id
            ).count()
            
            db_previstos = db.query(LancamentoPrevisto).filter(
                LancamentoPrevisto.tenant_id == tenant.id,
                LancamentoPrevisto.business_unit_id == business_unit.id
            ).count()

            # Contagem apenas de registros ativos (as APIs filtram is_active=True)
            db_diarios_active = db.query(LancamentoDiario).filter(
                LancamentoDiario.tenant_id == tenant.id,
                LancamentoDiario.business_unit_id == business_unit.id,
                LancamentoDiario.is_active.is_(True),
            ).count()

            db_previstos_active = db.query(LancamentoPrevisto).filter(
                LancamentoPrevisto.tenant_id == tenant.id,
                LancamentoPrevisto.business_unit_id == business_unit.id,
                LancamentoPrevisto.is_active.is_(True),
            ).count()

            # Amostra rápida para diagnosticar is_active
            sample_previsto = (
                db.query(LancamentoPrevisto)
                .filter(
                    LancamentoPrevisto.tenant_id == tenant.id,
                    LancamentoPrevisto.business_unit_id == business_unit.id,
                )
                .order_by(LancamentoPrevisto.created_at.desc())
                .first()
            )
            
            log_capture("\n" + "="*80)
            log_capture("📊 RESULTADO FINAL")
            log_capture("="*80)
            log_capture(f"Lançamentos Diários no banco: {db_diarios}")
            log_capture(f"Lançamentos Previstos no banco: {db_previstos}")
            log_capture(f"Lançamentos Diários ATIVOS: {db_diarios_active}")
            log_capture(f"Lançamentos Previstos ATIVOS: {db_previstos_active}")
            log_capture(f"Stats: {logger.stats}")
            log_capture("="*80)
            
            return JSONResponse(content={
                "success": db_diarios > 0 or db_previstos > 0,
                "diarios_banco": db_diarios,
                "previstos_banco": db_previstos,
                "diarios_ativos": db_diarios_active,
                "previstos_ativos": db_previstos_active,
                "sample_previsto": {
                    "id": sample_previsto.id,
                    "is_active": bool(sample_previsto.is_active),
                    "tenant_id": sample_previsto.tenant_id,
                    "business_unit_id": sample_previsto.business_unit_id,
                    "data_prevista": sample_previsto.data_prevista.isoformat() if getattr(sample_previsto, "data_prevista", None) else None,
                } if sample_previsto else None,
                "diarios_criados": diarios_count,
                "previstos_criados": previstos_count,
                "stats": logger.stats,
                "logs": logs
            })
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            log_capture(f"\n❌ Erro: {e}")
            log_capture(error_trace)
            return JSONResponse(
                status_code=500,
                content={"error": str(e), "traceback": error_trace, "logs": logs}
            )
        finally:
            db.close()
            
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc(), "logs": logs}
        )

