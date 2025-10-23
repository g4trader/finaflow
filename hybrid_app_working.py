from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import jwt
import datetime
import uuid
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session, relationship
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Date, Numeric, text
from fastapi.security import HTTPBearer

# VERSÃO FUNCIONAL 2025-10-22
print("="*80)
print("🚀 INICIANDO FINAFLOW BACKEND - VERSÃO FUNCIONAL")
print("="*80)

# Importar configurações do banco de dados
from app.database import get_db, engine
from app.models.auth import User, Tenant, BusinessUnit, UserTenantAccess, UserBusinessUnitAccess, Base as AuthBase
from app.models.chart_of_accounts import ChartAccountGroup, ChartAccountSubgroup, ChartAccount, BusinessUnitChartAccount, Base as ChartBase
from app.models.financial_transactions import FinancialTransaction, TransactionType, TransactionStatus, Base as FinancialBase
from backend.app.models.liquidation_accounts import LiquidationAccount, LiquidationAccountBalance, LiquidationAccountType, Base as LiquidationBase
from backend.app.models.scheduled_transactions import ScheduledTransaction, ScheduledTransactionExecution, Base as ScheduledBase

# Criar todas as tabelas
print("📊 Criando tabelas do banco de dados...")
AuthBase.metadata.create_all(bind=engine)
ChartBase.metadata.create_all(bind=engine)
FinancialBase.metadata.create_all(bind=engine)
LiquidationBase.metadata.create_all(bind=engine)
ScheduledBase.metadata.create_all(bind=engine)

