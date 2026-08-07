raise RuntimeError("LEGACY_SMTP_DISABLED: dated send script archived 2026-08-07. Use bd_orchestrator -> daily_session -> bd_sender only.")
#!/usr/bin/env python3
"""
BD Production Send — 2026-08-05
Clean stale → Select candidates → Plan → Auth → SMTP Send
"""
import sqlite3, re, json, hashlib, secrets, os, sys, smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta

ASIA_SH = timezone(timedelta(hours=8))
NOW = datetime.now(ASIA_SH)
NOW_STR = NOW.isoformat()
BATCH_ID = 'new_outreach_20260805_et1000'
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'bd_leads.db')
MAX_SELECT = 20
SEND_LIVE = False  # ARCHIVED 2026-08-07

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bd_template import get_email_for_lead, route_template_for_lead
from broad_outreach_gate import _gen_organization_key
from bd_sender import is_configured, send_one, create_send_authorization

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# ═══════════════════════════════════════════════════════════
# STEP 1: Clean stale auth/plans
# ═══════════════════════════════════════════════════════════
print('=' * 65)
print(f'  BD PRODUCTION SEND — {NOW_STR}')
print(f'  Batch: {BATCH_ID}')
print('=' * 65)

print('\n--- STEP 1: Clean stale auth/plans ---')
c.execute("DELETE FROM final_send_plan WHERE status='CANCELLED'")
c.execute("DELETE FROM final_send_plan WHERE status='planned'")
deleted = c.rowcount
c.execute("UPDATE send_authorizations SET status='revoked' WHERE status='active'")
revoked = c.rowcount
c.execute("DELETE FROM send_authorization_entries WHERE authorization_id IN (SELECT authorization_id FROM send_authorizations WHERE status='revoked')")
conn.commit()
print(f'  Deleted {deleted} stale plans, revoked {revoked} auths')

# ═══════════════════════════════════════════════════════════
# STEP 2: Update poller heartbeat
# ═══════════════════════════════════════════════════════════
print('\n--- STEP 2: Poller heartbeat ---')
ops_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'bd_ops_poller_status.json')
with open(ops_path, 'w') as f:
    json.dump({
        'last_heartbeat': NOW_STR, 'last_ping': NOW_STR,
        'status': 'alive', 'batch_id': BATCH_ID, 'updated_at': NOW_STR
    }, f)
print(f'  Heartbeat refreshed')

# ═══════════════════════════════════════════════════════════
# STEP 3: Build exclusion sets
# ═══════════════════════════════════════════════════════════
print('\n--- STEP 3: Exclusion sets ---')
suppressed = set((r[0] or '').lower() for r in c.execute('SELECT DISTINCT email FROM suppression_list'))
bounced = set((r[0] or '').lower() for r in c.execute(
    "SELECT DISTINCT email FROM bounce_log WHERE LOWER(COALESCE(bounce_type,'')) IN ('hard','policy','permanent','domain','domain_invalid')"))
sent_emails = set((r[0] or '').lower() for r in c.execute("SELECT DISTINCT email FROM send_log WHERE status='sent'"))
sent_orgs = set()
for r in c.execute("""SELECT DISTINCT COALESCE(NULLIF(l.organization_key,''), 'org_fallback_'||l.id) 
    FROM send_log sl JOIN leads l ON sl.lead_id=l.id WHERE sl.status='sent'"""):
    sent_orgs.add(r[0])
neg_reply_ids = set()
try:
    for r in c.execute('SELECT lead_id FROM reply_log'):
        neg_reply_ids.add(r[0])
except:
    pass

invalid_pat = re.compile(
    r'(\.png|\.jpg|\.gif|\.webp|\.svg|\.css|\.js\b|'
    r'sentry\.io|anthropic\.com|noreply|no.reply|donotreply|'
    r'example\.com|^www\.|^xxx@|'
    r'zendesk\.com|wixpress\.com|wix\.com)',
    re.I
)
print(f'  suppressed={len(suppressed)} bounced={len(bounced)} sent_e={len(sent_emails)} sent_o={len(sent_orgs)} neg={len(neg_reply_ids)}')

