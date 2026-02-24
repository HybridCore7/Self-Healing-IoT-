# Hardware Integration Guide

This guide explains how to connect real IoT hardware devices to the Self-Healing IoT System.

## Overview

The system is designed to work with any IoT device that can:
1. Connect to an MQTT broker
2. Publish sensor data in JSON format
3. Subscribe to and execute commands

## Supported Hardware Platforms

### 1. ESP32/ESP8266 (Recommended)
- **Cost**: $5-15
- **WiFi**: Built-in
- **Sensors**: GPIO, I2C, SPI support
- **Programming**: Arduino IDE, MicroPython, ESP-IDF

### 2. Raspberry Pi
- **Cost**: $35-75
- **WiFi**: Built-in (Pi 3+)
- **Sensors**: GPIO, I2C, SPI, USB
- **Programming**: Python, Node.js, C++

### 3. Arduino with WiFi/Ethernet Shield
- **Cost**: $20-40
- **Connectivity**: WiFi/Ethernet shield required
- **Sensors**: GPIO, I2C, SPI
- **Programming**: Arduino IDE

### 4. Other Platforms
- STM32 with WiFi module
- Nordic nRF52 series
- Any device with MQTT client library support

## Hardware Setup

### Option 1: ESP32 with DHT22 Sensor (Temperature & Humidity)

#### Components Needed
- ESP32 development board
- DHT22 temperature/humidity sensor
- Jumper wires
- Breadboard (optional)
- Micro USB cable

#### Wiring
```
DHT22 Pin 1 (VCC)  -> ESP32 3.3V
DHT22 Pin 2 (Data) -> ESP32 GPIO 4
DHT22 Pin 4 (GND)  -> ESP32 GND
```

#### Arduino Code

```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Broker
const char* mqtt_server = "YOUR_MQTT_BROKER_IP";  // e.g., "192.168.1.100"
const int mqtt_port = 1883;

// Device configuration
const char* device_id = "device_001";
const char* device_name = "ESP32 Sensor Node 1";

// DHT22 sensor
#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// MQTT client
WiFiClient espClient;
PubSubClient client(espClient);

// Timing
unsigned long lastTelemetry = 0;
unsigned long lastHeartbeat = 0;
const long telemetryInterval = 10000;  // 10 seconds
const long heartbeatInterval = 30000;  // 30 seconds

void setup() {
  Serial.begin(115200);
  
  // Initialize DHT sensor
  dht.begin();
  
  // Connect to WiFi
  setup_wifi();
  
  // Setup MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  
  // Parse JSON payload
  StaticJsonDocument<256> doc;
  deserializeJson(doc, payload, length);
  
  const char* command = doc["command"];
  
  // Handle commands
  if (strcmp(command, "reset") == 0) {
    Serial.println("Executing reset command");
    dht.begin();
  }
  else if (strcmp(command, "restart") == 0) {
    Serial.println("Executing restart command");
    ESP.restart();
  }
  else if (strcmp(command, "ping") == 0) {
    Serial.println("Ping received");
    publishHeartbeat();
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    if (client.connect(device_id)) {
      Serial.println("connected");
      
      // Subscribe to command topics
      String commandTopic = "iot/commands/" + String(device_id) + "/#";
      client.subscribe(commandTopic.c_str());
      
      publishHeartbeat();
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void publishTelemetry() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }
  
  // Publish temperature
  StaticJsonDocument<256> tempDoc;
  tempDoc["device_id"] = device_id;
  tempDoc["sensor_type"] = "temperature";
  tempDoc["value"] = temperature;
  tempDoc["unit"] = "°C";
  tempDoc["timestamp"] = millis();
  
  char tempBuffer[256];
  serializeJson(tempDoc, tempBuffer);
  
  String tempTopic = "iot/telemetry/" + String(device_id) + "/temperature";
  client.publish(tempTopic.c_str(), tempBuffer);
  
  // Publish humidity
  StaticJsonDocument<256> humDoc;
  humDoc["device_id"] = device_id;
  humDoc["sensor_type"] = "humidity";
  humDoc["value"] = humidity;
  humDoc["unit"] = "%";
  humDoc["timestamp"] = millis();
  
  char humBuffer[256];
  serializeJson(humDoc, humBuffer);
  
  String humTopic = "iot/telemetry/" + String(device_id) + "/humidity";
  client.publish(humTopic.c_str(), humBuffer);
  
  Serial.printf("Published: Temp=%.2f°C, Humidity=%.2f%%\n", temperature, humidity);
}

void publishHeartbeat() {
  StaticJsonDocument<256> doc;
  doc["device_id"] = device_id;
  doc["status"] = "online";
  doc["timestamp"] = millis();
  
  JsonObject metadata = doc.createNestedObject("metadata");
  metadata["uptime_seconds"] = millis() / 1000;
  metadata["device_name"] = device_name;
  metadata["device_type"] = "esp32_sensor";
  metadata["sensor_count"] = 2;
  metadata["rssi"] = WiFi.RSSI();
  
  char buffer[256];
  serializeJson(doc, buffer);
  
  String topic = "iot/health/" + String(device_id) + "/heartbeat";
  client.publish(topic.c_str(), buffer, true);
  
  Serial.println("Heartbeat published");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  unsigned long now = millis();
  
  if (now - lastTelemetry > telemetryInterval) {
    lastTelemetry = now;
    publishTelemetry();
  }
  
  if (now - lastHeartbeat > heartbeatInterval) {
    lastHeartbeat = now;
    publishHeartbeat();
  }
}
```

