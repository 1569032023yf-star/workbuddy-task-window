"""Authoritative full-DB V2 inventory scan with MX retry (neutralizes flaky dns_error)."""
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
from campaign_eligible_v2 import review_campaign_eligible_v2, _domain_of_email
from preflight_gate import query_mx

conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory=sqlite3.Row
rows = conn.execute(
    """SELECT id FROM leads WHERE email IS NOT NULL AND email != '' AND email LIKE '%@%.%'
       AND status NOT IN ('sent','bounced','do_not_contact','rejected','failed','delivery_issue','bounce_review','contact_form_pool')
       ORDER BY id""").fetchall()
ids=[r["id"] for r in rows]
leads={r["id"]:dict(r) for r in conn.execute("SELECT * FROM leads WHERE id IN (%s)" % ",".join("?"*len(ids)), ids).fetchall()}

# pre-build MX with 1 retry on dns_error
domains=sorted({_domain_of_email(leads[i]["email"]) for i in ids if _domain_of_email(leads[i]["email"])})
mx_lookup={}
for d in domains:
    try: st,_=query_mx(d)
    except Exception: st="dns_error"
    if st=="dns_error":
        try: st,_=query_mx(d)  # retry once
        except Exception: st="dns_error"
    mx_lookup[d]=st

eligible=[]; blocked={}
for i in ids:
    r=review_campaign_eligible_v2(leads[i], {"conn":conn,"mx_lookup":mx_lookup})
    if r["eligible"]: eligible.append(i)
    else:
        reason=r["blockers"][0] if r["blockers"] else "?"
        blocked[reason]=blocked.get(reason,0)+1

from collections import Counter
tz=Counter()
for i in eligible:
    tz[leads[i]["recipient_timezone"] or "UNSET"]+=1
print(f"FULL-DB CAMPAIGN_ELIGIBLE_V2 = {len(eligible)}")
print(f"  timezone: {dict(tz)}")
print(f"  blocked reasons: {dict(blocked)}")
print("  eligible ids + store + tz + tier + mx:")
for i in eligible:
    L=leads[i]
    print(f"    {i:<5} {L['store_name'][:32]:<32} {str(L['recipient_timezone']):<18} {L['state']:<3} mx={mx_lookup.get(_domain_of_email(L['email']),'?')}")
conn.close()
