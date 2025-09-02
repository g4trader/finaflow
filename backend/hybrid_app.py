from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import jwt
import datetime
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer

# Importar configurações do banco de dados
from app.database import get_db, engine
from app.models.auth import User, Tenant, BusinessUnit, UserTenantAccess, UserBusinessUnitAccess, Base as AuthBase
from app.models.chart_of_accounts import ChartAccountGroup, ChartAccountSubgroup, ChartAccount, BusinessUnitChartAccount, Base as ChartBase
from app.models.financial_transactions import FinancialTransaction, TransactionType, TransactionStatus, Base as FinancialBase
from app.models.permissions import Permission, UserPermission, PermissionType
from app.services.permissions import PermissionService
import bcrypt

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
    ChartBase.metadata.create_all(bind=engine)
    FinancialBase.metadata.create_all(bind=engine)
    print("✅ Database tables created")
except Exception as e:
    print(f"❌ Could not create database tables: {e}")
    raise e

# Dados mock para permissões (temporário)
business_unit_permissions_db = [
    {
        "id": "perm-1",
        "user_id": "0ea47945-21cf-4ed2-b99c-af9609eeb328",  # lucianoterresrosa@gmail.com
        "business_unit_id": "4ff6ce0c-b64c-410e-8a8c-62165916bc4f",  # G4 Matriz
        "tenant_id": "b410c4a2-0ab9-4624-89ea-05160ad55acb",  # G4 Mkt
        "can_read": True,
        "can_write": True,
        "can_delete": True,
        "can_manage_users": True,
        "created_at": "2025-01-01",
        "updated_at": "2025-01-01"
    }
]
next_permission_id = 1

# Dados mock para tenants e business units (temporário)
tenants_db = [
    {
        "id": "21564896-889d-4b5c-b431-dfa7ef4f0387",
        "name": "FinaFlow",
        "domain": "finaflow.com",
        "status": "active"
    }
]

business_units_db = [
    {
        "id": "d22ceace-80e8-4c0f-9000-88d910daaa1d",
        "name": "Matriz",
        "code": "MAT",
        "tenant_id": "21564896-889d-4b5c-b431-dfa7ef4f0387",
        "status": "active"
    },
    {
        "id": "4ff6ce0c-b64c-410e-8a8c-62165916bc4f",
        "name": "G4 Matriz",
        "code": "G4MAT",
        "tenant_id": "b410c4a2-0ab9-4624-89ea-05160ad55acb",
        "status": "active"
    }
]

# Modelos Pydantic para compatibilidade com o frontend
class UserCreate(BaseModel):
    name: str
    email: str
    phone: str
    password: str  # Senha obrigatória
    role: str = "user"
    status: str = "active"

class UserSetPassword(BaseModel):
    password: str

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

# Modelos Pydantic para Plano de Contas
class AccountGroupCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    tenant_id: str
    business_unit_id: str
    status: str = "active"

class AccountGroupUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class AccountGroupResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str]
    tenant_id: str
    business_unit_id: str
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class AccountSubgroupCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    group_id: str
    tenant_id: str
    business_unit_id: str
    status: str = "active"

class AccountSubgroupUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class AccountSubgroupResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str]
    group_id: str
    group_name: str
    tenant_id: str
    business_unit_id: str
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class ChartAccountCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    subgroup_id: str
    tenant_id: str
    business_unit_id: str
    is_active: bool = True
    status: str = "active"

class ChartAccountUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    status: Optional[str] = None

class ChartAccountResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str]
    subgroup_id: str
    subgroup_name: str
    group_id: str
    group_name: str
    tenant_id: str
    business_unit_id: str
    is_active: bool
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

