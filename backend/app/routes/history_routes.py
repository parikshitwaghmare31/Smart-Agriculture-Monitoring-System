"""
Route for historical data used to power dashboard charts.

  GET /api/v1/history/sensors      -> historical sensor readings
  GET /api/v1/history/predictions  -> historical predictions

Both endpoints are authenticated. Farmers are automatically restricted to
their own registered devices; admins see everything.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from app.config.settings import settings
from app.config.database import get_database
from app.services.auth_deps import get_current_user, get_allowed_device_ids

router = APIRouter(prefix="/history", tags=["History"])


def _serialize(doc) -> dict:
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc


async def _build_query(device_id: Optional[str], current_user: dict, db) -> dict:
    allowed = await get_allowed_device_ids(current_user, db)

    if device_id:
        if allowed is not None and device_id not in allowed:
            raise HTTPException(status_code=403, detail="You do not have access to this device")
        return {"device_id": device_id}

    if allowed is not None:
        return {"device_id": {"$in": allowed}}

    return {}


@router.get("/sensors")
async def get_sensor_history(
    device_id: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    query = await _build_query(device_id, current_user, db)
    cursor = (
        db[settings.SENSOR_COLLECTION]
        .find(query)
        .sort("timestamp", -1)
        .limit(limit)
    )
    results = [_serialize(doc) async for doc in cursor]
    results.reverse()  # chronological order for charting
    return {"count": len(results), "data": results}


@router.get("/predictions")
async def get_prediction_history(
    device_id: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    query = await _build_query(device_id, current_user, db)
    cursor = (
        db[settings.PREDICTION_COLLECTION]
        .find(query)
        .sort("timestamp", -1)
        .limit(limit)
    )
    results = [_serialize(doc) async for doc in cursor]
    results.reverse()
    return {"count": len(results), "data": results}
