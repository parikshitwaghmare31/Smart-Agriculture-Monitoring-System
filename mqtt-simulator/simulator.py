"""
simulator.py
------------
Simulates one or more ESP32 field devices publishing soil moisture,
temperature, and humidity readings over MQTT at a fixed interval.

This stands in for real ESP32 hardware. The JSON payload format matches
exactly what a real ESP32 sketch (see esp32_sketch.ino) would publish, so
swapping in real hardware later requires zero backend changes.

Usage:
    python simulator.py --devices 3 --interval 5
"""

import json
import time
import random
import argparse
import os
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "farm/sensors")
MQTT_USE_TLS = os.getenv("MQTT_USE_TLS", "false").lower() == "true"
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")


class VirtualSensor:
    """Keeps internal state so readings drift smoothly instead of jumping
    randomly every tick — much closer to how a real sensor behaves."""

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.soil_moisture = random.uniform(30, 70)
        self.temperature = random.uniform(20, 32)
        self.humidity = random.uniform(40, 70)

    def _drift(self, value, min_v, max_v, max_step):
        value += random.uniform(-max_step, max_step)
        return max(min_v, min(max_v, value))

    def read(self):
        self.soil_moisture = self._drift(self.soil_moisture, 0, 100, 2.5)
        self.temperature = self._drift(self.temperature, 10, 45, 0.8)
        self.humidity = self._drift(self.humidity, 10, 100, 2.0)

        return {
            "device_id": self.device_id,
            "soil_moisture": round(self.soil_moisture, 2),
            "temperature": round(self.temperature, 2),
            "humidity": round(self.humidity, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def main():
    parser = argparse.ArgumentParser(description="ESP32 MQTT sensor simulator")
    parser.add_argument("--devices", type=int, default=2, help="Number of virtual devices")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between publishes")
    parser.add_argument("--broker", type=str, default=MQTT_BROKER_HOST)
    parser.add_argument("--port", type=int, default=MQTT_BROKER_PORT)
    parser.add_argument("--topic", type=str, default=MQTT_TOPIC)
    args = parser.parse_args()

    client = mqtt.Client(client_id="esp32-simulator", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    if MQTT_USE_TLS:
        client.tls_set()  # uses system CA trust store; fine for publicly-trusted cloud brokers
        client.tls_insecure_set(False)

    print(f"Connecting to MQTT broker at {args.broker}:{args.port} (TLS={'on' if MQTT_USE_TLS else 'off'}) ...")
    client.connect(args.broker, args.port, keepalive=60)
    client.loop_start()

    sensors = [VirtualSensor(f"esp32-field-{i+1:02d}") for i in range(args.devices)]

    print(f"Simulating {len(sensors)} device(s), publishing to '{args.topic}' every {args.interval}s")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            for sensor in sensors:
                payload = sensor.read()
                client.publish(args.topic, json.dumps(payload), qos=1)
                print(f"Published: {payload}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopping simulator...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
