from pydantic import BaseModel
from typing import Optional

class TransactionCreate(BaseModel):
    account_id: str
    amount: float
    description: Optional[str] = None
    date: str
    tenant_id: str

class TransactionInDB(TransactionCreate):
    id: str
    created_at: str
