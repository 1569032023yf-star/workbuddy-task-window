"""Persistence boundary for immutable pre-send plans."""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime

from outreach_control import build_final_plan_entries


PLAN_COLUMNS = (
    "plan_id, lead_id, recipient_email, company_name, customer_type, lead_segment, template_id, "
    "source_city, source_state, evidence_url, hygiene_passed_at, message_type, outreach_batch_date, "
    "planned_sequence, subject, body_text, body_html"
)


def create_plan(conn: sqlite3.Connection, leads: list[dict], batch_date: str, message_type: str) -> str:
    entries = build_final_plan_entries(leads, batch_date, message_type)
    plan_id = f"{batch_date}:{message_type}:{uuid.uuid4().hex[:10]}"
    values = [tuple([plan_id] + [entry[key] for key in (
        "lead_id", "recipient_email", "company_name", "customer_type", "lead_segment", "template_id",
        "source_city", "source_state", "evidence_url", "hygiene_passed_at", "message_type",
        "outreach_batch_date", "planned_sequence", "subject", "body_text", "body_html",
    )]) for entry in entries]
    if not values:
        return ""
    conn.executemany(
        f"INSERT INTO final_send_plan ({PLAN_COLUMNS}) VALUES ({','.join('?' for _ in range(17))})", values
    )
    return plan_id


def load_planned_entries(conn: sqlite3.Connection, batch_date: str) -> list[dict]:
    rows = conn.execute("""
        SELECT * FROM final_send_plan WHERE outreach_batch_date=? AND status='planned'
        ORDER BY CASE message_type WHEN 'follow_up' THEN 0 ELSE 1 END, planned_sequence
    """, (batch_date,)).fetchall()
    return [dict(row) for row in rows]


def mark_entry(conn: sqlite3.Connection, entry_id: int, status: str, reason: str = "") -> None:
    sent_at = datetime.now().isoformat() if status == "sent" else None
    conn.execute("UPDATE final_send_plan SET status=?, skip_reason=?, sent_at=COALESCE(?, sent_at) WHERE id=?",
                 (status, reason, sent_at, entry_id))
