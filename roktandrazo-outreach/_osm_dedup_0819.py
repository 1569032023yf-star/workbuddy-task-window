"""P1.8B step 4 — read-only dedup of OSM Ithaca POIs vs bd_leads.db."""
import sqlite3, json, os, re

conn = sqlite3.connect(os.path.join("data", "bd_leads.db")); conn.row_factory = sqlite3.Row
pois = json.load(open("data/osm/ithaca_raw_pois.json", encoding="utf-8"))

def norm_name(s):
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s

db_names = set()
db_domains = set()
for r in conn.execute("SELECT store_name, official_website, email FROM leads"):
    db_names.add(norm_name(r["store_name"]))
    for u in [r["official_website"], r["email"]]:
        if u:
            dom = re.sub(r"^https?://", "", str(u)).split("/")[0].lower()
            db_domains.add(dom.replace("www.", ""))

def poidom(p):
    w = (p.get("website") or "").lower()
    if not w:
        return ""
    m = re.search(r"https?://([^/]+)", w)
    return m.group(1).replace("www.", "") if m else ""

already = []
net_new = []
for p in pois:
    nm = norm_name(p["name"])
    dom = poidom(p)
    hit = nm in db_names or (dom and dom in db_domains)
    (already if hit else net_new).append(p)

print(f"OSM unique businesses       = {len(pois)}")
print(f"ALREADY_IN_DB              = {len(already)}")
print(f"NET_NEW_OSM_CANDIDATES     = {len(net_new)}")
print()
print("=== NET NEW (not in DB) ===")
for p in net_new:
    print(f"  {p['name'][:40]:<40} | {p['shop']:<10} | {p['address'][:36]:<36} | {p['website'][:36]}")
print()
print("=== ALREADY IN DB ===")
for p in already:
    print(f"  {p['name'][:40]:<40} | {p['shop']:<10} | {p['website'][:36]}")
conn.close()
