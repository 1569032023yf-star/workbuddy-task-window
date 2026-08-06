#!/usr/bin/env python3
"""
Inventory Recovery — 2026-08-06 (Thursday, weekday target=30)
Skips hanging Google Places discovery. Runs Website Recovery only.

Rules: No SMTP. No Final Send Plan. No Send Authorization.
Reads active_retail_city from system_config ONLY. Does NOT hardcode cities.
"""

import os
import sys
import time
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))
os.chdir(str(PROJECT_DIR))

from bd_db import get_db, get_sendable_leads, is_suppressed
from outreach_control import INVENTORY_TARGET

print(f"=== BD Inventory Recovery ===")
print(f"Target: {INVENTORY_TARGET} sendable orgs (weekday)")
print(f"Time: {datetime.now().isoformat()}")

# ── Step 0: Read active city from system_config ──
conn = get_db()
conn.row_factory = sqlite3.Row
c = conn.cursor()

active_row = c.execute("SELECT key, value FROM system_config WHERE key='active_retail_city'").fetchone()
active_state_row = c.execute("SELECT key, value FROM system_config WHERE key='active_retail_state'").fetchone()
active_city_state = c.execute("SELECT key, value FROM system_config WHERE key='active_city_state'").fetchone()
active_page = c.execute("SELECT key, value FROM system_config WHERE key='active_page'").fetchone()
active_query = c.execute("SELECT key, value FROM system_config WHERE key='active_query'").fetchone()

active_city = active_row['value'] if active_row else 'Nashville'
active_state = active_state_row['value'] if active_state_row else 'Tennessee'
active_state_abbr = active_city_state['value'] if active_city_state else 'TN'
print(f"\n[CURSOR] active_retail_city={active_city}, active_retail_state={active_state}, active_city_state={active_state_abbr}")
print(f"[CURSOR] active_page={active_page['value'] if active_page else 'N/A'}, active_query={active_query['value'] if active_query else 'N/A'}")

# ── Step 1: Count current state ──
a0_raw = c.execute("SELECT COUNT(*) FROM leads WHERE auto_sendable=1 AND status='new' AND email IS NOT NULL AND email!=''").fetchone()[0]
a0_gate = len(get_sendable_leads(limit=INVENTORY_TARGET + 1, conn=conn))
print(f"\n[STATUS] A0 raw (auto_sendable=1): {a0_raw}")
print(f"[STATUS] A0 gate (sendable_leads): {a0_gate}")
print(f"[STATUS] Gap: {max(0, INVENTORY_TARGET - a0_gate)}")

# ── Step 2: Skip Lane A discovery (Google Places is unconfigured → hangs) ──
print(f"\n[SKIP] Lane A discovery: Google Places API not configured")

# ── Step 3: Staging postprocess ──
print(f"\n=== Staging Postprocess ===")
try:
    from discovery.discovery_service import DiscoveryService

    # Read city row from retail_city_queue
    city_row = c.execute(
        "SELECT * FROM retail_city_queue WHERE city=? AND state=?",
        (active_city, active_state)
    ).fetchone()
    if city_row:
        city_dict = dict(city_row)
        discovery_svc = DiscoveryService(conn)
        post_summary = discovery_svc.run_staging_postprocess(
            city_dict, max_results=20
        )
        print(f"  Staging: {post_summary.status} | processed={post_summary.results_seen} | leads_created={post_summary.leads_created}")
    else:
        print(f"  City row not found: {active_city}, {active_state}")
except Exception as e:
    print(f"  [WARN] Staging postprocess unavailable: {e}")

# ── Step 4: Website Recovery ──
print(f"\n=== Website Recovery (TN/AR/KY, no email, has website) ===")

candidates = c.execute("""
    SELECT * FROM leads
    WHERE state IN ('TN','AR','KY')
    AND status NOT IN ('sent','bounced','do_not_contact')
    AND (email IS NULL OR email='')
    AND official_website IS NOT NULL AND official_website != ''
    ORDER BY CASE WHEN state='TN' THEN 0 WHEN state='AR' THEN 1 ELSE 2 END,
             city, id
    LIMIT 35
""").fetchall()

print(f"  Candidates: {len(candidates)}")

from inventory_monitor_executor import http_scan_website
from manual_email_workflow import submit_manual_email

ssl_stats = {
    'direct_ok': 0, 'curl_ok': 0,
    'emails_found': 0, 'no_email': 0,
    'network_errors': 0, 'platform_skip': 0,
    'previously_sent': 0, 'new_emails': 0,
}
new_a0_promoted = []

