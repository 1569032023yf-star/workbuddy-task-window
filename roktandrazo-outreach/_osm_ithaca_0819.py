"""P1.8B — Read-only OSM feasibility test: extract Ithaca-area shop POIs from NY PBF.
No API calls, no system changes. Standard pyosmium local parse."""
import os, sys, json, math
import osmium

PBF = os.path.join("data", "osm", "new-york-latest.osm.pbf")
# Ithaca, NY center (approx): lat 42.4430, lon -76.5019 ; radius ~20km
CENTER = (42.4430, -76.5019)
RADIUS_KM = 20.0

SHOP_TYPES = {
    "games", "toys", "books", "gift", "collector", "craft",
    "model", "video_games", "hobby", "tabletop", "sports",
    "general", "antiques", "toy", "board_games", "cards", "comics",
}

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.asin(math.sqrt(a))

class ShopHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.pois = []
    def node(self, n):
        self._check(n, n.location.lat, n.location.lon)
    def way(self, w):
        try:
            if w.nodes and w.nodes[0].location:
                lat = w.nodes[0].location.lat; lon = w.nodes[0].location.lon
                self._check(w, lat, lon)
        except Exception:
            pass
    def _check(self, obj, lat, lon):
        if lat is None or lon is None:
            return
        if haversine_km(CENTER[0], CENTER[1], lat, lon) > RADIUS_KM:
            return
        tags = dict(obj.tags)
        shop = (tags.get("shop") or "").lower()
        if shop and shop in SHOP_TYPES:
            name = tags.get("name") or ""
            if not name:
                return
            self.pois.append({
                "osm_type": type(obj).__name__.lower(),
                "osm_id": obj.id,
                "name": name,
                "shop": shop,
                "address": " ".join(x for x in [tags.get("addr:housenumber"), tags.get("addr:street"), tags.get("addr:city"), tags.get("addr:postcode")] if x),
                "website": tags.get("website") or tags.get("contact:website") or "",
                "phone": tags.get("phone") or tags.get("contact:phone") or "",
                "lat": round(lat, 6), "lon": round(lon, 6),
            })

h = ShopHandler()
print("parsing", PBF)
h.apply_file(PBF, locations=True)
print("raw POIs (Ithaca 20km, named):", len(h.pois))

# dedup by name
seen = {}
for p in h.pois:
    key = p["name"].lower().strip()
    if key not in seen:
        seen[key] = p
unique = list(seen.values())
print("unique businesses:", len(unique))
print("with name:", sum(1 for p in unique if p["name"]))
print("with address:", sum(1 for p in unique if p["address"]))
print("with website:", sum(1 for p in unique if p["website"]))
print("with phone:", sum(1 for p in unique if p["phone"]))
print()
print("=== up to 30 stores ===")
for p in unique[:30]:
    print(f"  {p['name'][:38]:<38} | {p['shop']:<12} | {p['address'][:40]:<40} | {p['website'][:38]}")

with open("data/osm/ithaca_raw_pois.json", "w", encoding="utf-8") as f:
    json.dump(unique, f, indent=2, ensure_ascii=False)
print("\nsaved", len(unique), "to data/osm/ithaca_raw_pois.json")
