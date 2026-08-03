@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHON=C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=system"

if /I not "%MODE%"=="system" if /I not "%MODE%"=="display" (
    echo Usage: %~nx0 [system^|display]
    exit /b 2
)
if not exist "%PYTHON%" (
    echo Python not found: %PYTHON%
    exit /b 1
)

echo Starting Modern Standby test in %MODE% mode.
echo Log: output\modern_standby_test.log
echo Stop with Ctrl+C after the 30-minute manual display-off test.
"%PYTHON%" "%~dp0modern_standby_guard_test.py" --mode "%MODE%"
exit /b %errorlevel%
