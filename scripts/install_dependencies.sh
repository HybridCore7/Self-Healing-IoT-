#!/bin/bash
# Installation script for Self-Healing IoT System (Linux/Mac)

echo "========================================"
echo "Installing Self-Healing IoT Dependencies"
echo "========================================"
echo ""

echo "Step 1: Upgrading pip..."
python3 -m pip install --upgrade pip
echo "✓ pip upgraded"
echo ""

echo "Step 2: Installing all dependencies..."
pip3 install \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    pydantic-settings \
    paho-mqtt \
    aiosqlite \
    python-dotenv \
    pyyaml \
    loguru \
    psutil \
    numpy \
    scipy \
    pandas \
    streamlit \
    plotly \
    scikit-learn

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""

echo "Verifying installation..."
python3 -c "import fastapi; print('✓ FastAPI')"
python3 -c "import paho.mqtt.client; print('✓ MQTT')"
python3 -c "import aiosqlite; print('✓ Database')"
python3 -c "import loguru; print('✓ Logging')"
python3 -c "import streamlit; print('✓ Dashboard')"
python3 -c "import sklearn; print('✓ ML (scikit-learn)')"
echo ""

echo "Next steps:"
echo "1. Initialize database: python3 scripts/setup_db.py"
echo "2. Start backend: python3 -m src.backend.main"
echo ""
