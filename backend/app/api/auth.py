from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from uuid import uuid4
from app.models.user import UserCreate, UserInDB, Role
from app.services import security
from app.services.dependencies import get_current_active_user, require_super_admin
from app.db import bq_client  # BigQuery client wrapper

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/signup", status_code=201)
async def signup(user: UserCreate, current=Depends(require_super_admin)):
    if user.role == Role.tenant_user and not user.tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required for tenant_user")
    if user.role == Role.super_admin:
        user.tenant_id = None

    hashed = security.hash_password(user.password)
    user_id = str(uuid4())
    record = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed,
        "role": user.role.value,
        "tenant_id": user.tenant_id,
    }
    await bq_client.insert("User", record)
    return {"id": user_id}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Query BigQuery for user by username
    results = await bq_client.query_user(form_data.username)
    if not results:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    user = UserInDB(**results[0])
    if not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = security.create_access_token({
        "sub": user.id,
        "role": user.role.value,
        "tenant_id": user.tenant_id,
    })
    return {"access_token": access_token, "token_type": "bearer"}
