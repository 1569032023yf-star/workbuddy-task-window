@echo off
REM BD Delivery Guard - Status Script

setlocal
cd /d "%~dp0"

set PYTHON=C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe

echo ============================================
echo   BD Delivery Guard - Status
echo ============================================
echo.

REM Check if running
if exist "output\bd_delivery_guard.pid" (
    set /p PID=<"output\bd_delivery_guard.pid"
    tasklist /FI "PID eq !PID!" 2>NUL | find "!PID!" >NUL
    if !ERRORLEVEL! EQU 0 (
        echo [STATUS] RUNNING (PID !PID!)
    ) else (
        echo [STATUS] STOPPED (stale PID file)
    )
) else (
    echo [STATUS] STOPPED (no PID file)
)

echo.

REM Show detailed status from JSON
"%PYTHON%" "bd_delivery_guard.py" status

echo.
echo --------------------------------------------
echo Recent logs (last 10 lines):
echo --------------------------------------------
if exist "output\bd_delivery_guard.log" (
    powershell -Command "Get-Content 'output\bd_delivery_guard.log' -Tail 10"
) else (
    echo No log file found.
)

echo.
echo ============================================
echo Current Power Plan:
echo ============================================
powercfg /getactivescheme

echo.
echo System Uptime:
echo ============================================
powershell -Command "(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime"

endlocal
