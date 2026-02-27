# app/main.py
from fastapi import FastAPI
import logging
from contextlib import asynccontextmanager
from app.api.routes.telemetry import router as telemetry_router
from app.db.database import engine
from app.models.telemetry_model import Base
from app.db.init_db import init_db

# Налаштовуємо логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler замість deprecated @app.on_event("startup")
    Тут можна запускати init_db або інші startup/shutdown задачі
    """
    logging.info("Starting up application...")
    await init_db(engine)  # Ініціалізація БД
    yield
    logging.info("Shutting down application...")
    # Тут можна додати shutdown logic, якщо потрібно
    # наприклад, закриття підключень до БД або кешу

# Створюємо FastAPI app із lifespan
app = FastAPI(title="IoT Microclimate API", lifespan=lifespan)

# Підключаємо роутери
app.include_router(telemetry_router)