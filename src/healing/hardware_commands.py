"""
Hardware Healing Command Dispatcher
=====================================
Sends specific healing commands to physical hardware devices via MQTT.

This is what runs when the AI engine decides a physical device needs healing.
Each device type gets the right command for its capabilities.
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ── Healing Action → MQTT Command Mapping ──────────────────────────
# Maps AI healing decisions to actual commands understood by hardware
HEALING_COMMANDS = {
    # Action name          → command sent to device
    "restart_device":       "reset",
    "reset_sensor":         "recalibrate",
    "recalibrate":          "recalibrate",
    "increase_frequency":   "increase_frequency",
    "validate_readings":    "validate",
    "ping":                 "ping",
    "request_diagnostic":   "diagnostic",
}

# Commands by fault type
FAULT_TO_COMMAND = {
    "sensor_drift":    "recalibrate",
    "stuck_sensor":    "reset",
    "data_spike":      "validate",
    "offline":         "ping",
    "high_frequency":  "recalibrate",
    "frozen":          "reset",
    "noise":           "validate",
}

# Device type capabilities — some devices can't do all commands
DEVICE_CAPABILITIES = {
    "esp32":         {"reset", "recalibrate", "validate", "increase_frequency", "ping", "diagnostic"},
    "raspberry_pi":  {"reset", "recalibrate", "validate", "increase_frequency", "ping", "diagnostic"},
    "arduino":       {"reset", "recalibrate", "validate", "ping"},
    "unknown":       {"ping", "validate"},
}


class HardwareCommandDispatcher:
    """
    Dispatches healing commands to real hardware devices over MQTT.
    Called by the healing orchestrator when a fault is confirmed.
    """

    def __init__(self, mqtt_client=None):
        self.mqtt_client = mqtt_client
        self._command_log: list = []

    def set_mqtt_client(self, client):
        self.mqtt_client = client

    # ─────────────────────────────────────────────
    # Main dispatcher
    # ─────────────────────────────────────────────

    def dispatch_healing(self, device_id: str, fault_type: str,
                         device_type: str = "unknown",
                         extra_params: Dict[str, Any] = None) -> dict:
        """
        Choose and send the right healing command for a fault.

        Args:
            device_id   : Target device ID
            fault_type  : What went wrong ("sensor_drift", "stuck_sensor", etc.)
            device_type : "esp32", "arduino", "raspberry_pi", "unknown"
            extra_params: Extra parameters to include in command payload

        Returns:
            dict with command, topic, success status
        """
        # Determine command from fault type
        raw_command = FAULT_TO_COMMAND.get(fault_type, "validate")

        # Check device supports this command
        capabilities = DEVICE_CAPABILITIES.get(device_type, DEVICE_CAPABILITIES["unknown"])
        if raw_command not in capabilities:
            # Fall back to the safest supported command
            raw_command = "validate" if "validate" in capabilities else "ping"
            logger.warning(f"Device {device_id} ({device_type}) doesn't support "
                           f"'{raw_command}' — falling back to '{raw_command}'")

        result = self.send_command(
            device_id=device_id,
            command=raw_command,
            healing_reason=fault_type,
            params=extra_params or {}
        )

        logger.info(
            f"🔧 Healing dispatched to {device_id} | "
            f"fault={fault_type} | cmd={raw_command} | "
            f"sent={'✅' if result['success'] else '❌'}"
        )
        return result

    def send_command(self, device_id: str, command: str,
                     healing_reason: str = "",
                     params: Dict[str, Any] = None) -> dict:
        """Send a specific command to a device via MQTT."""
        topic   = f"iot/commands/{device_id}/{command}"
        payload = {
            "command":        command,
            "device_id":      device_id,
            "healing_reason": healing_reason,
            "parameters":     params or {},
            "issued_at":      datetime.utcnow().isoformat(),
            "issued_by":      "self_healing_ai",
        }
        payload_json = json.dumps(payload)
        success      = False

        if self.mqtt_client:
            try:
                self.mqtt_client.publish(topic, payload_json)
                success = True
                logger.debug(f"Published to {topic}: {payload_json}")
            except Exception as e:
                logger.error(f"Failed to publish command: {e}")
        else:
            logger.warning("No MQTT client — command not sent (set via set_mqtt_client())")

        # Log command
        entry = {
            "device_id":  device_id,
            "command":    command,
            "topic":      topic,
            "reason":     healing_reason,
            "success":    success,
            "timestamp":  datetime.utcnow().isoformat(),
        }
        self._command_log.append(entry)
        return {**entry, "payload": payload}

    # ─────────────────────────────────────────────
    # Convenience senders
    # ─────────────────────────────────────────────

    def send_ping(self, device_id: str) -> dict:
        return self.send_command(device_id, "ping", "liveness_check")

    def send_reset(self, device_id: str, reason: str = "ai_triggered") -> dict:
        return self.send_command(device_id, "reset", reason)

    def send_recalibrate(self, device_id: str) -> dict:
        return self.send_command(device_id, "recalibrate", "sensor_drift_detected")

    def send_validate(self, device_id: str, sample_count: int = 5) -> dict:
        return self.send_command(device_id, "validate", "anomaly_confirmation",
                                 params={"sample_count": sample_count})

    def send_increase_frequency(self, device_id: str) -> dict:
        return self.send_command(device_id, "increase_frequency", "post_healing_monitoring",
                                 params={"duration_seconds": 60})

    def broadcast_alert(self, message: str, severity: str = "warning"):
        """Broadcast system-wide alert to all devices."""
        if self.mqtt_client:
            payload = json.dumps({
                "type":      "alert",
                "message":   message,
                "severity":  severity,
                "timestamp": datetime.utcnow().isoformat(),
            })
            self.mqtt_client.publish("iot/system/alert", payload)

    # ─────────────────────────────────────────────
    # Introspection
    # ─────────────────────────────────────────────

    def get_command_log(self, limit: int = 50) -> list:
        return self._command_log[-limit:]

    def get_stats(self) -> dict:
        total   = len(self._command_log)
        success = sum(1 for c in self._command_log if c["success"])
        return {
            "total_commands": total,
            "successful":     success,
            "failed":         total - success,
            "success_rate":   (success / total * 100) if total else 100.0,
        }


# Singleton
_dispatcher: Optional[HardwareCommandDispatcher] = None


def get_dispatcher(mqtt_client=None) -> HardwareCommandDispatcher:
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = HardwareCommandDispatcher(mqtt_client)
    elif mqtt_client:
        _dispatcher.set_mqtt_client(mqtt_client)
    return _dispatcher
