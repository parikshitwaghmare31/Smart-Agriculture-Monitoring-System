"""
Pydantic schemas for the disease/crop recommendation rules engine.

Admins maintain a table of (crop, disease_label) -> advice. This is the
"default" recommendation source. Later, once a real image classifier is
trained on real data, its predictions can be looked up against this same
table — so the rules engine and the ML model share one recommendation
source of truth rather than needing two separate systems.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DiseaseClassCreate(BaseModel):
    crop: str = Field(..., examples=["Tomato"])
    disease_label: str = Field(..., examples=["Early Blight", "Healthy"])
    irrigation_advice: str = Field(..., min_length=1)
    fertilizer_advice: str = Field(..., min_length=1)
    spraying_advice: str = Field(..., min_length=1)


class DiseaseClassUpdate(BaseModel):
    irrigation_advice: Optional[str] = None
    fertilizer_advice: Optional[str] = None
    spraying_advice: Optional[str] = None


class DiseaseClassOut(BaseModel):
    id: str
    crop: str
    disease_label: str
    irrigation_advice: str
    fertilizer_advice: str
    spraying_advice: str
    updated_by: Optional[str] = None
    updated_at: datetime


class DiseasePredictionResponse(BaseModel):
    crop: str
    disease_label: str
    confidence: float
    irrigation_advice: Optional[str] = None
    fertilizer_advice: Optional[str] = None
    spraying_advice: Optional[str] = None
    recommendation_found: bool
    timestamp: datetime


class TrainingStatusOut(BaseModel):
    status: str  # "idle" | "running" | "completed" | "failed"
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metrics: Optional[dict] = None
