"""
Unit tests for the disease classifier service. Since no model has been
trained/deployed yet in this environment (that happens offline, per an
admin's own dataset), these tests verify the graceful "not trained yet"
behavior rather than actual classification accuracy.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.disease_service import DiseaseClassifierService


def test_service_reports_not_loaded_when_no_model_deployed(tmp_path):
    service = DiseaseClassifierService()
    # Point at an empty directory, guaranteed to have no model.onnx yet
    from app.config.settings import settings

    original_dir = settings.DISEASE_MODEL_DIR
    settings.DISEASE_MODEL_DIR = str(tmp_path)
    try:
        service.load()
        assert service.loaded is False
        assert service.class_metadata == []
    finally:
        settings.DISEASE_MODEL_DIR = original_dir


def test_predict_raises_clear_error_when_not_loaded():
    service = DiseaseClassifierService()
    service.loaded = False
    try:
        service.predict(b"fake-image-bytes")
        assert False, "Expected RuntimeError when no model is deployed"
    except RuntimeError as e:
        assert "not been deployed" in str(e) or "No disease classifier" in str(e)


def test_list_crops_empty_when_no_classes_loaded():
    service = DiseaseClassifierService()
    service.class_metadata = []
    assert service.list_crops() == []


def test_list_crops_deduplicates_and_sorts():
    service = DiseaseClassifierService()
    service.class_metadata = [
        {"class_name": "Tomato__Healthy", "crop": "Tomato", "disease_label": "Healthy"},
        {"class_name": "Tomato__Early_Blight", "crop": "Tomato", "disease_label": "Early Blight"},
        {"class_name": "Potato__Healthy", "crop": "Potato", "disease_label": "Healthy"},
    ]
    assert service.list_crops() == ["Potato", "Tomato"]
