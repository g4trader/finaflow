from pydantic import BaseModel
from typing import Optional

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tenant_id: str

class GroupInDB(GroupCreate):
    id: str
    created_at: str
