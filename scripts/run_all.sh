#!/bin/bash
# Startup script for Self-Healing IoT System
# Starts all services in the correct order

echo "======================================"
echo "Self-Healing IoT System Startup"
echo "======================================"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Create necessary directories
mkdir -p logs data/telemetry data/processed models

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}.env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please update .env with your configuration${NC}"
fi

# Initialize database
echo -e "${GREEN}Initializing database...${NC}"
python scripts/setup_db.py

# Start MQTT Broker
echo -e "${GREEN}Starting MQTT Broker...${NC}"
if command -v mosquitto &> /dev/null; then
    mosquitto -c config/mosquitto.conf -d
    echo "MQTT Broker started"
else
    echo -e "${YELLOW}Mosquitto not found. Please install: sudo apt-get install mosquitto${NC}"
fi

# Wait a moment for broker to start
sleep 2

# Start Backend Server
echo -e "${GREEN}Starting Backend Server...${NC}"
python src/backend/main.py &
BACKEND_PID=$!
echo "Backend Server started (PID: $BACKEND_PID)"

# Wait for backend to be ready
sleep 3

# Start Device Simulator
echo -e "${GREEN}Starting Device Simulator...${NC}"
python src/simulator/device_simulator.py &
SIMULATOR_PID=$!
echo "Device Simulator started (PID: $SIMULATOR_PID)"

# Wait a moment
sleep 2

# Start Dashboard
echo -e "${GREEN}Starting Dashboard...${NC}"
streamlit run src/dashboard/app.py &
DASHBOARD_PID=$!
echo "Dashboard started (PID: $DASHBOARD_PID)"

echo ""
echo "======================================"
echo -e "${GREEN}All services started successfully!${NC}"
echo "======================================"
echo ""
echo "Service URLs:"
echo "  - Backend API: http://localhost:8000"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Dashboard: http://localhost:8501"
echo "  - MQTT Broker: localhost:1883"
echo ""
echo "Process IDs:"
echo "  - Backend: $BACKEND_PID"
echo "  - Simulator: $SIMULATOR_PID"
echo "  - Dashboard: $DASHBOARD_PID"
echo ""
echo "To stop all services, run: ./scripts/stop_all.sh"
echo "Or press Ctrl+C"
echo ""

# Keep script running
wait
