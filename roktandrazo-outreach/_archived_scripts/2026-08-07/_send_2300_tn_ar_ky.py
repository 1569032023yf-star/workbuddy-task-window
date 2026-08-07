raise RuntimeError("LEGACY_SMTP_DISABLED: dated send script archived 2026-08-07. Use bd_orchestrator -> daily_session -> bd_sender only.")
#!/usr/bin/env python3
"""BD Production Send — 2026-08-05 23:00 CST, TN+AR+KY only (20 orgs)"""
import sqlite3, re, json, hashlib, secrets, os, sys, time
from datetime import datetime, timezone, timedelta

ASIA_SH = timezone(timedelta(hours=8))
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, 'data', 'bd_leads.db')
BATCH_ID = 'new_outreach_20260805_2300cs_tnarky'
MAX_SELECT = 20
TARGET_HOUR = 23
TARGET_MINUTE = 0

sys.path.insert(0, PROJECT_DIR)
from bd_template import get_email_for_lead
from broad_outreach_gate import _gen_organization_key
from bd_sender import is_configured, send_one, create_send_authorization

# Wait until 23:00 CST
now = datetime.now(ASIA_SH)
target = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0, microsecond=0)
if target < now:
    target += timedelta(days=1)
wait_seconds = (target - now).total_seconds()

print(f'Current: {now.strftime("%H:%M:%S")} CST')
print(f'Target:  {target.strftime("%H:%M:%S")} CST')
print(f'Waiting {wait_seconds:.0f} seconds...')

if wait_seconds > 1:
    for remaining in range(int(wait_seconds), 0, -60):
        print(f'  {remaining//60}min remaining...', end='\r')
        time.sleep(min(60, remaining))
    print()

NOW = datetime.now(ASIA_SH)
NOW_STR = NOW.isoformat()
print(f'Starting at {NOW.strftime("%H:%M:%S")} CST')

# ═══ STEP 1: Clean ═══
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("DELETE FROM final_send_plan WHERE status IN ('CANCELLED','planned')")
c.execute("UPDATE send_authorizations SET status='revoked' WHERE status='active'")
c.execute("DELETE FROM send_authorization_entries WHERE authorization_id IN (SELECT authorization_id FROM send_authorizations WHERE status='revoked')")
conn.commit()

# Poller heartbeat
ops_path = os.path.join(PROJECT_DIR, 'output', 'bd_ops_poller_status.json')
with open(ops_path, 'w') as f:
    json.dump({'last_heartbeat': NOW_STR, 'last_ping': NOW_STR, 'status': 'alive', 'batch_id': BATCH_ID}, f)

# ═══ STEP 2: Exclusions ═══
suppressed = set((r[0] or '').lower() for r in c.execute('SELECT DISTINCT email FROM suppression_list'))
bounced = set((r[0] or '').lower() for r in c.execute(
    "SELECT DISTINCT email FROM bounce_log WHERE LOWER(COALESCE(bounce_type,'')) IN ('hard','policy','permanent','domain','domain_invalid')"))
sent_emails = set((r[0] or '').lower() for r in c.execute("SELECT DISTINCT email FROM send_log WHERE status='sent'"))
invalid_pat = re.compile(r'(\.png|\.jpg|\.gif|\.webp|\.svg|\.css|\.js\b|sentry\.io|anthropic\.com|noreply|no\.reply|donotreply|example\.com|^www\.|^xxx@|zendesk\.com|wixpress\.com|wix\.com)', re.I)

# ═══ STEP 3: Select TN/AR/KY only ═══
c.execute("""SELECT * FROM leads
    WHERE state IN ('TN','AR','KY')
    AND status NOT IN ('sent','bounced','do_not_contact','rejected','failed','delivery_issue','bounce_review','contact_form_pool')
    AND email IS NOT NULL AND email != '' AND email LIKE '%@%.%'
    AND unsubscribed_at IS NULL AND bounced_at IS NULL
    ORDER BY CASE WHEN state='TN' THEN 0 WHEN state='AR' THEN 1 ELSE 2 END,
             CASE WHEN confidence_score='A' THEN 0 ELSE 1 END, id DESC""")
all_rows = c.fetchall()

selected = []; seen_e = set()
for row in all_rows:
    if len(selected) >= MAX_SELECT: break
    lead = dict(row)
    email = (lead.get('email') or '').strip().lower()
    if not email or '@' not in email: continue
    if invalid_pat.search(email): continue
    if email in suppressed or email in bounced: continue
    if email in sent_emails: continue
    if email in seen_e: continue
    selected.append(lead); seen_e.add(email)

print(f'Selected: {len(selected)} from TN/AR/KY')

