"""
Sensor Drift Detection - Statistical drift analysis
"""
import numpy as np
from typing import List, Optional, Tuple
from collections import deque
from scipy import stats

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DriftDetector:
    """Detects gradual drift in sensor readings using statistical methods"""
    
    def __init__(
        self,
        window_size: int = 50,
        drift_threshold: float = 0.15
    ):
        """
        Initialize drift detector
        
        Args:
            window_size: Number of samples for analysis window
            drift_threshold: Percentage drift to trigger detection (0-1)
        """
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        
        # Data windows
        self.baseline_window = deque(maxlen=window_size)
        self.current_window = deque(maxlen=window_size)
        
        # Statistics
        self.baseline_mean: Optional[float] = None
        self.baseline_std: Optional[float] = None
        
        logger.debug(f"Initialized drift detector with window={window_size}, threshold={drift_threshold}")
    
    def add_sample(self, value: float):
        """
        Add sample to current window
        
        Args:
            value: Sensor reading
        """
        # Initialize baseline if not set
        if self.baseline_mean is None:
            self.baseline_window.append(value)
            
            if len(self.baseline_window) >= self.window_size:
                self._update_baseline()
        else:
            self.current_window.append(value)
    
    def _update_baseline(self):
        """Update baseline statistics"""
        if len(self.baseline_window) > 0:
            data = np.array(self.baseline_window)
            self.baseline_mean = np.mean(data)
            self.baseline_std = np.std(data)
            logger.debug(f"Updated baseline: mean={self.baseline_mean:.2f}, std={self.baseline_std:.2f}")
    
    def detect_drift(self) -> Tuple[bool, float, str]:
        """
        Detect drift in current window compared to baseline
        
        Returns:
            Tuple of (has_drift, drift_percentage, drift_type)
        """
        if self.baseline_mean is None or len(self.current_window) < self.window_size // 2:
            return False, 0.0, "none"
        
        current_data = np.array(self.current_window)
        current_mean = np.mean(current_data)
        
        # Calculate drift percentage
        drift_pct = abs(current_mean - self.baseline_mean) / (self.baseline_mean + 1e-10)
        
        # Determine drift type
        if current_mean > self.baseline_mean:
            drift_type = "upward"
        else:
            drift_type = "downward"
        
        # Check if drift exceeds threshold
        has_drift = drift_pct > self.drift_threshold
        
        if has_drift:
            logger.info(f"Detected {drift_type} drift: {drift_pct*100:.1f}%")
        
        return has_drift, drift_pct, drift_type
    
    def detect_sudden_change(self, value: float, z_threshold: float = 3.0) -> bool:
        """
        Detect sudden change using z-score
        
        Args:
            value: Current sensor reading
            z_threshold: Z-score threshold for detection
            
        Returns:
            True if sudden change detected
        """
        if self.baseline_mean is None or self.baseline_std is None:
            return False
        
        # Calculate z-score
        z_score = abs(value - self.baseline_mean) / (self.baseline_std + 1e-10)
        
        is_sudden = z_score > z_threshold
        
        if is_sudden:
            logger.info(f"Detected sudden change: z-score={z_score:.2f}")
        
        return is_sudden
    
    def reset_baseline(self):
        """Reset baseline to current window"""
        if len(self.current_window) >= self.window_size // 2:
            self.baseline_window = deque(self.current_window, maxlen=self.window_size)
            self._update_baseline()
            self.current_window.clear()
            logger.info("Reset baseline to current window")
    
    def get_statistics(self) -> dict:
        """Get drift detector statistics"""
        current_mean = np.mean(self.current_window) if len(self.current_window) > 0 else None
        
        return {
            'baseline_mean': self.baseline_mean,
            'baseline_std': self.baseline_std,
            'current_mean': current_mean,
            'baseline_samples': len(self.baseline_window),
            'current_samples': len(self.current_window),
            'drift_threshold': self.drift_threshold
        }
