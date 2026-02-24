"""
Healing Validator
Post-healing validation: verifies that a healing action was successful
by monitoring the sensor readings afterwards.

Trust Score Update (paper eq. 6):
  T_i(t+1) = α·T_i(t) + (1-α)·C_i
  where C_i is the consensus agreement score.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

ALPHA = 0.7          # Trust score exponential smoothing factor
VALIDATION_WINDOW = 30  # Seconds to wait before checking if healing worked
Z_THRESHOLD = 2.5    # Z-score below which device is considered healed


class HealingValidator:
    """
    Validates healing outcomes and maintains per-device trust scores.

    Trust Score T_i ∈ [0, 1]:
      - Starts at 1.0 (fully trusted)
      - Decreases when repeated faults occur
      - Recovers as device performs well
    """

    def __init__(self):
        # Trust scores per device: device_id → float in [0,1]
        self._trust_scores: Dict[str, float] = {}
        # Recent consensus scores: device_id → float in [0,1]
        self._consensus_scores: Dict[str, float] = {}
        # Validation results: healing_id → bool
        self._validation_results: Dict[str, bool] = {}

    # ─────────────────────────────────────────────
    # Trust Score (paper equation 6)
    # ─────────────────────────────────────────────

    def get_trust_score(self, device_id: str) -> float:
        """Return current trust score for a device (default 1.0)."""
        return self._trust_scores.get(device_id, 1.0)

    def update_trust_score(self, device_id: str, consensus_score: float) -> float:
        """
        Update trust score using exponential moving average.
        Paper equation (6): T_i(t+1) = α·T_i(t) + (1-α)·C_i
        """
        current = self.get_trust_score(device_id)
        new_trust = ALPHA * current + (1 - ALPHA) * consensus_score
        new_trust = max(0.0, min(1.0, new_trust))  # Clamp to [0,1]
        self._trust_scores[device_id] = new_trust
        self._consensus_scores[device_id] = consensus_score

        logger.debug(
            f"Trust update for {device_id}: {current:.3f} → {new_trust:.3f} "
            f"(C={consensus_score:.3f}, α={ALPHA})"
        )
        return new_trust

    def penalize_trust(self, device_id: str, penalty: float = 0.2):
        """Reduce trust score due to confirmed fault."""
        current = self.get_trust_score(device_id)
        new_trust = max(0.0, current - penalty)
        self._trust_scores[device_id] = new_trust
        logger.info(f"Trust penalty for {device_id}: {current:.3f} → {new_trust:.3f}")
        return new_trust

    def reward_trust(self, device_id: str, reward: float = 0.1):
        """Increase trust score after successful healing."""
        current = self.get_trust_score(device_id)
        new_trust = min(1.0, current + reward)
        self._trust_scores[device_id] = new_trust
        logger.info(f"Trust reward for {device_id}: {current:.3f} → {new_trust:.3f}")
        return new_trust

    def is_trusted(self, device_id: str, threshold: float = 0.4) -> bool:
        """Return True if device trust score is above threshold."""
        return self.get_trust_score(device_id) >= threshold

    # ─────────────────────────────────────────────
    # Consensus Deviation (paper equation 5)
    # ─────────────────────────────────────────────

    def compute_consensus_deviation(self, node_reading: float,
                                    neighbor_readings: list) -> float:
        """
        Paper equation (5): D_i = |S_i - (1/M) Σ S_j|
        If D_i > δ, node is marked faulty.
        """
        if not neighbor_readings:
            return 0.0
        neighbor_mean = sum(neighbor_readings) / len(neighbor_readings)
        deviation = abs(node_reading - neighbor_mean)
        return deviation

    def check_consensus_fault(self, node_reading: float,
                               neighbor_readings: list,
                               delta: float = 5.0) -> bool:
        """Return True if node reading deviates significantly from neighbors."""
        deviation = self.compute_consensus_deviation(node_reading, neighbor_readings)
        is_faulty = deviation > delta
        consensus_score = max(0.0, 1.0 - (deviation / (delta * 2)))
        return is_faulty, deviation, consensus_score

    # ─────────────────────────────────────────────
    # Post-Healing Validation
    # ─────────────────────────────────────────────

    async def validate_healing(self, device_id: str, healing_id: str,
                                db_manager=None,
                                wait_seconds: int = VALIDATION_WINDOW) -> bool:
        """
        Wait for `wait_seconds`, then check if device is still anomalous.
        Updates trust score accordingly.
        Returns True if healing was successful.
        """
        logger.info(
            f"Validating healing {healing_id} for {device_id} "
            f"(waiting {wait_seconds}s)..."
        )
        await asyncio.sleep(wait_seconds)

        try:
            if db_manager:
                # Check for anomalies after healing
                from src.database.repositories.anomaly_repo import AnomalyRepository
                repo = AnomalyRepository(db_manager)
                recent_anomalies = await repo.get_device_anomalies(device_id, limit=5)

                # Filter to anomalies after healing started
                cutoff = datetime.utcnow() - timedelta(seconds=wait_seconds + 10)
                post_healing_anomalies = [
                    a for a in recent_anomalies
                    if a.get('is_active') and
                    datetime.fromisoformat(a.get('detected_at', '2000-01-01')) > cutoff
                ]

                success = len(post_healing_anomalies) == 0
            else:
                # Without DB, assume success
                success = True

            if success:
                self.reward_trust(device_id)
                logger.info(f"✅ Healing {healing_id} validated: device {device_id} is healthy")
            else:
                self.penalize_trust(device_id)
                logger.warning(
                    f"❌ Healing {healing_id} failed: device {device_id} still anomalous"
                )

            self._validation_results[healing_id] = success
            return success

        except Exception as e:
            logger.error(f"Validation error for {healing_id}: {e}")
            self._validation_results[healing_id] = False
            return False

    def get_all_trust_scores(self) -> Dict[str, float]:
        return dict(self._trust_scores)

    def get_validation_results(self) -> Dict[str, bool]:
        return dict(self._validation_results)

    def get_stats(self) -> Dict:
        scores = self._trust_scores.values()
        results = self._validation_results.values()
        return {
            "devices_tracked": len(self._trust_scores),
            "avg_trust_score": sum(scores) / len(scores) if scores else 1.0,
            "total_validations": len(self._validation_results),
            "successful_validations": sum(1 for v in results if v),
            "failed_validations": sum(1 for v in results if not v),
        }


# Singleton
_validator: Optional[HealingValidator] = None


def get_healing_validator() -> HealingValidator:
    global _validator
    if _validator is None:
        _validator = HealingValidator()
    return _validator
