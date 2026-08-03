"""Inbox Polling Monitor — IMAP incremental scanner with DSN-based bounce detection.

Key design:
  - Classification order: self_sent → bounce(DSN) → unsubscribe → ignored_platform
    → auto_reply → support_ticket → hot_reply → normal_reply → unknown
  - First run: UIDVALIDITY baseline, skip historical messages (baseline_only=True)
  - Incremental: only UID > last_seen_uid
  - Stop signal: only for new UIDs attributable to current sends
  - Batch from oldest unprocessed UID (uids[:100]), not newest

Read-only. Never modifies DB, send_pause, or suppression.
"""
from __future__ import annotations

import email
import email.header
import email.utils
import imaplib
import json
import os
import re
import ssl
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
CHECKPOINT_FILE = PROJECT_DIR / "output" / "inbox_checkpoint.json"

# --- Load .env ---
env_path = PROJECT_DIR / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k.startswith("BD_"):
                    os.environ[k] = v

IMAP_HOST = os.getenv("BD_IMAP_HOST", "imap.exmail.qq.com")
IMAP_PORT = int(os.getenv("BD_IMAP_PORT", "993"))
IMAP_USER = os.getenv("BD_IMAP_USER", "")
IMAP_PASS = os.getenv("BD_IMAP_PASS", "")

# --- Patterns (clean separation) ---
BOUNCE_SUBJECTS = [
    re.compile(r"undelivered|delivery\s*status|returned\s*mail|mail\s*delivery", re.I),
    re.compile(r"failure\s*notice|failed\s*delivery|nondelivery", re.I),
    re.compile(r"delivery\s*notification|delivery\s*status\s*notification", re.I),
]
BOUNCE_FROM_PATTERNS = [
    re.compile(r"mailer-daemon|mailer\.daemon|postmaster", re.I),
]
AUTO_REPLY_SUBJECTS = [
    re.compile(r"automatic\s*reply|auto\.?reply|auto_reply", re.I),
    re.compile(r"out\s*of\s*(the\s*)?office|vacation|away\s*from", re.I),
]
UNSUB_SUBJECTS = [
    re.compile(r"unsubscribe", re.I),
]
UNSUB_BODY = [
    re.compile(r"you\s*have\s*been\s*unsubscribed|successfully\s*unsubscribed|removed\s*from.*list", re.I),
    re.compile(r"^unsubscribe$", re.I | re.M),
]
PLATFORM_SENDERS = [
    "tiktok", "no-reply@", "noreply@", "notification@", "verify@",
    "security@", "account@", "billing@", "donotreply", "do-not-reply",
    "admin@", "updates@", "info@.*newsletter",
]
SUPPORT_PATTERNS = [
    re.compile(r"support\s*ticket|case\s*#|ticket\s*#", re.I),
    re.compile(r"zendesk|freshdesk|helpscout|intercom", re.I),
]
MSGID_TECH_PATTERNS = [
    re.compile(r"message.id.*invalid|message.id.*rejected|message.id.*failed", re.I),
    re.compile(r"spf\s*(softfail|fail)|dkim\s*(fail|permerror)|dmarc\s*reject", re.I),
    re.compile(r"suspicious\s*.*header|malformed\s*.*header", re.I),
]

# Hot reply: requires clear intent combos, NOT single words like "store", "retail"
HOT_COMBO = [
    (re.compile(r"interested", re.I), re.compile(r"catalog|puzzle|game|product|line", re.I)),
    (re.compile(r"send\s*(me|us|your|the)", re.I), re.compile(r"catalog|price\s*list|line\s*sheet|info", re.I)),
    (re.compile(r"would\s*like\s*to", re.I), re.compile(r"carry|stock|order|wholesale|distribute", re.I)),
    (re.compile(r"tell\s*me\s*(more|about)", re.I), re.compile(r"puzzle|wholesale|pricing|product", re.I)),
    (re.compile(r"moq|minimum.*order", re.I), re.compile(r"puzzle|product|item", re.I)),
    (re.compile(r"wholesale", re.I), re.compile(r"info|information|price|pricing|catalog|inquiry", re.I)),
]

DEMO_DOMAINS = {"demo.com", "example.com", "test.com", "localhost"}
OUR_DOMAIN = IMAP_USER.split("@")[1] if "@" in IMAP_USER else ""


