from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class ChartAccountGroup(Base):
    """Grupo do Plano de Contas (1º nível)"""
    __tablename__ = "chart_account_groups"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True)  # Null = global/compartilhado
    code = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    subgroups = relationship("ChartAccountSubgroup", back_populates="group", cascade="all, delete-orphan")
    
    # Constraints: código único por tenant (ou global se tenant_id é null)
    __table_args__ = (
        UniqueConstraint('code', 'tenant_id', name='uq_group_code_tenant'),
    )

class ChartAccountSubgroup(Base):
    """Subgrupo do Plano de Contas (2º nível)"""
    __tablename__ = "chart_account_subgroups"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True)  # Null = global/compartilhado
    code = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    group_id = Column(String(36), ForeignKey("chart_account_groups.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    group = relationship("ChartAccountGroup", back_populates="subgroups")
    accounts = relationship("ChartAccount", back_populates="subgroup", cascade="all, delete-orphan")
    
    # Constraints: código único por grupo e tenant
    __table_args__ = (
        UniqueConstraint('code', 'group_id', 'tenant_id', name='uq_subgroup_code_group_tenant'),
    )

class ChartAccount(Base):
    """Conta do Plano de Contas (3º nível)"""
    __tablename__ = "chart_accounts"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True)  # Null = global/compartilhado
    code = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    subgroup_id = Column(String(36), ForeignKey("chart_account_subgroups.id"), nullable=False)
    account_type = Column(String(20), nullable=False)  # Ativo, Passivo, Receita, Despesa
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    subgroup = relationship("ChartAccountSubgroup", back_populates="accounts")
    
    # Constraints: código único por subgrupo e tenant
    __table_args__ = (
        UniqueConstraint('code', 'subgroup_id', 'tenant_id', name='uq_account_code_subgroup_tenant'),
    )

class BusinessUnitChartAccount(Base):
    """Relacionamento entre BU e Plano de Contas (para customizações)"""
    __tablename__ = "business_unit_chart_accounts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    chart_account_id = Column(String(36), ForeignKey("chart_accounts.id"), nullable=False)
    is_custom = Column(Boolean, default=False)  # Se é uma conta customizada da BU
    custom_code = Column(String(10))  # Código customizado se diferente
    custom_name = Column(String(100))  # Nome customizado se diferente
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('business_unit_id', 'chart_account_id', name='uq_bu_chart_account'),
    )

# Modelos Pydantic para APIs
from pydantic import BaseModel
from typing import Optional, List

class ChartAccountGroupCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None

class ChartAccountGroupUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ChartAccountGroupResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class ChartAccountSubgroupCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    group_id: str

class ChartAccountSubgroupUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    group_id: Optional[str] = None
    is_active: Optional[bool] = None

class ChartAccountSubgroupResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    group_id: str
    group_name: str
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class ChartAccountCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    subgroup_id: str
    account_type: str  # Ativo, Passivo, Receita, Despesa

class ChartAccountUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    subgroup_id: Optional[str] = None
    account_type: Optional[str] = None
    is_active: Optional[bool] = None

class ChartAccountResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    subgroup_id: str
    subgroup_name: str
    group_id: str
    group_name: str
    account_type: str
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class BusinessUnitChartAccountCreate(BaseModel):
    business_unit_id: str
    chart_account_id: str
    is_custom: bool = False
    custom_code: Optional[str] = None
    custom_name: Optional[str] = None

class BusinessUnitChartAccountUpdate(BaseModel):
    is_custom: Optional[bool] = None
    custom_code: Optional[str] = None
    custom_name: Optional[str] = None
    is_active: Optional[bool] = None

class BusinessUnitChartAccountResponse(BaseModel):
    id: str
    business_unit_id: str
    chart_account_id: str
    chart_account_name: str
    chart_account_code: str
    is_custom: bool
    custom_code: Optional[str] = None
    custom_name: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class ChartAccountHierarchyResponse(BaseModel):
    groups: List[ChartAccountGroupResponse]
    subgroups: List[ChartAccountSubgroupResponse]
    accounts: List[ChartAccountResponse]
