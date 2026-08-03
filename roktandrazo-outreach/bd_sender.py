"""
Roktandrazo BD Outreach - Email Sender (Closed-Loop)
通过腾讯企业邮箱 SMTP 发信，从 .env 读取配置
支持 HTML + 纯文本双格式，Reply-To 头

P0 Gate: All production customer sends require a valid send_authorization.
No authorization = SendAuthorizationError raised, SMTP connection count = 0.
"""
import hashlib
import imaplib
import json
import os
import smtplib
import sqlite3
import ssl
import time
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid

from env_loader import get_smtp_config, get_sender_info, get_sending_limits, get_test_config, get_imap_config, is_configured, mask
from bd_db import update_lead_status, log_send, add_to_suppression, is_suppressed

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'bd_leads.db')
ASIA_SH = timezone(timedelta(hours=8))


class SendAuthorizationError(Exception):
    """Raised when a production customer send lacks a valid authorization."""
    pass


def validate_send_authorization(authorization_id: str = None, plan_entry_id: int = None,
                                 lead_id: int = None, recipient_email: str = None) -> dict:
    """Validate a send authorization before allowing SMTP.
    
    Supports per-entry consumption via send_authorization_entries table.
    Raises SendAuthorizationError if any check fails.
    """
    if not authorization_id:
        raise SendAuthorizationError("No authorization_id provided.")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        auth = conn.execute(
            "SELECT * FROM send_authorizations WHERE authorization_id=? AND status IN ('approved','in_progress')",
            (authorization_id,)
        ).fetchone()
        
        if not auth:
            raise SendAuthorizationError(f"Authorization {authorization_id} not found or not approved")
        
        expires_at = auth['expires_at']
        if expires_at:
            expiry = datetime.fromisoformat(expires_at)
            now = datetime.now(ASIA_SH)
            if now >= expiry.replace(tzinfo=ASIA_SH):
                raise SendAuthorizationError(f"Authorization {authorization_id} expired at {expires_at}")
        
        if auth['preflight_status'] != 'passed':
            raise SendAuthorizationError(f"preflight_status={auth['preflight_status']}")
        
        # Per-entry consumption check
        if plan_entry_id:
            entry = conn.execute(
                "SELECT status, consumed_at, lead_id, recipient_email FROM send_authorization_entries WHERE authorization_id=? AND plan_entry_id=?",
                (authorization_id, plan_entry_id)
            ).fetchone()
            if not entry:
                raise SendAuthorizationError(f"plan_entry_id={plan_entry_id} not in authorization")
            if entry['status'] == 'consumed':
                raise SendAuthorizationError(f"plan_entry_id={plan_entry_id} already consumed at {entry['consumed_at']}")
            if lead_id and entry['lead_id'] != lead_id:
                raise SendAuthorizationError(f"lead_id mismatch: auth has {entry['lead_id']}, requested {lead_id}")
            if recipient_email:
                auth_email = str(entry['recipient_email'] or '').strip().lower()
                req_email = str(recipient_email or '').strip().lower()
                if auth_email != req_email:
                    raise SendAuthorizationError(f"email mismatch: auth has {auth_email}, requested {req_email}")
        
        mp = conn.execute("SELECT value FROM system_config WHERE key='manual_pause'").fetchone()
        if mp and mp['value'] == 'true':
            raise SendAuthorizationError("manual_pause is true")
        
        sa = conn.execute("SELECT value FROM system_config WHERE key='standing_authorization'").fetchone()
        if not sa or sa['value'] != 'true':
            raise SendAuthorizationError("standing_authorization is not true")
        
        rg = conn.execute("SELECT value FROM system_config WHERE key='risk_gate_status'").fetchone()
        if not rg or rg['value'] != 'clear':
            raise SendAuthorizationError(f"risk_gate_status={rg['value'] if rg else 'N/A'}")
        
        return dict(auth)
    finally:
        conn.close()


