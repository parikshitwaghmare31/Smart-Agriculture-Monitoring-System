"""
Pydantic schemas for authentication, users, and device ownership/registration.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=1)
    phone_number: Optional[str] = Field(
        default=None,
        description="Include country code, e.g. +919876543210 — required to receive SMS/WhatsApp irrigation alerts",
    )


class UserOut(BaseModel):
    email: EmailStr
    full_name: str
    role: Literal["admin", "farmer"]
    created_at: datetime
    phone_number: Optional[str] = None
    alerts_enabled: bool = False
    alert_channel: Literal["sms", "whatsapp", "both"] = "sms"
    preferred_language: Literal["en", "mr"] = "en"


class UserWithDeviceCount(UserOut):
    device_count: int = 0


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[Literal["admin", "farmer"]] = None
    new_password: Optional[str] = Field(
        default=None, min_length=8, description="Admin-triggered password reset for this user"
    )
    phone_number: Optional[str] = None
    alerts_enabled: Optional[bool] = None
    alert_channel: Optional[Literal["sms", "whatsapp", "both"]] = None
    preferred_language: Optional[Literal["en", "mr"]] = None


class MyProfileUpdate(BaseModel):
    """A restricted subset of UserUpdate — a farmer can change their own
    contact/alert/language preferences, but never their own role."""
    phone_number: Optional[str] = None
    alerts_enabled: Optional[bool] = None
    alert_channel: Optional[Literal["sms", "whatsapp", "both"]] = None
    preferred_language: Optional[Literal["en", "mr"]] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DeviceCreate(BaseModel):
    device_id: str = Field(..., examples=["esp32-field-04"])
    label: str = Field(..., description="Friendly name, e.g. 'North Field Plot A'")
    owner_email: EmailStr = Field(..., description="Must belong to an already-registered farmer")
    location: Optional[str] = None
    area_value: Optional[float] = Field(
        default=None, gt=0, description="Size of the field this sensor covers"
    )
    area_unit: Literal["acre", "hectare", "square_meter", "square_feet"] = "acre"
    flow_rate_lph: Optional[float] = Field(
        default=None, gt=0,
        description="Direct irrigation system flow rate in liters/hour, if known. "
                    "If you instead provide the detailed system parameters below "
                    "(row spacing, emitter spacing, emitter discharge, and pump info), "
                    "the effective flow rate is calculated automatically and this value is ignored.",
    )

    # Detailed irrigation system parameters — used to CALCULATE flow_rate_lph
    # automatically instead of guessing it, and to warn about pump/demand mismatches.
    crop: Optional[str] = Field(default=None, description="e.g. 'Ladyfinger (Okra)'")
    row_spacing_cm: Optional[float] = Field(
        default=None, gt=0, description="Distance between drip lateral lines / crop rows"
    )
    emitter_spacing_cm: Optional[float] = Field(
        default=None, gt=0, description="Distance between emitters along a drip lateral"
    )
    emitter_discharge_lph: Optional[float] = Field(
        default=None, gt=0, description="Each emitter's rated discharge, e.g. 4 for a 4 LPH dripper"
    )
    pipe_diameter_mm: Optional[float] = Field(
        default=None, gt=0, description="Drip lateral pipe diameter (for reference; doesn't affect the calculation)"
    )
    pump_hp: Optional[float] = Field(
        default=None, gt=0, description="Pump horsepower, used to ESTIMATE discharge if pump_rated_discharge_lph isn't known"
    )
    pump_rated_discharge_lph: Optional[float] = Field(
        default=None, gt=0,
        description="Pump's actual rated discharge from its nameplate/catalog, if known — "
                    "much more accurate than estimating from horsepower alone",
    )


class DeviceUpdate(BaseModel):
    """All fields optional — only the ones provided get updated (partial update)."""
    label: Optional[str] = None
    owner_email: Optional[EmailStr] = Field(
        default=None, description="Reassign this device to a different registered farmer"
    )
    location: Optional[str] = None
    area_value: Optional[float] = Field(default=None, gt=0)
    area_unit: Optional[Literal["acre", "hectare", "square_meter", "square_feet"]] = None
    flow_rate_lph: Optional[float] = Field(default=None, gt=0)
    crop: Optional[str] = None
    row_spacing_cm: Optional[float] = Field(default=None, gt=0)
    emitter_spacing_cm: Optional[float] = Field(default=None, gt=0)
    emitter_discharge_lph: Optional[float] = Field(default=None, gt=0)
    pipe_diameter_mm: Optional[float] = Field(default=None, gt=0)
    pump_hp: Optional[float] = Field(default=None, gt=0)
    pump_rated_discharge_lph: Optional[float] = Field(default=None, gt=0)


class DeviceOut(BaseModel):
    device_id: str
    label: str
    owner_email: EmailStr
    owner_name: Optional[str] = None
    location: Optional[str] = None
    area_value: Optional[float] = None
    area_unit: Optional[str] = None
    flow_rate_lph: Optional[float] = None
    crop: Optional[str] = None
    row_spacing_cm: Optional[float] = None
    emitter_spacing_cm: Optional[float] = None
    emitter_discharge_lph: Optional[float] = None
    pipe_diameter_mm: Optional[float] = None
    pump_hp: Optional[float] = None
    pump_rated_discharge_lph: Optional[float] = None
    created_at: datetime
