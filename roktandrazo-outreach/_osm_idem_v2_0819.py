"""P1.8D step 5+ — idempotency re-run + V2/MX scan for Ithaca."""
import os, sys, sqlite3
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
os.environ["DISCOVERY_PROVIDER"] = "browser_maps"
os.environ["BROWSER_MAPS_MODE"] = "file"
os.environ["BROWSER_MAPS_JSON_FILE"] = os.path.join(BASE, "data", "osm", "ithaca_bm_file.json")

from discovery.discovery_service import DiscoveryService

conn = sqlite3.connect(os.path.join(BASE, "data", "bd_leads.db")); conn.row_factory = sqlite3.Row
city = dict(conn.execute("SELECT * FROM retail_city_queue WHERE city='Ithaca' AND state='NY'").fetchone())

# ---- RUN 2 (idempotency) ----
svc = DiscoveryService(conn)
s2 = svc.run_places_batch(city, max_pages=1)
print("=== RUN 2 (idempotency) ===")
print("status:", s2.status)
print("results_seen:", s2.results_seen)
print("new_unique_places:", s2.new_unique_places)
print("duplicate_places:", s2.duplicate_places)
print("leads_created:", s2.leads_created)
n_disc2 = conn.execute("SELECT COUNT(*) FROM lead_discovery_results WHERE active_city_id=?", (city["id"],)).fetchone()[0]
print("lead_discovery_results total:", n_disc2)

# ---- V2/MX scan for Ithaca new leads with emails ----
print("\n=== Ithaca leads with emails (V2-relevant) ===")
emails = conn.execute("SELECT id, store_name, email, email_source_type, status FROM leads WHERE city='Ithaca' AND state='NY' AND email IS NOT NULL AND email != ''").fetchall()
for r in emails:
    print(f"  lead={r['id']:<5} {r['store_name'][:28]:<28} {r['email'][:38]:<38} src={str(r['email_source_type'])[:18]:<18} st={r['status']}")
conn.close()
