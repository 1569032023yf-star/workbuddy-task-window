#!/usr/bin/env python3
"""
Nashville Master Import + Inventory Build
Creates post-migration backup, imports all webfetch candidates,
counts inventory levels, provides readiness report.
"""

import sqlite3, json, hashlib, os, sys, shutil
from datetime import datetime, timezone

# === Configuration ===
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PROD_DB = os.path.join(PROJECT_DIR, 'data', 'bd_leads.db')
MASTER_JSON = os.path.join(PROJECT_DIR, 'data', 'webfetch_nashville_master.json')
BACKUP_DIR = os.path.join(PROJECT_DIR, 'data', 'production_acceptance_backup_20260727')

# Individual query files for incremental import
QUERY_FILES = [
    'data/webfetch_nashville_boardgame_enriched.json',
    'data/webfetch_nashville_toy_store.json',
    'data/webfetch_nashville_game_store.json',
    'data/webfetch_nashville_gift_shop.json',
    'data/webfetch_nashville_museum_gift_shop.json',
    'data/webfetch_nashville_comic_book_store.json',
    'data/webfetch_nashville_hobby_store.json',
    'data/webfetch_nashville_independent_bookstore.json',
    'data/webfetch_nashville_childrens_store.json',
]


def step1_backup():
    """Create post-migration production DB backup."""
    now = datetime.now().strftime('%Y%m%d_%H%M')
    backup_path = os.path.join(BACKUP_DIR, f'bd_leads_pre_import_{now}.db')
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(PROD_DB, backup_path)
    
    h = hashlib.sha256(open(backup_path, 'rb').read()).hexdigest()
    print(f'[BACKUP] {os.path.abspath(backup_path)}')
    print(f'[BACKUP] SHA-256: {h}')
    print(f'[BACKUP] Size: {os.path.getsize(backup_path)} bytes')
    
    # Integrity
    c = sqlite3.connect(f'file:{backup_path}?mode=ro', uri=True).cursor()
    for p in ['quick_check', 'integrity_check', 'foreign_key_check']:
        r = c.execute(f'PRAGMA {p}').fetchall()
        print(f'[BACKUP] PRAGMA {p}: {r}')
    c.connection.close()
    return backup_path


def step2_clean_test_records(conn):
    """Block any remaining acceptance test records."""
    c = conn.cursor()
    c.execute("UPDATE leads SET status='do_not_contact', notes=COALESCE(notes,'')||' [blocked:import_cleanup]' WHERE notes LIKE '%acceptance_test%' AND status != 'do_not_contact'")
    c.execute("UPDATE leads SET status='do_not_contact', notes=COALESCE(notes,'')||' [blocked:test_domain]' WHERE official_website LIKE '%test.example%' AND status != 'do_not_contact'")
    conn.commit()
    remaining = c.execute("SELECT COUNT(*) FROM leads WHERE (notes LIKE '%acceptance_test%' OR official_website LIKE '%test.example%') AND status != 'do_not_contact'").fetchone()[0]
    print(f'[CLEAN] Test records blocked: {remaining} remaining')
    return remaining == 0


