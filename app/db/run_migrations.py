import asyncio
from app.db.database import engine
from app.db.init_db import init_db

async def run():
    # One-shot DB initialization:
    # - ensure TimescaleDB extension exists
    # - create tables
    # - convert table into hypertable (idempotent)
    await init_db(engine)

if __name__ == "__main__":
    asyncio.run(run())