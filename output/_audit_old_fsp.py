import sqlite3
DB = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\data\bd_leads.db"
c = sqlite3.connect(DB); cur = c.cursor()
cur.execute("PRAGMA table_info(final_send_plan)")
cols=[r[1] for r in cur.fetchall()]
print("SCHEMA:", cols)
targets = [185,187,188,189,190,191,192,193,194]
print("\n=== OLD FSP 185,187-194 (8/19 batch) ===")
cur.execute("SELECT * FROM final_send_plan WHERE id IN (%s) ORDER BY id" % ",".join(str(t) for t in targets))
dcols=[d[0] for d in cur.description]
for r in cur.fetchall():
    d=dict(zip(dcols,r))
    print("  id=%s lead=%s batch=%s status=%s sent_at=%s skip=%s" % (
        d.get('id'), d.get('lead_id'), d.get('outreach_batch_date'), d.get('status'), d.get('sent_at'), d.get('skip_reason')))
print("\n=== send_log for those leads ===")
cur.execute("SELECT lead_id, status, error_message, sent_at FROM send_log WHERE lead_id IN (1068,1070,1071,1072,1073,1074,1075,1076,1077)")
rows=cur.fetchall()
print("  send_log rows:", len(rows))
for r in rows: print("  ", r)
print("\n=== Authorizations (8/19 & 8/20) ===")
cur.execute("SELECT authorization_id, outreach_batch_date, approved_entry_count, preflight_status, status, approved_at, consumed_at FROM send_authorizations WHERE outreach_batch_date IN ('2026-08-19','2026-08-20') ORDER BY rowid DESC LIMIT 5")
for r in cur.fetchall(): print("  ", r)
c.close()
