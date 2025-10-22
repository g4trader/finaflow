from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Numeric, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class TransactionType(str, enum.Enum):
    """Tipos de transação baseados no Grupo e Subgrupo"""
    RECEITA = "RECEITA"
    DESPESA = "DESPESA"
    CUSTO = "CUSTO"
    ATIVO = "ATIVO"
    PASSIVO = "PASSIVO"
    PATRIMONIO_LIQUIDO = "PATRIMONIO_LIQUIDO"

class TransactionStatus(str, enum.Enum):
    """Status da transação"""
    PENDENTE = "pendente"
    LIQUIDADO = "liquidado"
    CANCELADO = "cancelado"

class LancamentoDiario(Base):
    """
    Lançamento Diário - Espelho exato da planilha
    Estrutura: Data Movimentação, Conta, Subgrupo, Grupo, Valor, Liquidação, Observações
    """
    __tablename__ = "lancamentos_diarios"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Campos obrigatórios da planilha
    data_movimentacao = Column(DateTime, nullable=False)  # Data Movimentação
    valor = Column(Numeric(15, 2), nullable=False)  # Valor
    liquidacao = Column(DateTime, nullable=True)  # Liquidação
    observacoes = Column(Text, nullable=True)  # Observações
    
    # Campos obrigatórios vinculados ao plano de contas
    conta_id = Column(String(36), ForeignKey("chart_accounts.id"), nullable=False)  # Conta
    subgrupo_id = Column(String(36), ForeignKey("chart_account_subgroups.id"), nullable=False)  # Subgrupo
    grupo_id = Column(String(36), ForeignKey("chart_account_groups.id"), nullable=False)  # Grupo
    
    # Tipo de transação baseado no Grupo (calculado automaticamente)
    transaction_type = Column(Enum(TransactionType), nullable=True)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDENTE)
    
    # Vinculação com empresa/BU
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    
    # Usuário que criou
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Metadados
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    conta = relationship("ChartAccount", foreign_keys=[conta_id])
    subgrupo = relationship("ChartAccountSubgroup", foreign_keys=[subgrupo_id])
    grupo = relationship("ChartAccountGroup", foreign_keys=[grupo_id])
    tenant = relationship("Tenant")
    business_unit = relationship("BusinessUnit")
    creator = relationship("User", foreign_keys=[created_by])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('data_movimentacao', 'conta_id', 'valor', 'tenant_id', 'business_unit_id', 
                        name='uq_lancamento_data_conta_valor'),
    )

# Modelos Pydantic para APIs
from pydantic import BaseModel, validator
from typing import Optional, List
from decimal import Decimal

class LancamentoDiarioCreate(BaseModel):
    """Criação de lançamento diário"""
    data_movimentacao: str  # ISO format
    valor: Decimal
    liquidacao: Optional[str] = None  # ISO format
    observacoes: Optional[str] = None
    
    # Campos obrigatórios do plano de contas
    conta_id: str
    subgrupo_id: str
    grupo_id: str
    
    @validator('valor')
    def validate_valor(cls, v):
        if v <= 0:
            raise ValueError('Valor deve ser maior que zero')
        return v

class LancamentoDiarioUpdate(BaseModel):
    """Atualização de lançamento diário"""
    data_movimentacao: Optional[str] = None
    valor: Optional[Decimal] = None
    liquidacao: Optional[str] = None
    observacoes: Optional[str] = None
    status: Optional[TransactionStatus] = None
    
    # Campos obrigatórios do plano de contas
    conta_id: Optional[str] = None
    subgrupo_id: Optional[str] = None
    grupo_id: Optional[str] = None

class LancamentoDiarioResponse(BaseModel):
    """Resposta de lançamento diário"""
    id: str
    data_movimentacao: str
    valor: str  # Decimal como string para JSON
    liquidacao: Optional[str] = None
    observacoes: Optional[str] = None
    
    # Informações do plano de contas
    conta_id: str
    conta_nome: str
    conta_codigo: str
    subgrupo_id: str
    subgrupo_nome: str
    subgrupo_codigo: str
    grupo_id: str
    grupo_nome: str
    grupo_codigo: str
    
    # Tipo e status
    transaction_type: str
    status: str
    
    # Vinculações
    tenant_id: str
    business_unit_id: str
    created_by: str
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class LancamentoDiarioListResponse(BaseModel):
    """Lista de lançamentos diários com paginação"""
    lancamentos: List[LancamentoDiarioResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
