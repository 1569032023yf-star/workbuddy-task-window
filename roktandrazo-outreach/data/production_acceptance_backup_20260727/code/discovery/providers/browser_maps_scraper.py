#!/usr/bin/env python3
"""
Browser-based Google Maps scraper for Roktandrazo lead discovery.
Uses Playwright to search Google Maps and extract business listings.

PREREQUISITES:
    pip install playwright
    playwright install chromium

USAGE (single query):
    python discovery/providers/browser_maps_scraper.py \
        --query "board game store Nashville TN" \
        --city Nashville --state TN \
        --max-results 20 \
        --output data/browser_maps_nashville_boardgame.json

OUTPUT: JSON file with PlaceSearchResult-compatible records.
NO API key required. Uses your existing Chrome/Chromium browser.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_DIR))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── CONFIG ──────────────────────────────────────────────
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# Google Maps search URL template
GMAPS_SEARCH_URL = "https://www.google.com/maps/search/{query}"

# How long to wait for results to load (seconds)
PAGE_LOAD_WAIT = 5
SCROLL_WAIT = 2
RESULT_CARD_WAIT = 3

# Maximum scroll attempts to load more results
MAX_SCROLLS = 10


def extract_place_data_from_card(card_element) -> dict | None:
    """Extract business info from a Google Maps result card element.

    In Google Maps, each result card contains:
    - Business name (in an aria-label or heading)
    - Address info
    - Phone (sometimes, in expanded view)
    - Website link
    - Rating/reviews count
    - Category/type
    - Status (open/closed)
    """
    try:
        # Get the full text content of the card
        card_text = card_element.inner_text() if hasattr(card_element, 'inner_text') else card_element.text_content()
        aria_label = card_element.get_attribute('aria-label') or ''

        # Extract name from aria-label (most reliable)
        name_match = re.match(r'^(.+?)(?:\n|,)', aria_label) if aria_label else None
        business_name = name_match.group(1).strip() if name_match else ''

        if not business_name:
            # Fallback: find first heading-like element
            for tag in ['h3', 'h2', 'h1', '[role="heading"]']:
                try:
                    el = card_element.query_selector(tag)
                    if el:
                        business_name = el.inner_text().strip()
                        break
                except Exception:
                    pass

        if not business_name:
            return None  # Can't identify the business

        # Extract address from aria-label or card text
        lines = card_text.split('\n')
        address_parts = []
        website = ''
        phone = ''

        for i, line in enumerate(lines):
            line_s = line.strip()
            if not line_s:
                continue

            # Skip name, rating, category-like lines
            if line_s == business_name:
                continue
            if re.match(r'^[\d.]+\(\d+[Kk]?\)', line_s):  # Rating
                continue
            if re.match(r'^(Open|Closed|Temporarily|Permanently)', line_s, re.IGNORECASE):
                continue

            # Website detection
            if re.match(r'^https?://', line_s) or re.search(r'\.[a-z]{2,}(?:/|$)', line_s):
                if 'google.com' not in line_s and 'maps.app' not in line_s:
                    candidate = line_s if line_s.startswith('http') else f'https://{line_s}'
                    candidate = candidate.split('?')[0].split('#')[0]
                    if not website:
                        website = candidate
                continue

            # Phone detection
            phone_match = re.search(r'(?:\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})', line_s)
            if phone_match:
                phone = phone_match.group(0)
                continue

            # Address-like (contains number + street indicators)
            if re.search(r'\d+.*(?:St|Street|Ave|Avenue|Blvd|Blvd\.|Dr|Drive|Rd|Road|Ln|Lane|Pk|Pike|Way|Ct|Court|Hwy|Hwy\.|Pkwy|Hwy\.|Parkway|Cir|Circle|Pl|Place)', line_s, re.IGNORECASE):
                address_parts.append(line_s)

        address = ', '.join(address_parts) if address_parts else ''

        # Try to extract more from aria-label
        if not address:
            addr_match = re.search(r'(?:·|,)\s*(\d+[^·,]+(?:Nashville|TN)[^·,]*)', aria_label)
            if addr_match:
                address = addr_match.group(1).strip()

        # Get Google Maps URL
        maps_url = ''
        try:
            links = card_element.query_selector_all('a')
            for link in links:
                href = link.get_attribute('href') or ''
                if 'maps/place' in href or 'maps.app.goo.gl' in href:
                    if href.startswith('/'):
                        maps_url = f'https://www.google.com{href}'
                    elif href.startswith('http'):
                        maps_url = href
                    break
        except Exception:
            pass

        # Try clicking / expanding the card to get more details
        try:
            card_element.click()
            time.sleep(0.5)
        except Exception:
            pass

        # Re-read after potential expand
        expanded_text = card_element.inner_text() if hasattr(card_element, 'inner_text') else card_text
        if not phone:
            phone_match2 = re.search(r'(?:\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})', expanded_text)
            if phone_match2:
                phone = phone_match2.group(0)

        return {
            'business_name': business_name.strip(),
            'formatted_address': address.strip(),
            'phone': phone.strip(),
            'website': website.strip(),
            'google_maps_url': maps_url,
            'raw_text': expanded_text[:500],
        }

    except Exception as e:
        print(f"      [WARN] Failed to extract card: {e}")
        return None


def scrape_google_maps(
    query: str,
    city: str = '',
    state: str = '',
    max_results: int = 20,
    headless: bool = True,
    output_file: str | None = None,
) -> dict:
    """Scrape Google Maps search results using Playwright.

    Returns a dict with ProviderPage-compatible structure.
    """
    from playwright.sync_api import sync_playwright

    results_data = []
    errors = []
    search_url = GMAPS_SEARCH_URL.format(query=query.replace(' ', '+'))

    print(f"\n{'='*60}")
    print(f"Google Maps Browser Scraper")
    print(f"  Query:   {query}")
    print(f"  City:    {city}")
    print(f"  State:   {state}")
    print(f"  Max:     {max_results}")
    print(f"  Headless:{headless}")
    print(f"  URL:     {search_url}")
    print(f"{'='*60}\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={'width': 1280, 'height': 900},
            locale='en-US',
            timezone_id='America/Chicago',
        )

        # Normal browser — no stealth, no anti-detection, no webdriver hiding
        page = context.new_page()

        try:
            print("[1/4] Navigating to Google Maps...")
            page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(PAGE_LOAD_WAIT)

            # Check for captcha / verification
            page_text = page.inner_text('body') if hasattr(page, 'inner_text') else page.content()
            if 'verify' in page_text.lower() or 'captcha' in page_text.lower() or 'robot' in page_text.lower():
                errors.append("CAPTCHA_OR_VERIFICATION_DETECTED")
                print("  ⚠️  CAPTCHA or verification detected!")

            # Check for "no results"
            if 'No results found' in page_text:
                print("  📭 No results found for this query.")
                return {
                    'provider': 'browser_maps',
                    'query': query,
                    'city': city,
                    'state': state,
                    'page_cursor': '',
                    'next_page_cursor': '',
                    'status': 'ok',
                    'error': '',
                    'results': [],
                    'request_count': 1,
                    'cost_units': 0,
                    'errors': errors,
                    'collected_at': utc_now(),
                }

            print("[2/4] Reading search results...")
            # Results are in a scrollable sidebar panel
            # Try multiple selectors for the results container
            result_selectors = [
                '[role="feed"] > div',
                '[role="feed"] div[role="article"]',
                'div[aria-label*="Results for"] div[role="article"]',
                '.m6QErb.DxyBCb.kA9KIf.dS8AEf[role="feed"] > div',
                'div[role="main"] div[role="article"]',
            ]

            seen_names = set()
            scroll_attempts = 0
            last_count = 0

            while len(results_data) < max_results and scroll_attempts < MAX_SCROLLS:
                # Try each selector
                cards = []
                for selector in result_selectors:
                    try:
                        cards = page.query_selector_all(selector)
                        if cards:
                            break
                    except Exception:
                        continue

                if not cards:
                    # Generic fallback: find all clickable result-like elements
                    try:
                        cards = page.query_selector_all('a[aria-label]')
                        cards = [c for c in cards if len(c.get_attribute('aria-label') or '') > 10]
                    except Exception:
                        pass

                print(f"  Found {len(cards)} result cards (scroll {scroll_attempts+1})")

                for card in cards:
                    if len(results_data) >= max_results:
                        break

                    data = extract_place_data_from_card(card)
                    if not data or not data['business_name']:
                        continue

                    name_key = data['business_name'].lower().strip()
                    if name_key in seen_names:
                        continue  # Skip duplicates in this scrape session
                    seen_names.add(name_key)

                    results_data.append(data)

                # Scroll to load more results
                if len(results_data) > last_count:
                    last_count = len(results_data)
                    scroll_attempts = 0  # Reset counter when we get new results

                if len(results_data) < max_results:
                    try:
                        # Scroll the results panel
                        scroll_panel_selectors = [
                            '[role="feed"]',
                            'div[role="main"] div:first-child',
                            '.m6QErb.DxyBCb.kA9KIf.dS8AEf',
                        ]
                        for sel in scroll_panel_selectors:
                            try:
                                panel = page.query_selector(sel)
                                if panel:
                                    panel.evaluate('el => el.scrollTop = el.scrollHeight')
                                    break
                            except Exception:
                                continue
                        time.sleep(SCROLL_WAIT)
                        scroll_attempts += 1
                    except Exception:
                        break
                else:
                    break

            print(f"\n[3/4] Extracted {len(results_data)} unique business results")

            # Enrich results with city/state from query if not detected
            enriched = []
            for i, r in enumerate(results_data):
                result_city = city
                result_state = state

                # Try to detect city/state from address
                addr = r.get('formatted_address', '')
                if addr:
                    # Nashville, TN detection
                    nash_match = re.search(r'(Nashville|Antioch|Donelson|Hermitage|Madison|Goodlettsville|Brentwood|Franklin|Hendersonville)', addr, re.IGNORECASE)
                    if nash_match:
                        result_city = nash_match.group(1)
                    tn_match = re.search(r'\bTN\b|\bTennessee\b', addr, re.IGNORECASE)
                    if tn_match:
                        result_state = 'TN'

                enriched.append({
                    'provider': 'browser_maps',
                    'provider_result_id': f"browser_maps_{query.replace(' ','_')}_{i}",
                    'place_id': f"gmaps_{r['business_name'].lower().replace(' ','_').replace('-','_')}",
                    'business_name': r['business_name'],
                    'formatted_address': r.get('formatted_address', ''),
                    'city': result_city,
                    'state': result_state,
                    'country': 'US',
                    'phone': r.get('phone', ''),
                    'website': r.get('website', ''),
                    'business_status': 'OPERATIONAL',
                    'primary_type': 'store',
                    'types': [],
                    'source_query': query,
                    'source_url': r.get('google_maps_url', search_url),
                    'raw_payload': {'raw_text': r.get('raw_text', '')},
                    'next_page_cursor': '',
                    'fetched_at': utc_now(),
                    'location_lat': None,
                    'location_lng': None,
                })

            print(f"[4/4] Saving {len(enriched)} results...")

        except Exception as e:
            errors.append(f"BROWSER_ERROR: {str(e)[:200]}")
            print(f"  ❌ Error: {e}")
            enriched = results_data  # Use whatever we got

        finally:
            context.close()
            browser.close()

    output = {
        'provider': 'browser_maps',
        'query': query,
        'city': city,
        'state': state,
        'page_cursor': '',
        'next_page_cursor': str(len(enriched)),
        'status': 'ok' if not errors else 'partial',
        'error': '; '.join(errors) if errors else '',
        'results': enriched,
        'request_count': 1,
        'cost_units': 0,
        'errors': errors,
        'collected_at': utc_now(),
    }

    if output_file:
        out_path = Path(output_file)
        if not out_path.is_absolute():
            out_path = PROJECT_DIR / output_file
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\n  ✅ Saved to: {out_path}")
        print(f"  Results: {len(enriched)} businesses")
        print(f"  Status: {output['status']}")
        if errors:
            print(f"  Errors: {errors}")
        return output

    return output


def main():
    parser = argparse.ArgumentParser(description='Browser-based Google Maps scraper')
    parser.add_argument('--query', required=True, help='Search query (e.g. "board game store Nashville TN")')
    parser.add_argument('--city', required=True, help='Target city')
    parser.add_argument('--state', required=True, help='Target state (2-letter code)')
    parser.add_argument('--max-results', type=int, default=20, help='Maximum results (default 20)')
    parser.add_argument('--output', required=True, help='Output JSON file path')
    parser.add_argument('--no-headless', action='store_true', help='Show browser window (for debugging)')
    args = parser.parse_args()

    result = scrape_google_maps(
        query=args.query,
        city=args.city,
        state=args.state,
        max_results=args.max_results,
        headless=not args.no_headless,
        output_file=args.output,
    )

    # Summary
    n = len(result.get('results', []))
    with_websites = sum(1 for r in result.get('results', []) if r.get('website'))
    with_phones = sum(1 for r in result.get('results', []) if r.get('phone'))
    with_address = sum(1 for r in result.get('results', []) if r.get('formatted_address'))

    print(f"\n{'='*60}")
    print(f"SCRAPE COMPLETE")
    print(f"  Total results:      {n}")
    print(f"  With website:       {with_websites}")
    print(f"  With phone:         {with_phones}")
    print(f"  With address:       {with_address}")
    print(f"{'='*60}")

    return result


if __name__ == '__main__':
    main()
