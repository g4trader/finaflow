from fastapi import APIRouter, Depends
from app.services.reporting import cash_flow_summary
from app.services.dependencies import get_current_active_user

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/cash-flow")
async def cash_flow(group_by: str = "month", current=Depends(get_current_active_user)):
    return await cash_flow_summary(group_by)
