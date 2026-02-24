# Hardware Setup Guide — Self-Healing IoT Network
## Connect ESP32, Arduino & Raspberry Pi to the AI System

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         YOUR PC / SERVER                         │
│                                                                  │
│  ┌─────────────────┐    ┌──────────────────┐   ┌─────────────┐  │
│  │ Mosquitto MQTT  │    │  FastAPI Backend  │   │  Dashboard  │  │
│  │ Broker :1883    │←──→│  + AI Engine      │←→ │  :8501/8503 │  │
│  └─────────────────┘    │  + Auto-Discovery │   └─────────────┘  │
│          ↑ ↓            └──────────────────┘                     │
└──────────|───────────────────────────────────────────────────────┘
           │  WiFi / USB
    ┌──────┼────────────────────────────────────────────┐
    │      │          HARDWARE DEVICES                  │
    │   ┌──┴──────┐  ┌─────────────┐  ┌─────────────┐  │
    │   │  ESP32  │  │  Arduino +  │  │ Raspberry   │  │
    │   │  +DHT22 │  │  Pi Bridge  │  │ Pi (native) │  │
    │   └─────────┘  └─────────────┘  └─────────────┘  │
    └───────────────────────────────────────────────────┘
```

---

## Quick Start (5 Minutes)

### Step 1 — Install MQTT Broker
```bash
# Windows
# Download from https://mosquitto.org/download/
# Then start it:
mosquitto -v

# Linux / Raspberry Pi
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

### Step 2 — Start the Backend
```bash
cd d:\self-healing-iot
pip install -r requirements.txt
python -m src.backend.main
# Backend runs on http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Step 3 — Start the Dashboards
```bash
# Main live simulation dashboard
streamlit run dashboard_live.py --server.port 8501

# Hardware device manager (in another terminal)
streamlit run dashboard_hardware.py --server.port 8503
```

---

## ESP32 Setup (Recommended)

### Hardware
| Component | Cost  | Where           |
|-----------|-------|-----------------|
| ESP32 DevKit v1 | ~$3-5 | Amazon, AliExpress |
| DHT22 sensor    | ~$2   | Amazon, AliExpress |
| Jumper wires    | ~$1   | Amazon             |

### Wiring
```
DHT22 Pin 1 (VCC)  → ESP32 3.3V
DHT22 Pin 2 (DATA) → ESP32 GPIO4  (with 10kΩ pull-up to 3.3V)
DHT22 Pin 4 (GND)  → ESP32 GND
```

### Software Setup
1. Install Arduino IDE from https://www.arduino.cc/en/software

2. Add ESP32 board support:
   - File → Preferences → Additional Board URLs:
   - `https://dl.espressif.com/dl/package_esp32_index.json`
   - Tools → Board Manager → search "esp32" → Install

3. Install libraries (Sketch → Library Manager):
   - `PubSubClient` by Nick O'Leary (v2.8+)
   - `ArduinoJson` by Benoit Blanchon (v6.x)
   - `DHT sensor library` by Adafruit
   - `Adafruit Unified Sensor`

4. Open `hardware/esp32/esp32_sensor_node.ino`

5. Edit these lines at the top:
   ```cpp
   const char* WIFI_SSID     = "YourActualWiFiName";
   const char* WIFI_PASSWORD = "YourActualPassword";
   const char* MQTT_BROKER   = "192.168.1.X";  // ← your PC's local IP
   const char* DEVICE_ID     = "esp32_node_01"; // ← unique per device!
   const char* LOCATION      = "kitchen";        // ← label this node
   ```

6. Find your PC's IP:
   - Windows: `ipconfig` → look for "IPv4 Address"
   - Linux/Mac: `hostname -I`

7. Select board: Tools → Board → ESP32 Arduino → **ESP32 Dev Module**

8. Select port: Tools → Port → (your COM port e.g. COM5)

9. Click **Upload**

10. Open Serial Monitor (115200 baud) — you should see:
    ```
    Connecting to WiFi: YourWiFi......
    ✓ WiFi connected! IP: 192.168.1.42
    ✓ MQTT connected!
    [esp32_node_01] Temp=24.50°C  Hum=58.00%  RSSI=-52dBm
    ```

11. **Device appears on dashboard automatically! ✅**

---

## Arduino Setup (No WiFi — Uses Pi Bridge)

### Hardware
| Component | Cost |
|-----------|------|
| Arduino Uno/Nano/Mega | ~$5-20 |
| DHT22 sensor | ~$2 |
| USB cable | included |

### Wiring
```
DHT22 VCC  → Arduino 5V
DHT22 DATA → Arduino Digital Pin 2 (with 10kΩ pull-up to 5V)
DHT22 GND  → Arduino GND
```

### Software Setup
1. Flash `hardware/arduino/arduino_sensor.ino` via Arduino IDE
   - Change `DEVICE_ID` and `LOCATION` at the top
   - Select your Arduino board and port → Upload

2. Connect Arduino USB to Raspberry Pi

