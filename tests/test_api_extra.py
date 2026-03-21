import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from app.main import app


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


# Тимчасово вимкнено, бо GET /telemetry/{device_id}/stats не використовується:
# - test_get_stats_nonexistent_device
# - test_get_stats_service_error