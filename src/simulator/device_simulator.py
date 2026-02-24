"""
Device Simulator - Main orchestrator for multiple virtual devices
"""
import asyncio
from typing import List, Dict, Optional
import random

from src.simulator.virtual_node import VirtualNode
from src.utils.constants import SensorType
from src.utils.logger import get_logger
from src.mqtt.client import initialize_mqtt_client

logger = get_logger(__name__)


class DeviceSimulator:
    """Orchestrates multiple virtual IoT devices"""
    
    def __init__(self, num_devices: int = 3):
        """
        Initialize device simulator
        
        Args:
            num_devices: Number of virtual devices to create
        """
        self.num_devices = num_devices
        self.devices: Dict[str, VirtualNode] = {}
        self.running = False
        
        logger.info(f"Initializing device simulator with {num_devices} devices")
    
    def create_devices(self):
        """Create virtual devices"""
        device_configs = [
            {
                'device_id': f'device_{i:03d}',
                'device_name': f'IoT Node {i}',
                'device_type': 'environmental_sensor',
                'sensors': [SensorType.TEMPERATURE, SensorType.HUMIDITY]
            }
            for i in range(1, self.num_devices + 1)
        ]
        
        # Add some variety
        if self.num_devices > 2:
            device_configs[2]['sensors'].append(SensorType.LIGHT)
        
        if self.num_devices > 3:
            device_configs[3]['sensors'] = [SensorType.GAS, SensorType.TEMPERATURE]
        
        for config in device_configs:
            device = VirtualNode(**config)
            self.devices[config['device_id']] = device
        
        logger.info(f"Created {len(self.devices)} virtual devices")
    
    async def start_all(self):
        """Start all virtual devices"""
        if not self.devices:
            self.create_devices()
        
        self.running = True
        
        # Start all devices
        tasks = [device.start() for device in self.devices.values()]
        await asyncio.gather(*tasks)
        
        logger.info("All virtual devices started")
    
    async def stop_all(self):
        """Stop all virtual devices"""
        self.running = False
        
        # Stop all devices
        tasks = [device.stop() for device in self.devices.values()]
        await asyncio.gather(*tasks)
        
        logger.info("All virtual devices stopped")
    
    def get_device(self, device_id: str) -> Optional[VirtualNode]:
        """Get device by ID"""
        return self.devices.get(device_id)
    
    def list_devices(self) -> List[Dict]:
        """List all devices with their status"""
        return [device.get_status() for device in self.devices.values()]
    
    def inject_random_fault(self):
        """Inject random fault into random device"""
        if not self.devices:
            logger.warning("No devices available for fault injection")
            return
        
        # Select random device
        device_id = random.choice(list(self.devices.keys()))
        device = self.devices[device_id]
        
        # Select random sensor
        sensor_types = list(device.sensors.keys())
        if not sensor_types:
            return
        
        sensor_type = random.choice(sensor_types)
        
        # Select random fault type
        fault_types = ['stuck', 'drift', 'spike', 'out_of_range']
        fault_type = random.choice(fault_types)
        
        # Inject fault
        if fault_type == 'stuck':
            device.inject_sensor_fault(sensor_type, fault_type, value=random.uniform(0, 100))
        elif fault_type == 'drift':
            device.inject_sensor_fault(sensor_type, fault_type, rate=random.uniform(0.1, 0.5))
        else:
            device.inject_sensor_fault(sensor_type, fault_type)
        
        logger.info(f"Injected {fault_type} fault into {sensor_type.value} on {device_id}")
    
    async def run_with_periodic_faults(self, fault_interval: int = 60):
        """
        Run simulator with periodic random fault injection
        
        Args:
            fault_interval: Seconds between fault injections
        """
        await self.start_all()
        
        try:
            while self.running:
                await asyncio.sleep(fault_interval)
                
                if self.running:
                    self.inject_random_fault()
        
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop_all()


async def main():
    """Main entry point for device simulator"""
    logger.info("Starting IoT Device Simulator")
    
    # Initialize MQTT client
    mqtt_client = initialize_mqtt_client()
    
    # Wait for MQTT connection
    await asyncio.sleep(2)
    
    if not mqtt_client.is_connected():
        logger.error("Failed to connect to MQTT broker")
        return
    
    # Create and run simulator
    simulator = DeviceSimulator(num_devices=5)
    
    try:
        # Run with periodic fault injection (every 120 seconds)
        await simulator.run_with_periodic_faults(fault_interval=120)
    
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await simulator.stop_all()
        mqtt_client.disconnect()
        logger.info("Device simulator stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Simulator terminated by user")
