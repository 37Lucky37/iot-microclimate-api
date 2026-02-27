from pydantic import BaseModel
from datetime import datetime


class TelemetryStats(BaseModel):
    bucket: datetime
    avg_temperature: float
    avg_humidity: float
