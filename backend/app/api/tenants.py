from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4
from app.models.tenant import TenantCreate, TenantInDB
from app.services.dependencies import require_super_admin, get_current_active_user
from app.db.bq_client import insert, query

router = APIRouter(prefix="/tenants", tags=["tenants"])

@router.get("/", response_model=list[TenantInDB])
async def list_tenants(current=Depends(get_current_active_user)):
    return await query("Tenants", {})

@router.post("/", response_model=TenantInDB, status_code=201)
async def create_tenant(tenant: TenantCreate, current=Depends(require_super_admin)):
    new_id = str(uuid4())
    record = tenant.dict()
    record["id"] = new_id
    await insert("Tenants", record)
    return record

@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(tenant_id: str, current=Depends(require_super_admin)):
    await delete("Tenants", tenant_id)
