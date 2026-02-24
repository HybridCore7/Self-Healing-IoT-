"""
Event Bus
Lightweight async pub/sub system for internal component communication.
Enables loose coupling between: MQTT layer, AI engine, Healing engine, and APIs.
"""
import asyncio
from collections import defaultdict
from typing import Callable, Dict, List, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EventBus:
    """
    Async publish-subscribe event bus.

    Usage:
        bus = get_event_bus()

        # Subscribe
        async def on_anomaly(data):
            print("Anomaly detected:", data)
        bus.subscribe("anomaly.detected", on_anomaly)

        # Publish
        await bus.publish("anomaly.detected", {"device_id": "d1", "score": 0.9})
    """

    # Well-known event topics
    TELEMETRY_RECEIVED  = "telemetry.received"
    ANOMALY_DETECTED    = "anomaly.detected"
    ANOMALY_RESOLVED    = "anomaly.resolved"
    HEALING_STARTED     = "healing.started"
    HEALING_COMPLETED   = "healing.completed"
    HEALING_FAILED      = "healing.failed"
    DEVICE_ONLINE       = "device.online"
    DEVICE_OFFLINE      = "device.offline"
    HEARTBEAT_RECEIVED  = "heartbeat.received"
    SYSTEM_ALERT        = "system.alert"

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_log: List[Dict[str, Any]] = []
        self._max_log_size = 500

    # ─────────────────────────────────────────────
    # Subscribe / Unsubscribe
    # ─────────────────────────────────────────────

    def subscribe(self, topic: str, handler: Callable):
        """Register a handler for a topic."""
        self._subscribers[topic].append(handler)
        logger.debug(f"EventBus: subscribed to '{topic}' → {handler.__name__}")

    def unsubscribe(self, topic: str, handler: Callable):
        """Remove a handler for a topic."""
        handlers = self._subscribers.get(topic, [])
        if handler in handlers:
            handlers.remove(handler)
            logger.debug(f"EventBus: unsubscribed from '{topic}' → {handler.__name__}")

    # ─────────────────────────────────────────────
    # Publish
    # ─────────────────────────────────────────────

    async def publish(self, topic: str, data: Any = None):
        """
        Publish an event on a topic.
        All registered handlers are called concurrently.
        """
        handlers = self._subscribers.get(topic, [])

        # Log the event
        import datetime
        event_record = {
            "topic": topic,
            "data": data,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "handler_count": len(handlers),
        }
        self._event_log.append(event_record)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]

        if not handlers:
            logger.debug(f"EventBus: no handlers for '{topic}'")
            return

        logger.debug(f"EventBus: publishing '{topic}' to {len(handlers)} handler(s)")

        # Call all handlers concurrently
        tasks = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(asyncio.create_task(handler(data)))
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"EventBus: error calling handler {handler.__name__} for '{topic}': {e}")

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"EventBus: handler task raised exception for '{topic}': {result}")

    def publish_sync(self, topic: str, data: Any = None):
        """Fire-and-forget publish from synchronous context."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.publish(topic, data))
            else:
                loop.run_until_complete(self.publish(topic, data))
        except RuntimeError:
            asyncio.run(self.publish(topic, data))

    # ─────────────────────────────────────────────
    # Introspection
    # ─────────────────────────────────────────────

    def get_topics(self) -> List[str]:
        """List all topics with subscribers."""
        return list(self._subscribers.keys())

    def get_subscriber_count(self, topic: str) -> int:
        return len(self._subscribers.get(topic, []))

    def get_recent_events(self, n: int = 50) -> List[Dict]:
        """Return the most recent n events from the event log."""
        return self._event_log[-n:]

    def clear_log(self):
        self._event_log.clear()

    def get_stats(self) -> Dict:
        return {
            "topics": len(self._subscribers),
            "total_subscribers": sum(len(v) for v in self._subscribers.values()),
            "events_logged": len(self._event_log),
        }


# Singleton
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus singleton."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
