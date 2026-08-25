"""P1.8D step 2-3 — controlled Ithaca ingest via existing DiscoveryService (browser_maps FILE mode).
Only Ithaca. No sends. Uses existing assets only."""
import os, sys, sqlite3, json
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
os.environ["DISCOVERY_PROVIDER"] = "browser_maps"
os.environ["BROWSER_MAPS_MODE"] = "file"
os.environ["BROWSER_MAPS_JSON_FILE"] = os.path.join(BASE, "data", "osm", "ithaca_bm_file.json")

from discovery.discovery_service import DiscoveryService
from retail_city_queue import activate_next_city

conn = sqlite3.connect(os.path.join(BASE, "data", "bd_leads.db")); conn.row_factory = sqlite3.Row

# ONLY Ithaca: activate within NY scope
city = activate_next_city(conn, state="NY")
print(f"ACTIVE CITY = {city['city']}, {city['state']} (id={city['id']})")
assert city["city"] == "Ithaca", f"expected Ithaca, got {city['city']}"

svc = DiscoveryService(conn)
summary = svc.run_places_batch(city, max_pages=1)
print("\n=== RUN 1 SUMMARY ===")
print("status:", summary.status)
print("results_seen:", summary.results_seen)
print("new_unique_places:", summary.new_unique_places)
print("duplicate_places:", summary.duplicate_places)
print("leads_created:", summary.leads_created)
print("provider_errors:", summary.provider_errors)
print("validation_statuses:", dict(summary.validation_statuses))

# DB checks
n_disc = conn.execute("SELECT COUNT(*) FROM lead_discovery_results WHERE active_city_id=?", (city["id"],)).fetchone()[0]
print("\nlead_discovery_results for Ithaca:", n_disc)
n_leads = conn.execute("SELECT COUNT(*) FROM leads WHERE city='Ithaca' AND state='NY'").fetchone()[0]
print("leads created for Ithaca:", n_leads)
conn.close()
