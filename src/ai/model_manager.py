"""
Model Manager - Training, loading, and persistence of ML models
"""
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import json

from src.ai.anomaly_detector import AnomalyDetector
from src.utils.constants import SensorType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModelManager:
    """Manages ML model lifecycle - training, saving, loading"""
    
    def __init__(self, models_dir: str = "models"):
        """
        Initialize model manager
        
        Args:
            models_dir: Directory to store models
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        self.models: Dict[str, AnomalyDetector] = {}
        self.metadata: Dict[str, dict] = {}
        
        logger.info(f"Initialized model manager with directory: {models_dir}")
    
    def train_model(
        self,
        sensor_type: SensorType,
        training_data: list[float],
        model_version: Optional[str] = None
    ) -> bool:
        """
        Train new model for sensor type
        
        Args:
            sensor_type: Type of sensor
            training_data: Training data
            model_version: Optional version identifier
            
        Returns:
            True if training successful
        """
        if model_version is None:
            model_version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Create detector
        detector = AnomalyDetector(sensor_type)
        
        # Train
        success = detector.train(training_data)
        
        if success:
            # Save model
            model_path = self.models_dir / f"{sensor_type.value}_v{model_version}.pkl"
            detector.save_model(str(model_path))
            
            # Save metadata
            metadata = {
                'sensor_type': sensor_type.value,
                'version': model_version,
                'trained_at': datetime.utcnow().isoformat(),
                'training_samples': len(training_data),
                'model_path': str(model_path)
            }
            
            metadata_path = self.models_dir / f"{sensor_type.value}_v{model_version}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Store in memory
            self.models[sensor_type.value] = detector
            self.metadata[sensor_type.value] = metadata
            
            logger.info(f"Trained and saved model for {sensor_type.value} version {model_version}")
            return True
        
        return False
    
    def load_model(
        self,
        sensor_type: SensorType,
        model_version: Optional[str] = None
    ) -> Optional[AnomalyDetector]:
        """
        Load model for sensor type
        
        Args:
            sensor_type: Type of sensor
            model_version: Optional version (loads latest if not specified)
            
        Returns:
            Loaded detector or None
        """
        # Find model file
        if model_version:
            model_path = self.models_dir / f"{sensor_type.value}_v{model_version}.pkl"
        else:
            # Find latest version
            pattern = f"{sensor_type.value}_v*.pkl"
            model_files = sorted(self.models_dir.glob(pattern), reverse=True)
            
            if not model_files:
                logger.warning(f"No model found for {sensor_type.value}")
                return None
            
            model_path = model_files[0]
        
        if not model_path.exists():
            logger.warning(f"Model file not found: {model_path}")
            return None
        
        # Load model
        detector = AnomalyDetector(sensor_type)
        if detector.load_model(str(model_path)):
            self.models[sensor_type.value] = detector
            logger.info(f"Loaded model for {sensor_type.value} from {model_path}")
            return detector
        
        return None
    
    def get_model(self, sensor_type: SensorType) -> Optional[AnomalyDetector]:
        """
        Get model for sensor type (loads if not in memory)
        
        Args:
            sensor_type: Type of sensor
            
        Returns:
            Detector instance or None
        """
        if sensor_type.value in self.models:
            return self.models[sensor_type.value]
        
        return self.load_model(sensor_type)
    
    def list_models(self) -> list[dict]:
        """List all available models"""
        metadata_files = self.models_dir.glob("*_metadata.json")
        
        models_info = []
        for metadata_file in metadata_files:
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    models_info.append(metadata)
            except Exception as e:
                logger.error(f"Error reading metadata file {metadata_file}: {e}")
        
        return sorted(models_info, key=lambda x: x.get('trained_at', ''), reverse=True)
    
    def delete_model(self, sensor_type: SensorType, model_version: str) -> bool:
        """
        Delete model and metadata
        
        Args:
            sensor_type: Type of sensor
            model_version: Model version
            
        Returns:
            True if deleted successfully
        """
        model_path = self.models_dir / f"{sensor_type.value}_v{model_version}.pkl"
        metadata_path = self.models_dir / f"{sensor_type.value}_v{model_version}_metadata.json"
        
        deleted = False
        
        if model_path.exists():
            model_path.unlink()
            deleted = True
        
        if metadata_path.exists():
            metadata_path.unlink()
            deleted = True
        
        # Remove from memory
        if sensor_type.value in self.models:
            del self.models[sensor_type.value]
        
        if deleted:
            logger.info(f"Deleted model {sensor_type.value} version {model_version}")
        
        return deleted


# Global model manager instance
_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get global model manager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
