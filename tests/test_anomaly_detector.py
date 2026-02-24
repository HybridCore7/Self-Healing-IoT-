"""
Unit Tests: Anomaly Detection (Z-Score + Feature Engineering)
Tests paper equations (1), (2), (3)
"""
import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ai.feature_engineering import SensorFeatureExtractor


class TestFeatureEngineering:
    """Tests for feature extraction and z-score computation."""

    def setup_method(self):
        self.extractor = SensorFeatureExtractor(window_size=10)

    def test_neutral_features_when_empty(self):
        """With no history, neutral features returned."""
        features = self.extractor.extract_features("d1", "temperature", 25.0)
        assert features["z_score"] == 0.0
        assert features["rolling_std"] == 0.0

    def test_rolling_mean_equals_average(self):
        """Rolling mean matches manual average — paper eq. (1)."""
        values = [20.0, 22.0, 24.0, 26.0, 28.0]
        for v in values:
            self.extractor.add_reading("d1", "temperature", v)

        features = self.extractor.extract_features("d1", "temperature", 24.0)
        expected_mean = np.mean(values)
        assert abs(features["rolling_mean"] - expected_mean) < 0.01

    def test_z_score_normal_reading(self):
        """Normal reading near mean → low z-score — paper eq. (3)."""
        baseline = [25.0] * 10
        for v in baseline:
            self.extractor.add_reading("d1", "temperature", v)

        features = self.extractor.extract_features("d1", "temperature", 25.1)
        assert abs(features["z_score"]) < 1.0

    def test_z_score_anomalous_reading(self):
        """Spike far from mean → high z-score — paper eq. (3)."""
        baseline = [25.0] * 10
        for v in baseline:
            self.extractor.add_reading("d1", "temperature", v)

        features = self.extractor.extract_features("d1", "temperature", 100.0)
        assert abs(features["z_score"]) > 3.0

    def test_is_anomaly_by_zscore(self):
        """Direct z-score threshold anomaly detection."""
        # Fill with stable baseline
        for v in [25.0] * 10:
            self.extractor.add_reading("d1", "temperature", v)

        self.extractor.add_reading("d1", "temperature", 25.0)

        is_anomaly, z = self.extractor.is_anomaly_by_zscore("d1", "temperature", 25.5, threshold=3.0)
        assert not is_anomaly  # Normal reading

    def test_rate_of_change(self):
        """Rate of change correctly computed."""
        for v in [10.0, 20.0, 30.0]:
            self.extractor.add_reading("d1", "pressure", v)

        features = self.extractor.extract_features("d1", "pressure", 40.0)
        # Last reading was 30, new is 40 → rate = 10
        assert abs(features["rate_of_change"] - 10.0) < 0.01

    def test_reset_clears_buffer(self):
        """Reset clears reading history."""
        for v in [25.0] * 5:
            self.extractor.add_reading("d1", "temperature", v)
        self.extractor.reset("d1", "temperature")

        features = self.extractor.extract_features("d1", "temperature", 25.0)
        assert features["reading_count"] == 1.0

    def test_multiple_devices_isolated(self):
        """Different devices have independent buffers."""
        for v in [100.0] * 5:
            self.extractor.add_reading("d1", "temp", v)
        for v in [25.0] * 5:
            self.extractor.add_reading("d2", "temp", v)

        f1 = self.extractor.extract_features("d1", "temp", 100.0)
        f2 = self.extractor.extract_features("d2", "temp", 25.0)
        assert abs(f1["rolling_mean"] - 100.0) < 1.0
        assert abs(f2["rolling_mean"] - 25.0) < 1.0
