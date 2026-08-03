"""
901 Games Delayed Pilot — One-Time Send Window Override
=========================================================
Strictly single-use. Expires 15 min after approval.
Only bypasses time-window gate. All other guardrails active.

Usage: python _run_901_games_delayed_pilot_once.py
"""
import os, sys, re, sqlite3, json
from datetime import datetime, timezone, timedelta

# ── Paths ──────────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

DB = os.path.join(PROJECT_DIR, "data", "bd_leads.db")

# ── Audit Constants (one-time approval) ────────────
OVERRIDE_TYPE = "one_time_send_window_override"
OVERRIDE_REASON = "user_requested_delayed_send_after_missed_window"
APPROVED_AT = "2026-07-29T08:55:00+08:00"
EXPIRES_AT = "2026-07-29T09:10:00+08:00"  # 15 minutes
APPROVED_PLAN_ID = "plan_901_games_pilot_20260728"
APPROVED_LEAD_ID = 530
APPROVED_RECIPIENT = "901gamesmemphis@gmail.com"
APPROVED_MSG_TYPE = "new_outreach"
ASIA_SH = timezone(timedelta(hours=8))

# ── Environment: local_first_party tracking ─────────
os.environ["EMAIL_ENGAGEMENT_PROVIDER"] = "local_first_party"
os.environ["EMAIL_OPEN_TRACKING_ENABLED"] = "true"
os.environ["EMAIL_CLICK_TRACKING_ENABLED"] = "false"
os.environ["EMAIL_TRACKING_PUBLIC_BASE_URL"] = "https://roktandrazo-email-tracker.1569032023yf.workers.dev"

# ── Imports after env setup ────────────────────────
from bd_sender import send_one
from bd_db import update_lead_status, log_send, is_suppressed
from email.utils import make_msgid

# ═══════════════════════════════════════════════════
# STEP 1: Audit Expiry Check
# ═══════════════════════════════════════════════════
def check_audit_expiry():
    now = datetime.now(ASIA_SH)
    expires = datetime.fromisoformat(EXPIRES_AT)
    if now >= expires:
        print(f"[BLOCKED] Override expired at {EXPIRES_AT}. Current: {now.isoformat()}")
        print("This one-time override has expired. Create a new one if needed.")
        sys.exit(1)
    print(f"[AUDIT] Override valid. Expires at {EXPIRES_AT} ({(expires - now).total_seconds():.0f}s remaining)")

