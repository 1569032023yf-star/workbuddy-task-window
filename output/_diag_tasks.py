#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose why Schedule.Service COM is access-denied even elevated; try alternatives."""
import os, sys, ctypes, traceback, subprocess

RESULT = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\output\_diag_tasks_result.txt"
OUT = []
def log(msg):
    OUT.append(str(msg))
    try:
        with open(RESULT, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except Exception:
        pass

def main():
    if os.path.exists(RESULT):
        try:
            os.remove(RESULT)
        except Exception:
            pass
    log("=== DIAG START pid=%s ===" % os.getpid())

    # 1) elevation status
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        log("IsUserAnAdmin=%s" % is_admin)
    except Exception as e:
        log("IsUserAnAdmin ERR %s" % e)

    # 2) try COM with explicit CoInitializeSecurity
    log("")
    log("--- try Schedule.Service with CoInitializeSecurity ---")
    try:
        import pythoncom, win32com.client
        try:
            ctypes.windll.ole32.CoInitializeSecurity(None, -1, None, None, 0, 3, None, 0)
            log("CoInitializeSecurity OK")
        except Exception as e:
            log("CoInitializeSecurity note: %s" % e)
        pythoncom.CoInitialize()
        sched = win32com.client.Dispatch("Schedule.Service")
        sched.Connect(".")
        log("Connect OK")
        root = sched.GetFolder("\\")
        log("GetFolder OK")
        tasks = root.GetTasks(0)
        log("GetTasks OK count=%d" % tasks.Count)
        for i in range(tasks.Count):
            t = tasks.Item(i + 1)
            log("  task: %s" % t.Name)
    except Exception as e:
        log("COM FAILED: %s" % e)
        log(traceback.format_exc())

    # 3) direct write test to Tasks dir
    log("")
    log("--- write test to C:\\Windows\\System32\\Tasks ---")
    try:
        test_path = r"C:\Windows\System32\Tasks\_wb_write_test.tmp"
        with open(test_path, "w", encoding="utf-16") as f:
            f.write("x")
        os.remove(test_path)
        log("WRITE OK (System32\\Tasks writable)")
    except Exception as e:
        log("WRITE FAILED: %s" % e)

    # 4) schtasks availability from elevated process
    log("")
    log("--- schtasks from elevated python ---")
    try:
        r = subprocess.run(["schtasks", "/query", "/fo", "LIST"],
                           capture_output=True, text=True, timeout=30)
        log("schtasks rc=%s outlen=%s errlen=%s" % (r.returncode, len(r.stdout), len(r.stderr)))
        for line in r.stdout.splitlines():
            if any(k in line.lower() for k in ("rokt", "bd", "outreach", "orchestrat")):
                log("  " + line)
        if r.stderr.strip():
            log("stderr: " + r.stderr.strip()[:500])
    except Exception as e:
        log("schtasks ERR: %s" % e)

    log("")
    log("=== DIAG DONE ===")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        log("FATAL %s" % traceback.format_exc())
