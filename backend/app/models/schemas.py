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


class PredictionResponse(BaseModel):
    irrigate: bool
    confidence: float
    water_amount_liters: float
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