def consume_authorization_entry(authorization_id: str, plan_entry_id: int) -> bool:
    """Mark one plan entry as consumed. Marks batch consumed when all entries done."""
    conn = sqlite3.connect(DB_PATH)
    try:
        now = datetime.now(ASIA_SH).isoformat()
        conn.execute(
            "UPDATE send_authorization_entries SET consumed_at=?, status='consumed' WHERE authorization_id=? AND plan_entry_id=? AND status='pending'",
            (now, authorization_id, plan_entry_id)
        )
        pending = conn.execute(
            "SELECT COUNT(*) FROM send_authorization_entries WHERE authorization_id=? AND status='pending'",
            (authorization_id,)
        ).fetchone()[0]
        if pending == 0:
            conn.execute(
                "UPDATE send_authorizations SET consumed_at=?, status='consumed' WHERE authorization_id=? AND status='approved'",
                (now, authorization_id)
            )
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def create_send_authorization(plan_id: str, outreach_batch_date: str,
                               planned_entries: list,
                               preflight_passed: bool,
                               db_path: str = None) -> dict:
    """Create a short-lived send authorization after preflight passes.
    
    Returns dict with authorization_id or raises on failure.
    """
    if not preflight_passed:
        raise ValueError("Cannot create authorization: preflight not passed")
    if not planned_entries:
        raise ValueError("Cannot create authorization: no planned entries")
    
    db = db_path or DB_PATH
    conn = sqlite3.connect(db)
    try:
        hash_input = json.dumps(
            sorted([{
                'lead_id': e.get('lead_id'),
                'recipient_email': str(e.get('recipient_email', '')).strip().lower(),
                'message_type': e.get('message_type'),
            } for e in planned_entries], key=lambda x: x['lead_id']),
            sort_keys=True)
        entries_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        db_digest = hashlib.sha256(open(db, 'rb').read()).hexdigest()[:16]
        
        authorization_id = f"auth_{plan_id}_{outreach_batch_date}_{entries_hash}"
        now = datetime.now(ASIA_SH).isoformat()
        expires = (datetime.now(ASIA_SH) + timedelta(minutes=15)).isoformat()
        
        conn.execute("""
            INSERT INTO send_authorizations (
                authorization_id, plan_id, outreach_batch_date,
                plan_entries_hash, approved_entry_count, database_sha256,
                preflight_status, approved_at, expires_at, approved_by, status
            ) VALUES (?,?,?,?,?,?,?,?,?,?,'approved')
        """, (
            authorization_id, plan_id, outreach_batch_date,
            entries_hash, len(planned_entries), db_digest,
            'passed', now, expires, 'system'
        ))
        
        # Also create per-entry records
        for e in planned_entries:
            lid = e.get('lead_id')
            remail = str(e.get('recipient_email', '')).strip().lower()
            entry_hash = hashlib.sha256(f"{lid}:{remail}".encode()).hexdigest()[:12]
            conn.execute("""
                INSERT OR IGNORE INTO send_authorization_entries
                (authorization_id, plan_entry_id, lead_id, recipient_email, entry_hash, status)
                VALUES (?,?,?,?,?,'pending')
            """, (authorization_id, lid, lid, remail, entry_hash))
        
        conn.commit()
        return {
            'authorization_id': authorization_id,
            'plan_id': plan_id,
            'approved_entry_count': len(planned_entries),
            'plan_entries_hash': entries_hash,
            'expires_at': expires,
            'status': 'approved',
        }
    finally:
        conn.close()


def _activate_tracking(token_hash: str, tracking_message_id: str, lead_id: int):
    """Register tracking token in D1 after SMTP success. Non-blocking — failures are silent."""
    try:
        import subprocess, os, json
        TRACKING_BASE = "https://roktandrazo-email-tracker.1569032023yf.workers.dev"
        # Register via HTTP POST to Worker admin endpoint (or directly via D1 CLI)
        # For now, use D1 CLI as it's the simplest path
        node_path = "C:/Users/15690/.workbuddy/binaries/node/versions/22.22.2"
        env = os.environ.copy()
        env["PATH"] = node_path + ";" + env.get("PATH", "")
        sql = f"UPDATE tracking_messages SET status='active', activated_at=datetime('now') WHERE token_hash='{token_hash}' AND status='prepared'"
        subprocess.run(
            [f"{node_path}/npx.cmd", "wrangler", "d1", "execute", "roktandrazo-email-tracking", "--remote", "--command", sql],
            cwd="cloudflare", env=env, capture_output=True, timeout=15
        )
    except Exception:
        pass  # Tracking failure must not block send


