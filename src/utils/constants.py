"""
Application-wide constants and enumerations
"""
from enum import Enum


class DeviceStatus(str, Enum):
    """Device operational status"""
    ONLINE = "online"
    OFFLINE = "offline"
    ISOLATED = "isolated"
    HEALING = "healing"
    ERROR = "error"


class SensorType(str, Enum):
    """Sensor types supported by the system"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    LIGHT = "light"
    GAS = "gas"
    PRESSURE = "pressure"


class AnomalyType(str, Enum):
    """Types of anomalies detected"""
    SENSOR_FAULT = "sensor_fault"
    SENSOR_DRIFT = "sensor_drift"
    OUT_OF_RANGE = "out_of_range"
    STUCK_VALUE = "stuck_value"
    SUDDEN_SPIKE = "sudden_spike"
    COMMUNICATION_ERROR = "communication_error"


class HealingAction(str, Enum):
    """Healing actions that can be performed"""
    VALIDATE_READING = "validate_reading"
    SWITCH_SENSOR = "switch_to_backup_sensor"
    RESET_SENSOR = "reset_sensor"
    RESTART_DEVICE = "restart_device"
    ISOLATE_DEVICE = "isolate_device"
    CALIBRATE_SENSOR = "calibrate_sensor"
    RECONNECT_MQTT = "reconnect_mqtt"
    PING_DEVICE = "ping_device"


class HealingStatus(str, Enum):
    """Status of healing actions"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Severity(str, Enum):
    """Severity levels for faults and anomalies"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Sensor Value Ranges (Normal Operating Ranges)
SENSOR_RANGES = {
    SensorType.TEMPERATURE: {"min": -10.0, "max": 50.0, "unit": "°C"},
    SensorType.HUMIDITY: {"min": 0.0, "max": 100.0, "unit": "%"},
    SensorType.LIGHT: {"min": 0.0, "max": 1024.0, "unit": "lux"},
    SensorType.GAS: {"min": 0.0, "max": 1000.0, "unit": "ppm"},
}

# MQTT Topic Templates
MQTT_TOPICS = {
    "telemetry": "iot/telemetry/{device_id}/{sensor_type}",
    "health": "iot/health/{device_id}/heartbeat",
    "status": "iot/health/{device_id}/status",
    "alerts": "iot/alerts/{device_id}/{alert_type}",
    "commands": "iot/commands/{device_id}/{command}",
}

# Default Configuration Values
DEFAULT_HEARTBEAT_INTERVAL = 10  # seconds
DEFAULT_TELEMETRY_INTERVAL = 5  # seconds
DEFAULT_ANOMALY_WINDOW = 50  # number of samples
DEFAULT_HEALING_TIMEOUT = 30  # seconds

# Database Constants
DB_TABLES = {
    "devices": "devices",
    "telemetry": "telemetry",
    "anomalies": "anomalies",
    "healing_logs": "healing_logs",
}
