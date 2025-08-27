from fastapi import APIRouter, Depends
from uuid import uuid4
from app.models.transaction import TransactionCreate, TransactionInDB
from app.services.dependencies import get_current_active_user, require_tenant_access
from app.db.bq_client import query, insert, update, delete

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("/", response_model=list[TransactionInDB])
async def list_transactions(current=Depends(get_current_active_user)):
    if current.role.value == "tenant_user":
        return await query("Transactions", {"tenant_id": current.tenant_id})
    return await query("Transactions", {})

@router.post("/", response_model=TransactionInDB, status_code=201)
async def create_transaction(tx: TransactionCreate, current=Depends(get_current_active_user)):
    require_tenant_access(tx.tenant_id, current)
    tx_id = str(uuid4())
    record = tx.dict(); record["id"] = tx_id
    await insert("Transactions", record)
    return record

@router.put("/{tx_id}", response_model=TransactionInDB)
async def update_transaction(tx_id: str, tx: TransactionCreate, current=Depends(get_current_active_user)):
    require_tenant_access(tx.tenant_id, current)
    data = tx.dict()
    await update("Transactions", tx_id, data)
    return {"id": tx_id, **data}

@router.delete("/{tx_id}", status_code=204)
async def delete_transaction(tx_id: str, current=Depends(get_current_active_user)):
    # tenant check would normally load record to get tenant_id
    await delete("Transactions", tx_id)
