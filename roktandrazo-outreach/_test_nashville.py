#!/usr/bin/env python3
"""Safe Nashville city lead discovery verification - NO production writes, NO SMTP."""

import sqlite3, sys, os, hashlib, json, time, re
from datetime import datetime
from urllib.parse import urljoin, urlparse

PROJECT_DIR = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach'
DB_PATH = os.path.join(PROJECT_DIR, 'data', 'bd_leads.db')
TEST_DB_PATH = os.path.join(PROJECT_DIR, 'data', '_test_nashville_verify.db')

print("=" * 70)
print("NASHVILLE INVENTORY VERIFICATION (READ-ONLY + TEST COPY)")
print(f"Time: {datetime.now().isoformat()}")
print("=" * 70)

# Step 0: Copy production DB to test DB
print("\n[STEP 0] Copy production DB to test DB...")
import shutil
shutil.copy2(DB_PATH, TEST_DB_PATH)
print(f"  Source: {DB_PATH}")
print(f"  Test:   {TEST_DB_PATH}")
src_size = os.path.getsize(DB_PATH) / 1024 / 1024
print(f"  Size:   {src_size:.1f} MB")

# Step 1: Inspect production state
print("\n[STEP 1] Production DB state...")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

total = c.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
print(f"  Total leads: {total}")

nash = c.execute("SELECT COUNT(*) FROM leads WHERE city='Nashville' AND state='TN'").fetchone()[0]
print(f"  Nashville, TN leads: {nash}")

for row in c.execute("SELECT status, confidence_score, COUNT(*) FROM leads WHERE city='Nashville' AND state='TN' GROUP BY status, confidence_score ORDER BY status, confidence_score"):
    print(f"    {row[0]}/{row[1]}: {row[2]}")

# Strict A0 count
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
print(f"  Strict A0 (total): {a0}")

# Check retail_city_queue
has_queue = bool(c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='retail_city_queue'").fetchone())
if has_queue:
    rcq = c.execute("SELECT * FROM retail_city_queue ORDER BY priority").fetchall()
    print(f"\n  retail_city_queue ({len(rcq)} rows):")
    for r in rcq:
        d = dict(r)
        print(f"    {d['city']}, {d['state']} | status={d['status']} | query={d.get('active_query_family','None')} | cursor={d.get('page_cursor','None')} | discovered={d.get('discovered_count',0)} | domains={d.get('unique_domain_count',0)} | a0={d.get('strict_a0_count',0)}")
else:
    print("\n  retail_city_queue: TABLE DOES NOT EXIST")

# Nashville B2 candidates
b2 = c.execute("SELECT COUNT(*) FROM leads WHERE city='Nashville' AND state='TN' AND status='manual_review_needed' AND confidence_score='B' AND official_website IS NOT NULL AND official_website != '' AND email IS NULL").fetchone()[0]
cfp = c.execute("SELECT COUNT(*) FROM leads WHERE city='Nashville' AND state='TN' AND status='contact_form_pool' AND official_website IS NOT NULL AND official_website != ''").fetchone()[0]
print(f"\n  Nashville B2 (no email, has site): {b2}")
print(f"  Nashville contact_form_pool: {cfp}")

# All tables
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print(f"\n  Tables: {[t[0] for t in tables]}")

conn.close()

# Step 2: Trace actual inventory call chain
print("\n[STEP 2] Actual Inventory Call Chain Analysis")

# Read bd_orchestrator.py stage_inventory
with open(os.path.join(PROJECT_DIR, 'bd_orchestrator.py'), 'r') as f:
    orch_code = f.read()

# Read retail_city_queue.py
with open(os.path.join(PROJECT_DIR, 'retail_city_queue.py'), 'r') as f:
    rqc_code = f.read()

# Checks
has_web_search = any(kw in orch_code.lower() for kw in ['googlesearch', 'serpapi', 'google search', 'bing search', 'web_search(', 'search_engine', 'google_maps_api', 'places_api'])
has_maps_search = any(kw in orch_code.lower() for kw in ['google_maps', 'googlemaps', 'maps_api', 'places_api', 'maps search'])
uses_query_families = 'search_queries' in orch_code or 'active_query_family' in orch_code
uses_checkpoint = 'checkpoint(' in orch_code and 'retail_city_queue' in orch_code
uses_pagination = 'page_cursor' in orch_code

print(f"  Has web search API calls:     {has_web_search}")
print(f"  Has maps/places API calls:    {has_maps_search}")
print(f"  Uses search_queries():        {uses_query_families}")
print(f"  Uses checkpoint():            {uses_checkpoint}")
print(f"  Uses page_cursor/pagination:  {uses_pagination}")

# What DOES stage_inventory actually do?
print(f"\n  Actual stage_inventory operations:")
if 'fast_lead_discovery' in orch_code:
    print(f"    - Imports fast_lead_discovery (YES)")
if 'extract_emails' in orch_code:
    print(f"    - Calls extract_emails() (YES - email extraction from known URLs)")
if 'http_fast_scan' in orch_code:
    print(f"    - Calls http_fast_scan() (IMPORT - but may not be called)")
if 'activate_next_city' in orch_code:
    print(f"    - Calls activate_next_city() (YES)")
if 'seed_default_queue' in orch_code:
    print(f"    - Calls seed_default_queue() (YES)")

# Check actual call in stage_inventory
inventory_start = orch_code.find('def stage_inventory')
inventory_end = orch_code.find('\ndef stage_', inventory_start + 100)
inventory_code = orch_code[inventory_start:inventory_end] if inventory_end > inventory_start else orch_code[inventory_start:]

print(f"\n  Query family usage in stage_inventory:")
print(f"    search_queries called: {'search_queries' in inventory_code}")
print(f"    checkpoint called:     {'checkpoint' in inventory_code}")
print(f"    complete_if_exhausted: {'complete_if_exhausted' in inventory_code}")
print(f"    active_query_family:   {'active_query_family' in inventory_code}")
print(f"    page_cursor:           {'page_cursor' in inventory_code}")

# Step 3: Verify what the code ACTUALLY processes
print("\n[STEP 3] What stage_inventory ACTUALLY processes:")
lane1_match = re.search(r"Lane 1.*?(?=\n\s*(?:#|except|if not))", inventory_code, re.DOTALL)
lane2_match = re.search(r"Lane 2.*?(?=\n\s*(?:#|except|log\(f))", inventory_code, re.DOTALL)
if lane1_match:
    print(f"  Lane 1 SQL: SELECT from leads WHERE status='manual_review_needed' AND ... city=? AND state=?"  )
if lane2_match:
    print(f"  Lane 2 SQL: SELECT from leads WHERE status='contact_form_pool' AND ... city=? AND state=?")

print("\n[CONCLUSION PRELIMINARY]")
print("  stage_inventory:")
print("    1. Activates city from queue (activate_next_city)")
print("    2. Counts existing Strict A0")
print("    3. Queries EXISTING B2/manual_review_needed candidates for that city")
print("    4. Fetches their KNOWN websites via httpx")
print("    5. Extracts emails from those websites")
print("    6. Upgrades to A0 if email found")
print("    7. Falls back to contact_form_pool if B2 empty")
print("  ")
print("  It does NOT:")
print("    - Use any search engine API")
print("    - Use Google Maps / Places API")
print("    - Execute the 20 query families as actual searches")
print("    - Call search_queries(), checkpoint(), or complete_if_exhausted()")
print("    - Have any pagination logic")
print("    - Discover NEW stores that aren't in the DB")

print("\n[DONE]")
