"""API routes for transaction operations."""

from datetime import datetime
from uuid import uuid4

import asyncio
from fastapi import APIRouter, Depends, HTTPException

from app.db.bq_client import delete, insert, query, update
from app.models.finance import TransactionCreate, TransactionInDB
from app.services.dependencies import get_current_user, tenant

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=list[TransactionInDB])
async def list_transactions(
    current=Depends(get_current_user), tenant_id: str = Depends(tenant)
):
    return await asyncio.to_thread(query, "Transactions", {"tenant_id": tenant_id})


@router.post("/", response_model=TransactionInDB, status_code=201)
async def create_transaction(
    transaction: TransactionCreate,
    current=Depends(get_current_user),
    tenant_id: str = Depends(tenant),
):
    if transaction.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")

    new_id = str(uuid4())
    record = transaction.dict()
    record["id"] = new_id
    record["created_at"] = datetime.utcnow()
    await asyncio.to_thread(insert, "Transactions", record)
    return record


@router.put("/{transaction_id}", response_model=TransactionInDB)
async def update_transaction(
    transaction_id: str,
    transaction: TransactionCreate,
    current=Depends(get_current_user),
    tenant_id: str = Depends(tenant),
):
    if transaction.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")

    existing = await asyncio.to_thread(
        query, "Transactions", {"id": transaction_id, "tenant_id": tenant_id}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Transaction not found")

    await asyncio.to_thread(update, "Transactions", transaction_id, transaction.dict())
    return {**existing[0], **transaction.dict(), "id": transaction_id}


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: str, current=Depends(get_current_user), tenant_id: str = Depends(tenant)
):
    existing = await asyncio.to_thread(
        query, "Transactions", {"id": transaction_id, "tenant_id": tenant_id}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Transaction not found")

    await asyncio.to_thread(delete, "Transactions", transaction_id)
