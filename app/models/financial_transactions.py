from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Numeric, Integer, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class TransactionType(str, enum.Enum):
    """Tipos de transação"""
    RECEITA = "receita"
    DESPESA = "despesa"
    TRANSFERENCIA = "transferencia"
    AJUSTE = "ajuste"

class TransactionStatus(str, enum.Enum):
    """Status da transação"""
    PENDENTE = "pendente"
    APROVADA = "aprovada"
    REJEITADA = "rejeitada"
    CANCELADA = "cancelada"

class FinancialTransaction(Base):
    """Transação financeira vinculada ao plano de contas"""
    __tablename__ = "financial_transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Informações básicas
    reference = Column(String(100), nullable=False)  # Número de referência
    description = Column(Text, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)  # Valor da transação
    transaction_date = Column(DateTime, nullable=False)  # Data da transação
    
    # Tipo e status
    transaction_type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDENTE)
    
    # Vinculação com plano de contas
    chart_account_id = Column(String(36), ForeignKey("chart_accounts.id"), nullable=False)
    
    # Vinculação com empresa/BU
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    
    # Usuário que criou
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Metadados
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    
    # Relacionamentos
    chart_account = relationship("ChartAccount")
    tenant = relationship("Tenant")
    business_unit = relationship("BusinessUnit")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('reference', 'tenant_id', 'business_unit_id', name='uq_transaction_reference'),
    )

class TransactionAttachment(Base):
    """Anexos das transações (comprovantes, notas fiscais, etc.)"""
    __tablename__ = "transaction_attachments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    transaction_id = Column(String(36), ForeignKey("financial_transactions.id"), nullable=False)
    
    # Informações do arquivo
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Tamanho em bytes
    mime_type = Column(String(100), nullable=False)
    
    # Metadados
    description = Column(Text)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    transaction = relationship("FinancialTransaction")
    uploader = relationship("User")

class TransactionCategory(Base):
    """Categorias personalizadas para transações (além do plano de contas)"""
    __tablename__ = "transaction_categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Informações básicas
    name = Column(String(100), nullable=False)
    description = Column(Text)
    color = Column(String(7), default="#3B82F6")  # Código de cor hex
    
    # Vinculação
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    chart_account_id = Column(String(36), ForeignKey("chart_accounts.id"), nullable=True)
    
    # Metadados
    is_active = Column(Boolean, default=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    tenant = relationship("Tenant")
    business_unit = relationship("BusinessUnit")
    chart_account = relationship("ChartAccount")
    creator = relationship("User")

# Modelos Pydantic para APIs
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal

class FinancialTransactionCreate(BaseModel):
    reference: str
    description: str
    amount: Decimal
    transaction_date: str  # ISO format
    transaction_type: TransactionType
    chart_account_id: str
    notes: Optional[str] = None

class FinancialTransactionUpdate(BaseModel):
    reference: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    transaction_date: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
    chart_account_id: Optional[str] = None
    status: Optional[TransactionStatus] = None
    notes: Optional[str] = None

class FinancialTransactionResponse(BaseModel):
    id: str
    reference: str
    description: str
    amount: str  # Decimal como string para JSON
    transaction_date: str
    transaction_type: str
    status: str
    chart_account_id: str
    chart_account_name: str
    chart_account_code: str
    tenant_id: str
    business_unit_id: str
    created_by: str
    approved_by: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: str
    updated_at: str
    approved_at: Optional[str] = None

    class Config:
        from_attributes = True

class TransactionAttachmentCreate(BaseModel):
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    description: Optional[str] = None

class TransactionAttachmentResponse(BaseModel):
    id: str
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    description: Optional[str] = None
    uploaded_by: str
    uploaded_at: str

    class Config:
        from_attributes = True

class TransactionCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#3B82F6"
    chart_account_id: Optional[str] = None

class TransactionCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    chart_account_id: Optional[str] = None
    is_active: Optional[bool] = None

class TransactionCategoryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    color: str
    chart_account_id: Optional[str] = None
    chart_account_name: Optional[str] = None
    is_active: bool
    created_by: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
