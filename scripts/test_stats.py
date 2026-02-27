import asyncio
from app.db.database import AsyncSessionLocal
from app.services.telemetry_service_v2 import TelemetryService

async def main():
    async with AsyncSessionLocal() as s:
        try:
            stats = await TelemetryService.get_stats('iot-microclimate-node-02', '48h', None, None, s)
            print('stats', stats)
        except Exception as e:
            print('exception', e)

if __name__ == '__main__':
    asyncio.run(main())
