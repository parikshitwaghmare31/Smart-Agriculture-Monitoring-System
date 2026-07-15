"""
FastAPI application entrypoint.

Wires together:
  - MongoDB connection lifecycle
  - MQTT background client lifecycle
  - ML model loading
  - Route registration
  - CORS
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.config.logging_config import app_logger
from app.config.database import connect_to_mongo, close_mongo_connection
from app.services.ml_service import ml_service
from app.services.mqtt_service import init_mqtt_service, mqtt_service_instance

from app.routes import sensor_routes, predict_routes, history_routes, health_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info(f"Starting {settings.APP_NAME} ({settings.APP_ENV})")

    await connect_to_mongo()
    ml_service.load()

    loop = asyncio.get_event_loop()
    init_mqtt_service(loop)

    yield

    if mqtt_service_instance:
        mqtt_service_instance.stop()
    await close_mongo_connection()
    app_logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Production-ready AI-based Smart Agriculture Monitoring System API",
    lifespan=lifespan,
)

origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(sensor_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(predict_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(history_routes.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "docs": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
    }
