"""TONIGHT FSP PREPARE — create frozen Final Send Plan only. NO SEND, NO AUTH."""
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

import bd_template, final_send_plan
from env_loader import is_configured
assert is_configured(), "SMTP not configured"
SPEC = importlib.util.spec_from_file_location("cev2", os.path.join(BASE,"campaign_eligible_v2.py"))
cev2 = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(cev2)

conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory = sqlite3.Row
BATCH_DATE = "2026-08-19"
MAX = 10

# ---- 1) authoritative V2 inventory ----
ids = [r["id"] for r in conn.execute("SELECT id FROM leads").fetchall()]
res = cev2.scan_v2_inventory(ids, conn=conn)
eligible = []
for lead_id, r in zip(ids, res):
    if r.get("eligible"):
        L = dict(conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone())
        eligible.append(L)
print(f"V2_UNSENT_AVAILABLE = {len(eligible)}")

# ---- 2) rank: store-domain official first-party, verified=1, official_page_visible ----
def score(L):
    email = str(L.get("email") or "").lower()
    web = str(L.get("official_website") or "").lower()
    edom = email.rsplit("@",1)[-1] if "@" in email else ""
    dom = web.replace("https://","").replace("http://","").replace("www.","").split("/")[0]
    s = 0
    if edom == dom: s += 10            # store-domain mailbox (strongest)
    if str(L.get("email_source_type"))=="official_page_visible": s += 8
    if L.get("email_verified_on_official_site"): s += 6
    return s

eligible.sort(key=score, reverse=True)
chosen = eligible[:MAX]
print(f"chosen = {len(chosen)}")

# ---- 3) create frozen FSP via canonical create_plan ----
created = []
for L in chosen:
    lead = dict(L)
    bd_template.apply_email_to_lead(lead)
    plan_id = final_send_plan.create_plan(conn, [lead], BATCH_DATE, "new_outreach",
                                          eligible_check=lambda l: True)
    conn.commit()
    fsp = conn.execute(
        "SELECT id FROM final_send_plan WHERE lead_id=? AND outreach_batch_date=? AND status='planned' ORDER BY id DESC LIMIT 1",
        (lead["id"], BATCH_DATE)).fetchone()
    created.append({"fsp_id": fsp["id"], "lead_id": lead["id"], "store": lead["store_name"],
                    "email": lead["email"], "tz": lead.get("recipient_timezone") or ""})

print("\n=== CREATED FSP ===")
for c in created:
    bucket = "PT" if "Los_Angeles" in c["tz"] else "MT" if "Denver" in c["tz"] else "CT" if "Chicago" in c["tz"] else "ET" if "New_York" in c["tz"] else "?"
    print(f"  FSP{c['fsp_id']:<4} lead={c['lead_id']:<5} {c['store'][:26]:<26} {c['email'][:36]:<36} {bucket}")
conn.close()
print("\nPREP_DONE count=", len(created))
