from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List, Optional
import logging
from app.schemas.telemetry import Telemetry
from app.schemas.telemetry_stats import TelemetryStats
from app.services.telemetry_service_v2 import TelemetryService
from app.db.deps import get_session

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/telemetry", response_model=Telemetry)
async def receive_telemetry(
    data: Telemetry,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await TelemetryService.process(data, session)
    except Exception as e:
        logger.exception("Failed to receive telemetry")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/telemetry/{device_id}", response_model=List[Telemetry])
async def get_telemetry_by_device(
    device_id: str,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await TelemetryService.get_by_device(device_id, start, end, limit, session)
    except Exception:
        logger.exception("Telemetry processing failed")
        raise HTTPException(500, "Internal server error")


@router.get("/telemetry/{device_id}/stats", response_model=List[TelemetryStats])
async def get_telemetry_stats(
    device_id: str,
    interval: str = "1h",
    start: datetime | None = None,
    end: datetime | None = None,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await TelemetryService.get_stats(device_id, interval, start, end, session)
    except Exception as e:
        logger.exception("Telemetry stats failed")
        # expose underlying error for easier debugging
        raise HTTPException(500, detail=str(e))