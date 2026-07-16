"""
MQTT client service.

Subscribes to the sensor topic published by the ESP32 (or the Python
simulator) and stores every incoming reading in MongoDB. Runs on a
background thread managed by paho-mqtt's own network loop so it does not
block the FastAPI event loop.
"""

import json
import asyncio
import threading
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from app.config.settings import settings
from app.config.logging_config import app_logger
from app.config.database import get_database

_mqtt_connected = False


def is_mqtt_connected() -> bool:
    return _mqtt_connected


class MQTTService:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.client = mqtt.Client(
            client_id=settings.MQTT_CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        if settings.MQTT_USERNAME:
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

        if settings.MQTT_USE_TLS:
            # ca_certs=None with tls_set() uses the system CA trust store,
            # which is sufficient for most managed brokers (e.g. EMQX Cloud,
            # HiveMQ Cloud) since they use publicly-trusted certificates.
            # If MQTT_CA_CERT_PATH is provided, pin it explicitly instead.
            ca_certs = settings.MQTT_CA_CERT_PATH or None
            self.client.tls_set(ca_certs=ca_certs)
            self.client.tls_insecure_set(False)

    def start(self):
        try:
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            app_logger.error(f"Could not connect to MQTT broker: {e}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        global _mqtt_connected
        if reason_code == 0:
            _mqtt_connected = True
            app_logger.info(f"Connected to MQTT broker, subscribing to '{settings.MQTT_TOPIC}'")
            client.subscribe(settings.MQTT_TOPIC, qos=1)
        else:
            _mqtt_connected = False
            app_logger.error(f"MQTT connection failed with reason code {reason_code}")

    def on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        global _mqtt_connected
        _mqtt_connected = False
        app_logger.warning("Disconnected from MQTT broker")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            app_logger.debug(f"MQTT message received on {msg.topic}: {payload}")
            # Schedule the async DB insert on the main event loop
            asyncio.run_coroutine_threadsafe(self._persist_reading(payload), self.loop)
        except Exception as e:
            app_logger.error(f"Failed to process MQTT message: {e}")

    async def _persist_reading(self, payload: dict):
        db = get_database()
        if db is None:
            app_logger.warning("DB not ready, dropping MQTT reading")
            return

        document = {
            "device_id": payload.get("device_id", "unknown-device"),
            "soil_moisture": float(payload.get("soil_moisture", 0)),
            "temperature": float(payload.get("temperature", 0)),
            "humidity": float(payload.get("humidity", 0)),
            "timestamp": datetime.now(timezone.utc),
            "source": "mqtt",
        }
        await db[settings.SENSOR_COLLECTION].insert_one(document)
        app_logger.info(f"Stored sensor reading from {document['device_id']}")


mqtt_service_instance: "MQTTService | None" = None


def init_mqtt_service(loop):
    global mqtt_service_instance
    if not settings.MQTT_ENABLED:
        app_logger.info("MQTT disabled via settings, skipping broker connection")
        return None
    mqtt_service_instance = MQTTService(loop)
    mqtt_service_instance.start()
    return mqtt_service_instance
