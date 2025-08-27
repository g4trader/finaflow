from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tenant_id: str

class GroupInDB(GroupCreate):
    id: str
    created_at: datetime

class SubgroupCreate(BaseModel):
    group_id: str
    name: str
    description: Optional[str] = None
    tenant_id: str

class SubgroupInDB(SubgroupCreate):
    id: str
    created_at: datetime

class AccountCreate(BaseModel):
    subgroup_id: str
    name: str
    balance: Decimal
    tenant_id: str

class AccountInDB(AccountCreate):
    id: str
    created_at: datetime


class AccountImportSummary(BaseModel):
    inserted: list[AccountInDB]
    skipped: list[dict]
