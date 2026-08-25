import os, sys, sqlite3
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
def _load_env(p):
    try:
        for line in open(p, encoding="utf-8"):
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,v=line.split("=",1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError: pass
_load_env(os.path.join(BASE,".env"))
from campaign_eligible import review_campaign_eligible
from campaign_eligible_v2 import review_campaign_eligible_v2, _domain_of_email
from preflight_gate import query_mx
conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory=sqlite3.Row
ids = [1053, 727, 1054, 1056, 1058, 1062, 1066, 1074]  # 2 x 3-state (AR,KY) + 6 x non-3-state
mx_lookup = {}
print(f"{'id':>4} {'store':<24} {'st':<3} {'V2':<8} {'V1_pool':<20} {'3-state':<8} {'via_select_candidates(FSP)':<12}")
for i in ids:
    L = dict(conn.execute("SELECT * FROM leads WHERE id=?", (i,)).fetchone())
    d = _domain_of_email(L["email"])
    if d not in mx_lookup:
        try: st,_ = query_mx(d); mx_lookup[d] = st
        except Exception: mx_lookup[d] = "dns_error"
    v2 = review_campaign_eligible_v2(L, {"conn": conn, "mx_lookup": mx_lookup})
    v1 = review_campaign_eligible(L, {"conn": conn})
    in3 = L["state"] in ("TN","AR","KY")
    fsp_via_selector = in3 and v1["pool"] == "CAMPAIGN_ELIGIBLE"
    print(f"{i:>4} {str(L['store_name'])[:24]:<24} {str(L['state']):<3} {'PASS' if v2['eligible'] else 'BLOCK':<8} {v1['pool']:<20} {str(in3):<8} {'YES' if fsp_via_selector else 'NO'}")
conn.close()
