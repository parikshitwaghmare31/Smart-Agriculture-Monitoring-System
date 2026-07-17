/*
  esp32_sketch.ino
  -----------------
  Real ESP32 firmware for the Smart Agriculture Monitoring System.
  Updated to connect to EMQX Cloud over TLS (port 8883) with username/password
  authentication, matching the project's current cloud MQTT setup.

  Hardware:
    - Capacitive soil moisture sensor -> analog pin 34
    - DHT22 temperature/humidity sensor -> digital pin 4

  Publishes the exact same JSON payload shape as mqtt-simulator/simulator.py,
  so the backend requires zero changes when switching from simulation to
  real hardware.

  Required libraries (Arduino Library Manager):
    - PubSubClient
    - DHT sensor library (Adafruit)
    - ArduinoJson

  IMPORTANT: Give every physical device a UNIQUE DEVICE_ID below (e.g.
  esp32-field-01, esp32-field-02, ...) so the dashboard can tell them apart.
*/

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ---- WiFi ----
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// ---- MQTT (EMQX Cloud) ----
const char* MQTT_BROKER   = "gf81afde.ala.asia-southeast1.emqxsl.com";
const int   MQTT_PORT     = 8883;               // TLS port
const char* MQTT_TOPIC    = "farm/sensors";
const char* MQTT_USERNAME = "smartagri_mqtt";
const char* MQTT_PASSWORD = "YOUR_MQTT_PASSWORD";

// vvv CHANGE THIS FOR EACH PHYSICAL DEVICE vvv
const char* DEVICE_ID     = "esp32-field-01";
// ^^^ e.g. esp32-field-02, esp32-field-03 for additional units ^^^

// ---- TLS ----
// Option A (simplest, OK for hobby/demo projects): skip certificate
// validation entirely. This still encrypts traffic but does not verify
// the broker's identity, so it's vulnerable to man-in-the-middle attacks
// on untrusted networks. Fine for a home WiFi network demo.
#define USE_INSECURE_TLS true

// Option B (recommended for anything beyond a demo): paste the CA
// certificate you downloaded from the EMQX Cloud console below, and set
// USE_INSECURE_TLS to false. This validates the broker's identity properly.
const char* EMQX_ROOT_CA = R"EOF(
-----BEGIN CERTIFICATE-----
PASTE THE CONTENTS OF YOUR DOWNLOADED emqxsl-ca.crt FILE HERE
-----END CERTIFICATE-----
)EOF";

// ---- Sensors ----
#define SOIL_MOISTURE_PIN 34
#define DHT_PIN 4
#define DHT_TYPE DHT22

DHT dht(DHT_PIN, DHT_TYPE);
WiFiClientSecure espClient;
PubSubClient mqttClient(espClient);

const unsigned long PUBLISH_INTERVAL_MS = 5000;
unsigned long lastPublish = 0;

// Calibrate these for your specific capacitive sensor
const int SOIL_DRY_RAW = 3000;   // raw ADC value in dry air
const int SOIL_WET_RAW = 1200;   // raw ADC value in water

void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected, IP: " + WiFi.localIP().toString());
}

void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT broker over TLS...");
    if (mqttClient.connect(DEVICE_ID, MQTT_USERNAME, MQTT_PASSWORD)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" retrying in 5s");
      delay(5000);
    }
  }
}

float readSoilMoisturePercent() {
  int raw = analogRead(SOIL_MOISTURE_PIN);
  int percent = map(raw, SOIL_DRY_RAW, SOIL_WET_RAW, 0, 100);
  percent = constrain(percent, 0, 100);
  return (float)percent;
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  connectWiFi();

  if (USE_INSECURE_TLS) {
    espClient.setInsecure();
  } else {
    espClient.setCACert(EMQX_ROOT_CA);
  }

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setBufferSize(300);  // small headroom above the default 256 bytes
}

void loop() {
  if (!mqttClient.connected()) {
    connectMQTT();
  }
  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastPublish >= PUBLISH_INTERVAL_MS) {
    lastPublish = now;

    float soilMoisture = readSoilMoisturePercent();
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }

    StaticJsonDocument<200> doc;
    doc["device_id"] = DEVICE_ID;
    doc["soil_moisture"] = soilMoisture;
    doc["temperature"] = temperature;
    doc["humidity"] = humidity;

    char buffer[200];
    serializeJson(doc, buffer);

    mqttClient.publish(MQTT_TOPIC, buffer);
    Serial.println(String("Published: ") + buffer);
  }
}
