"""P1.7C regression — state scope fix, no sends. Writes: NY city seed only."""
import os, sys, sqlite3, io, contextlib
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
def _load_env(p):
    try:
        for line in open(p, encoding="utf-8"):
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,v=line.split("=",1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError: pass
_load_env(os.path.join(BASE,".env"))
from campaign_eligible import select_candidates_for_plan, review_campaign_eligible
from campaign_eligible_v2 import review_campaign_eligible_v2, _domain_of_email
from preflight_gate import query_mx
from retail_city_queue import active_city, activate_next_city, seed_state_cities, NY_FIRST_ROUND_CITIES

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {('| ' + str(detail)[:90]) if detail else ''}")

# ---------- 1) Seed NY (production, requested) ----------
conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db")); conn.row_factory=sqlite3.Row
existing_ny = conn.execute("SELECT COUNT(*) c FROM retail_city_queue WHERE state='NY'").fetchone()["c"]
added = 0 if existing_ny else seed_state_cities(conn, "NY", NY_FIRST_ROUND_CITIES)
ny_count = conn.execute("SELECT COUNT(*) c FROM retail_city_queue WHERE state='NY'").fetchone()["c"]
check("NY seed inserted", added == len(NY_FIRST_ROUND_CITIES), f"existing={existing_ny} added={added} total_NY={ny_count}")

# ---------- 2) State-scoped queue (in-memory DB, no production writes) ----------
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
seed_state_cities(mem, "NY", NY_FIRST_ROUND_CITIES[:5])
seed_state_cities(mem, "TN", [("Nashville","TN",1,"America/Chicago"),("Memphis","TN",2,"America/Chicago")])
returned = []
for _ in range(5):
    city = activate_next_city(mem, state="NY")
    returned.append(city["city"] if city else None)
    if city:
        mem.execute("UPDATE retail_city_queue SET status='search_matrix_exhausted' WHERE id=?", (city["id"],))
all_ny = all(c is not None for c in returned) and all(
    mem.execute("SELECT state FROM retail_city_queue WHERE city=?", (c,)).fetchone()["state"] == "NY" for c in returned)
check("activate_next_city(state='NY') never returns non-NY", all_ny, f"returned={returned}")
# legacy no-state behavior still works
first_any = activate_next_city(mem)
check("activate_next_city(state=None) legacy ok", first_any is not None and first_any["state"] == "TN",
      f"first any-state={first_any['city'] if first_any else None}")

# ---------- 3) FSP gate: all states allowed ----------
cands = select_candidates_for_plan(conn, limit=100)
cand_states = {c["state"] for c in cands}
cand_ids = [c["id"] for c in cands]
check("select_candidates_for_plan default = all states", len(cand_states) > 3, f"states={sorted(cand_states)}")
check("non-3-state V2 leads are FSP candidates", all(i in cand_ids for i in [1054, 1066, 1074]),
      f"FL/PA/WA ids in candidates={[i for i in [1054,1066,1074] if i in cand_ids]}")
check("3-state still normal", 1053 in cand_ids and 727 in cand_ids, "AR/KY ids present")

# NY V2 -> FSP (simulate NY lead from V2-eligible base, no DB write)
base = dict(conn.execute("SELECT * FROM leads WHERE id=1056").fetchone())
ny_lead = {**base, "state": "NY", "city": "Ithaca"}
v1 = review_campaign_eligible(ny_lead, {"conn": conn})
check("NY V2 lead -> V1 CAMPAIGN_ELIGIBLE (state ignored)", v1["pool"] == "CAMPAIGN_ELIGIBLE", v1["pool"])
d = _domain_of_email(ny_lead["email"]); mx,_ = query_mx(d)
v2 = review_campaign_eligible_v2(ny_lead, {"conn": conn, "mx_lookup": {d: mx}})
check("NY V2 lead -> V2 PASS (state ignored)", v2["eligible"], v2["blockers"])

# ---------- 4) V2 negatives unchanged ----------
def v2_block(lead):
    dd = _domain_of_email(lead["email"])
    try: m,_ = query_mx(dd)
    except Exception: m = "dns_error"
    return review_campaign_eligible_v2(lead, {"conn": conn, "mx_lookup": {dd: m}})

guessed = {**base, "email": "info@fake-guess-example.com", "email_source_type": "guessed_email"}
r = v2_block(guessed)
check("guessed_email -> V2 BLOCK", not r["eligible"], r["blockers"])

sup = {**base, "email": "info@atomicempire.com", "email_source_type": "official_page_visible",
       "email_verified_on_official_site": 1}
r = v2_block(sup)
check("suppressed email -> BLOCK", not r["eligible"], r["blockers"])

bounced = dict(conn.execute("SELECT * FROM leads WHERE id=771").fetchone())
r = v2_block(bounced)
check("bounced lead -> BLOCK", not r["eligible"], r["blockers"])

cf = dict(conn.execute("SELECT * FROM leads WHERE id=6").fetchone())
if cf.get("email"):
    r = v2_block(cf)
else:
    r = {"eligible": False, "blockers": ["no_email_contact_form"]}
check("contact_form_only -> BLOCK", not r["eligible"], r["blockers"])

print(f"\nNY_CITY_COUNT={ny_count}  TOTAL_QUEUE={conn.execute('SELECT COUNT(*) FROM retail_city_queue').fetchone()[0]}")
print("SUMMARY:", {n: ("PASS" if ok else "FAIL") for n, ok, _ in results})
conn.close()
mem.close()
sys.exit(0 if all(ok for _, ok, _ in results) else 1)