def ensure_standard_email_headers(msg: MIMEMultipart, sender_email: str, reply_to: str = None,
                                  message_id_domain: str = "roktandrazo.com") -> MIMEMultipart:
    """Ensure required RFC-style headers exist before serialization."""
    if "Date" not in msg:
        msg["Date"] = formatdate(localtime=True)
    if "Message-ID" not in msg:
        msg["Message-ID"] = make_msgid(domain=message_id_domain)
    if "MIME-Version" not in msg:
        msg["MIME-Version"] = "1.0"
    if "Reply-To" not in msg:
        msg["Reply-To"] = reply_to or sender_email
    return msg


def _create_connection():
    cfg = get_smtp_config()
    if not cfg["user"] or not cfg["password"]:
        raise ValueError("SMTP credentials not configured. Check .env file.")
    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=context, timeout=30)
    server.ehlo()
    server.login(cfg["user"], cfg["password"])
    return server


def _build_email(to_email: str, subject: str, body_text: str, body_html: str = None) -> MIMEMultipart:
    sender = get_sender_info()
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((sender["name"], sender["email"]))
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Reply-To"] = sender["email"]
    ensure_standard_email_headers(msg, sender["email"], sender["email"])

    # Plain text first, then HTML (HTML takes priority in email clients)
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))

    return msg


def _save_to_sent(msg: MIMEMultipart) -> None:
    """Save a copy of the sent email to the IMAP Sent folder (已发送)."""
    try:
        cfg = get_imap_config()
        if not cfg["user"] or not cfg["password"]:
            print("  [IMAP] No IMAP config, skipping sent-folder save")
            return

        if cfg["use_ssl"]:
            imap = imaplib.IMAP4_SSL(cfg["host"], cfg["port"], timeout=15)
        else:
            imap = imaplib.IMAP4(cfg["host"], cfg["port"], timeout=15)
        imap.login(cfg["user"], cfg["password"])

        raw_bytes = msg.as_bytes()

        # Tencent Exmail: "Sent Messages"
        folder = "Sent Messages"
        try:
            imap.append(folder, "\\Seen", imaplib.Time2Internaldate(time.time()), raw_bytes)
            print(f"  [IMAP] Saved to \"{folder}\"")
        except imaplib.IMAP4.error as e:
            print(f"  [IMAP] Failed to append to \"{folder}\": {e}")
            # Try the UTF-7 encoded parent path
            try:
                imap.append("&UXZO1mWHTvZZOQ-/Sent Messages", "\\Seen", imaplib.Time2Internaldate(time.time()), raw_bytes)
                print(f"  [IMAP] Saved to decoded Sent folder")
            except imaplib.IMAP4.error as e2:
                print(f"  [IMAP] Also failed: {e2}")

        imap.logout()
    except Exception as e:
        print(f"  [IMAP] Error: {e}")


def _pre_send_checks(subject: str, body_text: str) -> list[str]:
    """Safety checks before sending"""
    issues = []
    if "{{" in subject or "}}" in subject:
        issues.append(f"Subject contains unreplaced braces: {subject}")
    if "{{" in body_text or "}}" in body_text:
        issues.append("Body contains unreplaced braces {{}}")
    for bad in ["undefined", "None", "null"]:
        if bad in subject:
            issues.append(f"Subject contains '{bad}'")
    return issues


