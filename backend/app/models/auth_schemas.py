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


class UserOut(BaseModel):
    email: EmailStr
    full_name: str
    role: Literal["admin", "farmer"]
    created_at: datetime


class UserWithDeviceCount(UserOut):
    device_count: int = 0


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[Literal["admin", "farmer"]] = None
    new_password: Optional[str] = Field(
        default=None, min_length=8, description="Admin-triggered password reset for this user"
    )


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
        description="Your irrigation system's total flow rate in liters/hour (drip/sprinkler/etc), "
                    "used to convert a water recommendation into a run-time duration",
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


class DeviceOut(BaseModel):
    device_id: str
    label: str
    owner_email: EmailStr
    owner_name: Optional[str] = None
    location: Optional[str] = None
    area_value: Optional[float] = None
    area_unit: Optional[str] = None
    flow_rate_lph: Optional[float] = None
    created_at: datetime
