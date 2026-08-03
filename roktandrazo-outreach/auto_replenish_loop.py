
# ══ P0 HARD-DISABLED: Production SMTP blocked ══
class LegacySMTPDisabledError(Exception): pass
import os as _os
if not _os.environ.get('BD_TEST_MODE')=='true':
    raise LegacySMTPDisabledError('Legacy SMTP disabled. Use bd_orchestrator with valid authorization.')
#!/usr/bin/env python3
"""
Auto Replenish Loop — Roktandrazo BD Closed-Loop Automation

Implements:
1. Auto-replenish: When today_sent=0, auto-send to 20; when pool<20, replenish to 20
2. Manual confirmation notification: Auto-notify for leads needing manual review
3. B pool dedup: Remove all manually reviewed leads from B pool
4. Closed-loop: Full automation without manual intervention

Usage:
    # Run once (check and act)
    python auto_replenish_loop.py

    # Run in loop mode (continuous monitoring)
    python auto_replenish_loop.py --loop --interval 300

    # Dry run (no actual sending)
    python auto_replenish_loop.py --dry-run
"""

import argparse
import os
import sys
import time
import sqlite3
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)
os.chdir(PROJECT_DIR)

from bd_db import get_db, get_config, set_config, get_sendable_leads
from bd_template import get_email_for_lead
from bd_sender import send_one

DB_PATH = os.path.join(PROJECT_DIR, 'data', 'bd_leads.db')
DAILY_TARGET = 20
POOL_FLOOR = 20


def get_today_sent_count():
    """Get count of emails sent today."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM send_log WHERE date(sent_at) = date('now') AND status='sent'")
    count = c.fetchone()[0]
    conn.close()
    return count


def get_a0_sendable_count():
    """Get count of A0 sendable leads."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A'
        AND email_verified_on_official_site=1
        AND email_source_type IN ('official_page_visible','official_mailto','wholesale_vendor_page','manual_lookup')
        AND email IS NOT NULL AND email != ''
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent','bounced'))
        AND (mx_provider IS NULL OR mx_provider = '' OR
             (mx_provider NOT LIKE '%exchange%' AND mx_provider NOT LIKE '%outlook%' AND mx_provider NOT LIKE '%microsoft%'))''')
    count = c.fetchone()[0]
    conn.close()
    return count


def get_b_pool_stats():
    """Get B pool statistics with dedup info."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # B pool: not reviewed
    c.execute('''SELECT COUNT(*) FROM leads 
        WHERE confidence_score='B' 
        AND status IN ('new', 'manual_review_needed')
        AND id NOT IN (SELECT id FROM leads WHERE status='reviewed')''')
    b_active = c.fetchone()[0]
    
    # B pool: reviewed (should be excluded)
    c.execute('''SELECT COUNT(*) FROM leads 
        WHERE confidence_score='B' AND status='reviewed' ''')
    b_reviewed = c.fetchone()[0]
    
    # Manual review needed
    c.execute('''SELECT COUNT(*) FROM leads 
        WHERE confidence_score='B' AND status='manual_review_needed' ''')
    manual_needed = c.fetchone()[0]
    
    conn.close()
    return {
        'b_active': b_active,
        'b_reviewed': b_reviewed,
        'manual_needed': manual_needed
    }


def deduplicate_b_pool():
    """Mark B pool leads that have been manually reviewed."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Find B leads that are in send_log (already sent/reviewed)
    c.execute('''SELECT l.id FROM leads l 
        WHERE l.confidence_score='B' 
        AND l.status IN ('new', 'manual_review_needed')
        AND l.id IN (SELECT lead_id FROM send_log)''')
    already_sent = [r[0] for r in c.fetchall()]
    
    # Mark as reviewed
    updated = 0
    for lead_id in already_sent:
        c.execute('UPDATE leads SET status = "reviewed" WHERE id = ? AND status != "reviewed"', (lead_id,))
        if c.rowcount > 0:
            updated += 1
    
    conn.commit()
    conn.close()
    return updated


def replenish_a0_pool(dry_run=False):
    """Replenish A0 pool to reach POOL_FLOOR."""
    current = get_a0_sendable_count()
    gap = POOL_FLOOR - current
    
    if gap <= 0:
        print(f'  [OK] A0 pool sufficient: {current} >= {POOL_FLOOR}')
        return 0
    
    print(f'  [REPLENISH] A0 pool: {current}, need {gap} more')
    
    if dry_run:
        print(f'  [DRY-RUN] Would replenish {gap} leads')
        return gap
    
    # Try to upgrade B leads to A0
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Find B leads with verified emails that could be A0
    c.execute('''SELECT id, store_name, email, official_website 
        FROM leads 
        WHERE confidence_score='B' 
        AND status IN ('new', 'manual_review_needed')
        AND email IS NOT NULL AND email != ''
        AND email_verified_on_official_site=1
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent','bounced'))
        LIMIT ?''', (gap,))
    
    upgradeable = c.fetchall()
    upgraded = 0
    
    for lead_id, name, email, website in upgradeable:
        c.execute('UPDATE leads SET confidence_score = "A" WHERE id = ?', (lead_id,))
        upgraded += 1
        print(f'    Upgraded: {name} ({email[:5]}***)')
    
    conn.commit()
    conn.close()
    
    print(f'  [REPLENISH] Upgraded {upgraded} B leads to A0')
    return upgraded


def auto_send(dry_run=False):
    """Auto-send emails to reach daily target."""
    today_sent = get_today_sent_count()
    gap = DAILY_TARGET - today_sent
    
    if gap <= 0:
        print(f'  [OK] Daily target reached: {today_sent}/{DAILY_TARGET}')
        return 0
    
    a0_count = get_a0_sendable_count()
    send_count = min(gap, a0_count)
    
    if send_count <= 0:
        print(f'  [WARN] No A0 leads available for sending')
        return 0
    
    print(f'  [SEND] Today sent: {today_sent}, need {send_count} more')
    
    if dry_run:
        print(f'  [DRY-RUN] Would send {send_count} emails')
        return send_count
    
    leads = get_sendable_leads(limit=send_count)
    sent = 0
    failed = 0
    
    for lead in leads:
        ed = get_email_for_lead(lead)
        lead['email_subject'] = ed['subject']
        lead['email_body'] = ed['body_text']
        lead['email_body_html'] = ed.get('body_html', '')
        
        result = send_one(lead, dry_run=False)
        if result.get('status') == 'sent':
            sent += 1
            print(f'    Sent: {lead.get("store_name", "?")}')
        else:
            failed += 1
            print(f'    Failed: {lead.get("store_name", "?")} - {result.get("message", "?")}')
        
        if sent < send_count:
            time.sleep(90)  # Wait between sends
    
    print(f'  [SEND] Sent: {sent}, Failed: {failed}')
    return sent


def generate_notification():
    """Generate notification for manual review leads."""
    stats = get_b_pool_stats()
    
    if stats['manual_needed'] == 0:
        return None
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''SELECT id, store_name, city, state, email, official_website 
        FROM leads 
        WHERE confidence_score='B' AND status='manual_review_needed'
        ORDER BY collected_at DESC
        LIMIT 10''')
    
    leads = c.fetchall()
    conn.close()
    
    notification = {
        'type': 'manual_review_needed',
        'count': stats['manual_needed'],
        'leads': []
    }
    
    for lead_id, name, city, state, email, website in leads:
        notification['leads'].append({
            'id': lead_id,
            'store': name,
            'location': f'{city}, {state}',
            'email': email[:5] + '***' if email else 'N/A',
            'website': website or 'N/A'
        })
    
    return notification


