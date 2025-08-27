from pydantic import BaseModel
from typing import Optional

class ForecastCreate(BaseModel):
    account_id: str
    expected_date: str
    amount: float
    description: Optional[str] = None
    tenant_id: str

class ForecastInDB(ForecastCreate):
    id: str
    created_at: str
