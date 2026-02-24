@echo off
echo ========================================
echo Starting IoT Device Simulator
echo ========================================
echo.

echo This will create 3 virtual IoT devices that:
echo - Auto-register with the backend
echo - Send realistic telemetry data
echo - Simulate random faults
echo - Trigger self-healing actions
echo.

echo Make sure backend is running first!
echo.
pause

echo Starting simulator...
echo Press CTRL+C to stop
echo.

python -m src.simulator.device_simulator
