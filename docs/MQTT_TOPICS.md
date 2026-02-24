# MQTT Topic Structure

## Overview
This document describes the MQTT topic hierarchy used in the Self-Healing IoT System.

## Topic Convention
- All topics use lowercase
- Topics follow pattern: `domain/category/device_id/subcategory`
- QoS levels are defined per topic category
- Wildcards: `+` for single level, `#` for multi-level

## Topic Categories

### 1. Telemetry Topics (`iot/telemetry/`)
**Purpose**: Device sensor data publishing

**Topics**:
- `iot/telemetry/{device_id}/temperature` - Temperature readings
- `iot/telemetry/{device_id}/humidity` - Humidity readings
- `iot/telemetry/{device_id}/light` - Light sensor readings
- `iot/telemetry/{device_id}/gas` - Gas sensor readings
- `iot/telemetry/{device_id}/all` - Combined sensor data

**Message Format**:
```json
{
  "device_id": "esp32_001",
  "sensor_type": "temperature",
  "value": 25.5,
  "unit": "°C",
  "timestamp": "2026-02-06T10:30:00Z"
}
```

**QoS**: 1 (At least once)
**Retain**: false

---

### 2. Health Topics (`iot/health/`)
**Purpose**: Device health and heartbeat monitoring

**Topics**:
- `iot/health/{device_id}/heartbeat` - Regular heartbeat signal
- `iot/health/{device_id}/status` - Device status updates
- `iot/health/{device_id}/battery` - Battery level (if applicable)

**Heartbeat Format**:
```json
{
  "device_id": "esp32_001",
  "status": "online",
  "uptime": 3600,
  "timestamp": "2026-02-06T10:30:00Z"
}
```

**QoS**: 1 (At least once)
**Retain**: true (last heartbeat should be retained)

---

### 3. Alert Topics (`iot/alerts/`)
**Purpose**: Anomaly and fault notifications

**Topics**:
- `iot/alerts/{device_id}/anomaly` - ML-detected anomalies
- `iot/alerts/{device_id}/fault` - Hardware/sensor faults
- `iot/alerts/{device_id}/offline` - Device offline alerts

**Alert Format**:
```json
{
  "device_id": "esp32_001",
  "alert_type": "anomaly",
  "severity": "high",
  "description": "Temperature reading out of expected range",
  "timestamp": "2026-02-06T10:30:00Z"
}
```

**QoS**: 2 (Exactly once - critical alerts)
**Retain**: false

---

### 4. Command Topics (`iot/commands/`)
**Purpose**: Send healing commands from backend to devices

**Topics**:
- `iot/commands/{device_id}/reset` - Reset device/sensor
- `iot/commands/{device_id}/switch_sensor` - Switch to backup sensor
- `iot/commands/{device_id}/restart` - Restart device
- `iot/commands/{device_id}/isolate` - Isolate device from network
- `iot/commands/{device_id}/configure` - Configuration updates

**Command Format**:
```json
{
  "command_id": "cmd_12345",
  "device_id": "esp32_001",
  "action": "switch_sensor",
  "parameters": {
    "sensor_type": "backup"
  },
  "timestamp": "2026-02-06T10:30:00Z"
}
```

**Response Topic**: `iot/commands/{device_id}/response`

**Response Format**:
```json
{
  "command_id": "cmd_12345",
  "device_id": "esp32_001",
  "status": "success",
  "message": "Switched to backup sensor",
  "timestamp": "2026-02-06T10:30:05Z"
}
```

**QoS**: 2 (Exactly once - critical commands)
**Retain**: false

---

### 5. System Topics (`iot/system/`)
**Purpose**: System-wide management and discovery

**Topics**:
- `iot/system/discovery` - Device discovery broadcasts
- `iot/system/registration` - New device registration
- `iot/system/logs` - System-level logging

**QoS**: 1 (At least once)
**Retain**: true (for discovery and registration)

---

## Subscription Patterns

### Backend Server Subscriptions
```python
# Subscribe to all telemetry
iot/telemetry/+/+

# Subscribe to all health updates
iot/health/+/+

# Subscribe to all alerts
iot/alerts/+/+

# Subscribe to command responses
iot/commands/+/response
```

### Device Subscriptions
```python
# Subscribe to own commands
iot/commands/{device_id}/#

# Subscribe to system broadcasts
iot/system/#
```

---

## Best Practices

1. **Always include device_id** in message payload for validation
2. **Include timestamp** in all messages
3. **Use appropriate QoS** based on message criticality
4. **Validate message format** before processing
5. **Handle retained messages** properly on reconnection
6. **Implement timeout handling** for commands
7. **Log all command executions** for debugging

---

## Integration with Hardware

When integrating ESP32 devices:

1. Device publishes to telemetry topics at regular intervals (e.g., every 5 seconds)
2. Device publishes heartbeat every 10 seconds
3. Device subscribes to its command topic on startup
4. Device sends acknowledgment for every command received
5. Device implements graceful handling of network disconnections

---

## Testing MQTT Topics

Use mosquitto clients for testing:

```bash
# Subscribe to all topics (monitoring)
mosquitto_sub -h localhost -t "iot/#" -v

# Publish test telemetry
mosquitto_pub -h localhost -t "iot/telemetry/esp32_001/temperature" -m '{"value": 25.5}'

# Publish test command
mosquitto_pub -h localhost -t "iot/commands/esp32_001/reset" -m '{"action": "reset"}'
```
