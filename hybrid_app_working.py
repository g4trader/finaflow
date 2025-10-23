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

# Criar todas as tabelas
print("📊 Criando tabelas do banco de dados...")
AuthBase.metadata.create_all(bind=engine)
ChartBase.metadata.create_all(bind=engine)
FinancialBase.metadata.create_all(bind=engine)

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
                
                # Buscar tenant, usuário, business unit e conta contábil padrão
                tenant = db.query(Tenant).first()
                user = db.query(User).first()
                business_unit = db.query(BusinessUnit).first()
                chart_account = db.query(ChartAccount).first()
                
                if not tenant or not user or not business_unit:
                    return {"success": False, "error": "Nenhum tenant, usuário ou business unit encontrado. Execute primeiro /api/v1/admin/create-test-data"}
                
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
                    tenant_id=tenant.id,
                    business_unit_id=business_unit.id,  # Usar business unit existente
                    chart_account_id=chart_account.id,
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
            "total_receitas": receitas,
            "total_despesas": despesas,
            "saldo": receitas - despesas,
            "transaction_count": len(transactions)
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
            "total": len(transactions)
        }
    except Exception as e:
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