def step3_import_candidates(conn):
    """Import candidates from master and individual query files via bd_db.insert_lead."""
    sys.path.insert(0, PROJECT_DIR)
    from bd_db import insert_lead
    from history_crosscheck import cross_check
    
    c = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    
    stats = {
        'staging_imported': 0,
        'leads_created': 0,
        'leads_blocked': 0,
        'history_new': 0,
        'history_previously_sent': 0,
        'history_exact_duplicate': 0,
        'history_same_org_new_location': 0,
        'history_related_location': 0,
        'history_suppressed': 0,
        'errors': 0,
        'by_classification': {},
    }
    
    # Load master JSON
    with open(MASTER_JSON, encoding='utf-8') as f:
        master = json.load(f)
    
    # Also collect individual query results
    all_candidates = []
    registry = master.get('location_registry', [])
    
    if not registry:
        print('[IMPORT] WARNING: location_registry not found in master, trying individual files')
        for qf in QUERY_FILES:
            qf_path = os.path.join(PROJECT_DIR, qf)
            if os.path.exists(qf_path):
                with open(qf_path, encoding='utf-8') as f:
                    qdata = json.load(f)
                for r in qdata.get('results', []):
                    if r.get('classification') not in ('rejected_low_product_fit', 'outside_active_city'):
                        all_candidates.append(r)
    else:
        all_candidates = registry
    
    # Import into staging first
    for loc in all_candidates:
        loc_key = loc.get('location_key', loc.get('loc', ''))
        name = loc.get('business_name', loc.get('name', ''))
        city = loc.get('city', '').strip()
        state = loc.get('state', loc.get('st', 'TN')).strip()
        org_key = loc.get('organization_key', loc.get('org', ''))
        cls = loc.get('classification', loc.get('cls', ''))
        email = loc.get('candidate_email', loc.get('email', '')) or ''
        verified = 'verified' in str(loc.get('email_verification_status', ''))
        website = loc.get('official_website', loc.get('web', '')) or ''
        domain = loc.get('normalized_domain', loc.get('nd', '')) or ''
        phone = loc.get('phone', loc.get('ph', '')) or ''
        addr = loc.get('formatted_address', loc.get('addr', '')) or ''
        ev_url = loc.get('email_evidence_url', '') or ''
        ev_snippet = loc.get('email_evidence_snippet', '') or ''
        query_hits = loc.get('query_hits', loc.get('qh', []))
        
        # Skip rejected / outside
        if cls in ('rejected_low_product_fit', 'outside_active_city'):
            continue
        
        # Insert into lead_discovery_results
        try:
            c.execute('''INSERT INTO lead_discovery_results 
                (provider, provider_result_id, business_name, formatted_address, city, state,
                 phone, website, normalized_domain, source_query, query_family, 
                 active_city_id, discovered_at, last_seen_at, validation_status, country)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,1,?,?,'validation_pending','US')''',
                ('webfetch_google_maps', loc_key, name, addr, city, state,
                 phone, website, domain, 'webfetch_master_import',
                 query_hits[0] if isinstance(query_hits, list) and query_hits else 'unknown',
                 now, now))
            stats['staging_imported'] += 1
        except Exception as e:
            print(f'[IMPORT] Staging error for {name}: {e}')
        
        # Determine lead classification
        if cls in ('official_email_verified_candidate',) and verified and email:
            status = 'new'
            score = 'A'
        elif cls == 'retail_candidate' and verified and email:
            status = 'new'
            score = 'A'
        elif cls == 'contact_form_candidate':
            status = 'contact_form_pool'
            score = 'C'
        elif cls == 'custom_production_candidate':
            status = 'manual_review_needed'
            score = 'B'
        elif cls == 'low_priority_retail_review':
            status = 'manual_review_needed'
            score = 'C'
        elif cls == 'possible_historical_duplicate':
            status = 'manual_review_needed'
            score = 'B'
        elif cls in ('manual_review_candidate', 'website_lookup_required'):
            status = 'manual_review_needed'
            score = 'B'
        else:
            status = 'manual_review_needed'
            score = 'B'
        
        contact_channel = 'contact_form' if cls == 'contact_form_candidate' else ''
        
        candidate = {
            'store_name': name,
            'store_type': 'game_store',
            'city': city,
            'state': state,
            'official_website': website,
            'email': email,
            'email_type': 'general',
            'confidence_score': score,
            'status': status,
            'product_fit': 'puzzles_games',
            'source_keyword': 'webfetch_nashville_import',
            'notes': f'webfetch_nashville; org={org_key}; cls={cls}',
            'email_source_type': 'official_page_visible' if verified else 'unknown',
            'email_verified_on_official_site': 1 if verified else 0,
            'evidence_method': 'webfetch_google_maps',
            'evidence_url': ev_url,
            'evidence_snippet': ev_snippet,
            'phone': phone,
            'formatted_address': addr,
            'organization_key': org_key,
            'location_key': loc_key,
            'contact_channel': contact_channel,
            'contact_form_url': website if cls == 'contact_form_candidate' else '',
        }
        
        # Try insert via bd_db
        try:
            result = insert_lead(candidate, conn=conn)
            if result and result.get('id'):
                stats['leads_created'] += 1
                
                # Track crosscheck result
                crosscheck = result.get('crosscheck_result', 'unknown')
                if crosscheck == 'new_candidate':
                    stats['history_new'] += 1
                elif crosscheck == 'previously_sent':
                    stats['history_previously_sent'] += 1
                elif crosscheck == 'exact_duplicate':
                    stats['history_exact_duplicate'] += 1
                elif crosscheck == 'same_organization_new_location':
                    stats['history_same_org_new_location'] += 1
                elif crosscheck == 'related_location':
                    stats['history_related_location'] += 1
                elif crosscheck == 'suppressed_or_unsubscribed':
                    stats['history_suppressed'] += 1
                
                cls_count = stats['by_classification'].get(cls, 0)
                stats['by_classification'][cls] = cls_count + 1
            else:
                stats['leads_blocked'] += 1
        except Exception as e:
            stats['errors'] += 1
            print(f'[IMPORT] Error on {name}: {e}')
    
    conn.commit()
    return stats


