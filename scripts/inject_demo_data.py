"""
inject_demo_data.py
====================
Populates the SQLite database with realistic telemetry data for 3 hardware
nodes so the dashboard can be demoed without physical hardware.

Run:  python scripts/inject_demo_data.py
"""
import sqlite3
import os
import sys
import random
import math
from datetime import datetime, timedelta
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DB_PATH = os.path.join(project_root, "data", "iot_system.db")

# ── Node Definitions ──
NODES = [
    {"device_id": "node_1", "device_name": "Gateway Node",  "device_type": "custom", "role": "Parent Node"},
    {"device_id": "node_2", "device_name": "Sensor Alpha",  "device_type": "custom", "role": "Child Node"},
    {"device_id": "node_3", "device_name": "Sensor Beta",   "device_type": "custom", "role": "Child Node"},
]

# ── Simulation Config ──
DURATION_HOURS = 6          # 6 hours of historical data
INTERVAL_SECONDS = 30       # One reading every 30 seconds
ANOMALY_PROBABILITY = 0.06  # ~6% of readings will be anomalies

# Sensor baseline profiles per node
PROFILES = {
    "node_1": {"temperature": 26.0, "humidity": 55.0},
    "node_2": {"temperature": 24.5, "humidity": 60.0},
    "node_3": {"temperature": 25.0, "humidity": 58.0},
}

UNITS = {"temperature": "°C", "humidity": "%"}


def create_tables(conn):
    """Create tables if they don't exist (mirrors schema.sql)."""
    cursor = conn.cursor()

    cursor.execute("""
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
        )
    """)

    cursor.execute("""
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
        )
    """)

    cursor.execute("""
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
        )
    """)

    cursor.execute("""
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
        )
    """)

    # Try to add original_value column if missing
    try:
        cursor.execute("ALTER TABLE telemetry ADD COLUMN original_value REAL")
    except:
        pass  # column already exists

    conn.commit()


def register_devices(conn):
    """Insert the 3 demo devices."""
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    for node in NODES:
        cursor.execute("""
            INSERT OR REPLACE INTO devices
                (device_id, device_name, device_type, status, last_heartbeat, location)
            VALUES (?, ?, ?, 'online', ?, 'Lab Room 101')
        """, (node["device_id"], node["device_name"], node["device_type"], now))
    conn.commit()
    print(f"  ✓ Registered {len(NODES)} devices")


def generate_telemetry(conn):
    """Generate realistic sensor data with anomalies and AI corrections."""
    cursor = conn.cursor()
    now = datetime.utcnow()
    start = now - timedelta(hours=DURATION_HOURS)

    total_readings = 0
    total_anomalies = 0
    anomaly_ids = []

    for node_id, sensors in PROFILES.items():
        for sensor_type, baseline in sensors.items():
            t = start
            step = 0
            while t <= now:
                step += 1
                # Natural drift with sinusoidal pattern + noise
                drift = math.sin(step * 0.05) * 1.5
                noise = random.gauss(0, 0.3)
                value = baseline + drift + noise

                is_anomaly = 0
                original_value = None

                # Randomly inject anomalies
                if random.random() < ANOMALY_PROBABILITY:
                    is_anomaly = 1
                    total_anomalies += 1

                    # Choose fault type
                    fault = random.choice(["spike", "drop", "stuck"])
                    if fault == "spike":
                        original_value = value + random.uniform(15, 40)
                    elif fault == "drop":
                        original_value = value - random.uniform(15, 30)
                    else:  # stuck
                        original_value = 999.0 if sensor_type == "temperature" else 0.0

                    # The stored sensor_value is the AI-corrected value
                    # (the original faulty value is saved in original_value)

                cursor.execute("""
                    INSERT INTO telemetry
                        (device_id, sensor_type, sensor_value, unit, timestamp, is_anomaly, original_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    node_id,
                    sensor_type,
                    round(value, 2),
                    UNITS[sensor_type],
                    t.isoformat(),
                    is_anomaly,
                    round(original_value, 2) if original_value is not None else None,
                ))

                # If anomaly, also create an anomaly record and a healing log
                if is_anomaly:
                    severity = random.choice(["low", "medium", "high"])
                    score = round(random.uniform(0.7, 0.99), 3)
                    cursor.execute("""
                        INSERT INTO anomalies
                            (device_id, anomaly_type, severity, sensor_type, anomaly_score,
                             description, detected_at, resolved_at, is_resolved)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """, (
                        node_id,
                        "sensor_fault",
                        severity,
                        sensor_type,
                        score,
                        f"AI corrected {sensor_type} from {original_value:.1f} to {value:.2f}",
                        t.isoformat(),
                        (t + timedelta(seconds=2)).isoformat(),
                    ))
                    anomaly_id = cursor.lastrowid
                    anomaly_ids.append(anomaly_id)

                    # Healing log
                    cursor.execute("""
                        INSERT INTO healing_logs
                            (device_id, anomaly_id, healing_action, status,
                             initiated_at, completed_at, duration_seconds, success)
                        VALUES (?, ?, ?, 'completed', ?, ?, ?, 1)
                    """, (
                        node_id,
                        anomaly_id,
                        "ai_value_correction",
                        t.isoformat(),
                        (t + timedelta(seconds=2)).isoformat(),
                        round(random.uniform(0.5, 3.0), 2),
                    ))

                total_readings += 1
                t += timedelta(seconds=INTERVAL_SECONDS)

    conn.commit()
    print(f"  ✓ Generated {total_readings:,} telemetry readings")
    print(f"  ✓ Injected {total_anomalies} anomalies with AI corrections")
    print(f"  ✓ Created {len(anomaly_ids)} healing log entries")


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    print("=" * 55)
    print("  SELF-HEALING IoT — DEMO DATA INJECTOR")
    print("=" * 55)
    print(f"  Database: {DB_PATH}")
    print(f"  Duration: {DURATION_HOURS} hours of history")
    print(f"  Interval: every {INTERVAL_SECONDS}s")
    print(f"  Anomaly Rate: {ANOMALY_PROBABILITY*100:.0f}%")
    print("-" * 55)

    conn = sqlite3.connect(DB_PATH)

    create_tables(conn)
    register_devices(conn)
    generate_telemetry(conn)

    conn.close()

    print("-" * 55)
    print("  ✅ Demo data injected successfully!")
    print("  Now start the backend and dashboard:")
    print("    python -m src.backend.main")
    print("    streamlit run dashboard_hardware.py --server.port 8503")
    print("=" * 55)


if __name__ == "__main__":
    main()
