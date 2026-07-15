"""
ML inference service.
Loads the trained model bundle (classifier + regressor + scaler) once at
startup and exposes a simple predict() function used by the /predict route
and by the sensor ingestion pipeline (for optional auto-prediction).
"""

import os
import joblib
import numpy as np
from app.config.settings import settings
from app.config.logging_config import app_logger


class MLService:
    def __init__(self):
        self.classifier = None
        self.regressor = None
        self.scaler = None
        self.features = ["soil_moisture", "temperature", "humidity"]
        self.loaded = False

    def load(self):
        if not os.path.exists(settings.MODEL_PATH):
            app_logger.warning(
                f"Model file not found at {settings.MODEL_PATH}. "
                "Run ml/scripts/train_model.py to generate it. "
                "Predictions will fall back to a rule-based heuristic."
            )
            self.loaded = False
            return

        bundle = joblib.load(settings.MODEL_PATH)
        self.classifier = bundle["classifier"]
        self.regressor = bundle["regressor"]
        self.scaler = bundle["scaler"]
        self.features = bundle.get("features", self.features)
        self.loaded = True
        app_logger.info(f"ML model loaded from {settings.MODEL_PATH}")

    def _rule_based_fallback(self, soil_moisture, temperature, humidity):
        """Used only if no trained model artifact is present, so the API
        never hard-fails even before training has been run."""
        dryness = (100 - soil_moisture) / 100
        heat = (temperature - 10) / 35
        dry_air = (100 - humidity) / 100
        need_score = 0.55 * dryness + 0.25 * heat + 0.20 * dry_air
        irrigate = need_score > 0.45
        water = round(max(0, need_score * 40), 2) if irrigate else 0.0
        return irrigate, min(0.99, round(0.5 + need_score / 2, 2)), water

    def predict(self, soil_moisture: float, temperature: float, humidity: float):
        if not self.loaded:
            irrigate, confidence, water = self._rule_based_fallback(
                soil_moisture, temperature, humidity
            )
            reasoning = "Rule-based fallback (no trained model artifact found)."
            return irrigate, confidence, water, reasoning

        X = np.array([[soil_moisture, temperature, humidity]])
        X_scaled = self.scaler.transform(X)

        pred_class = self.classifier.predict(X_scaled)[0]
        proba = self.classifier.predict_proba(X_scaled)[0]
        confidence = float(max(proba))

        irrigate = bool(pred_class == 1)
        if irrigate:
            water_amount = float(self.regressor.predict(X_scaled)[0])
            water_amount = round(max(0.0, water_amount), 2)
        else:
            water_amount = 0.0

        if irrigate:
            reasoning = (
                f"Soil moisture {soil_moisture}% is low relative to temperature "
                f"{temperature}°C and humidity {humidity}%, indicating irrigation is needed."
            )
        else:
            reasoning = (
                f"Soil moisture {soil_moisture}% is sufficient given current "
                f"temperature {temperature}°C and humidity {humidity}%."
            )

        return irrigate, round(confidence, 3), water_amount, reasoning


ml_service = MLService()
