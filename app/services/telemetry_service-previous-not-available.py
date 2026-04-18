from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from typing import List, Optional
from app.schemas.telemetry import Telemetry
from app.schemas.telemetry_stats import TelemetryStats
from app.models.telemetry_model import TelemetryDB

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

    @staticmethod
    async def get_by_device(
        device_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
        session: AsyncSession = None
    ) -> List[Telemetry]:

        # Build filter conditions
        conditions = [TelemetryDB.device_id == device_id]
        if start is not None:
            conditions.append(TelemetryDB.timestamp >= start)
        if end is not None:
            conditions.append(TelemetryDB.timestamp <= end)

        stmt = (
            select(TelemetryDB)
            .where(*conditions)
            .order_by(TelemetryDB.timestamp.desc())
            .limit(limit)
        )

        result = await session.execute(stmt)
        records = result.scalars().all()

        return [
            Telemetry(
                device_id=r.device_id,
                temperature=r.temperature,
                humidity=r.humidity,
                timestamp=r.timestamp
            )
            for r in records
        ]