from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import jwt
import datetime
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Importar configurações do banco de dados
try:
    from app.database import get_db, engine
    from app.models.auth import User, Base as AuthBase
    DB_AVAILABLE = True
    print("✅ Database models available")
except ImportError as e:
    DB_AVAILABLE = False
    print(f"⚠️ Database models not available: {e}")
    # Função de fallback para quando o banco não está disponível
    def get_db():
        return None

# Modelos Pydantic para Tenants e Business Units
class TenantCreate(BaseModel):
    name: str
    domain: str
    status: str = "active"

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    status: Optional[str] = None

class TenantResponse(BaseModel):
    id: str
    name: str
    domain: str
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class BusinessUnitCreate(BaseModel):
    tenant_id: str
    name: str
    code: str
    status: str = "active"

class BusinessUnitUpdate(BaseModel):
    tenant_id: Optional[str] = None
    name: Optional[str] = None
    code: Optional[str] = None
    status: Optional[str] = None

class BusinessUnitResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    code: str
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://finaflow.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criar tabelas no banco de dados se disponível
if DB_AVAILABLE:
    try:
        AuthBase.metadata.create_all(bind=engine)
        print("✅ Database tables created")
    except Exception as e:
        print(f"⚠️ Could not create database tables: {e}")
        DB_AVAILABLE = False

# Modelos Pydantic para compatibilidade com o frontend
class UserCreate(BaseModel):
    name: str
    email: str
    phone: str
    role: str = "user"
    status: str = "active"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    role: str
    status: str
    created_at: str
    last_login: Optional[str] = None

    class Config:
        from_attributes = True

# Banco de dados em memória como fallback
users_db = [
    {
        "id": "1",
        "name": "João Silva",
        "email": "joao@empresa.com",
        "phone": "(11) 99999-9999",
        "role": "admin",
        "status": "active",
        "created_at": "2024-01-15",
        "last_login": "2024-08-07"
    },
    {
        "id": "2",
        "name": "Maria Santos",
        "email": "maria@empresa.com",
        "phone": "(11) 88888-8888",
        "role": "manager",
        "status": "active",
        "created_at": "2024-02-20",
        "last_login": "2024-08-06"
    },
    {
        "id": "3",
        "name": "Pedro Costa",
        "email": "pedro@empresa.com",
        "phone": "(11) 77777-7777",
        "role": "user",
        "status": "inactive",
        "created_at": "2024-03-10",
        "last_login": "2024-07-30"
    }
]

# Dados em memória para Tenants
tenants_db = [
    {
        "id": "1",
        "name": "Empresa A",
        "domain": "empresa-a.com",
        "status": "active",
        "created_at": "2024-01-15",
        "updated_at": "2024-01-15"
    },
    {
        "id": "2",
        "name": "Empresa B",
        "domain": "empresa-b.com",
        "status": "active",
        "created_at": "2024-02-20",
        "updated_at": "2024-02-20"
    }
]

# Dados em memória para Business Units
business_units_db = [
    {
        "id": "1",
        "tenant_id": "1",
        "name": "BU São Paulo",
        "code": "SP",
        "status": "active",
        "created_at": "2024-01-15",
        "updated_at": "2024-01-15"
    },
    {
        "id": "2",
        "tenant_id": "1",
        "name": "BU Rio de Janeiro",
        "code": "RJ",
        "status": "active",
        "created_at": "2024-02-20",
        "updated_at": "2024-02-20"
    },
    {
        "id": "3",
        "tenant_id": "2",
        "name": "BU Minas Gerais",
        "code": "MG",
        "status": "active",
        "created_at": "2024-03-10",
        "updated_at": "2024-03-10"
    }
]

# Contadores para IDs
next_tenant_id = 3
next_bu_id = 4

next_user_id = 4

# Dados em memória para empresas e BUs
tenants_db = []
next_tenant_id = 1
business_units_db = []
next_bu_id = 1

