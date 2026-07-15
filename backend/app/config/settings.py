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

    # MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_TOPIC: str = "farm/sensors"
    MQTT_CLIENT_ID: str = "smart-agri-backend"
    MQTT_ENABLED: bool = True

    # ML model
    MODEL_PATH: str = "/app/ml/models/irrigation_model.pkl"

    # CORS
    CORS_ORIGINS: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
