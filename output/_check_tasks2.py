import os, winreg, subprocess

print("=== Tasks dir listing (first 50) ===")
tasks_root = r"C:/Windows/System32/Tasks"
try:
    entries = os.listdir(tasks_root)
    print(f"  count={len(entries)}")
    for e in sorted(entries)[:50]:
        print(f"  {e}")
except Exception as e:
    print("  ERROR:", e)

print()
print("=== Service state via pywin32 (if available) ===")
try:
    import win32serviceutil, win32service
    def qs(name):
        try:
            s = win32serviceutil.QueryServiceStatus(name)
            # state codes: 1 stopped, 2 start pending, 3 stop pending, 4 running
            states = {1:"STOPPED",2:"START_PENDING",3:"STOP_PENDING",4:"RUNNING"}
            return states.get(s[1], s[1])
        except Exception as e:
            return f"ERR {e}"
    print("  BDExecutionHost state:", qs("BDExecutionHost"))
except ImportError:
    print("  pywin32 not available in managed python")

print()
print("=== Service Start type change attempt (read-only first) ===")
try:
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\BDExecutionHost", 0, winreg.KEY_READ)
    for v in ("Start","Type","DisplayName"):
        try:
            val, _ = winreg.QueryValueEx(key, v)
            print(f"  {v} = {val}")
        except OSError:
            print(f"  {v} = <missing>")
    winreg.CloseKey(key)
except Exception as e:
    print("  ERROR:", e)
