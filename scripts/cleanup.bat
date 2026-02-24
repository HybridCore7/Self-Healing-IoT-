@echo off
echo ========================================
echo Cleaning Up Self-Healing IoT Project
echo ========================================
echo.

echo Removing Python cache files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul

echo Removing accidental environment variable files...
if exist "MQTT_BROKER_HOST" del /q "MQTT_BROKER_HOST"
if exist "MQTT_BROKER_PORT" del /q "MQTT_BROKER_PORT"

echo Removing log files...
if exist "logs\healing.log" del /q "logs\healing.log"
if exist "logs\mqtt.log" del /q "logs\mqtt.log"
if exist "logs\system.log" del /q "logs\system.log"

echo Removing pytest cache...
if exist ".pytest_cache" rd /s /q ".pytest_cache"

echo Removing any .DS_Store files (Mac)...
del /s /q .DS_Store 2>nul

echo Removing any Thumbs.db files (Windows)...
del /s /q Thumbs.db 2>nul

echo.
echo ✓ Cleanup complete!
echo.
echo Removed:
echo - Python cache files (__pycache__, *.pyc)
echo - Accidental environment variable files
echo - Log files
echo - Test cache
echo.
pause
