# Quick Setup Guide - Windows

## Issue: Missing Dependencies

You're seeing this error because Python packages aren't installed yet.

## Solution: Install Dependencies Step-by-Step

### Step 1: Install Core Dependencies (No C++ compiler needed)

```bash
pip install loguru fastapi uvicorn[standard] pydantic pydantic-settings paho-mqtt aiosqlite python-dotenv pyyaml psutil streamlit plotly pandas
```

### Step 2: Install scikit-learn (Pre-built wheel)

```bash
pip install scikit-learn
```

If scikit-learn fails with "Microsoft Visual C++ 14.0 required", use a pre-built wheel:

```bash
# For Python 3.11
pip install scikit-learn --only-binary :all:

# OR download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#scikit-learn
```

### Step 3: Verify Installation

```bash
python -c "import sklearn; print('scikit-learn:', sklearn.__version__)"
python -c "import fastapi; print('FastAPI installed')"
python -c "import paho.mqtt.client; print('MQTT installed')"
```

### Step 4: Run Backend

```bash
python -m src.backend.main
```

## Alternative: Use Conda (Recommended for Windows)

If you have Anaconda/Miniconda:

```bash
conda create -n iot-system python=3.11
conda activate iot-system
conda install scikit-learn numpy scipy
pip install fastapi uvicorn pydantic pydantic-settings paho-mqtt aiosqlite python-dotenv pyyaml loguru psutil streamlit plotly pandas
```

## Minimal Setup (Without ML)

If you just want to test the backend without ML:

1. Comment out scikit-learn imports temporarily
2. Install other packages
3. Run backend

The system will work without ML, but anomaly detection will be disabled.

## What's Installing Now

The command is currently installing these packages:
- loguru (logging)
- fastapi (web framework)
- uvicorn (ASGI server)
- pydantic (data validation)
- paho-mqtt (MQTT client)
- aiosqlite (async SQLite)
- python-dotenv (environment variables)
- pyyaml (YAML parsing)
- psutil (system metrics)
- streamlit (dashboard)
- plotly (charts)
- pandas (data manipulation)

After this completes, we'll install scikit-learn separately.
