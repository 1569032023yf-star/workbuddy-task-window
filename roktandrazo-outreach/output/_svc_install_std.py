"""Install BDExecutionHost using pywin32 standard InstallService API (correct binPath)."""
import sys, os
BASE = r"C:/Users/15690/WorkBuddy/2026-06-05-15-31-42/roktandrazo-outreach"
sys.path.insert(0, BASE)
import win32serviceutil, win32service

# ensure host exe + dll in place (idempotent)
import shutil
PY = r"C:/Users/15690/.workbuddy/binaries/python/versions/3.13.12"
for src, dst in [
    (os.path.join(PY, "Lib", "site-packages", "win32", "pythonservice.exe"), os.path.join(PY, "pythonservice.exe")),
    (os.path.join(PY, "Lib", "site-packages", "pywin32_system32", "pywintypes313.dll"), os.path.join(PY, "pywintypes313.dll")),
]:
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
        print("copied", os.path.basename(dst))

# delete old registration then install standard
try:
    win32serviceutil.StopService("BDExecutionHost")
except Exception:
    pass
try:
    import win32service
    hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
    try:
        win32service.DeleteService(win32service.OpenService(hscm, "BDExecutionHost", win32service.SERVICE_ALL_ACCESS))
        print("old service deleted")
    finally:
        win32service.CloseServiceHandle(hscm)
except Exception as e:
    print("delete skipped:", str(e)[:60])

win32serviceutil.InstallService(
    pythonClassString="bd_execution_host_service.BDExecutionHost",
    serviceName="BDExecutionHost",
    displayName="RoktAndRazoBDExecutionHost",
    startType=win32service.SERVICE_AUTO_START,
)
print("INSTALLED via pywin32 standard API")
