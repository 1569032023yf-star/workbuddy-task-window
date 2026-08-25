import subprocess, time, sys

OUT = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\output\_svc_trigger.result.txt"
def log(*a):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(" ".join(str(x) for x in a) + "\n")

open(OUT, "w", encoding="utf-8").close()

tasks = [
    ("RoktRazo-BD-PreSend", "22:30"),
    ("RoktRazo-BD-Outreach", "23:00"),
    ("RoktRazo-BD-PostSend", "00:10"),
]

log("=== TRIGGER via Task Scheduler (schtasks /run) ===")
for tn, slot in tasks:
    r = subprocess.run(["schtasks", "/run", "/tn", tn],
                       capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
    log(f"  [{slot}] {tn}: run rc={r.returncode} out={r.stdout.strip()} err={r.stderr.strip()}")
    time.sleep(3)

log("")
log("=== QUERY Last Result / Next Run (schtasks /query) ===")
for tn, slot in tasks:
    r = subprocess.run(["schtasks", "/query", "/tn", tn, "/fo", "LIST"],
                       capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
    out = r.stdout
    for line in out.splitlines():
        if any(k in line for k in ("TaskName", "Status", "Last Run Time", "Last Result", "Next Run Time")):
            log(f"  [{slot}] {line.strip()}")
    log(f"  [{slot}] (query rc={r.returncode})")
    log("")
log("DONE")
