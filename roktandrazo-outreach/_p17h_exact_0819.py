import sqlite3, os, sys
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
def _load_env(p):
    try:
        for line in open(p, encoding="utf-8"):
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,v=line.split("=",1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError: pass
_load_env(os.path.join(BASE,".env"))
conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory=sqlite3.Row
# the 8 no_mail_route domains found in unsent candidate probe
doms = ["brooklynlab.com","eparks.com","gamesngizmos.com","genxcomics.com","goldrushgames.com",
        "momastore.org","toptentoys.com","villainouslair.com"]
print("=== unsent leads with no_mail_route domains (status + v2-relevant fields) ===")
for d in doms:
    rows = conn.execute("SELECT id,store_name,email,status,email_source_type,email_verified_on_official_site,recipient_timezone,timezone_status FROM leads WHERE email LIKE ?", (f"%@{d}",)).fetchall()
    for r in rows:
        print(f"  {d:22s} lead={r['id']:<5} {r['store_name'][:26]:<26} {r['email'][:40]:<40} st={r['status']:<20} src={str(r['email_source_type'])[:14]:<14} verif={r['email_verified_on_official_site']} tz={r['timezone_status']}")
print()
print("=== those in manual_review_needed pool (the 3 new mx:no_mail_route blocks come from here) ===")
for d in doms:
    rows = conn.execute("SELECT id,store_name,email,status FROM leads WHERE email LIKE ? AND status='manual_review_needed'", (f"%@{d}",)).fetchall()
    for r in rows:
        print(f"  lead={r['id']:<5} {r['store_name'][:26]:<26} {r['email']}")
conn.close()
