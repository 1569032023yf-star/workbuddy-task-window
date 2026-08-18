"""P1.7 批次3：Machine-First 官网邮箱自动扫描。"""
import sys, os, json, time, re
sys.path.insert(0, '.')
for line in open('.env', encoding='utf-8'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip())
import urllib.request
from website_verifier import (extract_emails_from_html, extract_links_from_html,
                              find_contact_page, find_wholesale_page)
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    try:
        return urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'replace')
    except Exception:
        alt = url.replace('https://', 'http://') if url.startswith('https') else url.replace('http://', 'https://')
        try:
            req = urllib.request.Request(alt, headers=UA)
            return urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'replace')
        except Exception:
            raise
def clean(emails):
    out = []; seen = set()
    for e in emails:
        e = e.strip().lower().rstrip('.')
        if e in seen: continue
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', e): continue
        if any(x in e for x in ['example.com','test.com','yourdomain','placeholder','sentry','noreply','no-reply','wixpress','squarespace','.png','.jpg','.jpeg','.gif','.webp','godaddy']): continue
        seen.add(e); out.append(e)
    return out

batch = json.load(open('output/p17_batch3.json'))
clues = json.load(open('output/p17_batch3_dir_clues.json'))

out = []
for s in batch:
    name = s['name']
    clue = clues.get(name, {})
    website = clue.get('website', '')
    rec = {'name': name, 'city': s['city'], 'state': s['state'],
           'clue_website': website, 'dir_email_clue': clue.get('dir_email_clue', '')}
    if not website:
        rec['status'] = 'NO_WEBSITE_CLUE'
        out.append(rec); continue
    if 'facebook.com' in website:
        rec['status'] = 'FB_ONLY'
        out.append(rec); continue
    url = website if website.startswith('http') else 'http://' + website
    pages = []
    try:
        html = fetch(url)
        pages.append({'url': url, 'html': html})
        links = extract_links_from_html(html, url)
        for p in (find_contact_page(links), find_wholesale_page(links)):
            if p and p not in [x['url'] for x in pages] and len(pages) < 3:
                try: pages.append({'url': p, 'html': fetch(p)})
                except Exception: pass
    except Exception as e:
        rec['status'] = f'FETCH_ERR:{type(e).__name__}'
        out.append(rec); continue
    all_emails = []; evs = []
    for p in pages:
        ems = clean(extract_emails_from_html(p['html']))
        if ems: all_emails.extend(ems); evs.append(p['url'])
    all_emails = clean(all_emails)
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower().replace('www.', '')
    name_key = re.sub(r'[^a-z0-9]', '', name.lower())
    domain_key = re.sub(r'[^a-z0-9]', '', domain.split('.')[0])
    dm = name_key and domain_key and (name_key in domain or domain_key in name_key)
    rec['fetched_pages'] = len(pages)
    rec['emails'] = all_emails
    rec['evidence_urls'] = evs
    rec['domain'] = domain
    rec['domain_match_store'] = bool(dm)
    if all_emails and dm: rec['status'] = 'EMAIL_FOUND'
    elif all_emails: rec['status'] = 'EMAIL_FOUND_OTHER_DOMAIN'
    else: rec['status'] = 'NO_EMAIL'
    out.append(rec)
    print(f"{name:<42} {rec['status']:<22} {domain:<32} {all_emails[:3]}")
    time.sleep(0.15)

json.dump(out, open('output/p17_batch3_scan.json', 'w'), ensure_ascii=False, indent=2)
from collections import Counter
print('\n=== 汇总 ===')
print(dict(Counter(r['status'].split(':')[0] for r in out)))