@app.get("/")
async def root():
    return {"message": "FinaFlow Backend API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "finaflow-backend"}

@app.get("/api/v1/test")
async def test():
    return {"message": "API funcionando!"}

@app.post("/api/v1/auth/login")
async def login():
    # Criar um JWT simples para teste
    payload = {
        "sub": "1",
        "username": "admin",
        "email": "admin@finaflow.com",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin",
        "tenant_id": "1",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    
    # Usar uma chave secreta simples para teste
    secret_key = "finaflow-secret-key-2024"
    
    access_token = jwt.encode(payload, secret_key, algorithm="HS256")
    
    return {
        "access_token": access_token,
        "refresh_token": "test-refresh-token",
        "token_type": "bearer",
        "expires_in": 1800
    }

# CRUD de Empresas (Tenants)
@app.get("/api/v1/tenants", response_model=List[TenantResponse])
async def get_tenants(db: Session = Depends(get_db)):
    """Listar todas as empresas"""
    return [TenantResponse(**tenant) for tenant in tenants_db]

@app.get("/api/v1/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """Buscar empresa por ID"""
    tenant = next((t for t in tenants_db if t["id"] == tenant_id), None)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return TenantResponse(**tenant)

@app.post("/api/v1/tenants", response_model=TenantResponse, status_code=201)
async def create_tenant(tenant_data: TenantCreate, db: Session = Depends(get_db)):
    """Criar nova empresa"""
    global next_tenant_id
    tenant = {
        "id": str(next_tenant_id),
        "name": tenant_data.name,
        "domain": tenant_data.domain,
        "status": tenant_data.status,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d"),
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d")
    }
    tenants_db.append(tenant)
    next_tenant_id += 1
    return TenantResponse(**tenant)

@app.put("/api/v1/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, tenant_data: TenantUpdate, db: Session = Depends(get_db)):
    """Atualizar empresa"""
    tenant = next((t for t in tenants_db if t["id"] == tenant_id), None)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    if tenant_data.name is not None:
        tenant["name"] = tenant_data.name
    if tenant_data.domain is not None:
        tenant["domain"] = tenant_data.domain
    if tenant_data.status is not None:
        tenant["status"] = tenant_data.status
    
    tenant["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
    return TenantResponse(**tenant)

@app.delete("/api/v1/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """Excluir empresa"""
    global tenants_db
    tenant = next((t for t in tenants_db if t["id"] == tenant_id), None)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    tenants_db = [t for t in tenants_db if t["id"] != tenant_id]
    return {"message": "Empresa excluída com sucesso"}

# CRUD de Business Units
@app.get("/api/v1/business-units", response_model=List[BusinessUnitResponse])
async def get_business_units(db: Session = Depends(get_db)):
    """Listar todas as BUs"""
    return [BusinessUnitResponse(**bu) for bu in business_units_db]

@app.get("/api/v1/business-units/{bu_id}", response_model=BusinessUnitResponse)
async def get_business_unit(bu_id: str, db: Session = Depends(get_db)):
    """Buscar BU por ID"""
    bu = next((b for b in business_units_db if b["id"] == bu_id), None)
    if not bu:
        raise HTTPException(status_code=404, detail="BU não encontrada")
    return BusinessUnitResponse(**bu)

@app.post("/api/v1/business-units", response_model=BusinessUnitResponse, status_code=201)
async def create_business_unit(bu_data: BusinessUnitCreate, db: Session = Depends(get_db)):
    """Criar nova BU"""
    global next_bu_id
    bu = {
        "id": str(next_bu_id),
        "tenant_id": bu_data.tenant_id,
        "name": bu_data.name,
        "code": bu_data.code,
        "status": bu_data.status,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d"),
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d")
    }
    business_units_db.append(bu)
    next_bu_id += 1
    return BusinessUnitResponse(**bu)

@app.put("/api/v1/business-units/{bu_id}", response_model=BusinessUnitResponse)
async def update_business_unit(bu_id: str, bu_data: BusinessUnitUpdate, db: Session = Depends(get_db)):
    """Atualizar BU"""
    bu = next((b for b in business_units_db if b["id"] == bu_id), None)
    if not bu:
        raise HTTPException(status_code=404, detail="BU não encontrada")
    
    if bu_data.tenant_id is not None:
        bu["tenant_id"] = bu_data.tenant_id
    if bu_data.name is not None:
        bu["name"] = bu_data.name
    if bu_data.code is not None:
        bu["code"] = bu_data.code
    if bu_data.status is not None:
        bu["status"] = bu_data.status
    
    bu["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
    return BusinessUnitResponse(**bu)

@app.delete("/api/v1/business-units/{bu_id}")
async def delete_business_unit(bu_id: str, db: Session = Depends(get_db)):
    """Excluir BU"""
    global business_units_db
    bu = next((b for b in business_units_db if b["id"] == bu_id), None)
    if not bu:
        raise HTTPException(status_code=404, detail="BU não encontrada")
    
    business_units_db = [b for b in business_units_db if b["id"] != bu_id]
    return {"message": "BU excluída com sucesso"}

# CRUD de Usuários - Usando banco de dados real se disponível, senão em memória
@app.get("/api/v1/users", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db)):
    """Listar todos os usuários"""
    if DB_AVAILABLE and db:
        try:
            users = db.query(User).all()
            return [
                UserResponse(
                    id=user.id,
                    name=f"{user.first_name} {user.last_name}",
                    email=user.email,
                    phone=user.phone or '(11) 99999-9999',  # Usar campo phone do banco
                    role=user.role,
                    status=user.status,
                    created_at=user.created_at.strftime("%Y-%m-%d") if user.created_at else "",
                    last_login=user.last_login.strftime("%Y-%m-%d") if user.last_login else None
                )
                for user in users
            ]
        except Exception as e:
            print(f"Database error: {e}")
            # Fallback para dados em memória
            pass
    
    # Dados em memória
    return [UserResponse(**user) for user in users_db]

@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Buscar usuário por ID"""
    if DB_AVAILABLE and db:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return UserResponse(
                    id=user.id,
                    name=f"{user.first_name} {user.last_name}",
                    email=user.email,
                    phone=user.phone or '(11) 99999-9999',  # Usar campo phone do banco
                    role=user.role,
                    status=user.status,
                    created_at=user.created_at.strftime("%Y-%m-%d") if user.created_at else "",
                    last_login=user.last_login.strftime("%Y-%m-%d") if user.last_login else None
                )
        except Exception as e:
            print(f"Database error: {e}")
    
    # Dados em memória
    user = next((u for u in users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return UserResponse(**user)

@app.post("/api/v1/users", response_model=UserResponse, status_code=201)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Criar novo usuário"""
    if DB_AVAILABLE and db:
        try:
            # Verificar se email já existe
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email já cadastrado")
            
            # Separar nome completo em primeiro e último nome
            name_parts = user_data.name.split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            # Criar novo usuário
            new_user = User(
                tenant_id="1",
                username=user_data.email,
                email=user_data.email,
                first_name=first_name,
                last_name=last_name,
                phone=user_data.phone,  # Salvar telefone
                hashed_password="hashed_password_placeholder",
                role=user_data.role,
                status=user_data.status
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            return UserResponse(
                id=new_user.id,
                name=f"{new_user.first_name} {new_user.last_name}",
                email=new_user.email,
                phone=user_data.phone,
                role=new_user.role,
                status=new_user.status,
                created_at=new_user.created_at.strftime("%Y-%m-%d") if new_user.created_at else "",
                last_login=None
            )
        except Exception as e:
            print(f"Database error: {e}")
            # Fallback para dados em memória
            pass
    
    # Dados em memória
    global next_user_id
    if any(u["email"] == user_data.email for u in users_db):
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    new_user = {
        "id": str(next_user_id),
        "name": user_data.name,
        "email": user_data.email,
        "phone": user_data.phone,
        "role": user_data.role,
        "status": user_data.status,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d"),
        "last_login": None
    }
    
    users_db.append(new_user)
    next_user_id += 1
    
    return UserResponse(**new_user)

@app.put("/api/v1/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, db: Session = Depends(get_db)):
    """Atualizar usuário"""
    if DB_AVAILABLE and db:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                if user_data.name is not None:
                    name_parts = user_data.name.split(" ", 1)
                    user.first_name = name_parts[0]
                    user.last_name = name_parts[1] if len(name_parts) > 1 else ""
                
                if user_data.email is not None:
                    user.email = user_data.email
                    user.username = user_data.email
                
                if user_data.phone is not None:
                    user.phone = user_data.phone
                
                if user_data.role is not None:
                    user.role = user_data.role
                
                if user_data.status is not None:
                    user.status = user_data.status
                
                db.commit()
                db.refresh(user)
                
                return UserResponse(
                    id=user.id,
                    name=f"{user.first_name} {user.last_name}",
                    email=user.email,
                    phone=user.phone or '(11) 99999-9999',  # Usar campo phone do banco
                    role=user.role,
                    status=user.status,
                    created_at=user.created_at.strftime("%Y-%m-%d") if user.created_at else "",
                    last_login=user.last_login.strftime("%Y-%m-%d") if user.last_login else None
                )
        except Exception as e:
            print(f"Database error: {e}")
    
    # Dados em memória
    user_index = next((i for i, u in enumerate(users_db) if u["id"] == user_id), None)
    if user_index is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if user_data.name is not None:
        users_db[user_index]["name"] = user_data.name
    if user_data.email is not None:
        users_db[user_index]["email"] = user_data.email
    if user_data.phone is not None:
        users_db[user_index]["phone"] = user_data.phone
    if user_data.role is not None:
        users_db[user_index]["role"] = user_data.role
    if user_data.status is not None:
        users_db[user_index]["status"] = user_data.status
    
    return UserResponse(**users_db[user_index])

@app.delete("/api/v1/users/{user_id}")
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    """Deletar usuário"""
    if DB_AVAILABLE and db:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                db.delete(user)
                db.commit()
                return {"message": f"Usuário {user_id} deletado com sucesso"}
        except Exception as e:
            print(f"Database error: {e}")
    
    # Dados em memória
    user_index = next((i for i, u in enumerate(users_db) if u["id"] == user_id), None)
    if user_index is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    users_db.pop(user_index)
    return {"message": f"Usuário {user_id} deletado com sucesso"}

@app.get("/api/v1/financial/transactions")
async def get_transactions():
    return [
            {"id": 1, "description": "Vendas Cursos", "amount": 1000.00, "type": "credit"},
            {"id": 2, "description": "Salário", "amount": 5000.00, "type": "debit"}
        ]

@app.get("/api/v1/financial/accounts")
async def get_accounts():
    return [
        {"id": 1, "name": "Conta Corrente", "balance": 5000.00},
        {"id": 2, "name": "Poupança", "balance": 10000.00}
    ]

@app.get("/api/v1/financial/groups")
async def get_groups():
    return [
        {"id": 1, "name": "Receitas", "description": "Grupo de receitas"},
        {"id": 2, "name": "Despesas", "description": "Grupo de despesas"}
    ]

@app.get("/api/v1/financial/account-subgroups")
async def get_subgroups():
    return [
        {"id": 1, "name": "Vendas", "group_id": 1},
        {"id": 2, "name": "Salários", "group_id": 2}
    ]

@app.get("/api/v1/financial/forecasts")
async def get_forecasts():
    return [
        {"id": 1, "account_id": 1, "amount": 5000.00, "description": "Previsão de vendas"}
    ]

@app.get("/api/v1/financial/cash-flow")
async def get_cash_flow():
    return [
        {"date": "2024-01-01", "opening_balance": 10000, "total_revenue": 5000, "total_expenses": 3000, "closing_balance": 12000}
    ]

@app.get("/api/v1/reports/cash-flow")
async def get_cash_flow():
    return {
        "cash_flow": [
            {"month": "Jan", "income": 50000, "expense": 30000, "balance": 20000},
            {"month": "Fev", "income": 60000, "expense": 35000, "balance": 25000}
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
