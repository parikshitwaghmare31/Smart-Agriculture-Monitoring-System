"""
Smoke tests verifying the FastAPI app object is well-formed: it imports
without errors and all expected routes are registered. These tests
intentionally do NOT start the lifespan (no MongoDB/MQTT connection
required), since that's covered separately by the Docker Compose
integration environment, not unit CI.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app

EXPECTED_PATHS = {
    "/api/v1/health",
    "/api/v1/sensor-data",
    "/api/v1/sensor-data/latest",
    "/api/v1/sensor-data/devices",
    "/api/v1/predict",
    "/api/v1/history/sensors",
    "/api/v1/history/predictions",
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/me",
    "/api/v1/devices",
    "/api/v1/devices/my",
    "/",
}


def test_app_imports_successfully():
    assert app is not None
    assert app.title == "Smart Agriculture Monitoring API"


def test_all_expected_routes_are_registered():
    registered_paths = {route.path for route in app.routes}
    missing = EXPECTED_PATHS - registered_paths
    assert not missing, f"Missing expected routes: {missing}"


def test_cors_middleware_is_configured():
    middleware_classes = [m.cls.__name__ for m in app.user_middleware]
    assert "CORSMiddleware" in middleware_classes
