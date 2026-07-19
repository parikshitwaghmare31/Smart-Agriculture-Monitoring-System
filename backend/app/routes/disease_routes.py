"""
Routes for the disease classifier and the crop/disease recommendation rules table.

  GET    /api/v1/disease/crops           -> distinct crop names (any authenticated user, for the dropdown)
  GET    /api/v1/disease/classes         -> (admin only) full recommendation rules table
  POST   /api/v1/disease/classes         -> (admin only) add a new crop+disease recommendation entry
  PATCH  /api/v1/disease/classes/{id}    -> (admin only) edit advice text for an entry
  DELETE /api/v1/disease/classes/{id}    -> (admin only) remove an entry

  GET    /api/v1/disease/status          -> (any authenticated user) is a model deployed? which classes?
  POST   /api/v1/disease/classify        -> (any authenticated user) upload a photo, get a prediction + recommendation
  POST   /api/v1/disease/deploy-model    -> (admin only) upload a newly offline-trained model to hot-swap into production
"""

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File

from app.models.disease_schemas import (
    DiseaseClassCreate,
    DiseaseClassUpdate,
    DiseaseClassOut,
    DiseasePredictionResponse,
)
from app.services.auth_deps import get_current_user, require_admin
from app.services.disease_service import disease_service
from app.config.settings import settings
from app.config.database import get_database
from app.config.logging_config import app_logger

router = APIRouter(prefix="/disease", tags=["Disease Recommendations"])


def _serialize(doc) -> dict:
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc


