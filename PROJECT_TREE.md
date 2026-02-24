# Project Structure - Visual Tree

```
self-healing-iot/
│
├── 📄 README.md                          # Project overview and documentation
├── 📄 requirements.txt                   # Python dependencies
├── 📄 setup.py                          # Package installation setup
├── 📄 pytest.ini                        # Testing configuration
├── 📄 .env.example                      # Environment variables template
├── 📄 .gitignore                        # Git ignore rules
│
├── 📁 config/                           # ⚙️ Configuration Files
│   ├── __init__.py
│   ├── settings.py                      # Main application settings
│   ├── mqtt_config.yaml                 # MQTT topic structure
│   ├── healing_policies.yaml            # Self-healing policies
│   └── mosquitto.conf                   # MQTT broker config
│
├── 📁 src/                              # 💻 Source Code
│   ├── __init__.py
│   │
│   ├── 📁 backend/                      # 🌐 FastAPI Backend Server
│   │   ├── __init__.py
│   │   ├── main.py                      # Backend entry point ⭐
│   │   ├── 📁 api/                      # REST API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── devices.py               # Device management API
│   │   │   ├── telemetry.py             # Telemetry data API
│   │   │   ├── healing.py               # Healing actions API
│   │   │   └── health.py                # System health API
│   │   ├── 📁 models/                   # Pydantic data models
│   │   │   ├── __init__.py
│   │   │   ├── device.py                # Device models
│   │   │   ├── telemetry.py             # Telemetry models
│   │   │   ├── anomaly.py               # Anomaly models
│   │   │   └── healing.py               # Healing models
│   │   └── 📁 middleware/               # API middleware
│   │       ├── __init__.py
│   │       └── logging.py               # Request logging
│   │
│   ├── 📁 mqtt/                         # 📡 MQTT Communication Layer
│   │   ├── __init__.py
│   │   ├── client.py                    # MQTT client wrapper ⭐
│   │   ├── publisher.py                 # Publishing utilities
│   │   ├── subscriber.py                # Subscription handler
│   │   └── topics.py                    # Topic definitions
│   │
│   ├── 📁 ai/                           # 🤖 AI & Machine Learning
│   │   ├── __init__.py
│   │   ├── anomaly_detector.py          # Isolation Forest ⭐
│   │   ├── sensor_drift.py              # Drift detection
│   │   ├── model_manager.py             # Model training & loading
│   │   ├── feature_engineering.py       # Data preprocessing
│   │   └── predictor.py                 # Real-time prediction
│   │
│   ├── 📁 healing/                      # 🏥 Self-Healing Engine
│   │   ├── __init__.py
│   │   ├── orchestrator.py              # Main healing coordinator ⭐
│   │   ├── decision_engine.py           # Root cause analysis
│   │   ├── policies.py                  # Policy definitions
│   │   ├── actions.py                   # Healing action executors
│   │   └── validator.py                 # Post-healing validation
│   │
│   ├── 📁 database/                     # 💾 Database Layer
│   │   ├── __init__.py
│   │   ├── db_manager.py                # DB connection & setup ⭐
│   │   ├── schema.sql                   # Database schema
│   │   └── 📁 repositories/             # Data access layer
│   │       ├── __init__.py
│   │       ├── device_repo.py           # Device CRUD
│   │       ├── telemetry_repo.py        # Telemetry CRUD
│   │       ├── anomaly_repo.py          # Anomaly CRUD
│   │       └── healing_repo.py          # Healing logs CRUD
│   │
│   ├── 📁 simulator/                    # 🎮 IoT Device Simulator
│   │   ├── __init__.py
│   │   ├── device_simulator.py          # Main simulator ⭐
│   │   ├── virtual_node.py              # Virtual IoT node
│   │   ├── sensor_simulator.py          # Sensor data generation
│   │   ├── fault_injector.py            # Fault injection
│   │   └── heartbeat.py                 # Heartbeat mechanism
│   │
│   ├── 📁 dashboard/                    # 📊 Streamlit Dashboard
│   │   ├── __init__.py
│   │   ├── app.py                       # Main dashboard app ⭐
│   │   ├── 📁 pages/                    # Multi-page structure
│   │   │   ├── 1_overview.py            # System overview
│   │   │   ├── 2_devices.py             # Device monitoring
│   │   │   ├── 3_anomalies.py           # Anomaly visualization
│   │   │   └── 4_healing_logs.py        # Healing event logs
│   │   ├── 📁 components/               # Reusable UI components
│   │   │   ├── __init__.py
│   │   │   ├── charts.py                # Plotly charts
│   │   │   ├── metrics.py               # Metric cards
│   │   │   └── tables.py                # Data tables
│   │   └── 📁 utils/                    # Dashboard utilities
│   │       ├── __init__.py
│   │       └── data_fetcher.py          # API data fetching
│   │
│   ├── 📁 utils/                        # 🛠️ Shared Utilities
│   │   ├── __init__.py
│   │   ├── logger.py                    # Custom logging setup
│   │   ├── time_utils.py                # Time/date utilities
│   │   ├── validators.py                # Data validation
│   │   └── constants.py                 # Application constants
│   │
│   └── 📁 core/                         # 🎯 Core System Components
│       ├── __init__.py
│       ├── system_manager.py            # System orchestrator
│       └── event_bus.py                 # Event-driven communication
│
├── 📁 tests/                            # 🧪 Test Suite
│   ├── __init__.py
│   ├── conftest.py                      # Pytest fixtures
│   ├── 📁 unit/                         # Unit tests
│   │   ├── test_anomaly_detector.py
│   │   ├── test_healing_engine.py
│   │   └── test_mqtt_client.py
│   ├── 📁 integration/                  # Integration tests
│   │   ├── test_api.py
│   │   └── test_end_to_end.py
│   └── 📁 data/                         # Test data
│       └── sample_telemetry.csv
│
├── 📁 models/                           # 🎯 Saved ML Models
│   ├── .gitkeep
│   └── README.md
│
├── 📁 data/                             # 💿 Data Storage
│   ├── telemetry/                       # Raw telemetry data
│   ├── processed/                       # Processed data
│   └── iot_system.db                    # SQLite database
│
├── 📁 logs/                             # 📝 Application Logs
│   ├── system.log                       # General system logs
│   ├── mqtt.log                         # MQTT communication logs
│   └── healing.log                      # Healing action logs
│
├── 📁 docs/                             # 📚 Documentation
│   ├── project_structure.md             # Detailed structure
│   ├── API.md                           # API documentation
│   ├── MQTT_TOPICS.md                   # MQTT topic guide
│   ├── DEPLOYMENT.md                    # Deployment guide
│   ├── HARDWARE_INTEGRATION.md          # Hardware setup
│   └── QUICK_START.md                   # Quick start guide
│
└── 📁 scripts/                          # 🚀 Utility Scripts
    ├── setup_db.py                      # Database initialization
    ├── train_model.py                   # ML model training
    ├── generate_test_data.py            # Test data generation
    └── run_all.sh                       # Start all services
```

## Legend
- ⭐ = Critical files to implement first
- 📄 = Configuration/Documentation file
- 📁 = Directory
- 🌐 = Web/API related
- 📡 = Communication layer
- 🤖 = AI/ML related
- 🏥 = Self-healing logic
- 💾 = Data storage
- 🎮 = Simulation
- 📊 = Visualization
- 🛠️ = Utilities
- 🎯 = Core components
- 🧪 = Testing

## File Count Summary
- **Total Python Files**: ~65 files
- **Configuration Files**: 5
- **Documentation Files**: 6
- **Test Files**: ~10
- **Total Directories**: 25

## Implementation Priority
1. **Week 1**: MQTT, Database, Basic Simulator
2. **Week 2**: AI Engine, Healing Orchestrator
3. **Week 3**: Dashboard, Complete APIs
4. **Week 4**: Testing, Documentation, Hardware Integration
