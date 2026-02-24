"""
Device Auto-Discovery Service
==============================
Listens to MQTT heartbeat topic and automatically registers
any new devices that appear on the network.

Supports: ESP32, Raspberry Pi, Arduino (via bridge), any custom device.

MQTT Topics consumed:
  iot/health/+/heartbeat  — Device announces itself
  iot/status/+            — Status updates
  iot/telemetry/+/+       — Seen for first time → register

MQTT Topics emitted:
  iot/system/device_registered  — Broadcast when new device found
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────
# Device Registry (in-memory + DB)
# ─────────────────────────────────────────────
class DeviceRegistry:
    """
    Tracks all discovered devices and their last-seen timestamps.
    Auto-registers new devices when they first send a heartbeat or telemetry.
    """

    OFFLINE_TIMEOUT_SECONDS = 60   # Mark device offline after 60s of silence

    def __init__(self):
        self._known_devices: Dict[str, dict]  = {}   # device_id → info
        self._last_seen: Dict[str, datetime]  = {}   # device_id → timestamp
        self._db_manager = None

    def set_db(self, db_manager):
        self._db_manager = db_manager

    async def on_heartbeat(self, device_id: str, payload: dict) -> bool:
        """
        Called when a heartbeat arrives.
        Returns True if this is a newly discovered device.
        """
        is_new = device_id not in self._known_devices

        info = {
            "device_id":   device_id,
            "device_name": payload.get("device_name", device_id),
            "device_type": payload.get("device_type", "unknown"),
            "location":    payload.get("location", "unknown"),
            "ip":          payload.get("ip", ""),
            "mac":         payload.get("mac", ""),
            "status":      "online",
            "rssi":        payload.get("rssi", None),
            "last_seen":   datetime.utcnow().isoformat(),
            "registered_at": (
                self._known_devices.get(device_id, {}).get("registered_at")
                or datetime.utcnow().isoformat()
            ),
        }

        self._known_devices[device_id] = info
        self._last_seen[device_id]     = datetime.utcnow()

        if is_new:
            logger.info(f"✨ NEW DEVICE DISCOVERED: {device_id} "
                        f"({info['device_type']} @ {info['location']})")
            await self._register_in_db(info)

        return is_new

    async def on_telemetry(self, device_id: str, payload: dict) -> bool:
        """Called when telemetry arrives from an unknown device."""
        if device_id in self._known_devices:
            self._last_seen[device_id] = datetime.utcnow()
            return False

        # First time we see this device — register with minimal info
        info = {
            "device_id":    device_id,
            "device_name":  payload.get("device_name", device_id),
            "device_type":  payload.get("device_type", "unknown"),
            "location":     payload.get("location", "unknown"),
            "status":       "online",
            "last_seen":    datetime.utcnow().isoformat(),
            "registered_at": datetime.utcnow().isoformat(),
        }
        self._known_devices[device_id] = info
        self._last_seen[device_id]     = datetime.utcnow()
        logger.info(f"✨ Device auto-discovered from telemetry: {device_id}")
        await self._register_in_db(info)
        return True

    async def _register_in_db(self, info: dict):
        """Persist device to database."""
        if not self._db_manager:
            return
        try:
            from src.database.repositories.device_repo import DeviceRepository
            repo = DeviceRepository(self._db_manager)
            existing = await repo.get_device(info["device_id"])
            if not existing:
                await repo.create_device(info)
                logger.info(f"Device {info['device_id']} saved to database")
        except Exception as e:
            logger.warning(f"Could not save device to DB: {e}")

    async def check_offline_devices(self):
        """Background task — mark devices offline if no heartbeat received."""
        threshold = datetime.utcnow() - timedelta(seconds=self.OFFLINE_TIMEOUT_SECONDS)
        for device_id, last_seen in self._last_seen.items():
            if last_seen < threshold:
                info = self._known_devices.get(device_id, {})
                if info.get("status") != "offline":
                    info["status"] = "offline"
                    logger.warning(f"⚫ Device {device_id} went OFFLINE "
                                   f"(last seen: {last_seen.isoformat()})")

    def get_all_devices(self) -> list:
        """Return all known devices with current status."""
        now = datetime.utcnow()
        result = []
        for device_id, info in self._known_devices.items():
            last_seen = self._last_seen.get(device_id, datetime.min)
            seconds_ago = (now - last_seen).total_seconds()
            status = "online" if seconds_ago < self.OFFLINE_TIMEOUT_SECONDS else "offline"
            result.append({**info, "status": status, "seconds_since_seen": seconds_ago})
        return result

    def get_device(self, device_id: str) -> Optional[dict]:
        info = self._known_devices.get(device_id)
        if not info:
            return None
        last_seen = self._last_seen.get(device_id, datetime.min)
        seconds_ago = (datetime.utcnow() - last_seen).total_seconds()
        status = "online" if seconds_ago < self.OFFLINE_TIMEOUT_SECONDS else "offline"
        return {**info, "status": status, "seconds_since_seen": seconds_ago}

    def is_online(self, device_id: str) -> bool:
        g = self.get_device(device_id)
        return g is not None and g["status"] == "online"

    def get_stats(self) -> dict:
        all_devs = self.get_all_devices()
        return {
            "total":   len(all_devs),
            "online":  sum(1 for d in all_devs if d["status"] == "online"),
            "offline": sum(1 for d in all_devs if d["status"] == "offline"),
            "by_type": {},
        }

    def update_status(self, device_id: str, status: str):
        if device_id in self._known_devices:
            self._known_devices[device_id]["status"] = status


# ─────────────────────────────────────────────
# Discovery MQTT Handler (plugs into mqtt/subscriber.py)
# ─────────────────────────────────────────────
class DiscoveryHandler:
    """
    Plugs into the existing MQTT subscriber.
    Call handle_message() for every incoming MQTT message.
    """

    def __init__(self, registry: DeviceRegistry, mqtt_client=None):
        self.registry    = registry
        self.mqtt_client = mqtt_client
        self._loop       = None

    def handle_message(self, topic: str, payload_bytes: bytes):
        """Synchronous entry point — schedules async handler on event loop."""
        try:
            payload = json.loads(payload_bytes.decode())
        except Exception:
            return

        device_id = payload.get("device_id")
        if not device_id:
            # Try to extract from topic: iot/telemetry/{device_id}/{sensor}
            parts = topic.split("/")
            if len(parts) >= 3:
                device_id = parts[2]
            else:
                return

        # Schedule coroutine on the running event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                if "heartbeat" in topic:
                    loop.create_task(self.registry.on_heartbeat(device_id, payload))
                elif "telemetry" in topic:
                    loop.create_task(self.registry.on_telemetry(device_id, payload))
                elif "status" in topic:
                    self._handle_status(device_id, payload)
        except RuntimeError:
            pass

    def _handle_status(self, device_id: str, payload: dict):
        event = payload.get("event", "")
        if event in ("resetting", "offline"):
            self.registry.update_status(device_id, "offline")
        elif event in ("online", "pong", "recalibrated", "validated"):
            self.registry.update_status(device_id, "online")
            self._last_seen_update(device_id)

    def _last_seen_update(self, device_id: str):
        if device_id in self.registry._last_seen:
            self.registry._last_seen[device_id] = datetime.utcnow()

    def broadcast_new_device(self, device_id: str, info: dict):
        """Broadcast discovery event so dashboard can react."""
        if self.mqtt_client:
            payload = json.dumps({
                "event":     "device_registered",
                "device_id": device_id,
                "info":      info,
                "timestamp": datetime.utcnow().isoformat(),
            })
            self.mqtt_client.publish("iot/system/device_registered", payload)


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────
_registry: Optional[DeviceRegistry] = None


def get_device_registry() -> DeviceRegistry:
    global _registry
    if _registry is None:
        _registry = DeviceRegistry()
    return _registry
