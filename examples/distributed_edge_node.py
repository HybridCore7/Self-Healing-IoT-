#!/usr/bin/env python3
"""
Distributed AI Edge Node Client
================================
THIS is the "Distributed AI" part described in the paper.

Each node runs this script locally (on ESP32/Raspberry Pi/PC).
It autonomously:
  1. Senses data
  2. Detects anomalies locally (Z-score, paper eq. 3)
  3. Queries neighbors for consensus (paper eq. 5)
  4. Maintains its own trust score (paper eq. 6)
  5. Decides to self-heal WITHOUT asking any central server

Architecture:
  Node_1 <-- MQTT --> Node_2 <-- MQTT --> Node_3
      Each node runs this same script independently.
      No central server required for AI decisions.

Install:  pip3 install paho-mqtt
Run:      python3 distributed_edge_node.py --id node_001 --broker 192.168.1.100
"""
import paho.mqtt.client as mqtt
import json, time, math, random, argparse
from datetime import datetime
from collections import deque
from typing import Dict, Optional

# ─── Paper Parameters ───────────────────────────────────────
WINDOW_N       = 20     # Rolling window size for μ and σ
Z_THRESHOLD    = 3.0    # Anomaly threshold |Z_i| > 3 → anomaly
CONSENSUS_DELTA = 5.0   # Consensus deviation threshold δ
ALPHA          = 0.7    # Trust score smoothing factor α
TELEMETRY_SEC  = 5      # How often to sense + publish
HEARTBEAT_SEC  = 30     # Heartbeat interval
NEIGHBOR_TIMEOUT = 15   # Seconds before neighbor reading expires


