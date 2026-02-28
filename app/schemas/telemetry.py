from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Telemetry(BaseModel):
    device_id: str = Field(..., max_length=100, json_schema_extra={"example": "iot-microclimate-node-01"})

    temperature: float = Field(
        ...,
        ge=-40,
        le=85,
        json_schema_extra={"example": 24.0},
        description="Temperature in Celsius"
    )

    humidity: float = Field(
        ...,
        ge=0,
        le=100,
        json_schema_extra={"example": 60.0},
        description="Relative humidity in %"
    )

    timestamp: Optional[datetime] = Field(
        None,
        description="UTC timestamp in ISO 8601 format"
    )