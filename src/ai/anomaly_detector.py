"""
Anomaly Detector - Machine learning based anomaly detection using Isolation Forest
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from typing import List, Dict, Optional, Tuple
from collections import deque
import pickle
from pathlib import Path

from config.settings import settings
from src.utils.constants import SensorType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AnomalyDetector:
    """Isolation Forest based anomaly detector for sensor data"""
    
    def __init__(
        self,
        sensor_type: SensorType,
        window_size: int = None,
        contamination: float = None
    ):
        """
        Initialize anomaly detector
        
        Args:
            sensor_type: Type of sensor
            window_size: Number of samples for sliding window
            contamination: Expected proportion of anomalies
        """
        self.sensor_type = sensor_type
        self.window_size = window_size or settings.anomaly_window_size
        self.contamination = contamination or settings.anomaly_contamination
        
        # Initialize model
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        
        # Data buffer for sliding window
        self.data_buffer = deque(maxlen=self.window_size)
        
        # Training state
        self.is_trained = False
        self.training_data: List[float] = []
        
        logger.info(f"Initialized anomaly detector for {sensor_type.value}")
    
    def add_sample(self, value: float):
        """
        Add sample to data buffer
        
        Args:
            value: Sensor reading
        """
        self.data_buffer.append(value)
        
        # Also add to training data if not trained
        if not self.is_trained:
            self.training_data.append(value)
    
    def train(self, data: Optional[List[float]] = None) -> bool:
        """
        Train the anomaly detection model
        
        Args:
            data: Training data (uses buffered data if not provided)
            
        Returns:
            True if training successful
        """
        if data is None:
            data = self.training_data
        
        if len(data) < self.window_size:
            logger.warning(f"Insufficient data for training: {len(data)} < {self.window_size}")
            return False
        
        # Reshape data for sklearn
        X = np.array(data).reshape(-1, 1)
        
        try:
            self.model.fit(X)
            self.is_trained = True
            logger.info(f"Trained anomaly detector for {self.sensor_type.value} with {len(data)} samples")
            return True
        except Exception as e:
            logger.error(f"Error training anomaly detector: {e}")
            return False
    
    def predict(self, value: float) -> Tuple[bool, float]:
        """
        Predict if value is anomalous
        
        Args:
            value: Sensor reading
            
        Returns:
            Tuple of (is_anomaly, anomaly_score)
        """
        if not self.is_trained:
            # Auto-train if we have enough data
            if len(self.training_data) >= self.window_size:
                self.train()
            else:
                return False, 0.0
        
        # Reshape for prediction
        X = np.array([[value]])
        
        try:
            # Predict (-1 for anomaly, 1 for normal)
            prediction = self.model.predict(X)[0]
            
            # Get anomaly score (lower is more anomalous)
            score = self.model.score_samples(X)[0]
            
            # Convert to 0-1 range (higher is more anomalous)
            # Normalize score to approximate probability
            anomaly_score = 1.0 / (1.0 + np.exp(score))
            
            is_anomaly = prediction == -1
            
            return is_anomaly, float(anomaly_score)
        
        except Exception as e:
            logger.error(f"Error predicting anomaly: {e}")
            return False, 0.0
    
    def predict_batch(self, values: List[float]) -> List[Tuple[bool, float]]:
        """
        Predict anomalies for batch of values
        
        Args:
            values: List of sensor readings
            
        Returns:
            List of (is_anomaly, anomaly_score) tuples
        """
        if not self.is_trained:
            return [(False, 0.0)] * len(values)
        
        X = np.array(values).reshape(-1, 1)
        
        try:
            predictions = self.model.predict(X)
            scores = self.model.score_samples(X)
            
            results = []
            for pred, score in zip(predictions, scores):
                is_anomaly = pred == -1
                anomaly_score = 1.0 / (1.0 + np.exp(score))
                results.append((is_anomaly, float(anomaly_score)))
            
            return results
        
        except Exception as e:
            logger.error(f"Error in batch prediction: {e}")
            return [(False, 0.0)] * len(values)
    
    def get_statistics(self) -> Dict:
        """Get detector statistics"""
        return {
            'sensor_type': self.sensor_type.value,
            'is_trained': self.is_trained,
            'window_size': self.window_size,
            'contamination': self.contamination,
            'buffer_size': len(self.data_buffer),
            'training_samples': len(self.training_data)
        }
    
    def save_model(self, filepath: Optional[str] = None):
        """
        Save model to file
        
        Args:
            filepath: Path to save model (defaults to models directory)
        """
        if not self.is_trained:
            logger.warning("Cannot save untrained model")
            return
        
        if filepath is None:
            models_dir = Path("models")
            models_dir.mkdir(exist_ok=True)
            filepath = models_dir / f"anomaly_detector_{self.sensor_type.value}.pkl"
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info(f"Saved model to {filepath}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self, filepath: str) -> bool:
        """
        Load model from file
        
        Args:
            filepath: Path to model file
            
        Returns:
            True if loaded successfully
        """
        try:
            with open(filepath, 'rb') as f:
                self.model = pickle.load(f)
            self.is_trained = True
            logger.info(f"Loaded model from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False


class MultiSensorAnomalyDetector:
    """Manages anomaly detectors for multiple sensors"""
    
    def __init__(self):
        self.detectors: Dict[str, AnomalyDetector] = {}
        logger.info("Initialized multi-sensor anomaly detector")
    
    def get_or_create_detector(
        self,
        device_id: str,
        sensor_type: SensorType
    ) -> AnomalyDetector:
        """
        Get or create detector for device-sensor combination
        
        Args:
            device_id: Device identifier
            sensor_type: Sensor type
            
        Returns:
            Anomaly detector instance
        """
        key = f"{device_id}_{sensor_type.value}"
        
        if key not in self.detectors:
            self.detectors[key] = AnomalyDetector(sensor_type)
        
        return self.detectors[key]
    
    def add_sample(self, device_id: str, sensor_type: SensorType, value: float):
        """Add sample to appropriate detector"""
        detector = self.get_or_create_detector(device_id, sensor_type)
        detector.add_sample(value)
    
    def predict(
        self,
        device_id: str,
        sensor_type: SensorType,
        value: float
    ) -> Tuple[bool, float]:
        """Predict anomaly for device-sensor"""
        detector = self.get_or_create_detector(device_id, sensor_type)
        return detector.predict(value)
    
    def train_all(self):
        """Train all detectors"""
        for key, detector in self.detectors.items():
            if not detector.is_trained:
                detector.train()
    
    def get_all_statistics(self) -> Dict:
        """Get statistics for all detectors"""
        return {
            key: detector.get_statistics()
            for key, detector in self.detectors.items()
        }


# Global multi-sensor detector instance
_multi_detector: Optional[MultiSensorAnomalyDetector] = None


def get_anomaly_detector() -> MultiSensorAnomalyDetector:
    """Get global multi-sensor anomaly detector"""
    global _multi_detector
    if _multi_detector is None:
        _multi_detector = MultiSensorAnomalyDetector()
    return _multi_detector
