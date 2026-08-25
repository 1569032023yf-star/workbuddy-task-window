#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launch _diag_tasks.py elevated and wait for result."""
import ctypes, sys, time, os

RESULT = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\output\_diag_tasks_result.txt"
PYTHON = r"C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe"
HELPER = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\output\_diag_tasks.py"

if os.path.exists(RESULT):
    try:
        os.remove(RESULT)
    except Exception:
        pass

rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", PYTHON, '"%s"' % HELPER, None, 0)
if rc <= 32:
    print("ELEVATION_FAILED rc=%s" % rc)
    sys.exit(1)
print("ELEVATION_REQUESTED rc=%s..." % rc)

deadline = time.time() + 120
while time.time() < deadline:
    if os.path.exists(RESULT):
        try:
            with open(RESULT, encoding="utf-8") as f:
                content = f.read()
        except Exception:
            time.sleep(1)
            continue
        if "DIAG DONE" in content or "FATAL" in content:
            print("=== DIAG FINISHED ===")
            print(content)
            sys.exit(0)
    time.sleep(1)

print("DIAG TIMEOUT")
if os.path.exists(RESULT):
    with open(RESULT, encoding="utf-8") as f:
        print(f.read())
sys.exit(2)
