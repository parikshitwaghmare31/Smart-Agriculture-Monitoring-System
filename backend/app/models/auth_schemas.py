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


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DeviceCreate(BaseModel):
    device_id: str = Field(..., examples=["esp32-field-04"])
    label: str = Field(..., description="Friendly name, e.g. 'North Field Plot A'")
    owner_email: EmailStr = Field(..., description="Must belong to an already-registered farmer")
    location: Optional[str] = None


class DeviceOut(BaseModel):
    device_id: str
    label: str
    owner_email: EmailStr
    owner_name: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime
