from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Numeric, Enum, Integer
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class ScheduledTransactionStatus(str, enum.Enum):
    """Status dos lançamentos previstos"""
    PENDING = "pending"  # Pendente
    EXECUTED = "executed"  # Executado
    CANCELLED = "cancelled"  # Cancelado
    EXPIRED = "expired"  # Expirado

class ScheduledTransactionFrequency(str, enum.Enum):
    """Frequência de execução"""
    ONCE = "once"  # Uma vez
    DAILY = "daily"  # Diário
    WEEKLY = "weekly"  # Semanal
    MONTHLY = "monthly"  # Mensal
    YEARLY = "yearly"  # Anual

class ScheduledTransaction(Base):
    """Lançamentos previstos/futuros"""
    __tablename__ = "scheduled_transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    
    # Informações básicas
    title = Column(String(255), nullable=False)  # Título do lançamento
    description = Column(Text, nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    
    # Vinculação com plano de contas
    chart_account_id = Column(String(36), ForeignKey("chart_accounts.id"), nullable=False)
    liquidation_account_id = Column(String(36), ForeignKey("liquidation_accounts.id"), nullable=True)
    
    # Agendamento
    scheduled_date = Column(DateTime, nullable=False)  # Data prevista
    frequency = Column(Enum(ScheduledTransactionFrequency), default=ScheduledTransactionFrequency.ONCE)
    end_date = Column(DateTime, nullable=True)  # Data final para recorrência
    
    # Tipo e status
    transaction_type = Column(String(20), nullable=False)  # receita, despesa, etc.
    status = Column(Enum(ScheduledTransactionStatus), default=ScheduledTransactionStatus.PENDING)
    
    # Controle de execução
    last_executed = Column(DateTime, nullable=True)  # Última execução
    next_execution = Column(DateTime, nullable=True)  # Próxima execução
    execution_count = Column(Integer, default=0)  # Quantas vezes foi executado
    
    # Usuário que criou
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Metadados
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    tenant = relationship("Tenant")
    business_unit = relationship("BusinessUnit")
    chart_account = relationship("ChartAccount")
    liquidation_account = relationship("LiquidationAccount")
    creator = relationship("User")
    executions = relationship("ScheduledTransactionExecution", back_populates="scheduled_transaction", cascade="all, delete-orphan")

class ScheduledTransactionExecution(Base):
    """Histórico de execuções dos lançamentos previstos"""
    __tablename__ = "scheduled_transaction_executions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    scheduled_transaction_id = Column(String(36), ForeignKey("scheduled_transactions.id"), nullable=False)
    
    # Transação criada
    financial_transaction_id = Column(String(36), ForeignKey("financial_transactions.id"), nullable=True)
    
    # Data e status da execução
    execution_date = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False)  # success, failed, skipped
    
    # Detalhes da execução
    executed_amount = Column(Numeric(15, 2), nullable=True)  # Valor efetivamente executado
    error_message = Column(Text, nullable=True)  # Mensagem de erro se falhou
    
    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    scheduled_transaction = relationship("ScheduledTransaction", back_populates="executions")
    financial_transaction = relationship("FinancialTransaction")
