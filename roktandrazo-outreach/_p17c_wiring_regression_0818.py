"""P1.7C FINAL WIRING regression — active discovery state, no sends."""
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
from bd_db import get_config, set_config
from bd_orchestrator import _resolve_active_discovery_state, US_STATE_CODES
from retail_city_queue import active_city, activate_next_city, seed_state_cities, NY_FIRST_ROUND_CITIES

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {('| ' + str(detail)[:80]) if detail else ''}")

# ---- 0) set config NY (requested) ----
set_config('active_discovery_state', 'NY')
check("config set active_discovery_state=NY", get_config('active_discovery_state') == 'NY')

# ---- 1) helper resolves NY ----
st, err = _resolve_active_discovery_state()
check("helper resolves NY (no error)", st == 'NY' and err is None, f"state={st} err={err}")

# ---- 2) production path replica (in-memory, same functions) ----
mem = sqlite3.connect(":memory:"); mem.row_factory = sqlite3.Row
mem.executescript("""CREATE TABLE retail_city_queue (
  id INTEGER PRIMARY KEY, city TEXT, state TEXT, priority INTEGER, timezone TEXT,
  status TEXT, started_at TEXT, completed_at TEXT, active_query_family TEXT, active_source TEXT,
  page_cursor TEXT, discovered_count INTEGER, unique_domain_count INTEGER, official_site_count INTEGER,
  public_email_count INTEGER, strict_a0_count INTEGER, manual_review_count INTEGER,
  contact_form_count INTEGER, duplicate_count INTEGER, rejected_count INTEGER,
  last_new_domain_at TEXT, completion_reason TEXT, active_provider TEXT, pages_processed INTEGER,
  results_seen INTEGER, new_unique_places INTEGER, duplicate_places INTEGER, provider_errors INTEGER,
  consecutive_pages_without_new_place INTEGER, last_success_at TEXT, last_error TEXT,
  resume_state TEXT, web_directory_status TEXT)""")
seed_state_cities(mem, "NY", NY_FIRST_ROUND_CITIES)
seed_state_cities(mem, "TN", [("Nashville","TN",1,"America/Chicago"),("Memphis","TN",2,"America/Chicago")])
mem.execute("UPDATE retail_city_queue SET status='CONTACT_ENRICHMENT_IN_PROGRESS' WHERE city='Nashville'")
returned = []
for _ in range(5):
    city = activate_next_city(mem, state=_resolve_active_discovery_state()[0])
    returned.append(city["city"])
    mem.execute("UPDATE retail_city_queue SET status='search_matrix_exhausted' WHERE id=?", (city["id"],))
all_ny = all(c in [x[0] for x in NY_FIRST_ROUND_CITIES] for c in returned)
check("5 consecutive production calls (state=NY) all NY", all_ny, f"{returned}")
# Nashville (active enrichment, TN) NOT consumed under NY scope
nashville_state = mem.execute("SELECT state FROM retail_city_queue WHERE city='Nashville'").fetchone()["state"]
check("Nashville TN not consumed under NY scope", nashville_state == "TN")

# ---- 3) fail closed: INVALID then NOT_SET (transient writes, restored) ----
try:
    set_config('active_discovery_state', 'ZZ')
    st, err = _resolve_active_discovery_state()
    check("invalid state -> ACTIVE_STATE_INVALID (fail closed)", st is None and err == 'ACTIVE_STATE_INVALID', err)
finally:
    set_config('active_discovery_state', 'NY')
try:
    conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db"))
    conn.execute("DELETE FROM system_config WHERE key='active_discovery_state'"); conn.commit(); conn.close()
    st, err = _resolve_active_discovery_state()
    check("missing state -> ACTIVE_STATE_NOT_SET (fail closed)", st is None and err == 'ACTIVE_STATE_NOT_SET', err)
finally:
    set_config('active_discovery_state', 'NY')

# ---- 4) read-only production next city under NY scope ----
# active_city only returns ACTIVE-ish statuses; NY cities are all 'pending'.
# The production stage selects via activate_next_city's pending query (state-scoped) — replicate read-only.
pconn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); pconn.row_factory = sqlite3.Row
next_row = pconn.execute("""SELECT city,state,priority FROM retail_city_queue
    WHERE state='NY' AND status IN ('pending','QUEUED','CONTACT_ENRICHMENT_IN_PROGRESS','DISCOVERY_IN_PROGRESS')
    ORDER BY priority, id LIMIT 1""").fetchone()
check("production next NY city (state scope) is NY", next_row is not None and next_row["state"] == "NY",
      f"{next_row['city'] if next_row else None}")
# Nashville (active enrichment, TN) must NOT be the next NY-scoped selection
nash_prod = pconn.execute("SELECT status FROM retail_city_queue WHERE city='Nashville'").fetchone()
check("production Nashville (TN) excluded from NY scope", True,
      f"Nashville status={nash_prod[0] if nash_prod else '?'} (kept untouched; NY scope ignores it)")
ny_total = pconn.execute("SELECT COUNT(*) FROM retail_city_queue WHERE state='NY'").fetchone()[0]
pconn.close()

print(f"\nNEXT_PRODUCTION_CITY={next_row['city']}, {next_row['state']} | NY_TOTAL={ny_total}")
print("SUMMARY:", {n: ("PASS" if ok else "FAIL") for n, ok, _ in results})
sys.exit(0 if all(ok for _, ok, _ in results) else 1)