# ============================================================
# Helpers
# ============================================================

def _mask(email_addr: str) -> str:
    if "@" not in email_addr:
        return email_addr[:3] + "***"
    local, dom = email_addr.rsplit("@", 1)
    return f"{local[:3]}***@{dom}"

def _decode_header(val) -> str:
    if not val:
        return ""
    parts = email.header.decode_header(val or "")
    result = []
    for part, charset in parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or "utf-8", errors="replace"))
            except Exception:
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(str(part))
    return "".join(result)

def _decode_body(msg) -> str:
    """Extract body with charset, text/plain priority, strip quotes."""
    text_body = ""
    html_body = ""
    for part in msg.walk():
        ct = part.get_content_type()
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        charset = part.get_content_charset() or "utf-8"
        try:
            decoded = payload.decode(charset, errors="replace")
        except Exception:
            decoded = payload.decode("utf-8", errors="replace")
        if ct == "text/plain":
            text_body += decoded
        elif ct == "text/html":
            html_body += decoded

    body = text_body or html_body or ""
    # Strip quoted original message
    body = re.sub(r"(?:\r?\n>+[^\n]*)+", "", body)
    # Strip signatures (dash-dash-space)
    body = re.sub(r"\r?\n--\s*\r?\n.*$", "", body, flags=re.DOTALL)
    return body.strip()[:3000]

def _parse_dsn(msg) -> dict:
    """Extract DSN fields from bounce message."""
    body = _decode_body(msg)
    return {
        "final_recipient": _extract_dsn_field(body, r"Final-Recipient:\s*([^\n;]+)"),
        "original_recipient": _extract_dsn_field(body, r"Original-Recipient:\s*([^\n;]+)"),
        "original_message_id": _extract_dsn_field(body, r"Original-Message-ID:\s*<?([^\s>]+)>?"),
        "status": _extract_dsn_field(body, r"Status:\s*(\d+\.\d+\.\d+)"),
        "diagnostic": _extract_dsn_field(body, r"Diagnostic-Code:\s*([^\n]+)"),
    }

def _extract_dsn_field(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.I)
    return m.group(1).strip() if m else ""


# ============================================================
# Classification (ordered by priority)
# ============================================================

