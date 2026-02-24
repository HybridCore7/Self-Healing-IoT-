"""
MQTT Subscriber - Subscription management and message routing
"""
from typing import Callable, Dict, Optional
import asyncio

from src.mqtt.client import get_mqtt_client
from src.mqtt.topics import get_wildcard_topic, parse_topic
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MQTTSubscriber:
    """Manages MQTT subscriptions and message routing"""
    
    def __init__(self):
        self.client = get_mqtt_client()
        self.handlers: Dict[str, Callable] = {}
    
    def subscribe_to_telemetry(
        self,
        callback: Callable,
        device_id: Optional[str] = None
    ) -> bool:
        """
        Subscribe to telemetry messages
        
        Args:
            callback: Function to handle telemetry messages
            device_id: Optional device filter
            
        Returns:
            True if subscribed successfully
        """
        if not self.client or not self.client.is_connected():
            logger.warning("MQTT client not connected")
            return False
        
        topic = get_wildcard_topic('telemetry', device_id)
        
        def telemetry_handler(topic: str, message: dict):
            """Handle telemetry message"""
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Error in telemetry callback: {e}")
        
        self.handlers[topic] = telemetry_handler
        return self.client.subscribe(topic, callback=telemetry_handler, qos=0)
    
    def subscribe_to_heartbeats(
        self,
        callback: Callable,
        device_id: Optional[str] = None
    ) -> bool:
        """
        Subscribe to heartbeat messages
        
        Args:
            callback: Function to handle heartbeat messages
            device_id: Optional device filter
            
        Returns:
            True if subscribed successfully
        """
        if not self.client or not self.client.is_connected():
            return False
        
        topic = get_wildcard_topic('health', device_id)
        
        def heartbeat_handler(topic: str, message: dict):
            """Handle heartbeat message"""
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Error in heartbeat callback: {e}")
        
        self.handlers[topic] = heartbeat_handler
        return self.client.subscribe(topic, callback=heartbeat_handler, qos=1)
    
    def subscribe_to_alerts(
        self,
        callback: Callable,
        device_id: Optional[str] = None
    ) -> bool:
        """
        Subscribe to alert messages
        
        Args:
            callback: Function to handle alert messages
            device_id: Optional device filter
            
        Returns:
            True if subscribed successfully
        """
        if not self.client or not self.client.is_connected():
            return False
        
        topic = get_wildcard_topic('alerts', device_id)
        
        def alert_handler(topic: str, message: dict):
            """Handle alert message"""
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
        
        self.handlers[topic] = alert_handler
        return self.client.subscribe(topic, callback=alert_handler, qos=1)
    
    def subscribe_to_commands(
        self,
        callback: Callable,
        device_id: Optional[str] = None
    ) -> bool:
        """
        Subscribe to command messages (for monitoring)
        
        Args:
            callback: Function to handle command messages
            device_id: Optional device filter
            
        Returns:
            True if subscribed successfully
        """
        if not self.client or not self.client.is_connected():
            return False
        
        topic = get_wildcard_topic('commands', device_id)
        
        def command_handler(topic: str, message: dict):
            """Handle command message"""
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Error in command callback: {e}")
        
        self.handlers[topic] = command_handler
        return self.client.subscribe(topic, callback=command_handler, qos=1)
    
    def subscribe_all(
        self,
        telemetry_callback: Optional[Callable] = None,
        heartbeat_callback: Optional[Callable] = None,
        alert_callback: Optional[Callable] = None,
        command_callback: Optional[Callable] = None
    ):
        """
        Subscribe to all message types
        
        Args:
            telemetry_callback: Handler for telemetry messages
            heartbeat_callback: Handler for heartbeat messages
            alert_callback: Handler for alert messages
            command_callback: Handler for command messages
        """
        if telemetry_callback:
            self.subscribe_to_telemetry(telemetry_callback)
        
        if heartbeat_callback:
            self.subscribe_to_heartbeats(heartbeat_callback)
        
        if alert_callback:
            self.subscribe_to_alerts(alert_callback)
        
        if command_callback:
            self.subscribe_to_commands(command_callback)
        
        logger.info("Subscribed to all MQTT message types")
    
    def unsubscribe_all(self):
        """Unsubscribe from all topics"""
        if not self.client:
            return
        
        for topic in self.handlers.keys():
            self.client.unsubscribe(topic)
        
        self.handlers.clear()
        logger.info("Unsubscribed from all MQTT topics")


# Global subscriber instance
_subscriber: Optional[MQTTSubscriber] = None


def get_subscriber() -> MQTTSubscriber:
    """Get global MQTT subscriber instance"""
    global _subscriber
    if _subscriber is None:
        _subscriber = MQTTSubscriber()
    return _subscriber
