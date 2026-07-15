"""
Route for historical data used to power dashboard charts.

  GET /api/v1/history/sensors      -> historical sensor readings
  GET /api/v1/history/predictions  -> historical predictions
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.config.settings import settings
from app.config.database import get_database

router = APIRouter(prefix="/history", tags=["History"])


def _serialize(doc) -> dict:
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc


@router.get("/sensors")
async def get_sensor_history(
    device_id: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    query = {"device_id": device_id} if device_id else {}
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
):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    query = {"device_id": device_id} if device_id else {}
    cursor = (
        db[settings.PREDICTION_COLLECTION]
        .find(query)
        .sort("timestamp", -1)
        .limit(limit)
    )
    results = [_serialize(doc) async for doc in cursor]
    results.reverse()
    return {"count": len(results), "data": results}
