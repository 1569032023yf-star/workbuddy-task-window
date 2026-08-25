"""P1.8D step 4b — V2/MX scan for Ithaca leads with emails."""
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
ids = [1093,1094,1095,1096,1097,1098,1099,1100,1101]
print("=== V2/MX scan for Ithaca 9 leads (post-postprocess) ===")
res = cev2.scan_v2_inventory(ids, conn=conn)
for lead_id, r in zip(ids, res):
    L = conn.execute("SELECT store_name,email FROM leads WHERE id=?", (lead_id,)).fetchone()
    st = "V2 PASS" if r.get("eligible") else "BLOCK:" + str(r.get("reasons"))
    print(f"  lead={lead_id:<5} {str(L['store_name'])[:28]:<28} {str(L['email'])[:38]:<38} {st}")
conn.close()