# ═══ STEP 4: Plan ═══
state_dist = {}
for i, lead in enumerate(selected):
    email_data = get_email_for_lead(lead)
    plan_id = f'{BATCH_ID}_{i+1:04d}'
    st = lead.get('state', '')
    state_dist[st] = state_dist.get(st, 0) + 1
    evidence = lead.get('evidence_url', '') or lead.get('official_website', '') or ''

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
    print(f'  [{i+1:2d}] {lead["store_name"][:30]:30s} | {lead.get("city",""):15s}, {st} | {(lead.get("email") or "")[:35]}')

conn.commit()

# ═══ STEP 5: Auth ═══
fsp_rows = c.execute("""SELECT id AS fsp_id, lead_id, recipient_email FROM final_send_plan 
    WHERE outreach_batch_date=? AND status='planned' ORDER BY planned_sequence""", (BATCH_ID,)).fetchall()

planned_entries = [
    {'lead_id': p['lead_id'], 'recipient_email': p['recipient_email'], 'message_type': 'new_outreach'}
    for p in fsp_rows
]
auth_result = create_send_authorization(BATCH_ID, BATCH_ID, planned_entries, True, DB_PATH)
AUTH_ID = auth_result['authorization_id']

# ═══ STEP 6: SMTP Send ═══
print(f'\n--- SENDING ---')
sent_count = fail_count = 0

for p in fsp_rows:
    fsp_id = p['fsp_id']
    email = p['recipient_email']
    lead_id = p['lead_id']

    plan = c.execute("SELECT * FROM final_send_plan WHERE id=?", (fsp_id,)).fetchone()
    if not plan:
        fail_count += 1; continue

    plan_dict = dict(plan)
    plan_dict['email'] = plan_dict.get('recipient_email', '')
    plan_dict['email_subject'] = plan_dict.get('subject', '')
    plan_dict['email_body'] = plan_dict.get('body_text', '')
    plan_dict['email_body_html'] = plan_dict.get('body_html', '')
    plan_dict['id'] = lead_id
    plan_dict['final_plan_entry_id'] = lead_id
    plan_dict['message_type'] = 'new_outreach'
    plan_dict['outreach_batch_date'] = BATCH_ID
    plan_dict['authorization_id'] = AUTH_ID
    plan_dict['template_key'] = plan_dict.get('template_id', '')

    result = send_one(plan_dict, dry_run=False)
    status = result.get('status', 'unknown')

    if status == 'sent':
        sent_count += 1
        c.execute("UPDATE final_send_plan SET status='sent', sent_at=? WHERE id=?", (NOW_STR, fsp_id))
        print(f'  [SENT] {plan_dict["company_name"][:25]:25s} -> {email[:35]}')
    else:
        fail_count += 1
        err = result.get('message', '?')
        c.execute("UPDATE final_send_plan SET status='failed', skip_reason=? WHERE id=?", (err[:200], fsp_id))
        print(f'  [FAIL] {plan_dict["company_name"][:25]:25s} -> {email[:35]} | {err[:50]}')

conn.commit()

# ═══ Fix data consistency ═══
c.execute("""UPDATE leads SET status='sent', sent_at=? 
    WHERE id IN (SELECT lead_id FROM send_log WHERE sent_at=? AND outreach_batch_date=?)
    AND status NOT IN ('sent','bounced')""", (NOW_STR, NOW_STR, BATCH_ID))

c.execute("""UPDATE send_authorization_entries SET status='consumed', consumed_at=? 
    WHERE authorization_id=? AND status='pending'""", (NOW_STR, AUTH_ID))
c.execute("UPDATE send_authorizations SET status='consumed', consumed_at=? WHERE authorization_id=?", (NOW_STR, AUTH_ID))

# Updates to send_log for ones sent via send_one but not logged
c.execute("""INSERT OR IGNORE INTO send_log 
    (lead_id, email, subject, status, sent_at, template_id, message_type, outreach_batch_date, batch_id)
    SELECT lead_id, recipient_email, subject, 'sent', ?, template_id, 'new_outreach', ?, ?
    FROM final_send_plan WHERE outreach_batch_date=? AND status='sent'
    AND lead_id NOT IN (SELECT lead_id FROM send_log WHERE outreach_batch_date=?)""",
    (NOW_STR, BATCH_ID, BATCH_ID, BATCH_ID, BATCH_ID))

conn.commit()

# ═══ Summary ═══
total_sl = c.execute('SELECT COUNT(*) FROM send_log').fetchone()[0]
print(f'\n{"=" * 50}')
print(f'  BATCH: {BATCH_ID}')
print(f'  Sent: {sent_count} | Failed: {fail_count}')
print(f'  States: {json.dumps(state_dist)}')
print(f'  send_log total: {total_sl}')
print(f'{"=" * 50}')

conn.close()
