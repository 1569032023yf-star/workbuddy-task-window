import sqlite3, socket
DB = r"C:/Users/15690/WorkBuddy/2026-06-05-15-31-42/roktandrazo-outreach/data/bd_leads.db"
c = sqlite3.connect(DB); cur = c.cursor()

print("=== send_authorizations latest 5 ===")
cur.execute("SELECT authorization_id, outreach_batch_date, approved_entry_count, preflight_status, status, approved_at, consumed_at FROM send_authorizations ORDER BY rowid DESC LIMIT 5")
for r in cur.fetchall(): print("  ", r)

print("\n=== 08-20 FSP status distribution ===")
cur.execute("SELECT lead_segment, status, COUNT(*) FROM final_send_plan WHERE outreach_batch_date='2026-08-20' GROUP BY lead_segment, status")
for r in cur.fetchall(): print("  ", r)

print("\n=== ops_center heartbeat (127.0.0.1:8765) ===")
try:
    s = socket.create_connection(("127.0.0.1", 8765), timeout=3)
    s.close()
    print("  REACHABLE (port open)")
except Exception as e:
    print("  UNREACHABLE:", e)

print("\n=== preflight_blockers (raw) ===")
cur.execute("SELECT value FROM system_config WHERE key='preflight_blockers'")
print("  ", cur.fetchone()[0])
c.close()
