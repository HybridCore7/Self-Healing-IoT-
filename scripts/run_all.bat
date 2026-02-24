@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo.
echo ============================================================
echo  Self-Healing IoT Sensor Network - Startup Script
echo ============================================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

REM --- Set project root ---
SET "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"

REM --- Activate virtual environment if it exists ---
IF EXIST "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
) ELSE (
    echo [WARN] No venv found. Using system Python.
    echo        Run: python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
)

REM --- Initialize database ---
echo.
echo [STEP 1/4] Initializing database...
python scripts\setup_db.py
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Database initialization failed
    pause
    exit /b 1
)
echo [OK] Database ready

REM --- Start Backend API (in new window) ---
echo.
echo [STEP 2/4] Starting Backend API server...
start "IoT Backend" cmd /k "python -m src.backend.main"
echo [OK] Backend starting at http://localhost:8000

REM --- Wait for backend to come up ---
echo [INFO] Waiting 4 seconds for backend to start...
timeout /t 4 /nobreak >nul

REM --- Start Simulator (in new window) ---
echo.
echo [STEP 3/4] Starting Device Simulator...
start "IoT Simulator" cmd /k "python -m src.simulator.device_simulator"
echo [OK] Simulator started (5 virtual devices)

REM --- Start Dashboard (in new window) ---
echo.
echo [STEP 4/4] Starting Streamlit Dashboard...
start "IoT Dashboard" cmd /k "streamlit run src/dashboard/app.py"
echo [OK] Dashboard starting at http://localhost:8501

echo.
echo ============================================================
echo  All services started!
echo.
echo  Backend API  : http://localhost:8000
echo  API Docs     : http://localhost:8000/docs
echo  Dashboard    : http://localhost:8501
echo ============================================================
echo.
echo [TIP] Close the individual terminal windows to stop each service.
echo.
pause
