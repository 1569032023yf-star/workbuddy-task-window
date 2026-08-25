"""Discovery batch 2 — 14 clean store-domain candidates. Dedup -> insert -> enrich -> V2 scan.
Operations only, no system change. Mirrors V2 lead 1056 field pattern."""
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
from bd_db import insert_lead
from campaign_eligible_v2 import scan_v2_inventory
from timezone_resolver import resolve_timezone

NOW = datetime.now().isoformat()

# (name, city, state, website, email) -- email domain matches website domain (no third-party block)
NEW = [
 ("Hobby Knights","West Bend","WI","https://shop.hobbyknights.com","sean@hobbyknights.com"),
 ("Noble Knight Games","Fitchburg","WI","https://www.nobleknight.com","Contact@NobleKnight.com"),
 ("Gnome Games","Green Bay","WI","https://www.gnomegames.com","mail@gnomegames.com"),
 ("The Last Square","Mt. Horeb","WI","http://www.lastsquare.com","info@lastsquare.com"),
 ("Mystic Falls Cardboard Company","Atlanta","GA","https://mysticfallscardboardcompany.com","support@mysticfallscardboardcompany.com"),
 ("Terra Toys","Austin","TX","https://www.terratoys.com","info@terratoys.com"),
 ("LionHeart Hobby","Kyle","TX","https://www.lionhearthobby.com","shop@lionhearthobby.com"),
 ("Mimic's Market Cards & Games","Pittsburgh","PA","https://mimicsmarket.com","contact@mimicsmarket.com"),
 ("Game Masters","Pittsburgh","PA","https://gamemasterspgh.com","phil@gamemasterspgh.com"),
 ("Drawbridge Games","Pittsburgh","PA","https://www.drawbridgegames.com","info@drawbridgegames.com"),
 ("Game Theory","Raleigh","NC","https://gametheorystore.com","info@gametheorystore.com"),
 ("Well Played Board Game Cafe","Asheville","NC","https://wellplayedasheville.com","info@wellplayedasheville.com"),
 ("The Dancing Bear Toys","Asheville","NC","https://dancingbeartoys.com","info@dancingbeartoys.com"),
 ("Cape Fear Games","Wilmington","NC","https://capefeargames.com","info@capefeargames.com"),
]

conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory=sqlite3.Row
inserted=[]; skipped=[]
for nm,city,st,web,email in NEW:
    dom = web.lower().replace("https://","").replace("http://","").replace("www.","").split("/")[0]
    dh = hashlib.md5(dom.encode()).hexdigest()[:16]
    edom = email.rsplit("@",1)[-1].lower()
    exist = conn.execute("SELECT id,store_name,status FROM leads WHERE domain_hash=? OR email=?",(dh,email)).fetchone()
    if exist:
        skipped.append((nm, f"EXISTS id={exist['id']} {exist['store_name']} {exist['status']}")); continue
    tz, stt = resolve_timezone(city, st)
    if tz is None:
        skipped.append((nm, f"TZ_UNRESOLVED {city} {st}")); continue
    lead = {
        "store_name": nm, "city": city, "state": st, "official_website": web,
        "email": email, "email_source_type": "official_page_visible",
        "email_verified_on_official_site": 1, "evidence_url": web,
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
    print(f"  [inserted] {nm} (id={nid}, {city} {st}, {tz})")
    inserted.append(nid)

print(f"\nInserted: {len(inserted)}  Skipped: {len(skipped)}")
for s in skipped: print(f"  SKIP {s[0]}: {s[1]}")

print("\n=== V2 re-scan of inserted ids ===")
if inserted:
    res = scan_v2_inventory(inserted, conn)
    for r in res:
        print(f"  id={r['lead_id']:<5} {r['store_name'][:30]:<30} eligible={r['eligible']} tier={r['tier']} mx={r['mx_status']} blockers={r['blockers']}")
conn.close()
