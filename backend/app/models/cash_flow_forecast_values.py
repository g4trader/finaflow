from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text, ForeignKey, UniqueConstraint

from app.database import Base


class CashFlowForecastValue(Base):
    __tablename__ = "cash_flow_forecast_values"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "business_unit_id",
            "year",
            "label",
            "month",
            name="uq_cash_flow_forecast_values_tenant_bu_year_label_month",
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    business_unit_id = Column(String(36), ForeignKey("business_units.id"), nullable=False)
    year = Column(Integer, nullable=False)
    label = Column(Text, nullable=False)
    month = Column(Integer, nullable=False)
    value = Column(Numeric(18, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
