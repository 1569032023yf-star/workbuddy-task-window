"""P1.8D step 4 — staging postprocess for Ithaca batch only."""
import os, sys, sqlite3
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
os.environ["DISCOVERY_PROVIDER"] = "browser_maps"
os.environ["BROWSER_MAPS_MODE"] = "file"
os.environ["BROWSER_MAPS_JSON_FILE"] = os.path.join(BASE, "data", "osm", "ithaca_bm_file.json")

from discovery.discovery_service import DiscoveryService

conn = sqlite3.connect(os.path.join(BASE, "data", "bd_leads.db")); conn.row_factory = sqlite3.Row
city = conn.execute("SELECT * FROM retail_city_queue WHERE city='Ithaca' AND state='NY'").fetchone()
city = dict(city)

svc = DiscoveryService(conn)
summary = svc.run_staging_postprocess(city, max_results=30)
print("=== STAGING POSTPROCESS ===")
print("status:", summary.status)
print("results_seen:", summary.results_seen)
print("leads_created:", summary.leads_created)
print("validation_statuses:", dict(summary.validation_statuses))
print()

# post-state of Ithaca discovery rows
print("=== Ithaca discovery row statuses ===")
for r in conn.execute("SELECT validation_status, COUNT(*) c FROM lead_discovery_results WHERE active_city_id=? GROUP BY validation_status ORDER BY c DESC", (city["id"],)):
    print(f"  {r[0]:<30} {r[1]}")
print()
print("=== Ithaca leads summary ===")
for r in conn.execute("SELECT status, COUNT(*) c FROM leads WHERE city='Ithaca' AND state='NY' GROUP BY status ORDER BY c DESC"):
    print(f"  {r[0]:<28} {r[1]}")
print()
print("=== Ithaca leads with official website / email ===")
for r in conn.execute("SELECT id,store_name,official_website,email,email_source_type,status FROM leads WHERE city='Ithaca' AND state='NY' ORDER BY id"):
    print(f"  {r['id']:<5} {r['store_name'][:30]:<30} web={str(r['official_website'])[:30]:<30} email={str(r['email'])[:30]:<30} src={str(r['email_source_type'])[:16]:<16} st={r['status']}")
conn.close()