3. On Raspberry Pi:
   ```bash
   pip3 install paho-mqtt pyserial
   
   # Find the Arduino port:
   ls /dev/tty*
   # Usually /dev/ttyUSB0 or /dev/ttyACM0
   
   # Run the bridge:
   python3 hardware/raspberry_pi/pi_serial_bridge.py \
       --port /dev/ttyUSB0 \
       --broker 192.168.1.100  # ← your PC's IP
   ```

---

## Raspberry Pi (Native MQTT)

The Pi can run the full distributed AI node script directly:

```bash
# On Raspberry Pi
pip3 install paho-mqtt numpy

# Run as a self-healing AI edge node:
python3 examples/distributed_edge_node.py \
    --id rpi_node_01 \
    --broker 192.168.1.100 \
    --temp 25.0

# Or with real sensor (requires RPi.GPIO, Adafruit_DHT):
pip3 install Adafruit_DHT RPi.GPIO
python3 examples/distributed_edge_node.py \
    --id rpi_node_01 \
    --broker 192.168.1.100 \
    --real-sensor  # reads from GPIO4
```

---

## How Self-Healing Works on Real Hardware

### Detection → Command Flow

```
ESP32 sends: temp=85.5°C  (way too hot)
     ↓
Backend AI: Z-score = 8.7 → ANOMALY
     ↓
Consensus: neighbors average 25°C, deviation = 60.5 → FAULT CONFIRMED
     ↓
Trust score update: T_new = 0.7 × T_old + 0.3 × 0.0 = low trust
     ↓
Healing decision: "sensor_drift" → send "recalibrate" command
     ↓
MQTT publish: iot/commands/esp32_node_01/recalibrate
     ↓
ESP32 receives: blinks LED × 3, re-reads sensor, sends new baseline
     ↓
Dashboard shows: healing event logged, trust score recovers
```

### Fault → Healing Command Table

| Fault Type      | Detected When                      | Command Sent        | Device Action              |
|-----------------|-------------------------------------|---------------------|----------------------------|
| sensor_drift    | Readings slowly climbing off-scale  | `recalibrate`       | Re-reads sensor baseline   |
| stuck_sensor    | Same value >10 readings in a row    | `reset`             | Hardware restart           |
| data_spike      | Single extreme Z-score (>5)         | `validate`          | Sends 5 rapid samples      |
| offline         | No heartbeat for 60 seconds         | `ping`              | Respond or show as offline |
| noise           | High variance, many anomalies       | `validate`          | Send burst of readings     |
| frozen          | No data at all, device unreachable  | `reset`             | Force restart              |

---

## Multiple Devices Setup

You can connect as many devices as you want:

```
esp32_node_01  — Kitchen (DHT22)
esp32_node_02  — Bedroom (DHT22)
esp32_node_03  — Garage (DHT22 + MQ135 gas sensor)
arduino_node_01 — Roof (via Pi bridge)
rpi_node_01     — Living Room (native Pi)
```

Each just needs a **unique DEVICE_ID** in its firmware.

---

## Troubleshooting

### ESP32 won't connect to MQTT
```bash
# Test broker is reachable from ESP32's network:
# On PC run:
mosquitto_pub -h localhost -t "test" -m "hello"
mosquitto_sub -h localhost -t "test"

# Check firewall allows port 1883:
# Windows: Windows Defender Firewall → Allow port 1883 (TCP)
```

### Arduino serial bridge not finding port
```bash
# Linux: add yourself to dialout group
sudo usermod -aG dialout $USER
# Then log out and back in

# Try both:
ls /dev/ttyUSB*   # FTDI chips
ls /dev/ttyACM*   # ATmega chips (Uno, Mega)
```

### Device not appearing on dashboard
- Check MQTT broker is running: `mosquitto -v`
- Check backend is running: open http://localhost:8000/docs
- Manually check MQTT traffic:
  ```bash
  mosquitto_sub -h localhost -t "iot/#" -v
  ```
  You should see heartbeat and telemetry messages

### Checking API directly
```bash
# See all discovered hardware devices:
curl http://localhost:8000/api/hardware/devices

# Send a ping to esp32_node_01:
curl -X POST http://localhost:8000/api/hardware/ping/esp32_node_01

# Trigger AI healing:
curl -X POST http://localhost:8000/api/hardware/heal/esp32_node_01 \
  -H "Content-Type: application/json" \
  -d '{"fault_type": "sensor_drift", "device_type": "esp32"}'
```

---

## Files Reference

```
hardware/
├── esp32/
│   └── esp32_sensor_node.ino      ← Flash to ESP32
├── arduino/
│   └── arduino_sensor.ino         ← Flash to Arduino
└── raspberry_pi/
    └── pi_serial_bridge.py        ← Run on Pi to bridge Arduino

src/
├── mqtt/
│   └── device_discovery.py        ← Auto-discovers devices from MQTT
├── healing/
│   └── hardware_commands.py       ← Sends healing commands to hardware
└── backend/api/
    └── hardware.py                ← REST API for hardware management

dashboard_hardware.py              ← Browser UI for hardware devices
```
