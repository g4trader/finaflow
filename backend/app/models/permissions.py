from datetime import datetime
from enum import Enum
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
    
    # Usuários
    USERS_READ = "users_read"
    USERS_WRITE = "users_write"
    USERS_DELETE = "users_delete"

class Permission(Base):
    """Modelo para permissões do sistema"""
    __tablename__ = "permissions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    category = Column(String(50), nullable=False, default="general")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserPermission(Base):
    """Permissões específicas de usuário por BU"""
    __tablename__ = "user_permissions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    permission_code = Column(String(50), nullable=False)
    is_granted = Column(Boolean, default=True)
    granted_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'business_unit_id', 'permission_code', name='uq_user_bu_permission'),
    )
