# SAFE TEST IMPORT — fail-closed, test DB only, uses real bd_db.insert_lead
import json, sqlite3, shutil, hashlib, os, sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
TEST_DB_PATH = PROJECT_DIR / "data" / "bd_leads_test_nashville_webfetch.db"
PROD_DB_PATH = PROJECT_DIR / "data" / "bd_leads.db"
MASTER_JSON = PROJECT_DIR / "data" / "webfetch_nashville_master.json"

# ═══════════════════════════════════════════════
# FAIL-CLOSED PROTECTIONS
# ═══════════════════════════════════════════════
def fail_closed_guard():
    """All guards must pass or script exits immediately."""
    checks = []

    # Guard 1: Explicit test DB path
    test_path = str(TEST_DB_PATH.resolve())
    prod_path = str(PROD_DB_PATH.resolve())
    checks.append(("Test DB path not empty", bool(test_path)))
    checks.append(("Prod DB path not empty", bool(prod_path)))

    # Guard 2: Test != Production
    checks.append(("Test != Production", test_path != prod_path))

    # Guard 3: Test path contains 'test'
    checks.append(("Path contains 'test'", 'test' in str(TEST_DB_PATH).lower()))

    # Guard 4: Must not end with bd_leads.db
    checks.append(("Not named bd_leads.db", not str(TEST_DB_PATH).endswith('bd_leads.db')))

    for name, result in checks:
        if not result:
            print(f"FAIL-CLOSED: {name}")
            print(f"  Test: {test_path}")
            print(f"  Prod: {prod_path}")
            sys.exit(1)
        print(f"  ✅ {name}")

    print(f"  Resolved test DB: {test_path}")
    print(f"  Resolved prod DB:  {prod_path}")
    return test_path, prod_path

test_path, prod_path = fail_closed_guard()

# Guard 5: Capture production hash before ANY operations
with open(prod_path, 'rb') as f:
    PROD_HASH_BEFORE = hashlib.sha256(f.read()).hexdigest()
print(f"  Prod hash before: {PROD_HASH_BEFORE[:16]}...")

# ═══════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════
print(f"\n=== SETUP ===")

# Remove old test DB
if os.path.exists(test_path):
    os.unlink(test_path)
    print(f"  Removed old test DB")

# Copy production → test
shutil.copy2(prod_path, test_path)
print(f"  Copied {prod_path} → {test_path}")

# Import bd_db AFTER paths are confirmed
sys.path.insert(0, str(PROJECT_DIR))
import bd_db
from history_crosscheck import cross_check

# Verify bd_db.DB_PATH is NOT pointing to our test path
print(f"  bd_db.DB_PATH: {bd_db.DB_PATH}")
assert bd_db.DB_PATH != test_path, f"bd_db points to test path!"
print(f"  ✅ bd_db.DB_PATH does not point to test DB")

# Open test connection
test_conn = sqlite3.connect(f"file:{test_path}?mode=rw", uri=True)
test_conn.row_factory = sqlite3.Row
test_conn.execute("PRAGMA journal_mode=WAL")
c = test_conn.cursor()

# Ensure discovery staging table
c.execute("""CREATE TABLE IF NOT EXISTS lead_discovery_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT DEFAULT 'webfetch_google_maps',
    provider_result_id TEXT, place_id TEXT, business_name TEXT NOT NULL,
    formatted_address TEXT, city TEXT, state TEXT, phone TEXT,
    website TEXT, source_query TEXT, query_family TEXT,
    raw_payload_json TEXT, active_city_id INTEGER DEFAULT 1,
    discovered_at TEXT, last_seen_at TEXT,
    validation_status TEXT DEFAULT 'validation_pending',
    history_crosscheck_result TEXT, linked_lead_id INTEGER,
    country TEXT DEFAULT 'US'
)""")
test_conn.commit()

# ═══════════════════════════════════════════════
# LOAD MASTER + IMPORT STAGING
# ═══════════════════════════════════════════════
print(f"\n=== IMPORT STAGING ===")
with open(MASTER_JSON, 'r', encoding='utf-8') as f:
    master = json.load(f)
registry = master.get('location_registry', [])
now = datetime.now().isoformat()

