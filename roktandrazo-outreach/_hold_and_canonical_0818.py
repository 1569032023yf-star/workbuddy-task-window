import os, sys, sqlite3
from datetime import datetime
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
def _load_env(p):
    try:
        for line in open(p, encoding="utf-8"):
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,v=line.split("=",1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError: pass
_load_env(os.path.join(BASE,".env"))
NOW = datetime.now().isoformat(timespec="seconds")

conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory=sqlite3.Row

# ---- 3) HOLD id=802 ----
print("=== APPLY HOLD: id=802 Grand Adventures (duplicate of sent id=701) ===")
r = conn.execute("SELECT id,status FROM final_send_plan WHERE id=175").fetchone()
print("  FSP 175 before:", dict(r) if r else None)
if r and r["status"] == "planned":
    conn.execute("UPDATE final_send_plan SET status='cancelled', skip_reason='duplicate_store_hold: id=701 same store already sent' WHERE id=175")
    print("  FSP 175 -> cancelled")
else:
    print("  FSP 175 already not planned, no change")
# suppression entry
ex = conn.execute("SELECT id FROM suppression_list WHERE email='granddadventuress@gmail.com'").fetchone()
if ex:
    print("  suppression entry already exists id=", ex["id"])
else:
    conn.execute("INSERT INTO suppression_list (email, reason, added_at) VALUES (?,?,?)",
                 ("granddadventuress@gmail.com", "duplicate_store_hold:701_sent", NOW))
    print("  suppression entry added (granddadventuress@gmail.com)")
# ensure auto_sendable=0 (already 0, idempotent)
conn.execute("UPDATE leads SET auto_sendable=0, last_checked_at=? WHERE id=802", (NOW,))
conn.commit()
print("  leads 802 auto_sendable=0 confirmed")

# ---- verify collected_at for today's new ids ----
print("\n=== collected_at for ids 1056-1078 ===")
for r in conn.execute("SELECT id,collected_at,last_checked_at FROM leads WHERE id BETWEEN 1056 AND 1078 ORDER BY id"):
    print(f"  id={r['id']:<5} collected={r['collected_at']} last_check={r['last_checked_at']}")
conn.close()
