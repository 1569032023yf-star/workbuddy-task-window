"""P1.7D controlled NY discovery batch — canonical production path only. No sends."""
import os, sys, sqlite3
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
def _load_env(p):
    try:
        for line in open(p, encoding="utf-8"):
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,v=line.split("=",1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError: pass
_load_env(os.path.join(BASE,".env"))
from bd_orchestrator import _resolve_active_discovery_state
from retail_city_queue import activate_next_city, seed_default_queue
from bd_db import get_db

state, err = _resolve_active_discovery_state()
print(f"ACTIVE_STATE={state} err={err}")
if err:
    print("ABORT: active state fail-closed"); sys.exit(0)

conn = get_db(); conn.row_factory = sqlite3.Row
with conn:
    seed_default_queue(conn)
    city = activate_next_city(conn, state=state)
print(f"CURRENT_CITY={city['city']}, {city['state']} (status={city['status']}, id={city['id']})")

from discovery.discovery_service import DiscoveryService
svc = DiscoveryService(conn)
try:
    summary = svc.run_places_batch(city, max_pages=2)
    print("RUN_PLACES_BATCH:", summary)
except Exception as e:
    print("RUN_PLACES_BATCH EXC:", type(e).__name__, str(e)[:200])
try:
    post = svc.run_staging_postprocess(city, max_results=10)
    print("POSTPROCESS:", post)
except Exception as e:
    print("POSTPROCESS EXC:", type(e).__name__, str(e)[:200])

# Post-batch DB deltas for NY (Ithaca + any NY leads)
print("\n=== NY lead inventory (post-batch) ===")
ny = conn.execute("SELECT COUNT(*) c FROM leads WHERE state='NY'").fetchone()["c"]
print("NY leads total:", ny)
for r in conn.execute("SELECT id,store_name,city,email,status,email_source_type,confidence_score FROM leads WHERE state='NY' ORDER BY id LIMIT 20"):
    print("  ", dict(r))
# queue state after
for r in conn.execute("SELECT city,state,status,provider_errors FROM retail_city_queue WHERE state='NY' ORDER BY priority LIMIT 6"):
    print("  queue:", dict(r))
# next NY pending city
nxt = conn.execute("""SELECT city FROM retail_city_queue WHERE state='NY'
    AND status IN ('pending','QUEUED','CONTACT_ENRICHMENT_IN_PROGRESS','DISCOVERY_IN_PROGRESS')
    ORDER BY priority, id LIMIT 1""").fetchone()
exhausted = nxt is None
print(f"\nNEXT_PRODUCTION_CITY={nxt['city'] if nxt else None} NY_STATE_EXHAUSTED={exhausted}")
conn.close()