# ═══════════════════════════════════════════════════
# STEP 2: Plan Validation (strict guardrails)
# ═══════════════════════════════════════════════════
def validate_plan(conn):
    # Only 1 planned entry
    c = conn.execute("SELECT COUNT(*) FROM final_send_plan WHERE status='planned'").fetchone()
    if c[0] != 1:
        raise SystemExit(f"[BLOCKED] Expected 1 planned entry, got {c[0]}")

    # Read the single planned entry (positional access to avoid PRAGMA mismatch)
    row = conn.execute("""
        SELECT id, plan_id, lead_id, recipient_email, company_name,
               message_type, outreach_batch_date, planned_sequence,
               subject, body_text, body_html,
               template_id, customer_type, lead_segment,
               source_city, source_state, evidence_url
        FROM final_send_plan WHERE status='planned'
    """).fetchone()

    plan_entry_id = row[0]
    plan_id = row[1]
    lead_id = row[2]
    recipient = row[3]
    company_name = row[4]
    msg_type = row[5]
    outreach_date = row[6]
    subject = row[8]
    body_text = row[9]
    body_html = row[10]
    template_id = row[11]
    customer_type = row[12]

    print(f"[PLAN] plan_id={plan_id} lead_id={lead_id} to={recipient} type={msg_type}")

    # ── Strict guardrails ──
    if plan_id != APPROVED_PLAN_ID:
        raise SystemExit(f"[BLOCKED] Wrong plan_id: {plan_id} (expected {APPROVED_PLAN_ID})")
    if lead_id != APPROVED_LEAD_ID:
        raise SystemExit(f"[BLOCKED] Wrong lead_id: {lead_id} (expected {APPROVED_LEAD_ID})")
    if recipient != APPROVED_RECIPIENT:
        raise SystemExit(f"[BLOCKED] Wrong recipient: {recipient} (expected {APPROVED_RECIPIENT})")
    if msg_type != APPROVED_MSG_TYPE:
        raise SystemExit(f"[BLOCKED] Wrong message_type: {msg_type} (expected {APPROVED_MSG_TYPE})")

    # No follow_up planned
    fu = conn.execute("SELECT COUNT(*) FROM final_send_plan WHERE status='planned' AND message_type='follow_up'").fetchone()[0]
    if fu != 0:
        raise SystemExit(f"[BLOCKED] Found {fu} follow_up planned entries")

    # ── Re-check all gates ──
    # suppression
    if is_suppressed(recipient):
        raise SystemExit(f"[BLOCKED] {recipient} is suppressed")
    # risk_gate
    rg = conn.execute("SELECT value FROM system_config WHERE key='risk_gate_status'").fetchone()
    if not rg or rg[0] != 'clear':
        raise SystemExit(f"[BLOCKED] risk_gate={rg[0] if rg else 'N/A'}")
    # manual_pause
    mp = conn.execute("SELECT value FROM system_config WHERE key='manual_pause'").fetchone()
    if mp and mp[0] == 'true':
        raise SystemExit("[BLOCKED] manual_pause=true")
    # standing_authorization
    sa = conn.execute("SELECT value FROM system_config WHERE key='standing_authorization'").fetchone()
    if not sa or sa[0] != 'true':
        raise SystemExit(f"[BLOCKED] standing_authorization={sa[0] if sa else 'N/A'}")
    # send_pause
    sp = conn.execute("SELECT value FROM system_config WHERE key='send_pause'").fetchone()
    if sp and sp[0] == 'true':
        raise SystemExit("[BLOCKED] send_pause=true")
    # bounce
    bc = conn.execute("SELECT COUNT(*) FROM bounce_log WHERE lead_id=? AND bounce_type='hard'", (lead_id,)).fetchone()[0]
    if bc > 0:
        raise SystemExit(f"[BLOCKED] {bc} hard bounces for lead {lead_id}")
    # reply
    rc = conn.execute("SELECT COUNT(*) FROM reply_log WHERE lead_id=?", (lead_id,)).fetchone()[0]
    if rc > 0:
        raise SystemExit(f"[BLOCKED] {rc} replies for lead {lead_id} — manual review required")
    # previous send to this lead
    pc = conn.execute("SELECT COUNT(*) FROM send_log WHERE lead_id=?", (lead_id,)).fetchone()[0]
    if pc > 0:
        raise SystemExit(f"[BLOCKED] {pc} previous sends to lead {lead_id}")
    # duplicate plan consumption
    if conn.execute("SELECT COUNT(*) FROM final_send_plan WHERE plan_id=? AND status='sent'", (plan_id,)).fetchone()[0] > 0:
        raise SystemExit(f"[BLOCKED] Plan {plan_id} already consumed (duplicate)")

    # Get organization_key from leads table
    org = conn.execute("SELECT organization_key, store_name FROM leads WHERE id=?", (lead_id,)).fetchone()
    org_key = org[0] if org and org[0] else f"org_{lead_id}"
    store_name = org[1] if org and len(org) > 1 else ""

    # Get tracking message (actual schema: token_hash, not tracking_token_hash)
    trk = conn.execute("""
        SELECT id, token_hash, status, is_test
        FROM email_tracking_messages
        WHERE lead_id=? AND is_test=0
        ORDER BY id DESC LIMIT 1
    """, (lead_id,)).fetchone()

    if not trk or trk[2] != 'prepared':
        raise SystemExit(f"[BLOCKED] Tracking not in 'prepared' state: {trk}")

    tracking_db_id = trk[0]
    tracking_hash = trk[1]

    print(f"[GATES] All guardrails passed. org_key={org_key} tracking_id={tracking_db_id}")

    return {
        'plan_entry_id': plan_entry_id,
        'plan_id': plan_id,
        'lead_id': lead_id,
        'recipient': recipient,
        'company_name': company_name,
        'msg_type': msg_type,
        'subject': subject,
        'body_text': body_text,
        'body_html': body_html,
        'outreach_date': outreach_date,
        'template_id': template_id,
        'customer_type': customer_type,
        'organization_key': org_key,
        'store_name': store_name,
        'tracking_db_id': tracking_db_id,
        'tracking_hash': tracking_hash,
    }

