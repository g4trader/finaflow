from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.db.bq_client import delete, insert, query, update
from app.models.finance import SubgroupCreate, SubgroupInDB
from app.services.dependencies import get_current_user, tenant


router = APIRouter(prefix="/subgroups", tags=["subgroups"])


@router.get("/", response_model=list[SubgroupInDB])
async def list_subgroups(
    current=Depends(get_current_user), tenant_id: str = Depends(tenant)
):
    return await query("Subgroups", {"tenant_id": tenant_id})


@router.post("/", response_model=SubgroupInDB, status_code=201)
async def create_subgroup(
    subgroup: SubgroupCreate, current=Depends(get_current_user), tenant_id: str = Depends(tenant)
):
    if subgroup.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")

    new_id = str(uuid4())
    record = subgroup.dict()
    record["id"] = new_id
    await insert("Subgroups", record)
    return record


@router.get("/{subgroup_id}", response_model=SubgroupInDB)
async def get_subgroup(
    subgroup_id: str, current=Depends(get_current_user), tenant_id: str = Depends(tenant)
):
    res = await query("Subgroups", {"id": subgroup_id, "tenant_id": tenant_id})
    if not res:
        raise HTTPException(status_code=404, detail="Subgroup not found")
    return res[0]


@router.put("/{subgroup_id}", response_model=SubgroupInDB)
async def update_subgroup(
    subgroup_id: str,
    subgroup: SubgroupCreate,
    current=Depends(get_current_user),
    tenant_id: str = Depends(tenant),
):
    if subgroup.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")

    existing = await query("Subgroups", {"id": subgroup_id, "tenant_id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Subgroup not found")

    await update("Subgroups", subgroup_id, subgroup.dict())
    return {**existing[0], **subgroup.dict(), "id": subgroup_id}


@router.delete("/{subgroup_id}", status_code=204)
async def delete_subgroup(
    subgroup_id: str, current=Depends(get_current_user), tenant_id: str = Depends(tenant)
):
    existing = await query("Subgroups", {"id": subgroup_id, "tenant_id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Subgroup not found")

    await delete("Subgroups", subgroup_id)

