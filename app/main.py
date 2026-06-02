from fastapi import FastAPI, HTTPException
import logging
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.api.routes.telemetry import router as telemetry_router
from app.db.database import engine
from app.db.init_db import init_db
from app.core.config import settings

# Налаштовуємо логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting up application...")
    if settings.RUN_DB_INIT:
        logging.info("RUN_DB_INIT is enabled, initializing database schema...")
        await init_db(engine)
    else:
        logging.info("RUN_DB_INIT is disabled, skipping database initialization")
    yield
    logging.info("Shutting down application...")


app = FastAPI(title="IoT Microclimate API", lifespan=lifespan)

@app.get("/health")
async def health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        logging.exception("Health check failed")
        raise HTTPException(status_code=503, detail="Service unhealthy")


# Підключаємо роутери
app.include_router(telemetry_router)