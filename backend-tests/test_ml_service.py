"""
Unit tests for the ML inference service.

These deliberately avoid needing MongoDB or MQTT running, so they're
suitable for CI: they test the ML service in isolation.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.ml_service import MLService


def _service_with_model():
    svc = MLService()
    svc.load()
    return svc


def test_model_loads_successfully():
    svc = _service_with_model()
    assert svc.loaded is True, (
        "Model failed to load. Did you run `python ml/scripts/train_model.py` "
        "and set MODEL_PATH correctly before running tests?"
    )


def test_predict_returns_expected_shape():
    svc = _service_with_model()
    irrigate, confidence, water_amount, reasoning = svc.predict(
        soil_moisture=40, temperature=28, humidity=50
    )
    assert isinstance(irrigate, bool)
    assert 0.0 <= confidence <= 1.0
    assert water_amount >= 0.0
    assert isinstance(reasoning, str) and len(reasoning) > 0


def test_dry_hot_conditions_recommend_irrigation():
    """Sanity check the model against an unambiguous agronomic scenario:
    very dry soil + high heat + low humidity should always recommend irrigation."""
    svc = _service_with_model()
    irrigate, confidence, water_amount, _ = svc.predict(
        soil_moisture=10, temperature=40, humidity=15
    )
    assert irrigate is True
    assert water_amount > 0


def test_wet_mild_conditions_recommend_no_irrigation():
    """Sanity check the opposite scenario: saturated soil + mild weather
    should not recommend irrigation."""
    svc = _service_with_model()
    irrigate, confidence, water_amount, _ = svc.predict(
        soil_moisture=90, temperature=20, humidity=70
    )
    assert irrigate is False
    assert water_amount == 0.0
