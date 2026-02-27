from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass


class TelemetryDB(Base):
    __tablename__ = "telemetry"

    device_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    temperature: Mapped[float] = mapped_column(Float)
    humidity: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, index=True)
