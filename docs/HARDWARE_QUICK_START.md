# Quick Hardware Setup Guide

## 🎯 Goal
Connect real IoT hardware (ESP32 or Raspberry Pi) to the Self-Healing IoT System.

## 📋 What You Need

### For ESP32 Setup
- ESP32 development board ($5-10)
- DHT22 temperature/humidity sensor ($3-5)
- 3 jumper wires
- Micro USB cable
- Arduino IDE installed

### For Raspberry Pi Setup
- Raspberry Pi (any model with WiFi)
- DHT22 sensor (optional - works with simulated data too)
- 3 jumper wires (if using sensor)
- Python 3 installed

## 🔌 Wiring (DHT22 Sensor)

```
DHT22          ESP32/Pi
------         --------
Pin 1 (VCC) -> 3.3V
Pin 2 (Data)-> GPIO 4
Pin 4 (GND) -> GND
```

## 🚀 Quick Start

### Step 1: Start the Backend System

```bash
# Terminal 1: Start MQTT broker
mosquitto -v

# Terminal 2: Initialize database
python scripts/setup_db.py

# Terminal 3: Start backend API
python -m src.backend.main
```

### Step 2: Register Your Device

```bash
curl -X POST http://localhost:8000/api/devices \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device_001",
    "device_name": "My ESP32 Node",
    "device_type": "esp32_sensor",
    "location": "Home Lab"
  }'
```

### Step 3: Flash Hardware Code

#### For ESP32:
1. Open Arduino IDE
2. Install libraries: `PubSubClient`, `DHT sensor library`, `ArduinoJson`
3. Copy code from `docs/HARDWARE_INTEGRATION.md`
4. Update WiFi credentials and MQTT broker IP
5. Flash to ESP32

#### For Raspberry Pi:
```bash
# Install dependencies
pip3 install paho-mqtt Adafruit_DHT

# Edit configuration
nano examples/raspberry_pi_client.py
# Change MQTT_BROKER to your PC's IP address

# Run
python3 examples/raspberry_pi_client.py
```

### Step 4: Verify Connection

```bash
# Monitor MQTT messages
mosquitto_sub -h localhost -t "iot/#" -v

# Check device status
curl http://localhost:8000/api/devices/device_001

# View telemetry
curl http://localhost:8000/api/telemetry/device_001
```

## 📊 What Happens Next

The system will automatically:
1. ✅ Receive telemetry data every 10 seconds
2. ✅ Track device heartbeats every 30 seconds  
3. ✅ Detect anomalies using ML
4. ✅ Trigger healing actions when needed
5. ✅ Log everything to database

## 🧪 Test Healing

Inject a fault manually:
```bash
# Simulate sensor stuck at high value
# (modify your device code to send constant value)

# Watch the system detect anomaly and trigger healing
# Check healing logs:
curl http://localhost:8000/api/healing/logs
```

## 🔍 Troubleshooting

**Device not connecting?**
- Check WiFi credentials
- Verify MQTT broker IP (use `ipconfig` or `ifconfig`)
- Ensure broker is running

**No data appearing?**
- Monitor MQTT: `mosquitto_sub -h localhost -t "#" -v`
- Check device serial output
- Verify JSON format

**Commands not working?**
- Ensure device subscribes to `iot/commands/{device_id}/#`
- Check command handler in device code

## 📚 Full Documentation

- **Hardware Integration**: `docs/HARDWARE_INTEGRATION.md`
- **ESP32 Code**: In hardware integration doc
- **Raspberry Pi Code**: `examples/raspberry_pi_client.py`
- **API Documentation**: http://localhost:8000/docs

## 💡 Tips

1. **Start simple**: Use simulated data first (Raspberry Pi example works without sensor)
2. **Monitor MQTT**: Always keep `mosquitto_sub` running to see messages
3. **Check logs**: Backend logs show anomaly detection and healing actions
4. **Use API docs**: Interactive API at http://localhost:8000/docs

## 🎓 Next Steps

1. Get hardware working with simulated data
2. Connect real sensors
3. Test fault injection
4. Observe autonomous healing
5. Build dashboard for visualization

Happy building! 🚀
