@echo off
echo ========================================
echo Starting Self-Healing IoT Backend
echo ========================================
echo.

echo Starting FastAPI backend server...
echo Server will run on http://localhost:8000
echo API docs available at http://localhost:8000/docs
echo.
echo Press CTRL+C to stop the server
echo.

python -m src.backend.main
