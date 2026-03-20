import asyncio
from app.db.database import engine
from app.models.telemetry_model import Base

async def run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(run())