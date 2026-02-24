"""
Sensor Simulator - Realistic sensor data generation with fault injection
"""
import random
import time
from typing import Optional, Dict
from datetime import datetime

from src.utils.constants import SensorType, SENSOR_RANGES
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SensorSimulator:
    """Simulates realistic sensor readings with noise and faults"""
    
    def __init__(
        self,
        sensor_type: SensorType,
        base_value: Optional[float] = None,
        noise_level: float = 0.05
    ):
        """
        Initialize sensor simulator
        
        Args:
            sensor_type: Type of sensor
            base_value: Base value for readings (defaults to mid-range)
            noise_level: Amount of noise to add (0-1)
        """
        self.sensor_type = sensor_type
        self.noise_level = noise_level
        
        # Get sensor range
        sensor_config = SENSOR_RANGES.get(sensor_type, {"min": 0, "max": 100, "unit": ""})
        self.min_value = sensor_config["min"]
        self.max_value = sensor_config["max"]
        self.unit = sensor_config["unit"]
        
        # Set base value
        if base_value is None:
            self.base_value = (self.min_value + self.max_value) / 2
        else:
            self.base_value = base_value
        
        self.current_value = self.base_value
        
        # Fault injection state
        self.fault_active = False
        self.fault_type = None
        self.stuck_value = None
        self.drift_rate = 0.0
        
        logger.debug(f"Initialized {sensor_type.value} sensor simulator")
    
    def read(self) -> float:
        """
        Generate sensor reading
        
        Returns:
            Sensor value
        """
        if self.fault_active:
            return self._generate_faulty_reading()
        else:
            return self._generate_normal_reading()
    
    def _generate_normal_reading(self) -> float:
        """Generate normal sensor reading with noise"""
        # Add random noise
        noise = random.gauss(0, self.noise_level * (self.max_value - self.min_value))
        
        # Add slight drift for realism
        drift = random.uniform(-0.01, 0.01)
        
        # Update current value
        self.current_value = self.current_value + drift + noise
        
        # Clamp to valid range
        self.current_value = max(self.min_value, min(self.max_value, self.current_value))
        
        return round(self.current_value, 2)
    
    def _generate_faulty_reading(self) -> float:
        """Generate faulty sensor reading based on fault type"""
        if self.fault_type == "stuck":
            return self.stuck_value
        
        elif self.fault_type == "drift":
            # Gradual drift
            self.current_value += self.drift_rate
            self.current_value = max(self.min_value, min(self.max_value, self.current_value))
            return round(self.current_value, 2)
        
        elif self.fault_type == "spike":
            # Random spikes
            if random.random() < 0.3:  # 30% chance of spike
                spike_value = random.uniform(self.max_value * 0.8, self.max_value * 1.2)
                return round(spike_value, 2)
            else:
                return self._generate_normal_reading()
        
        elif self.fault_type == "out_of_range":
            # Values outside normal range
            if random.random() < 0.5:
                return round(self.max_value * random.uniform(1.1, 1.5), 2)
            else:
                return round(self.min_value * random.uniform(0.5, 0.9), 2)
        
        else:
            return self._generate_normal_reading()
    
    def inject_fault(
        self,
        fault_type: str,
        **kwargs
    ):
        """
        Inject fault into sensor
        
        Args:
            fault_type: Type of fault (stuck, drift, spike, out_of_range)
            **kwargs: Fault-specific parameters
        """
        self.fault_active = True
        self.fault_type = fault_type
        
        if fault_type == "stuck":
            self.stuck_value = kwargs.get('value', self.current_value)
            logger.info(f"Injected stuck fault at value {self.stuck_value}")
        
        elif fault_type == "drift":
            self.drift_rate = kwargs.get('rate', 0.1)
            logger.info(f"Injected drift fault with rate {self.drift_rate}")
        
        elif fault_type == "spike":
            logger.info("Injected spike fault")
        
        elif fault_type == "out_of_range":
            logger.info("Injected out-of-range fault")
    
    def clear_fault(self):
        """Clear injected fault"""
        self.fault_active = False
        self.fault_type = None
        self.stuck_value = None
        self.drift_rate = 0.0
        self.current_value = self.base_value
        logger.info(f"Cleared fault for {self.sensor_type.value} sensor")
    
    def reset(self):
        """Reset sensor to base value"""
        self.current_value = self.base_value
        self.clear_fault()
        logger.debug(f"Reset {self.sensor_type.value} sensor")
    
    def get_info(self) -> Dict:
        """Get sensor information"""
        return {
            'sensor_type': self.sensor_type.value,
            'unit': self.unit,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'current_value': self.current_value,
            'fault_active': self.fault_active,
            'fault_type': self.fault_type
        }
