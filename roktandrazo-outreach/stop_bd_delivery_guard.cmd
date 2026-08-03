@echo off
REM BD Delivery Guard - Stop Script

setlocal
cd /d "%~dp0"

set PYTHON=C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe

echo Stopping BD Delivery Guard...

if exist "output\bd_delivery_guard.pid" (
    "%PYTHON%" "bd_delivery_guard.py" stop
    timeout /t 2 /nobreak >NUL

    REM Force kill if still running
    if exist "output\bd_delivery_guard.pid" (
        set /p PID=<"output\bd_delivery_guard.pid"
        echo Force stopping PID !PID!...
        taskkill /PID !PID! /F 2>NUL
        del "output\bd_delivery_guard.pid" 2>NUL
        del "output\bd_delivery_guard.lock" 2>NUL
    )
    echo [OK] Delivery Guard stopped.
) else (
    set /p PID=<"output\bd_delivery_guard.pid"
    REM Check if process actually exists
    tasklist /FI "PID eq !PID!" 2>NUL | find "!PID!" >NUL
    if !ERRORLEVEL! EQU 0 (
        echo [WARN] PID file missing but process !PID! found. Force stopping...
        taskkill /PID !PID! /F 2>NUL
    ) else (
        echo [INFO] Delivery Guard is not running.
    )
)

REM Clear any stale locks
del "output\bd_delivery_guard.pid" 2>NUL
del "output\bd_delivery_guard.lock" 2>NUL

REM Confirm execution state cleared
echo.
echo Power requests should now be cleared.
echo Run status_bd_delivery_guard.cmd to verify.

endlocal