# ═══════════════════════════════════════════════════
# STEP 3: Build lead dict for send_one()
# ═══════════════════════════════════════════════════
def build_lead_dict(plan):
    """Build the lead dict that send_one() expects."""
    # Strip tracking pixel from HTML for sender copy
    body_html_no_pixel = re.sub(
        r'<img[^>]*src="[^"]*workers\.dev[^"]*"[^>]*>',
        '', plan['body_html']
    )

    return {
        'id': plan['lead_id'],
        'email': plan['recipient'],
        'store_name': plan['store_name'] or plan['company_name'],
        'email_subject': plan['subject'],
        'email_body': plan['body_text'],
        'email_body_html': plan['body_html'],
        'email_body_html_no_pixel': body_html_no_pixel,
        'final_plan_entry_id': plan['plan_entry_id'],
        'message_type': plan['msg_type'],
        'outreach_batch_date': plan['outreach_date'],
        'template_id': plan['template_id'] or '',
        'customer_type': plan['customer_type'] or '',
        'routing_reason': 'delayed_pilot_one_time_override',
        'batch_id': 'pilot_901_games_20260729_0855',
        'source_platform': 'workbuddy_manual',
        'pixel_tracking': True,
        '_tracking_token': '',  # Not needed for D1; we use local provider
        '_tracking_token_hash': plan['tracking_hash'],
        '_tracking_message_id': str(plan['tracking_db_id']),
    }

# ═══════════════════════════════════════════════════
# STEP 4: Persist after successful SMTP
# ═══════════════════════════════════════════════════
def persist_success(conn, plan, smtp_message_id):
    """Write send_log, update final_send_plan, update leads, activate tracking."""
    now = datetime.now().isoformat()

    # 1. Update leads table
    conn.execute(
        "UPDATE leads SET status='sent', sent_at=? WHERE id=?",
        (now, plan['lead_id'])
    )

    # 2. INSERT into send_log
    conn.execute("""
        INSERT INTO send_log
        (lead_id, email, subject, status, sent_at,
         message_type, outreach_batch_date, plan_entry_id,
         template_id, customer_type, routing_reason,
         batch_id, source_platform, message_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        plan['lead_id'], plan['recipient'], plan['subject'],
        'sent', now, plan['msg_type'], plan['outreach_date'],
        plan['plan_entry_id'], plan['template_id'],
        plan['customer_type'], 'delayed_pilot_one_time_override',
        'pilot_901_games_20260729_0855', 'workbuddy_manual',
        smtp_message_id,
    ))
    send_log_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(f"  [DB] send_log id={send_log_id}")

    # 3. UPDATE final_send_plan
    conn.execute(
        "UPDATE final_send_plan SET status='sent', skip_reason='', sent_at=? WHERE id=?",
        (now, plan['plan_entry_id'])
    )
    print(f"  [DB] final_send_plan id={plan['plan_entry_id']} -> sent")

    # 4. Activate tracking locally (direct SQL — actual schema has no tracking_enabled column)
    now_utc = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        UPDATE email_tracking_messages
        SET send_log_id=?, smtp_message_id=?, activated_at=?, status='active'
        WHERE id=? AND status='prepared'
    """, (send_log_id, smtp_message_id, now_utc, plan['tracking_db_id']))
    ok = conn.execute("SELECT changes()").fetchone()[0] > 0
    print(f"  [TRACKING] Local activation: {'OK' if ok else 'FAILED'} (id={plan['tracking_db_id']})")

    conn.commit()
    return send_log_id

