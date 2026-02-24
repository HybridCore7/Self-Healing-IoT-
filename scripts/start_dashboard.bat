@echo off
echo ========================================
echo Starting Self-Healing IoT Dashboard
echo ========================================
echo.

echo Checking if backend is running...
curl -s http://localhost:8000/api/health/ > nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Backend server is not running!
    echo Please start the backend first:
    echo   python -m src.backend.main
    echo.
    echo Continue anyway? (Dashboard will show backend offline)
    pause
)

echo ✓ Backend check complete
echo.

echo Starting Streamlit dashboard...
echo Dashboard will open in your browser at http://localhost:8501
echo.
echo Press CTRL+C to stop the dashboard
echo.

python -m streamlit run src\dashboard\app.py
