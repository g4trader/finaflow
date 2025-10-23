from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Numeric, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class LiquidationAccountType(str, enum.Enum):
    """Tipos de conta de liquidação"""
    BANK_ACCOUNT = "bank_account"  # Conta bancária (CEF, SCB, etc.)
    CASH = "cash"  # Caixa físico
    INVESTMENT = "investment"  # Investimentos
    CREDIT_CARD = "credit_card"  # Cartão de crédito
    OTHER = "other"  # Outros

class LiquidationAccount(Base):
    """Contas de liquidação (scb, CEF, CX, etc.)"""
    __tablename__ = "liquidation_accounts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=True)
    
    # Identificação da conta
    code = Column(String(20), nullable=False)  # scb, CEF, CX, etc.
    name = Column(String(100), nullable=False)  # Nome da conta
    description = Column(Text, nullable=True)
    
    # Tipo e configurações
    account_type = Column(Enum(LiquidationAccountType), nullable=False)
    bank_name = Column(String(100), nullable=True)  # Nome do banco se aplicável
    account_number = Column(String(50), nullable=True)  # Número da conta se aplicável
    
    # Saldo e controle
    current_balance = Column(Numeric(15, 2), default=0)  # Saldo atual
    initial_balance = Column(Numeric(15, 2), default=0)  # Saldo inicial
    currency = Column(String(10), default="BRL")
    
    # Status e controle
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Conta padrão para lançamentos
    
    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    tenant = relationship("Tenant")
    business_unit = relationship("BusinessUnit")
    
    # Constraints: código único por tenant
    __table_args__ = (
        # UniqueConstraint('code', 'tenant_id', name='uq_liquidation_account_code_tenant'),
    )

class LiquidationAccountBalance(Base):
    """Histórico de saldos das contas de liquidação"""
    __tablename__ = "liquidation_account_balances"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    liquidation_account_id = Column(String(36), ForeignKey("liquidation_accounts.id"), nullable=False)
    
    # Data e saldo
    balance_date = Column(DateTime, nullable=False)  # Data do saldo
    opening_balance = Column(Numeric(15, 2), nullable=False)  # Saldo de abertura
    closing_balance = Column(Numeric(15, 2), nullable=False)  # Saldo de fechamento
    
    # Movimentações do dia
    total_credits = Column(Numeric(15, 2), default=0)  # Total de créditos
    total_debits = Column(Numeric(15, 2), default=0)  # Total de débitos
    net_movement = Column(Numeric(15, 2), default=0)  # Movimentação líquida
    
    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    liquidation_account = relationship("LiquidationAccount")
