#!/usr/bin/env python3
"""
Arduino → MQTT Serial Bridge
==============================
Runs on Raspberry Pi. Reads serial CSV from Arduino and forwards to MQTT.
Also relays healing commands received from MQTT back to Arduino.

Install: pip3 install paho-mqtt pyserial
Run:     python3 pi_serial_bridge.py --port /dev/ttyUSB0 --broker 192.168.1.100
"""
import serial
import json
import time
import argparse
import threading
from datetime import datetime
import paho.mqtt.client as mqtt

# ── Queue for commands to send to Arduino ──────
_command_queue = []

def make_payload(device_id: str, sensor_type: str, value: float,
                 unit: str, location: str, seq: int) -> dict:
    return {
        "device_id":   device_id,
        "device_name": f"Arduino {device_id}",
        "device_type": "arduino",
        "sensor_type": sensor_type,
        "value":       value,
        "unit":        unit,
        "location":    location,
        "seq":         seq,
        "timestamp":   datetime.utcnow().isoformat(),
    }

def make_heartbeat(device_id: str, location: str, uptime_ms: int) -> dict:
    return {
        "device_id":   device_id,
        "device_name": f"Arduino {device_id}",
        "device_type": "arduino",
        "location":    location,
        "status":      "online",
        "uptime_ms":   uptime_ms,
        "timestamp":   datetime.utcnow().isoformat(),
    }

def on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✓ MQTT bridge connected")
        # Subscribe to commands for ALL arduino devices (wildcard)
        client.subscribe("iot/commands/arduino_+/#")
    else:
        print(f"✗ MQTT connect failed: rc={rc}")

def on_mqtt_message(client, userdata, msg):
    """Relay MQTT healing command to Arduino over serial."""
    try:
        payload = json.loads(msg.payload.decode())
        command = payload.get("command", "")
        # Extract device_id from topic: iot/commands/{device_id}/{action}
        parts = msg.topic.split("/")
        if len(parts) >= 3:
            device_id = parts[2]
            print(f"[Bridge] Relaying command '{command}' to {device_id} via serial")
            _command_queue.append(command)
    except Exception as e:
        print(f"[Bridge] Error parsing MQTT command: {e}")

def run_bridge(serial_port: str, baud: int, broker: str, port: int):
    # Setup MQTT
    client = mqtt.Client("arduino_bridge")
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message
    client.connect(broker, port, 60)
    client.loop_start()

    # Open serial
    print(f"Opening serial port {serial_port} at {baud} baud...")
    ser = serial.Serial(serial_port, baud, timeout=1)
    time.sleep(2)  # Let Arduino settle after reset
    print("✓ Serial connected. Listening for data...")

    while True:
        # Relay pending MQTT commands to Arduino
        while _command_queue:
            cmd = _command_queue.pop(0)
            ser.write((cmd + "\n").encode())
            print(f"[Bridge] Sent to Arduino: {cmd}")

        # Read line from Arduino
        try:
            raw = ser.readline().decode("utf-8", errors="ignore").strip()
        except Exception:
            time.sleep(0.5)
            continue

        if not raw:
            continue

        parts = raw.split(",")
        msg_type = parts[0] if parts else ""

        # TELEMETRY,device_id,sensor_type,value,unit,location,seq
        if msg_type == "TELEMETRY" and len(parts) >= 7:
            device_id   = parts[1]
            sensor_type = parts[2]
            try:
                value = float(parts[3])
            except ValueError:
                continue
            unit     = parts[4]
            location = parts[5]
            seq      = int(parts[6]) if parts[6].isdigit() else 0

            payload  = make_payload(device_id, sensor_type, value, unit, location, seq)
            topic    = f"iot/telemetry/{device_id}/{sensor_type}"
            client.publish(topic, json.dumps(payload))
            print(f"[{device_id}] {sensor_type}={value}{unit}")

        # HEARTBEAT,device_id,device_type,location,uptime_ms
        elif msg_type == "HEARTBEAT" and len(parts) >= 5:
            device_id  = parts[1]
            location   = parts[3]
            uptime_ms  = int(parts[4]) if parts[4].isdigit() else 0
            payload    = make_heartbeat(device_id, location, uptime_ms)
            topic      = f"iot/health/{device_id}/heartbeat"
            client.publish(topic, json.dumps(payload), retain=True)
            print(f"[{device_id}] ♥ Heartbeat (uptime={uptime_ms}ms)")

        # STATUS,device_id,event,message
        elif msg_type == "STATUS" and len(parts) >= 4:
            device_id = parts[1]
            event     = parts[2]
            message   = ",".join(parts[3:])
            payload   = {
                "device_id": device_id, "event": event,
                "message": message, "timestamp": datetime.utcnow().isoformat()
            }
            topic = f"iot/status/{device_id}"
            client.publish(topic, json.dumps(payload))
            print(f"[{device_id}] Status: {event} — {message}")

        else:
            if raw:
                print(f"[Serial] {raw}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arduino → MQTT Serial Bridge")
    parser.add_argument("--port",   default="/dev/ttyUSB0", help="Serial port")
    parser.add_argument("--baud",   type=int, default=9600, help="Baud rate")
    parser.add_argument("--broker", default="localhost",    help="MQTT broker host")
    parser.add_argument("--mport",  type=int, default=1883, help="MQTT broker port")
    args = parser.parse_args()

    try:
        run_bridge(args.port, args.baud, args.broker, args.mport)
    except KeyboardInterrupt:
        print("\nBridge stopped.")
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        print(f"Check that Arduino is connected to {args.port}")
        print("Available ports: ls /dev/tty* (Linux) or Device Manager (Windows)")
