# Quick Start Guide

## Getting Started in 5 Minutes

### Step 1: Clone and Setup

```bash
# Navigate to your project directory
cd self-healing-iot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings (optional for local development)
# Default settings work out of the box for local testing
```

### Step 3: Initialize Database

```bash
python scripts/setup_db.py
```

### Step 4: Start Services

**Option A: All at Once (Recommended for Development)**
```bash
chmod +x scripts/run_all.sh
./scripts/run_all.sh
```

**Option B: Manually (For Testing Individual Components)**

Terminal 1 - MQTT Broker:
```bash
mosquitto -c config/mosquitto.conf
```

Terminal 2 - Backend Server:
```bash
python src/backend/main.py
```

Terminal 3 - Device Simulator:
```bash
python src/simulator/device_simulator.py
```

Terminal 4 - Dashboard:
```bash
streamlit run src/dashboard/app.py
```

### Step 5: Access the System

Open your browser and navigate to:

- **Dashboard**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **Backend API**: http://localhost:8000

---

## What to Build Next

The folder structure is complete. Now you need to implement the core logic in these key files:

### Priority 1: Core Infrastructure (Week 1)
1. **MQTT Communication** (`src/mqtt/`)
   - `client.py` - MQTT client wrapper with reconnection logic
   - `publisher.py` - Publishing utilities
   - `subscriber.py` - Message handling and routing
   - `topics.py` - Topic management

2. **Database Layer** (`src/database/`)
   - `db_manager.py` - Database connection and initialization
   - `repositories/device_repo.py` - Device CRUD operations
   - `repositories/telemetry_repo.py` - Telemetry data storage
   - `repositories/anomaly_repo.py` - Anomaly tracking
   - `repositories/healing_repo.py` - Healing action logs

### Priority 2: Device Simulation (Week 1-2)
3. **Simulator** (`src/simulator/`)
   - `virtual_node.py` - Virtual IoT device class
   - `sensor_simulator.py` - Realistic sensor data generation
   - `fault_injector.py` - Fault injection for testing
   - `device_simulator.py` - Main simulator orchestrator

### Priority 3: AI/ML Components (Week 2)
4. **AI Engine** (`src/ai/`)
   - `anomaly_detector.py` - Isolation Forest implementation
   - `model_manager.py` - Model training and persistence
   - `feature_engineering.py` - Data preprocessing
   - `sensor_drift.py` - Drift detection algorithms

### Priority 4: Self-Healing Logic (Week 2-3)
5. **Healing System** (`src/healing/`)
   - `orchestrator.py` - Main healing coordinator
   - `decision_engine.py` - Root cause analysis
   - `policies.py` - Policy loader from YAML
   - `actions.py` - Healing action executors
   - `validator.py` - Post-healing validation

### Priority 5: Dashboard (Week 3)
6. **Visualization** (`src/dashboard/`)
   - `app.py` - Main Streamlit application
   - `pages/` - Multi-page dashboard
   - `components/` - Reusable UI components

### Priority 6: Complete Backend APIs (Week 3-4)
7. **Backend APIs** (`src/backend/api/`)
   - Complete implementations for all endpoints
   - Add proper error handling
   - Implement authentication (if needed)

---

## Development Workflow

### 1. Test MQTT Communication First
```bash
# Terminal 1: Start broker
mosquitto -c config/mosquitto.conf

# Terminal 2: Subscribe to test topic
mosquitto_sub -h localhost -t "test/topic" -v

# Terminal 3: Publish test message
mosquitto_pub -h localhost -t "test/topic" -m "Hello MQTT"
```

### 2. Implement and Test Each Module
- Write unit tests in `tests/unit/`
- Run tests: `pytest tests/unit/test_module_name.py`
- Integration tests in `tests/integration/`

### 3. Use the Simulator for Development
- No hardware needed during development
- Inject faults to test healing logic
- Generate realistic telemetry data

### 4. Monitor Logs
```bash
# Watch all logs
tail -f logs/system.log

# Watch MQTT logs
tail -f logs/mqtt.log

# Watch healing logs
tail -f logs/healing.log
```

---

## Project Milestones

### Milestone 1: Basic Infrastructure ✓
- [x] Project structure created
- [x] Configuration files ready
- [x] Database schema defined
- [ ] MQTT client working
- [ ] Database operations working

### Milestone 2: Device Simulation
- [ ] Virtual devices can connect
- [ ] Telemetry data generation
- [ ] Heartbeat mechanism
- [ ] Fault injection working

### Milestone 3: ML Integration
- [ ] Anomaly detection model trained
- [ ] Real-time prediction working
- [ ] Model persistence implemented

### Milestone 4: Self-Healing
- [ ] Anomaly detection → healing trigger
- [ ] Healing actions executed
- [ ] Recovery validation working
- [ ] Closed-loop healing cycle complete

### Milestone 5: Visualization
- [ ] Dashboard displays devices
- [ ] Real-time telemetry charts
- [ ] Anomaly alerts visible
- [ ] Healing logs displayed

### Milestone 6: Hardware Integration
- [ ] ESP32 firmware developed
- [ ] Real device connected
- [ ] Hardware healing actions working
- [ ] Production deployment

---

## Tips for Success

1. **Start Simple**: Get basic MQTT communication working first
2. **Test Often**: Write tests as you develop each module
3. **Use Logs**: Logger is configured - use it extensively
4. **Incremental Development**: Complete one module before moving to next
5. **Documentation**: Update docs as you build features
6. **Version Control**: Commit frequently with clear messages

---

## Need Help?

- **MQTT Issues**: Check `docs/MQTT_TOPICS.md`
- **Database Issues**: Check schema in `src/database/schema.sql`
- **Configuration**: See `config/settings.py` and `.env.example`
- **Hardware Integration**: See `docs/HARDWARE_INTEGRATION.md`

---

## Next Steps

1. ✓ Complete folder structure (DONE!)
2. Implement MQTT client (`src/mqtt/client.py`)
3. Implement database manager (`src/database/db_manager.py`)
4. Create simple device simulator (`src/simulator/device_simulator.py`)
5. Test end-to-end flow with simulated device
6. Implement anomaly detection
7. Implement healing orchestrator
8. Build dashboard
9. Integrate real hardware

**You're all set! Start coding! 🚀**
