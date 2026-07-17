"""
Routes for device registration and ownership management.

  POST /api/v1/devices     -> (admin only) register a new sensor node and assign it to a farmer
  GET  /api/v1/devices      -> (admin only) list every registered device across all farmers
  GET  /api/v1/devices/my   -> (any authenticated user) list devices you own
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends

from app.models.auth_schemas import DeviceCreate, DeviceOut
from app.services.auth_deps import get_current_user, require_admin
from app.config.settings import settings
from app.config.database import get_database
from app.config.logging_config import app_logger

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("", response_model=DeviceOut, status_code=201)
async def register_device(payload: DeviceCreate, admin: dict = Depends(require_admin)):
    """
    Admin-only: register a new sensor node (e.g. a physical ESP32 unit) and
    assign it to a farmer by email. The farmer must already have an account
    (they self-register first via /auth/register).
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    owner = await db[settings.USER_COLLECTION].find_one({"email": payload.owner_email})
    if not owner:
        raise HTTPException(
            status_code=404,
            detail=f"No registered user found with email {payload.owner_email}. "
            "The farmer must create an account before a device can be assigned to them.",
        )

    existing_device = await db[settings.DEVICE_COLLECTION].find_one({"device_id": payload.device_id})
    if existing_device:
        raise HTTPException(status_code=409, detail=f"Device '{payload.device_id}' is already registered")

    device_doc = {
        "device_id": payload.device_id,
        "label": payload.label,
        "owner_email": payload.owner_email,
        "location": payload.location,
        "created_at": datetime.now(timezone.utc),
        "created_by": admin["email"],
    }
    await db[settings.DEVICE_COLLECTION].insert_one(device_doc)
    app_logger.info(
        f"Device '{payload.device_id}' registered by admin {admin['email']} for farmer {payload.owner_email}"
    )

    return DeviceOut(**device_doc, owner_name=owner.get("full_name"))


@router.get("", response_model=list[DeviceOut])
async def list_all_devices(admin: dict = Depends(require_admin)):
    """Admin-only: view every registered device across all farmers."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    devices = []
    async for device in db[settings.DEVICE_COLLECTION].find():
        owner = await db[settings.USER_COLLECTION].find_one({"email": device["owner_email"]})
        devices.append(DeviceOut(**device, owner_name=owner.get("full_name") if owner else None))

    return devices


@router.get("/my", response_model=list[DeviceOut])
async def list_my_devices(current_user: dict = Depends(get_current_user)):
    """Any authenticated user: list devices registered to them."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    devices = []
    async for device in db[settings.DEVICE_COLLECTION].find({"owner_email": current_user["email"]}):
        devices.append(DeviceOut(**device, owner_name=current_user.get("full_name")))

    return devices
