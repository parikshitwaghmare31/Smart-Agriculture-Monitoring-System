"""
FastAPI application entrypoint.

Wires together:
  - MongoDB connection lifecycle
  - MQTT background client lifecycle
  - ML model loading
  - Admin account bootstrap
  - Route registration
  - CORS
"""

import asyncio
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.config.logging_config import app_logger
from app.config.database import connect_to_mongo, close_mongo_connection, get_database
from app.services.ml_service import ml_service
from app.services.mqtt_service import init_mqtt_service, mqtt_service_instance
from app.services.auth_service import hash_password

from app.routes import (
    sensor_routes,
    predict_routes,
    history_routes,
    health_routes,
    auth_routes,
    device_routes,
    user_routes,
)


async def bootstrap_admin_account():
    """
    On startup, if ADMIN_BOOTSTRAP_EMAIL/PASSWORD are set and no admin user
    exists yet, create one. This lets you log in as an administrator
    immediately after deployment without touching the database by hand.
    """
    if not settings.ADMIN_BOOTSTRAP_EMAIL or not settings.ADMIN_BOOTSTRAP_PASSWORD:
        app_logger.info(
            "ADMIN_BOOTSTRAP_EMAIL/PASSWORD not set — skipping admin bootstrap. "
            "Set these env vars if you need an initial admin account created automatically."
        )
        return

    db = get_database()
    existing_admin = await db[settings.USER_COLLECTION].find_one({"role": "admin"})
    if existing_admin:
        app_logger.info("Admin account already exists, skipping bootstrap")
        return

    admin_doc = {
        "email": settings.ADMIN_BOOTSTRAP_EMAIL,
        "full_name": settings.ADMIN_BOOTSTRAP_NAME,
        "hashed_password": hash_password(settings.ADMIN_BOOTSTRAP_PASSWORD),
        "role": "admin",
        "created_at": datetime.now(timezone.utc),
    }
    await db[settings.USER_COLLECTION].insert_one(admin_doc)
    app_logger.info(f"Bootstrapped initial admin account: {settings.ADMIN_BOOTSTRAP_EMAIL}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info(f"Starting {settings.APP_NAME} ({settings.APP_ENV})")

    await connect_to_mongo()
    await bootstrap_admin_account()
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
app.include_router(auth_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(device_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(user_routes.router, prefix=settings.API_V1_PREFIX)
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