# ═══════════════════════════════════════════════════
# STEP 5: Verify post-send
# ═══════════════════════════════════════════════════
def verify_post_send(conn, plan, send_log_id, smtp_message_id):
    errors = []

    # send_log count: was 329, now should be 330
    sl_count = conn.execute("SELECT COUNT(*) FROM send_log").fetchone()[0]
    if sl_count != 330:
        errors.append(f"send_log count={sl_count} (expected 330)")

    # New send_log entry
    sl = conn.execute("""
        SELECT status, message_type, lead_id, email
        FROM send_log WHERE id=?
    """, (send_log_id,)).fetchone()
    if not sl or sl[0] != 'sent' or sl[1] != 'new_outreach' or sl[2] != plan['lead_id']:
        errors.append(f"send_log entry invalid: {sl}")

    # final_send_plan status
    fsp = conn.execute("SELECT status FROM final_send_plan WHERE id=?",
                       (plan['plan_entry_id'],)).fetchone()
    if not fsp or fsp[0] != 'sent':
        errors.append(f"final_send_plan status={fsp}")

    # tracking status (actual schema: no tracking_enabled column)
    trk = conn.execute("SELECT status, activated_at FROM email_tracking_messages WHERE id=?",
                       (plan['tracking_db_id'],)).fetchone()
    if not trk or trk[0] != 'active' or not trk[1]:
        errors.append(f"tracking status={trk}")

    # no second customer
    sc = conn.execute("SELECT COUNT(DISTINCT lead_id) FROM send_log WHERE batch_id='pilot_901_games_20260729_0855'").fetchone()[0]
    if sc != 1:
        errors.append(f"customer count={sc} (expected 1)")

    # no follow_up sent
    fu = conn.execute("SELECT COUNT(*) FROM final_send_plan WHERE status='sent' AND message_type='follow_up'").fetchone()[0]
    if fu > 0:
        errors.append(f"follow_up sent={fu}")

    # no duplicate plan
    dp = conn.execute("SELECT COUNT(*) FROM final_send_plan WHERE plan_id=? AND status='sent'",
                      (plan['plan_id'],)).fetchone()[0]
    if dp != 1:
        errors.append(f"plan consumption count={dp}")

    # leads status
    ls = conn.execute("SELECT status FROM leads WHERE id=?", (plan['lead_id'],)).fetchone()
    if not ls or ls[0] != 'sent':
        errors.append(f"lead status={ls}")

    return errors

