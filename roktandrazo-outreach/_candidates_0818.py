import sqlite3, os, urllib.request, ssl
conn = sqlite3.connect(os.path.join("data","bd_leads.db")); conn.row_factory=sqlite3.Row

# candidate: manual pool, has website, not sent, not dup domain
rows = conn.execute("""
  SELECT l.id, l.store_name, l.city, l.state, l.official_website, l.email,
         l.review_reason_code, l.icp_route, l.recipient_timezone,
         (l.id IN (SELECT lead_id FROM send_log WHERE status='sent')) AS is_sent,
         (l.domain_hash IN (SELECT domain_hash FROM leads WHERE status='sent' AND domain_hash IS NOT NULL)) AS is_dupdom
  FROM leads l WHERE l.status='manual_review_needed'
    AND l.official_website IS NOT NULL AND l.official_website!=''
  ORDER BY is_sent ASC, l.icp_route ASC, l.id
""").fetchall()
print(f"pool leads WITH website: {len(rows)}")
valid = [dict(r) for r in rows if not r['is_sent'] and not r['is_dupdom']]
print(f"  of which NOT sent & NOT dup-domain: {len(valid)}")
sent_w = [dict(r) for r in rows if r['is_sent']]
print(f"  already sent: {len(sent_w)}")
for r in valid[:8]:
    print(f"   id={r['id']:<5} {r['store_name'][:26]:<26} {r['state']:<3} {r['review_reason_code'][:22]:<22} route={r['icp_route']} {r['official_website'][:44]}")
print("sample ids:", [r['id'] for r in valid[:50]])

# network probe: fetch 2 websites directly
def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.status, resp.read(300).decode("utf-8","replace")
import re
for r in valid[:2]:
    url = r['official_website']
    if not url.startswith("http"): url = "http://" + url
    try:
        st, body = fetch(url)
        print(f"FETCH {r['store_name'][:20]:<20} {url[:40]:<40} -> {st} | {body[:60]!r}")
    except Exception as e:
        print(f"FETCH {r['store_name'][:20]:<20} {url[:40]:<40} -> FAIL {type(e).__name__} {str(e)[:60]}")
conn.close()
