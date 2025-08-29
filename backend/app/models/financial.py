from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.database import Base

# SQLAlchemy Models
class AccountGroup(Base):
    """Grupo de contas (ex: Receita, Custos, Despesas Operacionais)"""
    __tablename__ = "account_groups"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subgroups = relationship("AccountSubgroup", back_populates="group")

class AccountSubgroup(Base):
    """Subgrupo de contas (ex: Receita Financeira, Custos com Mão de Obra)"""
    __tablename__ = "account_subgroups"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    group_id = Column(String(36), ForeignKey("account_groups.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    group = relationship("AccountGroup", back_populates="subgroups")
    accounts = relationship("Account", back_populates="subgroup")

class Account(Base):
    """Conta específica (ex: Vendas Cursos pelo comercial, Salário)"""
    __tablename__ = "accounts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    subgroup_id = Column(String(36), ForeignKey("account_subgroups.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    account_type = Column(String(50), nullable=False)  # revenue, expense, cost, asset, liability
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subgroup = relationship("AccountSubgroup", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")

class Transaction(Base):
    """Transação financeira"""
    __tablename__ = "transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    
    transaction_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    transaction_type = Column(String(50), nullable=False)  # credit, debit
    category = Column(String(100), nullable=True)
    
    # Campos de controle
    is_recurring = Column(Boolean, default=False)
    is_forecast = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=True)
    
    # Campos de auditoria
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    business_unit = relationship("BusinessUnit")
    department = relationship("Department")
    created_by_user = relationship("User")

class CashFlow(Base):
    """Fluxo de caixa consolidado"""
    __tablename__ = "cash_flows"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=True)
    
    date = Column(DateTime, nullable=False)
    opening_balance = Column(Numeric(15, 2), nullable=False)
    total_revenue = Column(Numeric(15, 2), nullable=False)
    total_expenses = Column(Numeric(15, 2), nullable=False)
    total_costs = Column(Numeric(15, 2), nullable=False)
    net_flow = Column(Numeric(15, 2), nullable=False)
    closing_balance = Column(Numeric(15, 2), nullable=False)
    
    # Campos de controle
    is_forecast = Column(Boolean, default=False)
    period_type = Column(String(50), nullable=False)  # daily, monthly, yearly
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BankAccount(Base):
    """Conta bancária"""
    __tablename__ = "bank_accounts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=True)
    
    bank_name = Column(String(255), nullable=False)
    account_number = Column(String(50), nullable=False)
    account_type = Column(String(50), nullable=False)  # checking, savings, investment
    balance = Column(Numeric(15, 2), nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="BRL")
    status = Column(String(50), default="active")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic Models
class AccountGroupCreate(BaseModel):
    tenant_id: str
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None

class AccountGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    status: Optional[str] = None

class AccountGroupResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    code: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

class AccountSubgroupCreate(BaseModel):
    tenant_id: str
    group_id: str
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None

class AccountSubgroupUpdate(BaseModel):
    group_id: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    status: Optional[str] = None

class AccountSubgroupResponse(BaseModel):
    id: str
    tenant_id: str
    group_id: str
    name: str
    code: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

class AccountCreate(BaseModel):
    tenant_id: str
    subgroup_id: str
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    account_type: str = Field(..., pattern="^(revenue|expense|cost|asset|liability)$")

class AccountUpdate(BaseModel):
    subgroup_id: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    account_type: Optional[str] = Field(None, pattern="^(revenue|expense|cost|asset|liability)$")
    status: Optional[str] = None

class AccountResponse(BaseModel):
    id: str
    tenant_id: str
    subgroup_id: str
    name: str
    code: str
    description: Optional[str]
    account_type: str
    status: str
    created_at: datetime
    updated_at: datetime

class TransactionCreate(BaseModel):
    tenant_id: str
    account_id: str
    business_unit_id: Optional[str] = None
    department_id: Optional[str] = None
    transaction_date: datetime
    description: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    transaction_type: str = Field(..., pattern="^(credit|debit)$")
    category: Optional[str] = None
    is_recurring: bool = False
    is_forecast: bool = False

class TransactionUpdate(BaseModel):
    account_id: Optional[str] = None
    business_unit_id: Optional[str] = None
    department_id: Optional[str] = None
    transaction_date: Optional[datetime] = None
    description: Optional[str] = Field(None, min_length=1)
    amount: Optional[float] = Field(None, gt=0)
    transaction_type: Optional[str] = Field(None, pattern="^(credit|debit)$")
    category: Optional[str] = None
    is_recurring: Optional[bool] = None
    is_forecast: Optional[bool] = None
    is_approved: Optional[bool] = None

class TransactionResponse(BaseModel):
    id: str
    tenant_id: str
    account_id: str
    business_unit_id: Optional[str]
    department_id: Optional[str]
    transaction_date: datetime
    description: str
    amount: float
    transaction_type: str
    category: Optional[str]
    is_recurring: bool
    is_forecast: bool
    is_approved: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

class CashFlowResponse(BaseModel):
    id: str
    tenant_id: str
    business_unit_id: Optional[str]
    date: datetime
    opening_balance: float
    total_revenue: float
    total_expenses: float
    total_costs: float
    net_flow: float
    closing_balance: float
    is_forecast: bool
    period_type: str
    created_at: datetime
    updated_at: datetime

class BankAccountCreate(BaseModel):
    tenant_id: str
    business_unit_id: Optional[str] = None
    bank_name: str = Field(..., min_length=1, max_length=255)
    account_number: str = Field(..., min_length=1, max_length=50)
    account_type: str = Field(..., pattern="^(checking|savings|investment)$")
    balance: float = Field(..., ge=0)
    currency: str = Field(..., min_length=3, max_length=10)

class BankAccountUpdate(BaseModel):
    business_unit_id: Optional[str] = None
    bank_name: Optional[str] = Field(None, min_length=1, max_length=255)
    account_number: Optional[str] = Field(None, min_length=1, max_length=50)
    account_type: Optional[str] = Field(None, pattern="^(checking|savings|investment)$")
    balance: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=10)
    status: Optional[str] = None

class BankAccountResponse(BaseModel):
    id: str
    tenant_id: str
    business_unit_id: Optional[str]
    bank_name: str
    account_number: str
    account_type: str
    balance: float
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
