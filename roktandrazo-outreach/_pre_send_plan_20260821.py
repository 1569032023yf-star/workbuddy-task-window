"""BD Production Pre-Send — 2026-08-21. NO SMTP. Read frozen snapshot, else NO_BATCH_TODAY."""
import sqlite3
import os
from datetime import datetime

WORKSPACE = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach'
DB_PATH = os.path.join(WORKSPACE, 'data', 'bd_leads.db')
OUTPUT_DIR = os.path.join(WORKSPACE, 'output')

ALLOWED_STATES = ['TN', 'AR', 'KY', 'OH', 'IN', 'MN', 'NE', 'NC', 'OR', 'CO']

today_str = datetime.now().strftime('%Y%m%d')
report_date = datetime.now().strftime('%Y-%m-%d')
batch_id = f'new_outreach_{today_str}_et1000'
snapshot_name = f'frozen_{batch_id}.json'

candidate_paths = [
    os.path.join(OUTPUT_DIR, snapshot_name),
    os.path.join(WORKSPACE, 'data', snapshot_name),
]

print(f"=== BD Production Pre-Send — {report_date} (ET 09:30 / CST 21:30) ===")
print(f"Batch ID: {batch_id}")
print(f"Looking for frozen snapshot '{snapshot_name}' ...")

snapshot_path = None
for p in candidate_paths:
    if os.path.exists(p):
        snapshot_path = p
        break

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def upsert_config(key, value):
    cur.execute(
        "INSERT INTO system_config (key, value, updated_at) VALUES (?, ?, datetime('now')) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')",
        (key, value),
    )

if snapshot_path is None:
    # === NO_BATCH_TODAY path ===
    print(f"\n>>> NO_BATCH_TODAY: frozen snapshot '{snapshot_name}' NOT FOUND.")
    print("No 21:10 CST freeze snapshot exists for today. Clean exit.")

    ph = ','.join('?' for _ in ALLOWED_STATES)
    cur.execute(
        f"SELECT COUNT(*) FROM leads WHERE state IN ({ph}) "
        "AND email IS NOT NULL AND email != '' AND (sent_at IS NULL OR sent_at = '')",
        ALLOWED_STATES,
    )
    raw_eligible = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM send_log WHERE outreach_batch_date = ?",
        (today_str,),
    )
    today_sent = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM final_send_plan WHERE outreach_batch_date = ?",
        (today_str,),
    )
    today_plan = cur.fetchone()[0]

    upsert_config('preflight_status', 'no_batch')
    upsert_config('preflight_verdict', 'NO_BATCH_TODAY')
    upsert_config('preflight_last_run', datetime.now().strftime('%Y-%m-%d %H:%M:%S CST'))
    upsert_config('preflight_batch_id', batch_id)
    upsert_config('preflight_follow_up', '0')
    conn.commit()

    cur.execute("SELECT key, value, updated_at FROM system_config WHERE key='preflight_status'")
    row = cur.fetchone()
    print(f"system_config: {dict(row)}")

    report_path = os.path.join(OUTPUT_DIR, f'pre_send_report_{report_date}_2130.md')
    report = f"""# BD Pre-Send Report — {report_date} (ET 09:30 / CST 21:30)

**Batch ID:** `{batch_id}`
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Asia/Shanghai
**Status:** ❌ NO_BATCH_TODAY

---

## Diagnosis

| Check | Result |
|-------|--------|
| Frozen snapshot | `{snapshot_name}` — NOT FOUND |
| Last known snapshot | `frozen_new_outreach_20260804_et1000.json` (Aug 4) |
| Freeze gap | no snapshot produced since Aug 4 |

## DB Context (FYI only — no action taken)

| Metric | Value |
|--------|-------|
| Raw eligible unsent (ALLOWED_STATES) | {raw_eligible} |
| Today sent | {today_sent} |
| Today plan entries | {today_plan} |
| preflight_status | `no_batch` |
| Follow-up | 0 |
| SMTP | 0 (no SMTP) |

## Actions Taken

- [x] Confirmed no `{snapshot_name}` exists (checked output/ and data/)
- [x] Set `preflight_status = no_batch` in system_config
- [x] No SMTP — clean exit
- [x] Follow-up = 0

## Root Cause

The pre-send pipeline requires a frozen candidate inventory snapshot created by the
21:10 CST freeze step. Without it there is no authoritative candidate list to plan from.
The freeze step has not produced a snapshot since Aug 4.

## Recommendation

Investigate why the 21:10 CST freeze step is not generating
`frozen_new_outreach_YYYYMMDD_et1000.json`:
1. Is the 5-phase schedule (daily_operator_auto.py / BD Execution Host Service) running?
2. Is the freeze/log collection step erroring out?
3. Is the Nashville A0 pool replenished (known gap of ~37)?
"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\nReport saved: {report_path}")
    print("\n=== Clean exit: NO_BATCH_TODAY ===")
else:
    print(f"\n>>> Snapshot found: {snapshot_path}")
    print("Full pre-send planning would proceed here (not reached today).")

conn.close()