staging = 0
for loc in registry:
    qf = loc.get('query_hits', [])
    c.execute("""INSERT OR IGNORE INTO lead_discovery_results
        (provider, provider_result_id, place_id, business_name, formatted_address,
         city, state, phone, website, source_query, query_family, raw_payload_json,
         discovered_at, last_seen_at, validation_status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,'validation_pending')""",
        ('webfetch_google_maps', loc.get('location_key',''), loc.get('location_key',''),
         loc['business_name'], loc.get('addr','') or loc.get('formatted_address',''),
         loc['city'], loc['state'], loc.get('ph','') or loc.get('phone',''),
         loc.get('web','') or loc.get('official_website',''),
         f"webfetch:{','.join(qf)}", qf[0] if qf else 'unknown',
         json.dumps(loc), now, now))
    staging += 1
test_conn.commit()
print(f"  Staging rows: {staging}")

# ═══════════════════════════════════════════════
# HISTORY CROSSCHECK + INSERT VIA bd_db
# ═══════════════════════════════════════════════
print(f"\n=== CROSSCHECK + INSERT (via bd_db.insert_lead with test_conn) ===")

results = {'new_candidate':0,'exact_duplicate':0,'identity_duplicate_new_email':0,
           'previously_sent':0,'suppressed':0,'bounced':0,'related_location':0}
inserted = 0; blocked = 0

# Evidence recovery data
evidence = master.get('evidence_recovery_results',{}).get('details',[])
org_emails = {
    'game_point_cafe': ('info@gamepointcafe.com', True, 'https://gamepointcafe.com/contact', '[info@gamepointcafe.com](mailto:info@gamepointcafe.com) — site footer on contact page', 'https://gamepointcafe.com'),
    'the_great_escape': ('contactus@thegreatescapeonline.com', True, 'http://thegreatescapeonline.com/CustomPage/8534', 'Charlotte Avenue Superstore: contactus@thegreatescapeonline.com', 'https://www.thegreatescapeonline.com'),
    'tabla_rasa_toys': ('shop@tablarasatoys.com', True, 'https://tablarasatoys.com/visit-us', 'shop@tablarasatoys.com — mailto link in footer', 'https://tablarasatoys.com'),
    'phillips_toy_mart': ('support@phillipstoymart.com', False, '', '', 'https://phillipstoymart.com'),
    'miniature_cottage': ('miniaturecottage@gmail.com', True, 'https://miniaturecottage.com/about-us', 'Contact info: miniaturecottage@gmail.com', 'https://miniaturecottage.com'),
    'rhino_booksellers': ('rhinobks@gmail.com', False, '', '', 'https://rhinobooksellers.com'),
}

for loc in registry:
    name = loc['business_name']; cls = loc.get('classification','')
    city_l = loc['city']; state_l = loc['state']; org_key = loc.get('org','')
    active = loc.get('active', False)
    website = loc.get('web','') or loc.get('official_website','')
    phone = loc.get('ph','') or loc.get('phone','')

    if not active or cls == 'outside_active_city':
        results['related_location'] = results.get('related_location',0) + 1; continue
    if cls == 'rejected_low_product_fit': continue

    # Get email + evidence
    email = ''; email_verified = False; ev_url = ''; ev_snippet = ''; org_website = ''
    if org_key in org_emails:
        tup = org_emails[org_key]
        email = tup[0]; email_verified = tup[1]
        if len(tup) > 2: ev_url = tup[2]
        if len(tup) > 3: ev_snippet = tup[3]
        if len(tup) > 4: org_website = tup[4]

    # Use org website if location doesn't have one
    if not website and org_website:
        website = org_website

    # Crosscheck
    hc = cross_check(test_conn, {
        'store_name': name, 'city': city_l, 'state': state_l,
        'official_website': website, 'email': email
    })
    hc_result = hc['result']
    results[hc_result] = results.get(hc_result, 0) + 1

    if hc_result != 'new_candidate':
        blocked += 1; continue

    # Build lead for bd_db
    status = 'new'; score = 'A'
    if cls in ('official_email_verified_candidate',) and email_verified:
        status = 'new'; score = 'A'
    elif cls in ('retail_candidate',) and email_verified:
        status = 'new'; score = 'A'
    elif cls in ('manual_review_candidate','retail_candidate'):
        status = 'manual_review_needed'; score = 'B'
    elif cls == 'contact_form_candidate':
        status = 'contact_form_pool'; score = 'C'
    elif cls == 'custom_production_candidate':
        status = 'manual_review_needed'; score = 'B'
    elif cls == 'low_priority_retail_review':
        status = 'manual_review_needed'; score = 'C'
    elif cls == 'possible_historical_duplicate':
        blocked += 1; continue
    else:
        status = 'manual_review_needed'; score = 'B'

    lead = {
        'store_name': name, 'store_type': 'game_store',
        'city': city_l, 'state': state_l,
        'official_website': website,
        'email': email,
        'email_type': 'general' if email else 'unknown',
        'confidence_score': score,
        'status': status,
        'product_fit': 'puzzles_games',
        'source_keyword': 'webfetch_nashville',
        'notes': f'webfetch_nashville; org={org_key}; cls={cls}',
        'email_source_type': 'official_page_visible' if email_verified else 'unknown',
        'email_verified_on_official_site': 1 if email_verified else 0,
        'evidence_method': 'webfetch_google_maps',
        'evidence_url': ev_url,
        'evidence_snippet': ev_snippet,
        'phone': phone,
    }

    lid = bd_db.insert_lead(lead, conn=test_conn)
    if lid:
        inserted += 1
    else:
        blocked += 1

