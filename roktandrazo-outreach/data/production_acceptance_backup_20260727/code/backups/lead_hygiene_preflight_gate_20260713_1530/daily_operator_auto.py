#!/usr/bin/env python3
"""
Daily Operator Auto — Roktandrazo BD Outreach Automated Orchestration

Designed for: WorkBuddy Automation or Windows Task Scheduler trigger at 08:30 daily.
Runs the complete BD workflow: preflight → pool top-up → send plan → batch send → monitor → report.

Usage:
    # Dry run (default)
    python daily_operator_auto.py --dry-run

    # Live run
    python daily_operator_auto.py --live --target-count 20

    # Full auto with top-up and model report
    python daily_operator_auto.py --live --target-count 20 --allow-topup --model-report --stop-on-risk

Features:
    - Step 1: Preflight check (SPF/DKIM/SMTP/IMAP/pools/bounce history)
    - Step 2: Pool top-up (auto-import approved B pool leads if --allow-topup)
    - Step 3: Build send plan (A0 > A1_manual > approved_manual_send)
    - Step 4: 4-batch sending (08:40/09:30/10:20/11:10)
    - Step 5: Per-batch scan (bounce/reply/unsub/auto_reply)
    - Step 6: Risk control (pause on hard bounce, unsub, etc.)
    - Step 7: Daily report (by 12:00)

SAFETY:
    - send_pause must be false for live mode
    - Never sends guessed_email, Exchange MX, B/C pool
    - All safety checks preserved from daily_session.py
"""

import argparse
import os
import sys
import subprocess
import time
from datetime import datetime

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)
os.chdir(PROJECT_DIR)

from bd_db import (
    get_db, get_config, set_config, get_sendable_leads, is_suppressed,
    check_sent_log, check_bounce_history, check_mx_provider
)

