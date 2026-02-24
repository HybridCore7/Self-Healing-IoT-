"""
System Manager
High-level orchestrator for all Self-Healing IoT System components.
Handles startup, shutdown, and inter-component coordination.
"""
import asyncio
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SystemManager:
    """
    Top-level system coordinator.
    Manages lifecycle of: Database, MQTT, AnomalyDetector, HealingOrchestrator.
    """

    def __init__(self):
        self._running = False
        self._db_manager = None
        self._mqtt_client = None
        self._healing_orchestrator = None
        self._anomaly_detector = None

    # ─────────────────────────────────────────────
    # Startup
    # ─────────────────────────────────────────────

    async def start(self):
        """Initialize and start all subsystems in order."""
        logger.info("=== Self-Healing IoT System Starting ===")

        await self._init_database()
        await self._init_mqtt()
        await self._init_ai()
        await self._init_healing()

        self._running = True
        logger.info("=== All subsystems started successfully ===")

    async def _init_database(self):
        from src.database.db_manager import get_db_manager
        self._db_manager = await get_db_manager()
        logger.info("✓ Database initialized")

    async def _init_mqtt(self):
        from src.mqtt.client import initialize_mqtt_client
        self._mqtt_client = initialize_mqtt_client()

        # Wait for connection
        for i in range(10):
            await asyncio.sleep(1)
            if self._mqtt_client.is_connected():
                logger.info("✓ MQTT client connected")
                return
            logger.debug(f"Waiting for MQTT... ({i + 1}/10)")

        logger.warning("MQTT connection timeout - continuing without MQTT")

    async def _init_ai(self):
        from src.ai.anomaly_detector import get_anomaly_detector
        self._anomaly_detector = get_anomaly_detector()
        logger.info("✓ Anomaly detector initialized")

    async def _init_healing(self):
        from src.healing.orchestrator import get_healing_orchestrator
        self._healing_orchestrator = get_healing_orchestrator()
        await self._healing_orchestrator.start()
        logger.info("✓ Healing orchestrator started")

    # ─────────────────────────────────────────────
    # Shutdown
    # ─────────────────────────────────────────────

    async def stop(self):
        """Gracefully stop all subsystems."""
        logger.info("=== Self-Healing IoT System Shutting Down ===")
        self._running = False

        if self._healing_orchestrator:
            await self._healing_orchestrator.stop()
            logger.info("✓ Healing orchestrator stopped")

        if self._mqtt_client:
            self._mqtt_client.disconnect()
            logger.info("✓ MQTT client disconnected")

        if self._db_manager:
            await self._db_manager.disconnect()
            logger.info("✓ Database disconnected")

        logger.info("=== Shutdown complete ===")

    # ─────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────

    def get_status(self) -> dict:
        """Return current status of all components."""
        mqtt_connected = self._mqtt_client.is_connected() if self._mqtt_client else False
        healing_status = self._healing_orchestrator.get_status() if self._healing_orchestrator else {}

        return {
            "running": self._running,
            "database": "connected" if self._db_manager else "disconnected",
            "mqtt": "connected" if mqtt_connected else "disconnected",
            "anomaly_detector": "active" if self._anomaly_detector else "inactive",
            "healing_orchestrator": healing_status.get('running', False),
        }

    @property
    def is_running(self) -> bool:
        return self._running


# Singleton
_system_manager: Optional[SystemManager] = None


def get_system_manager() -> SystemManager:
    global _system_manager
    if _system_manager is None:
        _system_manager = SystemManager()
    return _system_manager