test_conn.commit()

print(f"  Inserted: {inserted}")
print(f"  Blocked: {blocked}")
print(f"  Crosscheck: {dict((k,v) for k,v in results.items() if v>0)}")

# ═══════════════════════════════════════════════
# FINAL STATS
# ═══════════════════════════════════════════════
print(f"\n=== FINAL STATS ===")
for sql, label in [
    ("SELECT COUNT(*) FROM leads","Total leads"),
    ("SELECT COUNT(*) FROM leads WHERE notes LIKE '%webfetch_nashville%'","Webfetch leads"),
    ("SELECT COUNT(*) FROM leads WHERE notes LIKE '%webfetch%' AND status='new' AND confidence_score='A'","Strict A0"),
    ("SELECT COUNT(*) FROM leads WHERE notes LIKE '%webfetch%' AND status='manual_review_needed'","Manual Review"),
    ("SELECT COUNT(*) FROM leads WHERE notes LIKE '%webfetch%' AND status='contact_form_pool'","Contact Form"),
    ("SELECT COUNT(*) FROM leads WHERE notes LIKE '%webfetch%' AND status='manual_review_needed' AND confidence_score='C'","Low Priority"),
    ("SELECT COUNT(*) FROM lead_discovery_results","Staging"),
]:
    cnt = c.execute(sql).fetchone()[0]
    print(f"  {label}: {cnt}")

# Organization checks
for org, name_like in [('game_point_cafe','Game Point%'),('nashville_souvenirs','Nashville Souvenirs%'),('the_great_escape','The Great Escape%')]:
    rows = c.execute("SELECT id, store_name, status, confidence_score, email FROM leads WHERE store_name LIKE ? AND notes LIKE '%webfetch%'", (name_like,)).fetchall()
    print(f"  {org}: {len(rows)} records")
    for r in rows:
        print(f"    [{r[0]}] {r[1]}: {r[2]}/{r[3]} {r[4][:30] if r[4] else 'no email'}")

test_conn.close()

# Guard 6: Verify production unchanged
with open(prod_path, 'rb') as f:
    PROD_HASH_AFTER = hashlib.sha256(f.read()).hexdigest()
prod_unchanged = PROD_HASH_BEFORE == PROD_HASH_AFTER

print(f"\n=== INTEGRITY ===")
print(f"  Prod hash before: {PROD_HASH_BEFORE[:16]}...")
print(f"  Prod hash after:  {PROD_HASH_AFTER[:16]}...")
print(f"  Production unchanged: {prod_unchanged}")
print(f"  Test DB: {test_path}")

if not prod_unchanged:
    print("  ❌ PRODUCTION DB WAS MODIFIED!")
    sys.exit(1)

print(f"\n✅ DONE. Production DB intact. {inserted} leads in test DB via real bd_db.insert_lead.")
