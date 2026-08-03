@echo off
setlocal
cd /d "%~dp0"
set PYTHON=C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe

echo ============================================
echo   BD Ops Center + Delivery Guard Starter
echo ============================================
echo.

REM Start Delivery Guard first
echo [1/2] Starting BD Delivery Guard...
call "%~dp0start_bd_delivery_guard.cmd"
echo.

REM Start Ops Center
netstat -ano | findstr ":8765" | findstr "LISTENING" >nul
if %errorlevel%==0 (
  echo [2/2] BD Ops Center is already running on port 8765.
  start http://127.0.0.1:8765/
  exit /b 0
)

echo [2/2] Starting BD Ops Center on http://127.0.0.1:8765/
start "BD Ops Center" /MIN "%PYTHON%" bd_review_server.py --port 8765
echo %date% %time% Started > output\bd_ops_center.pid
ping -n 3 127.0.0.1 >nul
start http://127.0.0.1:8765/

echo.
echo ============================================
echo   All services started successfully!
echo   - Ops Center: http://127.0.0.1:8765/
echo   - Delivery Guard: status_bd_delivery_guard.cmd
echo   - Poller: integrated with Ops Center
echo ============================================
