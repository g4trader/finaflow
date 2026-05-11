from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text, ForeignKey, UniqueConstraint

from app.database import Base


class CashFlowYearSettings(Base):
    __tablename__ = "cash_flow_year_settings"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "business_unit_id",
            "year",
            name="uq_cash_flow_year_settings_tenant_bu_year",
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    year = Column(Integer, nullable=False)
    saldo_ano_anterior = Column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    line_order = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