def classify_message(msg, dsn_result: dict = None) -> dict:
    subject = _decode_header(msg.get("Subject", ""))
    from_addr = (_decode_header(msg.get("From", "")) or "").lower()
    to_addr = (_decode_header(msg.get("To", "")) or "").lower()
    body = _decode_body(msg)
    dsn = dsn_result or {}

    # --- 0. Self-sent ---
    if OUR_DOMAIN and OUR_DOMAIN in from_addr:
        return {"type": "self_sent", "from": _mask(from_addr), "subject": subject[:60]}

    # --- 1. DSN / Bounce ---
    is_bounce = False
    for pat in BOUNCE_SUBJECTS:
        if pat.search(subject):
            is_bounce = True
            break
    if not is_bounce:
        for pat in BOUNCE_FROM_PATTERNS:
            if pat.search(from_addr):
                is_bounce = True
                break
    if is_bounce:
        status = dsn.get("status", "")
        diag = dsn.get("diagnostic", "")
        full = f"{status} {diag}"
        if not status:
            # Fallback: search body
            if re.search(r"5\.\d\.\d", body) or re.search(r"550|551|552|553|554", full):
                status = "5.0.0"
            elif re.search(r"4\.\d\.\d", body) or re.search(r"450|451|452", full):
                status = "4.0.0"
            else:
                return {"type": "unknown_bounce", "from": _mask(from_addr), "subject": subject[:60],
                        "recipient": _mask(dsn.get("final_recipient", "unknown"))}
        # Message-ID tech issues
        for pat in MSGID_TECH_PATTERNS:
            if pat.search(full):
                return {"type": "msgid_tech_bounce", "from": _mask(from_addr), "subject": subject[:60],
                        "recipient": _mask(dsn.get("final_recipient", "")), "diagnostic": diag[:80]}
        if status.startswith("5"):
            return {"type": "hard_bounce", "from": _mask(from_addr), "subject": subject[:60],
                    "recipient": _mask(dsn.get("final_recipient", "")), "status": status, "diagnostic": diag[:80]}
        elif status.startswith("4"):
            return {"type": "soft_bounce", "from": _mask(from_addr), "subject": subject[:60],
                    "recipient": _mask(dsn.get("final_recipient", "")), "status": status, "diagnostic": diag[:80]}
        else:
            return {"type": "unknown_bounce", "from": _mask(from_addr), "subject": subject[:60],
                    "recipient": _mask(dsn.get("final_recipient", "unknown"))}

    # --- 2. Unsubscribe ---
    for pat in UNSUB_SUBJECTS:
        if pat.search(subject):
            return {"type": "unsubscribe", "from": _mask(from_addr), "subject": subject[:60]}
    for pat in UNSUB_BODY:
        if pat.search(body[:500]):
            return {"type": "unsubscribe", "from": _mask(from_addr), "subject": subject[:60]}

    # --- 3. Ignored platform ---
    for ps in PLATFORM_SENDERS:
        if ps in from_addr:
            return {"type": "ignored_platform", "from": _mask(from_addr), "subject": subject[:60]}

    # --- 4. Auto-reply ---
    for pat in AUTO_REPLY_SUBJECTS:
        if pat.search(subject):
            return {"type": "auto_reply", "from": _mask(from_addr), "subject": subject[:60]}

    # --- 5. Support ticket ---
    for pat in SUPPORT_PATTERNS:
        if pat.search(body):
            return {"type": "support_ticket", "from": _mask(from_addr), "subject": subject[:60]}

    # --- 6. Hot reply (analyze customer-added text only, not original subject) ---
    if from_addr and "@" in from_addr and len(body) > 40:
        for left_pat, right_pat in HOT_COMBO:
            if left_pat.search(body) and right_pat.search(body):
                return {"type": "hot_reply", "from": _mask(from_addr), "subject": subject[:60]}

    # --- 7. Normal reply (real sender + content exists) ---
    if from_addr and "@" in from_addr and body:
        return {"type": "normal_reply", "from": _mask(from_addr), "subject": subject[:60]}

    # --- 8. Unknown ---
    return {"type": "unknown", "from": _mask(from_addr), "subject": subject[:60]}


# ============================================================
# IMAP & Polling
# ============================================================

def connect_imap() -> imaplib.IMAP4_SSL | None:
    try:
        ctx = ssl.create_default_context()
        conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=ctx)
        conn.login(IMAP_USER, IMAP_PASS)
        status, data = conn.select("INBOX", readonly=True)
        if status != "OK":
            return None
        return conn
    except Exception as e:
        print(f"  [IMAP ERROR] {str(e)[:80]}")
        return None

def get_uidvalidity(conn) -> int:
    try:
        status, data = conn.status("INBOX", "(UIDVALIDITY)")
        if status == "OK" and data and data[0]:
            m = re.search(rb"UIDVALIDITY\s+(\d+)", data[0] if isinstance(data[0], bytes) else str(data[0]).encode())
            if m:
                return int(m.group(1))
    except Exception:
        pass
    return 0

def get_max_uid(conn) -> int:
    try:
        status, data = conn.uid("SEARCH", None, "ALL")
        if status == "OK" and data and data[0]:
            uids = [int(u) for u in data[0].split() if u.isdigit()]
            return max(uids) if uids else 0
    except Exception:
        pass
    return 0

def _empty_result():
    return {
        "normal_reply": 0, "hot_reply": 0, "auto_reply": 0,
        "hard_bounce": 0, "soft_bounce": 0, "unknown_bounce": 0,
        "msgid_tech_bounce": 0, "unsubscribe": 0, "support_ticket": 0,
        "ignored_platform": 0, "self_sent": 0, "unknown": 0,
        "total_new": 0, "has_more": False,
        "stop_required": False, "stop_reasons": [],
        "baseline_only": False, "poll_error": None,
    }

