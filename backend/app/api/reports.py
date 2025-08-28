from typing import Literal

from fastapi import APIRouter, Depends

from app.services.reporting import cash_flow_summary
from app.services.dependencies import get_current_active_user, tenant

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/cash-flow")
async def cash_flow(
    group_by: Literal["month", "day"] = "month",
    tenant_id: str = Depends(tenant),
    current=Depends(get_current_active_user),
):
    return await cash_flow_summary(group_by, tenant_id)
