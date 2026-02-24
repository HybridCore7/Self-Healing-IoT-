"""
MQTT Publisher - Publishing utilities for different message types
"""
from typing import Dict, Any, Optional
from datetime import datetime

from src.mqtt.client import get_mqtt_client
from src.mqtt.topics import (
    get_telemetry_topic,
    get_heartbeat_topic,
    get_status_topic,
    get_alert_topic,
    get_command_topic
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MQTTPublisher:
    """Utility class for publishing different types of MQTT messages"""
    
    def __init__(self):
        self.client = get_mqtt_client()
    
    def publish_telemetry(
        self,
        device_id: str,
        sensor_type: str,
        sensor_value: float,
        unit: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish telemetry data
        
        Args:
            device_id: Device identifier
            sensor_type: Type of sensor
            sensor_value: Sensor reading
            unit: Unit of measurement
            metadata: Additional metadata
            
        Returns:
            True if published successfully
        """
        if not self.client or not self.client.is_connected():
            logger.warning("MQTT client not connected")
            return False
        
        topic = get_telemetry_topic(device_id, sensor_type)
        
        payload = {
            'device_id': device_id,
            'sensor_type': sensor_type,
            'value': sensor_value,
            'unit': unit,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        return self.client.publish(topic, payload, qos=0)
    
    def publish_heartbeat(
        self,
        device_id: str,
        status: str = 'online',
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish device heartbeat
        
        Args:
            device_id: Device identifier
            status: Device status
            metadata: Additional metadata (uptime, health metrics, etc.)
            
        Returns:
            True if published successfully
        """
        if not self.client or not self.client.is_connected():
            return False
        
        topic = get_heartbeat_topic(device_id)
        
        payload = {
            'device_id': device_id,
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        return self.client.publish(topic, payload, qos=1)
    
    def publish_status(
        self,
        device_id: str,
        status: str,
        message: Optional[str] = None
    ) -> bool:
        """
        Publish device status update
        
        Args:
            device_id: Device identifier
            status: Status value
            message: Optional status message
            
        Returns:
            True if published successfully
        """
        if not self.client or not self.client.is_connected():
            return False
        
        topic = get_status_topic(device_id)
        
        payload = {
            'device_id': device_id,
            'status': status,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return self.client.publish(topic, payload, qos=1, retain=True)
    
    def publish_alert(
        self,
        device_id: str,
        alert_type: str,
        severity: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish alert/anomaly notification
        
        Args:
            device_id: Device identifier
            alert_type: Type of alert
            severity: Alert severity
            message: Alert message
            metadata: Additional metadata
            
        Returns:
            True if published successfully
        """
        if not self.client or not self.client.is_connected():
            return False
        
        topic = get_alert_topic(device_id, alert_type)
        
        payload = {
            'device_id': device_id,
            'alert_type': alert_type,
            'severity': severity,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        return self.client.publish(topic, payload, qos=1)
    
    def publish_command(
        self,
        device_id: str,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish command to device
        
        Args:
            device_id: Device identifier
            command: Command name
            parameters: Command parameters
            
        Returns:
            True if published successfully
        """
        if not self.client or not self.client.is_connected():
            return False
        
        topic = get_command_topic(device_id, command)
        
        payload = {
            'device_id': device_id,
            'command': command,
            'parameters': parameters or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Publishing command '{command}' to device {device_id}")
        return self.client.publish(topic, payload, qos=1)


# Global publisher instance
_publisher: Optional[MQTTPublisher] = None


def get_publisher() -> MQTTPublisher:
    """Get global MQTT publisher instance"""
    global _publisher
    if _publisher is None:
        _publisher = MQTTPublisher()
    return _publisher
