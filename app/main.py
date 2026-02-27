from fastapi import FastAPI
import logging
from app.api.routes.telemetry import router as telemetry_router
from sqlalchemy import text
from app.db.database import engine
from app.models.telemetry_model import Base
from app.db.init_db import init_db

app = FastAPI(title="IoT Microclimate API")

app.include_router(telemetry_router)

@app.on_event("startup")
async def startup():
    await init_db(engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


