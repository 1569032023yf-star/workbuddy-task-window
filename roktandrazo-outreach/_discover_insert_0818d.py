"""Discovery batch 4 (0818d) — primary-state candidates TN/AR/KY.
Dedup -> insert -> enrich -> real-gate V2 verification (dnspython MX, since the
canonical MX Worker is temporarily unreachable). Operations only, no system change.
Mirrors V2 lead 1056/1058 field pattern.
"""
import os, sys, sqlite3, hashlib
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
from bd_db import insert_lead
from timezone_resolver import resolve_timezone

NOW = datetime.now().isoformat()

def mx_status(domain, retries=1):
    """Return (status, detail) matching preflight_gate contract: ok/nxdomain/no_mail_route/dns_error."""
    for _ in range(retries + 1):
        try:
            dns.resolver.resolve(domain, "MX", lifetime=6)
            return "ok", ""
        except dns.resolver.NXDOMAIN:
            return "nxdomain", ""
        except dns.resolver.NoAnswer:
            try:
                dns.resolver.resolve(domain, "A", lifetime=6)
                return "no_mail_route", ""
            except Exception:
                return "nxdomain", ""
        except Exception as e:
            last = str(e)[:80]
    return "dns_error", last

# (name, city, state, website, email)
NEW = [
    ("Game Goblins","Little Rock","AR","http://gamegoblins.com","info@gamegoblins.com"),
    ("Sci-Fi City","Knoxville","TN","https://www.sci-fi-city.com","orders@sci-fi-city.com"),
    ("Comic Book World","Florence","KY","https://www.comicbookworld.com","cbwinfo@comicbookworld.com"),
    ("Grand Adventures Comics","Murfreesboro","TN","https://www.grandadventurescomics.com","info@grandadventurescomics.com"),
]

def host_of(web):
    h = web.lower().replace("https://","").replace("http://","").replace("www.","").split("/")[0]
    return h

conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory=sqlite3.Row
inserted=[]; skipped=[]
for nm,city,st,web,email in NEW:
    dom = host_of(web)
    web_clean = web.rstrip("/")
    dh = hashlib.md5(dom.encode()).hexdigest()[:16]
    edom = email.rsplit("@",1)[-1].lower()
    exist = conn.execute("SELECT id,store_name,status FROM leads WHERE domain_hash=? OR email=? OR store_name=?",
                         (dh,email,nm)).fetchone()
    if exist:
        skipped.append((nm, f"SQL_EXISTS id={exist['id']} {exist['store_name']} {exist['status']}")); continue
    tz, stt = resolve_timezone(city, st)
    if tz is None:
        skipped.append((nm, f"TZ_UNRESOLVED {city} {st}")); continue
    if dom != edom:
        skipped.append((nm, f"THIRD_PARTY_MISMATCH site={dom} email={edom}")); continue
    mx, _ = mx_status(dom)
    if mx != "ok":
        skipped.append((nm, f"MX={mx}")); continue
    lead = {
        "store_name": nm, "city": city, "state": st, "official_website": web_clean,
        "email": email, "email_source_type": "official_page_visible",
        "email_verified_on_official_site": 1, "evidence_url": web_clean,
        "evidence_snippet": f"{nm}, {city}, {st} - {email} (official site contact)",
        "evidence_method": "official_website_fetch", "status": "new",
        "store_type": "board_game_comic_hobby", "collected_at": NOW, "last_checked_at": NOW,
    }
    nid = insert_lead(lead, conn)
    if nid is None:
        r = conn.execute("SELECT id,store_name,status FROM leads WHERE email=? OR store_name=?",(email,nm)).fetchone()
        if r: skipped.append((nm, f"cross_check_exists id={r['id']} {r['store_name']} {r['status']}"))
        continue
    conn.execute("""UPDATE leads SET organization_key=?, recipient_timezone=?, timezone_status='RESOLVED',
        mx_provider='ok', auto_sendable=1, review_status='pending', email_type='store', last_checked_at=? WHERE id=?""",
        (f"org:domain:{dom}", tz, NOW, nid))
    conn.commit()
    print(f"  [inserted] {nm:26s} (id={nid}, {city} {st}, {tz.split('/')[-1]}, mx=ok)")
    inserted.append(nid)

print(f"\nInserted: {len(inserted)}  Skipped: {len(skipped)}")
for s in skipped: print(f"  SKIP {s[0]}: {s[1]}")

# Real-gate verification of the newly inserted leads (independent of MX Worker)
from campaign_eligible_v2 import review_campaign_eligible_v2, _domain_of_email
mx_lookup = {}
for nid in inserted:
    L = dict(conn.execute("SELECT * FROM leads WHERE id=?", (nid,)).fetchone())
    d = _domain_of_email(L["email"])
    if d not in mx_lookup:
        mx_lookup[d] = mx_status(d)[0]
    r = review_campaign_eligible_v2(L, {"conn": conn, "mx_lookup": mx_lookup})
    print(f"  [gate] id={nid} {L['store_name'][:26]:26s} V2={'PASS' if r['eligible'] else 'FAIL'} blockers={r['blockers']}")
conn.close()
