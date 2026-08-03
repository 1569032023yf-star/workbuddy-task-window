@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHON=C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "SCRIPT=%~dp0bd_execution_host_service.py"
set "SERVICE_NAME=BDExecutionHost"

rem This installer requests the normal Windows UAC prompt.  It never enables
rem Auto Logon, stores a password, or changes registry credentials.
net session >nul 2>&1
if errorlevel 1 (
    echo Requesting Administrator approval through UAC...
    powershell -NoProfile -Command "Start-Process -FilePath '%ComSpec%' -ArgumentList '/c ""%~f0""' -Verb RunAs"
    exit /b %errorlevel%
)

if not exist "%PYTHON%" (
    echo [FAIL] Required Python executable was not found: %PYTHON%
    exit /b 1
)
if not exist "%SCRIPT%" (
    echo [FAIL] Service script was not found: %SCRIPT%
    exit /b 1
)

echo Installing %SERVICE_NAME% as Automatic with restart recovery...
"%PYTHON%" "%SCRIPT%" install
if errorlevel 1 exit /b %errorlevel%

sc start %SERVICE_NAME% >nul 2>&1
timeout /t 10 /nobreak >nul

"%PYTHON%" "%SCRIPT%" status
"%PYTHON%" -c "import json, pathlib, sys; p=pathlib.Path(r'%~dp0output\bd_execution_host_status.json'); s=json.loads(p.read_text(encoding='utf-8')); c=s.get('components',{}); ok=all(c.get(n,{}).get('healthy') for n in ('delivery_guard','ops_center','poller')); print('Startup health:', 'PASS' if ok else 'FAIL', c); sys.exit(0 if ok else 1)"
exit /b %errorlevel%
