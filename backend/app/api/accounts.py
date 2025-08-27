"""API routes for account operations."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.db.bq_client import delete, insert, query, update
from app.models.finance import AccountCreate, AccountInDB
from app.services.dependencies import get_current_user, tenant


router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/", response_model=list[AccountInDB])
async def list_accounts(
    current=Depends(get_current_user), tenant_id: str = Depends(tenant)
):
    return await query("Accounts", {"tenant_id": tenant_id})


@router.post("/", response_model=AccountInDB, status_code=201)
async def create_account(
    account: AccountCreate, current=Depends(get_current_user), tenant_id: str = Depends(tenant)
):
    if account.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")

    new_id = str(uuid4())
    record = account.dict()
    record["id"] = new_id
    await insert("Accounts", record)
    return record


@router.get("/{account_id}", response_model=AccountInDB)
async def get_account(
    account_id: str, current=Depends(get_current_user), tenant_id: str = Depends(tenant)
):
    res = await query("Accounts", {"id": account_id, "tenant_id": tenant_id})
    if not res:
        raise HTTPException(status_code=404, detail="Account not found")
    return res[0]


@router.put("/{account_id}", response_model=AccountInDB)
async def update_account(
    account_id: str,
    account: AccountCreate,
    current=Depends(get_current_user),
    tenant_id: str = Depends(tenant),
):
    if account.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")

    existing = await query("Accounts", {"id": account_id, "tenant_id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Account not found")

    await update("Accounts", account_id, account.dict())
    return {**existing[0], **account.dict(), "id": account_id}


@router.delete("/{account_id}", status_code=204)
async def delete_account(
    account_id: str, current=Depends(get_current_user), tenant_id: str = Depends(tenant)
):
    existing = await query("Accounts", {"id": account_id, "tenant_id": tenant_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Account not found")

    await delete("Accounts", account_id)


@router.post("/load_initial_data", response_model=list[AccountInDB], status_code=201)
async def load_initial_data(
    accounts: list[AccountCreate],
    current=Depends(get_current_user),
    tenant_id: str = Depends(tenant),
):
    """Bulk insert a list of accounts for the given tenant."""
    records: list[AccountInDB] = []
    for account in accounts:
        if account.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Access denied to this tenant")
        new_id = str(uuid4())
        record = account.dict()
        record["id"] = new_id
        await insert("Accounts", record)
        records.append(record)
    return records

