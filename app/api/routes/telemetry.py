from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.schemas.telemetry import Telemetry
from app.services.telemetry_service import TelemetryService
from app.deps.security import mask_api_key, verify_iot_key
from app.db.deps import get_session

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/telemetry", response_model=Telemetry)
async def receive_telemetry(
    data: Telemetry,
    api_key: str = Depends(verify_iot_key),
    session: AsyncSession = Depends(get_session)
):
    # api_key is returned by the dependency for logging purposes
    logger.info(
        "Received telemetry POST for device '%s' using IoT key %s",
        data.device_id,
        mask_api_key(api_key),
    )
    try:
        return await TelemetryService.process(data, session)
    except Exception as e:
        logger.exception("Failed to receive telemetry")
        raise HTTPException(status_code=500, detail=str(e))
