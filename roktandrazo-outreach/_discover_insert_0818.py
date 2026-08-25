"""Discovery insert + enrich — 5 new Verified V2 leads (operations, no system change).
Mirrors existing V2 lead 1056 field pattern. Reads from bd_leads.db (Source of Truth)."""
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

from bd_db import insert_lead
from campaign_eligible_v2 import scan_v2_inventory

NOW = datetime.now().isoformat()

# (store_name, city, state, official_website, email, evidence_url, evidence_snippet, tz)
NEW = [
 ("Village Meeple Board Game Cafe","Springfield","MO","https://www.villagemeeple.com",
   "info@villagemeeple.com","https://www.villagemeeple.com",
   "Village Meeple Board Game Cafe, Springfield MO - info@villagemeeple.com (official site contact)","America/Chicago"),
 ("Meta-Games Unlimited (MGU)","Springfield","MO","https://www.mguinc.com",
   "customerservice@mguinc.com","https://www.mguinc.com",
   "Meta-Games Unlimited (MGU), Springfield MO - customerservice@mguinc.com (official site contact)","America/Chicago"),
 ("Ye Gamer's Guild","Greenwood","IN","https://yegamersguild.com",
   "borr@yegamersguild.com","https://yegamersguild.com",
   "Ye Gamer's Guild, Greenwood IN - borr@yegamersguild.com (official site contact)","America/New_York"),
 ("Hobby Hole","Montgomery","AL","https://hobby-hole.com",
   "store@hobby-hole.com","https://hobby-hole.com/contact-us",
   "Hobby Hole, Montgomery AL - store@hobby-hole.com (official contact page)","America/Chicago"),
 ("The Destination Games Toys & Comics","Louisville","KY","https://destinationcomics.com",
   "thedestinationky@gmail.com","https://destinationcomics.com",
   "The Destination Games Toys & Comics, Louisville KY - thedestinationky@gmail.com (official store page)","America/New_York"),
]

conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db"))
conn.row_factory = sqlite3.Row
inserted_ids = []
for nm,city,st,web,email,ev_url,ev_snip,tz in NEW:
    dom = web.lower().replace("https://","").replace("http://","").replace("www.","").split("/")[0]
    lead = {
        "store_name": nm, "city": city, "state": st, "official_website": web,
        "email": email, "email_source_type": "official_page_visible",
        "email_verified_on_official_site": 1, "evidence_url": ev_url, "evidence_snippet": ev_snip,
        "evidence_method": "official_website_fetch", "status": "new",
        "store_type": "board_game_comic_hobby", "confidence_score": None,
        "collected_at": NOW, "last_checked_at": NOW,
    }
    new_id = insert_lead(lead, conn)
    if new_id is None:
        # already existed (cross_check) — find existing id by domain/email
        r = conn.execute("SELECT id FROM leads WHERE email=?",(email,)).fetchone()
        new_id = r["id"] if r else None
        print(f"  [skip/exists] {nm} -> id={new_id}")
        if new_id: inserted_ids.append(new_id)
        continue
    # enrich fields insert_lead does not set
    org_key = f"org:domain:{dom}"
    conn.execute(
        """UPDATE leads SET organization_key=?, recipient_timezone=?, timezone_status='RESOLVED',
           mx_provider='ok', auto_sendable=1, review_status='pending', email_type='store',
           last_checked_at=? WHERE id=?""",
        (org_key, tz, NOW, new_id))
    conn.commit()
    print(f"  [inserted] {nm} (id={new_id}, {city} {st}, {tz})")
    inserted_ids.append(new_id)

print(f"\nInserted/enriched ids: {inserted_ids}")
# Re-scan V2 on the new ids (live MX via Worker)
print("\n=== V2 re-scan of new leads ===")
res = scan_v2_inventory(inserted_ids, conn)
for r in res:
    print(f"  id={r['lead_id']:<5} {r['store_name'][:30]:<30} eligible={r['eligible']} tier={r['tier']} mx={r['mx_status']} blockers={r['blockers']}")
conn.close()
