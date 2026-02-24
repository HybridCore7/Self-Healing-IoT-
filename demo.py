"""
Self-Healing IoT Network - Standalone Demo
==========================================
Runs a complete simulation of the self-healing algorithm described in the paper:
  - Anomaly detection (Z-score, eq. 3)
  - Distributed consensus (eq. 5)
  - Trust score update (eq. 6)
  - Self-healing decisions

No backend server or MQTT broker required.
Run with: python demo.py
"""
import time
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List

# ─────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────
NUM_NODES = 6
WINDOW_SIZE = 20
Z_THRESHOLD = 3.0
CONSENSUS_DELTA = 5.0
ALPHA = 0.7          # Trust score smoothing
SIMULATION_STEPS = 40
STEP_DELAY = 0.3     # seconds

# Fault injection schedule
FAULT_SCHEDULE = {
    "node_2": {"start": 10, "end": 20, "type": "drift",   "magnitude": 15.0},
    "node_5": {"start": 25, "end": 40, "type": "stuck",   "stuck_value": 999.0},
    "node_4": {"start": 15, "end": 18, "type": "offline"},
}


# ─────────────────────────────────────────────────────
# Node class (simplified self-healing algorithm)
# ─────────────────────────────────────────────────────
class IoTNode:
    def __init__(self, node_id: str, base_temp: float = 25.0):
        self.node_id = node_id
        self.base_temp = base_temp
        self.trust_score = 1.0
        self.history: List[float] = []
        self.is_online = True
        self.is_faulty = False
        self.anomaly_count = 0
        self.healed_count = 0
        self.last_reading = base_temp

    def rolling_mean(self) -> float:
        if not self.history:
            return self.base_temp
        return sum(self.history[-WINDOW_SIZE:]) / len(self.history[-WINDOW_SIZE:])

    def rolling_std(self) -> float:
        if len(self.history) < 2:
            return 0.0
        window = self.history[-WINDOW_SIZE:]
        mu = sum(window) / len(window)
        variance = sum((x - mu) ** 2 for x in window) / len(window)
        return math.sqrt(variance)

    def z_score(self, value: float) -> float:
        """Paper equation (3)"""
        sigma = self.rolling_std()
        if sigma < 1e-9:
            return 0.0
        return (value - self.rolling_mean()) / sigma

    def sense(self, step: int, fault_config: dict = None) -> float:
        """Generate a sensor reading (with faults if configured)."""
        if not self.is_online:
            return None

        # Normal reading with small noise
        reading = self.base_temp + random.gauss(0, 0.5)

        if fault_config:
            fault_type = fault_config.get("type")
            if fault_type == "drift":
                reading += fault_config["magnitude"] * random.uniform(0.8, 1.2)
            elif fault_type == "stuck":
                reading = fault_config["stuck_value"]

        self.last_reading = reading
        self.history.append(reading)
        return reading

    def update_trust(self, consensus_score: float):
        """Paper equation (6): T_i(t+1) = α·T_i(t) + (1-α)·C_i"""
        self.trust_score = ALPHA * self.trust_score + (1 - ALPHA) * consensus_score
        self.trust_score = max(0.0, min(1.0, self.trust_score))

    def heal(self):
        """Execute self-healing: reset to interpolated value from neighbors."""
        self.is_faulty = False
        self.anomaly_count = 0
        self.healed_count += 1
        # Clear last few bad readings
        if len(self.history) > 5:
            self.history = self.history[:-3]
        return True


