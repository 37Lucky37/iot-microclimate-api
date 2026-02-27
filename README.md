# verifly-ai

<!-- IoT Microclimate API README -->

# IoT Microclimate API

Lightweight FastAPI service for ingesting and aggregating microclimate telemetry from IoT nodes.

**Contents**
- Project: brief overview
- Requirements: dependencies and environment
- Installation: local and Docker
- Running: dev and production examples
- API: endpoints and examples
- Configuration: env vars
- Tests & utilities
- Contributing
- License

## Project
This service ingests telemetry (temperature, humidity, timestamp) from devices and provides aggregated statistics in time buckets. It uses Async SQLAlchemy, TimescaleDB/Postgres (optional), and FastAPI for the HTTP API.

## Requirements
- Python 3.10+
- Recommended: virtualenv or venv
- PostgreSQL / TimescaleDB for production (local SQLite may be used for quick tests if configured)

Install deps:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Running
### Docker (recommended)
Build and start the service:

```bash
docker compose up --build
```

This will create the service and (if configured) the database containers.

### Local (development)
Start the app with Uvicorn:

```bash
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment / Configuration
Copy `.env.example` (if present) to `.env` and set values. Important environment variables:

- `DATABASE_URL` - SQLAlchemy database URL (postgresql+asyncpg://...)
- `ENV` - environment name (development/production)
- Other app-specific settings in `app/core/config.py`.

The repository ignores `.env` by default in `.gitignore`.

## API
Base URL: `http://localhost:8000`

Endpoints:

- POST /telemetry/
	- Description: ingest a telemetry sample
	- Body (JSON):
		```json
		{
			"device_id": "iot-microclimate-node-02",
			"temperature": 23.9,
			"humidity": 62.9,
			"timestamp": "2026-02-27T12:34:56Z"  // optional, UTC
		}
		```
	- Response: 200 with the stored telemetry payload

- GET /telemetry/{device_id}/stats?interval=1h&start=...&end=...
	- Description: returns time-bucketed averages for the device
	- Query params:
		- `interval` (required): bucket interval, e.g. `1h`, `10m`, `48h`
		- `start` (optional): ISO datetime to override window start
		- `end` (optional): ISO datetime to override window end
	- Behavior: when `start` is not provided the service restricts the query to the recent window `now() - interval`. If no records exist in that window the endpoint returns HTTP 200 with an empty array `[]`.
	- Response example:
		```json
		[
			{"bucket": "2026-02-27T12:00:00Z", "avg_temperature": 23.9, "avg_humidity": 62.9}
		]
		```

## Testing
A small script `scripts/test_stats.py` shows how to call the service layer directly for ad-hoc checks. Prefer running API-level tests (not included) or using `curl` / `httpie`.

Example curl calls:

```bash
curl -X POST http://localhost:8000/telemetry/ -H 'Content-Type: application/json' -d '{"device_id":"iot-microclimate-node-02","temperature":24.1,"humidity":60.0}'

curl 'http://localhost:8000/telemetry/iot-microclimate-node-02/stats?interval=10h'
```

## Contributing
- Fork and create a feature branch
- Add tests for any behavior changes
- Run linters and formatters

## License
This project includes a `LICENSE` file. Check it for terms.

If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
