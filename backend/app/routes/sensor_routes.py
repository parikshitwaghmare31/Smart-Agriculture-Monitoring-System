"""
Routes for ingesting and reading sensor data.

  POST /api/v1/sensor-data          -> manually push a reading (e.g. from Postman, or a
                                        device that can't use MQTT)
  GET  /api/v1/sensor-data/latest   -> most recent reading(s), optionally filtered by device
  GET  /api/v1/sensor-data/devices  -> list of known device IDs with their last-seen reading
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId

from app.models.schemas import SensorReadingIn, SensorReadingOut
from app.config.settings import settings
from app.config.database import get_database
from app.config.logging_config import app_logger

router = APIRouter(prefix="/sensor-data", tags=["Sensor Data"])


def _serialize(doc) -> dict:
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc


@router.post("", response_model=SensorReadingOut, status_code=201)
async def create_sensor_reading(reading: SensorReadingIn):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

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
):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    query = {"device_id": device_id} if device_id else {}
    cursor = db[settings.SENSOR_COLLECTION].find(query).sort("timestamp", -1).limit(limit)
    results = [_serialize(doc) async for doc in cursor]
    return results


@router.get("/devices")
async def list_devices():
    """
    Returns every distinct device_id seen in sensor_readings, each with its
    most recent reading, so the frontend can populate a device selector
    dropdown without having to fetch full history for every device up front.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    device_ids = await db[settings.SENSOR_COLLECTION].distinct("device_id")

    devices = []
    for device_id in sorted(device_ids):
        latest = await db[settings.SENSOR_COLLECTION].find_one(
            {"device_id": device_id}, sort=[("timestamp", -1)]
        )
        if latest:
            devices.append(_serialize(latest))

    return {"count": len(devices), "devices": devices}
