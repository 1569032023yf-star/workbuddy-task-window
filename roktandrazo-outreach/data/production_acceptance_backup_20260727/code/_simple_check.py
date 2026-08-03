import sqlite3, os, shutil, re
from datetime import datetime

DB = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\data\bd_leads.db'
TEST_DB = DB.replace('.db', '_nashville_test_copy.db')

print("Copying DB...")
shutil.copy2(DB, TEST_DB)

conn = sqlite3.connect(TEST_DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("Total leads:", c.execute("SELECT COUNT(*) FROM leads").fetchone()[0])
print("Nashville TN:", c.execute("SELECT COUNT(*) FROM leads WHERE city='Nashville' AND state='TN'").fetchone()[0])

# Check retail_city_queue
if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='retail_city_queue'").fetchone():
    for r in c.execute("SELECT * FROM retail_city_queue ORDER BY priority"):
        d = dict(r)
        print(f"  {d['city']} {d['state']} | {d['status']} | qf={d.get('active_query_family','-')} | cur={d.get('page_cursor','-')}")

# Strict A0
a0 = c.execute("""
    SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A'
    AND email_verified_on_official_site=1
    AND email_source_type IN ('official_page_visible','official_mailto','wholesale_vendor_page')
    AND evidence_url IS NOT NULL AND evidence_url != ''
    AND evidence_snippet IS NOT NULL AND evidence_snippet != ''
    AND email IS NOT NULL AND email != ''
    AND email NOT IN (SELECT email FROM suppression_list)
    AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent','bounced'))
""").fetchone()[0]
print("Strict A0:", a0)

# Nashville candidates
b2 = c.execute("SELECT COUNT(*) FROM leads WHERE city='Nashville' AND state='TN' AND status='manual_review_needed' AND official_website IS NOT NULL AND official_website != '' AND email IS NULL").fetchone()[0]
cfp = c.execute("SELECT COUNT(*) FROM leads WHERE city='Nashville' AND state='TN' AND status='contact_form_pool'").fetchone()[0]
print(f"Nashville B2: {b2}, CFP: {cfp}")

# Show Nashville B2 candidates
if b2 > 0:
    print("\nNashville B2 candidates:")
    for r in c.execute("SELECT id, store_name, store_type, official_website FROM leads WHERE city='Nashville' AND state='TN' AND status='manual_review_needed' AND official_website IS NOT NULL AND official_website != '' AND email IS NULL LIMIT 10"):
        print(f"  [{r[0]}] {r[1]} ({r[2]}) - {r[3][:60]}")

conn.close()

# Now trace the code
print("\n" + "="*60)
print("CODE TRACE: stage_inventory()")
print("="*60)

with open(r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\bd_orchestrator.py') as f:
    code = f.read()

inv = code[code.find('def stage_inventory'):code.find('\ndef stage_', code.find('def stage_inventory')+10)]

has = lambda s: s in inv
print(f"Imports fast_lead_discovery:  {has('fast_lead_discovery')}")
print(f"Calls seed_default_queue:     {has('seed_default_queue')}")
print(f"Calls activate_next_city:     {has('activate_next_city')}")
print(f"Calls search_queries():       {has('search_queries')}")
print(f"Calls checkpoint():           {has('checkpoint(')}")
print(f"Uses active_query_family:     {has('active_query_family')}")
print(f"Uses page_cursor:             {has('page_cursor')}")
print(f"Calls complete_if_exhausted:  {has('complete_if_exhausted')}")
print(f"Has Google/Bing search:       {has('googlesearch') or has('google') and has('search')}")
print(f"Has Google Maps API:          {has('google_maps') or has('maps_api') or has('places_api')}")
print(f"Queries B2 candidates:        {has(\"status='manual_review_needed'\")}")
print(f"Queries contact_form_pool:    {has('contact_form_pool')}")
print(f"Uses extract_emails:          {has('extract_emails')}")
print(f"Uses httpx:                   {has('httpx')}")

print(f"\n*** CONCLUSION: {'NO web search or map search' if not has('search_queries') else 'HAS search'} ***")
