"""
Virtual IoT Node - Simulated IoT device with sensors and MQTT connectivity
"""
import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime

from src.simulator.sensor_simulator import SensorSimulator
from src.mqtt.publisher import get_publisher
from src.utils.constants import SensorType, DeviceStatus, DEFAULT_HEARTBEAT_INTERVAL, DEFAULT_TELEMETRY_INTERVAL
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VirtualNode:
    """Virtual IoT device with multiple sensors"""
    
    def __init__(
        self,
        device_id: str,
        device_name: str,
        device_type: str = "virtual",
        sensors: Optional[List[SensorType]] = None
    ):
        """
        Initialize virtual IoT node
        
        Args:
            device_id: Unique device identifier
            device_name: Human-readable device name
            device_type: Type of device
            sensors: List of sensor types to simulate
        """
        self.device_id = device_id
        self.device_name = device_name
        self.device_type = device_type
        self.status = DeviceStatus.OFFLINE
        
        # Initialize sensors
        if sensors is None:
            sensors = [SensorType.TEMPERATURE, SensorType.HUMIDITY]
        
        self.sensors: Dict[SensorType, SensorSimulator] = {}
        for sensor_type in sensors:
            self.sensors[sensor_type] = SensorSimulator(sensor_type)
        
        # Timing
        self.heartbeat_interval = DEFAULT_HEARTBEAT_INTERVAL
        self.telemetry_interval = DEFAULT_TELEMETRY_INTERVAL
        self.start_time = time.time()
        
        # Running state
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
        # Publisher
        self.publisher = get_publisher()
        
        logger.info(f"Initialized virtual node: {device_id} ({device_name})")
    
    async def start(self):
        """Start the virtual device"""
        if self.running:
            logger.warning(f"Device {self.device_id} is already running")
            return
        
        self.running = True
        self.status = DeviceStatus.ONLINE
        self.start_time = time.time()
        
        # Start background tasks
        self.tasks = [
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._telemetry_loop())
        ]
        
        logger.info(f"Started virtual device: {self.device_id}")
    
    async def stop(self):
        """Stop the virtual device"""
        self.running = False
        self.status = DeviceStatus.OFFLINE
        
        # Cancel background tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        
        logger.info(f"Stopped virtual device: {self.device_id}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages"""
        while self.running:
            try:
                uptime = int(time.time() - self.start_time)
                
                metadata = {
                    'uptime_seconds': uptime,
                    'device_name': self.device_name,
                    'device_type': self.device_type,
                    'sensor_count': len(self.sensors)
                }
                
                self.publisher.publish_heartbeat(
                    self.device_id,
                    status=self.status.value,
                    metadata=metadata
                )
                
                await asyncio.sleep(self.heartbeat_interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop for {self.device_id}: {e}")
                await asyncio.sleep(self.heartbeat_interval)
    
    async def _telemetry_loop(self):
        """Send periodic telemetry data"""
        while self.running:
            try:
                # Read and publish data from all sensors
                for sensor_type, sensor in self.sensors.items():
                    value = sensor.read()
                    
                    self.publisher.publish_telemetry(
                        self.device_id,
                        sensor_type.value,
                        value,
                        unit=sensor.unit
                    )
                
                await asyncio.sleep(self.telemetry_interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in telemetry loop for {self.device_id}: {e}")
                await asyncio.sleep(self.telemetry_interval)
    
    def inject_sensor_fault(
        self,
        sensor_type: SensorType,
        fault_type: str,
        **kwargs
    ):
        """
        Inject fault into specific sensor
        
        Args:
            sensor_type: Type of sensor
            fault_type: Type of fault
            **kwargs: Fault parameters
        """
        if sensor_type in self.sensors:
            self.sensors[sensor_type].inject_fault(fault_type, **kwargs)
            logger.info(f"Injected {fault_type} fault into {sensor_type.value} sensor on device {self.device_id}")
        else:
            logger.warning(f"Sensor {sensor_type.value} not found on device {self.device_id}")
    
    def clear_sensor_fault(self, sensor_type: SensorType):
        """Clear fault from specific sensor"""
        if sensor_type in self.sensors:
            self.sensors[sensor_type].clear_fault()
            logger.info(f"Cleared fault from {sensor_type.value} sensor on device {self.device_id}")
    
    def clear_all_faults(self):
        """Clear faults from all sensors"""
        for sensor in self.sensors.values():
            sensor.clear_fault()
        logger.info(f"Cleared all faults from device {self.device_id}")
    
    def get_status(self) -> Dict:
        """Get device status information"""
        uptime = int(time.time() - self.start_time) if self.running else 0
        
        sensor_info = {
            sensor_type.value: sensor.get_info()
            for sensor_type, sensor in self.sensors.items()
        }
        
        return {
            'device_id': self.device_id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'status': self.status.value,
            'uptime_seconds': uptime,
            'running': self.running,
            'sensors': sensor_info
        }
