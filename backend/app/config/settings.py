"""
Centralized application configuration.
All values are overridable via environment variables / .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Smart Agriculture Monitoring API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "smart_agriculture"
    SENSOR_COLLECTION: str = "sensor_readings"
    PREDICTION_COLLECTION: str = "predictions"
    USER_COLLECTION: str = "users"
    DEVICE_COLLECTION: str = "devices"

    # Auth
    JWT_SECRET_KEY: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Bootstrap: on first startup, if no admin user exists yet, one is
    # created automatically from these credentials. Set these as real
    # secrets in production (Render env vars), then you can log in as
    # admin immediately without manual DB setup.
    ADMIN_BOOTSTRAP_EMAIL: str = ""
    ADMIN_BOOTSTRAP_PASSWORD: str = ""
    ADMIN_BOOTSTRAP_NAME: str = "Administrator"

    # MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_TOPIC: str = "farm/sensors"
    MQTT_CLIENT_ID: str = "smart-agri-backend"
    MQTT_ENABLED: bool = True
    MQTT_USE_TLS: bool = False
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""
    MQTT_CA_CERT_PATH: str = ""

    # ML model
    MODEL_PATH: str = "/app/ml/models/irrigation_model.pkl"

    # Disease classifier (offline-trained, ONNX-served)
    DISEASE_MODEL_DIR: str = "/app/ml/disease_classifier/models"
    DISEASE_CLASS_COLLECTION: str = "disease_classes"
    TRAINING_STATUS_COLLECTION: str = "training_status"

    # CORS
    CORS_ORIGINS: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