@router.get("/crops")
async def list_crops(current_user: dict = Depends(get_current_user)):
    """Any authenticated user: distinct crop names configured so far, for the farmer-facing dropdown."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    crops = await db[settings.DISEASE_CLASS_COLLECTION].distinct("crop")
    return {"crops": sorted(crops)}


@router.get("/status")
async def get_model_status(current_user: dict = Depends(get_current_user)):
    """
    Any authenticated user: whether a disease classifier model is currently
    deployed, and which crop/disease classes it can recognize. The frontend
    uses this to show/hide the photo-upload feature and its dropdown options.
    """
    return {
        "model_loaded": disease_service.loaded,
        "num_classes": len(disease_service.class_metadata),
        "classes": disease_service.class_metadata,
        "training_report": disease_service.training_report,
    }


@router.post("/classify", response_model=DiseasePredictionResponse)
async def classify_plant_photo(
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Any authenticated user: upload a photo of a crop/vegetable/fruit and get
    back the predicted disease (or "Healthy") plus whatever irrigation/
    fertilizer/spraying recommendation an admin has configured for it, if any.
    """
    if not disease_service.loaded:
        raise HTTPException(
            status_code=503,
            detail="No disease classifier model has been deployed yet. "
            "An admin needs to train one offline and upload it via the Admin Panel.",
        )

    image_bytes = await image.read()
    try:
        crop, disease_label, confidence = disease_service.predict(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        app_logger.error(f"Disease classification failed: {e}")
        raise HTTPException(status_code=500, detail="Classification failed") from e

    db = get_database()
    recommendation = None
    if db is not None:
        recommendation = await db[settings.DISEASE_CLASS_COLLECTION].find_one(
            {"crop": crop, "disease_label": disease_label}
        )

    response = DiseasePredictionResponse(
        crop=crop,
        disease_label=disease_label,
        confidence=round(confidence, 4),
        irrigation_advice=recommendation.get("irrigation_advice") if recommendation else None,
        fertilizer_advice=recommendation.get("fertilizer_advice") if recommendation else None,
        spraying_advice=recommendation.get("spraying_advice") if recommendation else None,
        recommendation_found=recommendation is not None,
        timestamp=datetime.now(timezone.utc),
    )

    if db is not None:
        await db["disease_predictions_log"].insert_one(
            {**response.model_dump(), "user_email": current_user["email"]}
        )

    return response


@router.post("/deploy-model")
async def deploy_model(
    onnx_model_file: UploadFile = File(..., description="model.onnx from train_classifier.py"),
    class_names_file: UploadFile = File(..., description="class_names.json from train_classifier.py"),
    training_report_file: UploadFile = File(
        default=None, description="Optional training_report.json for reference"
    ),
    admin: dict = Depends(require_admin),
):
    """
    Admin-only: upload a model trained offline via
    ml/disease_classifier/scripts/train_classifier.py to hot-swap it into
    production immediately, without a redeploy.
    """
    import os

    os.makedirs(settings.DISEASE_MODEL_DIR, exist_ok=True)

    model_bytes = await onnx_model_file.read()
    with open(os.path.join(settings.DISEASE_MODEL_DIR, "model.onnx"), "wb") as f:
        f.write(model_bytes)

    class_names_bytes = await class_names_file.read()
    with open(os.path.join(settings.DISEASE_MODEL_DIR, "class_names.json"), "wb") as f:
        f.write(class_names_bytes)

    if training_report_file is not None:
        report_bytes = await training_report_file.read()
        with open(os.path.join(settings.DISEASE_MODEL_DIR, "training_report.json"), "wb") as f:
            f.write(report_bytes)

    disease_service.reload()

    if not disease_service.loaded:
        raise HTTPException(
            status_code=400,
            detail="Files were saved but the model failed to load. Check that model.onnx and "
            "class_names.json are valid and were generated together by the same training run.",
        )

    app_logger.info(
        f"Disease classifier model deployed by admin {admin['email']}: "
        f"{len(disease_service.class_metadata)} classes"
    )

    return {
        "status": "deployed",
        "num_classes": len(disease_service.class_metadata),
        "classes": disease_service.class_metadata,
    }


@router.get("/classes", response_model=list[DiseaseClassOut])
async def list_disease_classes(admin: dict = Depends(require_admin)):
    """Admin-only: view the full recommendation rules table."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    docs = [_serialize(d) async for d in db[settings.DISEASE_CLASS_COLLECTION].find()]
    return docs


@router.post("/classes", response_model=DiseaseClassOut, status_code=201)
async def create_disease_class(payload: DiseaseClassCreate, admin: dict = Depends(require_admin)):
    """Admin-only: add a new (crop, disease) recommendation entry."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    existing = await db[settings.DISEASE_CLASS_COLLECTION].find_one(
        {"crop": payload.crop, "disease_label": payload.disease_label}
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A recommendation entry for {payload.crop} / {payload.disease_label} already exists.",
        )

    doc = payload.model_dump()
    doc["updated_by"] = admin["email"]
    doc["updated_at"] = datetime.now(timezone.utc)
    result = await db[settings.DISEASE_CLASS_COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id

    app_logger.info(f"Disease class '{payload.crop}/{payload.disease_label}' created by {admin['email']}")
    return _serialize(doc)


@router.patch("/classes/{class_id}", response_model=DiseaseClassOut)
async def update_disease_class(
    class_id: str, payload: DiseaseClassUpdate, admin: dict = Depends(require_admin)
):
    """Admin-only: edit the advice text for an existing recommendation entry."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        object_id = ObjectId(class_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid class id")

    existing = await db[settings.DISEASE_CLASS_COLLECTION].find_one({"_id": object_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Recommendation entry not found")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    updates["updated_by"] = admin["email"]
    updates["updated_at"] = datetime.now(timezone.utc)
    await db[settings.DISEASE_CLASS_COLLECTION].update_one({"_id": object_id}, {"$set": updates})

    updated = await db[settings.DISEASE_CLASS_COLLECTION].find_one({"_id": object_id})
    app_logger.info(f"Disease class '{class_id}' updated by {admin['email']}")
    return _serialize(updated)


@router.delete("/classes/{class_id}", status_code=204)
async def delete_disease_class(class_id: str, admin: dict = Depends(require_admin)):
    """Admin-only: remove a recommendation entry."""
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        object_id = ObjectId(class_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid class id")

    result = await db[settings.DISEASE_CLASS_COLLECTION].delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recommendation entry not found")

    app_logger.info(f"Disease class '{class_id}' deleted by {admin['email']}")
