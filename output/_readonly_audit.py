import sqlite3
DB = r"C:/Users/15690/WorkBuddy/2026-06-05-15-31-42/roktandrazo-outreach/data/bd_leads.db"
c = sqlite3.connect(DB)
cur = c.cursor()
print("=== TABLES ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print([r[0] for r in cur.fetchall()])

print("\n=== SYSTEM_CONFIG ===")
try:
    cur.execute("SELECT key,value FROM system_config ORDER BY key")
    rows = cur.fetchall()
    if not rows:
        print("  (empty)")
    for k, v in rows:
        kl = k.lower()
        if any(x in kl for x in ("pause","risk","scale","gate","author","block","mode","send","sched","fsp")):
            print(f"  {k} = {v}")
except Exception as e:
    print("  ERR", e)

print("\n=== SEND_SCALE / PAUSE raw scan ===")
try:
    cur.execute("SELECT key,value FROM system_config WHERE key LIKE '%PAUSE%' OR key LIKE '%SCALE%' OR key LIKE '%RISK%' OR key LIKE '%MANUAL%' OR key LIKE '%GATE%' OR key LIKE '%AUTH%' OR key LIKE '%SEND%' OR key LIKE '%SCHED%'")
    for k, v in cur.fetchall():
        print(f"  {k} = {v}")
except Exception as e:
    print("  ERR", e)

print("\n=== FINAL_SEND_PLAN (batch 2026-08-19) ===")
try:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%send_plan%'")
    print("  plan tables:", [r[0] for r in cur.fetchall()])
    cur.execute("SELECT * FROM final_send_plan WHERE batch_id LIKE '%2026-08-19%' OR business_date='2026-08-19'")
    cols = [d[0] for d in cur.description]
    print("  cols:", cols)
    rows = cur.fetchall()
    print("  rows:", len(rows))
    for r in rows[:20]:
        print("  ", r)
except Exception as e:
    print("  ERR", e)

print("\n=== V2 inventory (campaign_eligible_v2) ===")
try:
    cur.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') AND (name LIKE '%campaign%' OR name LIKE '%v2%')")
    print("  matches:", [r[0] for r in cur.fetchall()])
except Exception as e:
    print("  ERR", e)
c.close()
