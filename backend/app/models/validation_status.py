"""
Modelo para rastrear o status de validação do dashboard contra a planilha do cliente.
"""
from datetime import datetime
from enum import Enum
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class ValidationStatus(str, Enum):
    """Status da validação"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"


class DashboardValidationStatus(Base):
    """
    Tabela para armazenar o status da última validação do dashboard.
    Uma entrada por tenant/business_unit.
    """
    __tablename__ = "dashboard_validation_status"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Vinculação com tenant e business unit
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    
    # Status da validação
    status = Column(String(20), nullable=False, default=ValidationStatus.PENDING)
    
    # Ano validado
    year = Column(String(4), nullable=False)
    
    # Detalhes da validação
    last_validation_at = Column(DateTime, nullable=True)
    validation_details = Column(Text, nullable=True)  # JSON com detalhes dos mismatches, se houver
    
    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    business_unit = relationship("BusinessUnit", foreign_keys=[business_unit_id])

