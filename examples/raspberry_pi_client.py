#!/usr/bin/env python3
"""
Raspberry Pi IoT Device Client
Connects to Self-Healing IoT System via MQTT

Hardware: Raspberry Pi with DHT22 sensor
Wiring:
  DHT22 VCC  -> Pi Pin 1 (3.3V)
  DHT22 Data -> Pi Pin 7 (GPIO 4)
  DHT22 GND  -> Pi Pin 6 (GND)

Installation:
  pip3 install paho-mqtt Adafruit_DHT

Usage:
  python3 raspberry_pi_client.py
"""
import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime
import sys

# Try to import sensor libraries
try:
    import Adafruit_DHT
    DHT_SENSOR = Adafruit_DHT.DHT22
    DHT_PIN = 4
    HAS_DHT = True
except ImportError:
    HAS_DHT = False
    print("⚠️  DHT library not found, using simulated data")
    print("   Install with: pip3 install Adafruit_DHT")

# Configuration
MQTT_BROKER = "192.168.1.100"  # Change to your MQTT broker IP
MQTT_PORT = 1883
DEVICE_ID = "rpi_001"
DEVICE_NAME = "Raspberry Pi Sensor Node"
DEVICE_TYPE = "raspberry_pi"

# Intervals (seconds)
TELEMETRY_INTERVAL = 10
HEARTBEAT_INTERVAL = 30


class IoTDevice:
    """IoT Device Client for Raspberry Pi"""
    
    def __init__(self):
        self.client = mqtt.Client(client_id=DEVICE_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.running = True
        self.start_time = time.time()
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            print(f"✓ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            
            # Subscribe to commands
            command_topic = f"iot/commands/{DEVICE_ID}/#"
            client.subscribe(command_topic)
            print(f"✓ Subscribed to {command_topic}")
            
            # Send initial heartbeat
            self.publish_heartbeat()
        else:
            print(f"✗ Connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected"""
        if rc != 0:
            print(f"⚠️  Unexpected disconnection (code {rc}), reconnecting...")
    
    def on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            payload = json.loads(msg.payload.decode())
            command = payload.get('command')
            parameters = payload.get('parameters', {})
            
            print(f"\n📨 Received command: {command}")
            
            # Handle commands
            if command == 'ping':
                print("   Responding to ping...")
                self.publish_heartbeat()
                
            elif command == 'reset':
                print("   Executing reset...")
                # Reset logic here
                self.publish_status("Device reset completed")
                
            elif command == 'restart':
                print("   Restarting device...")
                self.publish_status("Restarting...")
                time.sleep(1)
                sys.exit(0)
                
            elif command == 'validate':
                print("   Validating sensor readings...")
                sample_count = parameters.get('sample_count', 5)
                interval = parameters.get('interval', 2)
                
                for i in range(sample_count):
                    self.publish_telemetry()
                    if i < sample_count - 1:
                        time.sleep(interval)
                
                self.publish_status(f"Validation complete: {sample_count} samples")
            
            else:
                print(f"   Unknown command: {command}")
                
        except Exception as e:
            print(f"✗ Error handling message: {e}")
    
    def read_sensors(self):
        """Read sensor data from DHT22 or simulate"""
        if HAS_DHT:
            # Try to read from actual sensor
            humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            
            if humidity is not None and temperature is not None:
                return {
                    'temperature': round(temperature, 2),
                    'humidity': round(humidity, 2)
                }
            else:
                print("⚠️  Failed to read from DHT sensor, using simulated data")
        
        # Simulated data (for testing without hardware)
        return {
            'temperature': round(20 + random.uniform(-5, 5), 2),
            'humidity': round(50 + random.uniform(-10, 10), 2)
        }
    
    def publish_telemetry(self):
        """Publish sensor telemetry to MQTT"""
        data = self.read_sensors()
        
        # Publish temperature
        temp_payload = {
            'device_id': DEVICE_ID,
            'sensor_type': 'temperature',
            'value': data['temperature'],
            'unit': '°C',
            'timestamp': datetime.utcnow().isoformat()
        }
        temp_topic = f"iot/telemetry/{DEVICE_ID}/temperature"
        self.client.publish(temp_topic, json.dumps(temp_payload))
        
        # Publish humidity
        hum_payload = {
            'device_id': DEVICE_ID,
            'sensor_type': 'humidity',
            'value': data['humidity'],
            'unit': '%',
            'timestamp': datetime.utcnow().isoformat()
        }
        hum_topic = f"iot/telemetry/{DEVICE_ID}/humidity"
        self.client.publish(hum_topic, json.dumps(hum_payload))
        
        print(f"📊 Telemetry: Temp={data['temperature']}°C, Humidity={data['humidity']}%")
    
    def publish_heartbeat(self):
        """Publish device heartbeat"""
        uptime = int(time.time() - self.start_time)
        
        payload = {
            'device_id': DEVICE_ID,
            'status': 'online',
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': {
                'uptime_seconds': uptime,
                'device_name': DEVICE_NAME,
                'device_type': DEVICE_TYPE,
                'sensor_count': 2,
                'has_real_sensor': HAS_DHT
            }
        }
        
        topic = f"iot/health/{DEVICE_ID}/heartbeat"
        self.client.publish(topic, json.dumps(payload), retain=True)
        print(f"💓 Heartbeat sent (uptime: {uptime}s)")
    
    def publish_status(self, message):
        """Publish status update"""
        payload = {
            'device_id': DEVICE_ID,
            'status': 'online',
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        topic = f"iot/status/{DEVICE_ID}"
        self.client.publish(topic, json.dumps(payload), retain=True)
        print(f"📢 Status: {message}")
    
    def run(self):
        """Main run loop"""
        print(f"\n🚀 Starting IoT Device Client")
        print(f"   Device ID: {DEVICE_ID}")
        print(f"   Device Name: {DEVICE_NAME}")
        print(f"   MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"   Sensor: {'DHT22 (real)' if HAS_DHT else 'Simulated'}")
        print()
        
        # Connect to broker
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        except Exception as e:
            print(f"✗ Failed to connect to MQTT broker: {e}")
            print(f"   Make sure broker is running at {MQTT_BROKER}:{MQTT_PORT}")
            return
        
        self.client.loop_start()
        
        last_telemetry = 0
        last_heartbeat = 0
        
        try:
            while self.running:
                now = time.time()
                
                # Publish telemetry
                if now - last_telemetry >= TELEMETRY_INTERVAL:
                    self.publish_telemetry()
                    last_telemetry = now
                
                # Publish heartbeat
                if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                    self.publish_heartbeat()
                    last_heartbeat = now
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down...")
            self.publish_status("Device shutting down")
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            print("👋 Disconnected from MQTT broker")


if __name__ == "__main__":
    device = IoTDevice()
    device.run()