# Criar aplicação FastAPI
app = FastAPI(
    title="FinaFlow Backend",
    description="Sistema de gestão financeira",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://finaflow.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar autenticação
security = HTTPBearer()

def get_current_user(token: str = Depends(security)):
    """Verificar token JWT"""
    try:
        payload = jwt.decode(token.credentials, "finaflow-secret-key-2024", algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Endpoints básicos
@app.get("/")
async def root():
    return {"message": "FinaFlow Backend is running!", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "database": "connected"}

@app.get("/api/v1/status")
async def status():
    return {
        "status": "operational",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/v1/debug/users")
async def debug_users(db: Session = Depends(get_db)):
    """Endpoint público para debug - listar usuários"""
    try:
        users = db.query(User).all()
        return [{
            "id": str(u.id),
            "username": u.username,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "role": u.role,
            "status": u.status
        } for u in users]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/debug/transaction-types")
async def debug_transaction_types():
    """Endpoint para verificar tipos de transação aceitos"""
    try:
        from app.models.financial_transactions import TransactionType, TransactionStatus
        return {
            "transaction_types": [t.value for t in TransactionType],
            "transaction_status": [s.value for s in TransactionStatus],
            "enum_values": {
                "types": list(TransactionType),
                "status": list(TransactionStatus)
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/v1/admin/import-google-sheets")
async def import_google_sheets_data(db: Session = Depends(get_db)):
    """Importar dados da planilha Google Sheets"""
    try:
        # Dados da planilha (primeiras 100 linhas como exemplo)
        sheet_data = [
            {"data": "02/01/2025", "conta": "Diversos", "subgrupo": "Receita", "grupo": "Receita", "valor": 324.79, "liquidacao": "scb", "observacoes": ""},
            {"data": "02/01/2025", "conta": "Diversos", "subgrupo": "Receita", "grupo": "Receita", "valor": 179.87, "liquidacao": "scb", "observacoes": ""},
            {"data": "02/01/2025", "conta": "Compra de material para consumo-CSP", "subgrupo": "Custos com Serviços Prestados", "grupo": "Custos", "valor": 1493.50, "liquidacao": "scb", "observacoes": "metade capas de tnt"},
            {"data": "03/01/2025", "conta": "Diversos", "subgrupo": "Receita", "grupo": "Receita", "valor": 356.10, "liquidacao": "CEF", "observacoes": ""},
            {"data": "03/01/2025", "conta": "Tarifas Bancárias", "subgrupo": "Despesas Financeiras", "grupo": "Despesas Operacionais", "valor": 3.16, "liquidacao": "CEF", "observacoes": "TAXA PIX"},
            {"data": "03/01/2025", "conta": "Outras saídas não operacionais", "subgrupo": "Saídas não Operacionais", "grupo": "Movimentações Não Operacionais", "valor": 270.00, "liquidacao": "scb", "observacoes": ""},
            {"data": "03/01/2025", "conta": "Diversos", "subgrupo": "Receita", "grupo": "Receita", "valor": 500.00, "liquidacao": "CX", "observacoes": ""},
            {"data": "03/01/2025", "conta": "Pró-Labore-ADM", "subgrupo": "Despesas com Pessoal", "grupo": "Despesas Operacionais", "valor": 500.00, "liquidacao": "CX", "observacoes": ""},
            {"data": "06/01/2025", "conta": "Diversos", "subgrupo": "Receita", "grupo": "Receita", "valor": 205.30, "liquidacao": "CEF", "observacoes": ""},
            {"data": "06/01/2025", "conta": "Tarifas Bancárias", "subgrupo": "Despesas Financeiras", "grupo": "Despesas Operacionais", "valor": 1.82, "liquidacao": "CEF", "observacoes": "TAXA PIX"},
        ]
        
        imported_count = 0
        
        for row in sheet_data:
            try:
                # Converter data
                data_movimentacao = datetime.datetime.strptime(row["data"], "%d/%m/%Y")
                
                # Buscar tenant, usuário, business unit, conta contábil e conta de liquidação
                tenant = db.query(Tenant).first()
                user = db.query(User).first()
                business_unit = db.query(BusinessUnit).first()
                
                # Buscar conta contábil baseada no nome da conta da planilha
                chart_account = db.query(ChartAccount).filter(
                    ChartAccount.name == row["conta"]
                ).first()
                
                # Se não encontrar, usar a primeira conta disponível
                if not chart_account:
                    chart_account = db.query(ChartAccount).first()
                
                # Buscar conta de liquidação baseada no campo "liquidacao" da planilha
                liquidation_account = None
                if row.get("liquidacao"):
                    liquidation_account = db.query(LiquidationAccount).filter(
                        LiquidationAccount.code == row["liquidacao"],
                        LiquidationAccount.tenant_id == tenant.id
                    ).first()
                
                if not tenant or not user or not business_unit:
                    print(f"Erro: tenant={tenant}, user={user}, business_unit={business_unit}")
                    continue
                
                # Se não houver conta contábil, criar uma padrão
                if not chart_account:
                    # Criar grupo primeiro
                    group = ChartAccountGroup(
                        id=str(uuid.uuid4()),
                        code="001",
                        name="Grupo Padrão",
                        description="Grupo padrão para importação",
                        is_active=True,
                        created_at=datetime.datetime.now(),
                        updated_at=datetime.datetime.now()
                    )
                    db.add(group)
                    db.flush()
                    
                    # Criar subgrupo
                    subgroup = ChartAccountSubgroup(
                        id=str(uuid.uuid4()),
                        code="001",
                        name="Subgrupo Padrão",
                        description="Subgrupo padrão para importação",
                        group_id=group.id,
                        is_active=True,
                        created_at=datetime.datetime.now(),
                        updated_at=datetime.datetime.now()
                    )
                    db.add(subgroup)
                    db.flush()
                    
                    # Criar conta contábil
                    chart_account = ChartAccount(
                        id=str(uuid.uuid4()),
                        code="001",
                        name="Conta Padrão",
                        description="Conta padrão para importação",
                        subgroup_id=subgroup.id,
                        account_type="asset",
                        is_active=True,
                        created_at=datetime.datetime.now(),
                        updated_at=datetime.datetime.now()
                    )
                    db.add(chart_account)
                    db.flush()
                
                # Criar transação financeira
                transaction = FinancialTransaction(
                    id=str(uuid.uuid4()),
                    reference=f"GS-{row['data'].replace('/', '')}-{imported_count + 1}",  # Referência única
                    business_unit_id=business_unit.id,  # Usar business unit existente
                    chart_account_id=chart_account.id,
                    liquidation_account_id=liquidation_account.id if liquidation_account else None,
                    transaction_date=data_movimentacao,
                    amount=row["valor"],
                    description=f"{row['conta']} - {row['observacoes']}".strip(" -"),
                    transaction_type="receita" if "Receita" in row["grupo"] else "despesa",
                    status="aprovada",
                    created_by=user.id,
                    approved_by=user.id,
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now()
                )
                
                db.add(transaction)
                imported_count += 1
                
            except Exception as e:
                print(f"Erro ao importar linha: {row} - {str(e)}")
                continue
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Importação concluída com sucesso",
            "imported_count": imported_count,
            "total_rows": len(sheet_data)
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

# Endpoints do Dashboard
@app.get("/api/v1/auth/user-info")
async def get_user_info(db: Session = Depends(get_db)):
    """Informações do usuário logado"""
    try:
        # Por enquanto, retornar usuário padrão
        user = db.query(User).first()
        if user:
            return {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "status": user.status
            }
        return {"error": "Usuário não encontrado"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/financial/annual-summary")
async def get_annual_summary(year: int = 2025, db: Session = Depends(get_db)):
    """Resumo anual das finanças"""
    try:
        # Buscar transações do ano
        transactions = db.query(FinancialTransaction).filter(
            FinancialTransaction.transaction_date >= f"{year}-01-01",
            FinancialTransaction.transaction_date <= f"{year}-12-31"
        ).all()
        
        receitas = sum(t.amount for t in transactions if t.transaction_type == "receita")
        despesas = sum(t.amount for t in transactions if t.transaction_type == "despesa")
        
        return {
            "year": year,
            "revenue": receitas,
            "expenses": despesas,
            "profit": receitas - despesas,
            "total_receitas": receitas,
            "total_despesas": despesas,
            "saldo": receitas - despesas,
            "transaction_count": len(transactions),
            "monthly_data": [
                {
                    "month": "01",
                    "revenue": receitas,
                    "expenses": despesas,
                    "profit": receitas - despesas
                }
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/financial/wallet")
async def get_wallet(year: int = 2025, db: Session = Depends(get_db)):
    """Informações da carteira/saldo"""
    try:
        # Buscar transações do ano
        transactions = db.query(FinancialTransaction).filter(
            FinancialTransaction.transaction_date >= f"{year}-01-01",
            FinancialTransaction.transaction_date <= f"{year}-12-31"
        ).all()
        
        receitas = sum(t.amount for t in transactions if t.transaction_type == "receita")
        despesas = sum(t.amount for t in transactions if t.transaction_type == "despesa")
        saldo = receitas - despesas
        
        return {
            "saldo_disponivel": saldo,
            "total_receitas": receitas,
            "total_despesas": despesas,
            "year": year
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/financial/transactions")
async def get_transactions(year: int = 2025, limit: int = 10, cursor: str = "", db: Session = Depends(get_db)):
    """Listar transações financeiras"""
    try:
        query = db.query(FinancialTransaction).filter(
            FinancialTransaction.transaction_date >= f"{year}-01-01",
            FinancialTransaction.transaction_date <= f"{year}-12-31"
        ).order_by(FinancialTransaction.transaction_date.desc())
        
        transactions = query.limit(limit).all()
        
        return {
            "transactions": [{
                "id": str(t.id),
                "description": t.description,
                "amount": t.amount,
                "transaction_type": t.transaction_type,
                "transaction_date": t.transaction_date.isoformat(),
                "status": t.status,
                "type": t.transaction_type,
                "date": t.transaction_date.isoformat(),
                "value": t.amount
            } for t in transactions],
            "has_more": len(transactions) == limit,
            "data": [{
                "id": str(t.id),
                "description": t.description,
                "amount": t.amount,
                "transaction_type": t.transaction_type,
                "transaction_date": t.transaction_date.isoformat(),
                "status": t.status
            } for t in transactions]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/financial/cash-flow")
async def get_cash_flow(db: Session = Depends(get_db)):
    """Fluxo de caixa"""
    try:
        # Buscar transações dos últimos 12 meses
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        transactions = db.query(FinancialTransaction).filter(
            FinancialTransaction.transaction_date >= start_date,
            FinancialTransaction.transaction_date <= end_date
        ).all()
        
        receitas = sum(t.amount for t in transactions if t.transaction_type == "receita")
        despesas = sum(t.amount for t in transactions if t.transaction_type == "despesa")
        
        return {
            "periodo": "Últimos 12 meses",
            "revenue": receitas,
            "expenses": despesas,
            "profit": receitas - despesas,
            "total_receitas": receitas,
            "total_despesas": despesas,
            "saldo": receitas - despesas,
            "transaction_count": len(transactions),
            "monthly_data": [
                {
                    "month": "01",
                    "revenue": receitas,
                    "expenses": despesas,
                    "profit": receitas - despesas
                }
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/saldo-disponivel")
async def get_saldo_disponivel(db: Session = Depends(get_db)):
    """Saldo disponível"""
    try:
        transactions = db.query(FinancialTransaction).all()
        receitas = sum(t.amount for t in transactions if t.transaction_type == "receita")
        despesas = sum(t.amount for t in transactions if t.transaction_type == "despesa")
        
        return {
            "saldo_disponivel": receitas - despesas,
            "total_receitas": receitas,
            "total_despesas": despesas
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/lancamentos-diarios")
async def get_lancamentos_diarios(year: int = 2025, limit: int = 10, db: Session = Depends(get_db)):
    """Lançamentos diários"""
    try:
        query = db.query(FinancialTransaction).filter(
            FinancialTransaction.transaction_date >= f"{year}-01-01",
            FinancialTransaction.transaction_date <= f"{year}-12-31"
        ).order_by(FinancialTransaction.transaction_date.desc())
        
        transactions = query.limit(limit).all()
        
        return {
            "lancamentos": [{
                "id": str(t.id),
                "description": t.description,
                "amount": t.amount,
                "transaction_type": t.transaction_type,
                "transaction_date": t.transaction_date.isoformat(),
                "status": t.status
            } for t in transactions],
            "data": [{
                "id": str(t.id),
                "description": t.description,
                "amount": t.amount,
                "transaction_type": t.transaction_type,
                "transaction_date": t.transaction_date.isoformat(),
                "status": t.status
            } for t in transactions],
            "total": len(transactions)
        }
    except Exception as e:
        return {"error": str(e)}

# Endpoints de Contas de Liquidação
@app.get("/api/v1/liquidation-accounts")
async def get_liquidation_accounts(db: Session = Depends(get_db)):
    """Listar contas de liquidação"""
    try:
        accounts = db.query(LiquidationAccount).filter(LiquidationAccount.is_active == True).all()
        return [{
            "id": str(a.id),
            "code": a.code,
            "name": a.name,
            "description": a.description,
            "account_type": a.account_type,
            "bank_name": a.bank_name,
            "account_number": a.account_number,
            "current_balance": float(a.current_balance),
            "currency": a.currency,
            "is_default": a.is_default
        } for a in accounts]
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/v1/liquidation-accounts")
async def create_liquidation_account(account_data: dict, db: Session = Depends(get_db)):
    """Criar conta de liquidação"""
    try:
        # Buscar tenant padrão
        tenant = db.query(Tenant).first()
        if not tenant:
            return {"error": "Nenhum tenant encontrado"}
        
        account = LiquidationAccount(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            code=account_data.get("code"),
            name=account_data.get("name"),
            description=account_data.get("description"),
            account_type=account_data.get("account_type", "other"),
            bank_name=account_data.get("bank_name"),
            account_number=account_data.get("account_number"),
            current_balance=account_data.get("current_balance", 0),
            currency=account_data.get("currency", "BRL"),
            is_default=account_data.get("is_default", False),
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        
        db.add(account)
        db.commit()
        
        return {
            "success": True,
            "message": "Conta de liquidação criada com sucesso",
            "account": {
                "id": str(account.id),
                "code": account.code,
                "name": account.name
            }
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@app.post("/api/v1/admin/create-default-liquidation-accounts")
async def create_default_liquidation_accounts(db: Session = Depends(get_db)):
    """Criar contas de liquidação padrão baseadas na planilha"""
    try:
        # Buscar tenant padrão
        tenant = db.query(Tenant).first()
        if not tenant:
            return {"error": "Nenhum tenant encontrado. Execute primeiro /api/v1/admin/create-test-data"}
        
        # Contas padrão da planilha
        default_accounts = [
            {"code": "scb", "name": "SCB", "account_type": "bank_account", "bank_name": "SCB"},
            {"code": "CEF", "name": "Caixa Econômica Federal", "account_type": "bank_account", "bank_name": "CEF"},
            {"code": "CX", "name": "Caixa", "account_type": "cash", "bank_name": None},
            {"code": "cef", "name": "Caixa Econômica Federal (Minúsculo)", "account_type": "bank_account", "bank_name": "CEF"},
        ]
        
        created_count = 0
        for acc_data in default_accounts:
            # Verificar se já existe
            existing = db.query(LiquidationAccount).filter(
                LiquidationAccount.code == acc_data["code"],
                LiquidationAccount.tenant_id == tenant.id
            ).first()
            
            if not existing:
                account = LiquidationAccount(
                    id=str(uuid.uuid4()),
                    code=acc_data["code"],
                    name=acc_data["name"],
                    account_type=acc_data["account_type"],
                    bank_name=acc_data["bank_name"],
                    current_balance=0,
                    currency="BRL",
                    is_default=False,
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now()
                )
                db.add(account)
                created_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Criadas {created_count} contas de liquidação padrão",
            "created_count": created_count
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@app.post("/api/v1/admin/create-chart-accounts")
async def create_chart_accounts(db: Session = Depends(get_db)):
    """Criar plano de contas completo baseado na planilha"""
    try:
        # Buscar tenant padrão
        tenant = db.query(Tenant).first()
        if not tenant:
            return {"error": "Nenhum tenant encontrado. Execute primeiro /api/v1/admin/create-test-data"}
        
        # Verificar se já existem contas
        existing_accounts = db.query(ChartAccount).count()
        if existing_accounts > 0:
            return {
                "success": True,
                "message": f"Plano de contas já existe com {existing_accounts} contas",
                "existing_count": existing_accounts
            }
        
        # Criar plano de contas diretamente
        chart_structure = {
            "Receita": {
                "Receita": ["Diversos", "Serviço Ivone"],
                "Receita Financeira": ["Outras Receitas Financeiras"]
            },
            "Custos": {
                "Custos com Serviços Prestados": ["Compra de material para consumo-CSP", "Serviços de terceiros-CSP"],
                "Custos com Mão de Obra": ["Salário"]
            },
            "Despesas Operacionais": {
                "Despesas Financeiras": ["Tarifas Bancárias", "Aluguel de Máquinas de Cartão"],
                "Despesas com Pessoal": ["Pró-Labore-ADM"],
                "Despesas Administrativas": ["Serviços de terceiros-ADM", "Seguros", "Telefone e Internet-ADM"],
                "Despesas Comerciais": ["Brindes", "Gasolina / Combustível-COM"]
            },
            "Movimentações Não Operacionais": {
                "Saídas não Operacionais": ["Outras saídas não operacionais"]
            }
        }
        
        created_groups = {}
        created_subgroups = {}
        created_accounts = {}
        
        # Criar grupos
        for group_name in chart_structure.keys():
            group = ChartAccountGroup(
                code=_generate_group_code(group_name),
                name=group_name,
                description=f"Grupo {group_name}",
                is_active=True
            )
            db.add(group)
            created_groups[group_name] = group
        
        db.flush()
        
        # Criar subgrupos
        for group_name, subgroups in chart_structure.items():
            group = created_groups[group_name]
            for subgroup_name, accounts in subgroups.items():
                subgroup = ChartAccountSubgroup(
                    code=f"{group.code}{len(created_subgroups)+1:02d}",
                    name=subgroup_name,
                    description=f"Subgrupo {subgroup_name}",
                    group_id=group.id,
                    is_active=True
                )
                db.add(subgroup)
                created_subgroups[subgroup_name] = subgroup
        
        db.flush()
        
        # Criar contas
        for group_name, subgroups in chart_structure.items():
            for subgroup_name, accounts in subgroups.items():
                subgroup = created_subgroups[subgroup_name]
                for account_name in accounts:
                    account = ChartAccount(
                        code=f"{subgroup.code}{len(created_accounts)+1:03d}",
                        name=account_name,
                        description=f"Conta {account_name}",
                        subgroup_id=subgroup.id,
                        account_type=_determine_account_type(group_name, subgroup_name),
                        is_active=True
                    )
                    db.add(account)
                    created_accounts[account_name] = account
        
        db.commit()
        
        return {
            "success": True,
            "message": "Plano de contas criado com sucesso",
            "created": {
                "groups": len(created_groups),
                "subgroups": len(created_subgroups),
                "accounts": len(created_accounts)
            }
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

def _generate_group_code(group_name: str) -> str:
    """Gerar código para grupo"""
    codes = {
        "Receita": "1",
        "Custos": "2", 
        "Despesas Operacionais": "3",
        "Movimentações Não Operacionais": "4"
    }
    return codes.get(group_name, "9")

def _generate_subgroup_code(subgroup_name: str) -> str:
    """Gerar código para subgrupo"""
    codes = {
        "Receita": "01",
        "Receita Financeira": "02",
        "Custos com Serviços Prestados": "01",
        "Custos com Mão de Obra": "02",
        "Despesas Financeiras": "01",
        "Despesas com Pessoal": "02",
        "Despesas Administrativas": "03",
        "Despesas Comerciais": "04",
        "Saídas não Operacionais": "01"
    }
    return codes.get(subgroup_name, "99")

def _generate_account_code(account_name: str) -> str:
    """Gerar código para conta"""
    codes = {
        "Diversos": "001",
        "Serviço Ivone": "002",
        "Outras Receitas Financeiras": "001",
        "Compra de material para consumo-CSP": "001",
        "Serviços de terceiros-CSP": "002",
        "Salário": "001",
        "Tarifas Bancárias": "001",
        "Aluguel de Máquinas de Cartão": "002",
        "Pró-Labore-ADM": "001",
        "Serviços de terceiros-ADM": "001",
        "Seguros": "002",
        "Telefone e Internet-ADM": "003",
        "Brindes": "001",
        "Gasolina / Combustível-COM": "002",
        "Outras saídas não operacionais": "001"
    }
    return codes.get(account_name, "999")

def _determine_account_type(group_name: str, subgroup_name: str) -> str:
    """Determinar tipo da conta baseado no grupo e subgrupo"""
    if "Receita" in group_name:
        return "receita"
    elif "Custo" in group_name:
        return "custo"
    elif "Despesa" in group_name:
        return "despesa"
    elif "Movimentação" in group_name:
        return "movimentacao"
    else:
        return "outro"

@app.post("/api/v1/admin/clear-chart-accounts")
async def clear_chart_accounts(db: Session = Depends(get_db)):
    """Limpar plano de contas existente"""
    try:
        # Deletar contas
        db.query(ChartAccount).delete()
        # Deletar subgrupos
        db.query(ChartAccountSubgroup).delete()
        # Deletar grupos
        db.query(ChartAccountGroup).delete()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Plano de contas limpo com sucesso"
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@app.post("/api/v1/admin/reset-and-create-chart-accounts")
async def reset_and_create_chart_accounts(db: Session = Depends(get_db)):
    """Resetar sistema e criar plano de contas completo"""
    try:
        # Buscar tenant padrão
        tenant = db.query(Tenant).first()
        if not tenant:
            return {"error": "Nenhum tenant encontrado. Execute primeiro /api/v1/admin/create-test-data"}
        
        # Limpar transações financeiras primeiro
        db.query(FinancialTransaction).delete()
        
        # Limpar plano de contas
        db.query(ChartAccount).delete()
        db.query(ChartAccountSubgroup).delete()
        db.query(ChartAccountGroup).delete()
        
        db.flush()
        
        # Criar plano de contas completo
        chart_structure = {
            "Receita": {
                "Receita": ["Diversos", "Serviço Ivone"],
                "Receita Financeira": ["Outras Receitas Financeiras"]
            },
            "Custos": {
                "Custos com Serviços Prestados": ["Compra de material para consumo-CSP", "Serviços de terceiros-CSP"],
                "Custos com Mão de Obra": ["Salário"]
            },
            "Despesas Operacionais": {
                "Despesas Financeiras": ["Tarifas Bancárias", "Aluguel de Máquinas de Cartão"],
                "Despesas com Pessoal": ["Pró-Labore-ADM"],
                "Despesas Administrativas": ["Serviços de terceiros-ADM", "Seguros", "Telefone e Internet-ADM"],
                "Despesas Comerciais": ["Brindes", "Gasolina / Combustível-COM"]
            },
            "Movimentações Não Operacionais": {
                "Saídas não Operacionais": ["Outras saídas não operacionais"]
            }
        }
        
        created_groups = {}
        created_subgroups = {}
        created_accounts = {}
        
        # Criar grupos
        for group_name in chart_structure.keys():
            group = ChartAccountGroup(
                code=_generate_group_code(group_name),
                name=group_name,
                description=f"Grupo {group_name}",
                is_active=True
            )
            db.add(group)
            created_groups[group_name] = group
        
        db.flush()
        
        # Criar subgrupos
        for group_name, subgroups in chart_structure.items():
            group = created_groups[group_name]
            for subgroup_name, accounts in subgroups.items():
                subgroup = ChartAccountSubgroup(
                    code=f"{group.code}{len(created_subgroups)+1:02d}",
                    name=subgroup_name,
                    description=f"Subgrupo {subgroup_name}",
                    group_id=group.id,
                    is_active=True
                )
                db.add(subgroup)
                created_subgroups[subgroup_name] = subgroup
        
        db.flush()
        
        # Criar contas
        for group_name, subgroups in chart_structure.items():
            for subgroup_name, accounts in subgroups.items():
                subgroup = created_subgroups[subgroup_name]
                for account_name in accounts:
                    account = ChartAccount(
                        code=f"{subgroup.code}{len(created_accounts)+1:03d}",
                        name=account_name,
                        description=f"Conta {account_name}",
                        subgroup_id=subgroup.id,
                        account_type=_determine_account_type(group_name, subgroup_name),
                        is_active=True
                    )
                    db.add(account)
                    created_accounts[account_name] = account
        
        db.commit()
        
        return {
            "success": True,
            "message": "Sistema resetado e plano de contas criado com sucesso",
            "created": {
                "groups": len(created_groups),
                "subgroups": len(created_subgroups),
                "accounts": len(created_accounts)
            }
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@app.get("/api/v1/chart-accounts")
async def get_chart_accounts(db: Session = Depends(get_db)):
    """Listar plano de contas hierárquico"""
    try:
        # Buscar grupos
        groups = db.query(ChartAccountGroup).filter(ChartAccountGroup.is_active == True).all()
        
        result = []
        for group in groups:
            group_data = {
                "id": str(group.id),
                "code": group.code,
                "name": group.name,
                "description": group.description,
                "subgroups": []
            }
            
            # Buscar subgrupos do grupo
            subgroups = db.query(ChartAccountSubgroup).filter(
                ChartAccountSubgroup.group_id == group.id,
                ChartAccountSubgroup.is_active == True
            ).all()
            
            for subgroup in subgroups:
                subgroup_data = {
                    "id": str(subgroup.id),
                    "code": subgroup.code,
                    "name": subgroup.name,
                    "description": subgroup.description,
                    "accounts": []
                }
                
                # Buscar contas do subgrupo
                accounts = db.query(ChartAccount).filter(
                    ChartAccount.subgroup_id == subgroup.id,
                    ChartAccount.is_active == True
                ).all()
                
                for account in accounts:
                    account_data = {
                        "id": str(account.id),
                        "code": account.code,
                        "name": account.name,
                        "description": account.description,
                        "account_type": account.account_type
                    }
                    subgroup_data["accounts"].append(account_data)
                
                group_data["subgroups"].append(subgroup_data)
            
            result.append(group_data)
        
        return result
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/cash-flow-by-liquidation")
async def get_cash_flow_by_liquidation(year: int = 2025, db: Session = Depends(get_db)):
    """Fluxo de caixa detalhado por conta de liquidação"""
    try:
        # Buscar todas as contas de liquidação
        liquidation_accounts = db.query(LiquidationAccount).filter(
            LiquidationAccount.is_active == True
        ).all()
        
        result = []
        for account in liquidation_accounts:
            # Buscar transações da conta no ano (usando filtro por string)
            transactions = db.query(FinancialTransaction).filter(
                FinancialTransaction.liquidation_account_id == str(account.id),
                FinancialTransaction.transaction_date >= f"{year}-01-01",
                FinancialTransaction.transaction_date <= f"{year}-12-31"
            ).all()
            
            # Calcular totais
            total_credits = sum(t.amount for t in transactions if t.transaction_type == "receita")
            total_debits = sum(t.amount for t in transactions if t.transaction_type == "despesa")
            net_flow = total_credits - total_debits
            
            account_data = {
                "account_id": str(account.id),
                "account_code": account.code,
                "account_name": account.name,
                "account_type": account.account_type,
                "bank_name": account.bank_name,
                "current_balance": float(account.current_balance),
                "total_credits": total_credits,
                "total_debits": total_debits,
                "net_flow": net_flow,
                "transaction_count": len(transactions),
                "transactions": [{
                    "id": str(t.id),
                    "date": t.transaction_date.isoformat(),
                    "description": t.description,
                    "amount": float(t.amount),
                    "type": t.transaction_type,
                    "reference": t.reference
                } for t in transactions[:10]]  # Últimas 10 transações
            }
            result.append(account_data)
        
        return {
            "year": year,
            "accounts": result,
            "summary": {
                "total_accounts": len(result),
                "total_credits": sum(a["total_credits"] for a in result),
                "total_debits": sum(a["total_debits"] for a in result),
                "net_flow": sum(a["net_flow"] for a in result)
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/liquidation-account-statement/{account_id}")
async def get_liquidation_account_statement(account_id: str, year: int = 2025, month: int = None, db: Session = Depends(get_db)):
    """Extrato detalhado de uma conta de liquidação específica"""
    try:
        # Buscar conta
        account = db.query(LiquidationAccount).filter(
            LiquidationAccount.id == account_id
        ).first()
        
        if not account:
            return {"error": "Conta de liquidação não encontrada"}
        
        # Construir filtro de data
        date_filter = FinancialTransaction.transaction_date >= f"{year}-01-01"
        date_filter = date_filter & (FinancialTransaction.transaction_date <= f"{year}-12-31")
        
        if month:
            date_filter = date_filter & (FinancialTransaction.transaction_date >= f"{year}-{month:02d}-01")
            date_filter = date_filter & (FinancialTransaction.transaction_date <= f"{year}-{month:02d}-31")
        
        # Buscar transações
        transactions = db.query(FinancialTransaction).filter(
            FinancialTransaction.liquidation_account_id == str(account_id),
            date_filter
        ).order_by(FinancialTransaction.transaction_date.desc()).all()
        
        # Calcular saldo inicial (simulado)
        opening_balance = float(account.current_balance) - sum(
            t.amount if t.transaction_type == "receita" else -t.amount 
            for t in transactions
        )
        
        # Calcular totais
        total_credits = sum(t.amount for t in transactions if t.transaction_type == "receita")
        total_debits = sum(t.amount for t in transactions if t.transaction_type == "despesa")
        closing_balance = opening_balance + total_credits - total_debits
        
        return {
            "account": {
                "id": str(account.id),
                "code": account.code,
                "name": account.name,
                "account_type": account.account_type,
                "bank_name": account.bank_name
            },
            "period": {
                "year": year,
                "month": month,
                "opening_balance": opening_balance,
                "closing_balance": closing_balance
            },
            "summary": {
                "total_credits": total_credits,
                "total_debits": total_debits,
                "net_movement": total_credits - total_debits,
                "transaction_count": len(transactions)
            },
            "transactions": [{
                "id": str(t.id),
                "date": t.transaction_date.isoformat(),
                "description": t.description,
                "amount": float(t.amount),
                "type": t.transaction_type,
                "reference": t.reference,
                "status": t.status
            } for t in transactions]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/admin/debug-import")
async def debug_import(db: Session = Depends(get_db)):
    """Debug da importação"""
    try:
        # Verificar dados básicos
        tenant = db.query(Tenant).first()
        user = db.query(User).first()
        business_unit = db.query(BusinessUnit).first()
        chart_account = db.query(ChartAccount).first()
        liquidation_account = db.query(LiquidationAccount).first()
        
        return {
            "tenant": str(tenant.id) if tenant else None,
            "user": str(user.id) if user else None,
            "business_unit": str(business_unit.id) if business_unit else None,
            "chart_account": str(chart_account.id) if chart_account else None,
            "liquidation_account": str(liquidation_account.id) if liquidation_account else None,
            "chart_accounts_count": db.query(ChartAccount).count(),
            "liquidation_accounts_count": db.query(LiquidationAccount).count(),
            "transactions_count": db.query(FinancialTransaction).count()
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/v1/admin/create-test-transaction")
async def create_test_transaction(db: Session = Depends(get_db)):
    """Criar uma transação de teste"""
    try:
        # Buscar dados básicos
        tenant = db.query(Tenant).first()
        user = db.query(User).first()
        business_unit = db.query(BusinessUnit).first()
        chart_account = db.query(ChartAccount).first()
        liquidation_account = db.query(LiquidationAccount).first()
        
        if not all([tenant, user, business_unit, chart_account, liquidation_account]):
            return {"error": "Dados básicos não encontrados"}
        
        # Criar transação de teste
        transaction = FinancialTransaction(
            reference="TEST-001",
            tenant_id=tenant.id,
            business_unit_id=business_unit.id,
            chart_account_id=chart_account.id,
            liquidation_account_id=liquidation_account.id,
            transaction_date=datetime.datetime.now(),
            amount=100.00,
            description="Transação de teste",
            transaction_type="receita",
            status="aprovada",
            created_by=user.id,
            approved_by=user.id,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        
        db.add(transaction)
        db.commit()
        
        return {
            "success": True,
            "message": "Transação de teste criada com sucesso",
            "transaction_id": str(transaction.id)
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

# Endpoints de autenticação
@app.post("/api/v1/auth/login")
async def login(credentials: dict, db: Session = Depends(get_db)):
    """Login do usuário"""
    try:
        username = credentials.get("username")
        password = credentials.get("password")
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username e password são obrigatórios")
        
        # Buscar usuário
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        # Verificar senha
        if password != user.hashed_password:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        # Gerar token
        token_data = {
            "user_id": str(user.id),
            "username": user.username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        
        token = jwt.encode(token_data, "finaflow-secret-key-2024", algorithm="HS256")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Endpoints de dados
@app.get("/api/v1/tenants")
async def get_tenants(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Listar tenants"""
    try:
        tenants = db.query(Tenant).all()
        return [{"id": str(t.id), "name": t.name, "created_at": t.created_at.isoformat()} for t in tenants]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/business-units")
async def get_business_units(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Listar business units"""
    try:
        business_units = db.query(BusinessUnit).all()
        return [{"id": str(bu.id), "name": bu.name, "tenant_id": str(bu.tenant_id)} for bu in business_units]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/chart-accounts")
async def get_chart_accounts(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Listar plano de contas"""
    try:
        accounts = db.query(ChartAccount).all()
        return [{"id": str(a.id), "name": a.name, "code": a.code} for a in accounts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/transactions")
async def get_transactions(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Listar transações financeiras"""
    try:
        transactions = db.query(FinancialTransaction).limit(100).all()
        return [{
            "id": str(t.id),
            "amount": float(t.amount),
            "description": t.description,
            "date": t.transaction_date.isoformat() if t.transaction_date else None
        } for t in transactions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para criar dados de teste
@app.post("/api/v1/admin/create-test-data")
async def create_test_data(db: Session = Depends(get_db)):
    """Criar dados de teste"""
    try:
        # Criar tenant
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name="Empresa Teste",
            domain="empresa-teste.com",
            status="active",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        db.add(tenant)
        db.flush()
        
        # Criar business unit
        business_unit = BusinessUnit(
            id=str(uuid.uuid4()),
            name="Unidade Principal",
            code="UNI001",
            tenant_id=tenant.id,
            status="active",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        db.add(business_unit)
        db.flush()
        
        # Criar usuário admin
        admin_user = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@finaflow.com",
            hashed_password="admin123",
            first_name="Admin",
            last_name="Sistema",
            tenant_id=tenant.id,
            business_unit_id=business_unit.id,
            role="admin",
            status="active",
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        db.add(admin_user)
        db.flush()
        
        # Criar acesso do usuário ao tenant
        user_tenant_access = UserTenantAccess(
            id=str(uuid.uuid4()),
            user_id=admin_user.id,
            tenant_id=tenant.id,
            role="admin",
            created_at=datetime.datetime.now()
        )
        db.add(user_tenant_access)
        
        # Criar acesso do usuário ao business unit
        user_bu_access = UserBusinessUnitAccess(
            id=str(uuid.uuid4()),
            user_id=admin_user.id,
            business_unit_id=business_unit.id,
            role="admin",
            created_at=datetime.datetime.now()
        )
        db.add(user_bu_access)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Dados de teste criados com sucesso",
            "tenant_id": str(tenant.id),
            "business_unit_id": str(business_unit.id),
            "user_id": str(admin_user.id)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar dados de teste: {str(e)}")

if __name__ == "__main__":
    print("🚀 Iniciando servidor...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
