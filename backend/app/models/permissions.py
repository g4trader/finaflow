from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class PermissionType(str, Enum):
    """Tipos de permissão disponíveis no sistema"""
    # Dashboard
    DASHBOARD_READ = "dashboard_read"
    DASHBOARD_WRITE = "dashboard_write"
    
    # Transações
    TRANSACTIONS_READ = "transactions_read"
    TRANSACTIONS_WRITE = "transactions_write"
    TRANSACTIONS_DELETE = "transactions_delete"
    
    # Contas
    ACCOUNTS_READ = "accounts_read"
    ACCOUNTS_WRITE = "accounts_write"
    ACCOUNTS_DELETE = "accounts_delete"
    
    # Grupos e Subgrupos
    GROUPS_READ = "groups_read"
    GROUPS_WRITE = "groups_write"
    GROUPS_DELETE = "groups_delete"
    
    SUBGROUPS_READ = "subgroups_read"
    SUBGROUPS_WRITE = "subgroups_write"
    SUBGROUPS_DELETE = "subgroups_delete"
    
    # Relatórios
    REPORTS_READ = "reports_read"
    REPORTS_EXPORT = "reports_export"
    
    # Previsões
    FORECAST_READ = "forecast_read"
    FORECAST_WRITE = "forecast_write"
    FORECAST_DELETE = "forecast_delete"
    
    # Importação
    IMPORT_CSV = "import_csv"
    
    # Usuários e Permissões
    USERS_READ = "users_read"
    USERS_WRITE = "users_write"
    USERS_DELETE = "users_delete"
    
    PERMISSIONS_READ = "permissions_read"
    PERMISSIONS_WRITE = "permissions_write"
    
    # Empresas e BUs
    COMPANIES_READ = "companies_read"
    COMPANIES_WRITE = "companies_write"
    COMPANIES_DELETE = "companies_delete"
    
    BUSINESS_UNITS_READ = "business_units_read"
    BUSINESS_UNITS_WRITE = "business_units_write"
    BUSINESS_UNITS_DELETE = "business_units_delete"
    
    # Configurações
    SETTINGS_READ = "settings_read"
    SETTINGS_WRITE = "settings_write"

class PermissionCategory(str, Enum):
    """Categorias de permissões para organização"""
    DASHBOARD = "dashboard"
    FINANCIAL = "financial"
    REPORTS = "reports"
    ADMINISTRATION = "administration"
    SYSTEM = "system"

class Permission(Base):
    """Modelo para permissões granulares do sistema"""
    __tablename__ = "permissions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    category = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_permissions = relationship("UserPermission", back_populates="permission", cascade="all, delete-orphan")
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")

class UserPermission(Base):
    """Permissões específicas de usuário por BU"""
    __tablename__ = "user_permissions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    permission_id = Column(String(36), ForeignKey("permissions.id"), nullable=False)
    is_granted = Column(Boolean, default=True)
    granted_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="permissions")
    business_unit = relationship("BusinessUnit", back_populates="user_permissions")
    permission = relationship("Permission", back_populates="user_permissions")
    granted_by_user = relationship("User", foreign_keys=[granted_by])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'business_unit_id', 'permission_id', name='uq_user_bu_permission'),
    )

class RolePermission(Base):
    """Permissões por role (padrão)"""
    __tablename__ = "role_permissions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    role = Column(String(50), nullable=False)
    permission_id = Column(String(36), ForeignKey("permissions.id"), nullable=False)
    is_granted = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    permission = relationship("Permission", back_populates="role_permissions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('role', 'permission_id', name='uq_role_permission'),
    )
