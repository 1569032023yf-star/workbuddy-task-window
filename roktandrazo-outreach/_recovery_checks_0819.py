"""Immediate post-send recovery checks — read-only reconciliation for the 10-lead batch.
Checks: send_log, FSP status, IMAP DSN scan, suppression, reply, duplicate-send.
"""
import os, sys, sqlite3, json
from datetime import datetime, timedelta
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)

def _load_env(p):
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass
_load_env(os.path.join(BASE, ".env"))

conn = sqlite3.connect(os.path.join(BASE, "data", "bd_leads.db")); conn.row_factory = sqlite3.Row
LEAD_IDS = [727, 814, 815, 839, 883, 923, 1018, 1053, 1054, 1069]
EMAILS = ["hardknoxgames@gmail.com","dragonstarhobbies@gmail.com","orders@fantasyfactory.com",
          "ac1@atlantis-comics.com","bookeryfan@aol.com","staff@chicagolandgames.com",
          "sales@blueoxgames.com","vddw@baldmangames.com","info@falloutcomics.com",
          "info@bluebridgegames.com"]

print("=== 1) send_log rows for this batch (newest 15) ===")
rows = conn.execute(
    "SELECT id, lead_id, email, status, sent_at, smtp_accepted_at, message_id, error_message, batch_id "
    "FROM send_log WHERE lead_id IN (%s) ORDER BY id DESC LIMIT 15" % ",".join("?" * len(LEAD_IDS)),
    LEAD_IDS).fetchall()
for r in rows:
    print("  ", dict(r))

print("\n=== 2) FSP status for planned ids 174,176-184 ===")
for r in conn.execute("SELECT id, lead_id, status, skip_reason, sent_at FROM final_send_plan WHERE id IN (174,176,177,178,179,180,181,182,183,184) ORDER BY id"):
    print("  ", dict(r))

print("\n=== 3) suppression check for batch emails ===")
for r in conn.execute("SELECT email, reason, added_at FROM suppression_list WHERE email IN (%s)" % ",".join("?" * len(EMAILS)), EMAILS):
    print("  SUPPRESSED:", dict(r))
print("  (none above = none suppressed)")

print("\n=== 4) bounce_log for batch emails ===")
for r in conn.execute("SELECT id, lead_id, email, bounce_received_at, diagnostic_code, bounce_type FROM bounce_log WHERE email IN (%s)" % ",".join("?" * len(EMAILS)), EMAILS):
    print("  ", dict(r))
print("  (none above = no bounces)")

print("\n=== 5) unmatched_dsn for batch emails ===")
for r in conn.execute("SELECT id, original_recipient, detected_at, diagnostic_code, original_sent_at FROM unmatched_dsn WHERE original_recipient IN (%s)" % ",".join("?" * len(EMAILS)), EMAILS):
    print("  ", dict(r))
print("  (none above = no unmatched DSN)")

print("\n=== 6) reply_log for batch emails ===")
for r in conn.execute("SELECT id, email, reply_received_at, reply_type, summary FROM reply_log WHERE email IN (%s)" % ",".join("?" * len(EMAILS)), EMAILS):
    print("  ", dict(r))
print("  (none above = no replies)")

print("\n=== 7) leads status after send ===")
for r in conn.execute("SELECT id, store_name, email, status, last_checked_at FROM leads WHERE id IN (%s) ORDER BY id" % ",".join("?" * len(LEAD_IDS)), LEAD_IDS):
    print("  ", dict(r))

print("\n=== 8) authorization records (latest 3) ===")
for r in conn.execute("SELECT id, authorization_id, plan_id, approved_entry_count, preflight_status, approved_at, expires_at, status, consumed_at FROM send_authorizations ORDER BY id DESC LIMIT 3"):
    print("  ", dict(r))

print("\n=== 9) duplicate send check (count send_log per email, all-time) ===")
for r in conn.execute("SELECT email, COUNT(*) c, GROUP_CONCAT(status) sts FROM send_log WHERE email IN (%s) GROUP BY email" % ",".join("?" * len(EMAILS)), EMAILS):
    print("  ", dict(r))

print("\n=== 10) today totals (2026-08-19) ===")
print("  today send_log rows:", conn.execute("SELECT COUNT(*) FROM send_log WHERE sent_at LIKE '2026-08-19%'").fetchone()[0])
print("  today bounce_log rows:", conn.execute("SELECT COUNT(*) FROM bounce_log WHERE bounce_received_at LIKE '2026-08-19%'").fetchone()[0])
conn.close()
print("\nRECOVERY_CHECKS_DONE")
