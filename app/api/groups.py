from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4

import asyncio

from app.models.finance import GroupCreate, GroupInDB
from app.services.dependencies import (
    get_current_user,
    require_super_admin,
    require_tenant_access,
)
from app.db.bq_client import delete, insert, query, update

router = APIRouter(prefix="/groups", tags=["groups"])

@router.get("/", response_model=list[GroupInDB])
async def list_groups(current=Depends(get_current_user)):
    if current.role == "tenant_user":
        return await asyncio.to_thread(query, "Groups", {"tenant_id": current.tenant_id})
    return await asyncio.to_thread(query, "Groups", {})

@router.post("/", response_model=GroupInDB, status_code=201)
async def create_group(group: GroupCreate, current=Depends(require_super_admin)):
    gid = str(uuid4())
    rec = group.dict()
    rec["id"] = gid
    await asyncio.to_thread(insert, "Groups", rec)
    return rec


@router.put("/{group_id}", response_model=GroupInDB)
async def update_group(group_id: str, group: GroupCreate, current=Depends(get_current_user)):
    existing = await asyncio.to_thread(query, "Groups", {"id": group_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Group not found")

    tenant_id = existing[0]["tenant_id"]
    require_tenant_access(tenant_id, current)

    if group.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")

    await asyncio.to_thread(update, "Groups", group_id, group.dict())
    return {**existing[0], **group.dict(), "id": group_id}


@router.delete("/{group_id}", status_code=204)
async def delete_group(group_id: str, current=Depends(get_current_user)):
    existing = await asyncio.to_thread(query, "Groups", {"id": group_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Group not found")

    tenant_id = existing[0]["tenant_id"]
    require_tenant_access(tenant_id, current)

    await asyncio.to_thread(delete, "Groups", group_id)
