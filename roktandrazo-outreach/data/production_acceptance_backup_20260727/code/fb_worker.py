#!/usr/bin/env python3
"""
Facebook Enrichment Worker — processes fb_enrichment_queue.
Uses existing inventory_recovery_loop FB functions + Playwright.

Usage: python fb_worker.py --max-tasks 20 --max-runtime 60
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

DB_PATH = PROJECT_DIR / 'data' / 'bd_leads.db'

# Import FB functions from existing recovery loop
from inventory_recovery_loop import (
    read_fb_page, find_fb_link, extract_fb_links,
    safe_write_b1, safe_write_a0, select_batch,
    count_strict_a0, fetch_html,
    FBRateLimiter as FBLimiter,
)

try:
    from inventory_recovery_loop import FBRateLimiter
except ImportError:
    from facebook_enrichment.fb_rate_limiter import FBRateLimiter


BASE_DELAY = 10
PAGE_DELAY = 8
ABOUT_DELAY = 3
COOLDOWN_EVERY = 5
COOLDOWN_SECONDS = 40


def now_cst():
    return datetime.utcnow() + timedelta(hours=8)


def db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def update_fb_queue(conn, lead_id, **kwargs):
    allowed = {'fb_check_status', 'fb_match_score', 'fb_email', 'fb_evidence_url',
               'fb_evidence_snippet', 'fb_retry_count', 'fb_last_checked_at',
               'fb_exclusion_reason', 'facebook_url', 'facebook_source'}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    updates['updated_at'] = "datetime('now')"
    updates['fb_last_checked_at'] = "datetime('now')"
    updates['fb_retry_count'] = f"COALESCE(fb_retry_count,0)+1"
    set_clauses = []
    values = []
    for k, v in updates.items():
        set_clauses.append(f"{k} = ?")
        values.append(v)
    values.append(lead_id)
    conn.execute(f"UPDATE fb_enrichment_queue SET {', '.join(set_clauses)} WHERE lead_id = ?", values)


def match_score(lead, fb_data):
    """Score how well a Facebook page matches the lead."""
    score = 0.0
    signals = []
    name = (lead.get('store_name') or '').lower().strip()
    city = (lead.get('city') or '').lower().strip()
    state = (lead.get('state') or '').strip().upper()
    web = (lead.get('official_website') or '').lower().strip()

    fb_name = (fb_data.get('name') or '').lower().strip()
    fb_web = (fb_data.get('website') or '').lower().strip()
    fb_city = (fb_data.get('city') or '').lower().strip()
    fb_state = (fb_data.get('state') or '').strip().upper()
    fb_phone = (fb_data.get('phone') or '').strip()
    fb_addr = (fb_data.get('address') or '').strip()

    # Name match
    if fb_name and name:
        name_words = set(name.split())
        fb_words = set(fb_name.split())
        common = name_words & fb_words
        if common:
            score += 0.3 * len(common) / max(len(name_words), 1)
            signals.append(f'name_match:{",".join(common)}')

    # Website match
    if fb_web and web:
        from urllib.parse import urlparse
        web_dom = urlparse(web).netloc.replace('www.', '') if 'http' in web else web
        fb_dom = urlparse(fb_web).netloc.replace('www.', '') if 'http' in fb_web else fb_web
        if web_dom and fb_dom and (web_dom in fb_dom or fb_dom in web_dom):
            score += 0.3
            signals.append('website_match')

    # City match
    if fb_city and city and city in fb_city:
        score += 0.15
        signals.append('city_match')

    # State match
    if fb_state and state and fb_state == state:
        score += 0.1
        signals.append('state_match')

    # Phone match (just check presence for now)
    if fb_phone:
        score += 0.1
        signals.append('phone_present')

    # Address match
    if fb_addr and city and city in fb_addr.lower():
        score += 0.05
        signals.append('address_partial_match')

    return min(score, 1.0), signals


def process_one_task(conn, page, task, limiter):
    """Process a single FB enrichment task. Returns result dict."""
    lead_id = task['lead_id']
    fb_url = (task.get('facebook_url') or '').strip()
    lead = dict(task)
    result = {'lead_id': lead_id, 'fb_check_status': 'pending'}

    # If no FB URL yet, try to find one from website
    if not fb_url:
        web = lead.get('official_website', '')
        if web:
            fb_url = find_fb_link(web)
            if fb_url:
                result['facebook_url'] = fb_url
                result['facebook_source'] = 'official_website_link'

    # Still no FB URL — try search
    if not fb_url:
        result['fb_check_status'] = 'no_facebook_link'
        result['fb_exclusion_reason'] = 'No Facebook link found on website or via search'
        return result

    # Read FB page
    if limiter.should_stop():
        result['fb_check_status'] = 'blocked'
        result['fb_exclusion_reason'] = f'Rate limiter blocked: {limiter.block_reason}'
        return result

    print(f"  Reading: {fb_url}")
    fb_data = read_fb_page(page, fb_url, limiter)
    result['fb_data'] = fb_data

    if fb_data.get('error'):
        error = fb_data['error']
        if 'login' in error or 'captcha' in error:
            result['fb_check_status'] = 'blocked'
            result['fb_exclusion_reason'] = f'FB blocked: {error}'
        else:
            result['fb_check_status'] = 'failed'
            result['fb_exclusion_reason'] = error
        return result

    # Check if page loaded
    if not fb_data.get('name') and not fb_data.get('email'):
        result['fb_check_status'] = 'failed'
        result['fb_exclusion_reason'] = 'FB page returned empty'
        return result

    # Match scoring
    score, signals = match_score(lead, fb_data)
    result['fb_match_score'] = score
    result['fb_match_signals'] = signals

    fb_email = fb_data.get('email', '').strip()

    if score < 0.4:
        result['fb_check_status'] = 'mismatch'
        return result

    # Check for public email
    if fb_email and '@' in fb_email:
        result['fb_email'] = fb_email
        result['fb_evidence_url'] = fb_data.get('about_url', '') or fb_url
        result['fb_evidence_snippet'] = f"Facebook About/Contact → {fb_email}"
        result['fb_phone'] = fb_data.get('phone', '')
        result['fb_address'] = fb_data.get('address', '')
        result['fb_website'] = fb_data.get('website', '')

        # Check if website also has the same email (→ can become A0)
        web = lead.get('official_website', '')
        has_web_email = False
        if web:
            try:
                html = fetch_html(web)
                if html:
                    emails_found = [e for e in re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)]
                    for e in emails_found:
                        if e.lower() == fb_email.lower():
                            has_web_email = True
                            result['fb_evidence_snippet'] += f" | Website also shows: {e}"
                            break
            except Exception:
                pass

        if has_web_email:
            result['fb_check_status'] = 'email_found'
            result['classification'] = 'strict_a0_candidate'
        else:
            result['fb_check_status'] = 'email_found'
            result['classification'] = 'b1_social_verified'
    else:
        # Check if there's Messenger/contact
        if fb_data.get('about'):
            result['fb_check_status'] = 'social_contact_only'
        else:
            result['fb_check_status'] = 'no_public_email'

    return result


def write_result(conn, result):
    """Write enrichment result to DB."""
    lead_id = result['lead_id']
    status = result.get('fb_check_status', 'failed')
    classification = result.get('classification', '')

    # Update FB queue
    update_fb_queue(conn, lead_id,
                    fb_check_status=status,
                    fb_match_score=result.get('fb_match_score', 0),
                    fb_email=result.get('fb_email', ''),
                    fb_evidence_url=result.get('fb_evidence_url', ''),
                    fb_evidence_snippet=(result.get('fb_evidence_snippet', '') or '')[:500],
                    fb_exclusion_reason=(result.get('fb_exclusion_reason', '') or '')[:300],
                    facebook_url=result.get('facebook_url', ''))

    # Update lead based on classification
    now = now_cst().isoformat()
    if classification == 'strict_a0_candidate':
        # Website also has the email → can be strict A0
        conn.execute("""
            UPDATE leads SET email = ?, email_source_type = 'official_page_visible',
            email_verified_on_official_site = 1, evidence_url = ?,
            confidence_score = 'A', review_status = 'resolved',
            review_reason_code = NULL, review_reason_detail = NULL,
            review_updated_at = ?, last_checked_at = ?
            WHERE id = ?
        """, (result.get('fb_email', ''), result.get('fb_evidence_url', ''),
              now, now, lead_id))
    elif classification == 'b1_social_verified':
        # FB-only email → B1, manual send candidate
        fb_email = result.get('fb_email', '')
        conn.execute("""
            UPDATE leads SET email = ?, email_source_type = 'social_media_verified',
            email_verified_on_official_site = 0, evidence_url = ?,
            review_reason_code = 'MANUAL_SEND_CANDIDATE',
            review_reason_detail = 'Email found on Facebook — requires manual approval',
            review_status = 'pending', review_updated_at = ?, last_checked_at = ?
            WHERE id = ?
        """, (fb_email, result.get('fb_evidence_url', ''), now, now, lead_id))
    elif status in ('failed', 'blocked'):
        pass  # Don't change lead state
    elif status in ('no_public_email', 'social_contact_only'):
        conn.execute("""
            UPDATE leads SET review_status = 'pending',
            review_reason_code = 'CONTACT_FORM_ONLY',
            review_reason_detail = 'FB check completed: ' || ?,
            review_updated_at = ? WHERE id = ?
        """, (result.get('fb_exclusion_reason', status), now, lead_id))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-tasks', type=int, default=20)
    parser.add_argument('--max-runtime', type=int, default=60)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    conn = db()
    c = conn.cursor()

    # Fetch pending tasks
    tasks = c.execute("""
        SELECT * FROM fb_enrichment_queue
        WHERE fb_check_status = 'pending'
        ORDER BY facebook_url IS NOT NULL DESC, created_at ASC
        LIMIT ?
    """, (args.max_tasks,)).fetchall()

    total = len(tasks)
    print(f"FB Worker: {total} pending tasks (max {args.max_tasks})")
    if total == 0:
        conn.close()
        return

    # Start Playwright browser
    from playwright.sync_api import sync_playwright
    profile_dir = os.environ.get('FB_PROFILE_DIR', 'D:/BD_BROWSER_PROFILES/facebook_business_enrichment')

    limiter = FBLimiter()

    print("Starting browser...")
    results = {'total': total, 'matched': 0, 'email_found': 0, 'b1_social': 0,
               'strict_a0': 0, 'social_only': 0, 'no_public_email': 0,
               'no_fb_link': 0, 'mismatch': 0, 'blocked': 0, 'failed': 0}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=False,
                args=['--disable-blink-features=AutomationControlled'],
            )
            page = browser.new_page()
            page.set_default_timeout(30000)

            # Check login
            page.goto('https://www.facebook.com/', wait_until='domcontentloaded', timeout=15000)
            time.sleep(3)
            if 'login' in page.url.lower() or 'checkpoint' in page.url.lower():
                print("⚠ FB not logged in — worker will stop")
                for task in tasks:
                    update_fb_queue(conn, task['lead_id'], fb_check_status='blocked',
                                    fb_exclusion_reason='facebook_not_logged_in')
                conn.commit()
                browser.close()
                return

            start_time = time.time()
            count = 0

            for i, task in enumerate(tasks):
                if limiter.should_stop():
                    print(f"  Stopped by rate limiter")
                    for remaining in tasks[i:]:
                        update_fb_queue(conn, remaining['lead_id'], fb_check_status='blocked',
                                        fb_exclusion_reason=limiter.block_reason)
                    break

                elapsed = (time.time() - start_time) / 60
                if elapsed > args.max_runtime:
                    print(f"  Runtime limit reached ({elapsed:.0f}m)")
                    break

                lead_id = task['lead_id']
                name = task['store_name'] or f'#{lead_id}'
                print(f"\n[{i+1}/{total}] {name}")

                # Delay before page
                time.sleep(PAGE_DELAY + (i % 3) * 2)

                result = process_one_task(conn, page, dict(task), limiter)
                write_result(conn, result)
                conn.commit()

                status = result.get('fb_check_status', '?')
                print(f"  → {status}")
                results[status] = results.get(status, 0) + 1

                if result.get('fb_email'):
                    results['email_found'] += 1
                if result.get('classification') == 'b1_social_verified':
                    results['b1_social'] += 1
                if result.get('classification') == 'strict_a0_candidate':
                    results['strict_a0'] += 1

                count += 1
                # Cooldown
                if count % COOLDOWN_EVERY == 0:
                    print(f"  Cooling down {COOLDOWN_SECONDS}s...")
                    time.sleep(COOLDOWN_SECONDS)

                limiter.after_page(result.get('facebook_url', ''))

            browser.close()
    except Exception as e:
        print(f"Browser error: {e}")
        import traceback
        traceback.print_exc()
        # Mark remaining as failed
        for task in tasks:
            if task['id'] not in results:
                update_fb_queue(conn, task['lead_id'], fb_check_status='failed',
                                fb_exclusion_reason=str(e)[:200])

    conn.commit()
    conn.close()

    # Summary
    print(f"\n{'='*50}")
    print("FB Worker complete")
    for k, v in sorted(results.items()):
        print(f"  {k}: {v}")


if __name__ == '__main__':
    main()
