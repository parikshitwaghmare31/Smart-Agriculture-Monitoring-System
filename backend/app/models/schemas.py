"""
Pydantic request/response schemas shared across routes.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SensorReadingIn(BaseModel):
    device_id: str = Field(..., examples=["esp32-field-01"])
    soil_moisture: float = Field(..., ge=0, le=100, description="Percentage")
    temperature: float = Field(..., ge=-10, le=60, description="Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Percentage")
    timestamp: Optional[datetime] = None


class SensorReadingOut(SensorReadingIn):
    id: str
    timestamp: datetime


class PredictionRequest(BaseModel):
    soil_moisture: float = Field(..., ge=0, le=100)
    temperature: float = Field(..., ge=-10, le=60)
    humidity: float = Field(..., ge=0, le=100)
    device_id: Optional[str] = "manual-request"


class FieldAreaInfo(BaseModel):
    area_value: float
    area_unit: str
    area_square_meters: float
    total_liters_needed: float
    recommended_duration_hours: Optional[float] = None
    num_emitters: Optional[int] = None
    system_demand_lph: Optional[float] = None
    pump_supply_lph: Optional[float] = None
    pump_supply_is_estimated: Optional[bool] = None
    zones_needed: Optional[int] = None


class PredictionResponse(BaseModel):
    irrigate: bool
    confidence: float
    water_amount_liters: float = Field(
        description="Irrigation depth in liters per square meter (equivalently, mm of water depth) — "
        "a per-unit-area figure, not the total for any specific field size"
    )
    field_area: Optional[FieldAreaInfo] = Field(
        default=None,
        description="Present only if the request's device_id has a registered field area, "
        "scaling the recommendation to a real total volume and (if flow rate is known) run-time",
    )
    reasoning: str
    timestamp: datetime


class HistoryQuery(BaseModel):
    device_id: Optional[str] = None
    limit: int = 100


class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    status: str
    mongo_connected: bool
    model_loaded: bool
    mqtt_connected: bool
