from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.database import Base
import os

# Verificar se estamos usando SQLite
IS_SQLITE = os.getenv("DATABASE_URL", "").startswith("sqlite")

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    BUSINESS_UNIT_MANAGER = "business_unit_manager"
    DEPARTMENT_MANAGER = "department_manager"
    USER = "user"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_ACTIVATION = "pending_activation"

# SQLAlchemy Models
class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    domain = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    business_units = relationship("BusinessUnit", back_populates="tenant")
    user_access = relationship("UserTenantAccess", back_populates="tenant")
    # contas_bancarias = relationship("ContaBancaria", back_populates="tenant", lazy="dynamic", passive_deletes=True)
    # caixas = relationship("Caixa", back_populates="tenant", lazy="dynamic", passive_deletes=True)
    # investimentos = relationship("Investimento", back_populates="tenant", lazy="dynamic", passive_deletes=True)

class BusinessUnit(Base):
    __tablename__ = "business_units"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="business_units")
    users = relationship("User", back_populates="business_unit")
    departments = relationship("Department", back_populates="business_unit")
    user_access = relationship("UserBusinessUnitAccess", back_populates="business_unit")
    # contas_bancarias = relationship("ContaBancaria", back_populates="business_unit", lazy="dynamic", passive_deletes=True)
    # caixas = relationship("Caixa", back_populates="business_unit", lazy="dynamic", passive_deletes=True)
    # investimentos = relationship("Investimento", back_populates="business_unit", lazy="dynamic", passive_deletes=True)


class Department(Base):
    __tablename__ = "departments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    business_unit = relationship("BusinessUnit", back_populates="departments")
    users = relationship("User", back_populates="department")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)  # Campo para telefone
    
    role = Column(String(50), nullable=False, default=UserRole.USER)
    status = Column(String(50), default=UserStatus.PENDING_ACTIVATION)
    
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    business_unit = relationship("BusinessUnit", back_populates="users")
    department = relationship("Department", back_populates="users")
    sessions = relationship("UserSession", back_populates="user")
    tenant_access = relationship("UserTenantAccess", back_populates="user")
    business_unit_access = relationship("UserBusinessUnitAccess", back_populates="user")


class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    refresh_token = Column(String(255), unique=True, nullable=False)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")

# Tabelas de relacionamento para acesso multi-empresa/BU
class UserTenantAccess(Base):
    __tablename__ = "user_tenant_access"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    
    # Permissões específicas para esta empresa
    can_read = Column(Boolean, default=True)
    can_write = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_manage_users = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tenant_access")
    tenant = relationship("Tenant", back_populates="user_access")
    
    # Constraint único para evitar duplicatas
    __table_args__ = (UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant_access'),)

class UserBusinessUnitAccess(Base):
    __tablename__ = "user_business_unit_access"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    
    # Permissões específicas para esta BU
    can_read = Column(Boolean, default=True)
    can_write = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_manage_users = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="business_unit_access")
    business_unit = relationship("BusinessUnit", back_populates="user_access")
    
    # Constraint único para evitar duplicatas
    __table_args__ = (UniqueConstraint('user_id', 'business_unit_id', name='uq_user_business_unit_access'),)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models
class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)

class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = None

class TenantResponse(BaseModel):
    id: str
    name: str
    domain: str
    status: str
    created_at: datetime
    updated_at: datetime

class BusinessUnitCreate(BaseModel):
    tenant_id: str
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)

class BusinessUnitUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[str] = None

class BusinessUnitResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    code: str
    status: str
    created_at: datetime
    updated_at: datetime

class DepartmentCreate(BaseModel):
    business_unit_id: str
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[str] = None

class DepartmentResponse(BaseModel):
    id: str
    business_unit_id: str
    name: str
    code: str
    status: str
    created_at: datetime
    updated_at: datetime

class UserCreate(BaseModel):
    tenant_id: str
    business_unit_id: Optional[str] = None
    department_id: Optional[str] = None
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.USER

class UserUpdate(BaseModel):
    business_unit_id: Optional[str] = None
    department_id: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None

class UserResponse(BaseModel):
    id: str
    tenant_id: str
    business_unit_id: Optional[str]
    department_id: Optional[str]
    username: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: UserRole
    status: UserStatus
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

# Modelos para controle de acesso
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
    created_at: datetime
    updated_at: datetime

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
    created_at: datetime
    updated_at: datetime

# Modelos para login e autenticação
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str
