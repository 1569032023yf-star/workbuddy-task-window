"""
Roktandrazo BD Outreach - Database (Closed-Loop Version + Manual Fields)
支持完整闭环：收集 → 草稿 → 审核 → 发送 → 回复/退信/退订 → 状态更新
v2.0: 新增 manual_ 字段、approved_manual_send 池、发送前检查
"""

import sqlite3
import os
import re as _re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "bd_leads.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    # ---- 主线索表（CREATE 用于新库，ALTER 向下兼容旧库） ----
    c.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_name TEXT NOT NULL,
        store_type TEXT,
        city TEXT,
        state TEXT,
        official_website TEXT,
        contact_page TEXT,
        wholesale_or_vendor_page TEXT,
        email TEXT,
        email_type TEXT,
        contact_form_url TEXT,
        evidence_url TEXT,
        source_keyword TEXT,
        fit_reason TEXT,
        product_fit TEXT,
        confidence_score TEXT,
        status TEXT DEFAULT 'new',
        email_subject TEXT,
        email_body TEXT,
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_checked_at TIMESTAMP,
        sent_at TIMESTAMP,
        replied_at TIMESTAMP,
        bounced_at TIMESTAMP,
        unsubscribed_at TIMESTAMP,
        last_followup_at TIMESTAMP,
        followup_count INTEGER DEFAULT 0,
        notes TEXT,
        error_message TEXT,
        domain_hash TEXT,
        email_source_type TEXT DEFAULT 'unknown',
        email_verified_on_official_site INTEGER DEFAULT 0,
        mx_provider TEXT DEFAULT '',
        campaign TEXT DEFAULT '',
        template_id TEXT DEFAULT '',
        priority TEXT DEFAULT 'normal',
        UNIQUE(domain_hash)
    )
    """)

    # --- 安全迁移：添加 manual_ 列（如果不存在） ---
    _migrate_manual_columns(c)

    c.execute("""
    CREATE TABLE IF NOT EXISTS suppression_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        reason TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS send_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        email TEXT,
        subject TEXT,
        status TEXT,
        error_message TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lead_id) REFERENCES leads(id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS bounce_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        email TEXT,
        domain TEXT,
        campaign TEXT,
        bounce_received_at TEXT,
        status_code TEXT,
        diag TEXT,
        bounce_type TEXT DEFAULT 'unknown',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    for idx in [
        "CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)",
        "CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(confidence_score)",
        "CREATE INDEX IF NOT EXISTS idx_leads_domain ON leads(domain_hash)",
        "CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)",
        "CREATE INDEX IF NOT EXISTS idx_send_log_lead ON send_log(lead_id)",
        "CREATE INDEX IF NOT EXISTS idx_suppression_email ON suppression_list(email)",
        "CREATE INDEX IF NOT EXISTS idx_bounce_email ON bounce_log(email)",
    ]:
        try:
            c.execute(idx)
        except Exception:
            pass

    conn.commit()
    conn.close()
    print("[DB] Database initialized (v2.0 with manual fields)")


def _migrate_manual_columns(c):
    """Add manual_ columns if they don't already exist (safe migration)."""
    c.execute("PRAGMA table_info(leads)")
    existing = {row[1] for row in c.fetchall()}
    manual_cols = [
        ("manual_found_email", "TEXT"),
        ("manual_email_source_url", "TEXT"),
        ("manual_email_source_type", "TEXT"),
        ("manual_decision", "TEXT"),
        ("manual_note", "TEXT"),
        ("manual_verified_by", "TEXT DEFAULT 'user'"),
        ("manual_verified_at", "TIMESTAMP"),
    ]
    for col_name, col_type in manual_cols:
        if col_name not in existing:
            try:
                c.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
                print(f"  [MIGRATE] Added column: {col_name}")
            except Exception as e:
                print(f"  [MIGRATE] Warning adding {col_name}: {e}")
    c.execute("PRAGMA table_info(leads)")
    final_cols = {row[1] for row in c.fetchall()}
    all_manual = [c for c in final_cols if c.startswith("manual_")]
    print(f"  [MIGRATE] Manual columns present: {all_manual}")


def _domain_hash(website: str) -> str:
    if not website:
        return ""
    domain = website.lower().strip()
    domain = domain.replace("https://", "").replace("http://", "").replace("www.", "")
    domain = domain.split("/")[0].split("?")[0].split("#")[0]
    return domain


def insert_lead(lead: dict) -> int | None:
    conn = get_db()
    c = conn.cursor()
    website = lead.get("official_website", "")
    domain = _domain_hash(website)
    if not domain:
        domain = f"{lead.get('store_name', '').lower().strip()}_{lead.get('city', '').lower().strip()}"
    try:
        c.execute("""
        INSERT OR IGNORE INTO leads
        (store_name, store_type, city, state, official_website, contact_page,
         wholesale_or_vendor_page, email, email_type, contact_form_url, evidence_url,
         source_keyword, fit_reason, product_fit, confidence_score, status, notes, domain_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead.get("store_name"), lead.get("store_type"),
            lead.get("city"), lead.get("state"),
            lead.get("official_website"), lead.get("contact_page"),
            lead.get("wholesale_or_vendor_page"),
            lead.get("email"), lead.get("email_type"),
            lead.get("contact_form_url"), lead.get("evidence_url"),
            lead.get("source_keyword"), lead.get("fit_reason"),
            lead.get("product_fit"), lead.get("confidence_score"),
            lead.get("status", "new"), lead.get("notes"), domain,
        ))
        conn.commit()
        if c.lastrowid and c.rowcount > 0:
            print(f"  [+] {lead.get('store_name')} ({lead.get('city')}, {lead.get('state')})")
            return c.lastrowid
        return None
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_leads_by_status(status: str, limit: int = 100) -> list[dict]:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM leads WHERE status = ? ORDER BY confidence_score ASC, collected_at DESC LIMIT ?", (status, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_approved_leads(limit: int = 5) -> list[dict]:
    """Get leads ready to send (approved, has email, not suppressed, not already sent)"""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    SELECT * FROM leads
    WHERE status = 'approved'
    AND email IS NOT NULL AND email != ''
    AND email NOT IN (SELECT email FROM suppression_list)
    AND id NOT IN (SELECT lead_id FROM send_log WHERE status = 'sent')
    ORDER BY confidence_score ASC
    LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_lead_status(lead_id: int, status: str, **kwargs):
    """Update lead status and optional fields"""
    conn = get_db()
    c = conn.cursor()
    fields = ["status = ?", "last_checked_at = ?"]
    values = [status, datetime.now().isoformat()]

    for key in ["email_subject", "email_body", "sent_at", "replied_at",
                "bounced_at", "unsubscribed_at", "last_followup_at",
                "followup_count", "error_message", "notes"]:
        if key in kwargs:
            fields.append(f"{key} = ?")
            values.append(kwargs[key])

    values.append(lead_id)
    c.execute(f"UPDATE leads SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()


def add_to_suppression(email: str, reason: str = "unsubscribed"):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO suppression_list (email, reason) VALUES (?, ?)", (email, reason))
    conn.commit()
    conn.close()


def is_suppressed(email: str) -> bool:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM suppression_list WHERE email = ?", (email,))
    result = c.fetchone()[0] > 0
    conn.close()
    return result


def log_send(lead_id: int, email: str, subject: str, status: str, error_message: str = None):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    INSERT INTO send_log (lead_id, email, subject, status, error_message)
    VALUES (?, ?, ?, ?, ?)
    """, (lead_id, email, subject, status, error_message))
    conn.commit()
    conn.close()


def get_stats() -> dict:
    conn = get_db()
    c = conn.cursor()
    stats = {}
    c.execute("SELECT COUNT(*) FROM leads"); stats["total"] = c.fetchone()[0]
    c.execute("SELECT status, COUNT(*) FROM leads GROUP BY status"); stats["by_status"] = dict(c.fetchall())
    c.execute("SELECT confidence_score, COUNT(*) FROM leads GROUP BY confidence_score"); stats["by_score"] = dict(c.fetchall())
    c.execute("SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND email != ''"); stats["with_email"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM suppression_list"); stats["suppressed"] = c.fetchone()[0]
    c.execute("SELECT status, COUNT(*) FROM send_log GROUP BY status"); stats["send_log"] = dict(c.fetchall())
    conn.close()
    return stats


# ============================================================
# 新增: approved_manual_send 池查询
# ============================================================

def get_approved_manual_send_leads(limit: int = 5) -> list[dict]:
    """Get leads in approved_manual_send status, ready for sending.
    Includes all safety checks: suppression, sent_log, bounce_log.
    """
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    SELECT * FROM leads
    WHERE status = 'approved_manual_send'
    AND email IS NOT NULL AND email != ''
    AND email NOT IN (SELECT email FROM suppression_list)
    AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent', 'bounced'))
    AND id NOT IN (SELECT lead_id FROM bounce_log)
    ORDER BY manual_verified_at ASC, collected_at ASC
    LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_sendable_leads(limit: int = 20, exclude_ids: list = None) -> list[dict]:
    """Get all sendable leads by priority: A0 → A1 → approved_manual_send.
    Includes full safety chain: suppression / sent_log / bounce / Exchange MX.
    Returns up to `limit` leads.
    """
    conn = get_db()
    c = conn.cursor()
    exclude_clause = ""
    if exclude_ids:
        exclude_clause = f"AND id NOT IN ({','.join('?'*len(exclude_ids))})"

    # A0: verified official email, non-Exchange
    a0 = c.execute(f"""
    SELECT * FROM leads
    WHERE status = 'new' AND confidence_score = 'A'
    AND email_verified_on_official_site = 1
    AND email_source_type IN ('official_page_visible','official_mailto','wholesale_vendor_page')
    AND email IS NOT NULL AND email != ''
    AND email NOT IN (SELECT email FROM suppression_list)
    AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent','bounced'))
    AND (mx_provider IS NULL OR mx_provider = '' OR
         (mx_provider NOT LIKE '%exchange%' AND mx_provider NOT LIKE '%outlook%' AND mx_provider NOT LIKE '%microsoft%'))
    {exclude_clause}
    ORDER BY collected_at ASC
    LIMIT ?
    """, (*(exclude_ids or []), limit)).fetchall()

    a0_ids = [r['id'] for r in a0]
    remaining = limit - len(a0)
    result = [dict(r) for r in a0]

    if remaining > 0:
        excl = (exclude_ids or []) + a0_ids
        excl_placeholders = ','.join('?' * len(excl)) if excl else '0'
        # approved_manual_send
        manual = c.execute(f"""
        SELECT * FROM leads
        WHERE status = 'approved_manual_send'
        AND email IS NOT NULL AND email != ''
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent','bounced'))
        AND id NOT IN (SELECT lead_id FROM bounce_log)
        AND id NOT IN ({excl_placeholders})
        ORDER BY manual_verified_at ASC
        LIMIT ?
        """, (*excl, remaining)).fetchall()
        result.extend([dict(r) for r in manual])

    conn.close()
    return result


# ============================================================
# 发送前安全检查
# ============================================================

def check_sent_log(email: str) -> bool:
    """Check if an email has already been sent (based on send_log)."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM send_log WHERE email = ? AND status = 'sent'", (email,))
    result = c.fetchone()[0] > 0
    conn.close()
    return result


def check_domain_sent(domain: str) -> bool:
    """Check if any email from this domain has already been sent."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM send_log WHERE email LIKE ? AND status = 'sent'", (f'%@{domain}',))
    result = c.fetchone()[0] > 0
    conn.close()
    return result


def check_bounce_history(email: str) -> dict:
    """Check bounce history for an email. Returns {'hard': bool, 'policy': bool, 'detail': str}."""
    conn = get_db()
    c = conn.cursor()
    result = {"hard": False, "policy": False, "detail": ""}
    c.execute("SELECT bounce_type, diagnostic_code FROM bounce_log WHERE email = ? ORDER BY bounce_received_at DESC LIMIT 1", (email,))
    row = c.fetchone()
    if row:
        result["hard"] = row[0] == 'hard'
        result["policy"] = row[0] == 'policy'
        result["detail"] = row[1] or ""
    conn.close()
    return result


def check_mx_provider(domain: str) -> str:
    """Check MX provider category for a domain.
    Returns: 'exchange' / 'google' / 'other' / 'no_mx'
    Falls back to empty string if DNS lookup fails (non-blocking).
    """
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, 'MX')
        mx_str = ' '.join([str(x.exchange).lower() for x in answers])
        if any(k in mx_str for k in ['outlook', 'protection.outlook', 'microsoft', 'exchange']):
            return 'exchange'
        elif 'google' in mx_str:
            return 'google'
        return 'other'
    except Exception:
        return 'no_mx'


