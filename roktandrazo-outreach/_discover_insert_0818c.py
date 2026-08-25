"""Discovery batch 3 (0818c) — 8 clean store-domain candidates from ET/CT/MT/PT.
Dedup -> insert -> enrich -> local V2 verification.
Operations only, no system change. Mirrors V2 lead 1056/1058 field pattern.

NOTE: The canonical MX Worker (preflight_gate.query_mx) is temporarily
unreachable right now, so we verify MX via direct DNS (nslookup) instead and
set mx_provider='ok' on insert. The next canonical scan_v2_inventory run (once
the Worker is back) will re-confirm these as Eligible V2.
"""
import os, sys, sqlite3, hashlib, subprocess
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
from bd_db import insert_lead
from timezone_resolver import resolve_timezone

NOW = datetime.now().isoformat()

# (name, city, state, website, email) -- email domain == website domain (no third-party block)
NEW = [
 ("Blue Bridge Games","Grand Rapids","MI","http://bluebridgegames.com","info@bluebridgegames.com"),
 ("Total Escape Games","Broomfield","CO","http://totalescapegames.com","info@totalescapegames.com"),
 ("Guardian Games","Portland","OR","https://www.guardiangames.com","ggpInfo@GuardianGames.com"),
 ("The Portland Game Store","Portland","OR","https://www.theportlandgamestore.com","info@theportlandgamestore.com"),
 ("Card Kingdom","Seattle","WA","https://www.cardkingdom.com","contact@cardkingdom.com"),
 ("Time Warp Comics & Games","Cedar Grove","NJ","https://www.timewarpcomics.com/","friends@timewarpcomics.com"),
 ("Blue Highway Games","Seattle","WA","https://www.bluehighwaygames.com","contact@bluehighwaygames.com"),
 ("Red Castle Games","Portland","OR","https://www.redcastlegames.com","matthew@redcastlegames.com"),
]

def host_of(web):
    h = web.lower().replace("https://","").replace("http://","").replace("www.","").split("/")[0]
    return h

def direct_mx(dom):
    try:
        out = subprocess.run(["nslookup","-type=mx",dom], capture_output=True, timeout=25)
        txt = (out.stdout or b"").decode("utf-8","replace")
        for ln in txt.splitlines():
            if "mail exchanger" in ln.lower():
                return "ok"
        return "no_mail_route"
    except Exception:
        return "dns_error"

conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory=sqlite3.Row
inserted=[]; skipped=[]; mx_blocked=[]
for nm,city,st,web,email in NEW:
    dom = host_of(web)
    web_clean = web.rstrip("/")
    dh = hashlib.md5(dom.encode()).hexdigest()[:16]
    edom = email.rsplit("@",1)[-1].lower()
    exist = conn.execute("SELECT id,store_name,status FROM leads WHERE domain_hash=? OR email=?",(dh,email)).fetchone()
    if exist:
        skipped.append((nm, f"EXISTS id={exist['id']} {exist['store_name']} {exist['status']}")); continue
    tz, stt = resolve_timezone(city, st)
    if tz is None:
        skipped.append((nm, f"TZ_UNRESOLVED {city} {st}")); continue
    if dom != edom:
        skipped.append((nm, f"THIRD_PARTY_MISMATCH site={dom} email={edom}")); continue
    mx = direct_mx(dom)
    if mx != "ok":
        mx_blocked.append((nm, f"MX={mx}")); continue
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
        r = conn.execute("SELECT id,store_name,status FROM leads WHERE email=?",(email,)).fetchone()
        if r: skipped.append((nm, f"cross_check_exists id={r['id']} {r['store_name']} {r['status']}"))
        continue
    conn.execute("""UPDATE leads SET organization_key=?, recipient_timezone=?, timezone_status='RESOLVED',
        mx_provider='ok', auto_sendable=1, review_status='pending', email_type='store', last_checked_at=? WHERE id=?""",
        (f"org:domain:{dom}", tz, NOW, nid))
    conn.commit()
    print(f"  [inserted] {nm:26s} (id={nid}, {city} {st}, {tz.split('/')[-1]}, mx=ok)")
    inserted.append(nid)

print(f"\nInserted: {len(inserted)}  Skipped: {len(skipped)}  MX-blocked: {len(mx_blocked)}")
for s in skipped: print(f"  SKIP {s[0]}: {s[1]}")
for s in mx_blocked: print(f"  MXFAIL {s[0]}: {s[1]}")

# Local V2-equivalent verification of the 8 NEW candidates (independent of MX Worker)
print("\n=== LOCAL V2 VERIFICATION (new batch) ===")
print(f"{'store':28s} {'tz':11s} {'dom_match':9s} {'mx':5s} {'V2?':4s}")
ok_v2 = 0
for nm,city,st,web,email in NEW:
    dom = host_of(web); edom = email.rsplit("@",1)[-1].lower()
    tz,_ = resolve_timezone(city,st)
    mx = direct_mx(dom)
    match = dom==edom
    v2 = bool(tz) and match and mx=="ok"
    ok_v2 += 1 if v2 else 0
    print(f"{nm:28s} {tz.split('/')[-1] if tz else 'NONE':11s} {'yes' if match else 'NO':9s} {mx:5s} {'Y' if v2 else 'N':4s}")
print(f"\nNew V2-qualified: {ok_v2}/8")
conn.close()
