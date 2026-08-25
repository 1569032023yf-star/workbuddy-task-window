"""P1.8D step 4 retry — staging postprocess with explicit commit."""
import os, sys, sqlite3
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
os.environ["DISCOVERY_PROVIDER"] = "browser_maps"
os.environ["BROWSER_MAPS_MODE"] = "file"
os.environ["BROWSER_MAPS_JSON_FILE"] = os.path.join(BASE, "data", "osm", "ithaca_bm_file.json")

from discovery.discovery_service import DiscoveryService

conn = sqlite3.connect(os.path.join(BASE, "data", "bd_leads.db")); conn.row_factory = sqlite3.Row
city = dict(conn.execute("SELECT * FROM retail_city_queue WHERE city='Ithaca' AND state='NY'").fetchone())

svc = DiscoveryService(conn)
summary = svc.run_staging_postprocess(city, max_results=30)
conn.commit()  # persist lead creation
print("=== STAGING POSTPROCESS (committed) ===")
print("status:", summary.status)
print("results_seen:", summary.results_seen)
print("leads_created:", summary.leads_created)
print("validation_statuses:", dict(summary.validation_statuses))

print("\n=== Ithaca leads with emails (final) ===")
for r in conn.execute("SELECT id,store_name,email,email_source_type,status FROM leads WHERE city='Ithaca' AND state='NY' AND email IS NOT NULL AND email!='' ORDER BY id"):
    print(f"  lead={r['id']:<5} {r['store_name'][:28]:<28} {r['email'][:38]:<38} src={str(r['email_source_type'])[:18]:<18} st={r['status']}")
print("\n=== Ithaca leads count by status ===")
for r in conn.execute("SELECT status, COUNT(*) c FROM leads WHERE city='Ithaca' AND state='NY' GROUP BY status ORDER BY c DESC"):
    print(f"  {r['status']:<26} {r['c']}")
conn.close()