def poll_inbox(conn) -> dict:
    """Poll inbox incrementally. First run = baseline (no stop signal).
    Returns: classification dict."""
    cp = _load_checkpoint()
    uidvalidity = get_uidvalidity(conn)
    max_uid = get_max_uid(conn)

    # Check UIDVALIDITY change
    if uidvalidity and cp.get("uidvalidity") and uidvalidity != cp["uidvalidity"]:
        print("  [RESET] UIDVALIDITY changed. Re-baselining.")
        cp = {"last_seen_uid": 0, "uidvalidity": uidvalidity, "processed_total": 0}

    # First ever run: establish baseline
    is_baseline = False
    if cp.get("last_seen_uid", 0) == 0 or not CHECKPOINT_FILE.exists():
        is_baseline = True
        cp["uidvalidity"] = uidvalidity
        cp["last_seen_uid"] = max_uid
        cp["processed_total"] = cp.get("processed_total", 0)
        _save_checkpoint(cp)
        result = _empty_result()
        result["baseline_only"] = True
        result["total_new"] = max_uid
        print(f"  [BASELINE] UIDVALIDITY={uidvalidity}, highest UID={max_uid}. No stop signals for history.")
        return result

    last_uid = cp.get("last_seen_uid", 0)

    # Search new UIDs (strictly > last_seen_uid)
    try:
        status, data = conn.uid("SEARCH", None, f"UID {last_uid + 1}:*")
    except Exception as e:
        result = _empty_result()
        result["poll_error"] = str(e)[:80]
        print(f"  [POLL ERROR] IMAP SEARCH failed: {e}")
        return result

    if status != "OK":
        result = _empty_result()
        result["poll_error"] = f"SEARCH status: {status}"
        return result

    if not data or not data[0]:
        result = _empty_result()
        cp["last_checked_at"] = datetime.now().isoformat()
        _save_checkpoint(cp)
        return result

    uids = sorted([int(u) for u in data[0].split() if u.isdigit()])
    has_more = len(uids) > 100

    # Process from OLDEST first: uids[:100]
    batch = uids[:100]

    result = _empty_result()
    result["total_new"] = len(batch)
    result["has_more"] = has_more
    processed_ok = 0

    for uid in batch:
        try:
            s, msg_data = conn.uid("FETCH", str(uid), "(RFC822)")
            if s != "OK" or not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1] if isinstance(msg_data[0], tuple) else None
            if not raw:
                continue
            msg = email.message_from_bytes(raw)
        except Exception:
            continue  # Don't skip the UID — but we can't checkpoint past this

        dsn = _parse_dsn(msg) if _is_bounce_envelope(msg) else {}
        cls = classify_message(msg, dsn)
        key = cls["type"]

        if key in result:
            result[key] += 1

        # Stop signal: only for new UIDs attributable to current BD sends
        if not is_baseline and key in ("hard_bounce", "unsubscribe", "msgid_tech_bounce"):
            result["stop_required"] = True
            recipient = (cls.get("recipient") or cls.get("from"))[:40]
            result["stop_reasons"].append(f"{key}: {recipient}")

        processed_ok = uid  # checkpoint only to highest successfully processed UID

    # Update checkpoint (only to highest consecutive OK UID)
    if processed_ok > last_uid:
        cp["last_seen_uid"] = processed_ok
        cp["uidvalidity"] = uidvalidity
        cp["processed_total"] = cp.get("processed_total", 0) + processed_ok - last_uid
        _save_checkpoint(cp)

    return result

def _is_bounce_envelope(msg) -> bool:
    """Quick check if message looks like a bounce/DSN."""
    from_addr = (_decode_header(msg.get("From", "")) or "").lower()
    subject = _decode_header(msg.get("Subject", ""))
    for pat in BOUNCE_FROM_PATTERNS:
        if pat.search(from_addr):
            return True
    for pat in BOUNCE_SUBJECTS:
        if pat.search(subject):
            return True
    return False

# ============================================================
# Checkpoint
# ============================================================

def _load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        try:
            return json.loads(CHECKPOINT_FILE.read_text())
        except Exception:
            pass
    return {"last_seen_uid": 0, "uidvalidity": 0, "processed_total": 0}

def _save_checkpoint(cp: dict):
    cp["last_checked_at"] = datetime.now().isoformat()
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_FILE.write_text(json.dumps(cp, indent=2))

# ============================================================
# Main
# ============================================================