class DistributedAINode:
    """
    Self-contained distributed AI IoT node.

    Implements the full self-healing algorithm from the paper,
    running entirely at the EDGE with no central AI server.

    Mathematical Models Used:
      Eq.(1)  μ_i = (1/N) Σ x_i(k)           — rolling mean
      Eq.(2)  σ_i = sqrt((1/N)Σ(x_i(k)-μ_i)²) — std deviation
      Eq.(3)  Z_i(t) = (x_i(t) - μ_i) / σ_i   — z-score
      Eq.(5)  D_i = |S_i - (1/M)Σ S_j|          — consensus deviation
      Eq.(6)  T_i(t+1) = α·T_i(t) + (1-α)·C_i  — trust score update
    """

    def __init__(self, node_id: str, broker_host: str, broker_port: int = 1883,
                 base_temp: float = 25.0, simulate_fault: bool = False):
        self.node_id = node_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.base_temp = base_temp
        self.simulate_fault = simulate_fault

        # ─── Local AI State (no server needed) ───
        # Rolling window of personal readings (for μ, σ)
        self._readings: deque = deque(maxlen=WINDOW_N)

        # Neighbor readings: {neighbor_id: (value, received_at)}
        self._neighbor_readings: Dict[str, tuple] = {}

        # Trust score T_i ∈ [0,1] — starts fully trusted
        self.trust_score: float = 1.0

        # State tracking
        self.anomaly_count: int = 0
        self.heal_count: int = 0
        self.is_in_healing: bool = False
        self.step: int = 0

        # MQTT
        self.client = mqtt.Client(client_id=node_id)
        self.client.on_connect    = self._on_connect
        self.client.on_message    = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.running = True

    # ─────────────────────────────────────────────
    # Paper Equations (Local AI — runs on edge)
    # ─────────────────────────────────────────────

    def _rolling_mean(self) -> float:
        """Paper equation (1): μ_i = (1/N) Σ x_i(k)"""
        if not self._readings:
            return self.base_temp
        return sum(self._readings) / len(self._readings)

    def _rolling_std(self) -> float:
        """Paper equation (2): σ_i = sqrt((1/N)Σ(x_i(k)-μ_i)²)"""
        if len(self._readings) < 2:
            return 0.0
        mu = self._rolling_mean()
        variance = sum((x - mu)**2 for x in self._readings) / len(self._readings)
        return math.sqrt(variance)

    def _z_score(self, value: float) -> float:
        """Paper equation (3): Z_i(t) = (x_i(t) - μ_i) / σ_i"""
        sigma = self._rolling_std()
        if sigma < 1e-9:
            return 0.0
        return (value - self._rolling_mean()) / sigma

    def _local_anomaly_detection(self, value: float) -> tuple:
        """
        STEP 1: Local anomaly detection at the edge node.
        No server involved — pure local computation.
        Returns (is_anomaly, z_score, mean, std)
        """
        z = self._z_score(value)
        is_anomaly = abs(z) > Z_THRESHOLD
        return is_anomaly, z, self._rolling_mean(), self._rolling_std()

    def _get_valid_neighbor_readings(self) -> list:
        """Return neighbor readings that are still fresh (not expired)."""
        now = time.time()
        return [
            v for (v, ts) in self._neighbor_readings.values()
            if now - ts < NEIGHBOR_TIMEOUT
        ]

    def _consensus_check(self, my_value: float) -> tuple:
        """
        STEP 2: Distributed consensus vote.
        Paper equation (5): D_i = |S_i - (1/M) Σ S_j|
        If D_i > δ, node is marked faulty.
        Returns (fault_confirmed, deviation, consensus_score, neighbor_mean)
        """
        neighbors = self._get_valid_neighbor_readings()
        if not neighbors:
            return False, 0.0, 1.0, my_value  # No neighbors → assume OK

        neighbor_mean = sum(neighbors) / len(neighbors)
        deviation = abs(my_value - neighbor_mean)            # Eq.(5)
        consensus_score = max(0.0, 1.0 - deviation / (CONSENSUS_DELTA * 2))
        fault_confirmed = deviation > CONSENSUS_DELTA

        return fault_confirmed, deviation, consensus_score, neighbor_mean

    def _update_trust(self, consensus_score: float) -> float:
        """
        Paper equation (6): T_i(t+1) = α·T_i(t) + (1-α)·C_i
        Keeps trust in [0,1].
        """
        self.trust_score = ALPHA * self.trust_score + (1 - ALPHA) * consensus_score
        self.trust_score = max(0.0, min(1.0, self.trust_score))
        return self.trust_score

    def _self_heal(self, corrected_value: float):
        """
        STEP 3: Self-healing action.
        Replace faulty reading with interpolated neighbor value.
        Reset rolling buffer to avoid bad history polluting future detections.
        """
        # Clear last 3 potentially-bad readings  
        for _ in range(min(3, len(self._readings))):
            if self._readings:
                self._readings.pop()

        # Insert corrected value
        self._readings.append(corrected_value)
        self.heal_count += 1
        self.is_in_healing = False

        self._log(f"🔧 SELF-HEALED: replaced reading with interpolated value {corrected_value:.2f}")
        self._publish_status("healed", {"corrected_value": corrected_value})

    # ─────────────────────────────────────────────
    # Main Sensing + Decision Loop
    # ─────────────────────────────────────────────

    def _sense_and_decide(self):
        """
        Full self-healing algorithm loop (paper flowchart, Fig. 2):
          Sense Data → Anomaly? → Query Neighbors → Fault Confirmed? → Self-Heal
        """
        self.step += 1
        value = self._read_sensor()
        self._readings.append(value)

        self._log(f"[Step {self.step}] Reading: {value:.2f}°C | μ={self._rolling_mean():.2f} | σ={self._rolling_std():.2f} | T={self.trust_score:.3f}")

        # ── Sense Data → Anomaly? (Z-score local check) ──
        is_anomaly, z, mu, sigma = self._local_anomaly_detection(value)

        if not is_anomaly:
            self._log(f"  ✅ Z={z:.3f} — Normal. No action needed.")
            # Reward trust slightly for consistent normal reading
            self._update_trust(1.0)
            self._publish_telemetry(value, z, is_anomaly=False)
            self._broadcast_reading(value)  # Share with neighbors
            return

        self._log(f"  ⚠️  Z={z:.3f} — LOCAL ANOMALY DETECTED! Querying neighbors...")
        self.anomaly_count += 1

        # ── Query Neighbors → Fault Confirmed? (Consensus) ──
        self._publish_telemetry(value, z, is_anomaly=True)
        fault_confirmed, deviation, consensus_score, neighbor_mean = self._consensus_check(value)

        # Update trust score (eq. 6)
        self._update_trust(consensus_score)

        if not fault_confirmed:
            self._log(f"  ℹ️  D={deviation:.2f} < δ={CONSENSUS_DELTA} — Anomaly NOT confirmed by neighbors. Trust={self.trust_score:.3f}")
            return

        # ── Fault Confirmed → Self-Heal ──
        self._log(f"  🔴 FAULT CONFIRMED! D={deviation:.2f} > δ={CONSENSUS_DELTA} | Neighbors mean={neighbor_mean:.2f}")
        self._log(f"     Trust score reduced: {self.trust_score:.3f}")
        self.is_in_healing = True
        self._self_heal(corrected_value=neighbor_mean)

    # ─────────────────────────────────────────────
    # Sensor Reading
    # ─────────────────────────────────────────────

    def _read_sensor(self) -> float:
        """Simulate or read real sensor. Injects faults for demo."""
        value = self.base_temp + random.gauss(0, 0.5)

        # Simulate sensor drift fault after step 15 for 10 steps
        if self.simulate_fault and 15 <= self.step <= 25:
            drift = 20.0 * random.uniform(0.9, 1.1)
            value += drift
            self._log(f"  [FAULT INJECTED: +{drift:.1f}°C drift]")

        return round(value, 2)

    # ─────────────────────────────────────────────
    # MQTT Communication
    # ─────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ [{self.node_id}] Connected to MQTT broker {self.broker_host}:{self.broker_port}")
            # Subscribe to ALL neighbor readings (wildcard)
            client.subscribe("iot/distributed/readings/#")
            client.subscribe(f"iot/commands/{self.node_id}/#")
        else:
            print(f"❌ [{self.node_id}] Connection failed: rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print(f"⚠️  [{self.node_id}] Disconnected. Reconnecting...")

    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages from neighbors."""
        try:
            payload = json.loads(msg.payload.decode())

            # Neighbor reading → store for consensus
            if "iot/distributed/readings/" in msg.topic:
                sender_id = payload.get("node_id")
                sender_value = payload.get("value")
                if sender_id and sender_id != self.node_id and sender_value is not None:
                    self._neighbor_readings[sender_id] = (sender_value, time.time())

            # Incoming command (from another node or user)
            elif f"iot/commands/{self.node_id}" in msg.topic:
                cmd = payload.get("command")
                if cmd == "reset":
                    self._readings.clear()
                    self.trust_score = 1.0
                    self._log("🔄 Reset by command")

        except Exception as e:
            print(f"[{self.node_id}] Message error: {e}")

    def _broadcast_reading(self, value: float):
        """Share current reading with all neighbors via MQTT."""
        topic = f"iot/distributed/readings/{self.node_id}"
        payload = {
            "node_id": self.node_id,
            "value": value,
            "trust_score": self.trust_score,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.client.publish(topic, json.dumps(payload))

    def _publish_telemetry(self, value: float, z_score: float, is_anomaly: bool):
        """Publish full telemetry to backend (for logging/dashboard)."""
        topic = f"iot/telemetry/{self.node_id}/temperature"
        payload = {
            "device_id": self.node_id,
            "sensor_type": "temperature",
            "value": value,
            "unit": "°C",
            "z_score": round(z_score, 4),
            "is_anomaly": is_anomaly,
            "trust_score": round(self.trust_score, 4),
            "anomaly_count": self.anomaly_count,
            "heal_count": self.heal_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.client.publish(topic, json.dumps(payload))

    def _publish_heartbeat(self):
        topic = f"iot/health/{self.node_id}/heartbeat"
        payload = {
            "device_id": self.node_id,
            "status": "online",
            "trust_score": round(self.trust_score, 3),
            "anomaly_count": self.anomaly_count,
            "heal_count": self.heal_count,
            "neighbors_known": len(self._neighbor_readings),
            "timestamp": datetime.utcnow().isoformat()
        }
        self.client.publish(topic, json.dumps(payload), retain=True)

    def _publish_status(self, event: str, data: dict = None):
        topic = f"iot/distributed/status/{self.node_id}"
        payload = {
            "node_id": self.node_id,
            "event": event,
            "trust_score": round(self.trust_score, 3),
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        self.client.publish(topic, json.dumps(payload))

    # ─────────────────────────────────────────────
    # Run Loop
    # ─────────────────────────────────────────────

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}][{self.node_id}] {msg}")

    def run(self):
        print(f"\n{'='*60}")
        print(f"  Distributed AI Edge Node: {self.node_id}")
        print(f"  Broker: {self.broker_host}:{self.broker_port}")
        print(f"  Fault simulation: {self.simulate_fault}")
        print(f"  Implements: Paper eqs. (1)(2)(3)(5)(6)")
        print(f"{'='*60}\n")

        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
        except Exception as e:
            print(f"❌ Cannot connect to MQTT broker: {e}")
            print("   Start broker: mosquitto -v")
            return

        self.client.loop_start()

        last_telemetry = 0
        last_heartbeat = 0

        try:
            while self.running:
                now = time.time()

                if now - last_telemetry >= TELEMETRY_SEC:
                    self._sense_and_decide()
                    self._broadcast_reading(self._readings[-1] if self._readings else self.base_temp)
                    last_telemetry = now

                if now - last_heartbeat >= HEARTBEAT_SEC:
                    self._publish_heartbeat()
                    last_heartbeat = now

                time.sleep(0.5)

        except KeyboardInterrupt:
            self._log("Shutting down...")
        finally:
            self._publish_status("offline")
            self.client.loop_stop()
            self.client.disconnect()
            print(f"\n[{self.node_id}] Disconnected. Stats: anomalies={self.anomaly_count}, heals={self.heal_count}")


# ─────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed AI IoT Edge Node")
    parser.add_argument("--id",     default="node_001",       help="Unique node ID")
    parser.add_argument("--broker", default="localhost",      help="MQTT broker host")
    parser.add_argument("--port",   type=int, default=1883,   help="MQTT broker port")
    parser.add_argument("--temp",   type=float, default=25.0, help="Baseline temperature")
    parser.add_argument("--fault",  action="store_true",      help="Simulate sensor faults")
    args = parser.parse_args()

    node = DistributedAINode(
        node_id=args.id,
        broker_host=args.broker,
        broker_port=args.port,
        base_temp=args.temp,
        simulate_fault=args.fault
    )
    node.run()
