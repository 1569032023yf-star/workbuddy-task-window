"""
Roktandrazo BD Outreach - Email Sender (Closed-Loop)
通过腾讯企业邮箱 SMTP 发信，从 .env 读取配置
支持 HTML + 纯文本双格式，Reply-To 头
"""

import imaplib
import smtplib
import ssl
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid

from env_loader import get_smtp_config, get_sender_info, get_sending_limits, get_test_config, get_imap_config, is_configured, mask
from bd_db import update_lead_status, log_send, add_to_suppression, is_suppressed


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

    # Validation
    if not email:
        return {"success": False, "message": "No email", "status": "failed"}

    if is_suppressed(email):
        return {"success": False, "message": "Email is suppressed", "status": "skipped"}

    if not subject or not body_text:
        return {"success": False, "message": "Missing email_subject or email_body", "status": "failed"}

    if not is_configured():
        return {"success": False, "message": "SMTP not configured", "status": "failed"}

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

    # Test mode: redirect to test email, add [TEST] tag
    test_cfg = get_test_config()
    actual_to = email
    if test_cfg["test_mode"] and test_cfg["test_email"]:
        actual_to = test_cfg["test_email"]
        subject = f"[TEST->{email}] {subject}"

    # Build and send
    try:
        msg = _build_email(actual_to, subject, body_text, body_html if body_html else None)
        sender_email = get_sender_info()["email"]
        server = _create_connection()
        # BCC a copy to self so it appears in the sender's Inbox
        server.sendmail(sender_email, [actual_to, sender_email], msg.as_string())
        server.quit()

        # Save a copy to the Sent folder via IMAP (secondary)
        _save_to_sent(msg)

        now = datetime.now().isoformat()
        update_lead_status(lead_id, "sent", sent_at=now)
        log_send(lead_id, email, subject, "sent")

        return {"success": True, "message": f"Sent to {actual_to}", "status": "sent"}

    except smtplib.SMTPRecipientsRefused as e:
        update_lead_status(lead_id, "failed", error_message=str(e))
        log_send(lead_id, email, subject, "failed", str(e))
        return {"success": False, "message": f"Recipient refused: {e}", "status": "failed"}

    except smtplib.SMTPDataError as e:
        error_str = str(e)
        if "550" in error_str or "bounce" in error_str.lower():
            update_lead_status(lead_id, "bounced", bounced_at=datetime.now().isoformat(), error_message=error_str)
            add_to_suppression(email, "bounced")
            log_send(lead_id, email, subject, "bounced", error_str)
            return {"success": False, "message": f"Bounced: {e}", "status": "bounced"}
        update_lead_status(lead_id, "failed", error_message=error_str)
        log_send(lead_id, email, subject, "failed", error_str)
        return {"success": False, "message": f"SMTP error: {e}", "status": "failed"}

    except Exception as e:
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
