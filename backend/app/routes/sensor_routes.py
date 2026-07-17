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
    Returns every distinct device_id seen in sensor_readings that the current
    user is allowed to see (all of them for admins, only owned ones for
    farmers), each with its most recent reading.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    allowed = await get_allowed_device_ids(current_user, db)

    query = {"device_id": {"$in": allowed}} if allowed is not None else {}
    device_ids = await db[settings.SENSOR_COLLECTION].distinct("device_id", query)

    devices = []
    for device_id in sorted(device_ids):
        latest = await db[settings.SENSOR_COLLECTION].find_one(
            {"device_id": device_id}, sort=[("timestamp", -1)]
        )
        if latest:
            devices.append(_serialize(latest))

    return {"count": len(devices), "devices": devices}
