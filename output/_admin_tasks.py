#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Elevated helper: enumerate + align Windows Scheduled Tasks + set BDExecutionHost service to Manual.

Run via ShellExecuteW(runas) from the main agent. Writes results to _admin_tasks_result.txt
"""
import os, sys, winreg, traceback

RESULT = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\output\_admin_tasks_result.txt"
PYTHON = r"C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe"
SCRIPT = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\bd_orchestrator.py"
OUTREACH_DIR = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach"

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
    log("=== ADMIN HELPER START pid=%s ===" % os.getpid())

    # 1) enumerate scheduled tasks (recursive), find Rokt/BD/Outreach
    log("")
    log("=== [1] EXISTING TASKS (match rokt/bd/outreach/orchestrat) ===")
    try:
        import win32com.client
        sched = win32com.client.Dispatch("Schedule.Service")
        sched.Connect(".")
        found = []

        def walk(folder, depth=0):
            try:
                tasks = folder.GetTasks(0)
                for t in tasks:
                    name = t.Name
                    if any(k in name.lower() for k in ("rokt", "bd", "outreach", "orchestrat")):
                        xml = ""
                        try:
                            xml = t.Definition.Xml
                        except Exception:
                            try:
                                xml = t.Xml
                            except Exception:
                                xml = "<no xml>"
                        found.append((folder.Path, name, t.Enabled, xml))
                for sub in folder.GetFolders(0):
                    walk(sub, depth + 1)
            except Exception as e:
                log("  walk error %s: %s" % (folder.Path, e))

        walk(sched.GetFolder("\\"))
        if not found:
            log("  (no Rokt/BD tasks found)")
        for fp, nm, en, xml in found:
            import re
            m = re.search(r"<StartBoundary>([^<]+)</StartBoundary>", xml)
            start = m.group(1) if m else "?"
            log("  TASK: %s\\%s | enabled=%s | start=%s" % (fp, nm, en, start))
    except Exception as e:
        log("  ERROR enumerating: %s" % e)
        traceback.print_exc(file=sys.stdout)
        log("")

    # 2) create/update three tasks
    log("")
    log("=== [2] CREATE/UPDATE TASKS (Asia/Shanghai local time) ===")
    plans = [
        ("RoktRazo-BD-PreSend",  "22:30", "pre-send"),
        ("RoktRazo-BD-Outreach", "23:00", "outreach"),
        ("RoktRazo-BD-PostSend", "00:10", "post-send"),
    ]
    try:
        import win32com.client
        sched = win32com.client.Dispatch("Schedule.Service")
        sched.Connect(".")
        root = sched.GetFolder("\\")
        for name, start, stage in plans:
            hh, mm = start.split(":")
            td = sched.NewTask(0)
            td.RegistrationInfo.Description = "BD Orchestrator stage %s (RoktRazo)" % stage
            td.RegistrationInfo.Author = "RoktRazoBD"
            st = td.Settings
            st.MultipleInstancesPolicy = 1  # IgnoreNew
            st.DisallowStartIfOnBatteries = False
            st.StopIfGoingOnBatteries = False
            st.StartWhenAvailable = True
            st.Enabled = True
            st.Hidden = True
            st.ExecutionTimeLimit = "PT2H"
            tr = td.Triggers.Create(2)  # DAILY
            tr.StartBoundary = "2026-08-20T%s:%s:00" % (hh, mm)
            tr.DaysInterval = 1
            tr.Enabled = True
            ac = td.Actions.Create(0)  # EXEC
            ac.Path = PYTHON
            ac.Arguments = '"%s" --stage %s' % (SCRIPT, stage)
            ac.WorkingDirectory = OUTREACH_DIR
            root.RegisterTaskDefinition(name, td, 6, None, None, 3, None)  # CREATE_OR_UPDATE, INTERACTIVE_TOKEN
            log("  CREATED/UPDATED: %s @ %s -> --stage %s" % (name, start, stage))
    except Exception as e:
        log("  ERROR creating tasks: %s" % e)
        traceback.print_exc(file=sys.stdout)

    # 3) disable old 09:00 task if present (avoid duplicate scheduling)
    log("")
    log("=== [3] DISABLE LEGACY 09:00 TASK (if any) ===")
    try:
        import win32com.client
        sched = win32com.client.Dispatch("Schedule.Service")
        sched.Connect(".")
        root = sched.GetFolder("\\")
        for legacy in ("RoktRazo-BD-Daily-Outreach", "RoktRazo-BD-Daily-Outreach2"):
            try:
                t = root.GetTask(legacy)
                if t.Enabled:
                    t.Enabled = False
                    log("  DISABLED: %s" % legacy)
                else:
                    log("  ALREADY DISABLED: %s" % legacy)
            except Exception as e:
                log("  (no legacy task %s: %s)" % (legacy, e))
    except Exception as e:
        log("  ERROR disabling legacy: %s" % e)

    # 4) set BDExecutionHost service Start=3 (Manual) - keep registration, never auto-run
    log("")
    log("=== [4] BDExecutionHost SERVICE -> MANUAL (keep registration) ===")
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SYSTEM\CurrentControlSet\Services\BDExecutionHost",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 3)
        winreg.CloseKey(key)
        log("  SET Start=3 (Manual). Service will NOT auto-start. Registration kept.")
    except Exception as e:
        log("  ERROR setting service Start: %s" % e)

    log("")
    log("=== ADMIN HELPER DONE ===")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        log("FATAL: %s" % traceback.format_exc())