#### Required Arduino Libraries
- WiFi (built-in)
- PubSubClient (by Nick O'Leary)
- DHT sensor library (by Adafruit)
- ArduinoJson (by Benoit Blanchon)

Install via Arduino IDE: `Sketch > Include Library > Manage Libraries`

### Option 2: Raspberry Pi with Python

See `examples/raspberry_pi_client.py` for complete Python implementation.

## MQTT Topic Structure

### Publishing (Device → System)

**Telemetry:**
```
Topic: iot/telemetry/{device_id}/{sensor_type}
Payload: {
  "device_id": "device_001",
  "sensor_type": "temperature",
  "value": 23.5,
  "unit": "°C",
  "timestamp": "2026-02-11T03:00:00Z"
}
```

**Heartbeat:**
```
Topic: iot/health/{device_id}/heartbeat
Payload: {
  "device_id": "device_001",
  "status": "online",
  "timestamp": "2026-02-11T03:00:00Z",
  "metadata": {
    "uptime_seconds": 3600
  }
}
```

### Subscribing (System → Device)

**Commands:**
```
Topic: iot/commands/{device_id}/#
Payload: {
  "command": "reset",
  "parameters": {}
}
```

## Device Registration

Register device via API before connecting:

```bash
curl -X POST http://localhost:8000/api/devices \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device_001",
    "device_name": "ESP32 Sensor Node 1",
    "device_type": "esp32_sensor",
    "location": "Lab Room A"
  }'
```

## Supported Commands

| Command | Description |
|---------|-------------|
| `ping` | Respond with heartbeat |
| `reset` | Reset sensor |
| `restart` | Restart device |
| `calibrate` | Calibrate sensor |
| `validate` | Take multiple readings |

## Testing

1. Start backend: `python -m src.backend.main`
2. Flash hardware code
3. Monitor MQTT: `mosquitto_sub -h localhost -t "iot/#" -v`
4. Check API: `curl http://localhost:8000/api/devices`

## Troubleshooting

- **No connection**: Check WiFi credentials and MQTT broker IP
- **No data**: Verify topic format and JSON payload
- **Commands not working**: Ensure subscription to command topics

For detailed examples and advanced configurations, see the `examples/` directory.
