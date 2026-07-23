"""
test_alert_trigger.py
-----------------------
Publishes ONE deliberately dry sensor reading to EMQX Cloud, using the
device_id of a device you've already registered to a farmer (via the
Admin Panel). Since it publishes to the real MQTT topic, your backend
processes it exactly like it would from real ESP32 hardware — including
the irrigation prediction and alert check.

Use this to verify the full pipeline (MQTT -> backend -> prediction ->
alert -> SMS/WhatsApp) works, before real hardware exists.

Usage:
    pip install paho-mqtt
    python test_alert_trigger.py
"""

import json
import time
import paho.mqtt.client as mqtt

# --- EDIT THESE ---
BROKER_HOST = "gf81afde.ala.asia-southeast1.emqxsl.com"
MQTT_USERNAME = "smartagri_mqtt"
MQTT_PASSWORD = "Devamruta0399"  # <-- replace this
DEVICE_ID = "esp32-field-04"          # <-- the farmer's REGISTERED device_id
# ------------------

BROKER_PORT = 8883
TOPIC = "farm/sensors"


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("Connected. Publishing test reading...")
        payload = {
            "device_id": DEVICE_ID,
            "soil_moisture": 8,     # very dry — should trigger irrigate=true
            "temperature": 39,
            "humidity": 18,
        }
        client.publish(TOPIC, json.dumps(payload), qos=1)
        print(f"Published: {payload}")
    else:
        print(f"Connection failed: {reason_code}")


client = mqtt.Client(client_id="alert-trigger-test", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set()
client.on_connect = on_connect

client.connect(BROKER_HOST, BROKER_PORT, keepalive=10)
client.loop_start()
time.sleep(3)
client.loop_stop()
client.disconnect()

print("\nDone. Now check:")
print("1. Render backend logs — search for 'Stored sensor reading' then 'Irrigation alert'")
print("2. Twilio Console -> Monitor -> Logs -> Messaging — for a new outgoing message")
print("3. Your phone, if alerts_enabled + phone_number are set for this device's owner")
