"""P1.8F C — re-run V2 on 3 Ithaca official-email leads after enrichment."""
import os, sys, sqlite3, importlib.util
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
def _load_env(p):
    try:
        for line in open(p, encoding="utf-8"):
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,v=line.split("=",1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError: pass
_load_env(os.path.join(BASE,".env"))
SPEC = importlib.util.spec_from_file_location("cev2", os.path.join(BASE,"campaign_eligible_v2.py"))
cev2 = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(cev2)

conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory=sqlite3.Row
ids = [1095, 1096, 1101]
res = cev2.scan_v2_inventory(ids, conn=conn)
print("=== V2 AFTER ENRICHMENT (canonical worker) ===")
for lead_id, r in zip(ids, res):
    L = conn.execute("SELECT store_name,email,organization_key,recipient_timezone,timezone_status FROM leads WHERE id=?", (lead_id,)).fetchone()
    print(f"  lead_id={lead_id}")
    print(f"    store={L['store_name']}")
    print(f"    email={L['email']}")
    print(f"    timezone={L['recipient_timezone']} ({L['timezone_status']})")
    print(f"    organization_key={L['organization_key']}")
    print(f"    mx={r.get('mx_status')}")
    print(f"    v2_eligible={r.get('eligible')}")
    print(f"    blockers={r.get('blockers')}")
conn.close()