# ═══════════════════════════════════════════════════════════
# STEP 4: Query & select candidates
# ═══════════════════════════════════════════════════════════
print('\n--- STEP 4: Select candidates ---')
c.execute("""
    SELECT * FROM leads
    WHERE status NOT IN ('sent','bounced','do_not_contact','rejected','failed','delivery_issue','bounce_review','contact_form_pool')
    AND email IS NOT NULL AND email != ''
    AND email LIKE '%@%.%'
    AND unsubscribed_at IS NULL
    AND bounced_at IS NULL
    AND COALESCE(defer_reason,'') = ''
    ORDER BY 
        CASE WHEN state='TN' THEN 0 WHEN state='AR' THEN 1 WHEN state='KY' THEN 2 ELSE 3 END,
        CASE WHEN confidence_score='A' THEN 0 ELSE 1 END,
        collected_at ASC
""")
all_rows = c.fetchall()
print(f'  Raw candidates: {len(all_rows)}')

selected = []
seen_orgs = set()
seen_emails = set()
skip_invalid = skip_suppress = skip_sent = skip_dupe = skip_neg = 0

for row in all_rows:
    if len(selected) >= MAX_SELECT:
        break
    lead = dict(row)
    email = (lead.get('email') or '').strip().lower()
    lead_id = lead['id']

    org_key = (lead.get('organization_key') or '').strip()
    if not org_key:
        org_key = _gen_organization_key(lead)

    if not email or '@' not in email:
        skip_invalid += 1; continue
    if invalid_pat.search(email):
        skip_invalid += 1; continue
    if email in suppressed:
        skip_suppress += 1; continue
    if email in bounced:
        skip_suppress += 1; continue
    if email in sent_emails:
        skip_sent += 1; continue
    if org_key in sent_orgs:
        skip_sent += 1; continue
    if lead_id in neg_reply_ids:
        skip_neg += 1; continue
    if org_key in seen_orgs or email in seen_emails:
        skip_dupe += 1; continue

    selected.append(lead)
    seen_orgs.add(org_key)
    seen_emails.add(email)

print(f'  Selected: {len(selected)} | skip: invalid={skip_invalid} suppress={skip_suppress} sent={skip_sent} dupe={skip_dupe} neg={skip_neg}')

if not selected:
    print('\n*** NO CANDIDATES — EXITING ***')
    conn.close()
    sys.exit(0)

# ═══════════════════════════════════════════════════════════
# STEP 5: Build emails, create plan entries
# ═══════════════════════════════════════════════════════════
print(f'\n--- STEP 5: Plan ({len(selected)} orgs) ---')
state_dist = {}
template_dist = {}

