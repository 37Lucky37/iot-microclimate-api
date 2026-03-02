# app/deps/security.py
from fastapi import Header, HTTPException, Request
import logging
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


def _mask_key(key: Optional[str]) -> str:
    """Повертає замасковане значення ключа для логів."""
    if not key:
        return "<empty>"
    if len(key) <= 4:
        return "***"
    return f"{key[:2]}***{key[-2:]}"


class RateLimiter:
    """Простий in-memory rate limiter по API key."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._store: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> bool:
        """True якщо запит дозволено, False якщо ліміт вичерпано."""
        now = time.time()
        window_start = now - self.window_seconds
        q = self._store[key]

        # очищаємо старі записи
        while q and q[0] < window_start:
            q.popleft()

        if len(q) >= self.max_requests:
            return False

        q.append(now)
        return True


# Окремі лімітери для IoT POST та Grafana GET (конфігуровані через Settings)
_iot_rate_limiter = RateLimiter(
    max_requests=settings.IOT_RATE_LIMIT_MAX_REQUESTS,
    window_seconds=settings.IOT_RATE_LIMIT_WINDOW_SECONDS,
)
_grafana_rate_limiter = RateLimiter(
    max_requests=settings.GRAFANA_RATE_LIMIT_MAX_REQUESTS,
    window_seconds=settings.GRAFANA_RATE_LIMIT_WINDOW_SECONDS,
)


async def verify_iot_key(
    request: Request,
    x_api_key: str | None = Header(None),
):
    """Перевірка API key для AWS IoT (POST) + rate limiting.

    - `401` when header is missing.
    - `403` when provided key does not match configuration.
    - `429` when too many requests with same key.
    """
    if x_api_key is None:
        logger.warning("Missing IoT API key header from %s", request.client.host if request.client else "unknown")
        raise HTTPException(status_code=401, detail="Unauthorized: IoT API Key required")

    if x_api_key != settings.IOT_API_KEY:
        logger.warning(
            "Invalid IoT API key received (masked=%s) from %s",
            _mask_key(x_api_key),
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(status_code=403, detail="Forbidden: Invalid IoT API Key")

    if not _iot_rate_limiter.check(x_api_key):
        logger.warning(
            "IoT rate limit exceeded for key (masked=%s) from %s",
            _mask_key(x_api_key),
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(status_code=429, detail="Too Many Requests: IoT rate limit exceeded")

    return x_api_key


async def verify_grafana_key(
    request: Request,
    x_api_key: str | None = Header(None),
):
    """Перевірка API key для Grafana (GET) + rate limiting.

    - `401` when header is missing.
    - `403` when provided key does not match configuration.
    - `429` when too many requests with same key.
    """
    if x_api_key is None:
        logger.warning("Missing Grafana API key header from %s", request.client.host if request.client else "unknown")
        raise HTTPException(status_code=401, detail="Unauthorized: Grafana API Key required")

    if x_api_key != settings.GRAFANA_API_KEY:
        logger.warning(
            "Invalid Grafana API key received (masked=%s) from %s",
            _mask_key(x_api_key),
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Grafana API Key")

    if not _grafana_rate_limiter.check(x_api_key):
        logger.warning(
            "Grafana rate limit exceeded for key (masked=%s) from %s",
            _mask_key(x_api_key),
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(status_code=429, detail="Too Many Requests: Grafana rate limit exceeded")

    return x_api_key