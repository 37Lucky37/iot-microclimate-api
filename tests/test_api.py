import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from app.main import app
from app.schemas.telemetry import Telemetry
from app.schemas.telemetry_stats import TelemetryStats


# --------------------- Fixtures ---------------------
@pytest.fixture
def sample_telemetry():
    return {
        "device_id": "iot-microclimate-node-02",
        "temperature": 24.1,
        "humidity": 60.0
    }


@pytest.fixture
def fake_telemetry_service(monkeypatch):
    async def fake_process(data, session):
        if isinstance(data, Telemetry):
            return data
        return Telemetry(**data)

    async def fake_get_stats(device_id, interval, start, end, session):
        return []

    monkeypatch.setattr(
        "app.services.telemetry_service_v2.TelemetryService.process", fake_process
    )
    monkeypatch.setattr(
        "app.services.telemetry_service_v2.TelemetryService.get_stats", fake_get_stats
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
            r = await ac.post("/telemetry", json=sample_telemetry)
            assert r.status_code == 200

            # Валідація через Pydantic
            body = Telemetry(**r.json())
            assert body.device_id == sample_telemetry["device_id"]
            assert body.temperature == sample_telemetry["temperature"]
            assert body.humidity == sample_telemetry["humidity"]


@pytest.mark.asyncio
async def test_get_stats_empty(fake_telemetry_service, fake_db):
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get("/telemetry/iot-microclimate-node-02/stats?interval=10h")
            assert r.status_code == 200
            assert r.json() == []


@pytest.mark.asyncio
async def test_get_stats_returns_buckets(monkeypatch, fake_db):
    # Повертаємо один bucket
    bucket = TelemetryStats(bucket="2026-02-27T12:00:00Z", avg_temperature=23.9, avg_humidity=62.9)

    async def fake_get_stats(device_id, interval, start, end, session):
        return [bucket]

    monkeypatch.setattr("app.services.telemetry_service_v2.TelemetryService.get_stats", fake_get_stats)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get("/telemetry/iot-microclimate-node-02/stats?interval=1h")
            assert r.status_code == 200

            data = [TelemetryStats(**item) for item in r.json()]
            assert isinstance(data, list)
            assert data[0].avg_temperature == 23.9
            assert data[0].avg_humidity == 62.9