def run_cycle(dry_run=False):
    """Run one cycle of the closed-loop system."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'\n=== Auto Replenish Loop Cycle: {now} ===')
    
    # Step 1: Deduplicate B pool
    print('\n[Step 1] B Pool Deduplication')
    deduped = deduplicate_b_pool()
    print(f'  Deduplicated: {deduped} leads')
    
    # Step 2: Check and replenish A0 pool
    print('\n[Step 2] A0 Pool Replenishment')
    replenished = replenish_a0_pool(dry_run)
    
    # Step 3: Auto-send if needed
    print('\n[Step 3] Auto-Send')
    sent = auto_send(dry_run)
    
    # Step 4: Generate notification for manual review
    print('\n[Step 4] Manual Review Notification')
    notification = generate_notification()
    if notification:
        print(f'  Manual review needed: {notification["count"]} leads')
        for lead in notification['leads'][:5]:
            print(f'    - {lead["store"]} ({lead["location"]})')
    else:
        print('  No manual review needed')
    
    # Step 5: Status summary
    print('\n[Step 5] Status Summary')
    a0 = get_a0_sendable_count()
    today_sent = get_today_sent_count()
    b_stats = get_b_pool_stats()
    
    print(f'  A0 sendable: {a0}')
    print(f'  Today sent: {today_sent}/{DAILY_TARGET}')
    print(f'  B pool active: {b_stats["b_active"]}')
    print(f'  B pool reviewed: {b_stats["b_reviewed"]}')
    print(f'  Manual review needed: {b_stats["manual_needed"]}')
    
    return {
        'deduped': deduped,
        'replenished': replenished,
        'sent': sent,
        'a0_sendable': a0,
        'today_sent': today_sent,
        'b_stats': b_stats,
        'notification': notification
    }


def main():
    parser = argparse.ArgumentParser(description='Auto Replenish Loop')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    parser.add_argument('--loop', action='store_true', help='Run in continuous loop')
    parser.add_argument('--interval', type=int, default=300, help='Loop interval in seconds')
    args = parser.parse_args()
    
    print('=== Auto Replenish Loop System ===')
    print(f'Daily Target: {DAILY_TARGET}')
    print(f'Pool Floor: {POOL_FLOOR}')
    print(f'Mode: {"DRY-RUN" if args.dry_run else "LIVE"}')
    print(f'Loop: {args.loop} (interval: {args.interval}s)')
    
    if args.loop:
        while True:
            try:
                run_cycle(args.dry_run)
                print(f'\nNext cycle in {args.interval} seconds...')
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print('\nLoop stopped by user')
                break
            except Exception as e:
                print(f'\nError: {e}')
                time.sleep(60)
    else:
        run_cycle(args.dry_run)


if __name__ == '__main__':
    main()
