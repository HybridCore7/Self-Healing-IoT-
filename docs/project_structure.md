# Project Structure

```
self-healing-iot/
│
├── config/                          # Configuration files
│   ├── __init__.py
│   ├── settings.py                  # Application settings (loads from .env)
│   ├── mqtt_config.yaml             # MQTT topic structure
│   ├── healing_policies.yaml        # Healing action definitions
│   └── mosquitto.conf               # MQTT broker configuration
│
├── src/                             # Source code
│   │
│   ├── backend/                     # FastAPI backend server
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI application entry point
│   │   ├── api/                     # REST API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── devices.py           # Device management endpoints
│   │   │   ├── telemetry.py         # Telemetry data endpoints
│   │   │   ├── healing.py           # Healing actions endpoints
│   │   │   └── health.py            # System health endpoints
│   │   ├── models/                  # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── device.py            # Device data models
│   │   │   ├── telemetry.py         # Telemetry data models
│   │   │   ├── anomaly.py           # Anomaly data models
│   │   │   └── healing.py           # Healing action models
│   │   └── middleware/              # API middleware
│   │       ├── __init__.py
│   │       └── logging.py           # Request logging
│   │
│   ├── mqtt/                        # MQTT communication layer
│   │   ├── __init__.py
│   │   ├── client.py                # MQTT client wrapper
│   │   ├── publisher.py             # Publishing utilities
│   │   ├── subscriber.py            # Subscription handler
│   │   └── topics.py                # Topic definitions
│   │
│   ├── ai/                          # AI & Machine Learning
│   │   ├── __init__.py
│   │   ├── anomaly_detector.py      # Isolation Forest implementation
│   │   ├── sensor_drift.py          # Sensor drift detection
│   │   ├── model_manager.py         # Model training & loading
│   │   ├── feature_engineering.py   # Data preprocessing
│   │   └── predictor.py             # Real-time prediction
│   │
│   ├── healing/                     # Self-healing engine
│   │   ├── __init__.py
│   │   ├── orchestrator.py          # Main healing orchestrator
│   │   ├── decision_engine.py       # Root cause analysis & decision logic
│   │   ├── policies.py              # Healing policy definitions
│   │   ├── actions.py               # Healing action executors
│   │   └── validator.py             # Post-healing validation
│   │
│   ├── database/                    # Database layer
│   │   ├── __init__.py
│   │   ├── db_manager.py            # Database connection & setup
│   │   ├── repositories/            # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── device_repo.py       # Device CRUD operations
│   │   │   ├── telemetry_repo.py    # Telemetry CRUD operations
│   │   │   ├── anomaly_repo.py      # Anomaly CRUD operations
│   │   │   └── healing_repo.py      # Healing logs CRUD operations
│   │   └── schema.sql               # Database schema
│   │
│   ├── simulator/                   # IoT device simulator
│   │   ├── __init__.py
│   │   ├── device_simulator.py      # Main simulator orchestrator
│   │   ├── virtual_node.py          # Virtual IoT node
│   │   ├── sensor_simulator.py      # Sensor data generation
│   │   ├── fault_injector.py        # Fault injection module
│   │   └── heartbeat.py             # Heartbeat mechanism
│   │
│   ├── dashboard/                   # Streamlit dashboard
│   │   ├── __init__.py
│   │   ├── app.py                   # Main dashboard app
│   │   ├── pages/                   # Multi-page dashboard
│   │   │   ├── 1_overview.py        # System overview
│   │   │   ├── 2_devices.py         # Device monitoring
│   │   │   ├── 3_anomalies.py       # Anomaly visualization
│   │   │   └── 4_healing_logs.py    # Healing event logs
│   │   ├── components/              # Reusable UI components
│   │   │   ├── __init__.py
│   │   │   ├── charts.py            # Plotly charts
│   │   │   ├── metrics.py           # Metric cards
│   │   │   └── tables.py            # Data tables
│   │   └── utils/                   # Dashboard utilities
│   │       ├── __init__.py
│   │       └── data_fetcher.py      # API data fetching
│   │
│   ├── utils/                       # Shared utilities
│   │   ├── __init__.py
│   │   ├── logger.py                # Custom logging setup
│   │   ├── time_utils.py            # Time/date utilities
│   │   ├── validators.py            # Data validation
│   │   └── constants.py             # Application constants
│   │
│   └── core/                        # Core system components
│       ├── __init__.py
│       ├── system_manager.py        # Main system orchestrator
│       └── event_bus.py             # Event-driven communication
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/                        # Unit tests
│   │   ├── test_anomaly_detector.py
│   │   ├── test_healing_engine.py
│   │   └── test_mqtt_client.py
│   ├── integration/                 # Integration tests
│   │   ├── test_api.py
│   │   └── test_end_to_end.py
│   └── data/                        # Test data
│       └── sample_telemetry.csv
│
├── models/                          # Saved ML models
│   ├── .gitkeep
│   └── README.md
│
├── data/                            # Data storage
│   ├── telemetry/                   # Raw telemetry data
│   ├── processed/                   # Processed data
│   └── iot_system.db                # SQLite database
│
├── logs/                            # Application logs
│   ├── system.log
│   ├── mqtt.log
│   └── healing.log
│
├── docs/                            # Documentation
│   ├── API.md                       # API documentation
│   ├── MQTT_TOPICS.md               # MQTT topic structure
│   ├── DEPLOYMENT.md                # Deployment guide
│   ├── HARDWARE_INTEGRATION.md      # Hardware integration guide
│   └── project_structure.md         # This file
│
├── scripts/                         # Utility scripts
│   ├── setup_db.py                  # Database initialization
│   ├── train_model.py               # ML model training
│   ├── generate_test_data.py        # Test data generation
│   └── run_all.sh                   # Start all services
│
├── .env.example                     # Environment variables template
├── .env                             # Environment variables (git-ignored)
├── .gitignore                       # Git ignore rules
├── requirements.txt                 # Python dependencies
├── README.md                        # Project documentation
├── pytest.ini                       # Pytest configuration
└── setup.py                         # Package setup file
```

## Key Design Decisions

### 1. Modular Architecture
- Each layer (MQTT, AI, Healing, Backend) is independent
- Easy to test, maintain, and scale
- Hardware integration only requires changes to simulator module

### 2. Configuration Management
- All configurations in `config/` directory
- Environment-specific settings in `.env`
- YAML for complex configurations (MQTT topics, healing policies)

### 3. Database Layer
- Repository pattern for data access
- Easy to switch from SQLite to PostgreSQL/MongoDB later
- Separation of concerns between business logic and data access

### 4. API-First Design
- REST APIs for all operations
- Dashboard and external systems consume APIs
- Easy to build mobile apps or integrations later

### 5. Event-Driven Communication
- MQTT for device communication
- Event bus for internal system events
- Loose coupling between components

### 6. Testing Structure
- Unit tests for individual components
- Integration tests for workflows
- Test data and fixtures in separate directories

## Hardware Integration Strategy

When ready to integrate real ESP32 devices:

1. **No changes needed to**: Backend, AI, Healing, Database
2. **Minor changes to**: MQTT topics (if needed)
3. **Replace**: `src/simulator/` with real device firmware
4. **ESP32 will**: Publish to same MQTT topics, receive same commands

This is the beauty of the software-first approach!
