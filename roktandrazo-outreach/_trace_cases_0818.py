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
from campaign_eligible import review_campaign_eligible
from campaign_eligible_v2 import review_campaign_eligible_v2, _domain_of_email
from preflight_gate import query_mx

conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory=sqlite3.Row

def gate(lead):
    v1 = review_campaign_eligible(lead, {"conn": conn})
    try: mx,_ = query_mx(_domain_of_email(lead["email"])); mxok = (mx=="ok")
    except Exception: mxok=False; mx="dns_error"
    v2 = review_campaign_eligible_v2(lead, {"conn": conn, "mx_lookup": {_domain_of_email(lead["email"]): mx}})
    return v1, v2, mx

def probe(name, sql, args=()):
    rows = conn.execute(sql, args).fetchall()
    print(f"\n### {name}: {len(rows)} row(s)")
    for r in rows[:3]:
        L = dict(r)
        v1, v2, mx = gate(L)
        print(f"  id={L['id']:<5} {L['store_name'][:24]:<24} st={L['status']:<20} review={str(L.get('review_status'))[:16]:<16} conf={str(L.get('confidence_score')):>4} auto_send={L.get('auto_sendable')} email={str(L.get('email'))[:36]:<36}")
        print(f"     -> V1={v1['pool']} | MX={mx} | V2={'ELIGIBLE' if v2['eligible'] else 'BLOCK:'+str(v2['blockers'][:2])}")

probe("CASE A: approved_auto + has email", 
      "SELECT * FROM leads WHERE review_status='approved_auto' AND email IS NOT NULL AND email!=''")
probe("CASE B: approved_auto + email but MX not ok",
      "SELECT * FROM leads WHERE review_status='approved_auto' AND email IS NOT NULL AND email!='' AND (mx_provider IS NULL OR mx_provider NOT IN ('ok'))")
probe("CASE C: contact_form_pool",
      "SELECT * FROM leads WHERE status='contact_form_pool' AND email IS NOT NULL AND email!=''")
probe("CASE C2: contact_form_pool (any, sample)", 
      "SELECT * FROM leads WHERE status='contact_form_pool' LIMIT 2")

print("\n### review_log action counts (all-time)")
try:
    for r in conn.execute("SELECT decision, COUNT(*) c FROM review_log GROUP BY decision ORDER BY c DESC"):
        print(f"  {r['decision']:<20} {r['c']}")
except Exception as e:
    print("  review_log read err:", str(e)[:60])
conn.close()
