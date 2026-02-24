/**
 * Self-Healing IoT — ESP32 Sensor Node
 * ======================================
 * Sensors : DHT22 (Temperature + Humidity)
 *           Optionally: MQ135 (Air quality), BMP280 (Pressure)
 *
 * Libraries to install in Arduino IDE (Sketch → Include Library → Manage Libraries):
 *   - PubSubClient   by Nick O'Leary
 *   - ArduinoJson    by Benoit Blanchon  (v6.x)
 *   - DHT sensor     by Adafruit
 *   - Adafruit Unified Sensor
 *
 * Wiring (ESP32 DevKit):
 *   DHT22 VCC  → 3.3V pin
 *   DHT22 DATA → GPIO 4
 *   DHT22 GND  → GND
 *
 * How to use:
 *   1. Fill in WIFI_SSID, WIFI_PASSWORD, MQTT_BROKER below
 *   2. Give each physical device a unique DEVICE_ID
 *   3. Flash via Arduino IDE (Board: "ESP32 Dev Module")
 *   4. Device auto-appears in dashboard within 10 seconds
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ═══════════════════════════════════════════
//  !! CHANGE THESE FOR EACH DEVICE !!
// ═══════════════════════════════════════════
const char* WIFI_SSID      = "YourWiFiName";
const char* WIFI_PASSWORD  = "YourWiFiPassword";
const char* MQTT_BROKER    = "192.168.1.100";   // IP of PC running Mosquitto
const int   MQTT_PORT      = 1883;
const char* DEVICE_ID      = "esp32_node_01";   // Unique per device!
const char* DEVICE_NAME    = "ESP32 Living Room";
const char* LOCATION       = "living_room";
// ═══════════════════════════════════════════

// Sensor setup
#define DHT_PIN    4
#define DHT_TYPE   DHT22
#define LED_PIN    2   // Built-in LED — blinks on anomaly or healing
DHT dht(DHT_PIN, DHT_TYPE);

// MQTT
WiFiClient   espClient;
PubSubClient mqtt(espClient);

// State
unsigned long lastTelemetry  = 0;
unsigned long lastHeartbeat  = 0;
unsigned long startTime      = 0;
bool         isHealing       = false;
float        lastTemp        = 0.0;
float        lastHumidity    = 0.0;
int          telemetryCount  = 0;

// Topic strings (built in setup)
char topicTelemetryTemp[80];
char topicTelemetryHum[80];
char topicHeartbeat[80];
char topicStatus[80];
char topicCommand[80];

// ─────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  dht.begin();
  startTime = millis();

  // Build MQTT topic strings
  snprintf(topicTelemetryTemp, sizeof(topicTelemetryTemp),
           "iot/telemetry/%s/temperature", DEVICE_ID);
  snprintf(topicTelemetryHum,  sizeof(topicTelemetryHum),
           "iot/telemetry/%s/humidity", DEVICE_ID);
  snprintf(topicHeartbeat,     sizeof(topicHeartbeat),
           "iot/health/%s/heartbeat", DEVICE_ID);
  snprintf(topicStatus,        sizeof(topicStatus),
           "iot/status/%s", DEVICE_ID);
  snprintf(topicCommand,       sizeof(topicCommand),
           "iot/commands/%s/#", DEVICE_ID);

  connectWiFi();

  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(onCommand);
  mqtt.setBufferSize(512);

  connectMQTT();
  Serial.println("✓ Setup complete. Publishing telemetry every 5s.");
}

// ─────────────────────────────────────────────
void loop() {
  // Maintain MQTT connection
  if (!mqtt.connected()) connectMQTT();
  mqtt.loop();

  unsigned long now = millis();

  // Publish telemetry every 5 seconds
  if (now - lastTelemetry >= 5000) {
    publishTelemetry();
    lastTelemetry = now;
  }

  // Publish heartbeat every 30 seconds
  if (now - lastHeartbeat >= 30000) {
    publishHeartbeat();
    lastHeartbeat = now;
  }
}

// ─────────────────────────────────────────────
void connectWiFi() {
  Serial.printf("Connecting to WiFi: %s", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.printf("\n✓ WiFi connected! IP: %s\n", WiFi.localIP().toString().c_str());
}

void connectMQTT() {
  int attempts = 0;
  while (!mqtt.connected() && attempts < 5) {
    Serial.printf("Connecting to MQTT broker %s:%d ...\n", MQTT_BROKER, MQTT_PORT);
    if (mqtt.connect(DEVICE_ID)) {
      Serial.println("✓ MQTT connected!");
      mqtt.subscribe(topicCommand);
      publishHeartbeat();  // Announce presence immediately
      publishStatus("online", "Device connected");
    } else {
      Serial.printf("✗ MQTT failed, rc=%d — retrying in 3s\n", mqtt.state());
      delay(3000);
      attempts++;
    }
  }
}

// ─────────────────────────────────────────────
//  TELEMETRY PUBLISHING
// ─────────────────────────────────────────────
void publishTelemetry() {
  float temp = dht.readTemperature();
  float hum  = dht.readHumidity();

  if (isnan(temp) || isnan(hum)) {
    Serial.println("⚠ Sensor read failed!");
    publishStatus("sensor_error", "DHT22 read failed");
    return;
  }

  lastTemp     = temp;
  lastHumidity = hum;
  telemetryCount++;

  // ── Temperature ──────────────────────────
  StaticJsonDocument<256> doc;
  doc["device_id"]      = DEVICE_ID;
  doc["device_name"]    = DEVICE_NAME;
  doc["device_type"]    = "esp32";
  doc["sensor_type"]    = "temperature";
  doc["value"]          = serialized(String(temp, 2));
  doc["unit"]           = "C";
  doc["location"]       = LOCATION;
  doc["rssi"]           = WiFi.RSSI();          // Signal strength
  doc["uptime_ms"]      = millis() - startTime;
  doc["seq"]            = telemetryCount;
  doc["timestamp"]      = millis();             // Use NTP in production

  char buf[256];
  serializeJson(doc, buf);
  mqtt.publish(topicTelemetryTemp, buf);

  // ── Humidity ─────────────────────────────
  doc["sensor_type"] = "humidity";
  doc["value"]       = serialized(String(hum, 2));
  doc["unit"]        = "%";
  serializeJson(doc, buf);
  mqtt.publish(topicTelemetryHum, buf);

  Serial.printf("[%s] Temp=%.2f°C  Hum=%.2f%%  RSSI=%ddBm\n",
                DEVICE_ID, temp, hum, WiFi.RSSI());
}

// ─────────────────────────────────────────────
//  HEARTBEAT
// ─────────────────────────────────────────────
void publishHeartbeat() {
  StaticJsonDocument<256> doc;
  doc["device_id"]    = DEVICE_ID;
  doc["device_name"]  = DEVICE_NAME;
  doc["device_type"]  = "esp32";
  doc["location"]     = LOCATION;
  doc["status"]       = "online";
  doc["uptime_ms"]    = millis() - startTime;
  doc["rssi"]         = WiFi.RSSI();
  doc["ip"]           = WiFi.localIP().toString();
  doc["mac"]          = WiFi.macAddress();
  doc["free_heap"]    = ESP.getFreeHeap();
  doc["telemetry_count"] = telemetryCount;

  char buf[256];
  serializeJson(doc, buf);
  // retain=true so server sees it even if it starts after device
  mqtt.publish(topicHeartbeat, buf, true);
  Serial.printf("[%s] ♥ Heartbeat sent\n", DEVICE_ID);
}

// ─────────────────────────────────────────────
//  STATUS
// ─────────────────────────────────────────────
void publishStatus(const char* event, const char* message) {
  StaticJsonDocument<128> doc;
  doc["device_id"] = DEVICE_ID;
  doc["event"]     = event;
  doc["message"]   = message;
  doc["uptime_ms"] = millis() - startTime;
  char buf[128];
  serializeJson(doc, buf);
  mqtt.publish(topicStatus, buf);
}

// ─────────────────────────────────────────────
//  RECEIVE HEALING COMMANDS FROM BACKEND
// ─────────────────────────────────────────────
void onCommand(char* topic, byte* payload, unsigned int length) {
  // Parse command JSON
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (err) { Serial.println("⚠ JSON parse error"); return; }

  const char* command = doc["command"] | "unknown";
  Serial.printf("\n📩 Received command: %s\n", command);
  isHealing = true;
  blinkLED(3);  // Signal healing received

  // ── Handle each healing action ─────────────
  if (strcmp(command, "ping") == 0) {
    // Liveness check — respond with heartbeat
    publishHeartbeat();
    publishStatus("pong", "Alive");

  } else if (strcmp(command, "reset") == 0) {
    // Full hardware restart — most powerful healing
    Serial.println("  → Hardware reset in 2 seconds...");
    publishStatus("resetting", "Hardware reset triggered by AI");
    delay(2000);
    ESP.restart();

  } else if (strcmp(command, "recalibrate") == 0) {
    // Re-read sensor and report new baseline
    Serial.println("  → Recalibrating sensor...");
    delay(2000);  // Let sensor settle
    float newTemp = dht.readTemperature();
    float newHum  = dht.readHumidity();
    char msg[80];
    snprintf(msg, sizeof(msg), "Recalibrated: %.2fC / %.2f%%", newTemp, newHum);
    publishStatus("recalibrated", msg);
    Serial.printf("  → %s\n", msg);

  } else if (strcmp(command, "increase_frequency") == 0) {
    // Send 10 rapid readings for AI validation
    Serial.println("  → Sending 10 validation readings...");
    for (int i = 0; i < 10; i++) {
      publishTelemetry();
      delay(1000);
    }
    publishStatus("validation_complete", "10 samples sent");

  } else if (strcmp(command, "validate") == 0) {
    int samples = doc["parameters"]["sample_count"] | 5;
    Serial.printf("  → Sending %d validation samples...\n", samples);
    for (int i = 0; i < samples; i++) {
      publishTelemetry();
      delay(1500);
    }
    publishStatus("validated", "Validation samples sent");

  } else {
    Serial.printf("  → Unknown command: %s\n", command);
    publishStatus("unknown_command", command);
  }

  isHealing = false;
}

// ─────────────────────────────────────────────
void blinkLED(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(150);
    digitalWrite(LED_PIN, LOW);
    delay(150);
  }
}
