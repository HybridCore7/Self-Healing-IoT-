/**
 * Self-Healing IoT — Arduino Sensor Node
 * ========================================
 * For Arduino Uno/Nano/Mega (no built-in WiFi).
 * Sends data over Serial → Raspberry Pi bridge reads it → forwards to MQTT.
 *
 * Wiring (Arduino Uno):
 *   DHT22 VCC  → 5V
 *   DHT22 DATA → Digital Pin 2
 *   DHT22 GND  → GND
 *   (Optional) LED → Pin 13 (built-in)
 *
 * Libraries: DHT sensor library by Adafruit
 * Protocol:  CSV lines over Serial at 9600 baud
 *            Format: TELEMETRY,{device_id},{sensor},{value},{unit}
 *                    HEARTBEAT,{device_id},{uptime_ms}
 *                    STATUS,{device_id},{event},{msg}
 */

#include <DHT.h>

#define DHT_PIN    2
#define DHT_TYPE   DHT22
#define LED_PIN    13

// !! Change this for each Arduino !!
#define DEVICE_ID  "arduino_node_01"
#define LOCATION   "garage"

DHT dht(DHT_PIN, DHT_TYPE);

unsigned long lastSend    = 0;
unsigned long lastBeat    = 0;
unsigned long startTime   = 0;
int           readCount   = 0;
bool          healing     = false;

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);
  dht.begin();
  startTime = millis();

  // Signal ready
  delay(2000);
  Serial.print("HEARTBEAT,");
  Serial.print(DEVICE_ID);
  Serial.print(",arduino,");
  Serial.print(LOCATION);
  Serial.println(",0");
}

void loop() {
  unsigned long now = millis();

  // Check for commands from bridge (over Serial)
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    handleCommand(cmd);
  }

  // Send telemetry every 5 seconds
  if (now - lastSend >= 5000) {
    sendTelemetry();
    lastSend = now;
  }

  // Send heartbeat every 30 seconds
  if (now - lastBeat >= 30000) {
    sendHeartbeat();
    lastBeat = now;
  }
}

void sendTelemetry() {
  float temp = dht.readTemperature();
  float hum  = dht.readHumidity();

  if (isnan(temp) || isnan(hum)) {
    Serial.print("STATUS,");
    Serial.print(DEVICE_ID);
    Serial.println(",sensor_error,DHT22 read failed");
    return;
  }
  readCount++;

  // Temperature
  Serial.print("TELEMETRY,");
  Serial.print(DEVICE_ID);
  Serial.print(",temperature,");
  Serial.print(temp, 2);
  Serial.print(",C,");
  Serial.print(LOCATION);
  Serial.print(",");
  Serial.println(readCount);

  // Humidity
  Serial.print("TELEMETRY,");
  Serial.print(DEVICE_ID);
  Serial.print(",humidity,");
  Serial.print(hum, 2);
  Serial.print(",%,");
  Serial.print(LOCATION);
  Serial.print(",");
  Serial.println(readCount);
}

void sendHeartbeat() {
  Serial.print("HEARTBEAT,");
  Serial.print(DEVICE_ID);
  Serial.print(",arduino,");
  Serial.print(LOCATION);
  Serial.print(",");
  Serial.println(millis() - startTime);
}

void handleCommand(String cmd) {
  if (cmd == "reset") {
    Serial.print("STATUS,");
    Serial.print(DEVICE_ID);
    Serial.println(",resetting,Hardware reset triggered");
    // Arduino soft reset via watchdog (requires avr/wdt.h on Uno)
    delay(500);
    asm volatile ("jmp 0");   // Jump to address 0 = software reset

  } else if (cmd == "recalibrate") {
    // Discard a few readings so sensor stabilises
    delay(2000);
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    Serial.print("STATUS,");
    Serial.print(DEVICE_ID);
    Serial.print(",recalibrated,");
    Serial.print(t); Serial.print("C/");
    Serial.print(h); Serial.println("%");

  } else if (cmd == "validate") {
    // Send 5 rapid readings
    for (int i = 0; i < 5; i++) {
      sendTelemetry();
      delay(1000);
    }
    Serial.print("STATUS,");
    Serial.print(DEVICE_ID);
    Serial.println(",validated,5 samples sent");

  } else if (cmd == "ping") {
    sendHeartbeat();

  } else if (cmd.length() > 0) {
    Serial.print("STATUS,");
    Serial.print(DEVICE_ID);
    Serial.print(",unknown_cmd,");
    Serial.println(cmd);
  }
}
