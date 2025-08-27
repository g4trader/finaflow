"""API routes for forecast operations."""

from datetime import datetime
from uuid import uuid4

import asyncio
from fastapi import APIRouter, Depends, HTTPException

from app.db.bq_client import delete, insert, query, update
from app.models.finance import ForecastCreate, ForecastInDB
from app.services.dependencies import get_current_user, tenant

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/", response_model=list[ForecastInDB])
async def list_forecasts(
    current=Depends(get_current_user), tenant_id: str = Depends(tenant)
):
    return await asyncio.to_thread(query, "Forecasts", {"tenant_id": tenant_id})


@router.post("/", response_model=ForecastInDB, status_code=201)
async def create_forecast(
    forecast: ForecastCreate,
    current=Depends(get_current_user),
    tenant_id: str = Depends(tenant),
):
    if forecast.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")

    new_id = str(uuid4())
    record = forecast.dict()
    record["id"] = new_id
    record["created_at"] = datetime.utcnow()
    await asyncio.to_thread(insert, "Forecasts", record)
    return record


@router.put("/{forecast_id}", response_model=ForecastInDB)
async def update_forecast(
    forecast_id: str,
    forecast: ForecastCreate,
    current=Depends(get_current_user),
    tenant_id: str = Depends(tenant),
):
    if forecast.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")

    existing = await asyncio.to_thread(
        query, "Forecasts", {"id": forecast_id, "tenant_id": tenant_id}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Forecast not found")

    await asyncio.to_thread(update, "Forecasts", forecast_id, forecast.dict())
    return {**existing[0], **forecast.dict(), "id": forecast_id}


@router.delete("/{forecast_id}", status_code=204)
async def delete_forecast(
    forecast_id: str, current=Depends(get_current_user), tenant_id: str = Depends(tenant)
):
    existing = await asyncio.to_thread(
        query, "Forecasts", {"id": forecast_id, "tenant_id": tenant_id}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Forecast not found")

    await asyncio.to_thread(delete, "Forecasts", forecast_id)
