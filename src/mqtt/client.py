"""
MQTT Client Wrapper - Connection management and messaging
"""
import paho.mqtt.client as mqtt
from typing import Callable, Optional, Dict
import json
import time

from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MQTTClient:
    """MQTT client wrapper with auto-reconnection"""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        on_message_callback: Optional[Callable] = None
    ):
        """
        Initialize MQTT client
        
        Args:
            client_id: Unique client identifier
            on_message_callback: Callback function for incoming messages
        """
        self.client_id = client_id or f"iot_backend_{int(time.time())}"
        self.client = mqtt.Client(client_id=self.client_id)
        self.connected = False
        self.message_handlers: Dict[str, Callable] = {}
        
        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Store custom message callback
        self.on_message_callback = on_message_callback
        
        # Configure authentication if provided
        if settings.mqtt_username and settings.mqtt_password:
            self.client.username_pw_set(
                settings.mqtt_username,
                settings.mqtt_password
            )
        
        logger.info(f"MQTT client initialized: {self.client_id}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker at {settings.mqtt_broker_host}:{settings.mqtt_broker_port}")
            
            # Resubscribe to topics after reconnection
            if self.message_handlers:
                for topic in self.message_handlers.keys():
                    self.client.subscribe(topic)
                    logger.info(f"Resubscribed to topic: {topic}")
        else:
            self.connected = False
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker, return code: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        logger.debug(f"Received message on topic {topic}: {payload}")
        
        # Try to parse as JSON
        try:
            message_data = json.loads(payload)
        except json.JSONDecodeError:
            message_data = payload
        
        # Call topic-specific handler if registered
        if topic in self.message_handlers:
            try:
                self.message_handlers[topic](topic, message_data)
            except Exception as e:
                logger.error(f"Error in message handler for {topic}: {e}")
        
        # Call global message callback if provided
        if self.on_message_callback:
            try:
                self.on_message_callback(topic, message_data)
            except Exception as e:
                logger.error(f"Error in global message callback: {e}")
    
    def connect(self) -> bool:
        """
        Connect to MQTT broker
        
        Returns:
            True if connection initiated successfully
        """
        try:
            self.client.connect(
                settings.mqtt_broker_host,
                settings.mqtt_broker_port,
                settings.mqtt_keepalive
            )
            self.client.loop_start()
            logger.info("MQTT connection initiated")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT client disconnected")
    
    def publish(
        self,
        topic: str,
        payload: any,
        qos: int = 0,
        retain: bool = False
    ) -> bool:
        """
        Publish message to topic
        
        Args:
            topic: MQTT topic
            payload: Message payload (will be JSON-encoded if dict/list)
            qos: Quality of Service level (0, 1, or 2)
            retain: Whether to retain message
            
        Returns:
            True if published successfully
        """
        if not self.connected:
            logger.warning("Cannot publish - not connected to MQTT broker")
            return False
        
        # Convert payload to JSON if it's a dict or list
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload)
        
        try:
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {topic}: {payload}")
                return True
            else:
                logger.error(f"Failed to publish to {topic}, return code: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Error publishing to {topic}: {e}")
            return False
    
    def subscribe(
        self,
        topic: str,
        callback: Optional[Callable] = None,
        qos: int = 0
    ) -> bool:
        """
        Subscribe to topic
        
        Args:
            topic: MQTT topic (supports wildcards)
            callback: Optional callback function for this topic
            qos: Quality of Service level
            
        Returns:
            True if subscribed successfully
        """
        try:
            result = self.client.subscribe(topic, qos=qos)
            
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Subscribed to topic: {topic}")
                
                # Register topic-specific callback if provided
                if callback:
                    self.message_handlers[topic] = callback
                
                return True
            else:
                logger.error(f"Failed to subscribe to {topic}, return code: {result[0]}")
                return False
        except Exception as e:
            logger.error(f"Error subscribing to {topic}: {e}")
            return False
    
    def unsubscribe(self, topic: str) -> bool:
        """
        Unsubscribe from topic
        
        Args:
            topic: MQTT topic
            
        Returns:
            True if unsubscribed successfully
        """
        try:
            result = self.client.unsubscribe(topic)
            
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Unsubscribed from topic: {topic}")
                
                # Remove topic-specific handler
                if topic in self.message_handlers:
                    del self.message_handlers[topic]
                
                return True
            else:
                logger.error(f"Failed to unsubscribe from {topic}")
                return False
        except Exception as e:
            logger.error(f"Error unsubscribing from {topic}: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to broker"""
        return self.connected


# Global MQTT client instance
mqtt_client: Optional[MQTTClient] = None


def get_mqtt_client() -> Optional[MQTTClient]:
    """Get global MQTT client instance"""
    return mqtt_client


def initialize_mqtt_client(on_message_callback: Optional[Callable] = None) -> MQTTClient:
    """
    Initialize and connect global MQTT client
    
    Args:
        on_message_callback: Optional global message callback
        
    Returns:
        Initialized MQTT client
    """
    global mqtt_client
    mqtt_client = MQTTClient(on_message_callback=on_message_callback)
    mqtt_client.connect()
    return mqtt_client
