"""Check post-scroll DOM: any /maps/place/ links or list containers."""
import time
from playwright.sync_api import sync_playwright

URL = "https://www.google.com/maps/search/toy+store+Ithaca+NY"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled','--no-sandbox','--disable-dev-shm-usage'])
    ctx = browser.new_context(user_agent=UA, viewport={'width':1280,'height':900}, locale='en-US')
    page = ctx.new_page()
    page.goto(URL, wait_until='domcontentloaded', timeout=30000)
    time.sleep(5)
    # scroll main panel / body repeatedly
    for i in range(8):
        page.mouse.wheel(0, 2500)
        time.sleep(1.2)
    # look for place links
    links = page.query_selector_all('a[href*="/maps/place/"]')
    print("place links:", len(links))
    for a in links[:10]:
        aria = a.get_attribute('aria-label') or ''
        href = a.get_attribute('href') or ''
        print(f"  aria={aria[:50]!r} href={href[:70]}")
    # any heading elements
    heads = page.query_selector_all('h1, h2, h3')
    print("headings:", len(heads))
    for h in heads[:10]:
        print(f"  {h.tag_name}: {h.inner_text()[:50]!r}")
    # presence of 'limited view' banner
    body = page.inner_text('body')
    print("limited view banner:", 'limited view' in body.lower())
    print("sign in banner:", 'Sign in' in body)
    print("NO_RESULTS:", 'No results' in body)
    browser.close()
