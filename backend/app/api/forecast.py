from fastapi import APIRouter, Depends, HTTPException
from app.db.bq_client import delete, query
from app.services.dependencies import get_current_active_user, require_tenant_access

router = APIRouter(prefix="/forecast", tags=["forecast"])

@router.delete("/{forecast_id}", status_code=204)
async def delete_forecast(forecast_id: str, current=Depends(get_current_active_user)):
    records = await query("Forecasts", {"id": forecast_id})
    if not records:
        raise HTTPException(status_code=404, detail="Forecast not found")
    record = records[0]
    require_tenant_access(record["tenant_id"], current)
    await delete("Forecasts", forecast_id)
