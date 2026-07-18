"""
Routes for ingesting and reading sensor data.

  POST /api/v1/sensor-data          -> manually push a reading (e.g. from Postman, or a
                                        device that can't use MQTT)
  GET  /api/v1/sensor-data/latest   -> most recent reading(s), optionally filtered by device
  GET  /api/v1/sensor-data/devices  -> list of known device IDs with their last-seen reading

All GET endpoints here are authenticated. Farmers are automatically
restricted to devices registered to them; admins see everything.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from app.models.schemas import SensorReadingIn, SensorReadingOut
from app.config.settings import settings
from app.config.database import get_database
from app.config.logging_config import app_logger
from app.services.auth_deps import get_current_user, get_allowed_device_ids

router = APIRouter(prefix="/sensor-data", tags=["Sensor Data"])


def _serialize(doc) -> dict:
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc


@router.post("", response_model=SensorReadingOut, status_code=201)
async def create_sensor_reading(
    reading: SensorReadingIn, current_user: dict = Depends(get_current_user)
):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    # Farmers may only manually submit readings for devices they own.
    allowed = await get_allowed_device_ids(current_user, db)
    if allowed is not None and reading.device_id not in allowed:
        raise HTTPException(
            status_code=403, detail="You do not have permission to submit data for this device"
        )

    document = reading.model_dump()
    document["timestamp"] = reading.timestamp or datetime.now(timezone.utc)
    document["source"] = "rest-api"

    result = await db[settings.SENSOR_COLLECTION].insert_one(document)
    document["_id"] = result.inserted_id
    app_logger.info(f"Sensor reading stored via REST for device {reading.device_id}")
    return _serialize(document)


@router.get("/latest", response_model=list[SensorReadingOut])
async def get_latest_readings(
    limit: int = 10,
    device_id: Optional[str] = Query(default=None, description="Filter to a single device"),
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    allowed = await get_allowed_device_ids(current_user, db)

    if device_id:
        if allowed is not None and device_id not in allowed:
            raise HTTPException(status_code=403, detail="You do not have access to this device")
        query = {"device_id": device_id}
    else:
        query = {"device_id": {"$in": allowed}} if allowed is not None else {}

    cursor = db[settings.SENSOR_COLLECTION].find(query).sort("timestamp", -1).limit(limit)
    results = [_serialize(doc) async for doc in cursor]
    return results


@router.get("/devices")
async def list_devices(current_user: dict = Depends(get_current_user)):
    """
    Returns every device the current user is allowed to see, based on the
    `devices` registry (not just devices that happen to have sensor
    readings). This means a freshly-registered device shows up immediately
    with has_data=false, rather than being invisible until its first
    reading arrives.

    Farmers: only devices registered to them.
    Admins: every registered device, PLUS any device_id that is publishing
    sensor readings but was never formally registered (e.g. a simulator or
    test device an admin hasn't assigned to a farmer yet) — surfaced with
    label=None so admins can spot and register unclaimed devices.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    is_admin = current_user.get("role") == "admin"

    registered_query = {} if is_admin else {"owner_email": current_user["email"]}
    registered_devices = [d async for d in db[settings.DEVICE_COLLECTION].find(registered_query)]
    registered_ids = {d["device_id"] for d in registered_devices}

    devices = []
    for device in registered_devices:
        latest = await db[settings.SENSOR_COLLECTION].find_one(
            {"device_id": device["device_id"]}, sort=[("timestamp", -1)]
        )
        owner = None
        if is_admin:
            owner = await db[settings.USER_COLLECTION].find_one({"email": device["owner_email"]})

        devices.append(
            {
                "device_id": device["device_id"],
                "label": device.get("label"),
                "owner_email": device.get("owner_email"),
                "owner_name": owner.get("full_name") if owner else None,
                "location": device.get("location"),
                "has_data": latest is not None,
                "latest_reading": _serialize(latest) if latest else None,
            }
        )

    if is_admin:
        # Surface devices that are publishing readings but were never
        # registered/assigned, so nothing silently disappears from view.
        all_reading_device_ids = await db[settings.SENSOR_COLLECTION].distinct("device_id")
        orphan_ids = sorted(set(all_reading_device_ids) - registered_ids)
        for device_id in orphan_ids:
            latest = await db[settings.SENSOR_COLLECTION].find_one(
                {"device_id": device_id}, sort=[("timestamp", -1)]
            )
            devices.append(
                {
                    "device_id": device_id,
                    "label": None,
                    "owner_email": None,
                    "owner_name": None,
                    "location": None,
                    "has_data": True,
                    "latest_reading": _serialize(latest) if latest else None,
                }
            )

    devices.sort(key=lambda d: d["device_id"])
    return {"count": len(devices), "devices": devices}
