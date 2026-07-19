"""
Disease classifier inference service.

Loads a trained ONNX model (produced offline by
ml/disease_classifier/scripts/train_classifier.py) and runs inference on
uploaded plant photos. Deliberately uses `onnxruntime` instead of
TensorFlow for serving — a small fraction of TensorFlow's memory
footprint, which matters on Render's free tier (512MB RAM).

If no model has been deployed yet, all methods report a clear
"not trained yet" state rather than crashing, matching the same graceful-
degradation pattern used by ml_service.py for the irrigation model.
"""

import os
import json
import io

import numpy as np
from PIL import Image

from app.config.settings import settings
from app.config.logging_config import app_logger

IMG_SIZE = (224, 224)


def _mobilenet_v2_preprocess(image_array: np.ndarray) -> np.ndarray:
    """
    Replicates tf.keras.applications.mobilenet_v2.preprocess_input without
    needing TensorFlow installed: scales pixel values from [0, 255] to
    [-1, 1]. Must match exactly what train_classifier.py used, or
    predictions will be silently wrong.
    """
    return (image_array / 127.5) - 1.0


class DiseaseClassifierService:
    def __init__(self):
        self.session = None
        self.class_metadata = []  # list of {class_name, crop, disease_label}
        self.input_name = None
        self.training_report = None
        self.loaded = False

    def load(self):
        model_path = os.path.join(settings.DISEASE_MODEL_DIR, "model.onnx")
        classes_path = os.path.join(settings.DISEASE_MODEL_DIR, "class_names.json")
        report_path = os.path.join(settings.DISEASE_MODEL_DIR, "training_report.json")

        if not os.path.exists(model_path) or not os.path.exists(classes_path):
            app_logger.info(
                "Disease classifier not yet trained/deployed (no model.onnx found). "
                "Train one offline with ml/disease_classifier/scripts/train_classifier.py, "
                "then deploy it via the Admin Panel's 'Train Custom Model' tab."
            )
            self.loaded = False
            return

        try:
            import onnxruntime as ort
        except ImportError:
            app_logger.error("onnxruntime is not installed — cannot load disease classifier model")
            self.loaded = False
            return

        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

        with open(classes_path) as f:
            self.class_metadata = json.load(f)

        if os.path.exists(report_path):
            with open(report_path) as f:
                self.training_report = json.load(f)
        else:
            self.training_report = None

        self.loaded = True
        crop_disease_pairs = [f"{c['crop']}/{c['disease_label']}" for c in self.class_metadata]
        app_logger.info(
            f"Disease classifier loaded: {len(self.class_metadata)} classes -> {crop_disease_pairs}"
        )

    def reload(self):
        """Called after an admin uploads a new model, to hot-swap it in without a restart."""
        self.load()

    def list_crops(self) -> list:
        return sorted({c["crop"] for c in self.class_metadata})

    def predict(self, image_bytes: bytes):
        """Returns (crop, disease_label, confidence)."""
        if not self.loaded:
            raise RuntimeError(
                "No disease classifier model has been deployed yet. "
                "An admin needs to train one offline and upload it via the Admin Panel."
            )

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ValueError(f"Could not read image file: {e}") from e

        image = image.resize(IMG_SIZE)
        array = np.array(image, dtype=np.float32)
        array = _mobilenet_v2_preprocess(array)
        array = np.expand_dims(array, axis=0)  # add batch dimension

        outputs = self.session.run(None, {self.input_name: array})
        probabilities = outputs[0][0]  # first output, first (only) batch item

        predicted_index = int(np.argmax(probabilities))
        predicted_class = self.class_metadata[predicted_index]
        confidence = float(probabilities[predicted_index])

        return predicted_class["crop"], predicted_class["disease_label"], confidence


disease_service = DiseaseClassifierService()
