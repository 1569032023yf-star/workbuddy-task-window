#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump existing Rokt/BD task XMLs for inspection."""
import os, sys, subprocess

OUTDIR = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\output"
RESULT = os.path.join(OUTDIR, "_dump_tasks_result.txt")
TASKS = [
    r"\Roktandrazo_Daily_Outreach",
    r"\RoktRazo-BD-Daily-Outreach",
    r"\RoktRazo-BD-Inbox-Morning",
    r"\RoktRazo-BD-Inventory-Recovery",
    r"\RoktRazo-BD-Morning",
    r"\RoktRazo-BD-PostSend-Poll",
]
OUT = []
def log(msg):
    OUT.append(str(msg))
    with open(RESULT, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")

def main():
    if os.path.exists(RESULT):
        os.remove(RESULT)
    log("=== DUMP START pid=%s ===" % os.getpid())
    for tn in TASKS:
        log("")
        log("##### TASK: %s #####" % tn)
        try:
            r = subprocess.run(["schtasks", "/query", "/tn", tn, "/xml"],
                               capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
            if r.returncode == 0:
                log(r.stdout)
            else:
                log("  QUERY FAILED rc=%s: %s" % (r.returncode, r.stderr.strip()[:300]))
        except Exception as e:
            log("  ERR: %s" % e)
    log("")
    log("=== DUMP DONE ===")

if __name__ == "__main__":
    main()
