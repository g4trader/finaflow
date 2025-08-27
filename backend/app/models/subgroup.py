from pydantic import BaseModel
from typing import Optional

class SubgroupCreate(BaseModel):
    group_id: str
    name: str
    description: Optional[str] = None
    tenant_id: str

class SubgroupInDB(SubgroupCreate):
    id: str
    created_at: str
