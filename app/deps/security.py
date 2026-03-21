# app/deps/security.py
from fastapi import Header, HTTPException, Request
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


def mask_api_key(key: Optional[str]) -> str:
    """Повертає замасковане значення ключа для логів."""
    if not key:
        return "<empty>"
    if len(key) <= 4:
        return "***"
    return f"{key[:2]}***{key[-2:]}"


# Backward compatible alias (назва з підкресленням не є публічною, але може бути використана раніше)
def _mask_key(key: Optional[str]) -> str:
    return mask_api_key(key)


async def verify_iot_key(
    request: Request,
    x_api_key: str | None = Header(None),
):
    """Перевірка API key для AWS IoT (POST).

    - `401` when header is missing.
    - `403` when provided key does not match configuration.
    """
    if x_api_key is None:
        logger.warning("Missing IoT API key header from %s", request.client.host if request.client else "unknown")
        raise HTTPException(status_code=401, detail="Unauthorized: IoT API Key required")

    if x_api_key != settings.IOT_API_KEY:
        logger.warning(
            "Invalid IoT API key received (masked=%s) from %s",
            mask_api_key(x_api_key),
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(status_code=403, detail="Forbidden: Invalid IoT API Key")

    return x_api_key


async def verify_grafana_key(
    request: Request,
    x_api_key: str | None = Header(None),
):
    """Перевірка API key для Grafana (GET).

    - `401` when header is missing.
    - `403` when provided key does not match configuration.
    """
    if x_api_key is None:
        logger.warning("Missing Grafana API key header from %s", request.client.host if request.client else "unknown")
        raise HTTPException(status_code=401, detail="Unauthorized: Grafana API Key required")

    if x_api_key != settings.GRAFANA_API_KEY:
        logger.warning(
            "Invalid Grafana API key received (masked=%s) from %s",
            mask_api_key(x_api_key),
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Grafana API Key")

    return x_api_key