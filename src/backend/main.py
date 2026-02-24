"""
FastAPI Backend Server - Main Entry Point
Handles REST API, MQTT integration, and coordinates the self-healing system
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config.settings import settings
from src.utils.logger import get_logger
from src.backend.api import devices, telemetry, anomalies, healing, health
from src.backend.api import hardware as hardware_api

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle management for FastAPI application
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting Self-Healing IoT Backend Server...")
    logger.info(f"Debug Mode: {settings.debug_mode}")
    logger.info(f"MQTT Broker: {settings.mqtt_broker_host}:{settings.mqtt_broker_port}")
    
    # Initialize database connection
    from src.database.db_manager import get_db_manager
    db_manager = await get_db_manager()
    logger.info("✓ Database initialized")
    
    # Initialize MQTT client and subscribers
    from src.mqtt.client import initialize_mqtt_client
    from src.mqtt.subscriber import get_subscriber
    from src.mqtt.device_discovery import get_device_registry, DiscoveryHandler
    from src.healing.hardware_commands import get_dispatcher
    import asyncio
    
    mqtt_client = initialize_mqtt_client()
    
    # Wire up device discovery
    registry  = get_device_registry()
    registry.set_db(db_manager)
    discovery = DiscoveryHandler(registry, mqtt_client)
    app.state.discovery = discovery
    app.state.registry  = registry
    logger.info("✓ Device auto-discovery ready")

    # Wire up hardware command dispatcher
    dispatcher = get_dispatcher(mqtt_client)
    app.state.dispatcher = dispatcher
    logger.info("✓ Hardware command dispatcher ready")
    
    # Wait for MQTT connection with retries
    max_retries = 10
    for i in range(max_retries):
        await asyncio.sleep(1)
        if mqtt_client.is_connected():
            logger.info("✓ MQTT client connected")
            break
        logger.debug(f"Waiting for MQTT connection... ({i+1}/{max_retries})")
    else:
        logger.warning("MQTT connection timeout, continuing anyway")
    
    logger.info("✓ MQTT client initialized")
    
    # Set up message handlers
    from src.database.repositories.telemetry_repo import TelemetryRepository
    from src.database.repositories.device_repo import DeviceRepository
    from src.database.repositories.anomaly_repo import AnomalyRepository
    from src.ai.anomaly_detector import get_anomaly_detector
    from src.utils.constants import SensorType, AnomalyType, Severity
    
    subscriber = get_subscriber()
    anomaly_detector = get_anomaly_detector()
    telemetry_repo = TelemetryRepository(db_manager)
    device_repo = DeviceRepository(db_manager)
    anomaly_repo = AnomalyRepository(db_manager)
    
    async def handle_telemetry(message: dict):
        try:
            device_id = message.get('device_id')
            sensor_type = message.get('sensor_type')
            value = message.get('value')
            unit = message.get('unit')
            
            if device_id and sensor_type and value is not None:
                # Auto-register device if it doesn't exist
                existing_device = await device_repo.get_device(device_id)
                if not existing_device:
                    from src.backend.models.device import DeviceCreate
                    from src.utils.constants import DeviceType
                    
                    device_data = DeviceCreate(
                        device_id=device_id,
                        device_name=f"Auto-registered {device_id}",
                        device_type=DeviceType.CUSTOM,
                        location="Unknown",
                        metadata={"auto_registered": True, "source": "mqtt"}
                    )
                    await device_repo.create_device(device_data)
                    logger.info(f"Auto-registered device from MQTT: {device_id}")
                
                sensor_type_enum = SensorType(sensor_type)
                is_anomaly, anomaly_score = anomaly_detector.predict(device_id, sensor_type_enum, value)
                await telemetry_repo.insert_telemetry(device_id, sensor_type, value, unit, is_anomaly)
                
                if is_anomaly:
                    await anomaly_repo.create_anomaly(
                        device_id, AnomalyType.SENSOR_FAULT, Severity.MEDIUM,
                        sensor_type=sensor_type, anomaly_score=anomaly_score
                    )
        except Exception as e:
            logger.error(f"Error handling telemetry: {e}")
    
    async def handle_heartbeat(message: dict):
        try:
            device_id = message.get('device_id')
            if device_id:
                await device_repo.update_heartbeat(device_id)
        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}")
    
    # Subscribe to MQTT topics
    subscriber.subscribe_to_telemetry(lambda msg: asyncio.create_task(handle_telemetry(msg)))
    subscriber.subscribe_to_heartbeats(lambda msg: asyncio.create_task(handle_heartbeat(msg)))
    logger.info("✓ MQTT subscriptions configured")
    
    # Start healing orchestrator
    from src.healing.orchestrator import get_healing_orchestrator
    orchestrator = get_healing_orchestrator()
    await orchestrator.start()
    logger.info("✓ Healing orchestrator started")
    
    logger.info("🚀 Self-Healing IoT Backend Server ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Self-Healing IoT Backend Server...")
    
    await orchestrator.stop()
    logger.info("✓ Healing orchestrator stopped")
    
    mqtt_client.disconnect()
    logger.info("✓ MQTT client disconnected")
    
    await db_manager.disconnect()
    logger.info("✓ Database disconnected")
    
    logger.info("👋 Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Self-Healing IoT System API",
    description="REST API for AI-enabled autonomous fault detection and recovery in IoT systems",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(devices.router,      prefix="/api/devices",   tags=["Devices"])
app.include_router(telemetry.router,    prefix="/api/telemetry", tags=["Telemetry"])
app.include_router(anomalies.router,    prefix="/api/anomalies", tags=["Anomalies"])
app.include_router(healing.router,      prefix="/api/healing",   tags=["Healing"])
app.include_router(health.router,       prefix="/api/health",    tags=["System Health"])
app.include_router(hardware_api.router)  # /api/hardware — real device management


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "Self-Healing IoT System",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


def main():
    """Run the FastAPI application"""
    uvicorn.run(
        "src.backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug_mode,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
