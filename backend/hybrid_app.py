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
from app.database import get_db, engine
from app.models.auth import User, Tenant, BusinessUnit, UserTenantAccess, UserBusinessUnitAccess, Base as AuthBase

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

# Modelos Pydantic para permissões
class UserTenantAccessCreate(BaseModel):
    user_id: str
    tenant_id: str
    can_read: bool = True
    can_write: bool = False
    can_delete: bool = False
    can_manage_users: bool = False

class UserTenantAccessUpdate(BaseModel):
    can_read: Optional[bool] = None
    can_write: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_manage_users: Optional[bool] = None

class UserTenantAccessResponse(BaseModel):
    id: str
    user_id: str
    tenant_id: str
    tenant_name: str
    can_read: bool
    can_write: bool
    can_delete: bool
    can_manage_users: bool
    created_at: str
    updated_at: str

class UserBusinessUnitAccessCreate(BaseModel):
    user_id: str
    business_unit_id: str
    can_read: bool = True
    can_write: bool = False
    can_delete: bool = False
    can_manage_users: bool = False

class UserBusinessUnitAccessUpdate(BaseModel):
    can_read: Optional[bool] = None
    can_write: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_manage_users: Optional[bool] = None

class UserBusinessUnitAccessResponse(BaseModel):
    id: str
    user_id: str
    business_unit_id: str
    business_unit_name: str
    tenant_name: str
    can_read: bool
    can_write: bool
    can_delete: bool
    can_manage_users: bool
    created_at: str
    updated_at: str

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://finaflow.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criar tabelas no banco de dados
try:
    AuthBase.metadata.create_all(bind=engine)
    print("✅ Database tables created")
except Exception as e:
    print(f"❌ Could not create database tables: {e}")
    raise e

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

# Configuração JWT
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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
    tenants = db.query(Tenant).all()
    return [TenantResponse(
        id=tenant.id,
        name=tenant.name,
        domain=tenant.domain,
        status=tenant.status,
        created_at=tenant.created_at.strftime("%Y-%m-%d") if tenant.created_at else "",
        updated_at=tenant.updated_at.strftime("%Y-%m-%d") if tenant.updated_at else ""
    ) for tenant in tenants]

@app.get("/api/v1/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """Buscar empresa por ID"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        domain=tenant.domain,
        status=tenant.status,
        created_at=tenant.created_at.strftime("%Y-%m-%d") if tenant.created_at else "",
        updated_at=tenant.updated_at.strftime("%Y-%m-%d") if tenant.updated_at else ""
    )

@app.post("/api/v1/tenants", response_model=TenantResponse, status_code=201)
async def create_tenant(tenant_data: TenantCreate, db: Session = Depends(get_db)):
    """Criar nova empresa"""
    tenant = Tenant(
        name=tenant_data.name,
        domain=tenant_data.domain,
        status=tenant_data.status
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        domain=tenant.domain,
        status=tenant.status,
        created_at=tenant.created_at.strftime("%Y-%m-%d") if tenant.created_at else "",
        updated_at=tenant.updated_at.strftime("%Y-%m-%d") if tenant.updated_at else ""
    )

