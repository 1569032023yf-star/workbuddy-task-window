import sqlite3
DB = r"C:/Users/15690/WorkBuddy/2026-06-05-15-31-42/roktandrazo-outreach/data/bd_leads.db"
c = sqlite3.connect(DB); cur = c.cursor()

print("=== final_send_plan schema ===")
cur.execute("PRAGMA table_info(final_send_plan)")
for r in cur.fetchall(): print("  ", r)

print("\n=== final_send_plan rows (business_date 08-19 or 08-20) ===")
cur.execute("SELECT * FROM final_send_plan")
cols=[d[0] for d in cur.description]
print("COLS:", cols)
rows=cur.fetchall()
print("TOTAL rows:", len(rows))
for r in rows:
    d=dict(zip(cols,r))
    bd=d.get('business_date'); st=d.get('status'); fsp=d.get('fsp_id')
    if bd in ('2026-08-19','2026-08-20') or st in ('frozen','locked','pending','ready'):
        print(f"  fsp={d.get('fsp_id')} bd={bd} status={st} lead={d.get('lead_id')} auth={d.get('authorized')} sent={d.get('sent_at')}")

print("\n=== send_log recent ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='send_log'")
if cur.fetchone():
    cur.execute("PRAGMA table_info(send_log)")
    sc=[d[1] for d in cur.fetchall()]
    cur.execute(f"SELECT {', '.join(sc[:6])} FROM send_log ORDER BY rowid DESC LIMIT 8")
    print("COLS:", sc[:6])
    for r in cur.fetchall(): print("  ", r)

print("\n=== send_authorizations ===")
cur.execute("PRAGMA table_info(send_authorizations)")
ac=[d[1] for d in cur.fetchall()]
print("COLS:", ac)
cur.execute(f"SELECT * FROM send_authorizations ORDER BY rowid DESC LIMIT 8")
for r in cur.fetchall(): print("  ", r)

print("\n=== preflight gate fn scan ===")
c.close()
