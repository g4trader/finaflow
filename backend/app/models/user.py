from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional

class Role(str, Enum):
    super_admin = "super_admin"
    tenant_user = "tenant_user"

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Role
    tenant_id: Optional[str] = None

class UserInDB(BaseModel):
    id: str
    username: str
    email: EmailStr
    hashed_password: str
    role: Role
    tenant_id: Optional[str] = None
