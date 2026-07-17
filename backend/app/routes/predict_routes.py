"""
Route for irrigation prediction.

  POST /api/v1/predict -> given soil_moisture, temperature, humidity,
                           returns whether to irrigate and how much water to use.
                           Also persists the prediction for later review.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends

from app.models.schemas import PredictionRequest, PredictionResponse
from app.services.ml_service import ml_service
from app.config.settings import settings
from app.config.database import get_database
from app.config.logging_config import app_logger
from app.services.auth_deps import get_current_user

router = APIRouter(prefix="/predict", tags=["Prediction"])


@router.post("", response_model=PredictionResponse)
async def predict_irrigation(
    payload: PredictionRequest, current_user: dict = Depends(get_current_user)
):
    try:
        irrigate, confidence, water_amount, reasoning = ml_service.predict(
            payload.soil_moisture, payload.temperature, payload.humidity
        )
    except Exception as e:
        app_logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed") from e

    response = PredictionResponse(
        irrigate=irrigate,
        confidence=confidence,
        water_amount_liters=water_amount,
        reasoning=reasoning,
        timestamp=datetime.now(timezone.utc),
    )

    db = get_database()
    if db is not None:
        record = response.model_dump()
        record["device_id"] = payload.device_id
        record["input"] = {
            "soil_moisture": payload.soil_moisture,
            "temperature": payload.temperature,
            "humidity": payload.humidity,
        }
        await db[settings.PREDICTION_COLLECTION].insert_one(record)

    return response