def is_exchange_mx(email: str) -> bool:
    """Check if the email's MX is Exchange / Microsoft 365 (high bounce risk)."""
    domain = email.split('@')[1] if '@' in email else ''
    if not domain:
        return False
    mx = check_mx_provider(domain)
    return mx == 'exchange'


def update_manual_approval(lead_id: int, manual_fields: dict):
    """Update manual approval fields for a lead. Safe to call multiple times."""
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()
    fields = ["last_checked_at = ?"]
    values = [now]
    for key in ["manual_found_email", "manual_email_source_url", "manual_email_source_type",
                 "manual_decision", "manual_note", "manual_verified_by", "manual_verified_at"]:
        if key in manual_fields:
            fields.append(f"{key} = ?")
            values.append(manual_fields[key])
    if "manual_verified_at" not in manual_fields and "manual_decision" in manual_fields:
        fields.append("manual_verified_at = ?")
        values.append(now)
    values.append(lead_id)
    c.execute(f"UPDATE leads SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()


def get_config(key: str) -> str | None:
    """Get a value from system_config table."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value FROM system_config WHERE key = ?", (key,))
    r = c.fetchone()
    conn.close()
    return r[0] if r else None


def set_config(key: str, value: str):
    """Set a value in system_config table."""
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?, ?, datetime('now'))",
              (key, value))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