# ─────────────────────────────────────────────────────
# Network Simulation
# ─────────────────────────────────────────────────────
def run_simulation():
    print("=" * 65)
    print("  SELF-HEALING IoT SENSOR NETWORK SIMULATION")
    print("  Based on: 'Self-Healing IoT Using Distributed AI' Paper")
    print("=" * 65)
    print(f"  Nodes: {NUM_NODES} | Steps: {SIMULATION_STEPS} | "
          f"Z-threshold: {Z_THRESHOLD}")
    print("=" * 65)
    print()

    # Initialize nodes
    nodes = {
        f"node_{i}": IoTNode(f"node_{i}", base_temp=25.0 + i * 0.5)
        for i in range(1, NUM_NODES + 1)
    }

    # Track metrics
    total_anomalies = 0
    total_healed = 0
    detection_times = []

    for step in range(1, SIMULATION_STEPS + 1):
        print(f"{'─' * 65}")
        print(f"  STEP {step:02d}/{SIMULATION_STEPS}  |  "
              f"{datetime.now().strftime('%H:%M:%S')}")
        print(f"{'─' * 65}")

        # Apply/remove faults
        active_faults = {}
        for node_id, fc in FAULT_SCHEDULE.items():
            if fc["start"] <= step <= fc.get("end", SIMULATION_STEPS):
                if fc["type"] == "offline":
                    nodes[node_id].is_online = False
                else:
                    active_faults[node_id] = fc
            else:
                nodes[node_id].is_online = True

        # ─── Phase 1: Sense Data ───
        readings = {}
        for node_id, node in nodes.items():
            fault_config = active_faults.get(node_id)
            reading = node.sense(step, fault_config)
            readings[node_id] = reading

        # ─── Phase 2: Z-Score Anomaly Detection ───
        local_anomalies = {}
        for node_id, node in nodes.items():
            if not node.is_online or readings[node_id] is None:
                continue
            reading = readings[node_id]
            z = node.z_score(reading)
            is_anomaly = abs(z) > Z_THRESHOLD

            if is_anomaly:
                local_anomalies[node_id] = {
                    "z_score": z,
                    "reading": reading,
                    "mean": node.rolling_mean()
                }

        # ─── Phase 3: Distributed Consensus Voting ───
        confirmed_faults = {}
        for node_id in local_anomalies:
            if not nodes[node_id].is_online:
                continue

            node_reading = readings[node_id]
            # Get neighbor readings (all other online nodes)
            neighbor_readings = [
                readings[n] for n in readings
                if n != node_id and readings[n] is not None
                and nodes[n].is_online
            ]

            if not neighbor_readings:
                continue

            # Paper equation (5): D_i = |S_i - (1/M) Σ S_j|
            neighbor_mean = sum(neighbor_readings) / len(neighbor_readings)
            deviation = abs(node_reading - neighbor_mean)
            consensus_score = max(0.0, 1.0 - deviation / (CONSENSUS_DELTA * 2))

            is_confirmed = deviation > CONSENSUS_DELTA

            # Update trust score (paper equation 6)
            nodes[node_id].update_trust(consensus_score)

            if is_confirmed:
                confirmed_faults[node_id] = {
                    "deviation": deviation,
                    "neighbor_mean": neighbor_mean,
                    "reading": node_reading,
                    "trust_before": nodes[node_id].trust_score
                }
                total_anomalies += 1
                detection_times.append(step)

        # ─── Phase 4: Self-Healing ───
        for node_id, fault_info in confirmed_faults.items():
            # Get corrected value from neighbor interpolation
            neighbor_readings = [
                readings[n] for n in readings
                if n != node_id and readings[n] is not None
                and nodes[n].is_online
            ]
            corrected_value = sum(neighbor_readings) / len(neighbor_readings) if neighbor_readings else nodes[node_id].base_temp

            nodes[node_id].heal()
            nodes[node_id].history.append(corrected_value)  # Insert corrected reading
            total_healed += 1

        # ─── Print Node Status ───
        print(f"  {'Node':<10} {'Reading':>8} {'Z-Score':>8} {'Trust':>7} {'Status':<20}")
        print(f"  {'-'*58}")
        for node_id, node in nodes.items():
            reading = readings.get(node_id)
            if not node.is_online or reading is None:
                print(f"  {node_id:<10} {'OFFLINE':>8} {'---':>8} "
                      f"{node.trust_score:>6.2f}  ⚫ OFFLINE")
                continue

            z = node.z_score(reading)
            status = "✅ Normal"

            if node_id in local_anomalies:
                status = "⚠️  Anomaly detected"
            if node_id in confirmed_faults:
                status = "🔴 FAULT confirmed"
                nodes[node_id].anomaly_count += 1
            if nodes[node_id].healed_count > 0 and node_id not in confirmed_faults:
                if nodes[node_id].healed_count > 0:
                    status = "🔧 Healed"

            print(f"  {node_id:<10} {reading:>8.2f} {z:>8.3f} "
                  f"{node.trust_score:>6.2f}  {status}")

        # ─── Print Healing Actions ───
        if confirmed_faults:
            print()
            print("  🔧 SELF-HEALING ACTIONS:")
            for node_id, info in confirmed_faults.items():
                corrected = info['neighbor_mean']
                print(f"    [{node_id}] Fault confirmed (dev={info['deviation']:.2f})")
                print(f"           Raw: {info['reading']:.2f} → Corrected: {corrected:.2f}")
                print(f"           Trust: {nodes[node_id].trust_score:.3f}")
        else:
            print("\n  ✅ All nodes healthy — no healing needed")

        print()
        time.sleep(STEP_DELAY)

    # ─── Final Summary ───
    print("=" * 65)
    print("  SIMULATION COMPLETE — SUMMARY")
    print("=" * 65)
    print(f"  Total Steps         : {SIMULATION_STEPS}")
    print(f"  Total Anomalies     : {total_anomalies}")
    print(f"  Healing Actions     : {total_healed}")
    success_rate = (total_healed / total_anomalies * 100) if total_anomalies > 0 else 100.0
    print(f"  Healing Success Rate: {success_rate:.1f}%")
    print()
    print("  Final Trust Scores:")
    for node_id, node in nodes.items():
        bar_len = int(node.trust_score * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"    {node_id}: [{bar}] {node.trust_score:.3f}")
    print()
    print("  ✅ Self-healing IoT system simulation complete!")
    print("=" * 65)


if __name__ == "__main__":
    run_simulation()