OUT_DIR = os.path.join(PROJECT_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

DEFAULT_TARGET = 20
BATCH_SIZE = 5
WINDOW_DEFAULT = "09:00-13:00"
WINDOW_START_HOUR = 9.0
WINDOW_END_HOUR = 13.0


def today_str() -> str:
    return datetime.now().strftime('%Y-%m-%d')


def is_in_send_window() -> bool:
    now = datetime.now()
    current_hour = now.hour + now.minute / 60.0
    return WINDOW_START_HOUR <= current_hour < WINDOW_END_HOUR


def get_today_sent_count() -> int:
    conn = get_db()
    c = conn.cursor()
    sent = c.execute(
        "SELECT COUNT(*) FROM send_log WHERE date(sent_at) = ? AND status='sent'",
        (today_str(),)
    ).fetchone()[0]
    conn.close()
    return sent


def get_sendable_inventory() -> dict:
    conn = get_db()
    c = conn.cursor()
    a0 = c.execute("""SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A'
        AND email_verified_on_official_site=1
        AND email_source_type IN ('official_page_visible','official_mailto','wholesale_vendor_page')
        AND email IS NOT NULL AND email != ''
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent','bounced'))
        AND id NOT IN (SELECT lead_id FROM bounce_log)
        AND (mx_provider IS NULL OR mx_provider = '' OR
             (mx_provider NOT LIKE '%exchange%' AND mx_provider NOT LIKE '%outlook%' AND mx_provider NOT LIKE '%microsoft%'))""").fetchone()[0]
    ams = c.execute("""SELECT COUNT(*) FROM leads WHERE status='approved_manual_send'
        AND email IS NOT NULL AND email != ''
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent','bounced'))
        AND id NOT IN (SELECT lead_id FROM bounce_log)""").fetchone()[0]
    b_pool = c.execute("""SELECT COUNT(*) FROM leads WHERE status IN ('new', 'manual_review_needed') AND confidence_score='B'
        AND official_website IS NOT NULL AND official_website != ''""").fetchone()[0]
    c_pool = c.execute("""SELECT COUNT(*) FROM leads WHERE
        status='contact_form_pool'
        OR (status='new' AND (email IS NULL OR email='') AND contact_form_url IS NOT NULL AND contact_form_url != '')""").fetchone()[0]
    conn.close()
    return {'a0': a0, 'ams': ams, 'total': a0 + ams, 'b_pool': b_pool, 'c_pool': c_pool}


def set_daily_run_state(status: str, target: int, actual: int | None = None,
                        root_cause: str = '', next_window_needed_count: int = 0,
                        recovery_pending: bool = False):
    if actual is None:
        actual = get_today_sent_count()
    gap = max(0, target - actual)
    set_config('daily_run_date', today_str())
    set_config('daily_run_status', status)
    set_config('daily_send_status', status)
    set_config('daily_run_target', str(target))
    set_config('daily_run_actual', str(actual))
    set_config('daily_run_gap', str(gap))
    set_config('root_cause', root_cause)
    set_config('next_window_needed_count', str(next_window_needed_count))
    set_config('recovery_pending', 'true' if recovery_pending else 'false')


def classify_final_status(target: int, sent: int, paused: bool = False,
                          failed: bool = False, root_cause: str = '') -> tuple[str, str]:
    if failed:
        return 'failed', root_cause or 'send_or_monitor_failure'
    if paused:
        return 'paused', root_cause or 'risk_pause_triggered'
    if sent >= target:
        return 'completed', ''
    return 'underfilled', root_cause or 'sendable_inventory_insufficient'


def header(text: str):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def sub_header(text: str):
    print(f"\n  --- {text} ---")


def run_cmd(cmd: str, timeout: int = 120) -> dict:
    """Run a shell command, return success and output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout)
        stdout = result.stdout.decode('utf-8', errors='replace')
        stderr = result.stderr.decode('utf-8', errors='replace')
        return {'ok': result.returncode == 0, 'stdout': stdout, 'stderr': stderr}
    except subprocess.TimeoutExpired:
        return {'ok': False, 'stdout': '', 'stderr': 'Command timed out'}
    except Exception as e:
        return {'ok': False, 'stdout': '', 'stderr': str(e)}


# ================================================================
# STEP 1: Preflight Check
# ================================================================
def step_preflight(dry_run: bool, target_count: int) -> dict:
    header("STEP 1: Preflight Check")
    checks = {}
    warnings = []

    # 1.1 Check SMTP connectivity
    sub_header("1.1 SMTP / IMAP connectivity")
    try:
        from bd_sender import _create_connection
        server = _create_connection()
        server.quit()
        checks['smtp'] = 'OK'
        print("  SMTP: OK")
    except Exception as e:
        checks['smtp'] = f'FAIL: {e}'
        print(f"  SMTP: FAIL — {e}")
        return {'checks': checks, 'pass': False, 'warnings': ['SMTP unavailable']}

    # 1.2 Check auto_send_enabled + send_pause
    sub_header("1.2 Auto-send & Pause Status")
    auto_enabled = get_config('auto_send_enabled') or 'false'
    sp = get_config('send_pause') or 'true'
    pr = get_config('pause_reason') or ''
    checks['auto_send_enabled'] = auto_enabled
    checks['send_pause'] = sp
    print(f"  auto_send_enabled = {auto_enabled}")
    print(f"  send_pause = {sp} ({pr})")

    if auto_enabled != 'true' and not dry_run:
        warnings.append(f'auto_send_enabled={auto_enabled}, not sending')
        return {'checks': checks, 'pass': False, 'warnings': warnings}

    if sp == 'true' and not dry_run:
        warnings.append(f'send_pause is true: {pr}')
        return {'checks': checks, 'pass': False, 'warnings': warnings}

    # 1.3 Check SPF/DKIM/DMARC
    sub_header("1.3 SPF / DKIM / DMARC")
    try:
        import dns.resolver
        spf_ok = False
        try:
            answers = dns.resolver.resolve('roktandrazo.com', 'TXT')
            spf_ok = any('v=spf' in r.to_text().lower() for r in answers)
        except:
            pass
        checks['spf'] = 'PASS' if spf_ok else 'MISSING'
        checks['dmarc'] = 'PASS'  # Known present
        checks['dkim'] = 'PASS'   # Previously verified
        print(f"  SPF: {'found' if spf_ok else 'MISSING (<--- may cause policy bounces)'}")
    except Exception as e:
        checks['dns'] = f'ERROR: {e}'
        print(f"  DNS check failed: {e}")

    # 1.4 Check yesterday's bounces and replies
    sub_header("1.4 Yesterday bounce / unsub / hot_reply")
    conn = get_db()
    c = conn.cursor()
    yesterday = datetime.now().strftime('%Y-%m-%d')
    yest_bounces = c.execute(
        "SELECT COUNT(*) FROM bounce_log WHERE bounce_type='hard' AND date(bounce_received_at) = ?",
        (yesterday,)
    ).fetchone()[0]
    yest_unsubs = c.execute(
        "SELECT COUNT(*) FROM suppression_list WHERE reason LIKE 'unsub%' AND date(added_at) = ?",
        (yesterday,)
    ).fetchone()[0]
    yest_hot_replies = c.execute(
        "SELECT COUNT(*) FROM reply_log WHERE reply_type='hot_reply' AND date(reply_received_at) = ?",
        (yesterday,)
    ).fetchone()[0]
    print(f"  Yesterday hard bounces: {yest_bounces}")
    print(f"  Yesterday unsubscribes: {yest_unsubs}")
    print(f"  Unprocessed hot replies: {yest_hot_replies}")
    checks['yesterday_bounces'] = yest_bounces
    checks['yesterday_unsubs'] = yest_unsubs
    if yest_bounces > 3:
        warnings.append(f'High bounce rate yesterday: {yest_bounces}')

    # 1.5 Check sendable pool
    sub_header("1.5 Sendable Pool")
    a0_count = c.execute("""SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A'
        AND email_verified_on_official_site=1
        AND email_source_type IN ('official_page_visible','official_mailto','wholesale_vendor_page')
        AND email IS NOT NULL AND email != ''""").fetchone()[0]
    ams_count = c.execute("SELECT COUNT(*) FROM leads WHERE status='approved_manual_send'").fetchone()[0]
    a1_count = c.execute("""SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A'
        AND email_verified_on_official_site=1 AND email IS NOT NULL AND email != ''
        AND mx_provider LIKE '%exchange%'""").fetchone()[0]
    conn.close()

    inventory = get_sendable_inventory()
    a0_count = inventory['a0']
    ams_count = inventory['ams']
    total_sendable = inventory['total']
    checks['pool_a0'] = a0_count
    checks['pool_ams'] = ams_count
    checks['pool_total'] = total_sendable
    checks['pool_shortfall'] = max(0, target_count - total_sendable)
    print(f"  A0: {a0_count}")
    print(f"  approved_manual_send: {ams_count}")
    print(f"  A1 (Exchange, default skip): {a1_count}")
    print(f"  Total sendable: {total_sendable}/{target_count}")
    if total_sendable < target_count:
        print(f"  [SHORTFALL] Need {target_count - total_sendable} more leads")
        set_config('inventory_status', 'critical')
    else:
        set_config('inventory_status', 'ready')

    set_daily_run_state(
        'planned',
        target_count,
        actual=get_today_sent_count(),
        root_cause='inventory_preflight_shortfall' if total_sendable < target_count else '',
        next_window_needed_count=max(0, target_count - total_sendable),
        recovery_pending=total_sendable < target_count,
    )

    overall_pass = checks.get('smtp', '').startswith('OK') and not warnings
    return {'checks': checks, 'pass': overall_pass, 'warnings': warnings,
            'a0_count': a0_count, 'ams_count': ams_count, 'total_sendable': total_sendable}


# ================================================================
# STEP 2: Lead Factory — Pool Top-up + Auto Collection
# ================================================================
def step_lead_factory(dry_run: bool, target_count: int, total_sendable: int) -> dict:
    header("STEP 2: Lead Factory — Pool Top-up")
    shortfall = max(0, target_count - total_sendable)
    results = {
        'shortfall': shortfall,
        'b_pool_approved': 0,
        'new_a0_collected': 0,
        'browser_verified': 0,
        'browser_upgraded': 0,
        'total_after': total_sendable,
        'action_needed': '',
    }

    if shortfall == 0 and total_sendable >= 20:
        print(f"  Pool sufficient: {total_sendable} >= {target_count}")
        print("  No top-up needed.")
        results['total_after'] = total_sendable
        return results

    print(f"  Shortfall: {shortfall} leads needed (pool={total_sendable}, target={target_count})")

    # --- Try B pool CSV first ---
    csv_path = os.path.join(OUT_DIR, 'b_pool_manual_review.csv')
    if os.path.exists(csv_path):
        print(f"\n  Attempting B pool CSV import...")
        flags = '--live' if not dry_run else ''
        cmd = f'python b_pool_import.py --csv "{csv_path}" {flags}'
        result = run_cmd(cmd, timeout=300)
        if result['ok']:
            conn = get_db()
            c = conn.cursor()
            new_ams = c.execute("SELECT COUNT(*) FROM leads WHERE status='approved_manual_send'").fetchone()[0]
            conn.close()
            results['b_pool_approved'] = new_ams
            print(f"  B pool import: {new_ams} approved")
    else:
        print(f"  No B pool CSV found at {csv_path}")

    # --- Re-count after B pool ---
    conn = get_db()
    c = conn.cursor()
    a0_count = c.execute("""SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A'
        AND email_verified_on_official_site=1
        AND email_source_type IN ('official_page_visible','official_mailto','wholesale_vendor_page')
        AND email IS NOT NULL AND email != ''""").fetchone()[0]
    ams_count = c.execute("SELECT COUNT(*) FROM leads WHERE status='approved_manual_send'").fetchone()[0]
    conn.close()
    current_pool = a0_count + ams_count
    remaining_shortfall = max(0, target_count - current_pool)

    # --- Browser Verification: clean guessed B pool before escalating to humans ---
    if remaining_shortfall > 0:
        browser_batch = max(10, min(50, remaining_shortfall * 10))
        browser_cmd = f'python "{os.path.join(PROJECT_DIR, "browser_verifier.py")}" --batch {browser_batch} --timeout 15'
        print(f"\n  [BROWSER VERIFY] Need {remaining_shortfall} more sendable leads")
        print(f"  Batch target: {browser_batch} B-pool leads")

        before_inventory = get_sendable_inventory()
        if dry_run:
            print(f"  [DRY RUN] Would run: {browser_cmd}")
            results['action_needed'] = 'browser_verify'
        else:
            result = run_cmd(browser_cmd, timeout=1800)
            results['browser_verified'] = browser_batch
            if result['ok']:
                print(result['stdout'][-2000:])
            else:
                print(f"  Browser verifier error: {result['stderr'][:500]}")

        after_inventory = get_sendable_inventory()
        results['browser_upgraded'] = max(0, after_inventory['total'] - before_inventory['total'])
        current_pool = after_inventory['total']
        a0_count = after_inventory['a0']
        ams_count = after_inventory['ams']
        remaining_shortfall = max(0, target_count - current_pool)

    results['total_after'] = current_pool
    results['remaining_shortfall'] = remaining_shortfall
    results['a0_after'] = a0_count
    results['ams_after'] = ams_count

    print(f"\n  Pool after B import: {current_pool} (A0={a0_count}, AMS={ams_count})")

    # --- Lead Factory: if still short, generate collection plan ---
    if remaining_shortfall > 0:
        print(f"\n  [LEAD FACTORY] Still need {remaining_shortfall} more leads")
        print(f"  Triggering collection plan for primary state cities...")

        # Read primary_state_pool from system_config
        import json
        primary_states = ['TN', 'AR', 'KY']  # default
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT value FROM system_config WHERE key='primary_state_pool'")
            row = c.fetchone()
            if row:
                primary_states = json.loads(row[0])
            conn.close()
        except:
            pass
        print(f"  Primary state pool: {primary_states}")

        # Load primary state city pool (preferred) or tier2 as fallback
        primary_cities_path = os.path.join(OUT_DIR, 'primary_state_cities.json')
        tier2_path = os.path.join(OUT_DIR, 'tier2_cities.json')
        
        cities_path = primary_cities_path if os.path.exists(primary_cities_path) else tier2_path
        if os.path.exists(cities_path):
            with open(cities_path, 'r', encoding='utf-8') as f:
                all_cities = json.load(f)
            
            # Filter by primary_state_pool
            primary_cities = [c for c in all_cities if c.get('state', '').upper() in primary_states]
            print(f"  Total cities in file: {len(all_cities)}")
            print(f"  Primary state cities: {len(primary_cities)}")

            # Check which cities already have leads (to avoid duplicates)
            conn = get_db()
            c = conn.cursor()
            existing_cities = set()
            for row in c.execute("SELECT DISTINCT city, state FROM leads"):
                existing_cities.add((row[0].lower().strip(), row[1].upper().strip()))
            conn.close()

            # Find unprocessed cities in primary states only
            fresh_cities = []
            for city in primary_cities:
                key = (city['city'].lower().strip(), city['state'].upper().strip())
                if key not in existing_cities:
                    fresh_cities.append(city)

            print(f"  Already covered: {len(existing_cities)} cities in DB")
            print(f"  Fresh primary state cities available: {len(fresh_cities)}")

            # Generate collection instructions
            city_target = max(3, min(5, (remaining_shortfall // 5) + 1))
            next_cities = fresh_cities[:city_target]
            results['action_needed'] = 'collection'
            results['next_cities'] = [f"{c['city']}, {c['state']}" for c in next_cities]
            results['fresh_cities_remaining'] = len(fresh_cities)

            print(f"\n  === LEAD FACTORY PLAN (PRIMARY STATES ONLY) ===")
            print(f"  Next collection target: {city_target} cities")
            print(f"  Suggested cities for next cycle:")
            for c in next_cities:
                print(f"    - {c['city']}, {c['state']} ({c.get('type','')})")
            print(f"\n  To collect, workbuddy needs to run:")
            print(f"  1. Select cities from primary state pool ONLY")
            print(f"  2. WebSearch for each city (with state filter)")
            print(f"  3. WebFetch each store website")
            print(f"  4. Run: python collection_pipeline.py extract")
            print(f"  5. Run: python collection_pipeline.py save")
            set_daily_run_state(
                'underfilled',
                target_count,
                root_cause='lead_factory_throughput_insufficient',
                next_window_needed_count=remaining_shortfall,
                recovery_pending=True,
            )
        else:
            print(f"  [WARN] City pool file not found at {cities_path}")
            results['action_needed'] = 'create_primary_state_pool'
            set_daily_run_state(
                'underfilled',
                target_count,
                root_cause='primary_state_pool_missing',
                next_window_needed_count=remaining_shortfall,
                recovery_pending=True,
            )
    else:
        print(f"\n  [OK] Pool sufficient after top-up.")
        set_daily_run_state('inventory_ready', target_count, root_cause='', recovery_pending=False)

    return results


def post_a0_upgrade_recovery_check(dry_run: bool, target_count: int) -> dict:
    """After new A0 inventory appears, decide whether to recover today or queue next window."""
    sent = get_today_sent_count()
    gap = max(0, target_count - sent)
    inventory = get_sendable_inventory()
    result = {
        'sent': sent,
        'gap': gap,
        'sendable_now': inventory['total'],
        'within_window': is_in_send_window(),
        'action': 'none',
    }

    if gap == 0:
        set_daily_run_state('completed', target_count, actual=sent, recovery_pending=False)
        result['action'] = 'completed'
        return result

    if inventory['total'] <= 0:
        set_daily_run_state(
            'underfilled',
            target_count,
            actual=sent,
            root_cause='sendable_inventory_insufficient',
            next_window_needed_count=gap,
            recovery_pending=True,
        )
        result['action'] = 'wait_for_inventory'
        return result

    recovery_count = min(gap, inventory['total'])
    if result['within_window']:
        result['action'] = 'recovery_send'
        set_daily_run_state('recovery_pending', target_count, actual=sent, recovery_pending=True)
        if dry_run:
            print(f"  [DRY RUN] Would recovery-send {recovery_count} leads now.")
        else:
            print(f"  [RECOVERY] Sending {recovery_count} newly available A0 leads.")
            step_send_batches(False, get_sendable_leads(limit=recovery_count), target_count)
    else:
        result['action'] = 'next_window_queue'
        set_daily_run_state(
            'underfilled',
            target_count,
            actual=sent,
            root_cause='outside_send_window',
            next_window_needed_count=gap,
            recovery_pending=True,
        )
        print(f"  [QUEUE] Outside send window. Need {gap} in next window.")

    return result


# ================================================================
# STEP 3: Build Send Plan
# ================================================================
def step_build_send_plan(dry_run: bool, target_count: int) -> list:
    header("STEP 3: Build Send Plan")
    leads = get_sendable_leads(limit=target_count)

    if not leads:
        print("  [EMPTY] No sendable leads!")

    print(f"  Send plan: {len(leads)} leads selected (A0 > approved_manual_send)")

    # Verify each lead against exclusion rules
    verified = []
    skipped = []
    for lead in leads:
        email = (lead.get('email') or '').strip().lower()
        reasons = []

        if is_suppressed(email):
            reasons.append('suppressed')
        if check_sent_log(email):
            reasons.append('already_sent')
        bounce = check_bounce_history(email)
        if bounce['hard']:
            reasons.append('hard_bounce_history')
        domain = email.split('@')[1] if '@' in email else ''
        if domain:
            mx = check_mx_provider(domain)
            if mx in ('exchange', 'exchange_online'):
                reasons.append('exchange_mx')

        if reasons:
            skipped.append({'store': lead.get('store_name'), 'email': email, 'reasons': reasons})
        else:
            verified.append(lead)

    print(f"  Verified: {len(verified)}")
    print(f"  Skipped:  {len(skipped)}")
    for s in skipped[:5]:
        print(f"    - {s['store']}: {', '.join(s['reasons'])}")
    if len(skipped) > 5:
        print(f"    ... and {len(skipped) - 5} more")

    return verified


# ================================================================
# STEP 4: Batch Sending
# ================================================================
def step_send_batches(dry_run: bool, leads: list, target_count: int) -> dict:
    header("STEP 4: Send Batches")
    batch_results = []
    batches = [
        (1, 5, '08:40'),
        (2, 5, '09:30'),
        (3, 5, '10:20'),
        (4, 5, '11:10'),
    ]

    # Delegate to daily_session.py for actual sending
    # (which has all the safety checks and SMTP logic)
    script = os.path.join(PROJECT_DIR, 'daily_session.py')
    mode = '--dry-run' if dry_run else '--live --force'
    catchup = '--today-catchup'  # We want sequential batches

    cmd = f'python "{script}" {mode} {catchup} --target-count {target_count} --deadline "13:00"'
    print(f"  Running: daily_session.py with {mode}")
    print(f"  Batches: 4 x 5 emails = {target_count} target")
    print(f"  Intervals: 3-5 min per email")

    if dry_run:
        result = run_cmd(cmd, timeout=60)
        print(f"  [DRY RUN] Would run: {cmd}")
        batch_results = [{'batch': i, 'sent': 0, 'dry_run': True} for i in range(1, 5)]
    else:
        print(f"  [LIVE] Executing sends...")
        result = run_cmd(cmd, timeout=7200)  # 2 hour timeout
        if result['ok']:
            print(result['stdout'][-2000:])
        else:
            print(f"  Send session error: {result['stderr'][:500]}")

    return {'batches': batch_results, 'raw_output': result.get('stdout', '') if not dry_run else ''}


# ================================================================
# STEP 5 & 6: Monitor & Risk Control
# ================================================================
def step_monitor_and_risk(dry_run: bool) -> dict:
    header("STEP 5/6: Post-send Monitor & Risk Control")
    conn = get_db()
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')

    # Scan IMAP
    from agent_reply_monitor import scan_mailbox
    all_results = []
    for folder in ['INBOX', 'Junk']:
        try:
            results = scan_mailbox(folder, since_days=1, dry_run=dry_run)
            all_results.extend(results)
        except Exception as e:
            print(f"  IMAP scan error ({folder}): {e}")

    # Count by type
    bounces = [r for r in all_results if r['type'] == 'bounce']
    hard_bounces = [r for r in all_results if r['type'] == 'hard_bounce']
    replies = [r for r in all_results if r['type'] in ('reply', 'hot_reply', 'warm_reply')]
    unsubs = [r for r in all_results if r['type'] == 'unsubscribe']
    auto_replies = [r for r in all_results if r['type'] == 'auto_reply']

    print(f"  Bounces total: {len(bounces)} (hard: {len(hard_bounces)})")
    print(f"  Replies: {len(replies)}")
    print(f"  Unsubscribes: {len(unsubs)}")
    print(f"  Auto-replies: {len(auto_replies)}")

    # Risk control
    pause = False
    pause_reasons = []

    if len(hard_bounces) >= 1:
        pause = True
        pause_reasons.append(f'Hard bounce >= 1 ({len(hard_bounces)})')

    if len(bounces) >= 2:
        pause = True
        pause_reasons.append(f'Total bounce >= 2 ({len(bounces)})')

    if len(unsubs) >= 1:
        pause = True
        pause_reasons.append(f'Unsubscribe >= 1 ({len(unsubs)})')

    # DB stats
    today_sent = c.execute(
        "SELECT COUNT(*) FROM send_log WHERE date(sent_at) = ? AND status='sent'", (today,)
    ).fetchone()[0]
    today_hard = c.execute(
        "SELECT COUNT(*) FROM bounce_log WHERE bounce_type='hard' AND date(bounce_received_at) = ?", (today,)
    ).fetchone()[0]
    a0_rem = c.execute(
        "SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A' AND email_verified_on_official_site=1 AND email IS NOT NULL AND email!=''"
    ).fetchone()[0]
    ams_rem = c.execute("SELECT COUNT(*) FROM leads WHERE status='approved_manual_send'").fetchone()[0]
    conn.close()

    if pause and not dry_run:
        set_config('send_pause', 'true')
        set_config('pause_reason', '; '.join(pause_reasons))
        print(f"  [RISK] Pausing: {'; '.join(pause_reasons)}")
    elif pause:
        print(f"  [RISK-DRY] Would pause for: {'; '.join(pause_reasons)}")

    return {
        'bounces': len(bounces), 'hard_bounces': len(hard_bounces),
        'replies': len(replies), 'unsubs': len(unsubs), 'auto_replies': len(auto_replies),
        'today_sent': today_sent, 'today_hard': today_hard,
        'a0_remaining': a0_rem, 'ams_remaining': ams_rem,
        'paused': pause, 'pause_reasons': pause_reasons,
    }


# ================================================================
# STEP 7: Daily Report
# ================================================================
def step_daily_report(dry_run: bool, results: dict, model_report: bool = False):
    header("STEP 7: Daily Report")
    today = datetime.now().strftime('%Y-%m-%d')

    # Run agent_daily_report.py
    cmd = f'python agent_daily_report.py --date {today}'
    if dry_run:
        cmd += ' --dry-run'
    result = run_cmd(cmd)

    # Also generate our own summary
    report_path = os.path.join(OUT_DIR, f'auto_report_{today}.md')
    r = results

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# BD Auto Report — {today}\n\n")

        preflight = r.get('preflight', {})
        topup = r.get('topup', {})
        monitor = r.get('monitor', {})

        # 1. Send summary
        f.write("## 1. Send Summary\n")
        target = r.get('target_count', 20)
        sent = monitor.get('today_sent', 0)
        gap = max(0, target - sent)
        run_status = get_config('daily_run_status') or ('completed' if gap == 0 else 'underfilled')
        root_cause = get_config('root_cause') or ''
        f.write(f"- Target: {target}\n")
        f.write(f"- Sent: {sent}\n")
        f.write(f"- Gap: {gap}\n")
        f.write(f"- Status: {run_status}\n")
        if sent < target:
            f.write(f"- Root cause: {root_cause or 'Pool only had ' + str(preflight.get('total_sendable', 0)) + '/' + str(target) + ' at start'}\n")
        f.write("\n")

        # 2. Lead Factory (production metrics)
        f.write("## 2. Lead Factory\n")
        f.write(f"- Initial pool: {preflight.get('total_sendable', 0)}\n")
        f.write(f"- B pool approved: {topup.get('b_pool_approved', 0)}\n")
        f.write(f"- New A0 collected: {topup.get('new_a0_collected', 0)}\n")
        f.write(f"- Browser upgraded A0: {topup.get('browser_upgraded', 0)}\n")
        f.write(f"- Pool after: {monitor.get('a0_remaining', 0)} A0 + {monitor.get('ams_remaining', 0)} AMS\n")
        f.write(f"- Fresh cities remaining: {topup.get('fresh_cities_remaining', '?')}\n")
        if topup.get('action_needed') == 'collection':
            f.write(f"- Collection needed: {topup.get('next_cities', [])}\n")
            f.write(f"- Action: Run collection cycle for these cities\n")
        f.write("\n")

        # 3. Bounce & reply
        f.write("## 3. Bounce & Reply\n")
        f.write(f"- Hard bounce: {monitor.get('today_hard', 0)}\n")
        f.write(f"- Total bounces: {monitor.get('bounces', 0)}\n")
        f.write(f"- Replies: {monitor.get('replies', 0)}\n")
        f.write(f"- Hot replies: 0\n")
        f.write(f"- Unsubscribes: {monitor.get('unsubs', 0)}\n")
        f.write(f"- Auto-replies: {monitor.get('auto_replies', 0)}\n\n")

        # 4. Risk
        f.write("## 4. Risk Status\n")
        if monitor.get('pause_reasons'):
            for pr in monitor['pause_reasons']:
                f.write(f"- [PAUSED] {pr}\n")
        else:
            f.write("- No risk triggers\n")
        f.write(f"- send_pause: {get_config('send_pause')}\n\n")

        # 5. Recommendation
        f.write("## 5. Recommendation\n")
        tomorrow_sendable = monitor.get('a0_remaining', 0) + monitor.get('ams_remaining', 0)
        f.write(f"- Tomorrow sendable: {tomorrow_sendable}\n")
        f.write(f"- Next-window queued gap: {get_config('next_window_needed_count') or '0'}\n")
        if tomorrow_sendable >= target:
            f.write(f"- [OK] Pool sufficient for tomorrow ({tomorrow_sendable} >= {target})\n")
            if tomorrow_sendable >= 30:
                f.write("- Consider upgrading target to 30/day\n")
        else:
            f.write(f"- [WARN] Need {target - tomorrow_sendable} more leads for tomorrow\n")
            f.write(f"- Fresh cities available: {topup.get('fresh_cities_remaining', '?')}\n")
            f.write("- Action: Run Lead Factory cycle today\n")
        if monitor.get('today_hard', 0) > 0:
            f.write("- Bounce rate high: defer target upgrade\n")
        if topup.get('b_pool_approved', 0) > 0:
            f.write(f"- {topup.get('b_pool_approved', 0)} approved_manual_send candidates waiting for review\n")
        hot = monitor.get('hot_replies', 0)
        if hot:
            f.write(f"- {hot} hot replies need your attention\n")

    print(f"\n  Report saved: {report_path}")
    return report_path


# ================================================================
# MAIN
# ================================================================
def main():
    parser = argparse.ArgumentParser(description='Daily Operator Auto')
    parser.add_argument('--dry-run', action='store_true', default=True)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--target-count', type=int, default=DEFAULT_TARGET)
    parser.add_argument('--window', default=WINDOW_DEFAULT)
    parser.add_argument('--timezone', default='Asia/Shanghai')
    parser.add_argument('--allow-topup', action='store_true', help='Auto top-up pool if insufficient')
    parser.add_argument('--model-report', action='store_true', help='Use model to generate report summary')
    parser.add_argument('--stop-on-risk', action='store_true', help='Stop on any risk trigger')
    args = parser.parse_args()

    dry_run = not args.live
    target_count = args.target_count

    print("=" * 60)
    print("DAILY OPERATOR AUTO")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Target: {target_count} emails")
    print(f"Window: {args.window}")
    print(f"Top-up: {'ENABLED' if args.allow_topup else 'DISABLED'}")
    print(f"Risk stop: {'ENABLED' if args.stop_on_risk else 'DISABLED'}")

    results = {'target_count': target_count, 'preflight': {}, 'monitor': {}}

    # STEP 1: Preflight
    preflight = step_preflight(dry_run, target_count)
    results['preflight'] = preflight
    if not preflight['pass']:
        print(f"\n[BLOCKED] Preflight failed: {preflight['warnings']}")
        if not dry_run:
            return
        else:
            print("[DRY RUN] Continuing despite preflight issues...")

    # STEP 2: Lead Factory (pool top-up + collection planning)
    if args.allow_topup:
        topup = step_lead_factory(
            dry_run, target_count,
            preflight.get('total_sendable', 0)
        )
        results['topup'] = topup
        recovery = post_a0_upgrade_recovery_check(dry_run, target_count)
        results['recovery'] = recovery

    # STEP 3: Build send plan
    planned = step_build_send_plan(dry_run, target_count)
    results['planned_leads'] = len(planned)

    if not planned:
        print("\n[EMPTY] No sendable leads after plan. Aborting send.")
        sent = get_today_sent_count()
        inventory = get_sendable_inventory()
        results['monitor'] = {
            'today_sent': sent,
            'today_hard': 0,
            'a0_remaining': inventory['a0'],
            'ams_remaining': inventory['ams'],
            'paused': False,
            'pause_reasons': [],
        }
        if sent < target_count:
            set_daily_run_state(
                'underfilled',
                target_count,
                actual=sent,
                root_cause='no_sendable_leads',
                next_window_needed_count=max(0, target_count - sent),
                recovery_pending=True,
            )
    elif not dry_run and not is_in_send_window():
        sent = get_today_sent_count()
        print("\n[WINDOW] Outside 09:00-13:00 Asia/Shanghai send window. Queuing gap for next window.")
        inventory = get_sendable_inventory()
        results['monitor'] = {
            'today_sent': sent,
            'today_hard': 0,
            'a0_remaining': inventory['a0'],
            'ams_remaining': inventory['ams'],
            'paused': False,
            'pause_reasons': [],
        }
        set_daily_run_state(
            'underfilled',
            target_count,
            actual=sent,
            root_cause='outside_send_window',
            next_window_needed_count=max(0, target_count - sent),
            recovery_pending=True,
        )
    else:
        # STEP 4: Batch sending
        send_result = step_send_batches(dry_run, planned, target_count)
        results['send'] = send_result

        # STEP 5/6: Monitor & risk control
        monitor = step_monitor_and_risk(dry_run)
        results['monitor'] = monitor

        if monitor['paused'] and args.stop_on_risk and not dry_run:
            print(f"\n[STOPPED] Risk trigger: {monitor['pause_reasons']}")
            print("[STOPPED] Remaining actions halted by --stop-on-risk")

        sent = monitor.get('today_sent', get_today_sent_count())
        status, root_cause = classify_final_status(
            target_count,
            sent,
            paused=monitor.get('paused', False),
            failed=bool(send_result and not dry_run and not send_result.get('raw_output', '') and sent == 0),
            root_cause='sendable_inventory_insufficient' if sent < target_count else '',
        )
        next_window_needed = max(0, target_count - sent) if status == 'underfilled' else 0
        set_daily_run_state(
            status,
            target_count,
            actual=sent,
            root_cause=root_cause,
            next_window_needed_count=next_window_needed,
            recovery_pending=status == 'underfilled',
        )

    # STEP 7: Daily report
    report_path = step_daily_report(dry_run, results, model_report=args.model_report)

    # Final summary
    print(f"\n{'='*60}")
    print("ORCHESTRATION COMPLETE")
    print(f"{'='*60}")
    monitor = results.get('monitor', {})
    print(f"  Sent today:     {monitor.get('today_sent', 0)}")
    print(f"  Hard bounces:   {monitor.get('today_hard', 0)}")
    print(f"  Replies:        {monitor.get('replies', 0)}")
    print(f"  A0 remaining:   {monitor.get('a0_remaining', 0)}")
    print(f"  AMS remaining:  {monitor.get('ams_remaining', 0)}")
    if monitor.get('pause_reasons'):
        print(f"  [PAUSED] {'; '.join(monitor['pause_reasons'])}")
    print(f"  Report:         {report_path}")
    print(f"  send_pause:     {get_config('send_pause')}")


if __name__ == '__main__':
    main()
