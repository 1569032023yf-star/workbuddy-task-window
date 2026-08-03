#!/usr/bin/env python3
"""
Controlled inventory expansion runner for Roktandrazo BD automation.

Defaults are safe:
- dry-run only
- masked output only
- TN/AR/KY only
- no customer email send
- no Google Maps direct A0 upgrade
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import sqlite3
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
WORKBUDDY_ROOT = ROOT.parent
DB_PATH = ROOT / "data" / "bd_leads.db"
OUTPUT_DIR = ROOT / "output"
BACKUP_DIR = ROOT / "backups"
DEFAULT_STATES = ("TN", "AR", "KY")
CONTACT_PATHS = (
    "/", "/contact", "/contact-us", "/pages/contact", "/pages/contact-us",
    "/about", "/about-us", "/pages/about", "/wholesale", "/vendor", "/buyer",
    "/faq", "/pages/faq",
)
SOURCE_CHOICES = (
    "existing_evidence_url_missing_snippet",
    "historical_google_maps_candidates",
    "b2_official_website",
)
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
GENERIC_PREFIXES = ("info@", "contact@", "hello@", "sales@", "wholesale@", "orders@", "support@")
SKIP_EMAIL_PARTS = (
    "example.com", "yourdomain", "domain.com", "youremail", "roktandrazo",
    "wixpress", "sentry", "shopify", ".png", ".jpg", ".gif", ".svg",
)
SKIP_CANDIDATE_NAMES = (
    "walmart", "target", "dollar tree", "dollar general", "five below", "gamestop",
    "build-a-bear", "disney store", "lego store", "toys r us", "party city",
    "hobby lobby", "michaels", "cvs", "walgreens", "amazon",
)


@dataclass
class Candidate:
    source: str
    store_name: str
    city: str
    state: str
    official_website: str = ""
    evidence_url: str = ""
    email: str = ""
    lead_id: int | None = None
    store_type: str = ""
    google_maps_url: str = ""


@dataclass
class Result:
    source: str
    lead_id: int | None
    store_name: str
    city: str
    state: str
    official_domain: str
    masked_email: str
    email_for_write: str
    classification: str
    method: str
    evidence_url: str
    evidence_snippet: str
    would_write: bool
    reason: str
    pages_checked: int
    scan_seconds: float


def parse_states(raw: str) -> set[str]:
    states = {s.strip().upper() for s in raw.split(",") if s.strip()}
    if not states:
        states = set(DEFAULT_STATES)
    disallowed = states - set(DEFAULT_STATES)
    if disallowed:
        raise SystemExit(f"Only TN/AR/KY are allowed. Disallowed states: {sorted(disallowed)}")
    return states


def canonical_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    return u


def host(url: str) -> str:
    u = canonical_url(url)
    if not u:
        return ""
    try:
        h = urlparse(u).netloc.lower().split("@")[-1].split(":")[0]
        return h[4:] if h.startswith("www.") else h
    except Exception:
        return ""


def domains_match(a: str, b: str) -> bool:
    ah, bh = host(a), host(b)
    return bool(ah and bh and (ah == bh or ah.endswith("." + bh) or bh.endswith("." + ah)))


def email_domain_matches_site(email: str, site: str) -> bool:
    if not email or "@" not in email:
        return False
    ed = email.split("@")[-1].lower()
    wh = host(site)
    return bool(ed and wh and (ed == wh or ed.endswith("." + wh) or wh.endswith("." + ed)))


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return ""
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[:1] + "*"
    else:
        masked_local = local[:2] + "***"
    return masked_local + "@" + domain


def mask_emails_in_text(text: str) -> str:
    def repl(match):
        return mask_email(match.group(0).lower())
    return EMAIL_RE.sub(repl, text or "")


def clean_text(body: str) -> str:
    soup = BeautifulSoup(body or "", "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "img", "video", "audio", "iframe"]):
        tag.decompose()
    return re.sub(r"\s+", " ", html.unescape(soup.get_text(" ", strip=True))).strip()


def extract_emails(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for m in EMAIL_RE.finditer(text or ""):
        email = m.group(0).lower()
        if any(skip in email for skip in SKIP_EMAIL_PARTS):
            continue
        start = max(0, m.start() - 80)
        end = min(len(text), m.end() + 80)
        snippet = text[start:end].replace("\n", " ").strip()[:240]
        found.append((email, snippet))
    deduped: list[tuple[str, str]] = []
    seen = set()
    for email, snippet in found:
        if email not in seen:
            seen.add(email)
            deduped.append((email, snippet))
    return deduped


def has_contact_form(body: str) -> bool:
    low = (body or "").lower()
    return "<form" in low or "contact form" in low


def http_fetch(client: httpx.Client, url: str) -> tuple[int, str, str]:
    try:
        resp = client.get(canonical_url(url))
        return resp.status_code, resp.text or "", str(resp.url)
    except Exception as exc:
        return 0, "", f"fetch_error:{type(exc).__name__}"


def browser_fetch(url: str, timeout: int = 15) -> tuple[str, str]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return "", f"browser_unavailable:{type(exc).__name__}"
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
            )
            page = context.new_page()
            page.goto(canonical_url(url), wait_until="domcontentloaded", timeout=timeout * 1000)
            time.sleep(1)
            try:
                text = page.inner_text("body")
            except Exception:
                text = page.content()
            context.close()
            browser.close()
            return re.sub(r"\s+", " ", html.unescape(text)).strip(), "browser"
    except Exception as exc:
        return "", f"browser_error:{type(exc).__name__}"


def select_verified_email(emails: list[tuple[str, str]], site: str) -> tuple[str, str]:
    for email, snippet in emails:
        if email_domain_matches_site(email, site):
            return email, snippet
    for email, snippet in emails:
        if email.startswith(GENERIC_PREFIXES):
            return email, snippet
    return "", ""


def candidate_key(c: Candidate) -> str:
    dom = host(c.official_website) or host(c.evidence_url) or c.store_name.lower()
    return f"{dom}|{c.store_name.lower()}|{c.city.lower()}|{c.state}"


def domain_key(c: Candidate) -> str:
    return host(c.official_website) or host(c.evidence_url) or ""


def get_db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def load_existing_missing_snippet(con: sqlite3.Connection, states: set[str], limit: int) -> list[Candidate]:
    placeholders = ",".join("?" for _ in states)
    query = f"""
    SELECT l.id, l.store_name, l.city, l.state, l.store_type, l.official_website, l.evidence_url, l.email
    FROM leads l
    WHERE l.state IN ({placeholders})
      AND COALESCE(l.evidence_url,'')<>''
      AND (l.evidence_snippet IS NULL OR TRIM(l.evidence_snippet)='')
      AND COALESCE(l.status,'') <> 'sent'
      AND COALESCE(l.email_source_type,'') <> 'guessed_email'
      AND NOT EXISTS (SELECT 1 FROM suppression_list s WHERE lower(s.email)=lower(l.email))
      AND NOT EXISTS (SELECT 1 FROM send_log sl WHERE lower(sl.email)=lower(l.email) AND sl.status='sent')
      AND NOT EXISTS (SELECT 1 FROM bounce_log b WHERE lower(b.email)=lower(l.email) AND b.bounce_type IN ('hard','delivery_issue'))
      AND NOT EXISTS (SELECT 1 FROM reply_log r WHERE lower(r.email)=lower(l.email))
    ORDER BY l.state, l.city, l.id
    LIMIT ?
    """
    rows = con.execute(query, tuple(sorted(states)) + (limit,)).fetchall()
    return [Candidate(
        source="existing_evidence_url_missing_snippet",
        lead_id=r["id"], store_name=r["store_name"] or "", city=r["city"] or "",
        state=(r["state"] or "").upper(), store_type=r["store_type"] or "",
        official_website=r["official_website"] or "", evidence_url=r["evidence_url"] or "",
        email=r["email"] or "",
    ) for r in rows]


def load_b2_official_website(con: sqlite3.Connection, states: set[str], limit: int) -> list[Candidate]:
    placeholders = ",".join("?" for _ in states)
    query = f"""
    SELECT l.id, l.store_name, l.city, l.state, l.store_type, l.official_website, l.email
    FROM leads l
    WHERE l.state IN ({placeholders})
      AND l.status='manual_review_needed'
      AND l.confidence_score='B'
      AND COALESCE(l.official_website,'')<>''
      AND NOT EXISTS (SELECT 1 FROM send_log sl WHERE lower(sl.email)=lower(l.email) AND sl.status='sent')
    ORDER BY l.state, l.city, l.id
    LIMIT ?
    """
    rows = con.execute(query, tuple(sorted(states)) + (limit,)).fetchall()
    return [Candidate(
        source="b2_official_website",
        lead_id=r["id"], store_name=r["store_name"] or "", city=r["city"] or "",
        state=(r["state"] or "").upper(), store_type=r["store_type"] or "",
        official_website=r["official_website"] or "", email=r["email"] or "",
    ) for r in rows]


def iter_csv_rows(path: Path) -> Iterable[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as f:
            yield from csv.DictReader(f)
    except Exception:
        return


def load_historical_google_maps(states: set[str], limit: int) -> list[Candidate]:
    files = [
        WORKBUDDY_ROOT / "INVENTORY_SHIFT_TN_AR_KY_LIVE.csv",
        WORKBUDDY_ROOT / "INVENTORY_SHIFT_AR_KY_CANDIDATES.csv",
        WORKBUDDY_ROOT / "GOOGLE_MAPS_CANDIDATES_TN_SAMPLE.csv",
        WORKBUDDY_ROOT / "MANUAL_CONTACT_FETCH_QUEUE.csv",
    ]
    candidates: list[Candidate] = []
    seen = set()
    for path in files:
        if not path.exists():
            continue
        for row in iter_csv_rows(path):
            state = (row.get("state") or "").strip().upper()
            if state not in states:
                continue
            name = (row.get("store_name") or "").strip()
            if not name or any(skip in name.lower() for skip in SKIP_CANDIDATE_NAMES):
                continue
            key = f"{name.lower()}|{(row.get('city') or '').lower()}|{state}"
            if key in seen:
                continue
            seen.add(key)
            candidates.append(Candidate(
                source="historical_google_maps_candidates",
                store_name=name,
                city=(row.get("city") or "").strip(),
                state=state,
                official_website=(row.get("website") or row.get("official_website") or "").strip(),
                google_maps_url=(row.get("google_maps_url") or "").strip(),
                store_type=(row.get("store_type") or row.get("category") or "").strip(),
            ))
            if len(candidates) >= limit:
                return candidates
    return candidates


def gather_candidates(con: sqlite3.Connection, sources: list[str], states: set[str], batch_limit: int) -> list[Candidate]:
    candidates: list[Candidate] = []
    remaining = batch_limit
    if "existing_evidence_url_missing_snippet" in sources and remaining > 0:
        part = load_existing_missing_snippet(con, states, remaining)
        candidates.extend(part)
        remaining = batch_limit - len(candidates)
    if "historical_google_maps_candidates" in sources and remaining > 0:
        part = load_historical_google_maps(states, remaining)
        candidates.extend(part)
        remaining = batch_limit - len(candidates)
    if "b2_official_website" in sources and remaining > 0:
        part = load_b2_official_website(con, states, remaining)
        candidates.extend(part)
    deduped: list[Candidate] = []
    seen = set()
    for c in candidates:
        key = candidate_key(c)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)
        if len(deduped) >= batch_limit:
            break
    return deduped


def verify_existing_evidence(c: Candidate, client: httpx.Client, use_browser: bool, require_official_domain: bool) -> Result:
    start = time.time()
    if not c.email:
        return base_result(c, "B2_manual_review", "none", "", "missing_email", False, 0, start)
    if not c.official_website:
        return base_result(c, "invalid", "none", "", "missing_official_website", False, 0, start)
    if require_official_domain and not domains_match(c.evidence_url, c.official_website):
        return base_result(c, "invalid", "none", "", "evidence_url_not_official_domain", False, 0, start)
    if require_official_domain and not email_domain_matches_site(c.email, c.official_website):
        return base_result(c, "B2_manual_review", "none", "", "email_domain_not_official_domain", False, 0, start)
    status, body, final_url = http_fetch(client, c.evidence_url)
    pages = 1
    if status and status < 400:
        text = clean_text(body)
        emails = extract_emails(text) or extract_emails(html.unescape(body))
        for email, snippet in emails:
            if email == c.email.lower():
                return base_result(c, "A0_candidate", "http", snippet, "official_email_visible", True, pages, start, email=email, evidence_url=final_url)
        return base_result(c, "B2_manual_review", "http", "", "email_not_visible_on_evidence_url", False, pages, start)
    if use_browser:
        text, method = browser_fetch(c.evidence_url)
        if text:
            emails = extract_emails(text)
            for email, snippet in emails:
                if email == c.email.lower():
                    return base_result(c, "A0_candidate", "browser", snippet, "official_email_visible", True, pages, start, email=email, evidence_url=canonical_url(c.evidence_url))
            return base_result(c, "B2_manual_review", "browser", "", "email_not_visible_on_evidence_url", False, pages, start)
        reason = "blocked_cloudflare" if status in (403, 429) else method
        return base_result(c, "blocked_cloudflare" if status in (403, 429) else "browser_verification_needed", "browser", "", reason, False, pages, start)
    reason = "blocked_cloudflare" if status in (403, 429) else f"http_status_{status or 0}"
    return base_result(c, "blocked_cloudflare" if status in (403, 429) else "browser_verification_needed", "http", "", reason, False, pages, start)


def verify_website_scan(c: Candidate, client: httpx.Client, use_browser: bool, require_official_domain: bool) -> Result:
    start = time.time()
    if not c.official_website:
        return base_result(c, "B2_manual_review", "none", "", "missing_official_website_google_maps_candidate", False, 0, start)
    pages = 0
    saw_form = False
    for rel in CONTACT_PATHS:
        url = urljoin(canonical_url(c.official_website), rel)
        if require_official_domain and not domains_match(url, c.official_website):
            continue
        status, body, final_url = http_fetch(client, url)
        pages += 1
        if status and status < 400:
            text = clean_text(body)
            emails = extract_emails(text) or extract_emails(html.unescape(body))
            email, snippet = select_verified_email(emails, c.official_website)
            if email:
                return base_result(c, "A0_candidate", "http", snippet, "official_email_visible", True, pages, start, email=email, evidence_url=final_url)
            saw_form = saw_form or has_contact_form(body)
        elif status in (403, 429):
            if use_browser:
                text, method = browser_fetch(url)
                if text:
                    emails = extract_emails(text)
                    email, snippet = select_verified_email(emails, c.official_website)
                    if email:
                        return base_result(c, "A0_candidate", "browser", snippet, "official_email_visible", True, pages, start, email=email, evidence_url=url)
                return base_result(c, "blocked_cloudflare", "browser", "", "blocked_cloudflare", False, pages, start)
    if use_browser:
        for rel in CONTACT_PATHS[:5]:
            url = urljoin(canonical_url(c.official_website), rel)
            text, method = browser_fetch(url)
            pages += 1
            if text:
                emails = extract_emails(text)
                email, snippet = select_verified_email(emails, c.official_website)
                if email:
                    return base_result(c, "A0_candidate", "browser", snippet, "official_email_visible", True, pages, start, email=email, evidence_url=url)
    if saw_form:
        return base_result(c, "C_contact_form", "http", "", "contact_form_only", False, pages, start)
    return base_result(c, "B2_manual_review", "http_browser" if use_browser else "http", "", "no_official_email_found", False, pages, start)


def base_result(c: Candidate, classification: str, method: str, snippet: str, reason: str, would_write: bool,
                pages: int, start: float, email: str = "", evidence_url: str = "") -> Result:
    return Result(
        source=c.source,
        lead_id=c.lead_id,
        store_name=c.store_name,
        city=c.city,
        state=c.state,
        official_domain=host(c.official_website) or host(c.evidence_url),
        masked_email=mask_email(email or c.email),
        email_for_write=(email or c.email).lower(),
        classification=classification,
        method=method,
        evidence_url=evidence_url or canonical_url(c.evidence_url),
        evidence_snippet=snippet[:240],
        would_write=would_write and classification == "A0_candidate" and bool(snippet),
        reason=reason,
        pages_checked=pages,
        scan_seconds=round(time.time() - start, 2),
    )


def mark_duplicate_domains(results: list[Result]) -> tuple[list[Result], int]:
    seen: set[str] = set()
    duplicate_count = 0
    final: list[Result] = []
    for r in results:
        dom = r.official_domain
        if r.would_write and dom:
            if dom in seen:
                duplicate_count += 1
                r = Result(**{**asdict(r), "classification": "duplicate_domain", "would_write": False, "reason": "duplicate_domain"})
            else:
                seen.add(dom)
        final.append(r)
    return final, duplicate_count


def backup_db() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = BACKUP_DIR / f"inventory_expansion_write_safe_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / "bd_leads_backup.db"
    shutil.copy2(DB_PATH, dest)
    return str(dest)


def write_safe_updates(con: sqlite3.Connection, results: list[Result], evidence_method: str) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    updated = 0
    for r in results:
        if not r.would_write or r.lead_id is None:
            continue
        cur = con.execute(
            """
            UPDATE leads
            SET email=CASE WHEN COALESCE(email,'')='' THEN ? ELSE email END,
                email_type=CASE WHEN COALESCE(email_type,'')='' THEN 'business_email' ELSE email_type END,
                email_source_type=CASE WHEN COALESCE(email_source_type,'')='' THEN 'official_page_visible' ELSE email_source_type END,
                evidence_url=?, evidence_snippet=?, evidence_checked_at=?, evidence_method=?,
                email_verified_on_official_site=1,
                confidence_score='A', status='new', last_checked_at=?
            WHERE id=?
            """,
            (r.email_for_write, r.evidence_url, r.evidence_snippet, now, evidence_method, now, r.lead_id),
        )
        updated += max(cur.rowcount, 0)
    con.commit()
    return updated


def strict_pool_count(con: sqlite3.Connection, states: set[str]) -> tuple[int, int, int]:
    placeholders = ",".join("?" for _ in states)
    query = f"""
    SELECT l.id,l.official_website,l.email,l.domain_hash
    FROM leads l
    WHERE l.state in ({placeholders})
      AND l.status='new'
      AND l.confidence_score='A'
      AND coalesce(l.email_verified_on_official_site,0)=1
      AND coalesce(l.email,'')<>''
      AND coalesce(l.official_website,'')<>''
      AND coalesce(l.evidence_url,'')<>''
      AND coalesce(l.evidence_snippet,'')<>''
      AND coalesce(l.email_source_type,'') NOT IN ('guessed_email')
      AND lower(coalesce(l.mx_provider,'')) NOT LIKE '%microsoft%'
      AND lower(coalesce(l.mx_provider,'')) NOT LIKE '%outlook%'
      AND lower(coalesce(l.mx_provider,'')) NOT LIKE '%exchange%'
      AND NOT EXISTS (SELECT 1 FROM suppression_list s WHERE lower(s.email)=lower(l.email))
      AND NOT EXISTS (SELECT 1 FROM send_log sl WHERE lower(sl.email)=lower(l.email) AND sl.status='sent')
      AND NOT EXISTS (SELECT 1 FROM bounce_log b WHERE lower(b.email)=lower(l.email) AND b.bounce_type IN ('hard','delivery_issue'))
      AND NOT EXISTS (SELECT 1 FROM reply_log r WHERE lower(r.email)=lower(l.email))
    """
    rows = con.execute(query, tuple(sorted(states))).fetchall()
    seen = set()
    dup = 0
    for row in rows:
        dom = row["domain_hash"] or host(row["official_website"]) or (row["email"].split("@")[-1].lower() if row["email"] else "")
        if dom in seen:
            dup += 1
        else:
            seen.add(dom)
    return len(rows), len(seen), dup


def write_outputs(results: list[Result], summary: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    safe_results = []
    for r in results:
        item = asdict(r)
        item.pop("email_for_write", None)
        item["evidence_snippet"] = mask_emails_in_text(item.get("evidence_snippet", ""))
        safe_results.append(item)
    payload = {
        "summary": summary,
        "results": safe_results,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Controlled inventory expansion runner")
    parser.add_argument("--states", default=",".join(DEFAULT_STATES))
    parser.add_argument("--source", action="append", choices=SOURCE_CHOICES, default=[])
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--write-safe", action="store_true")
    parser.add_argument("--confirm-write-safe", default="")
    parser.add_argument("--mask-output", action="store_true", default=True)
    parser.add_argument("--batch-limit", type=int, default=50)
    parser.add_argument("--require-official-domain", action="store_true", default=True)
    parser.add_argument("--write-evidence-snippet", action="store_true", default=True)
    parser.add_argument("--browser", action="store_true", default=True)
    parser.add_argument("--no-browser", dest="browser", action="store_false")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    if args.batch_limit < 1 or args.batch_limit > 50:
        raise SystemExit("--batch-limit must be between 1 and 50")
    states = parse_states(args.states)
    sources = args.source or list(SOURCE_CHOICES)
    if args.write_safe and args.confirm_write_safe != "CONFIRM_WRITE_SAFE":
        raise SystemExit("--write-safe requires --confirm-write-safe CONFIRM_WRITE_SAFE")

    con = get_db()
    before_raw, before_strict, before_dupes = strict_pool_count(con, states)
    candidates = gather_candidates(con, sources, states, args.batch_limit)

    client = httpx.Client(
        follow_redirects=True,
        timeout=12,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"},
    )
    results: list[Result] = []
    for c in candidates:
        if c.state not in states:
            continue
        if c.source == "existing_evidence_url_missing_snippet":
            result = verify_existing_evidence(c, client, args.browser, args.require_official_domain)
        else:
            result = verify_website_scan(c, client, args.browser, args.require_official_domain)
        results.append(result)
    client.close()
    results, duplicate_count = mark_duplicate_domains(results)

    counts: dict[str, int] = {}
    for r in results:
        counts[r.classification] = counts.get(r.classification, 0) + 1
    would_write_count = sum(1 for r in results if r.would_write)
    backup_path = ""
    db_updated = 0
    if args.write_safe:
        backup_path = backup_db()
        db_updated = write_safe_updates(con, results, "website_browser_verified")
    after_raw, after_strict, after_dupes = strict_pool_count(con, states)
    con.close()

    estimate_after_write = before_strict + would_write_count
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dry_run": not args.write_safe,
        "write_safe": bool(args.write_safe),
        "states": sorted(states),
        "sources": sources,
        "total_checked": len(results),
        "browser_verified_count": sum(1 for r in results if r.method == "browser" and r.classification == "A0_candidate"),
        "http_verified_count": sum(1 for r in results if r.method == "http" and r.classification == "A0_candidate"),
        "new_A0_candidate_count": counts.get("A0_candidate", 0),
        "still_B2_count": counts.get("B2_manual_review", 0),
        "C_contact_form_count": counts.get("C_contact_form", 0),
        "invalid_count": counts.get("invalid", 0),
        "blocked_cloudflare_count": counts.get("blocked_cloudflare", 0),
        "duplicate_domain_count": duplicate_count,
        "would_write_count": would_write_count,
        "strict_pool_before": before_strict,
        "strict_pool_after_current_db": after_strict,
        "strict_pool_estimate_after_write": estimate_after_write,
        "gap_to_20_after_write_estimate": max(0, 20 - estimate_after_write),
        "gap_to_60_after_write_estimate": max(0, 60 - estimate_after_write),
        "db_backup_path": backup_path,
        "db_updated_rows": db_updated,
        "classification_counts": counts,
        "sensitive_output": "masked_only",
    }
    out = Path(args.output) if args.output else OUTPUT_DIR / f"inventory_expansion_dry_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    if not out.is_absolute():
        out = ROOT / out
    write_outputs(results, summary, out)

    print(json.dumps({
        "output": str(out),
        "total_checked": summary["total_checked"],
        "new_A0_candidate_count": summary["new_A0_candidate_count"],
        "would_write_count": summary["would_write_count"],
        "strict_pool_estimate_after_write": summary["strict_pool_estimate_after_write"],
        "gap_to_20_after_write_estimate": summary["gap_to_20_after_write_estimate"],
        "gap_to_60_after_write_estimate": summary["gap_to_60_after_write_estimate"],
        "sensitive_output": "masked_only",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
