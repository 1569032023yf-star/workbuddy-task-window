import sqlite3, os
from collections import Counter
conn = sqlite3.connect(os.path.join("data","bd_leads.db")); conn.row_factory=sqlite3.Row

def show(t):
    print(f"\n=== {t} ===")
    for r in conn.execute(f"PRAGMA table_info({t})"):
        print(f"   {r['name']:26s} {r['type']}")
    n = conn.execute(f"SELECT COUNT(*) c FROM {t}").fetchone()["c"]
    print(f"   ROWS={n}")

show("email_tracking_messages")
show("unmatched_dsn")
show("send_authorizations")
show("send_authorization_entries")
show("lead_email_history")

print("\n=== send_log statuses ===")
for r in conn.execute("SELECT status, COUNT(*) c FROM send_log GROUP BY status ORDER BY c DESC"):
    print(f"   {r['status']:24s} {r['c']}")

print("\n=== send_log sent_at range ===")
print("   min:", conn.execute("SELECT MIN(sent_at) m FROM send_log").fetchone()["m"])
print("   max:", conn.execute("SELECT MAX(sent_at) m FROM send_log").fetchone()["m"])

print("\n=== send_log message_type ===")
for r in conn.execute("SELECT message_type, COUNT(*) c FROM send_log GROUP BY message_type ORDER BY c DESC"):
    print(f"   {str(r['message_type']):26s} {r['c']}")

print("\n=== send_log by day (8/1-8/18) ===")
for r in conn.execute("""SELECT date(sent_at) d, COUNT(*) total,
    SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) st_sent,
    SUM(CASE WHEN smtp_accepted_at IS NOT NULL AND smtp_accepted_at!='' THEN 1 ELSE 0 END) accepted
    FROM send_log WHERE date(sent_at) BETWEEN '2026-08-01' AND '2026-08-18' GROUP BY d ORDER BY d"""):
    print(f"   {r['d']}  total={r['total']:3d}  status_sent={r['st_sent']:3d}  accepted={r['accepted']:3d}")

print("\n=== email_tracking_messages sample (last 15) ===")
cols = [c['name'] for c in conn.execute("PRAGMA table_info(email_tracking_messages)")]
print("   cols:", cols)
for r in conn.execute("SELECT * FROM email_tracking_messages ORDER BY rowid DESC LIMIT 15"):
    print("   ", dict(r))

print("\n=== unmatched_dsn sample ===")
cols = [c['name'] for c in conn.execute("PRAGMA table_info(unmatched_dsn)")]
print("   cols:", cols)
for r in conn.execute("SELECT * FROM unmatched_dsn ORDER BY rowid DESC LIMIT 10"):
    print("   ", dict(r))

print("\n=== reply_log all ===")
for r in conn.execute("SELECT * FROM reply_log"):
    print("   ", dict(r))

print("\n=== suppression_list reasons + range ===")
for r in conn.execute("SELECT reason, COUNT(*) c FROM suppression_list GROUP BY reason"):
    print(f"   {r['reason']:30s} {r['c']}")
print("   min added:", conn.execute("SELECT MIN(added_at) m FROM suppression_list").fetchone()["m"])
print("   max added:", conn.execute("SELECT MAX(added_at) m FROM suppression_list").fetchone()["m"])

print("\n=== leads status do_not_contact / unsubscribed counts ===")
for r in conn.execute("SELECT status, COUNT(*) c FROM leads WHERE status IN ('do_not_contact','unsubscribed','replied','bounced') GROUP BY status"):
    print(f"   {r['status']:20s} {r['c']}")

print("\n=== final_send_plan statuses + created range ===")
for r in conn.execute("SELECT status, COUNT(*) c FROM final_send_plan GROUP BY status ORDER BY c DESC"):
    print(f"   {r['status']:20s} {r['c']}")
print("   created min/max:", conn.execute("SELECT MIN(created_at) m1, MAX(created_at) m2 FROM final_send_plan").fetchone()["m1"], "/", conn.execute("SELECT MIN(created_at) m1, MAX(created_at) m2 FROM final_send_plan").fetchone()["m2"])
conn.close()
