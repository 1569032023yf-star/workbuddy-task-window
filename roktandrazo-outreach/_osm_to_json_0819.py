"""P1.8D step 1 — convert Ithaca OSM POIs to browser_maps FILE-mode compatible JSON.
Stable OSM identity: provider_result_id=osm:<type>:<id>, place_id=osm-<type>-<id>.
No email, no A0/V2 prediction."""
import json, os, re

pois = json.load(open("data/osm/ithaca_raw_pois.json", encoding="utf-8"))
results = []
for p in pois:
    # split loose address -> formatted + postal
    addr = p.get("address") or ""
    m = re.search(r"\b(\d{5})\b", addr)
    postal = m.group(1) if m else ""
    # city guess: if address contains a known Tompkins locality keep raw; else Ithaca
    city = "Ithaca"
    state = "NY"
    results.append({
        "provider": "browser_maps",
        "provider_result_id": f"osm:{p['osm_type']}:{p['osm_id']}",
        "place_id": f"osm-{p['osm_type']}-{p['osm_id']}",
        "business_name": p["name"],
        "formatted_address": addr,
        "city": city,
        "state": state,
        "country": "US",
        "postal_code": postal,
        "phone": p.get("phone") or "",
        "website": p.get("website") or "",
        "business_status": "OPERATIONAL",
        "primary_type": "store",
        "types": ["store", "point_of_interest", p.get("shop")],
        "source_query": f"toy store Ithaca NY",
        "source_url": "",
        "raw_payload": {"osm_shop": p.get("shop"), "osm_lat": p.get("lat"), "osm_lon": p.get("lon")},
        "next_page_cursor": "",
        "location_lat": p.get("lat"),
        "location_lng": p.get("lon"),
    })

out = {
    "provider": "browser_maps",
    "query": "toy store Ithaca NY",
    "city": "Ithaca",
    "state": "NY",
    "page_cursor": "",
    "next_page_cursor": "",
    "status": "ok",
    "error": "",
    "results": results,
    "request_count": 1,
    "cost_units": 0,
    "collected_at": "2026-08-19T00:00:00+00:00",
}
os.makedirs("data/osm", exist_ok=True)
outpath = "data/osm/ithaca_bm_file.json"
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print("WROTE", outpath, "rows =", len(results))
# verify stable ids unique
ids = [r["provider_result_id"] for r in results]
print("unique provider_result_id:", len(set(ids)) == len(ids))
