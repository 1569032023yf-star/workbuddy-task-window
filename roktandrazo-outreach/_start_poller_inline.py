"""Inline poller starter for BD Execution Host service.
Launches bd_ops_poller in a standalone thread."""
import os, sys, threading
BASE = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach"
sys.path.insert(0, BASE)
os.chdir(BASE)
from bd_ops_poller import start_poller
start_poller(daemon=True)
# Keep alive
import time
while True:
    time.sleep(60)