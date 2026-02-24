# AI-Enabled Self-Healing IoT System - Complete Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Core Concepts](#core-concepts)
4. [AI Anomaly Detection](#ai-anomaly-detection)
5. [Self-Healing System](#self-healing-system)
6. [Technology Stack](#technology-stack)
7. [System Components](#system-components)
8. [Data Flow](#data-flow)
9. [MQTT Communication](#mqtt-communication)
10. [Database Schema](#database-schema)
11. [API Endpoints](#api-endpoints)
12. [Configuration & Policies](#configuration--policies)
13. [Working Example Scenarios](#working-example-scenarios)
14. [Getting Started](#getting-started)

---

## Project Overview

The **AI-Enabled Self-Healing IoT System** is an intelligent platform that autonomously:
- **Detects** hardware and sensor faults in IoT devices using Machine Learning
- **Analyzes** anomalous sensor data in real-time
- **Decides** on appropriate healing actions based on configurable policies
- **Executes** automated recovery procedures without human intervention
- **Monitors** system health and validates healing success

### Key Features
✨ **Real-time Anomaly Detection** - Uses Isolation Forest ML algorithm
🔄 **Autonomous Self-Healing** - Automatically fixes detected issues
📊 **Live Dashboard** - Real-time monitoring and visualization
🌐 **MQTT-Based** - Scalable, distributed communication
💾 **Persistent Logging** - Complete audit trail of all actions
🔌 **Hardware Integration** - Supports ESP32, Arduino, Raspberry Pi
📈 **Policy-Driven** - Configurable healing strategies via YAML

---

## Architecture

### Layered Architecture

```
┌─────────────────────────────┐
│  APPLICATION LAYER          │
│  (Streamlit Dashboard)      │
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│  DECISION LAYER             │
│  (Healing Orchestrator)     │
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│  INTELLIGENCE LAYER         │
│  (Anomaly Detector - ML)    │
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│  PLATFORM LAYER             │
│  (FastAPI Backend)          │
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│  COMMUNICATION LAYER        │
│  (MQTT Broker)              │
└────────────┬────────────────┘
             │
┌────────────▼────────────────┐
│  PERCEPTION LAYER           │
│  (IoT Devices & Sensors)    │
└─────────────────────────────┘
```

### Component Architecture

```
IoT Devices (ESP32/Arduino/Pi)
    ↓ (MQTT Publish)
MQTT Broker (Mosquitto)
    ↓ (Subscribe)
FastAPI Backend
    ├─→ Database (SQLite)
    ├─→ Anomaly Detector (ML)
    ├─→ Healing Orchestrator
    └─→ API Endpoints
    ↓
Streamlit Dashboard
```

---

## Core Concepts

### 1. **Device**
An IoT device is a physical or virtual unit with:
- Unique device_id
- Multiple sensors
- Online/offline status
- Health metrics

### 2. **Sensor**
Measurement device that produces:
- Sensor readings (temperature, humidity, etc.)
- Timestamps
- Quality metrics

### 3. **Anomaly**
An unusual sensor reading detected by ML model that indicates:
- Potential hardware failure
- Sensor drift
- Communication issues
- Out-of-range values

### 4. **Fault**
A diagnosed problem that requires healing:
- Sensor Anomaly
- Device Offline
- Sensor Drift
- Communication Failure

### 5. **Healing Action**
Automated recovery procedure:
- Validate Reading
- Switch to Backup Sensor
- Reset Sensor
- Restart Device
- Isolate Device
- Calibrate Sensor
- Reconnect MQTT
- Ping Device

### 6. **Policy**
Rules that define how to heal specific faults:
- Priority of actions
- Conditions for execution
- Timeout values
- Cooldown periods

---

## AI Anomaly Detection

### Detection Algorithm: Isolation Forest

The system uses **Isolation Forest**, an unsupervised machine learning algorithm ideal for anomaly detection.

#### How Isolation Forest Works

1. **Isolation Principle**
   - Anomalies are "few and different"
   - Normal points require more splits to isolate
   - Anomalies need fewer splits

2. **Tree Building Process**
   ```
   For each tree in forest:
     1. Randomly select a feature
     2. Randomly select a split value
     3. Recursively partition data
     4. Build decision tree
   ```

3. **Scoring Process**
   ```
   anomaly_score = average_path_length_to_isolate_point
   
   Score close to 1 → Likely anomaly
   Score close to 0 → Normal data
   ```

#### Advantages for IoT

- ✅ Works with unlabeled data
- ✅ Efficient (linear time complexity)
- ✅ Handles high-dimensional data
- ✅ Robust to outliers
- ✅ No normal/abnormal training needed
- ✅ Low false positive rate

### Detection Process

```python
# 1. Initialize detector for each sensor
detector = AnomalyDetector(
    sensor_type=SensorType.TEMPERATURE,
    window_size=50,          # samples for training
    contamination=0.1        # expect 10% anomalies
)

# 2. Collect training samples (50 readings)
for reading in device.get_historical_data():
    detector.add_sample(reading)

# 3. Train model
detector.train()

# 4. Detect anomalies in real-time
is_anomaly, score = detector.predict(new_reading)

if score > 0.7:  # threshold
    report_anomaly(device_id, reading, score)
```

### Anomaly Types Detected

| Type | Detection Method | Severity |
|------|------------------|----------|
| **Sensor Fault** | Isolation Forest score > 0.7 | MEDIUM |
| **Sensor Drift** | Gradual value shift over time | LOW |
| **Out of Range** | Value outside min/max bounds | MEDIUM |
| **Stuck Value** | Same reading for extended period | MEDIUM |
| **Sudden Spike** | Large unexpected change | HIGH |
| **Communication Error** | Missing heartbeat | HIGH |

### Example: Temperature Anomaly

```
Normal readings: 22°C, 22.5°C, 23°C, 22.8°C, ...
Anomaly detected: 95°C  ← Isolation Forest score: 0.95

Decision: Likely sensor fault
Healing: Validate reading → Switch to backup sensor → Reset sensor
```

---

## Self-Healing System

### Healing Workflow

```
┌──────────────────┐
│  DETECTION PHASE │  (AI Detects Anomaly)
└────────┬─────────┘
         │ Anomaly Data
         ▼
┌──────────────────┐
│  ANALYSIS PHASE  │  (Fault Type Identification)
└────────┬─────────┘
         │ Fault Type + Severity
         ▼
┌──────────────────┐
│  DECISION PHASE  │  (Action Selection)
└────────┬─────────┘
         │ Recommended Actions
         ▼
┌──────────────────┐
│ EXECUTION PHASE  │  (Send Commands via MQTT)
└────────┬─────────┘
         │ Command Results
         ▼
┌──────────────────┐
│VALIDATION PHASE  │  (Verify Healing Success)
└────────┬─────────┘
         │ Success/Failure Status
         ▼
┌──────────────────┐
│  LOGGING PHASE   │  (Record Actions)
└──────────────────┘
```

### Healing Orchestrator

The **Healing Orchestrator** is the main coordinator:

```python
class HealingOrchestrator:
    
    async def monitor_anomalies(self):
        # Continuously watch for new anomalies
        # Check cooldown periods
        # Trigger healing for active anomalies
    
    async def execute_healing(self, device_id, anomaly):
        # 1. Get fault type from anomaly
        # 2. Load healing policy
        # 3. Select actions based on conditions
        # 4. Execute actions sequentially
        # 5. Validate results
        # 6. Log outcomes
```

### Decision Engine

The **Decision Engine** analyzes anomalies and recommends actions:

```python
class DecisionEngine:
    
    def analyze_anomaly(self, device_id, anomaly_type, score):
        # 1. Map anomaly to fault type
        #    SENSOR_FAULT → 'sensor_anomaly'
        #    DEVICE_OFFLINE → 'device_offline'
        #    SENSOR_DRIFT → 'sensor_drift'
        
        # 2. Retrieve policy for fault type
        policy = self.policies.get_policy(fault_type)
        
        # 3. Determine severity
        severity = policy['severity']  # low/medium/high/critical
        
        # 4. Select applicable actions
        actions = policy['actions']   # List of healing actions
        
        return fault_type, severity, actions
```

### Action Executor

The **Action Executor** performs healing actions via MQTT:

```python
class ActionExecutor:
    
    async def execute_action(self, device_id, action, timeout=30):
        # 1. Create command payload
        command = {
            "command_id": generate_id(),
            "device_id": device_id,
            "action": action.value,
            "parameters": get_action_parameters(action),
            "timestamp": now()
        }
        
        # 2. Publish command via MQTT
        mqtt_client.publish(
            topic=f"iot/commands/{device_id}/reset",
            payload=json.dumps(command),
            qos=2  # Exactly once delivery
        )
        
        # 3. Wait for response (with timeout)
        response = await self.wait_for_response(command_id, timeout)
        
        # 4. Return status: success/failed/timeout
        return response
```

### Healing Policies (YAML)

Policies define healing strategies:

```yaml
policies:
  sensor_anomaly:
    description: "Abnormal sensor reading detected"
    severity: "medium"
    actions:
      - action: "validate_reading"
        priority: 1
        timeout: 5
      - action: "switch_to_backup_sensor"
        priority: 2
        timeout: 10
        conditions:
          - backup_sensor_available: true
      - action: "reset_sensor"
        priority: 3
        timeout: 15
    max_attempts: 3
    cooldown: 60

  device_offline:
    description: "Device heartbeat timeout"
    severity: "high"
    actions:
      - action: "ping_device"
        priority: 1
        timeout: 10
      - action: "restart_device"
        priority: 2
        timeout: 30
    max_attempts: 3
    cooldown: 120
```

### Cooldown & Retry Logic

Prevents heal flooding:

```
1. Anomaly detected → Start healing
2. Healing executed → Set cooldown timer (e.g., 60 seconds)
3. Skip healing for device during cooldown period
4. After cooldown expires → Ready for next healing cycle
5. Max attempts reached → Isolate device
```

---

## Technology Stack

### Backend
- **Framework**: FastAPI (async Python)
- **Server**: Uvicorn (ASGI)
- **Validation**: Pydantic
- **Database**: SQLite with aiosqlite (async)

### Machine Learning
- **Algorithm**: Scikit-learn (Isolation Forest)
- **Data Processing**: NumPy, Pandas, SciPy

### Communication
- **Protocol**: MQTT (Mosquitto broker)
- **Client**: paho-mqtt
- **QoS Levels**: 1 (at least once), 2 (exactly once)

### Visualization
- **Dashboard**: Streamlit
- **Charts**: Plotly
- **Real-time**: stream auto-refresh

### Infrastructure
- **Configuration**: Python-dotenv, PyYAML
- **Logging**: Loguru (structured logging)
- **Testing**: Pytest, pytest-asyncio
- **Code Quality**: Black, Flake8, MyPy

### Deployment
- **OS Support**: Windows, Linux, macOS
- **Python**: 3.9+
- **Hardware**: ESP32, Arduino, Raspberry Pi

---

## System Components

### 1. **Backend Server** (`src/backend/main.py`)

FastAPI application with:
- ✅ Device management endpoints
- ✅ Telemetry data endpoints
- ✅ Anomaly query endpoints
- ✅ Healing action endpoints
- ✅ System health endpoint
- ✅ Auto-generated API docs

```python
# Start backend
python -m src.backend.main

# Access API
http://localhost:8000/docs  # Interactive documentation
http://localhost:8000/api/health/  # System status
```

### 2. **MQTT Client** (`src/mqtt/client.py`)

Handles device communication:
- 🔗 Connection management with auto-reconnect
- 📨 Subscribe to device telemetry
- 📤 Publish healing commands
- 🔄 Message routing
- 🔐 QoS level enforcement

```python
# Topics subscribed
iot/telemetry/+/+          # All sensor data
iot/health/+/heartbeat     # Device heartbeats
iot/alerts/+/+             # Device alerts
iot/commands/+/response    # Command responses
```

### 3. **Database Manager** (`src/database/db_manager.py`)

SQLite database with:
- 📋 Devices table (active devices)
- 📊 Telemetry table (sensor readings)
- ⚠️ Anomalies table (detected issues)
- 🔧 Healing logs table (action history)
- 👥 Indexed queries for performance

```python
# Database schema
- devices: id, device_id, status, last_seen, type
- telemetry: id, device_id, sensor_type, value, timestamp
- anomalies: id, device_id, type, score, status, timestamp
- healing_logs: id, device_id, action, status, timestamp
```

### 4. **Anomaly Detector** (`src/ai/anomaly_detector.py`)

Per-sensor ML detector:
- 🤖 Isolation Forest model per sensor type
- 📈 Real-time anomaly scoring
- 🎯 Adaptive thresholds
- 💾 Model persistence (pickle format)
- 🔄 Automatic retraining

```python
# Usage
detector = AnomalyDetector(SensorType.TEMPERATURE)
detector.add_sample(25.5)
is_anomaly, score = detector.predict(35.0)

if score > 0.7:
    trigger_alert(device_id, "Likely sensor fault")
```

### 5. **Healing Orchestrator** (`src/healing/orchestrator.py`)

Main healing coordinator:
- 👁️ Monitors for new anomalies
- 🔍 Checks cooldown periods
- ⚡ Triggers healing workflows
- ✅ Validates healing success
- 📊 Records all actions

```python
# Running in background
orchestrator = HealingOrchestrator()
await orchestrator.start()  # Runs indefinitely

# Monitors:
- Active anomalies every 5 seconds
- Pending actions every 10 seconds
```

### 6. **Decision Engine** (`src/healing/decision_engine.py`)

Fault analysis and action selection:
- 📋 Maps anomalies to fault types
- 🔍 Retrieves healing policies
- 🎯 Selects applicable actions
- 🔗 Checks action conditions
- 📈 Prioritizes by severity

### 7. **Action Executor** (`src/healing/actions.py`)

Executes healing commands:
- 📤 Publishes MQTT commands
- ⏱️ Enforces timeouts
- 📝 Records execution status
- 🔄 Handles retries
- ✅ Validates responses

### 8. **Dashboard** (`src/dashboard/app.py`)

Streamlit visualization:
- 📊 Real-time device status
- 📈 Sensor data trends
- ⚠️ Active anomalies
- 🔧 Healing action history
- 🟢 System health indicator

```
Dashboard Pages:
├── Home (Status Overview)
├── Devices (Device List & Details)
├── Anomalies (Active Issues)
├── Healing (Action History)
└── Analytics (Trends & Stats)
```

---

## Data Flow

### Complete Healing Workflow Example

```
1. IoT DEVICE PUBLISHES TEMPERATURE
   Device: esp32_001
   Sensor: temperature
   Value: 95°C (abnormal!)
   Topic: iot/telemetry/esp32_001/temperature
   
   ↓ MQTT
   
2. BACKEND RECEIVES DATA
   - Stores in telemetry table
   - Extracts value: 95.0
   
   ↓
   
3. ANOMALY DETECTOR ANALYZES
   - Compares against historical data
   - Isolation Forest score: 0.92 (high anomaly)
   - Threshold: 0.7
   - Decision: ANOMALOUS
   
   ↓
   
4. ANOMALY RECORDED
   - Table: anomalies
   - Fields: device_id, type, score, severity, status
   - Status: "active"
   
   ↓
   
5. HEALING ORCHESTRATOR DETECTS
   - Polls anomalies every 5 seconds
   - Finds: esp32_001 active anomaly
   - Checks: Not in cooldown
   - Action: Start healing
   
   ↓
   
6. DECISION ENGINE ANALYZES
   - Anomaly type: SENSOR_FAULT
   - Maps to: sensor_anomaly fault
   - Loads policy: sensor_anomaly
   - Severity: MEDIUM
   - Recommended actions:
     1. validate_reading (priority 1)
     2. switch_to_backup_sensor (priority 2)
     3. reset_sensor (priority 3)
   
   ↓
   
7. ACTION EXECUTOR EXECUTES
   
   Action 1: validate_reading
   - Command: Read sensor 5 times
   - Send: iot/commands/esp32_001/validate
   - Wait: 5 seconds
   - Response: Confirmed anomalous
   
   Action 2: switch_to_backup_sensor
   - Check condition: backup available? YES
   - Command: Switch to backup
   - Send: iot/commands/esp32_001/switch_sensor
   - Wait: 10 seconds
   - Response: Switched successfully
   
   ↓
   
8. HEALING LOG RECORDED
   - Device: esp32_001
   - Anomaly: sensor_fault
   - Action: switch_to_backup_sensor
   - Status: SUCCESS
   - Duration: 12 seconds
   - Timestamp: 2026-02-24 10:30:45
   
   ↓
   
9. ANOMALY STATUS UPDATED
   - Old status: active
   - New status: resolved
   - Resolved by: healing action
   
   ↓
   
10. COOLDOWN SET
    - Device: esp32_001
    - Cooldown duration: 60 seconds
    - Can't heal again until: 10:31:45
    
   ↓
   
11. DASHBOARD UPDATES
    - Removes from "Active Anomalies"
    - Updates "Healing History"
    - Shows "esp32_001: ONLINE"
    - Status badge: 🟢 HEALTHY
```

### Real-time Data Processing Pipeline

```
Sensor Reading
    ↓
MQTT Publish (Device)
    ↓ (Subscribe)
MQTT Broker
    ↓ (Process)
Backend API
    ├─→ Store Telemetry (Database)
    ├─→ Anomaly Detection (ML)
    │   ├─→ Is Anomaly? YES
    │   └─→ Store Anomaly (Database)
    └─→ Healing Orchestrator (Background)
        ├─→ Decision Engine (Policy)
        ├─→ Action Executor (MQTT)
        └─→ Log Healing (Database)
    ↓
Dashboard (Real-time Update)
    └─→ User Notification
```

---

## MQTT Communication

### Topic Hierarchy

```
iot/
├── telemetry/          (Sensor readings)
│   ├── {device_id}/
│   │   ├── temperature
│   │   ├── humidity
│   │   ├── light
│   │   └── gas
│   └── {device_id}/all
│
├── health/             (Device health)
│   └── {device_id}/
│       ├── heartbeat
│       ├── status
│       └── battery
│
├── alerts/             (Anomalies)
│   └── {device_id}/
│       ├── anomaly
│       ├── fault
│       └── offline
│
├── commands/           (Healing commands)
│   └── {device_id}/
│       ├── reset
│       ├── switch_sensor
│       ├── restart
│       ├── isolate
│       ├── configure
│       └── response
│
└── system/             (System management)
    ├── discovery
    ├── registration
    └── logs
```

### Message Formats

#### Telemetry Message
```json
{
  "device_id": "esp32_001",
  "sensor_type": "temperature",
  "value": 25.5,
  "unit": "°C",
  "timestamp": "2026-02-24T10:30:00Z"
}
```

#### Heartbeat Message
```json
{
  "device_id": "esp32_001",
  "status": "online",
  "uptime": 3600,
  "timestamp": "2026-02-24T10:30:00Z"
}
```

#### Alert Message
```json
{
  "device_id": "esp32_001",
  "alert_type": "anomaly",
  "severity": "high",
  "description": "Temperature reading abnormal (95°C)",
  "timestamp": "2026-02-24T10:30:00Z"
}
```

#### Command Message
```json
{
  "command_id": "cmd_12345",
  "device_id": "esp32_001",
  "action": "switch_sensor",
  "parameters": {
    "sensor_type": "backup"
  },
  "timestamp": "2026-02-24T10:30:00Z"
}
```

#### Command Response
```json
{
  "command_id": "cmd_12345",
  "device_id": "esp32_001",
  "status": "success",
  "message": "Switched to backup sensor",
  "timestamp": "2026-02-24T10:30:05Z"
}
```

### QoS Levels

| Topic Type | QoS | Reason |
|-----------|-----|--------|
| Telemetry | 1 | At least once delivery needed |
| Health | 1 | Heartbeats important for timeout detection |
| Alerts | 2 | Critical alerts need exact once delivery |
| Commands | 2 | Healing commands must execute exactly once |
| Responses | 2 | Must confirm command execution |

---

## Database Schema

### Tables

#### Devices
```sql
CREATE TABLE devices (
    id INTEGER PRIMARY KEY,
    device_id TEXT UNIQUE,      -- "esp32_001"
    status TEXT,                 -- online, offline, healing, isolated
    type TEXT,                   -- sensor_node, gateway, hub
    last_seen TIMESTAMP,         -- Last heartbeat time
    created_at TIMESTAMP
);
```

#### Telemetry
```sql
CREATE TABLE telemetry (
    id INTEGER PRIMARY KEY,
    device_id TEXT,
    sensor_type TEXT,            -- temperature, humidity, light, gas
    value REAL,
    unit TEXT,
    timestamp TIMESTAMP,
    created_at TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);
-- Index on: device_id, timestamp for fast queries
```

#### Anomalies
```sql
CREATE TABLE anomalies (
    id INTEGER PRIMARY KEY,
    device_id TEXT,
    anomaly_type TEXT,           -- sensor_fault, drift, out_of_range
    anomaly_score REAL,          -- 0.0 to 1.0
    severity TEXT,               -- low, medium, high, critical
    status TEXT,                 -- active, resolved, ignored
    details JSON,                -- Additional metadata
    detected_at TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);
-- Index on: device_id, status for quick filtering
```

#### Healing Logs
```sql
CREATE TABLE healing_logs (
    id INTEGER PRIMARY KEY,
    device_id TEXT,
    anomaly_id INTEGER,
    action TEXT,                 -- validate_reading, reset, restart
    status TEXT,                 -- pending, in_progress, success, failed
    duration_ms INTEGER,         -- Execution time
    result_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id),
    FOREIGN KEY (anomaly_id) REFERENCES anomalies(id)
);
```

### Useful Queries

```sql
-- Get active anomalies
SELECT * FROM anomalies 
WHERE status = 'active'
ORDER BY severity DESC, detected_at DESC;

-- Get device healing history
SELECT * FROM healing_logs
WHERE device_id = 'esp32_001'
ORDER BY started_at DESC
LIMIT 10;

-- Get today's anomalies by severity
SELECT severity, COUNT(*) as count
FROM anomalies
WHERE DATE(detected_at) = DATE('now')
GROUP BY severity;

-- Get offline devices
SELECT device_id, last_seen, 
  CAST((julianday('now') - julianday(last_seen)) * 24 AS INTEGER) as hours_offline
FROM devices
WHERE status = 'offline'
ORDER BY last_seen DESC;
```

---

## API Endpoints

### Base URL
```
http://localhost:8000
```

### Health Check
```
GET /api/health/

Response:
{
  "status": "healthy",
  "services": {
    "backend": "running",
    "mqtt": "connected",
    "database": "connected"
  }
}
```

### Devices Endpoints

```
GET     /api/devices                    List all devices
GET     /api/devices/{device_id}        Get device details
POST    /api/devices                    Register new device
PUT     /api/devices/{device_id}        Update device
DELETE  /api/devices/{device_id}        Remove device
GET     /api/devices/{device_id}/status Get device status
```

### Telemetry Endpoints

```
POST    /api/telemetry                  Create telemetry record
GET     /api/telemetry/{device_id}      Get device telemetry
GET     /api/telemetry/{device_id}/stats Get statistics
```

### Anomalies Endpoints

```
GET     /api/anomalies                           List anomalies
GET     /api/anomalies/{anomaly_id}             Get anomaly details
POST    /api/anomalies/{anomaly_id}/resolve     Mark as resolved
GET     /api/anomalies/device/{device_id}       Get device anomalies
GET     /api/anomalies/stats/summary           Get anomaly summary
GET     /api/anomalies/stats/timeline          Get timeline data
```

### Healing Endpoints

```
GET     /api/healing/logs                      Get healing action logs
GET     /api/healing/logs/{device_id}          Get device healing logs
GET     /api/healing/stats                     Get healing statistics
GET     /api/healing/active                    Get active workflows
POST    /api/healing/trigger/{device_id}       Manually trigger healing
GET     /api/healing/actions                   List available actions
```

---

## Configuration & Policies

### Environment Variables (`.env`)

```env
# MQTT Configuration
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=user
MQTT_PASSWORD=password

# Database
DATABASE_URL=sqlite:///data/iot_system.db

# AI/ML Settings
ANOMALY_WINDOW_SIZE=50
ANOMALY_CONTAMINATION=0.1
ANOMALY_THRESHOLD=0.7

# Healing Settings
HEALING_ENABLED=true
HEALING_TIMEOUT=30
HEALING_COOLDOWN=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/system.log
```

### Healing Policies (`config/healing_policies.yaml`)

Defines fault types and their healing strategies:

```yaml
policies:
  sensor_anomaly:
    description: "ML detected abnormal reading"
    severity: "medium"
    actions:
      - action: "validate_reading"
        priority: 1
        timeout: 5
      - action: "switch_to_backup_sensor"
        priority: 2
        timeout: 10
        conditions:
          - backup_sensor_available: true
      - action: "reset_sensor"
        priority: 3
        timeout: 15
    max_attempts: 3
    cooldown: 60

  device_offline:
    description: "Device not responding"
    severity: "high"
    actions:
      - action: "ping_device"
        priority: 1
        timeout: 10
      - action: "restart_device"
        priority: 2
        timeout: 30
      - action: "isolate_device"
        priority: 3
        timeout: 5
    max_attempts: 3
    cooldown: 120

  sensor_drift:
    description: "Gradual sensor drift detected"
    severity: "low"
    actions:
      - action: "calibrate_sensor"
        priority: 1
        timeout: 20
    max_attempts: 2
    cooldown: 300
```

### ML Model Configuration

```yaml
anomaly_detection:
  algorithm: "isolation_forest"
  window_size: 50              # Samples for training
  contamination: 0.1           # Expected % of anomalies
  threshold: 0.7               # Score threshold (0-1)
  n_estimators: 100            # Trees in forest
  random_state: 42             # Reproducibility
  
feature_engineering:
  enabled: true
  features:
    - raw_value
    - moving_average
    - rate_of_change
    - autocorrelation
```

---

## Working Example Scenarios

### Scenario 1: Temperature Sensor Fault

**Situation**: Temperature sensor starts producing erratic readings

**Timeline**:
```
10:00:00 - Sensor reads 22.5°C (normal)
10:00:05 - Sensor reads 22.6°C (normal)
10:00:10 - Sensor reads 22.4°C (normal)
...
10:05:00 - Sensor reads 95.5°C (ANOMALY!)
          Normal range: -10 to 50°C
          Isolation Forest score: 0.95

10:05:01 - DETECTION
          Anomaly stored in database
          Healing Orchestrator notified

10:05:02 - ANALYSIS
          Decision Engine runs
          Fault type: sensor_anomaly
          Severity: MEDIUM

10:05:03 - DECISION
          Policy retrieved for sensor_anomaly
          Actions selected:
          1. validate_reading (confirm anomaly)
          2. switch_to_backup_sensor (if available)
          3. reset_sensor (if still faulty)

10:05:04 - EXECUTION
          Action 1: validate_reading
          → Command: Read 5 times
          → Result: 2/5 reads > 80°C → Confirmed anomaly

10:05:08 - Action 2: switch_to_backup_sensor
          → Command: Switch active sensor
          → Result: Success

10:05:15 - VALIDATION
          New readings from backup sensor: 22.8°C (normal)
          Healing marked as SUCCESS

10:05:16 - COOLDOWN
          Device cooldown window: 60 seconds
          Next healing allowed: 10:06:16

10:05:20 - LOGGING
          Healing action recorded
          Anomaly status: RESOLVED
          Dashboard updated
```

### Scenario 2: Device Offline Detection

**Situation**: IoT device loses connectivity

**Timeline**:
```
Expected heartbeat interval: 10 seconds
Timeout threshold: 30 seconds (3 missed heartbeats)

10:00:00 - Heartbeat received from esp32_002 ✓
10:00:10 - Heartbeat received ✓
10:00:20 - Heartbeat received ✓
10:00:30 - No heartbeat (1st miss)
10:00:40 - No heartbeat (2nd miss)
10:00:50 - No heartbeat (3rd miss) → ALERT!

10:00:51 - DETECTION
          Anomaly type: DEVICE_OFFLINE
          Severity: HIGH
          Healing Orchestrator triggered

10:00:52 - ANALYSIS & DECISION
          Fault type: device_offline
          Recommended actions:
          1. ping_device (check connectivity)
          2. restart_device (if no response)

10:00:53 - EXECUTION
          Action 1: Ping Device
          → Command: iot/commands/esp32_002/ping
          → Timeout: 10 seconds
          → Result: NO RESPONSE

10:01:03 - Action 2: Restart Device
          → Command: iot/commands/esp32_002/restart
          → Timeout: 30 seconds
          → Result: ???

10:01:25 - If restart succeeds:
          → Heartbeat received! ✓
          → Device back online
          → Anomaly RESOLVED
          
          If restart fails:
          → Isolate device
          → Status: ISOLATED
          → Alert operator
```

### Scenario 3: Sensor Drift Detection

**Situation**: Sensor readings gradually drift from true values

**Timeline**:
```
Day 1:  Sensor: 25.0°C, True: 25.0°C (accurate)
Day 2:  Sensor: 26.2°C, True: 25.0°C (+1.2°C drift)
Day 3:  Sensor: 27.5°C, True: 25.0°C (+2.5°C drift)
Day 4:  Sensor: 28.8°C, True: 25.0°C (+3.8°C drift) ← Threshold!

Drift > 15% detected by Feature Engineering module

TIME BASED ON DAY 4:
- Drift detection algorithm identifies pattern
- Severity: LOW (gradual, not critical)
- Recommended action: Calibrate

HEALING ACTION:
- Send calibration command
- Sensor recalibrates against baseline
- New readings: 25.0°C (correct again!)
- Preventive action successful
```

### Scenario 4: Multiple Sensors, Cascading Healing

**Situation**: One device has multiple failing sensors

**Timeline**:
```
Device: esp32_003 (has 4 sensors: temp, humidity, light, gas)

10:00:00 - Temperature anomaly detected
           PingOrchestrator: Start healing for temperature
           
10:00:30 - During temperature healing...
           Humidity anomaly also detected!
           
10:00:31 - Orchestrator checks: device already healing?
           YES → Temperature healing in progress
           
10:00:31 - Orchestrator decisions:
           Option A: Wait for temperature healing (queue)
           Option B: Skip humidity (cooldown prevents multiple heals)
           
           Implementation: QUEUE approach
           Temperature healing continues
           Humidity marked as "pending_healing"
           
10:01:00 - Temperature healing completes (SUCCESS)
           Cooldown timer starts: 60 seconds
           
10:01:30 - During cooldown...
           Light anomaly detected
           Status: Queued (waiting for cooldown)
           
10:02:00 - Cooldown expires
           Device can heal again
           
10:02:01 - Start humidity healing
           Switch to backup humidity sensor
           Result: SUCCESS
           
10:02:30 - Set cooldown timer again
           
10:03:30 - Cooldown expires
           Can heal light sensor next
```

---

## Getting Started

### Prerequisites

```bash
# System Requirements
- Python 3.9 or higher
- Mosquitto MQTT Broker
- 2GB RAM minimum
- Windows/Linux/macOS
```

### Installation Steps

#### 1. Clone and Setup Environment

```bash
cd d:\self-healing-iot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Configure Environment

```bash
# Create .env file (copy from example if exists)
cp .env.example .env

# Edit .env with your settings:
# MQTT_BROKER_HOST=localhost
# MQTT_BROKER_PORT=1883
# DATABASE_URL=sqlite:///data/iot_system.db
```

#### 4. Initialize Database

```bash
python scripts/setup_db.py
```

#### 5. Start MQTT Broker

```bash
# On Windows with Mosquitto installed:
mosquitto -c config/mosquitto.conf

# On Linux:
mosquitto -c config/mosquitto.conf

# Or use Docker:
docker run -it -p 1883:1883 eclipse-mosquitto
```

#### 6. Start Backend Server

**Terminal 1:**
```bash
cd d:\self-healing-iot
python -m src.backend.main
```

Expected output:
```
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Backend initialized
INFO: MQTT connected
INFO: Database initialized
```

#### 7. Start Dashboard

**Terminal 2:**
```bash
cd d:\self-healing-iot
streamlit run src/dashboard/app.py
```

Expected output:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

#### 8. Start Device Simulator (Optional)

**Terminal 3:**
```bash
cd d:\self-healing-iot
python src/simulator/device_simulator.py
```

### Verification

#### Check Backend Health

```bash
curl http://localhost:8000/api/health/
```

Expected:
```json
{
  "status": "healthy",
  "services": {
    "backend": "running",
    "mqtt": "connected",
    "database": "connected"
  }
}
```

#### Check API Docs

```
http://localhost:8000/docs
```

You should see interactive API documentation with all endpoints.

#### Check Dashboard

```
http://localhost:8501
```

You should see the Streamlit dashboard with:
- Device status
- Active anomalies
- Healing history
- System health

### Running Tests

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_anomaly_detector.py

# Run with coverage
pytest --cov=src

# Run integration tests
pytest tests/integration/
```

### Quick Start Script

```bash
# Windows only - all in one!
scripts\run_all.bat
```

This starts:
1. MQTT Broker ✓
2. Backend Server ✓
3. Device Simulator ✓
4. Dashboard ✓

---

## File Structure Overview

```
self-healing-iot/
├── src/
│   ├── backend/              # FastAPI application
│   │   ├── main.py           # Server entry point
│   │   ├── api/              # API endpoints
│   │   │   ├── devices.py
│   │   │   ├── telemetry.py
│   │   │   ├── anomalies.py
│   │   │   ├── healing.py
│   │   │   └── health.py
│   │   └── middleware/       # HTTP middleware
│   │
│   ├── ai/                   # Machine Learning
│   │   ├── anomaly_detector.py   # Isolation Forest
│   │   ├── feature_engineering.py # Feature extraction
│   │   ├── model_manager.py      # Model persistence
│   │   └── sensor_drift.py       # Drift detection
│   │
│   ├── healing/              # Self-Healing Engine
│   │   ├── orchestrator.py       # Main coordinator
│   │   ├── decision_engine.py    # Policy-based decisions
│   │   ├── actions.py            # Action execution
│   │   ├── policies.py           # Policy loading
│   │   └── validator.py          # Healing validation
│   │
│   ├── mqtt/                 # MQTT Communication
│   │   ├── client.py         # MQTT connection
│   │   ├── publisher.py      # Publish messages
│   │   ├── subscriber.py     # Subscribe to topics
│   │   ├── device_discovery.py
│   │   └── topics.py         # Topic management
│   │
│   ├── database/             # Database Layer
│   │   ├── db_manager.py     # Connection management
│   │   ├── schema.sql        # Database schema
│   │   └── repositories/     # Data access objects
│   │       ├── device_repo.py
│   │       ├── telemetry_repo.py
│   │       ├── anomaly_repo.py
│   │       └── healing_repo.py
│   │
│   ├── simulator/            # Device Simulator
│   │   ├── device_simulator.py
│   │   ├── sensor_simulator.py
│   │   └── virtual_node.py
│   │
│   ├── dashboard/            # Streamlit Dashboard
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── components/
│   │   ├── pages/
│   │   └── utils/
│   │
│   ├── core/                 # Core System
│   │   ├── system_manager.py # Top-level orchestrator
│   │   └── event_bus.py      # Event management
│   │
│   └── utils/                # Utilities
│       ├── constants.py      # Enums & constants
│       ├── logger.py         # Logging setup
│       └── helpers.py        # Helper functions
│
├── config/                   # Configuration
│   ├── healing_policies.yaml # Healing strategies
│   ├── mqtt_config.yaml      # MQTT settings
│   ├── settings.py           # Pydantic settings
│   └── mosquitto.conf        # MQTT broker config
│
├── data/                     # Data Storage
│   ├── processed/            # Processed data
│   └── telemetry/            # Raw telemetry
│
├── logs/                     # Application Logs
│
├── tests/                    # Testing
│   ├── test_anomaly_detector.py
│   ├── test_healing_engine.py
│   ├── unit/
│   └── integration/
│
├── docs/                     # Documentation
│   ├── API_REFERENCE.md
│   ├── MQTT_TOPICS.md
│   ├── HARDWARE_INTEGRATION.md
│   ├── QUICK_START.md
│   └── project_structure.md
│
├── scripts/                  # Helper Scripts
│   ├── run_all.bat/sh        # Start all services
│   ├── setup_db.py           # Initialize database
│   └── cleanup.bat/sh        # Cleanup files
│
├── hardware/                 # Hardware Integration
│   ├── arduino/
│   │   └── arduino_sensor.ino
│   ├── esp32/
│   │   └── esp32_sensor_node.ino
│   └── raspberry_pi/
│       └── pi_serial_bridge.py
│
├── examples/                 # Example Code
│   ├── distributed_edge_node.py
│   └── raspberry_pi_client.py
│
├── requirements.txt          # Python dependencies
├── setup.py                  # Installation script
├── README.md                 # Project overview
└── PROJECT_SUMMARY.md        # Setup summary
```

---

## Key Takeaways

### What Makes This System Intelligent?

1. **Autonomous Detection**
   - Real-time ML-based anomaly detection
   - No manual threshold configuration
   - Adapts to device behavior

2. **Intelligent Healing**
   - Policy-driven decisions
   - Prioritized action sequences
   - Conditional execution based on device state

3. **Self-Learning**
   - Models improve with more data
   - Drift detection for sensor aging
   - Feature engineering for better accuracy

4. **Scalable Architecture**
   - Multi-device support via MQTT
   - Distributed edge nodes possible
   - MQTT broker handles scaling

5. **Production Ready**
   - Comprehensive logging
   - Database persistence
   - Error handling and retries
   - Hardware integration examples

### System Characteristics

```
┌─────────────────────────────────────────┐
│ SELF-HEALING IoT SYSTEM CHARACTERISTICS │
├─────────────────────────────────────────┤
│ ✓ Autonomous      - No human intervention
│ ✓ Intelligent     - ML-powered decisions
│ ✓ Distributed     - MQTT-based
│ ✓ Observable      - Full visibility via dashboard
│ ✓ Resilient       - Handles failures gracefully
│ ✓ Recoverable     - Validates and logs all actions
│ ✓ Configurable    - YAML-based policies
│ ✓ Scalable        - Supports many devices
│ ✓ Integrated      - Real hardware support
│ ✓ Tested          - Comprehensive test suite
└─────────────────────────────────────────┘
```

---

## Next Steps

1. **Run the System**
   - Follow Getting Started guide
   - Start all components
   - Verify all services running

2. **Explore the Dashboard**
   - View device status
   - Monitor anomalies
   - Check healing history

3. **Test Anomaly Detection**
   - Simulate faulty sensor
   - Watch healing in action
   - Verify database logging

4. **Customize Policies**
   - Edit `config/healing_policies.yaml`
   - Add new fault types
   - Adjust action sequences

5. **Integrate Hardware**
   - Use ESP32/Arduino sketches
   - Connect real devices
   - Deploy to production

6. **Monitor & Maintain**
   - Check logs regularly
   - Review healing statistics
   - Optimize model accuracy

---

## Additional Resources

### Documentation Files
- [API Reference](./docs/API_REFERENCE.md) - Complete endpoint documentation
- [MQTT Topics](./docs/MQTT_TOPICS.md) - Topic hierarchy and message formats
- [Project Structure](./docs/project_structure.md) - Detailed architecture
- [Hardware Integration](./docs/HARDWARE_INTEGRATION.md) - Device setup guides
- [Quick Start](./docs/QUICK_START.md) - Get running in 5 minutes

### Example Code
- `examples/distributed_edge_node.py` - Multi-sensor edge device
- `examples/raspberry_pi_client.py` - Raspberry Pi integration
- `hardware/esp32/esp32_sensor_node.ino` - ESP32 firmware

### Configuration
- `config/healing_policies.yaml` - Healing strategies
- `config/mqtt_config.yaml` - MQTT settings
- `.env.example` - Environment variables template

---

**Created**: February 2026
**Version**: 1.0
**Status**: Production Ready

For questions or issues, refer to the documentation in `docs/` folder or examine the source code directly.

Happy Healing! 🚀
