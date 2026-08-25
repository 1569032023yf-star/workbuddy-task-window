import os, sys, re, ssl, sqlite3, urllib.request
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
def fetch(url, timeout=9):
    try:
        op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
        req = urllib.request.Request(url, headers=UA)
        with op.open(req, timeout=timeout) as r:
            return r.status, r.read(400000).decode("utf-8","replace")
    except Exception as e:
        return None, str(e)[:80]
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
conn = sqlite3.connect(os.path.join("data","bd_leads.db")); conn.row_factory=sqlite3.Row
for lid in [26, 132]:
    L = dict(conn.execute("SELECT * FROM leads WHERE id=?", (lid,)).fetchone())
    web = L["official_website"]
    host = re.sub(r"^https?://","",web).split("/")[0].lower()
    print(f"\n##### id={lid} {L['store_name']} {host}")
    st, html = fetch(web)
    print(f"homepage: {st} len={len(html)}")
    if st == 200:
        links = re.findall(r'href=["\']([^"\']+)["\']', html)
        cand = [l for l in links if any(k in l.lower() for k in ("contact","about","visit","where","hours"))]
        print("contact-ish links:", cand[:12])
        allmails = EMAIL_RE.findall(html)
        print("emails on homepage:", allmails[:10])
        # fetch first contact link
        for l in cand[:3]:
            if l.startswith("/"): l = "https://" + host + l
            elif not l.startswith("http"): l = "https://" + host + "/" + l
            s2, h2 = fetch(l)
            print(f"  sub {l[:60]}: {s2} len={len(h2)}")
            if s2 == 200:
                print("    emails:", EMAIL_RE.findall(h2)[:10])
                break
conn.close()
