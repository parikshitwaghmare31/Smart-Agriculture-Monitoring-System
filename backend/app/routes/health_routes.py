"""Simple health check endpoint used by Docker healthchecks / load balancers."""

from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.config.database import get_database
from app.services.ml_service import ml_service
from app.services.mqtt_service import is_mqtt_connected

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    db = get_database()
    mongo_connected = False
    if db is not None:
        try:
            await db.client.admin.command("ping")
            mongo_connected = True
        except Exception:
            mongo_connected = False

    return HealthResponse(
        status="ok",
        mongo_connected=mongo_connected,
        model_loaded=ml_service.loaded,
        mqtt_connected=is_mqtt_connected(),
    )