# Configuração JWT
SECRET_KEY = "finaflow-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Funções de segurança simplificadas
def hash_password(password: str) -> str:
    """Hash de senha usando bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# Função para verificar token JWT
def get_current_user(token: str = Depends(HTTPBearer())):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido - username não encontrado")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Erro na autenticação: {str(e)}")

@app.get("/")
async def root():
    return {"message": "FinaFlow Backend API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Backend is running"}

@app.get("/test")
async def test_endpoint():
    return {"status": "ok", "message": "Test endpoint working"}

@app.get("/debug/tables")
async def debug_tables(db: Session = Depends(get_db)):
    """Debug endpoint para verificar estrutura das tabelas"""
    try:
        # Verificar se as tabelas existem
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        tables = inspector.get_table_names()
        table_info = {}
        
        for table in tables:
            if table.startswith('chart_account'):
                columns = inspector.get_columns(table)
                table_info[table] = [col['name'] for col in columns]
        
        return {
            "tables": tables,
            "chart_account_tables": table_info
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/debug/recreate-chart-tables")
async def recreate_chart_tables(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recreia as tabelas do plano de contas"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Sem permissão para recriar tabelas")
        
        # Remover tabelas antigas com CASCADE
        from sqlalchemy import text
        
        # Remover tabelas específicas do plano de contas
        db.execute(text("DROP TABLE IF EXISTS chart_accounts CASCADE"))
        db.execute(text("DROP TABLE IF EXISTS chart_account_subgroups CASCADE"))
        db.execute(text("DROP TABLE IF EXISTS chart_account_groups CASCADE"))
        db.execute(text("DROP TABLE IF EXISTS business_unit_chart_accounts CASCADE"))
        
        # Commit para garantir que as tabelas foram removidas
        db.commit()
        
        # Recriar tabelas
        ChartBase.metadata.create_all(bind=engine)
        
        # Commit para garantir que as tabelas foram criadas
        db.commit()
        
        return {"message": "Tabelas do plano de contas recriadas com sucesso"}
        
    except Exception as e:
        return {"error": str(e)}

from fastapi import Form

@app.post("/api/v1/auth/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Login com autenticação real"""
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username e password são obrigatórios")
    
    try:
        # Buscar usuário no banco
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        # Verificar senha
        if not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        # Criar payload do JWT
        # Verificar se o usuário tem múltiplas BUs disponíveis
        user_permissions = db.query(UserBusinessUnitAccess).filter(
            UserBusinessUnitAccess.user_id == user.id
        ).all()
        
        # Se tem múltiplas BUs, não incluir business_unit_id no token inicial
        should_include_bu = True
        if len(user_permissions) > 1:
            should_include_bu = False
        
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "tenant_id": str(user.tenant_id),
            "business_unit_id": str(user.business_unit_id) if user.business_unit_id and should_include_bu else None,
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
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/v1/auth/user-info")
async def get_user_info(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna informações completas do usuário logado"""
    user_id = current_user.get("sub")
    tenant_id = current_user.get("tenant_id")
    business_unit_id = current_user.get("business_unit_id")
    
    # Buscar informações da empresa e BU
    tenant_name = "Empresa não encontrada"
    business_unit_name = "BU não encontrada"
    
    if tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if tenant:
            tenant_name = tenant.name
    
    if business_unit_id:
        business_unit = db.query(BusinessUnit).filter(BusinessUnit.id == business_unit_id).first()
        if business_unit:
            business_unit_name = business_unit.name
    
    return {
        "user_id": user_id,
        "username": current_user.get("username"),
        "email": current_user.get("email"),
        "first_name": current_user.get("first_name"),
        "last_name": current_user.get("last_name"),
        "role": current_user.get("role"),
        "tenant_id": tenant_id,
        "tenant_name": tenant_name,
        "business_unit_id": business_unit_id,
        "business_unit_name": business_unit_name
    }



@app.get("/api/v1/auth/user-business-units")
async def get_user_business_units(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna as BUs disponíveis para o usuário logado"""
    user_id = current_user.get("sub")
    user_role = current_user.get("role")
    
    # Se é super_admin, retornar todas as BUs
    if user_role == "super_admin":
        business_units = db.query(BusinessUnit).all()
        available_bus = []
        for bu in business_units:
            tenant = db.query(Tenant).filter(Tenant.id == bu.tenant_id).first()
            available_bus.append({
                "id": str(bu.id),
                "name": bu.name,
                "code": bu.code,
                "tenant_id": str(bu.tenant_id),
                "tenant_name": tenant.name if tenant else "Empresa não encontrada",
                "permissions": {
                    "can_read": True,
                    "can_write": True,
                    "can_delete": True,
                    "can_manage_users": True
                }
            })
        return available_bus
    
    # Buscar permissões reais do usuário no banco de dados
    user_permissions = db.query(UserBusinessUnitAccess).filter(
        UserBusinessUnitAccess.user_id == user_id
    ).all()
    
    # Se não tem permissões específicas e não é admin, retornar vazio
    if not user_permissions and user_role != "admin":
        return []
    
    # Se é admin mas não tem permissões específicas, retornar todas as BUs
    if not user_permissions and user_role == "admin":
        business_units = db.query(BusinessUnit).all()
        available_bus = []
        for bu in business_units:
            tenant = db.query(Tenant).filter(Tenant.id == bu.tenant_id).first()
            available_bus.append({
                "id": str(bu.id),
                "name": bu.name,
                "code": bu.code,
                "tenant_id": str(bu.tenant_id),
                "tenant_name": tenant.name if tenant else "Empresa não encontrada",
                "permissions": {
                    "can_read": True,
                    "can_write": True,
                    "can_delete": True,
                    "can_manage_users": True
                }
            })
        return available_bus
    
    # Se tem permissões específicas, retornar apenas essas (mesmo sendo admin)
    if user_permissions:
        available_bus = []
        for permission in user_permissions:
            bu = db.query(BusinessUnit).filter(BusinessUnit.id == permission.business_unit_id).first()
            if bu:
                tenant = db.query(Tenant).filter(Tenant.id == bu.tenant_id).first()
                available_bus.append({
                    "id": str(bu.id),
                    "name": bu.name,
                    "code": bu.code,
                    "tenant_id": str(bu.tenant_id),
                    "tenant_name": tenant.name if tenant else "Empresa não encontrada",
                    "permissions": {
                        "can_read": permission.can_read,
                        "can_write": permission.can_write,
                        "can_delete": permission.can_delete,
                        "can_manage_users": permission.can_manage_users
                    }
                })
        return available_bus
    


@app.post("/api/v1/auth/create-superadmin")
async def create_superadmin(db: Session = Depends(get_db)):
    """Criar usuário superadmin inicial (endpoint temporário)"""
    # Verificar se já existe um superadmin
    existing_admin = db.query(User).filter(User.role == "super_admin").first()
    if existing_admin:
        return {"message": "Superadmin já existe", "username": existing_admin.username, "email": existing_admin.email}
    
    # Buscar o tenant padrão ou criar
    default_tenant = db.query(Tenant).first()
    if not default_tenant:
        default_tenant = Tenant(
            name="FinaFlow",
            domain="finaflow.com",
            status="active"
        )
        db.add(default_tenant)
        db.commit()
        db.refresh(default_tenant)
    
    # Criar superadmin
    superadmin_password = "Admin@123"
    hashed_password = hash_password(superadmin_password)
    
    superadmin = User(
        tenant_id=default_tenant.id,
        username="admin",
        email="admin@finaflow.com",
        first_name="Super",
        last_name="Admin",
        phone="(11) 99999-9999",
        hashed_password=hashed_password,
        role="super_admin",
        status="active"
    )
    
    db.add(superadmin)
    db.commit()
    db.refresh(superadmin)
    
    return {
        "message": "Superadmin criado com sucesso",
        "username": "admin",
        "email": "admin@finaflow.com",
        "password": superadmin_password,
        "role": "super_admin"
    }

@app.post("/api/v1/auth/reset-superadmin-password")
async def reset_superadmin_password(db: Session = Depends(get_db)):
    """Reset da senha do superadmin (endpoint temporário)"""
    # Buscar o superadmin
    superadmin = db.query(User).filter(User.role == "super_admin").first()
    if not superadmin:
        raise HTTPException(status_code=404, detail="Superadmin não encontrado")
    
    # Definir nova senha
    new_password = "Admin@123"
    hashed_password = hash_password(new_password)
    
    superadmin.hashed_password = hashed_password
    db.commit()
    db.refresh(superadmin)
    
    return {
        "message": "Senha do superadmin resetada com sucesso",
        "username": superadmin.username,
        "email": superadmin.email,
        "password": new_password,
        "role": superadmin.role
    }

@app.post("/api/v1/auth/select-business-unit")
async def select_business_unit(request: dict, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    business_unit_id = request.get("business_unit_id")
    if not business_unit_id:
        raise HTTPException(status_code=400, detail="business_unit_id é obrigatório")
    """Seleciona uma BU para o usuário e retorna um novo token com a BU selecionada"""
    user_id = current_user.get("sub")
    
    # Verificar se o usuário tem acesso à BU
    user_permissions = [p for p in business_unit_permissions_db if p["user_id"] == user_id and p["business_unit_id"] == business_unit_id]
    
    # Se não tem permissões específicas, permitir acesso (para admin)
    if not user_permissions:
        # Verificar se a BU existe
        bu = next((b for b in business_units_db if b["id"] == business_unit_id), None)
        if not bu:
            raise HTTPException(status_code=404, detail="Business Unit não encontrada")
        
        # Criar novo token com a BU selecionada
        new_payload = {
            "sub": user_id,
            "username": current_user.get("username"),
            "email": current_user.get("email"),
            "first_name": current_user.get("first_name"),
            "last_name": current_user.get("last_name"),
            "role": current_user.get("role"),
            "tenant_id": bu["tenant_id"],
            "business_unit_id": business_unit_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        
        secret_key = "finaflow-secret-key-2024"
        new_access_token = jwt.encode(new_payload, secret_key, algorithm="HS256")
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 1800,
            "selected_business_unit": {
                "id": bu["id"],
                "name": bu["name"],
                "code": bu["code"],
                "tenant_id": bu["tenant_id"]
            }
        }
    
    # Verificar permissões
    permission = user_permissions[0]
    if not permission["can_read"]:
        raise HTTPException(status_code=403, detail="Sem permissão de acesso a esta Business Unit")
    
    # Buscar informações da BU
    bu = next((b for b in business_units_db if b["id"] == business_unit_id), None)
    if not bu:
        raise HTTPException(status_code=404, detail="Business Unit não encontrada")
    
    # Criar novo token com a BU selecionada
    new_payload = {
        "sub": user_id,
        "username": current_user.get("username"),
        "email": current_user.get("email"),
        "first_name": current_user.get("first_name"),
        "last_name": current_user.get("last_name"),
        "role": current_user.get("role"),
        "tenant_id": bu["tenant_id"],
        "business_unit_id": business_unit_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    
    secret_key = "finaflow-secret-key-2024"
    new_access_token = jwt.encode(new_payload, secret_key, algorithm="HS256")
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": 1800,
        "selected_business_unit": {
            "id": bu["id"],
            "name": bu["name"],
            "code": bu["code"],
            "tenant_id": bu["tenant_id"]
        }
    }

# CRUD de Empresas (Tenants)
@app.get("/api/v1/tenants", response_model=List[TenantResponse])
async def get_tenants(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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

# Endpoint temporário sem autenticação para o frontend funcionar
@app.get("/api/v1/tenants-public", response_model=List[TenantResponse])
async def get_tenants_public(db: Session = Depends(get_db)):
    """Listar todas as empresas (sem autenticação - temporário)"""
    tenants = db.query(Tenant).all()
    return [TenantResponse(
        id=tenant.id,
        name=tenant.name,
        domain=tenant.domain,
        status=tenant.status,
        created_at=tenant.created_at.strftime("%Y-%m-%d") if tenant.created_at else "",
        updated_at=tenant.updated_at.strftime("%Y-%m-%d") if tenant.updated_at else ""
    ) for tenant in tenants]

@app.get("/api/v1/tenants-no-auth", response_model=List[TenantResponse])
async def get_tenants_no_auth(db: Session = Depends(get_db)):
    """Listar todas as empresas (sem autenticação para debug)"""
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
async def get_tenant(tenant_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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
async def create_tenant(tenant_data: TenantCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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
async def update_tenant(tenant_id: str, tenant_data: TenantUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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
async def delete_tenant(tenant_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Excluir empresa"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    db.delete(tenant)
    db.commit()
    return {"message": "Empresa excluída com sucesso"}

# CRUD de Business Units
@app.get("/api/v1/business-units", response_model=List[BusinessUnitResponse])
async def get_business_units(
    tenant_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Listar todas as BUs ou filtrar por tenant"""
    query = db.query(BusinessUnit)
    
    if tenant_id:
        query = query.filter(BusinessUnit.tenant_id == tenant_id)
    
    business_units = query.all()
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
async def get_business_unit(bu_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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
async def create_business_unit(bu_data: BusinessUnitCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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
async def update_business_unit(bu_id: str, bu_data: BusinessUnitUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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
async def delete_business_unit(bu_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Excluir BU"""
    bu = db.query(BusinessUnit).filter(BusinessUnit.id == bu_id).first()
    if not bu:
        raise HTTPException(status_code=404, detail="BU não encontrada")
    
    db.delete(bu)
    db.commit()
    return {"message": "BU excluída com sucesso"}

# CRUD de Usuários
@app.get("/api/v1/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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
async def get_user(user_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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
async def create_user(user_data: UserCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Criar novo usuário"""
    # Verificar se email já existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Separar nome completo em primeiro e último nome
    name_parts = user_data.name.split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    # Buscar o tenant padrão ou usar o tenant do usuário atual
    default_tenant = db.query(Tenant).first()
    if not default_tenant:
        # Criar tenant padrão se não existir
        default_tenant = Tenant(
            name="FinaFlow",
            domain="finaflow.com",
            status="active"
        )
        db.add(default_tenant)
        db.commit()
        db.refresh(default_tenant)
    
    # Hash da senha
    hashed_password = hash_password(user_data.password)
    
    # Criar novo usuário
    new_user = User(
        tenant_id=default_tenant.id,
        username=user_data.email,
        email=user_data.email,
        first_name=first_name,
        last_name=last_name,
        phone=user_data.phone,
        hashed_password=hashed_password,
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
async def update_user(user_id: str, user_data: UserUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Deletar usuário"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    db.delete(user)
    db.commit()
    return {"message": f"Usuário {user_id} deletado com sucesso"}

@app.post("/api/v1/users/{user_id}/set-password")
async def set_user_password(user_id: str, password_data: UserSetPassword, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Define senha para um usuário"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Hash da nova senha
    hashed_password = hash_password(password_data.password)
    user.hashed_password = hashed_password
    
    db.commit()
    db.refresh(user)
    
    return {"message": f"Senha definida com sucesso para o usuário {user.email}"}

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

@app.get("/api/v1/permissions")
async def get_permissions(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lista todas as permissões disponíveis"""
    try:
        permissions = db.query(Permission).filter(Permission.is_active == True).all()
        return [
            {
                "id": perm.id,
                "name": perm.name,
                "code": perm.code,
                "description": perm.description,
                "category": perm.category
            }
            for perm in permissions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar permissões: {str(e)}")

@app.post("/api/v1/permissions/initialize")
async def initialize_permissions(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Inicializa as permissões padrão do sistema"""
    try:
        # Verificar se o usuário atual é super_admin
        if current_user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Apenas super_admin pode inicializar permissões")
        
        success = PermissionService.initialize_permissions(db)
        if success:
            return {"message": "Permissões inicializadas com sucesso"}
        else:
            raise HTTPException(status_code=500, detail="Erro ao inicializar permissões")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao inicializar permissões: {str(e)}")

@app.get("/api/v1/permissions/users/{user_id}/business-units/{business_unit_id}")
async def get_user_permissions(
    user_id: str, 
    business_unit_id: str, 
    current_user: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Obtém permissões de um usuário para uma BU específica"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Sem permissão para visualizar permissões")
        
        # Buscar permissões específicas do usuário
        user_permissions = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.business_unit_id == business_unit_id
        ).all()
        
        # Se não há permissões específicas, retornar todas as permissões disponíveis com is_granted=False
        if not user_permissions:
            all_permissions = db.query(Permission).filter(Permission.is_active == True).all()
            result = []
            for perm in all_permissions:
                result.append({
                    "id": None,
                    "permission_code": perm.code,
                    "is_granted": False,
                    "granted_at": None
                })
            return result
        
        result = []
        for up in user_permissions:
            result.append({
                "id": up.id,
                "permission_code": up.permission_code,
                "is_granted": up.is_granted,
                "granted_at": up.granted_at.isoformat() if up.granted_at else None
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar permissões do usuário: {str(e)}")

@app.put("/api/v1/permissions/users/{user_id}/business-units/{business_unit_id}")
async def update_user_permissions(
    user_id: str,
    business_unit_id: str,
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza permissões de um usuário para uma BU específica"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Sem permissão para gerenciar permissões")
        
        permissions_data = request.get("permissions", [])
        
        for perm_data in permissions_data:
            permission_code = perm_data.get("permission_code")
            is_granted = perm_data.get("is_granted", False)
            
            if is_granted:
                PermissionService.grant_permission(
                    db, user_id, business_unit_id, permission_code, current_user.get("sub")
                )
            else:
                PermissionService.revoke_permission(db, user_id, business_unit_id, permission_code)
        
        return {"message": "Permissões atualizadas com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar permissões: {str(e)}")

# ENDPOINTS DO PLANO DE CONTAS
# ============================================================================

@app.post("/api/v1/chart-accounts/import")
async def import_chart_accounts(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Importa plano de contas do CSV"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Sem permissão para importar plano de contas")
        
        # Verificar se é um arquivo CSV
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
        
        # Ler conteúdo do arquivo
        csv_content = await file.read()
        csv_content = csv_content.decode('utf-8')
        
        # Importar usando o serviço
        from app.services.chart_accounts_importer import ChartAccountsImporter
        result = ChartAccountsImporter.import_chart_accounts(db, csv_content)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao importar plano de contas: {str(e)}")

@app.get("/api/v1/chart-accounts/groups")
async def get_chart_account_groups(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todos os grupos do plano de contas"""
    try:
        groups = db.query(ChartAccountGroup).filter(ChartAccountGroup.is_active == True).all()
        return [
            {
                "id": group.id,
                "code": group.code,
                "name": group.name,
                "description": group.description,
                "is_active": group.is_active,
                "created_at": group.created_at.isoformat(),
                "updated_at": group.updated_at.isoformat()
            }
            for group in groups
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar grupos: {str(e)}")

@app.get("/api/v1/chart-accounts/subgroups")
async def get_chart_account_subgroups(
    group_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista subgrupos do plano de contas"""
    try:
        query = db.query(ChartAccountSubgroup).filter(ChartAccountSubgroup.is_active == True)
        
        if group_id:
            query = query.filter(ChartAccountSubgroup.group_id == group_id)
        
        subgroups = query.all()
        return [
            {
                "id": subgroup.id,
                "code": subgroup.code,
                "name": subgroup.name,
                "description": subgroup.description,
                "group_id": subgroup.group_id,
                "group_name": subgroup.group.name,
                "is_active": subgroup.is_active,
                "created_at": subgroup.created_at.isoformat(),
                "updated_at": subgroup.updated_at.isoformat()
            }
            for subgroup in subgroups
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar subgrupos: {str(e)}")

@app.get("/api/v1/chart-accounts/accounts")
async def get_chart_accounts(
    subgroup_id: Optional[str] = None,
    group_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista contas do plano de contas"""
    try:
        query = db.query(ChartAccount).filter(ChartAccount.is_active == True)
        
        if subgroup_id:
            query = query.filter(ChartAccount.subgroup_id == subgroup_id)
        elif group_id:
            query = query.join(ChartAccountSubgroup).filter(ChartAccountSubgroup.group_id == group_id)
        
        accounts = query.all()
        return [
            {
                "id": account.id,
                "code": account.code,
                "name": account.name,
                "description": account.description,
                "subgroup_id": account.subgroup_id,
                "subgroup_name": account.subgroup.name,
                "group_id": account.subgroup.group.id,
                "group_name": account.subgroup.group.name,
                "account_type": account.account_type,
                "is_active": account.is_active,
                "created_at": account.created_at.isoformat(),
                "updated_at": account.updated_at.isoformat()
            }
            for account in accounts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar contas: {str(e)}")

@app.get("/api/v1/chart-accounts/hierarchy")
async def get_chart_accounts_hierarchy(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna a hierarquia completa do plano de contas"""
    try:
        groups = db.query(ChartAccountGroup).filter(ChartAccountGroup.is_active == True).all()
        subgroups = db.query(ChartAccountSubgroup).filter(ChartAccountSubgroup.is_active == True).all()
        accounts = db.query(ChartAccount).filter(ChartAccount.is_active == True).all()
        
        return {
            "groups": [
                {
                    "id": group.id,
                    "code": group.code,
                    "name": group.name,
                    "description": group.description,
                    "is_active": group.is_active,
                    "created_at": group.created_at.isoformat(),
                    "updated_at": group.updated_at.isoformat()
                }
                for group in groups
            ],
            "subgroups": [
                {
                    "id": subgroup.id,
                    "code": subgroup.code,
                    "name": subgroup.name,
                    "description": subgroup.description,
                    "group_id": subgroup.group_id,
                    "group_name": subgroup.group.name,
                    "is_active": subgroup.is_active,
                    "created_at": subgroup.created_at.isoformat(),
                    "updated_at": subgroup.updated_at.isoformat()
                }
                for subgroup in subgroups
            ],
            "accounts": [
                {
                    "id": account.id,
                    "code": account.code,
                    "name": account.name,
                    "description": account.description,
                    "subgroup_id": account.subgroup_id,
                    "subgroup_name": account.subgroup.name,
                    "group_id": account.subgroup.group.id,
                    "group_name": account.subgroup.group.name,
                    "account_type": account.account_type,
                    "is_active": account.is_active,
                    "created_at": account.created_at.isoformat(),
                    "updated_at": account.updated_at.isoformat()
                }
                for account in accounts
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar hierarquia: {str(e)}")

# ENDPOINTS DE TRANSAÇÕES FINANCEIRAS
# ============================================================================

@app.post("/api/v1/financial/transactions")
async def create_financial_transaction(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cria uma nova transação financeira"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin", "user"]:
            raise HTTPException(status_code=403, detail="Sem permissão para criar transações")
        
        # Importar serviço
        from app.services.financial_service import FinancialService
        
        # Criar transação
        transaction = FinancialService.create_transaction(
            db=db,
            data=request,
            tenant_id=current_user.get("tenant_id"),
            business_unit_id=current_user.get("business_unit_id"),
            created_by=current_user.get("sub")
        )
        
        return {
            "success": True,
            "message": "Transação criada com sucesso",
            "transaction_id": transaction.id,
            "reference": transaction.reference
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar transação: {str(e)}")

@app.get("/api/v1/financial/transactions")
async def get_financial_transactions(
    page: int = 1,
    limit: int = 50,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    chart_account_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista transações financeiras com filtros e paginação"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin", "user"]:
            raise HTTPException(status_code=403, detail="Sem permissão para visualizar transações")
        
        # Importar serviço
        from app.services.financial_service import FinancialService
        
        # Preparar filtros
        filters = {}
        if transaction_type:
            filters['transaction_type'] = transaction_type
        if status:
            filters['status'] = status
        if chart_account_id:
            filters['chart_account_id'] = chart_account_id
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if amount_min:
            filters['amount_min'] = amount_min
        if amount_max:
            filters['amount_max'] = amount_max
        if search:
            filters['search'] = search
        
        # Buscar transações
        transactions, total = FinancialService.get_transactions(
            db=db,
            tenant_id=current_user.get("tenant_id"),
            business_unit_id=current_user.get("business_unit_id"),
            filters=filters,
            page=page,
            limit=limit
        )
        
        # Formatar resposta
        transactions_data = []
        for transaction in transactions:
            transactions_data.append({
                "id": transaction.id,
                "reference": transaction.reference,
                "description": transaction.description,
                "amount": str(transaction.amount),
                "transaction_date": transaction.transaction_date.isoformat(),
                "transaction_type": transaction.transaction_type.value,
                "status": transaction.status.value,
                "chart_account_id": transaction.chart_account_id,
                "chart_account_name": transaction.chart_account.name,
                "chart_account_code": transaction.chart_account.code,
                "tenant_id": transaction.tenant_id,
                "business_unit_id": transaction.business_unit_id,
                "created_by": transaction.created_by,
                "approved_by": transaction.approved_by,
                "is_active": transaction.is_active,
                "notes": transaction.notes,
                "created_at": transaction.created_at.isoformat(),
                "updated_at": transaction.updated_at.isoformat(),
                "approved_at": transaction.approved_at.isoformat() if transaction.approved_at else None
            })
        
        return {
            "transactions": transactions_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar transações: {str(e)}")

@app.get("/api/v1/financial/transactions/{transaction_id}")
async def get_financial_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém uma transação financeira específica"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin", "user"]:
            raise HTTPException(status_code=403, detail="Sem permissão para visualizar transações")
        
        # Importar serviço
        from app.services.financial_service import FinancialService
        
        # Buscar transação
        transaction = FinancialService.get_transaction_by_id(
            db=db,
            transaction_id=transaction_id,
            tenant_id=current_user.get("tenant_id"),
            business_unit_id=current_user.get("business_unit_id")
        )
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        
        # Formatar resposta
        return {
            "id": transaction.id,
            "reference": transaction.reference,
            "description": transaction.description,
            "amount": str(transaction.amount),
            "transaction_date": transaction.transaction_date.isoformat(),
            "transaction_type": transaction.transaction_type.value,
            "status": transaction.status.value,
            "chart_account_id": transaction.chart_account_id,
            "chart_account_name": transaction.chart_account.name,
            "chart_account_code": transaction.chart_account.code,
            "tenant_id": transaction.tenant_id,
            "business_unit_id": transaction.business_unit_id,
            "created_by": transaction.created_by,
            "approved_by": transaction.approved_by,
            "is_active": transaction.is_active,
            "notes": transaction.notes,
            "created_at": transaction.created_at.isoformat(),
            "updated_at": transaction.updated_at.isoformat(),
            "approved_at": transaction.approved_at.isoformat() if transaction.approved_at else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar transação: {str(e)}")

@app.put("/api/v1/financial/transactions/{transaction_id}")
async def update_financial_transaction(
    transaction_id: str,
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza uma transação financeira"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Sem permissão para editar transações")
        
        # Importar serviço
        from app.services.financial_service import FinancialService
        
        # Atualizar transação
        transaction = FinancialService.update_transaction(
            db=db,
            transaction_id=transaction_id,
            data=request,
            tenant_id=current_user.get("tenant_id"),
            business_unit_id=current_user.get("business_unit_id")
        )
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        
        return {
            "success": True,
            "message": "Transação atualizada com sucesso"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar transação: {str(e)}")

@app.delete("/api/v1/financial/transactions/{transaction_id}")
async def delete_financial_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove uma transação financeira"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Sem permissão para remover transações")
        
        # Importar serviço
        from app.services.financial_service import FinancialService
        
        # Remover transação
        success = FinancialService.delete_transaction(
            db=db,
            transaction_id=transaction_id,
            tenant_id=current_user.get("tenant_id"),
            business_unit_id=current_user.get("business_unit_id")
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        
        return {
            "success": True,
            "message": "Transação removida com sucesso"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover transação: {str(e)}")

@app.post("/api/v1/financial/transactions/{transaction_id}/approve")
async def approve_financial_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aprova uma transação financeira"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Sem permissão para aprovar transações")
        
        # Importar serviço
        from app.services.financial_service import FinancialService
        
        # Aprovar transação
        transaction = FinancialService.approve_transaction(
            db=db,
            transaction_id=transaction_id,
            tenant_id=current_user.get("tenant_id"),
            business_unit_id=current_user.get("business_unit_id"),
            approved_by=current_user.get("sub")
        )
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        
        return {
            "success": True,
            "message": "Transação aprovada com sucesso"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao aprovar transação: {str(e)}")

@app.post("/api/v1/financial/transactions/{transaction_id}/reject")
async def reject_financial_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rejeita uma transação financeira"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Sem permissão para rejeitar transações")
        
        # Importar serviço
        from app.services.financial_service import FinancialService
        
        # Rejeitar transação
        transaction = FinancialService.reject_transaction(
            db=db,
            transaction_id=transaction_id,
            tenant_id=current_user.get("tenant_id"),
            business_unit_id=current_user.get("business_unit_id"),
            rejected_by=current_user.get("sub")
        )
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        
        return {
            "success": True,
            "message": "Transação rejeitada com sucesso"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao rejeitar transação: {str(e)}")

@app.get("/api/v1/financial/summary")
async def get_financial_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém resumo financeiro"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin", "user"]:
            raise HTTPException(status_code=403, detail="Sem permissão para visualizar resumo financeiro")
        
        # Importar serviço
        from app.services.financial_service import FinancialService
        
        # Preparar datas
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        
        # Buscar resumo
        summary = FinancialService.get_financial_summary(
            db=db,
            tenant_id=current_user.get("tenant_id"),
            business_unit_id=current_user.get("business_unit_id"),
            start_date=start_dt,
            end_date=end_dt
        )
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar resumo financeiro: {str(e)}")

@app.get("/api/v1/financial/chart-accounts-summary")
async def get_chart_accounts_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém resumo por conta contábil"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin", "user"]:
            raise HTTPException(status_code=403, detail="Sem permissão para visualizar resumo por conta")
        
        # Importar serviço
        from app.services.financial_service import FinancialService
        
        # Preparar datas
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        
        # Buscar resumo
        summary = FinancialService.get_chart_account_summary(
            db=db,
            tenant_id=current_user.get("tenant_id"),
            business_unit_id=current_user.get("business_unit_id"),
            start_date=start_dt,
            end_date=end_dt
        )
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar resumo por conta: {str(e)}")

# ENDPOINT DO DASHBOARD INTEGRADO
# ============================================================================

@app.get("/api/v1/dashboard/financial")
async def get_financial_dashboard(
    period: str = "month",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém dados completos do dashboard financeiro"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin", "user"]:
            raise HTTPException(status_code=403, detail="Sem permissão para visualizar dashboard")
        
        # Importar serviço
        from app.services.dashboard_service import DashboardService
        
        # Buscar dados do dashboard
        dashboard_data = DashboardService.get_dashboard_data(
            db=db,
            tenant_id=current_user.get("tenant_id"),
            business_unit_id=current_user.get("business_unit_id"),
            period=period
        )
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados do dashboard: {str(e)}")

@app.get("/api/v1/dashboard/chart-accounts-tree")
async def get_chart_accounts_tree_dashboard(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém árvore do plano de contas com resumos financeiros para o dashboard"""
    try:
        # Verificar se o usuário atual tem permissão
        if current_user.get("role") not in ["super_admin", "admin", "user"]:
            raise HTTPException(status_code=403, detail="Sem permissão para visualizar plano de contas")
        
        # Importar serviço
        from app.services.dashboard_service import DashboardService
        
        # Buscar árvore com resumos
        tree_data = DashboardService.get_chart_accounts_tree(
            db=db,
            tenant_id=current_user.get("tenant_id"),
            business_unit_id=current_user.get("business_unit_id")
        )
        
        return tree_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar árvore do plano de contas: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
