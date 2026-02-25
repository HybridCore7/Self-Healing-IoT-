# AI-Enabled Self-Healing IoT System

> 🛰️ Distributed AI network that autonomously detects faults and heals IoT nodes using Z-Score anomaly detection, consensus voting, and adaptive trust scoring.

---

## ⚡ Quick Start — Live Dashboard (No Setup Required!)

The live dashboard is **fully standalone** — no backend, no MQTT, no database needed.

**Step 1: Install the two required packages**
```bash
pip install -r requirements_dashboard.txt
```

**Step 2: Run the dashboard**
```bash
streamlit run dashboard_live.py --server.port 8502
```

**Step 3: Open your browser at** → `http://localhost:8502`

That's it! Click **▶ Start** in the sidebar to begin the live simulation.

> **Python 3.9+** is the only prerequisite.

---

## 🧠 What the Dashboard Shows

| Panel | Description |
|---|---|
| 📡 Live Sensor Readings | Real-time temperature streams for all 6 nodes |
| 📐 Z-Score Monitor | Anomaly detection threshold visualization |
| 🔐 Trust Scores | Per-node adaptive trust (Eq. 6 from paper) |
| 🗳️ Consensus Deviation | Peer-to-peer fault confirmation (Eq. 5) |
| 🌐 Network Topology | Animated mesh network graph |
| 📋 Event Log | Every fault detection and self-healing action |

**Scheduled fault scenario:**
- 🟡 **Node-B**: Sensor drift (steps 12–22)
- 🔴 **Node-D**: Stuck-at fault (steps 28–38)
- ⚫ **Node-E**: Goes offline (steps 18–23)
- ✅ Others: Normal operation

---

## 🏗️ Full System Architecture

```
Perception Layer   →  IoT devices (ESP32 + sensors)
Communication      →  MQTT protocol (Mosquitto)
Platform Layer     →  FastAPI backend (REST API)
Intelligence Layer →  ML anomaly detection (Isolation Forest + Z-Score)
Decision Layer     →  Automated healing orchestrator
Application Layer  →  Streamlit dashboard
```

## Tech Stack
- **Python 3.9+**
- **FastAPI** — REST API backend
- **Paho-MQTT** — MQTT communication
- **Scikit-learn** — Machine learning
- **Streamlit + Plotly** — Interactive dashboard
- **SQLite** — Local database
- **aiosqlite** — Async database access

---

## 🚀 Full System Setup (Optional — for backend + MQTT)

### Prerequisites
```
Python >= 3.9
Mosquitto MQTT broker
```

### Installation
```bash
# Clone repository
git clone <repo-url>
cd self-healing-iot

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install all dependencies
pip install -r requirements.txt
```

### Running the Full System

**Terminal 1 — MQTT Broker:**
```bash
mosquitto -c config/mosquitto.conf
```

**Terminal 2 — Backend Server:**
```bash
python -m src.backend.main
```

**Terminal 3 — Device Simulator:**
```bash
python -m src.simulator.device_simulator
```

**Terminal 4 — Full Dashboard:**
```bash
streamlit run src/dashboard/app.py
```

Access points:
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Dashboard:** http://localhost:8501

---

## 📁 Project Structure
See [`PROJECT_TREE.md`](PROJECT_TREE.md) for the full folder layout.

## 📄 License
MIT
