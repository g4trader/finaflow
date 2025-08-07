from pydantic import BaseModel
from typing import Optional

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tenant_id: str

class GroupInDB(GroupCreate):
    id: str
    created_at: str

class SubgroupCreate(BaseModel):
    group_id: str
    name: str
    description: Optional[str] = None
    tenant_id: str

class SubgroupInDB(SubgroupCreate):
    id: str
    created_at: str

class AccountCreate(BaseModel):
    subgroup_id: str
    name: str
    balance: float
    tenant_id: str

class AccountInDB(AccountCreate):
    id: str
    created_at: str
