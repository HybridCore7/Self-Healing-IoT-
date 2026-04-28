import sqlite3
import os

db_path = "data/self_healing_iot.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE telemetry ADD COLUMN original_value REAL;")
        conn.commit()
        print("Column original_value added to telemetry table.")
    except Exception as e:
        print(f"Error altering table: {e}")
    finally:
        conn.close()
else:
    print("Database not found. It will be created with the new schema.")
