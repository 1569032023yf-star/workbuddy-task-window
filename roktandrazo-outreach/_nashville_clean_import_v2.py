"""Nashville Clean Import V2 — Direct insert with full field population"""
import sqlite3, json, os, sys
from datetime import datetime, timezone, timedelta

ASIA_SH = timezone(timedelta(hours=8))
PROJECT_DIR = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach'
DB = os.path.join(PROJECT_DIR, 'data', 'bd_leads.db')
JSON_PATH = os.path.join(PROJECT_DIR, 'data', 'webfetch_nashville_master.json')
sys.path.insert(0, PROJECT_DIR)

conn = sqlite3.connect(DB)
now = datetime.now(ASIA_SH).isoformat()
now_utc = datetime.now(timezone.utc).isoformat()

# === Step 1: Clean up empty Nashville leads from failed import ===
print('=== CLEANUP ===')
empty_ids = conn.execute(
    "SELECT id FROM leads WHERE notes LIKE '%webfetch_nashville%' AND (email IS NULL OR email = '')"
).fetchall()
empty_id_list = [r[0] for r in empty_ids]
print(f'  Deleting {len(empty_id_list)} empty Nashville leads: {empty_id_list}')
for lid in empty_id_list:
    conn.execute('DELETE FROM leads WHERE id=?', (lid,))
conn.execute("DELETE FROM lead_discovery_results WHERE source_query='webfetch_master_import'")
conn.commit()
print(f'  Remaining leads: {conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]}')
print(f'  Remaining staging: {conn.execute("SELECT COUNT(*) FROM lead_discovery_results").fetchone()[0]}')

# === Step 2: Load Nashville JSON ===
with open(JSON_PATH, encoding='utf-8') as f:
    master = json.load(f)

registry = master.get('location_registry', [])
candidates = master.get('organization_outreach_candidates', {})
nash_candidates = candidates.get('nashville_candidates_list', [])
evidence = master.get('evidence_recovery_results', {})

# Build lookup: org_key -> {email, evidence}
org_email_map = {}
for c in nash_candidates:
    org_key = c.get('organization_key', '')
    email = c.get('email', '')
    if org_key and email and '@' in email:
        org_email_map[org_key] = email

print(f'\n=== NASHVILLE IMPORT ===')
print(f'  Location registry: {len(registry)}')
print(f'  Verified email orgs: {len(org_email_map)}')
print(f'  Evidence recovery: {evidence.get("new_official_emails_found", 0)} new emails')

# === Step 3: Import each location ===
from bd_db import insert_lead, _domain_hash, _domain_identity_key
from history_crosscheck import cross_check

stats = {'imported': 0, 'a0': 0, 'manual_review': 0, 'contact_form': 0, 
         'blocked': 0, 'skipped': 0, 'errors': 0}

for loc in registry:
    loc_key = loc.get('location_key', '')
    name = loc.get('business_name', '')
    city = loc.get('city', 'Nashville')
    state = loc.get('state', 'TN')
    org_key = loc.get('org', '')
    classification = loc.get('classification', '')
    active = loc.get('active', True)
    query_hits = loc.get('query_hits', [])
    
    if not active:
        stats['skipped'] += 1
        continue
    
    # Look up verified email for this org
    email = org_email_map.get(org_key, '')
    
    # Determine status/score based on classification
    if classification == 'official_email_verified_candidate' and email:
        status = 'new'
        score = 'A'
        auto_sendable = 1
        stats['a0'] += 1
    elif classification == 'retail_candidate' and email:
        status = 'new'
        score = 'A'
        auto_sendable = 1
        stats['a0'] += 1
    elif classification == 'contact_form_candidate':
        status = 'contact_form_pool'
        score = 'C'
        auto_sendable = 0
        stats['contact_form'] += 1
    elif classification == 'custom_production_candidate':
        status = 'manual_review_needed'
        score = 'B'
        auto_sendable = 0
        stats['manual_review'] += 1
    elif classification == 'low_priority_retail_review':
        status = 'manual_review_needed'
        score = 'C'
        auto_sendable = 0
        stats['manual_review'] += 1
    else:
        status = 'manual_review_needed'
        score = 'B'
        auto_sendable = 0
        stats['manual_review'] += 1
    
    # Build candidate
    candidate = {
        'store_name': name,
        'store_type': 'game_store',
        'city': city,
        'state': state,
        'official_website': '',
        'email': email if email else '',
        'email_type': 'website_email' if email else '',
        'confidence_score': score,
        'status': status,
        'product_fit': 'puzzles_games',
        'source_keyword': f'nashville_{query_hits[0] if query_hits else "retail"}',
        'notes': f'webfetch_nashville | org={org_key} | cls={classification} | loc={loc_key}',
        'email_source_type': 'official_page_visible' if email else '',
        'email_verified_on_official_site': 1 if email else 0,
        'evidence_method': 'webfetch_google_maps',
        'evidence_url': '',
        'evidence_snippet': '',
        'phone': '',
        'organization_key': org_key,
        'location_key': loc_key,
        'auto_sendable': auto_sendable,
        'manual_sendable': 0,
    }
    
    # Try insert
    try:
        result = insert_lead(candidate, conn=conn)
        # insert_lead returns int (lead_id) or None
        if result and isinstance(result, int):
            stats['imported'] += 1
            if auto_sendable == 1:
                print(f'  ✅ A0: {name} ({city}, {state}) lead_id={result} org={org_key} email={email}')
            else:
                print(f'  📋 {status}: {name} lead_id={result}')
        elif result is None:
            stats['blocked'] += 1
            print(f'  🚫 BLOCKED: {name} (history_crosscheck rejected)')
        else:
            stats['imported'] += 1
            print(f'  ⚠️  {name}: unexpected result type {type(result)}')
    except Exception as e:
        stats['errors'] += 1
        print(f'  ❌ ERROR {name}: {str(e)[:80]}')

conn.commit()

print(f'\n=== IMPORT RESULTS ===')
print(f'  Imported:      {stats["imported"]}')
print(f'  A0 candidates: {stats["a0"]}')
print(f'  Manual Review: {stats["manual_review"]}')
print(f'  Contact Form:  {stats["contact_form"]}')
print(f'  Blocked:       {stats["blocked"]}')
print(f'  Skipped:       {stats["skipped"]}')
print(f'  Errors:        {stats["errors"]}')
print(f'  Total leads:   {conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]}')

# === Step 4: Verify A0 leads ===
print(f'\n=== A0 VERIFICATION ===')
a0_leads = conn.execute("""
    SELECT id, store_name, organization_key, email, auto_sendable
    FROM leads WHERE notes LIKE '%webfetch_nashville%' AND status='new' AND confidence_score='A'
""").fetchall()
print(f'  Nashville A0 leads: {len(a0_leads)}')
for r in a0_leads:
    print(f'    id={r[0]:3d} auto={r[4]} org={r[2][:30] if r[2] else "NONE"} email={r[3][:35] if r[3] else "NONE"} {r[1][:30]}')

conn.close()
