"""
Feature Engineering for Anomaly Detection
Converts raw sensor readings into enriched ML feature vectors.

Mathematical basis (from paper):
  μ_i = (1/N) Σ x_i(k)           — rolling mean
  σ_i = sqrt((1/N) Σ (x_i(k)-μ_i)^2)  — standard deviation
  Z_i(t) = (x_i(t) - μ_i) / σ_i  — z-score anomaly metric
"""
import numpy as np
from collections import deque
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Window size for rolling statistics
DEFAULT_WINDOW = 20


class SensorFeatureExtractor:
    """
    Per-sensor, per-device rolling feature extractor.
    Implements the paper's z-score anomaly model plus additional features.
    """

    def __init__(self, window_size: int = DEFAULT_WINDOW):
        self.window_size = window_size
        # Buffer of recent readings per (device_id, sensor_type)
        self._buffers: Dict[str, deque] = {}
        self._timestamps: Dict[str, deque] = {}

    def _key(self, device_id: str, sensor_type: str) -> str:
        return f"{device_id}::{sensor_type}"

    def _get_buffer(self, device_id: str, sensor_type: str) -> deque:
        k = self._key(device_id, sensor_type)
        if k not in self._buffers:
            self._buffers[k] = deque(maxlen=self.window_size)
            self._timestamps[k] = deque(maxlen=self.window_size)
        return self._buffers[k]

    def add_reading(self, device_id: str, sensor_type: str, value: float,
                    timestamp: Optional[datetime] = None):
        """Append a new reading to the rolling window."""
        buf = self._get_buffer(device_id, sensor_type)
        buf.append(value)
        self._timestamps[self._key(device_id, sensor_type)].append(
            timestamp or datetime.utcnow()
        )

    def extract_features(self, device_id: str, sensor_type: str,
                         current_value: float) -> Dict[str, float]:
        """
        Extract feature vector for a single (device, sensor, value) sample.

        Returns a dict with:
          - z_score          : paper eq. (3)
          - rolling_mean     : paper eq. (1)
          - rolling_std      : paper eq. (2)
          - rate_of_change   : Δx between last two readings
          - window_min / max : range indicators
          - hour_of_day      : temporal feature (0-23)
          - reading_count    : buffer fill level
        """
        buf = self._get_buffer(device_id, sensor_type)

        if len(buf) < 2:
            # Not enough data yet — return neutral features
            return self._neutral_features(current_value)

        arr = np.array(list(buf))

        # Paper equations (1), (2)
        mu = float(np.mean(arr))
        sigma = float(np.std(arr))

        # Paper equation (3): Z-score
        if sigma > 1e-9:
            z_score = (current_value - mu) / sigma
        else:
            z_score = 0.0

        # Rate of change
        rate_of_change = current_value - arr[-1] if len(arr) > 0 else 0.0

        # Time feature
        hour_of_day = datetime.utcnow().hour

        return {
            "value":           current_value,
            "rolling_mean":    mu,
            "rolling_std":     sigma,
            "z_score":         z_score,
            "abs_z_score":     abs(z_score),
            "rate_of_change":  rate_of_change,
            "abs_rate":        abs(rate_of_change),
            "window_min":      float(np.min(arr)),
            "window_max":      float(np.max(arr)),
            "window_range":    float(np.max(arr) - np.min(arr)),
            "hour_of_day":     float(hour_of_day),
            "reading_count":   float(len(buf)),
        }

    def _neutral_features(self, value: float) -> Dict[str, float]:
        return {
            "value":           value,
            "rolling_mean":    value,
            "rolling_std":     0.0,
            "z_score":         0.0,
            "abs_z_score":     0.0,
            "rate_of_change":  0.0,
            "abs_rate":        0.0,
            "window_min":      value,
            "window_max":      value,
            "window_range":    0.0,
            "hour_of_day":     float(datetime.utcnow().hour),
            "reading_count":   1.0,
        }

    def is_anomaly_by_zscore(self, device_id: str, sensor_type: str,
                              value: float, threshold: float = 3.0) -> Tuple[bool, float]:
        """
        Direct z-score threshold check (paper eq. 3).
        Returns (is_anomaly, z_score).
        """
        features = self.extract_features(device_id, sensor_type, value)
        z = features["z_score"]
        return abs(z) > threshold, z

    def features_as_vector(self, device_id: str, sensor_type: str,
                           value: float) -> np.ndarray:
        """Return features as a numpy array for ML model input."""
        feats = self.extract_features(device_id, sensor_type, value)
        keys = sorted(feats.keys())
        return np.array([feats[k] for k in keys])

    def reset(self, device_id: Optional[str] = None, sensor_type: Optional[str] = None):
        """Reset buffers for a specific device/sensor or all."""
        if device_id and sensor_type:
            k = self._key(device_id, sensor_type)
            self._buffers.pop(k, None)
            self._timestamps.pop(k, None)
        elif device_id:
            keys_to_del = [k for k in self._buffers if k.startswith(f"{device_id}::")]
            for k in keys_to_del:
                self._buffers.pop(k, None)
                self._timestamps.pop(k, None)
        else:
            self._buffers.clear()
            self._timestamps.clear()

    def get_stats(self) -> Dict:
        return {
            "tracked_sensors": len(self._buffers),
            "window_size": self.window_size,
            "sensors": list(self._buffers.keys()),
        }


# Singleton
_extractor: Optional[SensorFeatureExtractor] = None


def get_feature_extractor(window_size: int = DEFAULT_WINDOW) -> SensorFeatureExtractor:
    global _extractor
    if _extractor is None:
        _extractor = SensorFeatureExtractor(window_size=window_size)
    return _extractor
