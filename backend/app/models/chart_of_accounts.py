from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid

class AccountGroup(Base):
    """Grupo de contas contábeis (ex: Receita, Custos, Despesas Operacionais)"""
    __tablename__ = "account_groups"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    tenant = relationship("Tenant", back_populates="account_groups")
    business_unit = relationship("BusinessUnit", back_populates="account_groups")
    subgroups = relationship("AccountSubgroup", back_populates="group", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'tenant_id', 'business_unit_id', name='uq_group_name_per_tenant_bu'),
    )

class AccountSubgroup(Base):
    """Subgrupo de contas contábeis (ex: Receita, Custos com Serviços Prestados)"""
    __tablename__ = "account_subgroups"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text)
    group_id = Column(String(36), ForeignKey("account_groups.id"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    group = relationship("AccountGroup", back_populates="subgroups")
    tenant = relationship("Tenant")
    business_unit = relationship("BusinessUnit")
    accounts = relationship("ChartAccount", back_populates="subgroup", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'group_id', 'tenant_id', 'business_unit_id', name='uq_subgroup_name_per_group_tenant_bu'),
    )

class ChartAccount(Base):
    """Conta contábil individual"""
    __tablename__ = "chart_accounts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text)
    subgroup_id = Column(String(36), ForeignKey("account_subgroups.id"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    subgroup = relationship("AccountSubgroup", back_populates="accounts")
    tenant = relationship("Tenant")
    business_unit = relationship("BusinessUnit")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'subgroup_id', 'tenant_id', 'business_unit_id', name='uq_account_name_per_subgroup_tenant_bu'),
    )
