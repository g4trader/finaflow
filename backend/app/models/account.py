from pydantic import BaseModel

class AccountCreate(BaseModel):
    subgroup_id: str
    name: str
    balance: float
    tenant_id: str

class AccountInDB(AccountCreate):
    id: str
    created_at: str
