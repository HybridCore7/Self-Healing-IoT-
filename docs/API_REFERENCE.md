# Backend API Endpoints - Complete Reference

## Overview

All backend API endpoints are now fully implemented with database integration, error handling, and comprehensive functionality.

## Base URL
`http://localhost:8000`

## API Documentation
Interactive API docs available at: `http://localhost:8000/docs`

---

## 1. Devices API (`/api/devices`)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/devices` | List all devices |
| GET | `/api/devices/{device_id}` | Get device details |
| POST | `/api/devices` | Register new device |
| PUT | `/api/devices/{device_id}` | Update device |
| DELETE | `/api/devices/{device_id}` | Remove device |
| GET | `/api/devices/{device_id}/status` | Get device status |

---

## 2. Telemetry API (`/api/telemetry`)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/telemetry` | Create telemetry record |
| GET | `/api/telemetry/{device_id}` | Get device telemetry |
| GET | `/api/telemetry/{device_id}/stats` | Get statistics |
| GET | `/api/telemetry/anomalies/recent` | Get anomalous data |

---

## 3. Anomalies API (`/api/anomalies`) ✨ NEW

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/anomalies` | List anomalies with filtering |
| GET | `/api/anomalies/{anomaly_id}` | Get anomaly details |
| POST | `/api/anomalies/{anomaly_id}/resolve` | Mark anomaly as resolved |
| GET | `/api/anomalies/device/{device_id}` | Get device anomalies |
| GET | `/api/anomalies/stats/summary` | Get anomaly summary |
| GET | `/api/anomalies/stats/timeline` | Get anomaly timeline |

### Query Parameters

**GET /api/anomalies**
- `device_id` (optional): Filter by device
- `severity` (optional): Filter by severity (low, medium, high, critical)
- `active_only` (bool): Show only unresolved anomalies
- `limit` (int): Maximum results (1-500, default 100)

**GET /api/anomalies/stats/timeline**
- `hours` (int): Time range in hours (1-168, default 24)

---

## 4. Healing API (`/api/healing`) ✨ NEW

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/healing/logs` | Get healing action logs |
| GET | `/api/healing/logs/{device_id}` | Get device healing logs |
| GET | `/api/healing/stats` | Get healing statistics |
| GET | `/api/healing/active` | Get active healing workflows |
| POST | `/api/healing/trigger/{device_id}` | Manually trigger healing |
| GET | `/api/healing/actions` | List available actions |

### Query Parameters

**GET /api/healing/logs**
- `device_id` (optional): Filter by device
- `status` (optional): Filter by status (pending, in_progress, success, failed, timeout)
- `limit` (int): Maximum logs (1-500, default 100)

**GET /api/healing/stats**
- `device_id` (optional): Filter by device

**POST /api/healing/trigger/{device_id}**
Request body:
```json
{
  "action": "reset",
  "parameters": {}
}
```

Available actions:
- `validate` - Validate sensor reading
- `switch_sensor` - Switch to backup sensor
- `reset` - Reset sensor
- `restart` - Restart device
- `isolate` - Isolate device
- `calibrate` - Calibrate sensor
- `reconnect` - Reconnect MQTT
- `ping` - Ping device

---

## 5. Health API (`/api/health`) ✨ NEW

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health/` | Overall system health |
| GET | `/api/health/metrics` | System performance metrics |
| GET | `/api/health/devices` | Device health summary |
| GET | `/api/health/anomalies` | Anomaly statistics |

### Response Examples

**GET /api/health/**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-11T03:00:00Z",
  "services": {
    "backend": "running",
    "mqtt": "connected",
    "database": "connected",
    "healing_orchestrator": "running"
  }
}
```

**GET /api/health/metrics**
```json
{
  "timestamp": "2026-02-11T03:00:00Z",
  "devices": {
    "total": 5,
    "active": 4,
    "offline": 1
  },
  "anomalies": {
    "active": 2,
    "by_severity": {
      "low": 0,
      "medium": 2,
      "high": 0,
      "critical": 0
    }
  },
  "healing": {
    "actions_today": 3,
    "total_actions": 15
  },
  "system_resources": {
    "cpu_percent": 12.5,
    "memory_percent": 45.2,
    "memory_used_mb": 512.3,
    "disk_percent": 60.1,
    "disk_free_gb": 50.5
  }
}
```

**GET /api/health/devices**
```json
{
  "total_devices": 5,
  "health_summary": {
    "healthy": 3,
    "warning": 1,
    "critical": 0,
    "offline": 1
  },
  "devices": [
    {
      "device_id": "device_001",
      "device_name": "Sensor Node 1",
      "status": "online",
      "health": "healthy",
      "active_anomalies": 0,
      "last_heartbeat": "2026-02-11T03:00:00Z"
    }
  ]
}
```

---

## Testing Examples

### Using cURL

```bash
# Get all devices
curl http://localhost:8000/api/devices

# Get system health
curl http://localhost:8000/api/health/

# Get active anomalies
curl http://localhost:8000/api/anomalies?active_only=true

# Get healing statistics
curl http://localhost:8000/api/healing/stats

# Trigger manual healing
curl -X POST http://localhost:8000/api/healing/trigger/device_001 \
  -H "Content-Type: application/json" \
  -d '{"action": "reset"}'

# Get anomaly timeline (last 24 hours)
curl http://localhost:8000/api/anomalies/stats/timeline?hours=24

# Resolve an anomaly
curl -X POST http://localhost:8000/api/anomalies/123/resolve
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Get system metrics
response = requests.get(f"{BASE_URL}/api/health/metrics")
metrics = response.json()
print(f"Active devices: {metrics['devices']['active']}")

# Get healing logs
response = requests.get(f"{BASE_URL}/api/healing/logs?limit=10")
logs = response.json()
print(f"Recent healing actions: {logs['count']}")

# Trigger healing
response = requests.post(
    f"{BASE_URL}/api/healing/trigger/device_001",
    json={"action": "reset"}
)
result = response.json()
print(f"Healing triggered: {result['success']}")
```

---

## Summary

### Total Endpoints: 27

- **Devices**: 6 endpoints
- **Telemetry**: 4 endpoints
- **Anomalies**: 6 endpoints ✨
- **Healing**: 6 endpoints ✨
- **Health**: 4 endpoints ✨
- **Root**: 1 endpoint

### Features

✅ Complete CRUD operations for all entities  
✅ Advanced filtering and querying  
✅ Real-time statistics and metrics  
✅ Manual healing triggers  
✅ System health monitoring  
✅ Resource usage tracking  
✅ Timeline and trend analysis  
✅ Comprehensive error handling  
✅ Input validation with Pydantic  
✅ Database integration  
✅ Async/await throughout  

### Next Steps

1. Test all endpoints with real data
2. Build dashboard to visualize this data
3. Add authentication/authorization
4. Implement rate limiting
5. Add caching for frequently accessed data
