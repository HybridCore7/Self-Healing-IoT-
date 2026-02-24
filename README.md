<<<<<<< HEAD
# Self-Healing-IoT-
=======
# AI-Enabled Self-Healing IoT System

## Project Overview
An intelligent IoT platform that autonomously detects faults and recovers from failures using machine learning and automated healing mechanisms.

## Architecture
- **Perception Layer**: IoT devices (ESP32 + sensors)
- **Communication Layer**: MQTT protocol
- **Platform Layer**: FastAPI backend
- **Intelligence Layer**: ML-based anomaly detection
- **Decision Layer**: Automated healing orchestrator
- **Application Layer**: Streamlit dashboard

## Tech Stack
- Python 3.9+
- FastAPI (Backend)
- MQTT (Mosquitto broker)
- Scikit-learn (ML)
- Streamlit (Dashboard)
- SQLite (Database)

## Getting Started

### Prerequisites
```bash
python >= 3.9
mosquitto (MQTT broker)
```

### Installation
```bash
# Clone repository
git clone <repo-url>
cd self-healing-iot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the System

1. **Start MQTT Broker**
```bash
mosquitto -c config/mosquitto.conf
```

2. **Start Backend Server**
```bash
python src/backend/main.py
```

3. **Start Device Simulator**
```bash
python src/simulator/device_simulator.py
```

4. **Start Dashboard**
```bash
streamlit run src/dashboard/app.py
```

## Project Structure
See `docs/project_structure.md` for detailed folder organization.

## License
MIT
>>>>>>> b1f0d45 (Self Healing IoT System)
