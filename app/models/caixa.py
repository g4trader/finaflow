"""
Modelos para Caixa (Dinheiro físico) e Movimentações
"""

from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class TipoMovimentacaoCaixa(str, enum.Enum):
    """Tipos de movimentação de caixa"""
    ENTRADA = "entrada"
    SAIDA = "saida"


class Caixa(Base):
    """Modelo de Caixa (Dinheiro Físico)"""
    __tablename__ = "caixas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String, ForeignKey("business_units.id"), nullable=False)
    
    # Dados do caixa
    nome = Column(String(100), nullable=False)  # Ex: "Caixa Principal", "Caixa Filial"
    descricao = Column(Text, nullable=True)
    
    # Saldos
    saldo_inicial = Column(Numeric(15, 2), nullable=False, default=0)
    saldo_atual = Column(Numeric(15, 2), nullable=False, default=0)
    
    # Controle
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant")
    business_unit = relationship("BusinessUnit")
    movimentacoes = relationship("MovimentacaoCaixa", back_populates="caixa")
    created_by_user = relationship("User")
    
    __table_args__ = (
        {"schema": None}
    )


class MovimentacaoCaixa(Base):
    """Modelo de Movimentação de Caixa"""
    __tablename__ = "movimentacoes_caixa"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caixa_id = Column(UUID(as_uuid=True), ForeignKey("caixas.id"), nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String, ForeignKey("business_units.id"), nullable=False)
    
    # Dados da movimentação
    data_movimentacao = Column(DateTime, nullable=False)
    tipo = Column(SQLEnum(TipoMovimentacaoCaixa), nullable=False)
    valor = Column(Numeric(15, 2), nullable=False)
    descricao = Column(Text, nullable=True)
    
    # Vínculo com lançamento diário (opcional)
    lancamento_diario_id = Column(UUID(as_uuid=True), ForeignKey("lancamentos_diarios.id"), nullable=True)
    
    # Controle
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    caixa = relationship("Caixa", back_populates="movimentacoes")
    lancamento_diario = relationship("LancamentoDiario")
    created_by_user = relationship("User")
    
    __table_args__ = (
        {"schema": None}
    )

