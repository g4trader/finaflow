from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4

import asyncio

from app.models.finance import GroupCreate, GroupInDB
from app.services.dependencies import (
    get_current_active_user,
    require_super_admin,
    require_tenant_access,
)
from app.db.bq_client import insert, query

router = APIRouter(prefix="/groups", tags=["groups"])

@router.get("/", response_model=list[GroupInDB])
async def list_groups(current=Depends(get_current_active_user)):
    if current.role.value == "tenant_user":
        return await asyncio.to_thread(query, "Groups", {"tenant_id": current.tenant_id})
    return await asyncio.to_thread(query, "Groups", {})

@router.post("/", response_model=GroupInDB, status_code=201)
async def create_group(group: GroupCreate, current=Depends(require_super_admin)):
    gid = str(uuid4())
    rec = group.dict()
    rec["id"] = gid
    await asyncio.to_thread(insert, "Groups", rec)
    return rec
