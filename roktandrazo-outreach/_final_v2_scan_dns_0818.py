"""Authoritative full-DB V2 inventory scan — dnspython MX variant.
Same logic as _final_v2_scan_0818.py but sources MX via direct DNS (dnspython)
instead of the canonical MX Worker (temporarily unreachable). Patching
preflight_gate.query_mx so the real gate code runs unmodified.
Operations verification only, no system change.
"""
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

import dns.resolver
import preflight_gate

def dns_query_mx(domain):
    ts = datetime.now().isoformat()
    for _ in range(2):  # 1 retry on dns_error
        try:
            dns.resolver.resolve(domain, "MX", lifetime=6)
            return "ok", ts
        except dns.resolver.NXDOMAIN:
            return "nxdomain", ts
        except dns.resolver.NoAnswer:
            try:
                dns.resolver.resolve(domain, "A", lifetime=6)
                return "no_mail_route", ts
            except Exception:
                return "nxdomain", ts
        except Exception:
            continue
    return "dns_error", ts

preflight_gate.query_mx = dns_query_mx

from campaign_eligible_v2 import review_campaign_eligible_v2, _domain_of_email

conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory=sqlite3.Row
rows = conn.execute(
    """SELECT id FROM leads WHERE email IS NOT NULL AND email != '' AND email LIKE '%@%.%'
       AND status NOT IN ('sent','bounced','do_not_contact','rejected','failed','delivery_issue','bounce_review','contact_form_pool')
       ORDER BY id""").fetchall()
ids=[r["id"] for r in rows]
leads={r["id"]:dict(r) for r in conn.execute("SELECT * FROM leads WHERE id IN (%s)" % ",".join("?"*len(ids)), ids).fetchall()}

domains=sorted({_domain_of_email(leads[i]["email"]) for i in ids if _domain_of_email(leads[i]["email"])})
mx_lookup={}
for d in domains:
    mx_lookup[d] = dns_query_mx(d)[0]

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
print(f"FULL-DB CAMPAIGN_ELIGIBLE_V2 (dns-mx) = {len(eligible)}")
print(f"  timezone: {dict(tz)}")
print(f"  blocked reasons: {dict(blocked)}")
print("  eligible ids + store + tz + state + mx:")
for i in eligible:
    L=leads[i]
    print(f"    {i:<5} {L['store_name'][:32]:<32} {str(L['recipient_timezone']):<18} {L['state']:<3} mx={mx_lookup.get(_domain_of_email(L['email']),'?')}")
conn.close()