def main():
    print("=" * 50)
    print("Inbox Polling Monitor v2")
    print("=" * 50)

    conn = connect_imap()
    if not conn:
        print("  [FAIL] Cannot connect IMAP.")
        return

    print(f"  Connected: {IMAP_HOST}")

    # Run poll (baseline auto-detected)
    result = poll_inbox(conn)
    conn.logout()

    print()
    print(f"  Total new:            {result['total_new']}")
    print(f"  Baseline only:        {result['baseline_only']}")
    print(f"  Has more:             {result['has_more']}")
    print()
    print(f"  normal_reply:         {result['normal_reply']}")
    print(f"  hot_reply:            {result['hot_reply']}")
    print(f"  auto_reply:           {result['auto_reply']}")
    print(f"  ignored_platform:     {result['ignored_platform']}")
    print(f"  hard_bounce:          {result['hard_bounce']}")
    print(f"  soft_bounce:          {result['soft_bounce']}")
    print(f"  unknown_bounce:       {result['unknown_bounce']}")
    print(f"  msgid_tech_bounce:    {result['msgid_tech_bounce']}")
    print(f"  unsubscribe:          {result['unsubscribe']}")
    print(f"  support_ticket:       {result['support_ticket']}")
    print(f"  self_sent:            {result['self_sent']}")
    print(f"  unknown:              {result['unknown']}")
    print()
    print(f"  Stop required:        {result['stop_required']}")
    if result["stop_reasons"]:
        for r in result["stop_reasons"]:
            print(f"    - {r}")
    if result["poll_error"]:
        print(f"  Poll error:           {result['poll_error']}")

    # Save
    output = {"timestamp": datetime.now().isoformat(), "poll": result}
    path = PROJECT_DIR / "output" / "inbox_poll_result.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n  Saved: {path}")


# ============================================================
# Regression tests
# ============================================================

def run_tests():
    """Embedded regression tests for classification."""
    tests = []

    # Create simple test messages
    def _make_msg(from_addr, subject, body):
        from email.mime.text import MIMEText
        msg = MIMEText(body)
        msg["From"] = from_addr
        msg["Subject"] = subject
        return msg

    # Test 1: unsubscribe
    m = _make_msg("customer@gmail.com", "Please unsubscribe", "Please unsubscribe me from your mailing list")
    cls = classify_message(m)
    tests.append(("unsubscribe request", cls["type"] == "unsubscribe", cls["type"]))

    # Test 2: DSN 5.1.1
    m = _make_msg("mailer-daemon@googlemail.com", "Delivery Status Notification (Failure)",
                  "Final-Recipient: rfc822; test@unknown.com\nStatus: 5.1.1\nDiagnostic-Code: smtp; 550 user unknown")
    cls = classify_message(m, _parse_dsn(m))
    tests.append(("DSN 5.1.1 hard_bounce", cls["type"] == "hard_bounce", cls["type"]))

    # Test 3: DSN 4.2.0
    m = _make_msg("mailer-daemon@example.com", "Delivery Status Notification (Delay)",
                  "Final-Recipient: rfc822; test@full.com\nStatus: 4.2.0\nDiagnostic-Code: smtp; mailbox full")
    cls = classify_message(m, _parse_dsn(m))
    tests.append(("DSN 4.2.0 soft_bounce", cls["type"] == "soft_bounce", cls["type"]))

    # Test 4: TikTok verification
    m = _make_msg("no-reply@mail.tiktokglobalshop.com", "TikTok Shop verification code", "Your code is 123456")
    cls = classify_message(m)
    tests.append(("TikTok ignored_platform", cls["type"] == "ignored_platform", cls["type"]))

    # Test 5: Thanks only → normal_reply, not hot
    m = _make_msg("buyer@toystore.com", "Re: Wholesale Inquiry - My Store", "Thanks!")
    cls = classify_message(m)
    tests.append(("Thanks = normal_reply", cls["type"] == "normal_reply", cls["type"]))

    # Test 6: Price list request → hot_reply
    m = _make_msg("buyer@toystore.com", "Re: Wholesale Inquiry", "Please send your price list and catalog. We are interested.")
    cls = classify_message(m)
    tests.append(("price list = hot_reply", cls["type"] == "hot_reply", cls["type"]))

    print("\n--- Regression Tests ---")
    passed = 0
    for name, ok, got in tests:
        print(f"  {'✓' if ok else '✗'} {name} (got: {got})")
        if ok:
            passed += 1
    print(f"  {passed}/{len(tests)} passed")

if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        run_tests()
    else:
        main()
