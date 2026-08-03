@echo off
REM BD Delivery Guard - Start Script
REM Launches background Python process to prevent Windows sleep during outreach windows

setlocal
cd /d "%~dp0"

set PYTHON=C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe

echo Starting BD Delivery Guard...
echo.
echo Normal window: 14:45-00:35 Asia/Shanghai (ES_CONTINUOUS + ES_SYSTEM_REQUIRED)
echo Critical window: 22:15-23:20 Asia/Shanghai (ES_CONTINUOUS + ES_SYSTEM_REQUIRED + ES_DISPLAY_REQUIRED)
echo.
echo NEVER calls SMTP. NEVER accesses customer data.
echo.

REM Check if already running
if exist "output\bd_delivery_guard.pid" (
    set /p PID=<"output\bd_delivery_guard.pid"
    tasklist /FI "PID eq !PID!" 2>NUL | find "!PID!" >NUL
    if !ERRORLEVEL! EQU 0 (
        echo [WARN] Delivery Guard already running (PID !PID!)
        echo Use stop_bd_delivery_guard.cmd to stop first.
        pause
        exit /b 1
    ) else (
        echo [INFO] Cleaning up stale PID file
        del "output\bd_delivery_guard.pid" 2>NUL
    )
)

REM Start guard in background
start "BD Delivery Guard" /MIN "%PYTHON%" "bd_delivery_guard.py" run

REM Wait a moment and check status
timeout /t 3 /nobreak >NUL

if exist "output\bd_delivery_guard.pid" (
    set /p PID=<"output\bd_delivery_guard.pid"
    echo [OK] Delivery Guard started (PID !PID!)
    echo Log: output\bd_delivery_guard.log
    echo Status: output\bd_delivery_guard_status.json
) else (
    echo [ERROR] Failed to start Delivery Guard
    echo Check output\bd_delivery_guard.log for details
)

endlocal
