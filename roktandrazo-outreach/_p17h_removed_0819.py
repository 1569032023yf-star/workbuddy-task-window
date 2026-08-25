import sqlite3, os, sys
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
def _load_env(p):
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError: pass
_load_env(os.path.join(BASE, ".env"))
from preflight_gate import query_mx
conn = sqlite3.connect(os.path.join(BASE, "data", "bd_leads.db")); conn.row_factory = sqlite3.Row

# All unsent candidates (status not terminal, not suppressed)
cands = conn.execute("""
    SELECT DISTINCT substr(email, instr(email,'@')+1) dom FROM leads
    WHERE email IS NOT NULL AND email!='' AND email LIKE '%@%.%'
    AND status NOT IN ('sent','bounced','do_not_contact','rejected','failed',
                       'delivery_issue','bounce_review','contact_form_pool')
    AND email NOT IN (SELECT email FROM suppression_list)
    ORDER BY dom
""").fetchall()
no_mx = []
for c in cands:
    d = c["dom"]
    st, _ = query_mx(d)
    if st != "ok":
        no_mx.append((d, st))
print("=== NON-OK domains among unsent candidates (fixed worker) ===")
for d, st in no_mx:
    print(f"  {d:36s} {st}")
print(f"\n  total non-ok = {len(no_mx)}")
print("  falloutcomics.com present?", any(d == "falloutcomics.com" for d, _ in no_mx))

# which leads use these domains (unsent)
print("\n=== LEAD ids using removed domains ===")
for d, st in no_mx:
    for r in conn.execute("SELECT id, store_name, email, status FROM leads WHERE email LIKE ?", (f"%@{d}",)):
        print(f"  {d:36s} lead={r['id']:<5} {r['store_name'][:24]:<24} {r['email']:<38} {r['status']}")
conn.close()