for i, cand in enumerate(candidates):
    cd = dict(cand)
    website = cd.get('official_website', '')
    if not website:
        continue

    scan_ss = {}
    email, ev_url, ev_snippet, result_type = http_scan_website(website, scan_ss)

    # Build status label
    store = cd['store_name'][:35]

    if email and '@' in email:
        ssl_stats['emails_found'] += 1
        if is_suppressed(email):
            ssl_stats['previously_sent'] += 1
            print(f"  [{i+1:2d}] ✉️  {store} → {email[:45]} | previously_sent/suppressed")
        else:
            ssl_stats['new_emails'] += 1
            # Submit and check hygiene
            try:
                conn2 = get_db()
                with conn2:
                    result = submit_manual_email(
                        conn2, cd['id'], 'inventory_lane',
                        email=email, evidence_url=website,
                        evidence_snippet=email,
                        evidence_method='official_contact_page',
                        contact_role='business_email',
                        notes=f'Unified scanner: {result_type}',
                    )
                final_status = result.get('final_status', 'unknown')
                print(f"  [{i+1:2d}] ✅ {store} → {email[:45]} | hygiene={final_status}")
                if final_status in ('a0_sendable', 'a0'):
                    new_a0_promoted.append((cd['id'], store, email))
            except Exception as e:
                print(f"  [{i+1:2d}] ⚠️  {store} → {email[:45]} | submit error: {e}")
            finally:
                try:
                    conn2.close()
                except:
                    pass
    elif result_type in ('no_email_found', 'website_scanned_no_email'):
        ssl_stats['no_email'] += 1
        print(f"  [{i+1:2d}] 📄 {store} — no email on page")
    elif 'curl' in result_type and 'fail' not in result_type:
        ssl_stats['curl_ok'] += 1
        print(f"  [{i+1:2d}] 🌐 {store} — curl OK, no email")
    elif 'network' in result_type or 'ssl' in result_type or 'timeout' in result_type:
        ssl_stats['network_errors'] += 1
        print(f"  [{i+1:2d}] ⚠️  {store} — NETWORK: {result_type}")
    elif 'platform' in result_type or 'skip' in result_type or 'facebook' in website.lower():
        ssl_stats['platform_skip'] += 1
        print(f"  [{i+1:2d}] 🚫 {store} — platform skip")
    else:
        print(f"  [{i+1:2d}] ❓ {store} — {result_type}")

    time.sleep(0.15)  # gentle throttle

# ── Step 5: Final count ──
conn2 = get_db()
a0_final_raw = conn2.execute("SELECT COUNT(*) FROM leads WHERE auto_sendable=1 AND status='new' AND email IS NOT NULL AND email!=''").fetchone()[0]
a0_final_gate = len(get_sendable_leads(limit=INVENTORY_TARGET + 1, conn=conn2))
conn2.close()
gap = max(0, INVENTORY_TARGET - a0_final_gate)

print(f"\n{'='*60}")
print(f"  RESULTS")
print(f"{'='*60}")
print(f"  Direct OK:        {ssl_stats['direct_ok']}")
print(f"  Curl OK:          {ssl_stats['curl_ok']}")
print(f"  Emails found:     {ssl_stats['emails_found']}")
print(f"    → Previously sent: {ssl_stats['previously_sent']}")
print(f"    → New emails:      {ssl_stats['new_emails']}")
print(f"  No email:         {ssl_stats['no_email']}")
print(f"  Network errors:   {ssl_stats['network_errors']}")
print(f"  Platform skips:   {ssl_stats['platform_skip']}")
print(f"  New A0 promoted:  {len(new_a0_promoted)}")
for pid, pname, pemail in new_a0_promoted:
    print(f"    #{pid} {pname} → {pemail}")
print(f"")
print(f"  A0 raw (final):   {a0_final_raw}")
print(f"  A0 gate (final):  {a0_final_gate}")
print(f"  Target:           {INVENTORY_TARGET}")
print(f"  Gap:              {gap}")

# Write summary JSON
summary = {
    'timestamp': datetime.now().isoformat(),
    'target': INVENTORY_TARGET,
    'a0_raw': a0_final_raw,
    'a0_gate': a0_final_gate,
    'gap': gap,
    'candidates_scanned': len(candidates),
    'ssl_stats': ssl_stats,
    'new_a0_promoted': [{'id': pid, 'name': pn, 'email': pe} for pid, pn, pe in new_a0_promoted],
    'active_city': active_city,
    'active_state': active_state_abbr,
}
summary_path = PROJECT_DIR / 'output' / 'inventory_recovery_20260806.json'
summary_path.parent.mkdir(exist_ok=True)
with open(summary_path, 'w') as f:
    json.dump(summary, f, indent=2, default=str)
print(f"\n  Summary saved: {summary_path}")

conn.close()
