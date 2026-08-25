import ctypes, time, sys

py = r"C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe"
script = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\output\_svc_trigger.py"
result = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\output\_svc_trigger.result.txt"

rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", py, script, None, 0)
if rc <= 32:
    print("ELEVATE_FAILED", rc)
    sys.exit(1)

# wait for DONE marker in result file
for _ in range(60):
    try:
        with open(result, "r", encoding="utf-8") as f:
            txt = f.read()
        if "DONE" in txt:
            print(txt)
            break
    except FileNotFoundError:
        pass
    time.sleep(1)
else:
    print("TIMEOUT waiting for elevated child")
    try:
        with open(result, "r", encoding="utf-8") as f:
            print(f.read())
    except Exception:
        pass
