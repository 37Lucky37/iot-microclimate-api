from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Telemetry(BaseModel):
    device_id: str = Field(..., max_length=100, example="iot-microclimate-node-01")

    temperature: float = Field(
        ...,
        ge=-40,
        le=85,
        example=23.9,
        description="Temperature in Celsius"
    )

    humidity: float = Field(
        ...,
        ge=0,
        le=100,
        example=62.9,
        description="Relative humidity in %"
    )

    timestamp: Optional[datetime] = Field(
        None,
        description="UTC timestamp in ISO 8601 format"
    )