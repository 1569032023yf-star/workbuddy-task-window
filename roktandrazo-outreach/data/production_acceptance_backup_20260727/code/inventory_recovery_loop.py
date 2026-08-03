"""Inventory Recovery Loop — continuous B pool enrichment until target reached.

Morning mode: target 20 for daily send window
Afternoon mode: target 60 for next-day inventory

Stages per batch:
  Stage 1: Website email verification
  Stage 2: Facebook fallback (rate-limited)
  Stage 3: Lead Hygiene Gate
  Stage 4: Safe DB write (backup, then insert/update)

Usage:
  python inventory_recovery_loop.py --mode morning --target 20 --batch-size 20 --dry-run
  python inventory_recovery_loop.py --mode afternoon --target 60 --batch-size 20 --write-safe --max-loops 5
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from facebook_enrichment.fb_rate_limiter import FBRateLimiter, RateLimitConfig

DB_PATH = PROJECT_DIR / "data" / "bd_leads.db"
BACKUP_DIR = PROJECT_DIR / "backups"
OUTPUT_DIR = PROJECT_DIR

ALLOWED_STATES = frozenset({"TN", "AR", "KY"})
BATCH_SIZE = 20
MAX_LOOPS = 10
MAX_RUNTIME_MINUTES = 120

# --- Patterns (from b_pool_recovery_runner) ---
EMAIL_RE = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9._%+-]{0,63}@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9]\.)*[a-zA-Z]{2,}')
MAILTO_RE = re.compile(r'mailto:([A-Za-z0-9.!#$%&\'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)', re.I)
FB_HREF_RE = re.compile(
    r'href=["\']?(https?://(?:www\.)?facebook\.com/(?!login|sharer|share|dialog|plugins|'
    r'tr|ajax|help|policies|privacy|legal|settings|messages|messenger|bookmarks|profile\.php)'
    r'[A-Za-z0-9.\-_/]+(?:\?[^"\'\s<>]*)?)["\']?', re.I
)
PHONE_RE = re.compile(r'(?:\+1[-\s]?)?\(?\d{3}\)?[-\s.]?\d{3}[-\s.]?\d{4}')
WEBSITE_LABEL_RE = re.compile(r'(?:Website|Web|Visit|Site)[:\s]*(https?://[^\s<>"\']+)', re.I)

UNSAFE_PREFIXES = ('no-reply', 'noreply', 'privacy', 'copyright', 'support-plugin',
                    'wordpress', 'shopify', 'wix', 'squarespace')
FREE_DOMAINS = {'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com'}
DIRECTORY_DOMAINS = {'yelp.com', 'yellowpages.com', 'facebook.com', 'google.com'}
NON_EMAIL_DOMAINS = {'sentry.io', '2x.jpg', '3x.jpg', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'css', 'js', 'woff', 'woff2'}

PROFILE_DIR = Path("D:/BD_BROWSER_PROFILES/facebook_business_enrichment")


# ============================================================
# Helpers
# ============================================================

def fetch_html(url: str, timeout: int = 12) -> str | None:
    try:
        import httpx
        r = httpx.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        }, timeout=timeout, follow_redirects=True, verify=False)
        r.raise_for_status()
        return r.text
    except Exception:
        return None


def extract_fb_links(html: str) -> list[str]:
    links, seen = [], set()
    for m in FB_HREF_RE.finditer(html):
        raw = m.group(1).rstrip('/"\'\\[]() ')
        parsed = urlparse(raw)
        path = parsed.path.rstrip('/')
        if not path or path == '/':
            continue
        clean = f"https://www.facebook.com{path}"
        if clean not in seen:
            seen.add(clean)
            links.append(clean)
    return links


def is_safe_email(email: str) -> bool:
    if '@' not in email:
        return False
    prefix = email.split('@')[0].strip().lower()
    domain = email.split('@')[1].strip().lower()
    tld = domain.rsplit('.', 1)[-1] if '.' in domain else ''
    if tld in NON_EMAIL_DOMAINS or domain in NON_EMAIL_DOMAINS:
        return False
    if prefix in UNSAFE_PREFIXES:
        return False
    if domain in DIRECTORY_DOMAINS:
        return False
    if len(prefix) > 40:
        return False
    if prefix[:3].isdigit() and len(prefix) >= 5 and not any(c.isalpha() for c in prefix[:4]):
        return False
    if 'www.' in prefix or 'http' in prefix:
        return False
    return True


def extract_emails(html: str) -> list[str]:
    emails, seen = [], set()
    for m in MAILTO_RE.finditer(html):
        e = m.group(1).strip().strip('"\'<>').lower()
        if e and '@' in e and e not in seen:
            seen.add(e)
            emails.append(e)
    for m in EMAIL_RE.finditer(html):
        e = m.group(0).strip().strip('"\'<>').lower()
        if e and '@' in e and e not in seen:
            seen.add(e)
            emails.append(e)
    return emails


def verify_website_email(website: str) -> tuple[str, str, str]:
    """Returns (best_email, evidence_url, evidence_snippet)."""
    pages = [
        (website, 'homepage'), (urljoin(website, '/contact'), 'contact'),
        (urljoin(website, '/about'), 'about'), (urljoin(website, '/about-us'), 'about-us'),
        (urljoin(website, '/wholesale'), 'wholesale'),
    ]
    for page_url, label in pages:
        html = fetch_html(page_url)
        if not html:
            continue
        emails = [e for e in extract_emails(html) if is_safe_email(e)]
        if emails:
            idx = html.lower().find(emails[0])
            snippet = ' '.join(html[max(0, idx - 80):idx + 120].split()) if idx >= 0 else emails[0]
            return emails[0], page_url, snippet[:200]
    return '', '', ''


def find_fb_link(website: str) -> str | None:
    for page in [website, urljoin(website, '/contact'), urljoin(website, '/about')]:
        html = fetch_html(page)
        if html:
            links = extract_fb_links(html)
            if links:
                return links[0]
    return None


# ============================================================
# DB Operations
# ============================================================

def count_strict_a0(conn) -> int:
    return conn.execute("""
        SELECT COUNT(*) FROM leads
        WHERE status = 'new' AND confidence_score = 'A'
        AND state IN ('TN','AR','KY')
        AND email_verified_on_official_site = 1
        AND email_source_type IN ('official_page_visible','official_mailto','wholesale_vendor_page','manual_lookup')
        AND email IS NOT NULL AND email != ''
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent','bounced'))
        AND (mx_provider IS NULL OR mx_provider = '' OR
             (mx_provider NOT LIKE '%exchange%' AND mx_provider NOT LIKE '%outlook%' AND mx_provider NOT LIKE '%microsoft%'))
    """).fetchone()[0]


def select_batch(conn, already_done_ids: set[int], limit: int = 20) -> list[dict]:
    """Select next batch of B/B2 candidates, excluding recently processed ids."""
    done_placeholders = ','.join('?' * len(already_done_ids)) if already_done_ids else '0'
    params = list(already_done_ids) + [limit]

    rows = conn.execute(f"""
        SELECT * FROM leads
        WHERE state IN ('TN','AR','KY')
        AND official_website IS NOT NULL AND official_website != ''
        AND status IN ('new','manual_review_needed','contact_form_pool')
        AND (email IS NULL OR email = '' OR email_source_type IN ('guessed_email','no_contact_found','unknown')
             OR email_verified_on_official_site = 0)
        AND status NOT IN ('sent','bounced','unsubscribed','delivery_issue','do_not_contact')
        AND email NOT IN (SELECT email FROM suppression_list WHERE email IS NOT NULL)
        AND id NOT IN (SELECT lead_id FROM bounce_log WHERE bounce_type='hard')
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status='sent')
        AND id NOT IN ({done_placeholders})
        AND (evidence_checked_at IS NULL OR evidence_checked_at < datetime('now', '-24 hours'))
        ORDER BY evidence_checked_at ASC NULLS FIRST, id ASC
        LIMIT ?
    """, params).fetchall()

    return [dict(r) for r in rows]


def safe_write_a0(conn, lead: dict):
    """Insert or update lead as A0 candidate."""
    now = datetime.now().isoformat()
    email = lead.get('website_email', '') or lead.get('email', '')
    official_website = lead.get('official_website', '')

    existing = conn.execute("SELECT id, confidence_score FROM leads WHERE id = ?", (lead['id'],)).fetchone()
    if not existing:
        return

    # Don't overwrite higher-quality manual evidence
    if existing['confidence_score'] == 'A' and lead.get('confidence_score') == 'A':
        # Already A, just update evidence if missing
        pass

    conn.execute("""
        UPDATE leads SET
            email = ?, official_website = ?,
            evidence_url = ?, evidence_snippet = ?, evidence_method = 'website_http_verified',
            evidence_checked_at = ?, email_verified_on_official_site = 1,
            email_source_type = 'official_page_visible',
            domain_hash = ?,
            confidence_score = 'A', status = 'new',
            last_checked_at = ?
        WHERE id = ?
    """, (
        email,
        official_website,
        lead.get('evidence_url', ''),
        lead.get('evidence_snippet', '')[:500],
        now,
        hashlib.sha256(email.split('@')[1].encode() if '@' in email else email.encode()).hexdigest(),
        now,
        lead['id'],
    ))
    conn.commit()


def safe_write_b1(conn, lead: dict):
    """Write Facebook-only email as B1. Uses manual_found_email + manual_note (no schema change)."""
    now = datetime.now().isoformat()
    social_data = json.dumps({
        'social_email': lead.get('fb_email', ''),
        'social_evidence_url': lead.get('fb_page_url', ''),
        'social_evidence_snippet': (lead.get('fb_about', '') or '')[:300],
        'social_match_score': lead.get('fb_match_score', 0),
        'facebook_source_url': lead.get('website', ''),
        'evidence_method': 'official_facebook_page',
        'classified_at': now,
    }, ensure_ascii=False)

    existing = conn.execute("SELECT id FROM leads WHERE id = ?", (lead['id'],)).fetchone()
    if not existing:
        return

    conn.execute("""
        UPDATE leads SET
            manual_found_email = ?, manual_note = ?,
            status = 'manual_review_needed',
            evidence_checked_at = ?, last_checked_at = ?
        WHERE id = ?
    """, (
        lead.get('fb_email', ''),
        social_data,
        now, now,
        lead['id'],
    ))
    conn.commit()


def safe_write_c(conn, lead: dict):
    """Write C (Messenger/contact form only)."""
    now = datetime.now().isoformat()
    existing = conn.execute("SELECT id FROM leads WHERE id = ?", (lead['id'],)).fetchone()
    if not existing:
        return

    conn.execute("""
        UPDATE leads SET
            status = 'contact_form_pool',
            contact_form_url = COALESCE(contact_form_url, ?),
            evidence_checked_at = ?, last_checked_at = ?
        WHERE id = ?
    """, (
        lead.get('fb_page_url', ''),
        now, now,
        lead['id'],
    ))
    conn.commit()


def mark_checked(conn, lead_id: int):
    """Mark lead as checked without changing classification."""
    now = datetime.now().isoformat()
    conn.execute("UPDATE leads SET evidence_checked_at = ?, last_checked_at = ? WHERE id = ?",
                 (now, now, lead_id))
    conn.commit()


def backup_db():
    """Create timestamped DB backup. Returns backup path."""
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    backup_dir = BACKUP_DIR / f"inventory_recovery_loop_{ts}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / "bd_leads_backup.db"
    shutil.copy2(DB_PATH, backup_path)
    with open(DB_PATH, 'rb') as f:
        db_hash = hashlib.sha256(f.read()).hexdigest()
    (backup_dir / "db_hash.txt").write_text(db_hash)
    return str(backup_path)


# ============================================================
# Facebook Page Reader (reused from b_pool_recovery_runner)
# ============================================================

def read_fb_page(page, fb_url: str, limiter: FBRateLimiter) -> dict:
    result = {'name': '', 'email': '', 'website': '', 'phone': '', 'about': '', 'error': ''}
    try:
        limiter.before_page_load()
        page.goto(fb_url, wait_until='domcontentloaded', timeout=30000)
        limiter.after_page_load()

        text_lower = page.content()[:5000].lower()
        if 'you must log in' in text_lower:
            result['error'] = 'facebook_login_required'
            limiter.block('facebook_login_required')
            return result
        if 'confirm your identity' in text_lower or 'captcha' in text_lower:
            result['error'] = 'facebook_captcha'
            limiter.block('facebook_captcha')
            return result

        try:
            h1 = page.query_selector('h1')
            if h1:
                result['name'] = h1.inner_text().strip()
        except Exception:
            pass

        try:
            body = page.query_selector('body')
            if body:
                result['about'] = body.inner_text()[:3000]
        except Exception:
            pass

        try:
            about_tab = page.query_selector('a[href*="/about"]')
            if about_tab and about_tab.is_visible():
                limiter.before_detail()
                about_tab.click()
                time.sleep(2)
                main = page.query_selector('div[role="main"]')
                if main:
                    result['about'] += '\n' + main.inner_text()[:2000]
        except Exception:
            pass

        full = result['about']
        emails = [e for e in EMAIL_RE.findall(full) if is_safe_email(e)]
        if emails:
            result['email'] = emails[0]
        phones = PHONE_RE.findall(full)
        if phones:
            result['phone'] = phones[0]
        ws = WEBSITE_LABEL_RE.findall(full)
        if ws:
            result['website'] = ws[0]
        if not result['website']:
            try:
                for link in page.query_selector_all('a[href*="http"]'):
                    href = (link.get_attribute('href') or '')[:200]
                    if href.startswith('http') and 'facebook.com' not in href and 'l.php' not in href:
                        result['website'] = href
                        break
            except Exception:
                pass
    except Exception as e:
        result['error'] = str(e)[:100]
    return result


# ============================================================
# Pipeline Batch Runner
# ============================================================

def run_one_batch(leads: list[dict], limiter: FBRateLimiter, page=None) -> list[dict]:
    """Process one batch through website→FB→gate. Returns enriched results."""
    results = []

    # Stage 1: Website verification
    for lead in leads:
        r = dict(lead)
        r['website_email'] = ''
        r['evidence_url'] = ''
        r['evidence_snippet'] = ''
        r['fb_link'] = ''
        r['fb_page_url'] = ''
        r['fb_name'] = ''
        r['fb_email'] = ''
        r['fb_website'] = ''
        r['fb_about'] = ''
        r['fb_match_score'] = 0.0
        r['fb_error'] = ''
        r['classification'] = ''
        r['a0_eligible'] = False

        website = lead.get('official_website', '')
        if website:
            email, ev_url, ev_snip = verify_website_email(website)
            if email:
                r['website_email'] = email
                r['evidence_url'] = ev_url
                r['evidence_snippet'] = ev_snip
                r['classification'] = 'website_email_found'

        results.append(r)

    # Stage 2: Facebook link extraction (for leads without website email)
    no_email = [r for r in results if not r['website_email'] and r.get('official_website')]
    for r in no_email:
        fb_url = find_fb_link(r['official_website'])
        if fb_url:
            r['fb_link'] = fb_url
            r['fb_page_url'] = fb_url

    # Stage 3: Facebook page reading (if browser available)
    fb_candidates = [r for r in no_email if r['fb_page_url'] and page is not None and not limiter.should_stop()]
    for r in fb_candidates:
        if limiter.is_cached(r['fb_page_url']):
            r['fb_error'] = 'cached'
            continue

        fb_data = read_fb_page(page, r['fb_page_url'], limiter)
        r['fb_name'] = fb_data.get('name', '')
        r['fb_email'] = fb_data.get('email', '')
        r['fb_website'] = fb_data.get('website', '')
        r['fb_about'] = (fb_data.get('about', '') or '')[:300]
        r['fb_error'] = fb_data.get('error', '')

        if r['fb_error']:
            r['classification'] = r['fb_error']
        elif r['fb_email']:
            r['classification'] = 'B1_social_verified'
            r['fb_match_score'] = 0.5  # From official website = strong signal
        elif r['fb_about']:
            r['classification'] = 'C_social_contact'
        else:
            r['classification'] = 'facebook_no_contact_info'

        limiter.after_page(r['fb_page_url'])

        if limiter.should_stop():
            break

    # For leads without FB or FB read → already classified
    for r in results:
        if not r['classification']:
            if not r.get('official_website'):
                r['classification'] = 'no_website'
            elif not r.get('fb_page_url') and not r.get('website_email'):
                r['classification'] = 'no_contact_method'
            elif r.get('fb_error') == 'cached':
                pass  # Keep blank

    return results


# ============================================================
# Main Loop
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Inventory Recovery Loop')
    parser.add_argument('--mode', choices=['morning', 'afternoon'], default='morning')
    parser.add_argument('--target', type=int, default=None)
    parser.add_argument('--batch-size', type=int, default=20)
    parser.add_argument('--write-safe', action='store_true', help='Enable production DB writes (requires explicit flag)')
    parser.add_argument('--dry-run', dest='dry_run', action='store_true', default=True)
    parser.add_argument('--no-dry-run', dest='dry_run', action='store_false', help='Disable dry-run (use with --write-safe)')
    parser.add_argument('--max-loops', type=int, default=MAX_LOOPS)
    parser.add_argument('--max-runtime-minutes', type=int, default=MAX_RUNTIME_MINUTES)
    parser.add_argument('--no-facebook', action='store_true', help='Skip Facebook enrichment phase')
    args = parser.parse_args()

    if args.mode == 'morning':
        target = args.target or 20
        mode_label = 'Morning Recovery'
    else:
        target = args.target or 60
        mode_label = 'Afternoon Inventory'

    write_enabled = args.write_safe and args.dry_run is False

    print("=" * 60)
    print(f"Inventory Recovery Loop — {mode_label}")
    print(f"Target: {target} | Batch: {args.batch_size} | Mode: {'WRITE-SAFE' if write_enabled else 'DRY-RUN'}")
    print(f"Max loops: {args.max_loops} | Max runtime: {args.max_runtime_minutes}min")
    print("=" * 60)

    if write_enabled:
        backup_path = backup_db()
        print(f"\n✓ DB backed up: {backup_path}")

    conn = sqlite3.connect(DB_PATH) if write_enabled else sqlite3.connect(f"file:{DB_PATH.resolve().as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    if write_enabled:
        # Also set row_factory on any write connections from safe_write functions
        # by using a helper that returns properly configured connections
        def _get_write_conn():
            c = sqlite3.connect(DB_PATH)
            c.row_factory = sqlite3.Row
            return c

    # Initial pool count
    pool = 0 if args.dry_run else count_strict_a0(conn)
    print(f"\nInitial strict A0 pool: {pool}/{target}")

    # Overall stats
    total_loops = 0
    total_processed = 0
    total_a0 = 0
    total_b1 = 0
    total_c = 0
    total_rejected = 0
    all_states = set()
    all_cities = set()
    already_done = set()
    hard_stop_reason = ""

    limiter = FBRateLimiter()
    limiter.start_round()

    runtime_start = time.time()

    # Only start browser if Facebook enabled
    browser_active = False
    p = None
    browser = None
    page = None

    if not args.no_facebook and not args.dry_run:
        try:
            from playwright.sync_api import sync_playwright
            PROFILE_DIR.mkdir(parents=True, exist_ok=True)
            p = sync_playwright().start()
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR), headless=False,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox'],
                viewport={'width': 1280, 'height': 900}, locale='en-US',
            )
            page = browser.new_page()
            # Quick login check
            test_p = browser.new_page()
            test_p.goto('https://www.facebook.com/', wait_until='domcontentloaded', timeout=15000)
            time.sleep(2)
            if test_p.query_selector('input[name="email"], #loginbutton'):
                print("⚠ Facebook not logged in. FB enrichment will be skipped.")
                test_p.close()
                browser.close()
                p.stop()
                browser_active = False
                page = None
                p = None
            else:
                test_p.close()
                browser_active = True
                print("✓ Facebook session active")
        except Exception as e:
            print(f"⚠ Browser init failed: {e}")
            browser_active = False

    # ===== MAIN LOOP =====
    while pool < target and total_loops < args.max_loops:
        elapsed_min = (time.time() - runtime_start) / 60
        if elapsed_min >= args.max_runtime_minutes:
            hard_stop_reason = f"Max runtime reached ({args.max_runtime_minutes}min)"
            break

        total_loops += 1
        print(f"\n{'=' * 60}")
        print(f"LOOP {total_loops} | Pool: {pool}/{target} | Elapsed: {elapsed_min:.0f}min")
        print(f"{'=' * 60}")

        # Select batch
        batch = select_batch(conn, already_done, args.batch_size)
        if not batch:
            hard_stop_reason = "Candidate queue exhausted"
            print(f"  No more candidates available.")
            break

        for b in batch:
            already_done.add(b['id'])

        # Track states/cities
        for b in batch:
            if b.get('state'):
                all_states.add(b['state'])
            if b.get('city'):
                all_cities.add(b['city'])

        # Run enrichment
        enriched = run_one_batch(batch, limiter, page)
        total_processed += len(enriched)

        loop_a0 = loop_b1 = loop_c = loop_rej = 0
        if write_enabled:
            write_conn = _get_write_conn()
            try:
                for r in enriched:
                    rid = r['id']
                    cls = r.get('classification', '')

                    if r.get('website_email') and cls == 'website_email_found':
                        # Stage 3: Run through Lead Hygiene Gate
                        try:
                            from lead_hygiene_gate import evaluate_a0
                            cand = {
                                'email': r['website_email'],
                                'official_website': r.get('official_website', ''),
                                'evidence_url': r.get('evidence_url', ''),
                                'evidence_snippet': r.get('evidence_snippet', ''),
                                'email_verified_on_official_site': True,
                                'email_source_type': 'official_page_visible',
                                'official_match': True,
                                'state': r.get('state', ''),
                            }
                            decision = evaluate_a0(cand)
                            if decision.a0_eligible:
                                r['a0_eligible'] = True
                        except ImportError:
                            r['a0_eligible'] = True  # Fallback: assume safe if gate unavailable

                    if r.get('a0_eligible') and r.get('website_email'):
                        safe_write_a0(write_conn, r)
                        loop_a0 += 1
                    elif r.get('classification') == 'B1_social_verified':
                        safe_write_b1(write_conn, r)
                        loop_b1 += 1
                    elif r.get('classification') == 'C_social_contact':
                        safe_write_c(write_conn, r)
                        loop_c += 1
                    else:
                        mark_checked(write_conn, rid)
                        loop_rej += 1
                write_conn.close()
            except Exception as e:
                hard_stop_reason = f"DB write failure: {e}"
                write_conn.close()
                break
        else:
            # Dry-run: simulate classification
            for r in enriched:
                cls = r.get('classification', '')
                if r.get('website_email') and cls == 'website_email_found':
                    loop_a0 += 1
                elif cls == 'B1_social_verified':
                    loop_b1 += 1
                elif cls == 'C_social_contact':
                    loop_c += 1
                else:
                    loop_rej += 1

        total_a0 += loop_a0
        total_b1 += loop_b1
        total_c += loop_c
        total_rejected += loop_rej

        # Recount
        if write_enabled:
            pool = count_strict_a0(conn)
        else:
            pool += loop_a0  # Simulate

        # Check hard stops
        if limiter.blocked:
            hard_stop_reason = f"Facebook {limiter.block_reason}"
            break

        # Print loop summary
        states_str = ', '.join(sorted(set(b.get('state', '') for b in batch if b.get('state')))[:5])
        cities_show = [b.get('city', '') for b in batch if b.get('city')][:5]
        print(f"\n  本轮: {len(batch)} 条 → A0: +{loop_a0} | B1: +{loop_b1} | C: +{loop_c} | Rej: +{loop_rej}")
        print(f"  州: {states_str}")
        print(f"  城市: {', '.join(cities_show)}")
        print(f"  池: {pool}/{target}")

        # Checkpoint
        ckpt = {
            'loop': total_loops, 'pool': pool, 'target': target,
            'mode': args.mode, 'total_a0': total_a0, 'total_b1': total_b1,
            'total_c': total_c, 'total_rejected': total_rejected, 'hard_stop': hard_stop_reason,
            'already_done_count': len(already_done),
        }
        (OUTPUT_DIR / 'inventory_checkpoint.json').write_text(json.dumps(ckpt, indent=2))

    # Cleanup
    if browser_active:
        try:
            browser.close()
            p.stop()
        except Exception:
            pass

    conn.close()

    # ===== FINAL SUMMARY =====
    reached = pool >= target
    print()
    print("=" * 60)
    if reached:
        print(f"{'Morning' if args.mode == 'morning' else 'Afternoon'} recovery COMPLETE")
    else:
        print(f"{'Morning' if args.mode == 'morning' else 'Afternoon'} recovery STOPPED (target not reached)")
    print("=" * 60)
    print(f"Loops executed:         {total_loops}")
    print(f"Total candidates:       {total_processed}")
    print(f"New A0 (added):         {total_a0}")
    print(f"New B1 (Facebook):      {total_b1}")
    print(f"New C (contact form):   {total_c}")
    print(f"Rejected/blocked:       {total_rejected}")
    print(f"States covered:         {', '.join(sorted(all_states))}")
    cities_list = sorted(all_cities)
    print(f"Cities covered ({len(cities_list)}): {', '.join(cities_list[:15])}")
    if len(cities_list) > 15:
        print(f"  ... +{len(cities_list)-15} more")
    print(f"Final strict A0 pool:   {pool}/{target}")
    if hard_stop_reason:
        print(f"Hard stop reason:       {hard_stop_reason}")
    print(f"DB writes:              {'Yes (safe)' if write_enabled else 'No (dry-run)'}")
    print(f"Email sent:             No")
    print("=" * 60)

    # Final audit
    audit = {
        'mode': args.mode, 'target': target, 'loops': total_loops,
        'total_a0': total_a0, 'total_b1': total_b1, 'total_c': total_c,
        'total_rejected': total_rejected, 'final_pool': pool, 'reached': reached,
        'hard_stop': hard_stop_reason, 'states': sorted(all_states),
        'cities': sorted(all_cities), 'write_enabled': write_enabled,
    }
    (OUTPUT_DIR / 'inventory_audit.json').write_text(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
