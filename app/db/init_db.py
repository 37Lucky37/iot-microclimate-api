# app/db/init_db.py
from sqlalchemy import text
from app.models.telemetry_model import Base

async def init_db(engine):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("""
            SELECT create_hypertable(
                'telemetry',
                'timestamp',
                if_not_exists => TRUE
            );
        """))