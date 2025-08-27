from fastapi import APIRouter, Depends
from uuid import uuid4
from pathlib import Path
import csv

from app.models.group import GroupCreate
from app.models.subgroup import SubgroupCreate
from app.models.account import AccountCreate
from app.services.dependencies import require_super_admin
from app.db.bq_client import insert

router = APIRouter(prefix="/accounts", tags=["accounts"])

REQUIRED_COLUMNS = {"Conta", "Subgrupo", "Grupo", "Escolha"}

@router.post("/init/{tenant_id}")
async def load_initial_data(tenant_id: str, current=Depends(require_super_admin)):
    base_dir = Path(__file__).resolve().parents[3] / "csv"
    group_ids = {}
    subgroup_ids = {}
    counts = {"groups": 0, "subgroups": 0, "accounts": 0}

    for csv_path in base_dir.glob("*.csv"):
        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fields = {field for field in reader.fieldnames if field}
            if not REQUIRED_COLUMNS.issubset(fields):
                continue
            for row in reader:
                if row.get("Escolha", "").strip().lower() != "usar":
                    continue
                group_name = row["Grupo"].strip()
                subgroup_name = row["Subgrupo"].strip()
                account_name = row["Conta"].strip()

                if group_name not in group_ids:
                    gid = str(uuid4())
                    group = GroupCreate(name=group_name, tenant_id=tenant_id)
                    await insert("Groups", {"id": gid, **group.dict()})
                    group_ids[group_name] = gid
                    counts["groups"] += 1
                if (group_name, subgroup_name) not in subgroup_ids:
                    sgid = str(uuid4())
                    subgroup = SubgroupCreate(group_id=group_ids[group_name], name=subgroup_name, tenant_id=tenant_id)
                    await insert("Subgroups", {"id": sgid, **subgroup.dict()})
                    subgroup_ids[(group_name, subgroup_name)] = sgid
                    counts["subgroups"] += 1
                aid = str(uuid4())
                account = AccountCreate(subgroup_id=subgroup_ids[(group_name, subgroup_name)], name=account_name, balance=0.0, tenant_id=tenant_id)
                await insert("Accounts", {"id": aid, **account.dict()})
                counts["accounts"] += 1
    return counts
