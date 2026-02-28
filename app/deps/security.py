# app/deps/security.py
from fastapi import Header, HTTPException
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def verify_iot_key(x_api_key: str | None = Header(None)):
    """Перевірка API key для AWS IoT (POST).

    - `401` when header is missing.
    - `403` when provided key does not match configuration.
    """
    if x_api_key is None:
        logger.warning("Missing IoT API key header")
        raise HTTPException(status_code=401, detail="Unauthorized: IoT API Key required")

    if x_api_key != settings.IOT_API_KEY:
        logger.warning("Invalid IoT API key received: %s", x_api_key)
        raise HTTPException(status_code=403, detail="Forbidden: Invalid IoT API Key")

async def verify_grafana_key(x_api_key: str | None = Header(None)):
    """Перевірка API key для Grafana (GET).

    - `401` when header is missing.
    - `403` when provided key does not match configuration.
    """
    if x_api_key is None:
        logger.warning("Missing Grafana API key header")
        raise HTTPException(status_code=401, detail="Unauthorized: Grafana API Key required")

    if x_api_key != settings.GRAFANA_API_KEY:
        logger.warning("Invalid Grafana API key received: %s", x_api_key)
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Grafana API Key")