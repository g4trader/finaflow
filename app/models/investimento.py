"""
Modelo para Investimentos e Aplicações Financeiras
"""

from sqlalchemy import Column, String, Numeric, Boolean, DateTime, Date, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class TipoInvestimento(str, enum.Enum):
    """Tipos de investimento"""
    RENDA_FIXA = "renda_fixa"
    RENDA_VARIAVEL = "renda_variavel"
    FUNDO = "fundo"
    CDB = "cdb"
    LCI = "lci"
    LCA = "lca"
    TESOURO_DIRETO = "tesouro_direto"
    POUPANCA = "poupanca"
    OUTRO = "outro"


class Investimento(Base):
    """Modelo de Investimento/Aplicação Financeira"""
    __tablename__ = "investimentos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String, ForeignKey("business_units.id"), nullable=False)
    
    # Dados do investimento
    tipo = Column(SQLEnum(TipoInvestimento), nullable=False)
    instituicao = Column(String(200), nullable=False)  # Ex: "Banco do Brasil", "XP Investimentos"
    descricao = Column(Text, nullable=True)
    
    # Valores
    valor_aplicado = Column(Numeric(15, 2), nullable=False)
    valor_atual = Column(Numeric(15, 2), nullable=False)
    
    # Datas
    data_aplicacao = Column(Date, nullable=False)
    data_vencimento = Column(Date, nullable=True)
    
    # Rentabilidade
    taxa_rendimento = Column(Numeric(10, 4), nullable=True)  # Ex: 12.5 para 12,5% a.a.
    
    # Controle
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant")
    business_unit = relationship("BusinessUnit")
    created_by_user = relationship("User")
    
    __table_args__ = (
        {"schema": None}
    )

