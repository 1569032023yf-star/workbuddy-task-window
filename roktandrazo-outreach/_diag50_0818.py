import os, sys, re, ssl, sqlite3, urllib.request
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
def fetch(url, timeout=8, proxy=False):
    try:
        if proxy:
            op = urllib.request.build_opener(urllib.request.ProxyHandler(
                {"http":"http://127.0.0.1:3213","https":"http://127.0.0.1:3213"}))
        else:
            op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
        with op.open(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.status, r.read(300000).decode("utf-8","replace")
    except Exception:
        return None, ""
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ids = [26,132,134,136,142,144,145,146,147,148,149,153,170,171,179,180,181,182,269,270,275,278,280,283,284,285,286,287,291,292,295,297,300,301,302,563,564,625,680,681,682,692,694,696,704,705,712,780,782,784]
conn = sqlite3.connect(os.path.join("data","bd_leads.db")); conn.row_factory=sqlite3.Row
ok=0; fail=0; withmail=0; matchmail=0
for i,lid in enumerate(ids,1):
    r = conn.execute("SELECT store_name,official_website FROM leads WHERE id=?",(lid,)).fetchone()
    web = str(r["official_website"] or "")
    if not web.startswith("http"): web = "http://" + web
    host = re.sub(r"^https?://","",web).split("/")[0].lower().replace("www.","")
    st, h = fetch(web)
    via = "direct"
    if st != 200:
        st, h = fetch(web, proxy=True); via = "proxy"
    emails = EMAIL_RE.findall(h)
    em = [e for e in emails if e.rsplit("@",1)[-1]==host or e.rsplit("@",1)[-1].endswith("."+host)]
    if st == 200: ok += 1
    else: fail += 1
    if emails: withmail += 1
    if em: matchmail += 1
    print(f"[{i:>2}] {lid:<4} {r['store_name'][:22]:<22} {via:<6} {st} emails={len(emails)} match={len(em)} {em[:2]}")
print(f"\nOK={ok} FAIL={fail} any_email={withmail} domain_match_email={matchmail} /50")
conn.close()