@app.put("/api/v1/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, tenant_data: TenantUpdate, db: Session = Depends(get_db)):
    """Atualizar empresa"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    if tenant_data.name is not None:
        tenant.name = tenant_data.name
    if tenant_data.domain is not None:
        tenant.domain = tenant_data.domain
    if tenant_data.status is not None:
        tenant.status = tenant_data.status
    
    db.commit()
    db.refresh(tenant)
    
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        domain=tenant.domain,
        status=tenant.status,
        created_at=tenant.created_at.strftime("%Y-%m-%d") if tenant.created_at else "",
        updated_at=tenant.updated_at.strftime("%Y-%m-%d") if tenant.updated_at else ""
    )

@app.delete("/api/v1/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """Excluir empresa"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    db.delete(tenant)
    db.commit()
    return {"message": "Empresa excluída com sucesso"}

# CRUD de Business Units
@app.get("/api/v1/business-units", response_model=List[BusinessUnitResponse])
async def get_business_units(db: Session = Depends(get_db)):
    """Listar todas as BUs"""
    business_units = db.query(BusinessUnit).all()
    return [BusinessUnitResponse(
        id=bu.id,
        tenant_id=bu.tenant_id,
        name=bu.name,
        code=bu.code,
        status=bu.status,
        created_at=bu.created_at.strftime("%Y-%m-%d") if bu.created_at else "",
        updated_at=bu.updated_at.strftime("%Y-%m-%d") if bu.updated_at else ""
    ) for bu in business_units]

@app.get("/api/v1/business-units/{bu_id}", response_model=BusinessUnitResponse)
async def get_business_unit(bu_id: str, db: Session = Depends(get_db)):
    """Buscar BU por ID"""
    bu = db.query(BusinessUnit).filter(BusinessUnit.id == bu_id).first()
    if not bu:
        raise HTTPException(status_code=404, detail="BU não encontrada")
    
    return BusinessUnitResponse(
        id=bu.id,
        tenant_id=bu.tenant_id,
        name=bu.name,
        code=bu.code,
        status=bu.status,
        created_at=bu.created_at.strftime("%Y-%m-%d") if bu.created_at else "",
        updated_at=bu.updated_at.strftime("%Y-%m-%d") if bu.updated_at else ""
    )

@app.post("/api/v1/business-units", response_model=BusinessUnitResponse, status_code=201)
async def create_business_unit(bu_data: BusinessUnitCreate, db: Session = Depends(get_db)):
    """Criar nova BU"""
    bu = BusinessUnit(
        tenant_id=bu_data.tenant_id,
        name=bu_data.name,
        code=bu_data.code,
        status=bu_data.status
    )
    db.add(bu)
    db.commit()
    db.refresh(bu)
    
    return BusinessUnitResponse(
        id=bu.id,
        tenant_id=bu.tenant_id,
        name=bu.name,
        code=bu.code,
        status=bu.status,
        created_at=bu.created_at.strftime("%Y-%m-%d") if bu.created_at else "",
        updated_at=bu.updated_at.strftime("%Y-%m-%d") if bu.updated_at else ""
    )

@app.put("/api/v1/business-units/{bu_id}", response_model=BusinessUnitResponse)
async def update_business_unit(bu_id: str, bu_data: BusinessUnitUpdate, db: Session = Depends(get_db)):
    """Atualizar BU"""
    bu = db.query(BusinessUnit).filter(BusinessUnit.id == bu_id).first()
    if not bu:
        raise HTTPException(status_code=404, detail="BU não encontrada")
    
    if bu_data.tenant_id is not None:
        bu.tenant_id = bu_data.tenant_id
    if bu_data.name is not None:
        bu.name = bu_data.name
    if bu_data.code is not None:
        bu.code = bu_data.code
    if bu_data.status is not None:
        bu.status = bu_data.status
    
    db.commit()
    db.refresh(bu)
    
    return BusinessUnitResponse(
        id=bu.id,
        tenant_id=bu.tenant_id,
        name=bu.name,
        code=bu.code,
        status=bu.status,
        created_at=bu.created_at.strftime("%Y-%m-%d") if bu.created_at else "",
        updated_at=bu.updated_at.strftime("%Y-%m-%d") if bu.updated_at else ""
    )

@app.delete("/api/v1/business-units/{bu_id}")
async def delete_business_unit(bu_id: str, db: Session = Depends(get_db)):
    """Excluir BU"""
    bu = db.query(BusinessUnit).filter(BusinessUnit.id == bu_id).first()
    if not bu:
        raise HTTPException(status_code=404, detail="BU não encontrada")
    
    db.delete(bu)
    db.commit()
    return {"message": "BU excluída com sucesso"}

# CRUD de Usuários
@app.get("/api/v1/users", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db)):
    """Listar todos os usuários"""
    users = db.query(User).all()
    return [
        UserResponse(
            id=user.id,
            name=f"{user.first_name} {user.last_name}",
            email=user.email,
            phone=user.phone or '(11) 99999-9999',
            role=user.role,
            status=user.status,
            created_at=user.created_at.strftime("%Y-%m-%d") if user.created_at else "",
            last_login=user.last_login.strftime("%Y-%m-%d") if user.last_login else None
        )
        for user in users
    ]