def step4_inventory_report(conn):
    """Generate inventory readiness report."""
    c = conn.cursor()
    
    report = {}
    
    # Strict A0 organizations (status=new, score=A, auto_sendable=1)
    a0_orgs = c.execute('''SELECT COUNT(DISTINCT COALESCE(NULLIF(organization_key,''), 'org_'||id)) 
        FROM leads WHERE status='new' AND confidence_score='A' AND auto_sendable=1
        AND email_verified_on_official_site=1 AND email IS NOT NULL AND email != '' ''').fetchone()[0]
    
    a0_locs = c.execute('''SELECT COUNT(*) FROM leads 
        WHERE status='new' AND confidence_score='A' AND auto_sendable=1
        AND email_verified_on_official_site=1 AND email IS NOT NULL AND email != '' ''').fetchone()[0]
    
    manual_review = c.execute("SELECT COUNT(*) FROM leads WHERE status='manual_review_needed' AND notes LIKE '%webfetch_nashville%'").fetchone()[0]
    contact_form = c.execute("SELECT COUNT(*) FROM leads WHERE status='contact_form_pool' AND notes LIKE '%webfetch_nashville%'").fetchone()[0]
    low_priority = c.execute("SELECT COUNT(*) FROM leads WHERE status='manual_review_needed' AND confidence_score='C' AND notes LIKE '%webfetch_nashville%'").fetchone()[0]
    website_lookup = c.execute("SELECT COUNT(*) FROM leads WHERE status='manual_review_needed' AND notes LIKE '%website_lookup%'").fetchone()[0]
    history_blocked = c.execute("SELECT COUNT(*) FROM leads WHERE notes LIKE '%webfetch_nashville%' AND (status='do_not_contact' OR notes LIKE '%previously_sent%')").fetchone()[0]
    
    total_nashville = c.execute("SELECT COUNT(*) FROM leads WHERE notes LIKE '%webfetch_nashville%'").fetchone()[0]
    
    # Sendable check
    sendable = c.execute('''SELECT id, store_name, email, organization_key FROM leads
        WHERE status='new' AND confidence_score='A' AND auto_sendable=1
        AND email_verified_on_official_site=1 AND email IS NOT NULL AND email != ''
        AND email_source_type IN ('official_page_visible','official_mailto','wholesale_vendor_page','manual_lookup')
        AND evidence_url IS NOT NULL AND evidence_url != ''
        AND evidence_snippet IS NOT NULL AND evidence_snippet != ''
        AND evidence_method IS NOT NULL
        AND unsubscribed_at IS NULL AND official_website IS NOT NULL
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status='sent' AND message_type='new_outreach')
        AND bounced_at IS NULL
        AND (mx_provider IS NULL OR mx_provider='' OR (mx_provider NOT LIKE '%exchange%' AND mx_provider NOT LIKE '%outlook%' AND mx_provider NOT LIKE '%microsoft%'))
        ORDER BY id''').fetchall()
    
    report = {
        'strict_a0_organizations': a0_orgs,
        'strict_a0_locations': a0_locs,
        'outreach_opportunities': a0_orgs,
        'manual_review': manual_review,
        'contact_form': contact_form,
        'low_priority': low_priority,
        'website_lookup': website_lookup,
        'history_blocked': history_blocked,
        'total_nashville_candidates': total_nashville,
        'sendable_details': [(r[0], r[1], r[2][:30] if r[2] else '', r[3]) for r in sendable],
        'gap_to_40': max(0, 40 - a0_orgs),
        'gap_to_80': max(0, 80 - a0_orgs),
        'gap_to_120': max(0, 120 - a0_orgs),
    }
    
    return report


