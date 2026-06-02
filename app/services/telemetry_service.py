import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timezone
from app.schemas.telemetry import Telemetry
from app.models.telemetry_model import TelemetryDB

logger = logging.getLogger(__name__)

class TelemetryService:

    @staticmethod
    async def process(
        data: Telemetry,
        session: AsyncSession
    ) -> Telemetry:

        if data.timestamp is None:
            data.timestamp = datetime.now(timezone.utc)

        db_obj = TelemetryDB(
            device_id=data.device_id,
            temperature=data.temperature,
            humidity=data.humidity,
            timestamp=data.timestamp
        )

        session.add(db_obj)
        await session.commit()

        return data
