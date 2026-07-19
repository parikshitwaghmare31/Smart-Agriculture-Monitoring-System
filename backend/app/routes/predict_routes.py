"""
Route for irrigation prediction.

  POST /api/v1/predict -> given soil_moisture, temperature, humidity,
                           returns whether to irrigate and how much water to use
                           (as a per-square-meter depth, scaled to the requesting
                           device's registered field size if one is set).
                           Also persists the prediction for later review.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends

from app.models.schemas import PredictionRequest, PredictionResponse, FieldAreaInfo
from app.services.ml_service import ml_service
from app.services.irrigation_area_utils import compute_total_water_needed, compute_irrigation_system_flow_rate
from app.config.settings import settings
from app.config.database import get_database
from app.config.logging_config import app_logger
from app.services.auth_deps import get_current_user

router = APIRouter(prefix="/predict", tags=["Prediction"])

# Placeholder device_ids used by the dashboard's manual prediction form when
# no specific real device is selected — these never have a registered area.
_NON_DEVICE_IDS = {"manual-request", "dashboard-manual"}


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

    field_area = None
    db = get_database()

    if irrigate and db is not None and payload.device_id not in _NON_DEVICE_IDS:
        device = await db[settings.DEVICE_COLLECTION].find_one({"device_id": payload.device_id})
        if device and device.get("area_value"):
            try:
                # Prefer a flow rate CALCULATED from real system parameters
                # (row/emitter spacing, emitter discharge, pump rating) over
                # a directly-entered guess, since it also surfaces whether
                # the pump can cover the whole field at once or needs zoning.
                system_info = {}
                has_detailed_params = all([
                    device.get("row_spacing_cm"),
                    device.get("emitter_spacing_cm"),
                    device.get("emitter_discharge_lph"),
                    device.get("pump_hp") or device.get("pump_rated_discharge_lph"),
                ])

                if has_detailed_params:
                    system_info = compute_irrigation_system_flow_rate(
                        area_value=device["area_value"],
                        area_unit=device.get("area_unit", "acre"),
                        row_spacing_cm=device["row_spacing_cm"],
                        emitter_spacing_cm=device["emitter_spacing_cm"],
                        emitter_discharge_lph=device["emitter_discharge_lph"],
                        pump_rated_discharge_lph=device.get("pump_rated_discharge_lph"),
                        pump_hp=device.get("pump_hp"),
                    )
                    effective_flow_rate = system_info["effective_flow_rate_lph"]
                else:
                    effective_flow_rate = device.get("flow_rate_lph")

                area_info = compute_total_water_needed(
                    water_depth_liters_per_sqm=water_amount,
                    area_value=device["area_value"],
                    area_unit=device.get("area_unit", "acre"),
                    flow_rate_lph=effective_flow_rate,
                )
                area_info.update({
                    "num_emitters": system_info.get("num_emitters"),
                    "system_demand_lph": system_info.get("system_demand_lph"),
                    "pump_supply_lph": system_info.get("pump_supply_lph"),
                    "pump_supply_is_estimated": system_info.get("pump_supply_is_estimated"),
                    "zones_needed": system_info.get("zones_needed"),
                })
                field_area = FieldAreaInfo(**area_info)
            except ValueError as e:
                app_logger.warning(f"Could not compute field area for {payload.device_id}: {e}")

    response = PredictionResponse(
        irrigate=irrigate,
        confidence=confidence,
        water_amount_liters=water_amount,
        field_area=field_area,
        reasoning=reasoning,
        timestamp=datetime.now(timezone.utc),
    )

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