if __name__ == '__main__':
    print('=' * 60)
    print('NASHVILLE MASTER IMPORT + INVENTORY BUILD')
    print('=' * 60)
    print()
    
    # Step 1: Backup
    print('--- STEP 1: Production DB Backup ---')
    backup = step1_backup()
    print()
    
    # Connect to production
    conn = sqlite3.connect(PROD_DB)
    
    # Step 2: Clean test records
    print('--- STEP 2: Clean Test Records ---')
    clean_ok = step2_clean_test_records(conn)
    print()
    
    # Step 3: Import
    print('--- STEP 3: Import Candidates ---')
    stats = step3_import_candidates(conn)
    print(f'  Staging imported: {stats["staging_imported"]}')
    print(f'  Leads created: {stats["leads_created"]}')
    print(f'  Leads blocked: {stats["leads_blocked"]}')
    print(f'  Errors: {stats["errors"]}')
    print(f'  History: new={stats["history_new"]} prev_sent={stats["history_previously_sent"]} dup={stats["history_exact_duplicate"]} same_org={stats["history_same_org_new_location"]}')
    print(f'  By class: {stats["by_classification"]}')
    print()
    
    # Step 4: Report
    print('--- STEP 4: Inventory Report ---')
    report = step4_inventory_report(conn)
    print(f'  Strict A0 Organizations: {report["strict_a0_organizations"]}')
    print(f'  Strict A0 Locations: {report["strict_a0_locations"]}')
    print(f'  Organization Outreach Opportunities: {report["outreach_opportunities"]}')
    print(f'  Manual Review: {report["manual_review"]}')
    print(f'  Contact Form: {report["contact_form"]}')
    print(f'  Low Priority: {report["low_priority"]}')
    print(f'  Website Lookup: {report["website_lookup"]}')
    print(f'  History Blocked: {report["history_blocked"]}')
    print(f'  Total Nashville Candidates: {report["total_nashville_candidates"]}')
    print()
    print(f'  Gap to 40 (critical): {report["gap_to_40"]}')
    print(f'  Gap to 80 (warning): {report["gap_to_80"]}')
    print(f'  Gap to 120 (target): {report["gap_to_120"]}')
    print()
    
    if report['sendable_details']:
        print('  Sendable A0 leads:')
        for sid, sname, semail, sorg in report['sendable_details']:
            print(f'    id={sid} {sname[:40]} email={semail} org={sorg}')
    else:
        print('  Sendable A0 leads: NONE')
    
    conn.close()
    
    print()
    print('=' * 60)
    print('IMPORT COMPLETE')
    print(f'Backup: {backup}')
    print(f'To start review server: python bd_review_server.py --port 8765')
    print('=' * 60)
