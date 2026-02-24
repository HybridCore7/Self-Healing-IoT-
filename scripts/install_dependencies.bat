@echo off
echo ========================================
echo Installing Self-Healing IoT Dependencies
echo ========================================
echo.

echo Step 1: Upgrading pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ERROR: Failed to upgrade pip
    pause
    exit /b 1
)
echo ✓ pip upgraded
echo.

echo Step 2: Installing core web framework...
pip install fastapi uvicorn[standard]
if %errorlevel% neq 0 (
    echo ERROR: Failed to install FastAPI
    pause
    exit /b 1
)
echo ✓ FastAPI installed
echo.

echo Step 3: Installing data validation...
pip install pydantic pydantic-settings
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Pydantic
    pause
    exit /b 1
)
echo ✓ Pydantic installed
echo.

echo Step 4: Installing MQTT client...
pip install paho-mqtt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install MQTT client
    pause
    exit /b 1
)
echo ✓ MQTT client installed
echo.

echo Step 5: Installing database...
pip install aiosqlite
if %errorlevel% neq 0 (
    echo ERROR: Failed to install aiosqlite
    pause
    exit /b 1
)
echo ✓ Database installed
echo.

echo Step 6: Installing utilities...
pip install python-dotenv pyyaml loguru psutil
if %errorlevel% neq 0 (
    echo ERROR: Failed to install utilities
    pause
    exit /b 1
)
echo ✓ Utilities installed
echo.

echo Step 7: Installing data science packages...
pip install numpy scipy pandas
if %errorlevel% neq 0 (
    echo ERROR: Failed to install data packages
    pause
    exit /b 1
)
echo ✓ Data packages installed
echo.

echo Step 8: Installing dashboard...
pip install streamlit plotly
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dashboard
    pause
    exit /b 1
)
echo ✓ Dashboard installed
echo.

echo Step 9: Installing scikit-learn (this may take a while)...
pip install scikit-learn --only-binary :all:
if %errorlevel% neq 0 (
    echo WARNING: scikit-learn installation failed
    echo The system will work but ML anomaly detection will be disabled
    echo.
    echo To install scikit-learn manually:
    echo   Option 1: Install Visual C++ Build Tools from:
    echo   https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo.
    echo   Option 2: Use Conda:
    echo   conda install scikit-learn
    echo.
) else (
    echo ✓ scikit-learn installed
)
echo.

echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Verifying installation...
python -c "import fastapi; print('✓ FastAPI')"
python -c "import paho.mqtt.client; print('✓ MQTT')"
python -c "import aiosqlite; print('✓ Database')"
python -c "import loguru; print('✓ Logging')"
python -c "import streamlit; print('✓ Dashboard')"
python -c "try: import sklearn; print('✓ ML (scikit-learn)'); except: print('✗ ML (scikit-learn not installed)')"
echo.

echo Next steps:
echo 1. Initialize database: python scripts\setup_db.py
echo 2. Start backend: python -m src.backend.main
echo.
pause
