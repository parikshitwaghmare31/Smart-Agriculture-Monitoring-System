"""
Routes for device registration and ownership management.

  POST   /api/v1/devices             -> (admin only) register a new sensor node and assign it to a farmer
  GET    /api/v1/devices              -> (admin only) list every registered device across all farmers
  GET    /api/v1/devices/my           -> (any authenticated user) list devices you own
  PATCH  /api/v1/devices/{device_id}  -> (admin only) edit a device's label, owner, or location
  DELETE /api/v1/devices/{device_id}  -> (admin only) unregister a device
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends

from app.models.auth_schemas import DeviceCreate, DeviceUpdate, DeviceOut
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
        "area_value": payload.area_value,
        "area_unit": payload.area_unit,
        "flow_rate_lph": payload.flow_rate_lph,
        "crop": payload.crop,
        "row_spacing_cm": payload.row_spacing_cm,
        "emitter_spacing_cm": payload.emitter_spacing_cm,
        "emitter_discharge_lph": payload.emitter_discharge_lph,
        "pipe_diameter_mm": payload.pipe_diameter_mm,
        "pump_hp": payload.pump_hp,
        "pump_rated_discharge_lph": payload.pump_rated_discharge_lph,
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


@router.patch("/{device_id}", response_model=DeviceOut)
async def update_device(
    device_id: str, payload: DeviceUpdate, admin: dict = Depends(require_admin)
):
    """
    Admin-only: edit a device's label, reassign it to a different farmer,
    or update its location. Only fields provided in the request body are
    changed — omitted fields keep their current value.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    existing = await db[settings.DEVICE_COLLECTION].find_one({"device_id": device_id})
    if not existing:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")

    updates = {}
    if payload.label is not None:
        updates["label"] = payload.label
    if payload.location is not None:
        updates["location"] = payload.location
    if payload.area_value is not None:
        updates["area_value"] = payload.area_value
    if payload.area_unit is not None:
        updates["area_unit"] = payload.area_unit
    if payload.flow_rate_lph is not None:
        updates["flow_rate_lph"] = payload.flow_rate_lph
    if payload.crop is not None:
        updates["crop"] = payload.crop
    if payload.row_spacing_cm is not None:
        updates["row_spacing_cm"] = payload.row_spacing_cm
    if payload.emitter_spacing_cm is not None:
        updates["emitter_spacing_cm"] = payload.emitter_spacing_cm
    if payload.emitter_discharge_lph is not None:
        updates["emitter_discharge_lph"] = payload.emitter_discharge_lph
    if payload.pipe_diameter_mm is not None:
        updates["pipe_diameter_mm"] = payload.pipe_diameter_mm
    if payload.pump_hp is not None:
        updates["pump_hp"] = payload.pump_hp
    if payload.pump_rated_discharge_lph is not None:
        updates["pump_rated_discharge_lph"] = payload.pump_rated_discharge_lph
    if payload.owner_email is not None:
        new_owner = await db[settings.USER_COLLECTION].find_one({"email": payload.owner_email})
        if not new_owner:
            raise HTTPException(
                status_code=404,
                detail=f"No registered user found with email {payload.owner_email}",
            )
        updates["owner_email"] = payload.owner_email

    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    await db[settings.DEVICE_COLLECTION].update_one({"device_id": device_id}, {"$set": updates})
    app_logger.info(f"Device '{device_id}' updated by admin {admin['email']}: {updates}")

    updated = await db[settings.DEVICE_COLLECTION].find_one({"device_id": device_id})
    owner = await db[settings.USER_COLLECTION].find_one({"email": updated["owner_email"]})
    return DeviceOut(**updated, owner_name=owner.get("full_name") if owner else None)


@router.delete("/{device_id}", status_code=204)
async def delete_device(device_id: str, admin: dict = Depends(require_admin)):
    """
    Admin-only: unregister a device. This only removes the ownership/registry
    record — any historical sensor readings already stored for this device_id
    are kept, so past data isn't lost. If a real device keeps publishing
    under this ID afterward, an admin will need to re-register it for a
    farmer to see it again.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    result = await db[settings.DEVICE_COLLECTION].delete_one({"device_id": device_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")

    app_logger.info(f"Device '{device_id}' unregistered by admin {admin['email']}")
