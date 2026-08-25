#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply task alignment: create 3 stage tasks, disable 2 legacy send tasks."""
import os, subprocess

OUTDIR = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\output"
RESULT = os.path.join(OUTDIR, "_apply_tasks_result.txt")
PYTHON = r"C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe"
SCRIPT = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\bd_orchestrator.py"
WORKDIR = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach"
SID = r"S-1-5-21-5926390-557196042-3608508572-1001"

OUT = []
def log(msg):
    OUT.append(str(msg))
    with open(RESULT, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")

def task_xml(name, desc, start, stage):
    return f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.3" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>{desc}</Description>
    <URI>\\{name}</URI>
  </RegistrationInfo>
  <Principals>
    <Principal id="Author">
      <UserId>{SID}</UserId>
      <LogonType>InteractiveToken</LogonType>
    </Principal>
  </Principals>
  <Settings>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <StartWhenAvailable>true</StartWhenAvailable>
    <IdleSettings>
      <Duration>PT10M</Duration>
      <WaitTimeout>PT1H</WaitTimeout>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <UseUnifiedSchedulingEngine>true</UseUnifiedSchedulingEngine>
  </Settings>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>{start}</StartBoundary>
      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>{PYTHON}</Command>
      <Arguments>&quot;{SCRIPT}&quot; --stage {stage} --live</Arguments>
      <WorkingDirectory>{WORKDIR}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
'''

def main():
    if os.path.exists(RESULT):
        os.remove(RESULT)
    log("=== APPLY START pid=%s ===" % os.getpid())

    # 1) write XML files (UTF-16 with BOM)
    plans = [
        ("RoktRazo-BD-PreSend",  "BD Orchestrator stage pre-send (22:30 Asia/Shanghai)", "2026-08-20T22:30:00+08:00", "pre-send"),
        ("RoktRazo-BD-Outreach", "BD Orchestrator stage outreach (23:00 Asia/Shanghai)", "2026-08-20T23:00:00+08:00", "outreach"),
        ("RoktRazo-BD-PostSend", "BD Orchestrator stage post-send (00:10 Asia/Shanghai)", "2026-08-21T00:10:00+08:00", "post-send"),
    ]
    xml_paths = {}
    for name, desc, start, stage in plans:
        p = os.path.join(OUTDIR, "_task_%s.xml" % name)
        xml = task_xml(name, desc, start, stage)
        with open(p, "w", encoding="utf-16") as f:
            f.write(xml)
        xml_paths[name] = p
        log("XML WRITTEN: %s @ %s -> --stage %s --live" % (name, start, stage))

    # 2) register tasks
    log("")
    log("=== REGISTER ===")
    for name in ("RoktRazo-BD-PreSend", "RoktRazo-BD-Outreach", "RoktRazo-BD-PostSend"):
        r = subprocess.run(["schtasks", "/create", "/tn", name, "/xml", xml_paths[name], "/f"],
                           capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
        log("  CREATE %s rc=%s: %s" % (name, r.returncode, (r.stdout or r.stderr).strip()[:200]))

    # 3) disable legacy send tasks
    log("")
    log("=== DISABLE LEGACY ===")
    for legacy in ("RoktRazo-BD-Daily-Outreach", "Roktandrazo_Daily_Outreach"):
        r = subprocess.run(["schtasks", "/change", "/tn", legacy, "/disable"],
                           capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
        log("  DISABLE %s rc=%s: %s" % (legacy, r.returncode, (r.stdout or r.stderr).strip()[:200]))

    # 4) verify
    log("")
    log("=== VERIFY ===")
    for name in ("RoktRazo-BD-PreSend", "RoktRazo-BD-Outreach", "RoktRazo-BD-PostSend",
                 "RoktRazo-BD-Daily-Outreach", "Roktandrazo_Daily_Outreach"):
        r = subprocess.run(["schtasks", "/query", "/tn", name, "/xml"],
                           capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
        if r.returncode == 0:
            x = r.stdout
            import re
            en = "ENABLED"
            if "<Enabled>false</Enabled>" in x:
                en = "DISABLED"
            m = re.search(r"<StartBoundary>([^<]+)</StartBoundary>", x)
            start = m.group(1) if m else "?"
            m2 = re.search(r"<Arguments>([^<]+)</Arguments>", x)
            args = m2.group(1) if m2 else "?"
            log("  %s | %s | start=%s" % (name, en, start))
            log("      args: %s" % args)
        else:
            log("  %s | QUERY FAILED rc=%s: %s" % (name, r.returncode, r.stderr.strip()[:200]))

    log("")
    log("=== APPLY DONE ===")

if __name__ == "__main__":
    main()
