import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from app.main import app
from app.schemas.telemetry import Telemetry


# --------------------- Fixtures ---------------------
@pytest.fixture
def sample_telemetry():
    return {
        "device_id": "iot-microclimate-node-02",
        "temperature": 24.1,
        "humidity": 60.0
    }


@pytest.fixture(autouse=True)
def set_keys(monkeypatch):
    # ensure predictable API key values during tests
    from app.core import config
    monkeypatch.setattr(config.settings, "IOT_API_KEY", "test-iot-key")
    yield


@pytest.fixture
def fake_telemetry_service(monkeypatch):
    async def fake_process(data, session):
        if isinstance(data, Telemetry):
            return data
        return Telemetry(**data)

    monkeypatch.setattr(
        "app.services.telemetry_service.TelemetryService.process", fake_process
    )


@pytest.fixture
def fake_db(monkeypatch):
    async def noop_init_db(engine):
        return None
    monkeypatch.setattr("app.main.init_db", noop_init_db)

    async def fake_get_session():
        yield None
    monkeypatch.setattr("app.db.deps.get_session", fake_get_session)


# --------------------- Tests ---------------------
@pytest.mark.asyncio
async def test_post_telemetry_monkeypatch(sample_telemetry, fake_telemetry_service, fake_db):
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # missing header should be rejected
            r = await ac.post("/telemetry", json=sample_telemetry)
            assert r.status_code == 401

            # wrong key
            r = await ac.post(
                "/telemetry",
                json=sample_telemetry,
                headers={"X-API-Key": "wrong"},
            )
            assert r.status_code == 403

            # correct key
            r = await ac.post(
                "/telemetry",
                json=sample_telemetry,
                headers={"X-API-Key": "test-iot-key"},
            )
            assert r.status_code == 200

            # Валідація через Pydantic
            body = Telemetry(**r.json())
            assert body.device_id == sample_telemetry["device_id"]
            assert body.temperature == sample_telemetry["temperature"]
            assert body.humidity == sample_telemetry["humidity"]



# Тимчасово вимкнено, бо GET endpoints для читання телеметрії не використовуються:
# - test_get_stats_empty
# - test_get_telemetry_empty
# - test_get_stats_returns_buckets