from pydantic import BaseModel
from typing import Optional

class TenantCreate(BaseModel):
    name: str
    parent_tenant_id: Optional[str]

class TenantInDB(TenantCreate):
    id: str
    created_at: str
