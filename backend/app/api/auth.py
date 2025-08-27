from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from uuid import uuid4

import asyncio

from app.models.user import UserCreate, UserInDB, Role
from app.services.security import hash_password, verify_password, create_access_token
from app.services.dependencies import get_current_active_user, require_super_admin
from app.db.bq_client import insert, query_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", status_code=201)
async def signup(user: UserCreate, current=Depends(require_super_admin)):
    if user.role == Role.tenant_user and not user.tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id required for tenant_user")
    if user.role == Role.super_admin:
        user.tenant_id = None
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
    return {"id": user_id}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    results = await asyncio.to_thread(query_user, form_data.username)
    if not results:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    user = UserInDB(**results[0])
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": user.id, "role": user.role.value, "tenant_id": user.tenant_id})
    return {"access_token": token, "token_type": "bearer"}
