from fastapi import APIRouter, Depends, HTTPException
from app.db.bq_client import delete, query
from app.services.dependencies import get_current_active_user, require_tenant_access

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(transaction_id: str, current=Depends(get_current_active_user)):
    records = await query("Transactions", {"id": transaction_id})
    if not records:
        raise HTTPException(status_code=404, detail="Transaction not found")
    record = records[0]
    require_tenant_access(record["tenant_id"], current)
    await delete("Transactions", transaction_id)
