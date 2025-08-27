from uuid import uuid4

import csv
import io
import logging
from typing import Any, Dict, Tuple

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile

from app.db import bq_client
from app.db.bq_client import delete, insert, query, update
from app.models.finance import AccountCreate, AccountInDB
from app.services.dependencies import get_current_user, tenant


router = APIRouter(prefix="/accounts", tags=["accounts"])

# Required columns for bulk CSV upload
REQUIRED_COLUMNS: set[str] = {"grupo", "subgrupo", "conta"}


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


@router.post("/import", status_code=201)
async def import_accounts(
    file: UploadFile = File(...),
    current=Depends(get_current_user),
    tenant_id: str = Depends(tenant),
):
    """Bulk import accounts, groups and subgroups from a CSV file."""

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV missing headers")

    # Normalize fieldnames for comparison
    headers = [h.lower() for h in reader.fieldnames if h]
    missing = REQUIRED_COLUMNS - set(headers)
    if missing:
        logging.error("Missing required columns: %s", ", ".join(sorted(missing)))
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(sorted(missing))}",
        )

    groups: Dict[str, Dict[str, Any]] = {}
    subgroups: Dict[Tuple[str, str], Dict[str, Any]] = {}
    accounts: list[Dict[str, Any]] = []

    for row in reader:
        lower = {k.lower(): v for k, v in row.items()}
        group_name = (lower.get("grupo") or "").strip()
        subgroup_name = (lower.get("subgrupo") or "").strip()
        account_name = (lower.get("conta") or "").strip()
        if not (group_name and subgroup_name and account_name):
            continue

        gkey = group_name.lower()
        if gkey not in groups:
            groups[gkey] = {
                "id": str(uuid4()),
                "name": group_name,
                "tenant_id": tenant_id,
            }

        sgkey = (gkey, subgroup_name.lower())
        if sgkey not in subgroups:
            subgroups[sgkey] = {
                "id": str(uuid4()),
                "group_id": groups[gkey]["id"],
                "name": subgroup_name,
                "tenant_id": tenant_id,
            }

        accounts.append(
            {
                "id": str(uuid4()),
                "name": account_name,
                "subgroup_id": subgroups[sgkey]["id"],
                "balance": 0.0,
                "tenant_id": tenant_id,
            }
        )

    if groups:
        bq_client.client.insert_rows_json(
            f"{bq_client.PROJECT_ID}.{bq_client.DATASET}.Groups",
            list(groups.values()),
        )

    if subgroups:
        bq_client.client.insert_rows_json(
            f"{bq_client.PROJECT_ID}.{bq_client.DATASET}.Subgroups",
            list(subgroups.values()),
        )

    if accounts:
        bq_client.client.insert_rows_json(
            f"{bq_client.PROJECT_ID}.{bq_client.DATASET}.Accounts",
            accounts,
        )

    return {
        "groups": len(groups),
        "subgroups": len(subgroups),
        "accounts": len(accounts),
    }

