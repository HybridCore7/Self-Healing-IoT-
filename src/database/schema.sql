-- Database Schema for Self-Healing IoT System
-- SQLite Database

-- Devices Table
CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    device_name TEXT NOT NULL,
    device_type TEXT NOT NULL,
    status TEXT DEFAULT 'offline',
    last_heartbeat TIMESTAMP,
    ip_address TEXT,
    firmware_version TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Telemetry Data Table
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    sensor_type TEXT NOT NULL,
    sensor_value REAL NOT NULL,
    unit TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_anomaly BOOLEAN DEFAULT 0,
    original_value REAL,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_telemetry_device_time 
ON telemetry(device_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_telemetry_anomaly 
ON telemetry(is_anomaly, timestamp DESC);

-- Anomalies Table
CREATE TABLE IF NOT EXISTS anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    anomaly_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    sensor_type TEXT,
    anomaly_score REAL,
    description TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    is_resolved BOOLEAN DEFAULT 0,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- Create index for anomaly queries
CREATE INDEX IF NOT EXISTS idx_anomalies_device 
ON anomalies(device_id, detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_anomalies_unresolved 
ON anomalies(is_resolved, detected_at DESC);

-- Healing Logs Table
CREATE TABLE IF NOT EXISTS healing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    anomaly_id INTEGER,
    healing_action TEXT NOT NULL,
    status TEXT NOT NULL,
    initiated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL,
    success BOOLEAN,
    error_message TEXT,
    metadata TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(device_id),
    FOREIGN KEY (anomaly_id) REFERENCES anomalies(id)
);

-- Create index for healing logs
CREATE INDEX IF NOT EXISTS idx_healing_device 
ON healing_logs(device_id, initiated_at DESC);

CREATE INDEX IF NOT EXISTS idx_healing_status 
ON healing_logs(status, initiated_at DESC);

-- System Events Table
CREATE TABLE IF NOT EXISTS system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    event_data TEXT,
    severity TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for system events
CREATE INDEX IF NOT EXISTS idx_events_time 
ON system_events(timestamp DESC);

-- Device Health Metrics Table
CREATE TABLE IF NOT EXISTS device_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    cpu_usage REAL,
    memory_usage REAL,
    battery_level REAL,
    signal_strength REAL,
    uptime_seconds INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- Create index for health metrics
CREATE INDEX IF NOT EXISTS idx_health_device 
ON device_health(device_id, timestamp DESC);

-- Views for common queries

-- Active Anomalies View
CREATE VIEW IF NOT EXISTS active_anomalies AS
SELECT 
    a.*,
    d.device_name,
    d.status as device_status
FROM anomalies a
JOIN devices d ON a.device_id = d.device_id
WHERE a.is_resolved = 0
ORDER BY a.detected_at DESC;

-- Recent Healing Actions View
CREATE VIEW IF NOT EXISTS recent_healing_actions AS
SELECT 
    hl.*,
    d.device_name,
    a.anomaly_type
FROM healing_logs hl
JOIN devices d ON hl.device_id = d.device_id
LEFT JOIN anomalies a ON hl.anomaly_id = a.id
ORDER BY hl.initiated_at DESC
LIMIT 100;

-- Device Statistics View
CREATE VIEW IF NOT EXISTS device_statistics AS
SELECT 
    d.device_id,
    d.device_name,
    d.status,
    COUNT(DISTINCT t.id) as total_telemetry_count,
    COUNT(DISTINCT CASE WHEN t.is_anomaly = 1 THEN t.id END) as anomaly_count,
    COUNT(DISTINCT a.id) as total_anomalies,
    COUNT(DISTINCT hl.id) as total_healing_actions,
    MAX(d.last_heartbeat) as last_seen
FROM devices d
LEFT JOIN telemetry t ON d.device_id = t.device_id
LEFT JOIN anomalies a ON d.device_id = a.device_id
LEFT JOIN healing_logs hl ON d.device_id = hl.device_id
GROUP BY d.device_id;