@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Buscar usuário por ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return UserResponse(
        id=user.id,
        name=f"{user.first_name} {user.last_name}",
        email=user.email,
        phone=user.phone or '(11) 99999-9999',
        role=user.role,
        status=user.status,
        created_at=user.created_at.strftime("%Y-%m-%d") if user.created_at else "",
        last_login=user.last_login.strftime("%Y-%m-%d") if user.last_login else None
    )

@app.post("/api/v1/users", response_model=UserResponse, status_code=201)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Criar novo usuário"""
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
        phone=user_data.phone,
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

@app.put("/api/v1/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, db: Session = Depends(get_db)):
    """Atualizar usuário"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
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
        phone=user.phone or '(11) 99999-9999',
        role=user.role,
        status=user.status,
        created_at=user.created_at.strftime("%Y-%m-%d") if user.created_at else "",
        last_login=user.last_login.strftime("%Y-%m-%d") if user.last_login else None
    )

@app.delete("/api/v1/users/{user_id}")
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    """Deletar usuário"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    db.delete(user)
    db.commit()
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

# ============================================================================
# ENDPOINTS DE PERMISSÕES
# ============================================================================

@app.get("/api/v1/permissions/tenants/{user_id}", response_model=List[UserTenantAccessResponse])
async def get_user_tenant_permissions(user_id: str, db: Session = Depends(get_db)):
    """Lista permissões de um usuário em empresas"""
    # Buscar permissões do usuário
    permissions = db.query(UserTenantAccess).filter(UserTenantAccess.user_id == user_id).all()
    
    # Formatar resposta
    result = []
    for perm in permissions:
        # Buscar nome da empresa
        tenant = db.query(Tenant).filter(Tenant.id == perm.tenant_id).first()
        tenant_name = tenant.name if tenant else "Empresa não encontrada"
        
        result.append(UserTenantAccessResponse(
            id=perm.id,
            user_id=perm.user_id,
            tenant_id=perm.tenant_id,
            tenant_name=tenant_name,
            can_read=perm.can_read,
            can_write=perm.can_write,
            can_delete=perm.can_delete,
            can_manage_users=perm.can_manage_users,
            created_at=perm.created_at.strftime("%Y-%m-%d") if perm.created_at else "",
            updated_at=perm.updated_at.strftime("%Y-%m-%d") if perm.updated_at else ""
        ))
    
    return result

@app.post("/api/v1/permissions/tenants", response_model=UserTenantAccessResponse)
async def create_user_tenant_permission(permission_data: UserTenantAccessCreate, db: Session = Depends(get_db)):
    """Cria permissão de usuário em uma empresa"""
    # Verificar se já existe permissão
    existing = db.query(UserTenantAccess).filter(
        UserTenantAccess.user_id == permission_data.user_id,
        UserTenantAccess.tenant_id == permission_data.tenant_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Permissão já existe para este usuário nesta empresa")
    
    # Criar nova permissão
    permission = UserTenantAccess(
        user_id=permission_data.user_id,
        tenant_id=permission_data.tenant_id,
        can_read=permission_data.can_read,
        can_write=permission_data.can_write,
        can_delete=permission_data.can_delete,
        can_manage_users=permission_data.can_manage_users
    )
    
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
    # Buscar nome da empresa
    tenant = db.query(Tenant).filter(Tenant.id == permission_data.tenant_id).first()
    tenant_name = tenant.name if tenant else "Empresa não encontrada"
    
    return UserTenantAccessResponse(
        id=permission.id,
        user_id=permission.user_id,
        tenant_id=permission.tenant_id,
        tenant_name=tenant_name,
        can_read=permission.can_read,
        can_write=permission.can_write,
        can_delete=permission.can_delete,
        can_manage_users=permission.can_manage_users,
        created_at=permission.created_at.strftime("%Y-%m-%d") if permission.created_at else "",
        updated_at=permission.updated_at.strftime("%Y-%m-%d") if permission.updated_at else ""
    )

@app.put("/api/v1/permissions/tenants/{permission_id}", response_model=UserTenantAccessResponse)
async def update_user_tenant_permission(permission_id: str, permission_data: UserTenantAccessUpdate, db: Session = Depends(get_db)):
    """Atualiza permissão de usuário em uma empresa"""
    # Buscar permissão
    permission = db.query(UserTenantAccess).filter(UserTenantAccess.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permissão não encontrada")
    
    # Atualizar permissões
    if permission_data.can_read is not None:
        permission.can_read = permission_data.can_read
    if permission_data.can_write is not None:
        permission.can_write = permission_data.can_write
    if permission_data.can_delete is not None:
        permission.can_delete = permission_data.can_delete
    if permission_data.can_manage_users is not None:
        permission.can_manage_users = permission_data.can_manage_users
    
    db.commit()
    db.refresh(permission)
    
    # Buscar nome da empresa
    tenant = db.query(Tenant).filter(Tenant.id == permission.tenant_id).first()
    tenant_name = tenant.name if tenant else "Empresa não encontrada"
    
    return UserTenantAccessResponse(
        id=permission.id,
        user_id=permission.user_id,
        tenant_id=permission.tenant_id,
        tenant_name=tenant_name,
        can_read=permission.can_read,
        can_write=permission.can_write,
        can_delete=permission.can_delete,
        can_manage_users=permission.can_manage_users,
        created_at=permission.created_at.strftime("%Y-%m-%d") if permission.created_at else "",
        updated_at=permission.updated_at.strftime("%Y-%m-%d") if permission.updated_at else ""
    )

@app.delete("/api/v1/permissions/tenants/{permission_id}")
async def delete_user_tenant_permission(permission_id: str, db: Session = Depends(get_db)):
    """Remove permissão de usuário em uma empresa"""
    permission = db.query(UserTenantAccess).filter(UserTenantAccess.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permissão não encontrada")
    
    db.delete(permission)
    db.commit()
    return {"message": "Permissão removida com sucesso"}

@app.get("/api/v1/permissions/business-units/{user_id}", response_model=List[UserBusinessUnitAccessResponse])
async def get_user_business_unit_permissions(user_id: str, db: Session = Depends(get_db)):
    """Lista permissões de um usuário em BUs"""
    # Buscar permissões do usuário
    permissions = [p for p in business_unit_permissions_db if p["user_id"] == user_id]
    
    # Formatar resposta
    result = []
    for perm in permissions:
        # Buscar nome da BU e empresa
        bu_name = "BU não encontrada"
        tenant_name = "Empresa não encontrada"
        
        for bu in business_units_db:
            if bu["id"] == perm["business_unit_id"]:
                bu_name = bu["name"]
                # Buscar empresa
                for tenant in tenants_db:
                    if tenant["id"] == bu["tenant_id"]:
                        tenant_name = tenant["name"]
                        break
                break
        
        result.append(UserBusinessUnitAccessResponse(
            id=perm["id"],
            user_id=perm["user_id"],
            business_unit_id=perm["business_unit_id"],
            business_unit_name=bu_name,
            tenant_name=tenant_name,
            can_read=perm["can_read"],
            can_write=perm["can_write"],
            can_delete=perm["can_delete"],
            can_manage_users=perm["can_manage_users"],
            created_at=perm["created_at"],
            updated_at=perm["updated_at"]
        ))
    
    return result

@app.post("/api/v1/permissions/business-units", response_model=UserBusinessUnitAccessResponse)
async def create_user_business_unit_permission(permission_data: UserBusinessUnitAccessCreate, db: Session = Depends(get_db)):
    """Cria permissão de usuário em uma BU"""
    global next_permission_id
    
    # Verificar se já existe permissão
    existing = next((p for p in business_unit_permissions_db 
                    if p["user_id"] == permission_data.user_id 
                    and p["business_unit_id"] == permission_data.business_unit_id), None)
    
    if existing:
        raise HTTPException(status_code=400, detail="Permissão já existe para este usuário nesta BU")
    
    # Criar nova permissão
    permission = {
        "id": str(next_permission_id),
        "user_id": permission_data.user_id,
        "business_unit_id": permission_data.business_unit_id,
        "can_read": permission_data.can_read,
        "can_write": permission_data.can_write,
        "can_delete": permission_data.can_delete,
        "can_manage_users": permission_data.can_manage_users,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d"),
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d")
    }
    
    business_unit_permissions_db.append(permission)
    next_permission_id += 1
    
    # Buscar nome da BU e empresa
    bu_name = "BU não encontrada"
    tenant_name = "Empresa não encontrada"
    
    for bu in business_units_db:
        if bu["id"] == permission_data.business_unit_id:
            bu_name = bu["name"]
            # Buscar empresa
            for tenant in tenants_db:
                if tenant["id"] == bu["tenant_id"]:
                    tenant_name = tenant["name"]
                    break
            break
    
    return UserBusinessUnitAccessResponse(
        id=permission["id"],
        user_id=permission["user_id"],
        business_unit_id=permission["business_unit_id"],
        business_unit_name=bu_name,
        tenant_name=tenant_name,
        can_read=permission["can_read"],
        can_write=permission["can_write"],
        can_delete=permission["can_delete"],
        can_manage_users=permission["can_manage_users"],
        created_at=permission["created_at"],
        updated_at=permission["updated_at"]
    )

@app.put("/api/v1/permissions/business-units/{permission_id}", response_model=UserBusinessUnitAccessResponse)
async def update_user_business_unit_permission(permission_id: str, permission_data: UserBusinessUnitAccessUpdate, db: Session = Depends(get_db)):
    """Atualiza permissão de usuário em uma BU"""
    # Buscar permissão
    permission = next((p for p in business_unit_permissions_db if p["id"] == permission_id), None)
    if not permission:
        raise HTTPException(status_code=404, detail="Permissão não encontrada")
    
    # Atualizar permissões
    if permission_data.can_read is not None:
        permission["can_read"] = permission_data.can_read
    if permission_data.can_write is not None:
        permission["can_write"] = permission_data.can_write
    if permission_data.can_delete is not None:
        permission["can_delete"] = permission_data.can_delete
    if permission_data.can_manage_users is not None:
        permission["can_manage_users"] = permission_data.can_manage_users
    
    permission["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Buscar nome da BU e empresa
    bu_name = "BU não encontrada"
    tenant_name = "Empresa não encontrada"
    
    for bu in business_units_db:
        if bu["id"] == permission["business_unit_id"]:
            bu_name = bu["name"]
            # Buscar empresa
            for tenant in tenants_db:
                if tenant["id"] == bu["tenant_id"]:
                    tenant_name = tenant["name"]
                    break
            break
    
    return UserBusinessUnitAccessResponse(
        id=permission["id"],
        user_id=permission["user_id"],
        business_unit_id=permission["business_unit_id"],
        business_unit_name=bu_name,
        tenant_name=tenant_name,
        can_read=permission["can_read"],
        can_write=permission["can_write"],
        can_delete=permission["can_delete"],
        can_manage_users=permission["can_manage_users"],
        created_at=permission["created_at"],
        updated_at=permission["updated_at"]
    )

@app.delete("/api/v1/permissions/business-units/{permission_id}")
async def delete_user_business_unit_permission(permission_id: str, db: Session = Depends(get_db)):
    """Remove permissão de usuário em uma BU"""
    global business_unit_permissions_db
    
    permission = next((p for p in business_unit_permissions_db if p["id"] == permission_id), None)
    if not permission:
        raise HTTPException(status_code=404, detail="Permissão não encontrada")
    
    business_unit_permissions_db = [p for p in business_unit_permissions_db if p["id"] != permission_id]
    return {"message": "Permissão removida com sucesso"}

@app.get("/api/v1/permissions/my-access")
async def get_my_access(db: Session = Depends(get_db)):
    """Retorna as permissões do usuário atual (mock)"""
    return {
        "user_id": "current-user-id",
        "role": "super_admin",
        "accessible_tenants": ["1", "2"],
        "accessible_business_units": ["1", "2", "3"]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
