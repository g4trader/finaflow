"""
Modelos para Contas Bancárias e Movimentações
"""

from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class TipoContaBancaria(str, enum.Enum):
    """Tipos de conta bancária"""
    CORRENTE = "corrente"
    POUPANCA = "poupanca"
    INVESTIMENTO = "investimento"
    OUTRO = "outro"


class TipoMovimentacaoBancaria(str, enum.Enum):
    """Tipos de movimentação bancária"""
    ENTRADA = "entrada"
    SAIDA = "saida"
    TRANSFERENCIA = "transferencia"


class ContaBancaria(Base):
    """Modelo de Conta Bancária"""
    __tablename__ = "contas_bancarias"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String, ForeignKey("business_units.id"), nullable=False)
    
    # Dados da conta
    banco = Column(String(100), nullable=False)  # Ex: "CEF", "SICOOB", "Banco do Brasil"
    agencia = Column(String(20), nullable=True)
    numero_conta = Column(String(50), nullable=True)
    tipo = Column(SQLEnum(TipoContaBancaria), nullable=False, default=TipoContaBancaria.CORRENTE)
    
    # Saldos
    saldo_inicial = Column(Numeric(15, 2), nullable=False, default=0)
    saldo_atual = Column(Numeric(15, 2), nullable=False, default=0)
    
    # Controle
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="contas_bancarias")
    business_unit = relationship("BusinessUnit", back_populates="contas_bancarias")
    movimentacoes = relationship("MovimentacaoBancaria", back_populates="conta_bancaria", foreign_keys="MovimentacaoBancaria.conta_bancaria_id")
    created_by_user = relationship("User")
    
    __table_args__ = (
        {"schema": None}
    )


class MovimentacaoBancaria(Base):
    """Modelo de Movimentação Bancária"""
    __tablename__ = "movimentacoes_bancarias"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conta_bancaria_id = Column(UUID(as_uuid=True), ForeignKey("contas_bancarias.id"), nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String, ForeignKey("business_units.id"), nullable=False)
    
    # Dados da movimentação
    data_movimentacao = Column(DateTime, nullable=False)
    tipo = Column(SQLEnum(TipoMovimentacaoBancaria), nullable=False)
    valor = Column(Numeric(15, 2), nullable=False)
    descricao = Column(Text, nullable=True)
    
    # Para transferências
    conta_destino_id = Column(UUID(as_uuid=True), ForeignKey("contas_bancarias.id"), nullable=True)
    
    # Vínculo com lançamento diário (opcional)
    lancamento_diario_id = Column(UUID(as_uuid=True), ForeignKey("lancamentos_diarios.id"), nullable=True)
    
    # Controle
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    conta_bancaria = relationship("ContaBancaria", back_populates="movimentacoes", foreign_keys=[conta_bancaria_id])
    conta_destino = relationship("ContaBancaria", foreign_keys=[conta_destino_id])
    lancamento_diario = relationship("LancamentoDiario")
    created_by_user = relationship("User")
    
    __table_args__ = (
        {"schema": None}
    )

