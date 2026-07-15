/*
  esp32_sketch.ino
  -----------------
  Real ESP32 firmware for the Smart Agriculture Monitoring System.

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
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ---- WiFi ----
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// ---- MQTT ----
const char* MQTT_BROKER   = "192.168.1.100";   // your broker IP
const int   MQTT_PORT     = 1883;
const char* MQTT_TOPIC    = "farm/sensors";
const char* DEVICE_ID     = "esp32-field-01";

// ---- Sensors ----
#define SOIL_MOISTURE_PIN 34
#define DHT_PIN 4
#define DHT_TYPE DHT22

DHT dht(DHT_PIN, DHT_TYPE);
WiFiClient espClient;
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
    Serial.print("Connecting to MQTT broker...");
    if (mqttClient.connect(DEVICE_ID)) {
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
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
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
