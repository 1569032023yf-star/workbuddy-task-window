@echo off
REM ====================================================
REM BD Execution Host — Elevated Service Installer
REM Run with Administrator privileges only
REM ====================================================

set PYTHON=C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe
set SCRIPT_DIR=C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach
set LOG=%SCRIPT_DIR%\output\bd_execution_host_install.log

echo ============================================ > "%LOG%"
echo BD Execution Host Install >> "%LOG%"
echo %date% %time% >> "%LOG%"
echo ============================================ >> "%LOG%"

echo [1/5] Stopping existing guard...
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq BD Delivery Guard" 2>nul
del "%SCRIPT_DIR%\output\bd_delivery_guard.pid" 2>nul
del "%SCRIPT_DIR%\output\bd_delivery_guard.lock" 2>nul
echo   Done >> "%LOG%"

echo [2/5] Ensuring poller inline script exists...
if not exist "%SCRIPT_DIR%\_start_poller_inline.py" (
    "%PYTHON%" -c "import sys; sys.path.insert(0,r'%SCRIPT_DIR%'); from bd_execution_host_service import _create_poller_script; _create_poller_script()" >> "%LOG%" 2>&1
)
echo   Done >> "%LOG%"

echo [3/5] Installing service via pywin32...
"%PYTHON%" -c "import win32service,pywintypes,time;SVC='BDExecutionHost';BP=r'%PYTHON% %SCRIPT_DIR%\bd_execution_host_service.py';
try:
 hs=win32service.OpenSCManager(None,None,win32service.SC_MANAGER_ALL_ACCESS)
 try:
  s=win32service.OpenService(hs,SVC,win32service.SERVICE_ALL_ACCESS)
  win32service.ControlService(s,win32service.SERVICE_CONTROL_STOP)
  time.sleep(2)
  win32service.DeleteService(s)
  s.Close()
  print('Existing removed')
 except pywintypes.error as e:
  if e.winerror!=1060: print(e)
 hs.Close()
except Exception as e:
 print(e)
hs=win32service.OpenSCManager(None,None,win32service.SC_MANAGER_CREATE_SERVICE)
s=win32service.CreateService(hs,SVC,'BD Execution Host',win32service.SERVICE_ALL_ACCESS,win32service.SERVICE_WIN32_OWN_PROCESS,win32service.SERVICE_AUTO_START,win32service.SERVICE_ERROR_NORMAL,BP,None,None,None,None,None)
print('Service created')
fap=win32service.SERVICE_FAILURE_ACTIONS()
fap.dwResetPeriod=86400
fap.cActions=3
fap.lpsaActions=[(1,60000),(1,60000),(1,60000)]
try: win32service.ChangeServiceConfig2(s,2,fap)
except: pass
s.Close();hs.Close()
print('Install OK')" >> "%LOG%" 2>&1

if %errorlevel% NEQ 0 (
    echo [FAIL] Service creation failed >> "%LOG%"
    type "%LOG%"
    pause
    exit /b 1
)

echo [4/5] Starting service...
"%PYTHON%" -c "import win32serviceutil,time;win32serviceutil.StartService('BDExecutionHost');time.sleep(3);s=win32serviceutil.QueryServiceStatus('BDExecutionHost');n={1:'STOPPED',2:'STARTING',4:'RUNNING'};print('Status: '+n.get(s[1],str(s[1])))" >> "%LOG%" 2>&1

echo [5/5] Done >> "%LOG%"
echo. >> "%LOG%"
echo Service installed. Check: %PYTHON% %SCRIPT_DIR%\bd_execution_host_service.py status >> "%LOG%"

type "%LOG%"
echo.
echo Press any key to close...
pause >nul
