"""Find new Google Maps results-list container structure."""
import time, re
from playwright.sync_api import sync_playwright

URL = "https://www.google.com/maps/search/toy+store+Ithaca+NY"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled','--no-sandbox','--disable-dev-shm-usage'])
    ctx = browser.new_context(user_agent=UA, viewport={'width':1280,'height':900}, locale='en-US')
    page = ctx.new_page()
    page.goto(URL, wait_until='domcontentloaded', timeout=30000)
    time.sleep(8)

    # 1) classic result card class Nv2PK
    nv = page.query_selector_all('.Nv2PK')
    print("Nv2PK cards:", len(nv))
    # 2) any element with aria-label containing 'Results'
    res = page.query_selector_all('[aria-label*="Results"]')
    print("aria-label*Results:", len(res))
    # 3) innerHTML snippet of main area to find containers
    html = page.content()
    # find class names that look like result containers
    classes = re.findall(r'class="([^"]{3,60})"', html)
    from collections import Counter
    cnt = Counter(classes)
    interesting = [c for c, n in cnt.most_common(60) if n > 2 and ('Nv2' in c or 'm6Q' in c or 'dS8' in c or 'kA9' in c or 'feed' in c or 'role' in c or 'section' in c or 'result' in c.lower())]
    print("interesting classes:", interesting[:20])
    # 4) try extracting via Nv2PK or a[aria-label] with business pattern
    print()
    print("=== extract attempts ===")
    cards = page.query_selector_all('.Nv2PK')
    if not cards:
        cards = page.query_selector_all('[role="feed"] > div')
    print("cards:", len(cards))
    for c in cards[:10]:
        txt = (c.inner_text() or '')[:80].replace('\n',' | ')
        print(f"  - {txt!r}")
    # 5) check if detail panel (hfpxzc anchor) present
    det = page.query_selector_all('a.hfpxzc')
    print()
    print("hfpxzc anchors:", len(det))
    for a in det[:8]:
        aria = a.get_attribute('aria-label') or ''
        href = a.get_attribute('href') or ''
        print(f"  aria={aria[:60]!r} href={href[:60]}")
    browser.close()
