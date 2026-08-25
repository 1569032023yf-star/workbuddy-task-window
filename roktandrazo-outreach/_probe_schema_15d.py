import sqlite3, os
conn = sqlite3.connect(os.path.join("data","bd_leads.db"))
tabs = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
print("=== TABLES ===")
for t in tabs: print(" ", t)
for t in ["send_log","final_send_plan","bounce_log","reply_log","oo_log","auto_reply_log","suppression_list","unsubscribe_log","dsn_log","tracking_log","send_auth","authorization"]:
    if t in tabs:
        print(f"\n=== SCHEMA {t} ===")
        for r in conn.execute(f"PRAGMA table_info({t})"):
            print(f"   {r[1]:24s} {r[2]}")
        try:
            n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"   ROWS={n}")
        except Exception as e:
            print("   count err", e)
conn.close()
