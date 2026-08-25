"""Diagnose Google Maps page structure for Ithaca toy store query."""
import json, time
from playwright.sync_api import sync_playwright

URL = "https://www.google.com/maps/search/toy+store+Ithaca+NY"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled','--no-sandbox','--disable-dev-shm-usage'])
    ctx = browser.new_context(user_agent=UA, viewport={'width':1280,'height':900}, locale='en-US')
    page = ctx.new_page()
    page.goto(URL, wait_until='domcontentloaded', timeout=30000)
    time.sleep(6)
    # dump body text first 800
    body = page.inner_text('body')[:800]
    print("=== BODY TEXT (first 800) ===")
    print(body)
    print()
    # check feed presence
    feeds = page.query_selector_all('[role="feed"]')
    print("feed count:", len(feeds))
    if feeds:
        # inside feed: list direct children with their text
        kids = feeds[0].query_selector_all(':scope > div')
        print("feed direct children:", len(kids))
        for i, k in enumerate(kids[:6]):
            txt = (k.inner_text() or '')[:100].replace('\n',' | ')
            aria = k.get_attribute('aria-label') or ''
            print(f"  child[{i}] aria={aria[:40]!r} text={txt!r}")
    # any article role?
    arts = page.query_selector_all('[role="article"]')
    print()
    print("article count:", len(arts))
    for i, a in enumerate(arts[:5]):
        txt = (a.inner_text() or '')[:100].replace('\n',' | ')
        print(f"  article[{i}] text={txt!r}")
    # look for anchor with business name pattern
    print()
    print("=== anchors with aria-label > 10 chars (first 10) ===")
    anchors = page.query_selector_all('a[aria-label]')
    n=0
    for a in anchors:
        lbl = a.get_attribute('aria-label') or ''
        if len(lbl) > 10:
            print(f"  aria={lbl[:70]!r}")
            n+=1
            if n>=10: break
    browser.close()
