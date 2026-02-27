import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timezone
from typing import List, Optional
from app.schemas.telemetry import Telemetry
from app.schemas.telemetry_stats import TelemetryStats
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

    @staticmethod
    async def get_stats(
        device_id: str,
        interval: str = "1h",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        session: AsyncSession = None
    ) -> List[TelemetryStats]:

        try:
            # Build filter conditions
            conditions = [TelemetryDB.device_id == device_id]
            if start is not None:
                conditions.append(TelemetryDB.timestamp >= start)
            if end is not None:
                conditions.append(TelemetryDB.timestamp <= end)

            # build raw SQL expression for interval; bind parameters can't handle pystr->interval
            # simple validation to avoid SQL injection (allow digits, letters, spaces, and punctuation hmsdwy)
            if not isinstance(interval, str) or not interval.replace(' ', '').isalnum():
                raise ValueError("invalid interval format")
            interval_expr = text(f"'{interval}'::interval")
            bucket_expr = func.time_bucket(interval_expr, TelemetryDB.timestamp).label("bucket")

            # If caller didn't provide `start`, restrict results to the recent interval window
            # so we don't return old buckets when there are no new records in the requested window.
            if start is None:
                conditions.append(text(f"timestamp >= now() - '{interval}'::interval"))

            stmt = (
                select(
                    bucket_expr,
                    func.avg(TelemetryDB.temperature).label("avg_temperature"),
                    func.avg(TelemetryDB.humidity).label("avg_humidity"),
                )
                .where(*conditions)
                .group_by(bucket_expr)
                .order_by(bucket_expr.desc())
            )

            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                logger.info("No telemetry records found for device %s in interval %s", device_id, interval)
                return []

            return [
                TelemetryStats(
                    bucket=r.bucket,
                    avg_temperature=float(r.avg_temperature) if r.avg_temperature is not None else 0.0,
                    avg_humidity=float(r.avg_humidity) if r.avg_humidity is not None else 0.0,
                )
                for r in rows
            ]
        except Exception as e:
            logger.exception("Failed to compute stats")
            raise
