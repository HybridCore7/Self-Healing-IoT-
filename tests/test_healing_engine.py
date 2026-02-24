"""
Unit Tests: Healing Validator (Trust Score + Consensus)
Tests paper equations (5) and (6)
"""
import pytest
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.healing.validator import HealingValidator


class TestHealingValidator:
    """Tests for trust scoring and consensus-based fault detection."""

    def setup_method(self):
        self.validator = HealingValidator()

    # ─── Trust Score Tests (paper eq. 6) ───

    def test_initial_trust_score_is_one(self):
        score = self.validator.get_trust_score("device_001")
        assert score == 1.0

    def test_trust_score_update_exponential_average(self):
        """T_i(t+1) = α·T_i(t) + (1-α)·C_i  (α=0.7)"""
        score = self.validator.update_trust_score("d1", consensus_score=0.0)
        # 0.7 * 1.0 + 0.3 * 0.0 = 0.7
        assert abs(score - 0.7) < 0.001

    def test_trust_score_clamped_to_zero_one(self):
        """Trust score always stays in [0, 1]."""
        self.validator.penalize_trust("d1", penalty=999.0)
        assert self.validator.get_trust_score("d1") == 0.0

        self.validator.reward_trust("d1", reward=999.0)
        assert self.validator.get_trust_score("d1") == 1.0

    def test_penalty_reduces_trust(self):
        initial = self.validator.get_trust_score("d1")
        self.validator.penalize_trust("d1", penalty=0.3)
        assert self.validator.get_trust_score("d1") < initial

    def test_reward_increases_trust(self):
        self.validator.penalize_trust("d1", penalty=0.5)
        after_penalty = self.validator.get_trust_score("d1")
        self.validator.reward_trust("d1", reward=0.2)
        assert self.validator.get_trust_score("d1") > after_penalty

    def test_is_trusted_above_threshold(self):
        assert self.validator.is_trusted("d1", threshold=0.4)  # 1.0 > 0.4

    def test_is_trusted_below_threshold(self):
        self.validator.penalize_trust("d1", penalty=0.8)  # now ~0.2
        assert not self.validator.is_trusted("d1", threshold=0.4)

    # ─── Consensus Tests (paper eq. 5) ───

    def test_consensus_deviation_zero_for_equal_readings(self):
        """|S_i - (1/M)ΣS_j| = 0 when all equal."""
        dev = self.validator.compute_consensus_deviation(25.0, [25.0, 25.0, 25.0])
        assert dev < 0.001

    def test_consensus_deviation_correct_calculation(self):
        """D_i = |25 - mean(20,22,24)| = |25 - 22| = 3."""
        dev = self.validator.compute_consensus_deviation(25.0, [20.0, 22.0, 24.0])
        assert abs(dev - 3.0) < 0.01

    def test_consensus_fault_detection(self):
        """Node with reading far from neighbors flagged as faulty."""
        is_faulty, dev, score = self.validator.check_consensus_fault(
            node_reading=100.0,
            neighbor_readings=[25.0, 26.0, 24.0],
            delta=5.0
        )
        assert is_faulty
        assert dev > 5.0

    def test_consensus_no_fault_for_normal_node(self):
        """Node reading close to neighbors is not faulty."""
        is_faulty, dev, score = self.validator.check_consensus_fault(
            node_reading=26.0,
            neighbor_readings=[25.0, 25.5, 26.5],
            delta=5.0
        )
        assert not is_faulty
        assert dev < 5.0

    def test_consensus_empty_neighbors_returns_zero(self):
        dev = self.validator.compute_consensus_deviation(25.0, [])
        assert dev == 0.0

    def test_multiple_devices_independent_trust(self):
        """Each device has its own independent trust score."""
        self.validator.penalize_trust("d1", penalty=0.5)
        assert self.validator.get_trust_score("d2") == 1.0  # d2 unaffected

    def test_stats_returns_summary(self):
        self.validator.penalize_trust("d1", 0.2)
        self.validator.reward_trust("d2", 0.1)
        stats = self.validator.get_stats()
        assert stats["devices_tracked"] == 2
        assert 0 <= stats["avg_trust_score"] <= 1.0