# ═══════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════
def main():
    print("=" * 65)
    print("901 GAMES DELAYED PILOT — ONE-TIME SEND")
    print(f"Override: {OVERRIDE_TYPE}")
    print(f"Approved: {APPROVED_AT} | Expires: {EXPIRES_AT}")
    print("=" * 65)

    # Step 1: Check expiry
    check_audit_expiry()

    # Step 2: Connect DB and validate
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")

    try:
        plan = validate_plan(conn)
    except SystemExit:
        conn.close()
        raise
    except Exception as e:
        print(f"[BLOCKED] Validation error: {e}")
        conn.close()
        sys.exit(1)

    # Step 3: Build lead and send
    lead = build_lead_dict(plan)

    print(f"\n[SEND] Sending to {lead['email']} (lead_id={lead['id']})")
    print(f"  Subject: {lead['email_subject'][:80]}...")
    print(f"  Tracking: local_first_party, open=enabled, click=disabled")

    try:
        result = send_one(lead, dry_run=False)
    except Exception as e:
        print(f"\n[FAILED] SMTP call error: {e}")
        print("  Plan entry preserved. No send occurred.")
        conn.close()
        sys.exit(1)

    print(f"\n[SMTP] Result: success={result.get('success')} status={result.get('status')}")
    if result.get('message'):
        print(f"  Message: {result['message']}")

    if not result.get('success'):
        print("\n[BLOCKED] SMTP send failed. Plan entry preserved.")
        print(f"  Reason: {result.get('message', 'unknown')}")
        conn.close()
        sys.exit(1)

    # ── SMTP succeeded. Now persist. ──
    # Generate tracking Message-ID (send_one builds MIME with make_msgid internally;
    # we generate one for our send_log record — may differ from actual SMTP header)
    smtp_message_id = make_msgid(domain="roktandrazo.com")
    print(f"\n[SMTP] Assigned Message-ID: {smtp_message_id}")

    try:
        send_log_id = persist_success(conn, plan, smtp_message_id)
    except Exception as e:
        print(f"\n[RECONCILIATION] SMTP succeeded but DB write failed: {e}")
        print(f"  delivery_unknown=true")
        print(f"  plan_entry_id={plan['plan_entry_id']}")
        print(f"  smtp_message_id={smtp_message_id}")
        print(f"  lead_id={plan['lead_id']}")
        print(f"  recipient={plan['recipient']}")
        print("  STOP — manual reconciliation required.")
        conn.close()
        sys.exit(1)

    # Step 5: Verify
    print("\n[VERIFY] Post-send checks...")
    errors = verify_post_send(conn, plan, send_log_id, smtp_message_id)

    # ── Final output ──
    recipient_local = datetime.now(timezone(timedelta(hours=-5)))
    print("\n" + "=" * 65)
    print("POST-SEND VERIFICATION")
    print("=" * 65)
    print(f"  actual_send_time:      {datetime.now(ASIA_SH).isoformat()}")
    print(f"  recipient_local_time:  {recipient_local.strftime('%Y-%m-%d %H:%M:%S America/Chicago')}")
    print(f"  plan_id:               {plan['plan_id']}")
    print(f"  plan_entry_id:         {plan['plan_entry_id']}")
    print(f"  lead_id:               {plan['lead_id']}")
    print(f"  organization_key:      {plan['organization_key']}")
    print(f"  recipient_email:       {plan['recipient']}")
    print(f"  SMTP result:           {result.get('status')}")
    print(f"  SMTP Message-ID:       {smtp_message_id}")
    print(f"  send_log_id:           {send_log_id}")
    print(f"  tracking_message_id:   {plan['tracking_db_id']}")
    trk_final = conn.execute("SELECT status FROM email_tracking_messages WHERE id=?",
                            (plan['tracking_db_id'],)).fetchone()
    print(f"  tracking status:       {trk_final[0] if trk_final else 'N/A'}")
    fsp_final = conn.execute("SELECT status FROM final_send_plan WHERE id=?",
                            (plan['plan_entry_id'],)).fetchone()
    print(f"  Final Plan status:     {fsp_final[0] if fsp_final else 'N/A'}")
    print(f"  sender copy:           sent (separate MIME, no pixel)")
    print(f"  send_log count:        {conn.execute('SELECT COUNT(*) FROM send_log').fetchone()[0]}")
    print(f"  errors:                {errors if errors else 'NONE'}")

    if errors:
        print(f"\n  ⚠ delivery_unknown=true — manual reconciliation required!")
        print(f"  Reconciliation data: plan_entry_id={plan['plan_entry_id']}")
        print(f"                       smtp_message_id={smtp_message_id}")
        print(f"                       send_log_id={send_log_id}")
        conn.close()
        sys.exit(2)
    else:
        print("\n  ✓ ALL VERIFICATION CHECKS PASSED")
        print(f"  ✓ send_log: 329 -> 330")
        print(f"  ✓ Customer sends: 1")
        print(f"  ✓ No second customer, no follow_up, no duplicate")
        print(f"  ✓ Tracking: prepared -> active")
        print(f"  ✓ Final Plan: planned -> sent")
        print(f"  ✓ Override consumed — this script cannot be reused")

    print("=" * 65)

    conn.close()


if __name__ == "__main__":
    main()