for i, lead in enumerate(selected):
    email_data = get_email_for_lead(lead)
    plan_id = f'{BATCH_ID}_{i+1:04d}'
    st = lead.get('state', '')
    tmpl = email_data.get('template_key', 'unknown')

    state_dist[st] = state_dist.get(st, 0) + 1
    template_dist[tmpl] = template_dist.get(tmpl, 0) + 1

    evidence = lead.get('evidence_url', '') or ''
    c.execute("""INSERT INTO final_send_plan 
        (plan_id, lead_id, company_name, recipient_email, message_type,
         outreach_batch_date, planned_sequence, status, subject, body_text, body_html,
         source_city, source_state, evidence_url, hygiene_passed_at, template_id, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (plan_id, lead['id'], lead.get('store_name', ''), (lead.get('email') or '').strip(),
         'new_outreach', BATCH_ID, i+1, 'planned',
         email_data['subject'], email_data['body_text'], email_data.get('body_html', ''),
         lead.get('city', ''), st, evidence, NOW_STR,
         email_data.get('template_key', ''), NOW_STR))
    print(f'  [{i+1:2d}] {lead["store_name"][:30]:30s} | {lead.get("city",""):15s}, {st} | {tmpl[:25]} | {(lead.get("email") or "")[:35]}')

conn.commit()

# ═══════════════════════════════════════════════════════════
# STEP 6: Create authorization (use bd_sender function)
# ═══════════════════════════════════════════════════════════
print(f'\n--- STEP 6: Authorization ---')
fsp_rows = c.execute("""SELECT id AS fsp_id, lead_id, recipient_email FROM final_send_plan 
    WHERE outreach_batch_date=? AND status='planned' ORDER BY planned_sequence""", (BATCH_ID,)).fetchall()

planned_entries = [
    {'lead_id': p['lead_id'], 'recipient_email': p['recipient_email'], 'message_type': 'new_outreach'}
    for p in fsp_rows
]

auth_result = create_send_authorization(BATCH_ID, BATCH_ID, planned_entries, True, DB_PATH)
AUTH_ID = auth_result['authorization_id']
print(f'  Auth: {AUTH_ID} | entries: {len(fsp_rows)}')

# Update plan entries with authorization_id link
for p in fsp_rows:
    c.execute("""UPDATE final_send_plan SET evidence_url = COALESCE(evidence_url, '') WHERE id = ?""", (p['fsp_id'],))
conn.commit()

# ═══════════════════════════════════════════════════════════
# STEP 7: SMTP Send
# ═══════════════════════════════════════════════════════════
if not SEND_LIVE:
    print('\n--- STEP 7: DRY RUN (SEND_LIVE=False) ---')
    for p in fsp_rows:
        print(f'  [DRY] Would send to {p["recipient_email"]}')
    conn.close()
    sys.exit(0)

print(f'\n--- STEP 7: SMTP Send ---')
if not is_configured():
    print('  *** SMTP NOT CONFIGURED — ABORTING ***')
    conn.close()
    sys.exit(1)

sent_count = 0
fail_count = 0

for p in fsp_rows:
    fsp_id = p['fsp_id']
    email = p['recipient_email']
    lead_id = p['lead_id']

    # Get plan details
    plan = c.execute("SELECT * FROM final_send_plan WHERE id=?", (fsp_id,)).fetchone()
    if not plan:
        print(f'  [SKIP] plan {fsp_id} not found')
        fail_count += 1
        continue

    plan_dict = dict(plan)
    # Map final_send_plan columns to send_one expectations
    plan_dict['email'] = plan_dict.get('recipient_email', '')
    plan_dict['email_subject'] = plan_dict.get('subject', '')
    plan_dict['email_body'] = plan_dict.get('body_text', '')
    plan_dict['email_body_html'] = plan_dict.get('body_html', '')
    plan_dict['id'] = lead_id
    # CRITICAL: send_one reads 'final_plan_entry_id' NOT 'plan_entry_id'
    plan_dict['final_plan_entry_id'] = lead_id
    plan_dict['message_type'] = 'new_outreach'
    plan_dict['outreach_batch_date'] = BATCH_ID
    plan_dict['authorization_id'] = AUTH_ID
    # Template fields for assertion check (stored as template_id in DB)
    plan_dict['template_key'] = plan_dict.get('template_id', '')

    result = send_one(plan_dict, dry_run=False)
    status = result.get('status', 'unknown')

    if status == 'sent':
        sent_count += 1
        c.execute("UPDATE final_send_plan SET status='sent', sent_at=? WHERE id=?", (NOW_STR, fsp_id))
        print(f'  [SENT] {plan_dict["company_name"][:25]:25s} → {email[:35]}')
    else:
        fail_count += 1
        err = result.get('message', 'unknown error')
        c.execute("UPDATE final_send_plan SET status=?, skip_reason=? WHERE id=?", ('failed', err[:200], fsp_id))
        print(f'  [FAIL] {plan_dict["company_name"][:25]:25s} → {email[:35]} | {err[:50]}')

conn.commit()

# ═══════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════
print(f'\n{"=" * 65}')
print(f'  SEND COMPLETE')
print(f'  Sent: {sent_count} | Failed: {fail_count}')
print(f'  States: {json.dumps(state_dist)}')
print(f'  Templates: {json.dumps(template_dist)}')
sl_total = c.execute('SELECT COUNT(*) FROM send_log').fetchone()[0]
print(f'  send_log total: {sl_total}')
print(f'{"=" * 65}')

conn.close()
