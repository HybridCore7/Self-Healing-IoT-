"""
MQTT Topic Management - Topic generation and parsing utilities
"""
from typing import Dict, Optional
from src.utils.constants import MQTT_TOPICS


def format_topic(template: str, **kwargs) -> str:
    """
    Format MQTT topic with parameters
    
    Args:
        template: Topic template with placeholders
        **kwargs: Values for placeholders
        
    Returns:
        Formatted topic string
    """
    return template.format(**kwargs)


def get_telemetry_topic(device_id: str, sensor_type: str) -> str:
    """
    Get telemetry topic for device and sensor
    
    Args:
        device_id: Device identifier
        sensor_type: Sensor type
        
    Returns:
        Telemetry topic
    """
    return format_topic(
        MQTT_TOPICS["telemetry"],
        device_id=device_id,
        sensor_type=sensor_type
    )


def get_heartbeat_topic(device_id: str) -> str:
    """
    Get heartbeat topic for device
    
    Args:
        device_id: Device identifier
        
    Returns:
        Heartbeat topic
    """
    return format_topic(
        MQTT_TOPICS["health"],
        device_id=device_id
    )


def get_status_topic(device_id: str) -> str:
    """
    Get status topic for device
    
    Args:
        device_id: Device identifier
        
    Returns:
        Status topic
    """
    return format_topic(
        MQTT_TOPICS["status"],
        device_id=device_id
    )


def get_alert_topic(device_id: str, alert_type: str) -> str:
    """
    Get alert topic for device
    
    Args:
        device_id: Device identifier
        alert_type: Type of alert
        
    Returns:
        Alert topic
    """
    return format_topic(
        MQTT_TOPICS["alerts"],
        device_id=device_id,
        alert_type=alert_type
    )


def get_command_topic(device_id: str, command: str) -> str:
    """
    Get command topic for device
    
    Args:
        device_id: Device identifier
        command: Command name
        
    Returns:
        Command topic
    """
    return format_topic(
        MQTT_TOPICS["commands"],
        device_id=device_id,
        command=command
    )


def parse_topic(topic: str) -> Dict[str, str]:
    """
    Parse MQTT topic into components
    
    Args:
        topic: MQTT topic string
        
    Returns:
        Dictionary with topic components
    """
    parts = topic.split('/')
    
    if len(parts) < 2:
        return {}
    
    result = {
        'namespace': parts[0],
        'category': parts[1] if len(parts) > 1 else None
    }
    
    # Parse based on category
    if result['category'] == 'telemetry' and len(parts) >= 4:
        result['device_id'] = parts[2]
        result['sensor_type'] = parts[3]
    elif result['category'] == 'health' and len(parts) >= 4:
        result['device_id'] = parts[2]
        result['message_type'] = parts[3]
    elif result['category'] == 'alerts' and len(parts) >= 4:
        result['device_id'] = parts[2]
        result['alert_type'] = parts[3]
    elif result['category'] == 'commands' and len(parts) >= 4:
        result['device_id'] = parts[2]
        result['command'] = parts[3]
    
    return result


def get_wildcard_topic(category: str, device_id: Optional[str] = None) -> str:
    """
    Get wildcard topic for subscribing to multiple topics
    
    Args:
        category: Topic category (telemetry, health, alerts, commands)
        device_id: Optional device filter
        
    Returns:
        Wildcard topic string
    """
    if device_id:
        return f"iot/{category}/{device_id}/#"
    else:
        return f"iot/{category}/#"
