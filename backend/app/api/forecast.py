from fastapi import APIRouter, Depends
from uuid import uuid4
from app.models.forecast import ForecastCreate, ForecastInDB
from app.services.dependencies import get_current_active_user, require_tenant_access
from app.db.bq_client import query, insert, update, delete

router = APIRouter(prefix="/forecast", tags=["forecast"])

@router.get("/", response_model=list[ForecastInDB])
async def list_forecasts(current=Depends(get_current_active_user)):
    if current.role.value == "tenant_user":
        return await query("Forecasts", {"tenant_id": current.tenant_id})
    return await query("Forecasts", {})

@router.post("/", response_model=ForecastInDB, status_code=201)
async def create_forecast(fc: ForecastCreate, current=Depends(get_current_active_user)):
    require_tenant_access(fc.tenant_id, current)
    fid = str(uuid4())
    record = fc.dict(); record["id"] = fid
    await insert("Forecasts", record)
    return record

@router.put("/{forecast_id}", response_model=ForecastInDB)
async def update_forecast(forecast_id: str, fc: ForecastCreate, current=Depends(get_current_active_user)):
    require_tenant_access(fc.tenant_id, current)
    data = fc.dict()
    await update("Forecasts", forecast_id, data)
    return {"id": forecast_id, **data}

@router.delete("/{forecast_id}", status_code=204)
async def delete_forecast(forecast_id: str, current=Depends(get_current_active_user)):
    await delete("Forecasts", forecast_id)
