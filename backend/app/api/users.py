from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4

import asyncio

from app.models.user import UserCreate, UserInDB
from app.services.security import hash_password
from app.services.dependencies import require_super_admin, get_current_active_user
from app.db.bq_client import delete, insert, query

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=list[UserInDB])
async def list_users(current=Depends(get_current_active_user)):
    # exemplo: super_admin vê todos; tenant_user pode filtrar
    return await asyncio.to_thread(query, "Users", {})

@router.post("/", response_model=UserInDB, status_code=201)
async def create_user(user: UserCreate, current=Depends(require_super_admin)):
    hashed = hash_password(user.password)
    user_id = str(uuid4())
    record = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed,
        "role": user.role.value,
        "tenant_id": user.tenant_id,
    }
    await asyncio.to_thread(insert, "Users", record)
    return record

@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: str, current=Depends(require_super_admin)):
    await asyncio.to_thread(delete, "Users", user_id)
