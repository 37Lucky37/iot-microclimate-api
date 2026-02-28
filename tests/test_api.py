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


@pytest.fixture(autouse=True)
def set_keys(monkeypatch):
    # ensure predictable API key values during tests
    from app.core import config
    monkeypatch.setattr(config.settings, "IOT_API_KEY", "test-iot-key")
    monkeypatch.setattr(config.settings, "GRAFANA_API_KEY", "test-grafana-key")
    yield


@pytest.fixture
def fake_telemetry_service(monkeypatch):
    async def fake_process(data, session):
        if isinstance(data, Telemetry):
            return data
        return Telemetry(**data)

    async def fake_get_stats(device_id, interval, start, end, session):
        return []

    async def fake_get_by_device(device_id, start, end, limit, session):
        return []

    monkeypatch.setattr(
        "app.services.telemetry_service_v2.TelemetryService.get_by_device",
        fake_get_by_device,
    )
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



@pytest.mark.asyncio
async def test_get_stats_empty(fake_telemetry_service, fake_db):
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # missing header => 401
            r = await ac.get("/telemetry/iot-microclimate-node-02/stats?interval=10h")
            assert r.status_code == 401

            # wrong header => 403
            r = await ac.get(
                "/telemetry/iot-microclimate-node-02/stats?interval=10h",
                headers={"X-API-Key": "bad"},
            )
            assert r.status_code == 403

            # good header
            r = await ac.get(
                "/telemetry/iot-microclimate-node-02/stats?interval=10h",
                headers={"X-API-Key": "test-grafana-key"},
            )
            assert r.status_code == 200
            assert r.json() == []


@pytest.mark.asyncio
async def test_get_telemetry_empty(fake_telemetry_service, fake_db):
    # ensure GET /telemetry/{device_id} also enforces the Grafana key
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get("/telemetry/iot-microclimate-node-02")
            assert r.status_code == 401

            r = await ac.get(
                "/telemetry/iot-microclimate-node-02",
                headers={"X-API-Key": "wrong"},
            )
            assert r.status_code == 403

            r = await ac.get(
                "/telemetry/iot-microclimate-node-02",
                headers={"X-API-Key": "test-grafana-key"},
            )
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
            # ensure authorization is required on stats endpoint too
            r = await ac.get("/telemetry/iot-microclimate-node-02/stats?interval=1h")
            assert r.status_code == 401

            # provide header
            r = await ac.get(
                "/telemetry/iot-microclimate-node-02/stats?interval=1h",
                headers={"X-API-Key": "test-grafana-key"},
            )
            assert r.status_code == 200

            data = [TelemetryStats(**item) for item in r.json()]
            assert isinstance(data, list)
            assert data[0].avg_temperature == 23.9
            assert data[0].avg_humidity == 62.9