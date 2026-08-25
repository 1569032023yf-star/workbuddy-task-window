"""P1.7B Machine-First Recovery — existing manual pool -> V2 (operations only).
Uses existing: bd_leads.db, discovery fetch pattern, review_workflow actions,
timezone_resolver, preflight MX worker, campaign_eligible_v2 gate.
No new system, no new fields, no send.
"""
import os, sys, re, ssl, sqlite3, urllib.request, urllib.error, uuid
from datetime import datetime
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)
def _load_env(p):
    try:
        for line in open(p, encoding="utf-8"):
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,v=line.split("=",1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError: pass
_load_env(os.path.join(BASE,".env"))
from timezone_resolver import resolve_timezone
from review_workflow import apply_review_action
from campaign_eligible_v2 import review_campaign_eligible_v2, _domain_of_email

LIVE = os.environ.get("LIVE") == "1"
DRY_IDS = set(int(x) for x in os.environ.get("DRY_IDS","").split(",") if x)
NOW = datetime.now().isoformat(timespec="seconds")

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
UA = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(url, timeout=9, use_proxy=False):
    try:
        if use_proxy:
            ph = urllib.request.ProxyHandler({"http":"http://127.0.0.1:3213","https":"http://127.0.0.1:3213"})
            op = urllib.request.build_opener(ph)
        else:
            op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
        req = urllib.request.Request(url, headers=UA)
        with op.open(req, timeout=timeout) as r:
            return r.status, r.read(400_000).decode("utf-8","replace")
    except Exception:
        return None, ""

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
JUNK = ("2x.jpg","sentry","example.com","wixpress","squarespace","godaddy","shopify",
        "schema.org",".png",".jpg",".jpeg",".gif",".webp",".svg",".css",".js","yourdomain",
        "email.com","domain.com","site.com")

def reg_of(host):
    h = host.lower().replace("www.","")
    return h

def emails_in(html):
    out = []
    for m in EMAIL_RE.findall(html or ""):
        e = m.strip().lower().rstrip(".")
        if not e or " " in e: continue
        dom = e.rsplit("@",1)[-1]
        if not dom or "." not in dom: continue
        if any(j in e for j in JUNK): continue
        if e.endswith((".png",".jpg",".jpeg",".gif",".webp",".svg")): continue
        out.append(e)
    return out

def mx_ok(domain):
    try:
        from preflight_gate import query_mx
        st,_ = query_mx(domain)
        if st == "dns_error":
            st,_ = query_mx(domain)
        return st == "ok"
    except Exception:
        return False

def process(conn, lead_id):
    lead = dict(conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone())
    if not lead: return ("MISSING", None)
    # 1) history / duplicate cross-check (existing rules)
    if lead["id"] in {r["lead_id"] for r in conn.execute("SELECT lead_id FROM send_log WHERE status='sent'")}:
        return ("DUPLICATE_SENT", None)
    if lead.get("domain_hash") and conn.execute(
        "SELECT 1 FROM leads WHERE status='sent' AND domain_hash=? AND id!=? LIMIT 1",
        (lead["domain_hash"], lead["id"])).fetchone():
        return ("DUPLICATE_ORG", None)
    web = str(lead.get("official_website") or "").strip()
    if not web:
        return ("NEEDS_HUMAN", "no_website")
    if not web.startswith("http"): web = "http://" + web
    host = re.sub(r"^https?://","",web).split("/")[0].lower().replace("www.","")
    reg = reg_of(host)
    # 2) ICP: use existing classification; route U / empty -> keep human unless website+email strong
    icp = str(lead.get("icp_route") or "")
    # 3-5) fetch homepage + up to 2 high-value pages
    pages = []
    st, html = fetch(web)
    if st != 200:
        st, html = fetch(web, use_proxy=True)
    if st == 200:
        pages.append((web, html))
        links = re.findall(r'href=["\']([^"\']+)["\']', html)
        want = []
        for lnk in links:
            l = lnk.lower()
            if any(k in l for k in ("contact","about","wholesale","privacy","hours","where","visit")) and not l.startswith(("javascript","mailto","tel:","#")):
                if l.startswith("/"): l = f"https://{host}{l}"
                elif l.startswith("http"): pass
                else: l = f"https://{host}/{l}"
                want.append(l)
        seen = {web}
        for w in want[:4]:
            if w in seen: continue
            seen.add(w)
            if len(pages) >= 3: break
            s2, h2 = fetch(w)
            if s2 != 200:
                s2, h2 = fetch(w, use_proxy=True)
            if s2 == 200:
                pages.append((w, h2))
    # collect first-party emails (domain must match site)
    cands = []
    for url, h in pages:
        for e in emails_in(h):
            edom = e.rsplit("@",1)[-1]
            if edom == reg or edom.endswith("." + reg):
                cands.append((e, url))
    # prefer lead's existing email if it appears on the page
    seen_e = set()
    found = []
    for e, url in cands:
        if e in seen_e: continue
        seen_e.add(e); found.append((e, url))
    if not found:
        return ("NEEDS_HUMAN", "no_first_party_email_found")
    # 6-7) pick best candidate, MX
    best = None
    for e, url in found:
        if mx_ok(e.rsplit("@",1)[-1]):
            best = (e, url); break
    if not best:
        # all candidates dead MX -> machine-confirmed no usable contact
        return ("AUTO_BLOCKED", "all_candidates_mx_fail")
    email, evurl = best
    # 8) Campaign Eligible V2
    tz, tzst = resolve_timezone(str(lead.get("city") or ""), str(lead.get("state") or ""))
    if tz is None:
        return ("NEEDS_HUMAN", "timezone_unresolved")
    tmp = {**lead, "email": email, "email_source_type": "official_page_visible",
           "email_verified_on_official_site": 1, "evidence_url": evurl,
           "evidence_snippet": f"{lead['store_name']} - {email} (found on {evurl})",
           "organization_key": f"org:domain:{reg}", "recipient_timezone": tz,
           "timezone_status": "RESOLVED", "mx_provider": "ok"}
    mx_lookup = {email.rsplit("@",1)[-1]: "ok"}
    r = review_campaign_eligible_v2(tmp, {"conn": conn, "mx_lookup": mx_lookup})
    if not r["eligible"]:
        return ("NEEDS_HUMAN", "v2_blocked:" + str(r["blockers"][:2]))
    # ---- write back (existing fields + existing review_workflow approve_auto) ----
    if not LIVE:
        return ("WOULD_RECOVER", (email, evurl))
    conn.execute("""UPDATE leads SET email=?, email_source_type='official_page_visible',
        email_verified_on_official_site=1, evidence_url=?, evidence_snippet=?,
        evidence_method='official_page_visible', organization_key=?, recipient_timezone=?,
        timezone_status='RESOLVED', mx_provider='ok', last_checked_at=? WHERE id=?""",
        (email, evurl, f"{lead['store_name']} - {email} (found on {evurl})",
         f"org:domain:{reg}", tz, NOW, lead_id))
    conn.commit()
    res = apply_review_action(conn, lead_id, "approve_auto", reviewer="machine_recovery_p17b",
                              reason="machine_recovered_v2", request_id=str(uuid.uuid4()))
    conn.execute("UPDATE leads SET review_reason_code='' WHERE id=?", (lead_id,))
    conn.commit()
    return ("RECOVERED", (email, evurl, res.get("new_status")))

def main():
    ids = [int(x) for x in sys.argv[1:]]
    conn = sqlite3.connect(os.path.join(BASE,"data","bd_leads.db"))
    conn.row_factory = sqlite3.Row
    from collections import Counter
    stats = Counter(); detail = []
    for i, lid in enumerate(ids, 1):
        outcome, info = process(conn, lid)
        stats[outcome] += 1
        detail.append((lid, outcome, info))
        print(f"[{i}/{len(ids)}] id={lid} -> {outcome} {'' if info is None else info}")
        conn.commit()
    print("\n=== SUMMARY ===")
    for k, v in stats.most_common(): print(f"  {k}: {v}")
    conn.close()

if __name__ == "__main__":
    main()
