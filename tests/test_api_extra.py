import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from app.main import app
from app.schemas.telemetry import Telemetry
from app.schemas.telemetry_stats import TelemetryStats
from fastapi import HTTPException


@pytest.fixture(autouse=True)
def set_keys(monkeypatch):
    from app.core import config
    monkeypatch.setattr(config.settings, "IOT_API_KEY", "test-iot-key")
    monkeypatch.setattr(config.settings, "GRAFANA_API_KEY", "test-grafana-key")
    yield


# -------------------- POST /telemetry edge cases -------------------- #
@pytest.mark.asyncio
async def test_post_telemetry_invalid_data(monkeypatch):
    """Validation check: send invalid data"""
    sample = {"device_id": "", "temperature": "hot", "humidity": -10}

    async def fake_process(data, session):
        return data  # this test checks FastAPI/Pydantic validation

    monkeypatch.setattr("app.services.telemetry_service_v2.TelemetryService.process", fake_process)

    async def noop_init_db(engine):
        return None
    monkeypatch.setattr("app.main.init_db", noop_init_db)

    async def fake_get_session():
        yield None
    monkeypatch.setattr("app.db.deps.get_session", fake_get_session)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # no key => unauthorized
            r = await ac.post("/telemetry", json=sample)
            assert r.status_code == 401

            # wrong key
            r = await ac.post(
                "/telemetry",
                json=sample,
                headers={"X-API-Key": "wrong"},
            )
            assert r.status_code == 403

            # valid key
            r = await ac.post(
                "/telemetry",
                json=sample,
                headers={"X-API-Key": "test-iot-key"},
            )
            assert r.status_code == 422  # validation error


@pytest.mark.asyncio
async def test_post_telemetry_service_error(monkeypatch):
    """Simulate exception inside the service → check 500 response"""
    sample = {"device_id": "node-03", "temperature": 22.0, "humidity": 55.0}

    async def fake_process(data, session):
        raise Exception("Something went wrong")

    monkeypatch.setattr("app.services.telemetry_service_v2.TelemetryService.process", fake_process)

    async def noop_init_db(engine):
        return None
    monkeypatch.setattr("app.main.init_db", noop_init_db)

    async def fake_get_session():
        yield None
    monkeypatch.setattr("app.db.deps.get_session", fake_get_session)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # should require key
            r = await ac.post("/telemetry", json=sample)
            assert r.status_code == 401

            r = await ac.post(
                "/telemetry",
                json=sample,
                headers={"X-API-Key": "test-iot-key"},
            )
            assert r.status_code == 500


# -------------------- GET /telemetry/{device_id}/stats edge cases -------------------- #
@pytest.mark.asyncio
async def test_get_stats_nonexistent_device(monkeypatch):
    """Request stats for a non-existent device → empty list"""
    async def fake_get_stats(device_id, interval, start, end, session):
        return []

    monkeypatch.setattr("app.services.telemetry_service_v2.TelemetryService.get_stats", fake_get_stats)

    async def noop_init_db(engine):
        return None
    monkeypatch.setattr("app.main.init_db", noop_init_db)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # no header should be rejected
            r = await ac.get("/telemetry/nonexistent-device/stats?interval=1h")
            assert r.status_code == 401

            # valid key returns empty list for unknown device
            r = await ac.get(
                "/telemetry/nonexistent-device/stats?interval=1h",
                headers={"X-API-Key": "test-grafana-key"},
            )
            assert r.status_code == 200
            assert r.json() == []


@pytest.mark.asyncio
async def test_get_stats_service_error(monkeypatch):
    """Simulate service error during GET stats → check 500 response"""
    async def fake_get_stats(device_id, interval, start, end, session):
        raise Exception("Database error")

    monkeypatch.setattr("app.services.telemetry_service_v2.TelemetryService.get_stats", fake_get_stats)

    async def noop_init_db(engine):
        return None
    monkeypatch.setattr("app.main.init_db", noop_init_db)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # missing key => unauthorized
            r = await ac.get("/telemetry/iot-microclimate-node-02/stats?interval=1h")
            assert r.status_code == 401

            # include correct key; service error should then return 500
            r = await ac.get(
                "/telemetry/iot-microclimate-node-02/stats?interval=1h",
                headers={"X-API-Key": "test-grafana-key"},
            )
            assert r.status_code == 500