def send_one(lead: dict, dry_run: bool = False) -> dict:
    email = (lead.get("email") or "").strip()
    lead_id = lead.get("id")
    subject = lead.get("email_subject", "")
    body_text = lead.get("email_body", "")
    body_html = lead.get("email_body_html", "")
    plan_entry_id = lead.get("final_plan_entry_id")
    message_type = lead.get("message_type")
    outreach_batch_date = lead.get("outreach_batch_date")

    # Validation
    if not email:
        return {"success": False, "message": "No email", "status": "failed"}

    # Production sending is plan-only. A sender must never refill a batch from
    # the candidate pool after pre-send hygiene has frozen the recipient list.
    if not dry_run and (not plan_entry_id or message_type not in ('new_outreach', 'follow_up') or not outreach_batch_date):
        return {"success": False, "message": "Missing immutable final send plan metadata", "status": "failed"}

    if is_suppressed(email):
        return {"success": False, "message": "Email is suppressed", "status": "skipped"}

    if not subject or not body_text:
        return {"success": False, "message": "Missing email_subject or email_body", "status": "failed"}

    # Safety checks
    issues = _pre_send_checks(subject, body_text)
    if issues:
        return {"success": False, "message": f"Safety check failed: {'; '.join(issues)}", "status": "failed"}

    # Dry run
    if dry_run:
        return {
            "success": True,
            "message": f"[DRY RUN] Would send to {email}",
            "status": "dry_run",
            "preview": {"to": email, "subject": subject, "body_text": body_text, "body_html": body_html},
        }

    if not is_configured():
        return {"success": False, "message": "SMTP not configured", "status": "failed"}

    # Test mode: redirect to test email, add [TEST] tag
    test_cfg = get_test_config()
    actual_to = email
    if test_cfg["test_mode"] and test_cfg["test_email"]:
        actual_to = test_cfg["test_email"]
        subject = f"[TEST->{email}] {subject}"

    # ── P0: Send Authorization Gate (fail-closed) ──
    # All production customer sends require a valid authorization.
    # Test mode and dry runs are exempt.
    authorization_id = lead.get("authorization_id", "")
    if not test_cfg["test_mode"] and not dry_run:
        try:
            validate_send_authorization(authorization_id,
                                          plan_entry_id=plan_entry_id,
                                          lead_id=lead_id,
                                          recipient_email=email)
        except SendAuthorizationError as auth_err:
            return {"success": False, "message": f"SendAuthorizationError: {auth_err}", "status": "blocked"}

        # ── P0: Template assertion ──
        # New Outreach must use locked V5 templates; no auto-shortening or fallback
        if lead.get("message_type") == "new_outreach":
            from bd_template import check_inline_forbidden, _TEMPLATE_REGISTRY
            body = lead.get("email_body", "")
            template_key = lead.get("template_key", "")
            
            # Check forbidden phrases
            forbidden = check_inline_forbidden(body or "")
            if forbidden:
                return {"success": False,
                        "message": f"TEMPLATE_REJECTED: forbidden phrase(s) {forbidden}. SMTP blocked.",
                        "status": "blocked"}
            
            # Check for inline/fallback patterns
            if not template_key or template_key not in _TEMPLATE_REGISTRY:
                return {"success": False,
                        "message": f"TEMPLATE_REJECTED: template_key='{template_key}' not in registry. "
                                   "Only retail_distributor_v5_locked or custom_printing_production_v5_locked allowed.",
                        "status": "blocked"}
            
            tpl = _TEMPLATE_REGISTRY.get(template_key, {})
            if tpl.get("status") != "ACTIVE_LOCKED":
                return {"success": False,
                        "message": f"TEMPLATE_REJECTED: template_key={template_key} status={tpl.get('status')}. Must be ACTIVE_LOCKED.",
                        "status": "blocked"}

    # Build customer MIME (with pixel if tracking) and sender copy (no pixel)
    try:
        msg = _build_email(actual_to, subject, body_text, body_html if body_html else None)
        sender_email = get_sender_info()["email"]

        # Build untracked sender copy if this email has a pixel version
        body_html_no_pixel = lead.get("email_body_html_no_pixel", "")
        has_pixel = lead.get("pixel_tracking", False) and body_html_no_pixel

        server = _create_connection()
        # Send to customer only (tracked MIME)
        server.sendmail(sender_email, [actual_to], msg.as_string())
        server.quit()

        _save_to_sent(msg)

        # ── Tracking activation ──────────────────────────
        tracking_token = lead.get("_tracking_token", "")
        tracking_hash = lead.get("_tracking_token_hash", "")
        tracking_msg_id = lead.get("_tracking_message_id", "")
        if has_pixel and tracking_hash and tracking_msg_id:
            _activate_tracking(tracking_hash, tracking_msg_id, lead_id)

        # ── Sender copy (untracked, separate MIME) ───────
        sender_copy_sent = False
        if sender_email != actual_to:
            try:
                sc = _build_email(sender_email, subject, body_text, body_html_no_pixel if body_html_no_pixel else None)
                sc["X-Roktandrazo-Type"] = "sender_copy"
                sc_server = _create_connection()
                sc_server.sendmail(sender_email, [sender_email], sc.as_string())
                sc_server.quit()
                sender_copy_sent = True
            except Exception as sce:
                # Sender copy failure must not affect customer send
                pass

        # Extract metadata
        message_id = msg.get("Message-ID", "")
        template_id = lead.get("template_id", "")
        customer_type = lead.get("customer_type", "")
        routing_reason = lead.get("routing_reason", "")
        batch_id = lead.get("batch_id", "")
        source_platform = lead.get("source_platform", "")

        if test_cfg["test_mode"] and test_cfg["test_email"]:
            # Redirected test mail must not become customer outreach history or
            # consume the customer's immutable Final Send Plan entry.
            log_send(None, actual_to, subject, "sent",
                     message_id=message_id, template_id=template_id,
                     customer_type=customer_type, routing_reason=routing_reason,
                     batch_id=batch_id, source_platform=source_platform,
                     message_type='test', outreach_batch_date=outreach_batch_date,
                     plan_entry_id=None)
            return {"success": True, "message": f"Test sent to {actual_to}", "status": "test"}

        if plan_entry_id and message_type in ('new_outreach', 'follow_up') and outreach_batch_date:
            return {"success": True, "message": f"Sent to {actual_to}", "status": "sent"}

        now = datetime.now().isoformat()
        update_lead_status(lead_id, "sent", sent_at=now)
        log_send(lead_id, email, subject, "sent",
                  message_id=message_id, template_id=template_id,
                  customer_type=customer_type, routing_reason=routing_reason,
                  batch_id=batch_id, source_platform=source_platform,
                  message_type=message_type, outreach_batch_date=outreach_batch_date,
                  plan_entry_id=plan_entry_id)

        return {"success": True, "message": f"Sent to {actual_to}", "status": "sent"}

    except smtplib.SMTPRecipientsRefused as e:
        if test_cfg["test_mode"] and test_cfg["test_email"]:
            return {"success": False, "message": f"Test recipient refused: {e}", "status": "test_failed"}
        update_lead_status(lead_id, "failed", error_message=str(e))
        log_send(lead_id, email, subject, "failed", str(e))
        return {"success": False, "message": f"Recipient refused: {e}", "status": "failed"}

    except smtplib.SMTPDataError as e:
        error_str = str(e)
        if test_cfg["test_mode"] and test_cfg["test_email"]:
            return {"success": False, "message": f"Test SMTP error: {e}", "status": "test_failed"}
        if "550" in error_str or "bounce" in error_str.lower():
            update_lead_status(lead_id, "bounced", bounced_at=datetime.now().isoformat(), error_message=error_str)
            add_to_suppression(email, "bounced")
            log_send(lead_id, email, subject, "bounced", error_str)
            return {"success": False, "message": f"Bounced: {e}", "status": "bounced"}
        update_lead_status(lead_id, "failed", error_message=error_str)
        log_send(lead_id, email, subject, "failed", error_str)
        return {"success": False, "message": f"SMTP error: {e}", "status": "failed"}

    except Exception as e:
        if test_cfg["test_mode"] and test_cfg["test_email"]:
            return {"success": False, "message": f"Test send error: {e}", "status": "test_failed"}
        update_lead_status(lead_id, "failed", error_message=str(e))
        log_send(lead_id, email, subject, "failed", str(e))
        return {"success": False, "message": f"Error: {e}", "status": "failed"}


def batch_send(leads: list[dict], dry_run: bool = False) -> list[dict]:
    limits = get_sending_limits()
    max_send = limits["max_per_batch"]
    delay = limits["delay_seconds"]

    results = []
    sent_count = 0

    for lead in leads:
        if sent_count >= max_send and not dry_run:
            results.append({"lead_id": lead.get("id"), "success": False, "message": "Batch limit reached", "status": "skipped"})
            continue

        result = send_one(lead, dry_run=dry_run)
        result["lead_id"] = lead.get("id")
        result["store_name"] = lead.get("store_name")
        result["email"] = lead.get("email")
        results.append(result)

        if result["success"] and result["status"] == "sent":
            sent_count += 1
            if not dry_run and sent_count < max_send:
                time.sleep(delay)

    return results
