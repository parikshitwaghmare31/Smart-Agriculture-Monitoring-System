"""
Quick standalone test: confirms your machine can connect to your EMQX Cloud
broker over TLS with the credentials you created. Run this once locally
before deploying, to catch connection issues early.

Usage:
    pip install paho-mqtt
    python test_mqtt_connection.py
"""

import paho.mqtt.client as mqtt
import time

# --- EDIT THESE THREE VALUES ---
BROKER_HOST = "gf81afde.ala.asia-southeast1.emqxsl.com"
MQTT_USERNAME = "smartagri_mqtt"
MQTT_PASSWORD = "Amruta1999"  # <-- replace this
# --------------------------------

BROKER_PORT = 8883


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("✅ SUCCESS: Connected to EMQX Cloud broker over TLS!")
    else:
        print(f"❌ FAILED: Connection refused with reason code {reason_code}")
        print("   (8 = bad username/password, 5 = not authorized — double check credentials)")


client = mqtt.Client(client_id="local-connection-test", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set()  # uses your system's trusted CA store — works for EMQX Cloud's public cert
client.on_connect = on_connect

print(f"Connecting to {BROKER_HOST}:{BROKER_PORT} ...")
client.connect(BROKER_HOST, BROKER_PORT, keepalive=10)
client.loop_start()
time.sleep(3)
client.loop_stop()
client.disconnect()
