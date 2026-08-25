"""Try proxy + headless=new for full Google Maps results."""
import time
from playwright.sync_api import sync_playwright

URL = "https://www.google.com/maps/search/toy+store+Ithaca+NY"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        headless=True,
        args=['--disable-blink-features=AutomationControlled','--no-sandbox','--disable-dev-shm-usage',
              '--proxy-server=http://127.0.0.1:3213'],
    )
    ctx = browser.new_context(user_agent=UA, viewport={'width':1280,'height':900}, locale='en-US')
    page = ctx.new_page()
    try:
        page.goto(URL, wait_until='domcontentloaded', timeout=40000)
        time.sleep(10)
        feeds = page.query_selector_all('[role="feed"]')
        print("feed:", len(feeds))
        nv = page.query_selector_all('.Nv2PK')
        print("Nv2PK:", len(nv))
        links = page.query_selector_all('a[href*="/maps/place/"]')
        print("place links:", len(links))
        body = page.inner_text('body')
        print("limited view:", 'limited view' in body.lower())
        print("body[:200]:", body[:200].replace('\n',' | '))
        if feeds:
            kids = feeds[0].query_selector_all(':scope > div')
            print("feed children:", len(kids))
            for k in kids[:5]:
                print("  -", (k.inner_text() or '')[:70].replace('\n',' | '))
    except Exception as e:
        print("EXC:", type(e).__name__, str(e)[:120])
    browser.close()
