#!/usr/bin/env python3
"""
BD Production Pre-Send — 21:30 Asia/Shanghai
Read frozen snapshot → Query DB → Create Final Send Plan (30 orgs, no SMTP)

batch_id: new_outreach_20260805_et1000
NO SMTP. Follow-up = 0.
"""
import json, hashlib, secrets, re, sqlite3, sys, os
from datetime import datetime, timezone, timedelta

ASIA_SH = timezone(timedelta(hours=8))
NOW = datetime.now(ASIA_SH)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

BATCH_ID = 'new_outreach_20260805_et1000'
DB_PATH = os.path.join(PROJECT_DIR, 'data', 'bd_leads.db')
SNAPSHOT_PATH = os.path.join(PROJECT_DIR, 'output', f'frozen_{BATCH_ID}.json')
PLAN_REPORT_PATH = os.path.join(PROJECT_DIR, 'output', f'pre_send_report_{NOW.strftime("%Y-%m-%d_%H%M")}.md')

MAX_SELECT = 30

print('=' * 65)
print('  BD PRODUCTION PRE-SEND — 21:30 CST')
print(f'  Batch: {BATCH_ID}')
print(f'  Time:  {NOW.isoformat()}')
print(f'  Rule:  NO SMTP. Follow-up = 0.')
print(f'  Max:   {MAX_SELECT} orgs')
print('=' * 65)

# ═══════════════════════════════════════════════════════════
# STEP 1: Read frozen snapshot
# ═══════════════════════════════════════════════════════════
print('\n── STEP 1: Read frozen candidate snapshot ──')
if not os.path.exists(SNAPSHOT_PATH):
    print(f'  [NO_BATCH_TODAY] Snapshot not found: {SNAPSHOT_PATH}')
    # Write NO_BATCH_TODAY marker
    report_lines = [
        f"# BD Pre-Send Report — {NOW.strftime('%Y-%m-%d %H:%M')} CST",
        "",
        f"**Batch:** {BATCH_ID}",
        "",
        "## Result: NO_BATCH_TODAY",
        "",
        f"Snapshot `frozen_{BATCH_ID}.json` not found in output/.",
        "No 21:10 freeze snapshot available for today. No Final Send Plan created. Exiting cleanly.",
    ]
    with open(PLAN_REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    print(f'  Report: {PLAN_REPORT_PATH}')

    # Set preflight_status=no_batch so downstream knows
    print('\n── STEP 8 (NO_BATCH): Set preflight_status=no_batch ──')
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?,?,datetime('now'))",
                      ('preflight_status', 'no_batch'))
        conn.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?,?,datetime('now'))",
                      ('preflight_batch_id', BATCH_ID))
        conn.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?,?,datetime('now'))",
                      ('preflight_plan_count', '0'))
        conn.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?,?,datetime('now'))",
                      ('preflight_follow_up', '0'))
        conn.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?,?,datetime('now'))",
                      ('preflight_at', NOW.isoformat()))
        conn.commit()
        conn.close()
        print(f'  system_config.preflight_status -> "no_batch"')
    except Exception as e:
        print(f'  [WARN] Could not update system_config: {e}')

    print('\n' + '=' * 65)
    print(f'  EXIT — NO_BATCH_TODAY')
    print(f'  Batch:   {BATCH_ID}')
    print(f'  Orgs:    0 (no snapshot)')
    print(f'  Report:  {PLAN_REPORT_PATH}')
    print('=' * 65)
    sys.exit(0)

with open(SNAPSHOT_PATH, 'r') as f:
    snapshot = json.load(f)

print(f'  Snapshot loaded: count={snapshot["count"]}, frozen_at={snapshot["frozen_at"]}')
print(f'  States: {json.dumps(snapshot["states"])}')

# ═══════════════════════════════════════════════════════════
# STEP 2: Query DB for Final Sendable Unsent orgs
# ═══════════════════════════════════════════════════════════
print('\n── STEP 2: Query Final Sendable Unsent orgs ──')
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Build exclusion sets (hard gates)
suppressed = set((r[0] or '').lower() for r in c.execute('SELECT DISTINCT email FROM suppression_list'))
bounced = set((r[0] or '').lower() for r in c.execute("SELECT DISTINCT email FROM bounce_log WHERE LOWER(COALESCE(bounce_type,'')) IN ('hard','policy','permanent','domain','domain_invalid')"))
sent_emails = set((r[0] or '').lower() for r in c.execute("SELECT DISTINCT email FROM send_log WHERE status='sent'"))
sent_leads = set(r[0] for r in c.execute("SELECT DISTINCT lead_id FROM send_log WHERE status='sent'"))

# Organization-level: orgs that have already been sent
sent_orgs = set()
for r in c.execute("""SELECT DISTINCT COALESCE(NULLIF(l.organization_key,''), 'org_fallback_'||l.id) 
    FROM send_log sl JOIN leads l ON sl.lead_id=l.id WHERE sl.status='sent'"""):
    sent_orgs.add(r[0])

# Negative reply detection
neg_reply_ids = set()
for r in c.execute("SELECT lead_id FROM reply_log"):
    neg_reply_ids.add(r[0])
for r in c.execute("""SELECT id FROM leads WHERE 
    (notes LIKE '%unsubscribe%' OR notes LIKE '%stop%' OR notes LIKE '%remove%' 
     OR notes LIKE '%do not contact%' OR notes LIKE '%not interested%')
    AND replied_at IS NOT NULL"""):
    neg_reply_ids.add(r[0])

# Invalid email pattern
invalid_pat = re.compile(
    r'(\.png|\.jpg|\.gif|\.webp|\.svg|\.css|\.js\b|'
    r'sentry\.io|anthropic\.com|noreply|no.reply|donotreply|'
    r'example\.com|^www\.|^xxx@|'
    r'zendesk\.com|wixpress\.com|wix\.com)',
    re.I
)

# System email prefixes — ONLY truly system/non-human addresses
system_prefixes = {'no-reply', 'noreply', 'privacy', 'copyright', 'abuse',
                   'postmaster', 'mailer-daemon', 'hostmaster', 'webmaster'}

EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")

print(f'  Exclusion sets: suppressed={len(suppressed)}, bounced={len(bounced)}, sent_emails={len(sent_emails)}, '
      f'sent_orgs={len(sent_orgs)}, neg_reply={len(neg_reply_ids)}')

# Query: unsent leads with valid email, TN→AR→KY priority, exclude already sent orgs
all_rows = c.execute("""
    SELECT * FROM leads
    WHERE status NOT IN ('sent','bounced','do_not_contact','rejected','failed','delivery_issue','bounce_review')
    AND email IS NOT NULL AND email != ''
    AND email LIKE '%@%.%'
    AND unsubscribed_at IS NULL
    AND bounced_at IS NULL
    AND COALESCE(defer_reason,'') = ''
    ORDER BY 
        CASE WHEN state='TN' THEN 0 WHEN state='AR' THEN 1 WHEN state='KY' THEN 2 ELSE 3 END,
        CASE WHEN confidence_score='A' THEN 0 ELSE 1 END,
        collected_at ASC
""").fetchall()

print(f'  Raw candidates from DB: {len(all_rows)}')

# ═══════════════════════════════════════════════════════════
# STEP 3: Filter and select up to 30 unique organizations
# ═══════════════════════════════════════════════════════════
print('\n── STEP 3: Select up to 30 unique organizations ──')
from bd_template import get_email_for_lead, route_template_for_lead
from broad_outreach_gate import _gen_organization_key

selected = []
seen_orgs = set()
seen_emails = set()
skipped_invalid = 0
skipped_suppressed = 0
skipped_sent_org = 0
skipped_dupe = 0
skipped_neg = 0

for row in all_rows:
    if len(selected) >= MAX_SELECT:
        break
    
    lead = dict(row)
    email = (lead.get('email') or '').strip().lower()
    lead_id = lead['id']
    
    # Compute org key
    org_key = (lead.get('organization_key') or '').strip()
    if not org_key:
        org_key = _gen_organization_key(lead)
    
    # Hard gates
    if not email or not EMAIL_RE.fullmatch(email):
        skipped_invalid += 1
        continue
    if invalid_pat.search(email):
        skipped_invalid += 1
        continue
    
    local = email.split('@')[0].lower()
    if local in system_prefixes:
        skipped_invalid += 1
        continue
    
    if email in suppressed:
        skipped_suppressed += 1
        continue
    if email in bounced:
        skipped_suppressed += 1
        continue
    if email in sent_emails:
        skipped_sent_org += 1
        continue
    if lead_id in sent_leads:
        skipped_sent_org += 1
        continue
    if lead_id in neg_reply_ids:
        skipped_neg += 1
        continue
    
    # Check org-level dedup
    org_fallback = f'org_fallback_{lead_id}'
    effective_org = org_key if org_key else org_fallback
    
    if effective_org in sent_orgs:
        skipped_sent_org += 1
        continue
    
    # Batch-level dedup
    if effective_org in seen_orgs:
        skipped_dupe += 1
        continue
    if email in seen_emails:
        skipped_dupe += 1
        continue
    
    # Contact form only check
    if lead.get('status') == 'contact_form_pool' or lead.get('contact_form_only'):
        skipped_invalid += 1
        continue
    
    # ✅ Passed all gates
    lead['_effective_org_key'] = effective_org
    selected.append(lead)
    seen_orgs.add(effective_org)
    seen_emails.add(email)

print(f'  Selected: {len(selected)} / {MAX_SELECT} max')
print(f'  Skipped: invalid={skipped_invalid}, suppressed/bounced={skipped_suppressed}, '
      f'sent_org={skipped_sent_org}, dupe={skipped_dupe}, neg_reply={skipped_neg}')

# State breakdown
state_counts = {}
for s in selected:
    st = s.get('state', '?')
    state_counts[st] = state_counts.get(st, 0) + 1
print(f'  By state: {json.dumps(state_counts)}')

if len(selected) == 0:
    print('\n  [FAIL] No sendable organizations found.')
    conn.close()
    sys.exit(1)

# ═══════════════════════════════════════════════════════════
# STEP 4+5: Route template + Generate emails
# ═══════════════════════════════════════════════════════════
print('\n── STEP 4+5: Route templates & Generate emails ──')
template_counts = {}
email_errors = []

for lead in selected:
    try:
        template_key = route_template_for_lead(lead)
        email_data = get_email_for_lead(lead)
        lead['email_template'] = template_key
        lead['email_subject'] = email_data['subject']
        lead['email_body'] = email_data['body_text']
        lead['email_body_html'] = email_data['body_html']
        lead['template_sha'] = email_data['template_sha256']
        template_counts[template_key] = template_counts.get(template_key, 0) + 1
    except Exception as e:
        email_errors.append((lead['id'], lead['store_name'], str(e)))

print(f'  Template routing: {json.dumps(template_counts)}')
if email_errors:
    for lid, name, err in email_errors:
        print(f'  [ERROR] lead_id={lid} {name}: {err}')

# ═══════════════════════════════════════════════════════════
# STEP 6: Create Final Send Plan entries
# ═══════════════════════════════════════════════════════════
print('\n── STEP 6: Create Final Send Plan entries ──')

# Delete old entries for this batch (CANCELLED from prior runs) to avoid UNIQUE collision
del_count = c.execute("DELETE FROM final_send_plan WHERE outreach_batch_date=?", (BATCH_ID,)).rowcount
print(f'  Deleted old entries: {del_count}')

# Clean old tracking tokens
c.execute("DELETE FROM email_tracking_messages WHERE tracking_message_id LIKE ?", (f'%trk_%{BATCH_ID}%',))

# Delete old auth entries
c.execute("DELETE FROM send_authorization_entries WHERE authorization_id LIKE ?", (f'%{BATCH_ID}%',))

# Revoke old auths
c.execute("UPDATE send_authorizations SET status='revoked' WHERE outreach_batch_date=? AND status='active'", (BATCH_ID,))
c.execute("DELETE FROM send_authorizations WHERE outreach_batch_date=?", (BATCH_ID,))

now_str = NOW.isoformat()
plan_entries = []

for i, lead in enumerate(selected):
    plan_id = f'{BATCH_ID}_{i+1:04d}'
    
    c.execute("""
        INSERT INTO final_send_plan 
        (plan_id, lead_id, company_name, recipient_email, message_type,
         outreach_batch_date, planned_sequence, status, subject, body_text, body_html,
         source_city, source_state, customer_type, template_id, evidence_url, hygiene_passed_at, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        plan_id, lead['id'], lead['store_name'], lead['email'].strip().lower(),
        'new_outreach', BATCH_ID, i + 1, 'planned',
        lead['email_subject'], lead['email_body'], lead.get('email_body_html', ''),
        lead.get('city', ''), lead.get('state', ''),
        lead.get('store_type') or 'retail', lead.get('email_template', ''),
        lead.get('evidence_url') or '', now_str, now_str
    ))
    
    plan_entries.append({
        'plan_id': plan_id,
        'lead_id': lead['id'],
        'recipient_email': lead['email'].strip().lower(),
        'sequence': i + 1,
        'company': lead['store_name'],
        'city': lead.get('city', ''),
        'state': lead.get('state', ''),
        'template': lead.get('email_template', ''),
    })

print(f'  Inserted: {len(plan_entries)} entries')

# ═══════════════════════════════════════════════════════════
# STEP 7: Save tracking tokens
# ═══════════════════════════════════════════════════════════
print('\n── STEP 7: Save tracking tokens ──')
tracking_count = 0
for i, lead in enumerate(selected):
    token = secrets.token_urlsafe(24)
    token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
    tracking_message_id = f'trk_{lead["id"]}_{BATCH_ID}_{i:04d}'
    
    try:
        c.execute("""
            INSERT INTO email_tracking_messages 
            (tracking_message_id, token_hash, lead_id, plan_entry_id, status, is_test)
            VALUES (?,?,?,?,?,0)
        """, (tracking_message_id, token_hash, lead['id'], 
              plan_entries[i]['plan_id'], 'prepared'))
        tracking_count += 1
    except Exception as e:
        print(f'  [WARN] Tracking token failed for lead_id={lead["id"]}: {e}')

print(f'  Tracking tokens: {tracking_count}/{len(selected)}')

# ═══════════════════════════════════════════════════════════
# STEP 7b: Create send_authorization
# ═══════════════════════════════════════════════════════════
print('\n── STEP 7b: Create send authorization ──')
auth_id = f'auth_{BATCH_ID}_{secrets.token_hex(8)}'
plan_entries_hash = hashlib.sha256(
    json.dumps([(pe['lead_id'], pe['recipient_email']) for pe in plan_entries], sort_keys=True).encode()
).hexdigest()

c.execute("""
    INSERT INTO send_authorizations 
    (authorization_id, plan_id, outreach_batch_date, plan_entries_hash, approved_entry_count,
     preflight_status, approved_at, expires_at, approved_by, status, created_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)
""", (auth_id, BATCH_ID, BATCH_ID, plan_entries_hash, len(selected),
      'planned', now_str, (NOW + timedelta(hours=24)).isoformat(), 'system', 'active', now_str))

# Fetch FSP row IDs for auth entries
fsp_rows = c.execute(
    "SELECT id, lead_id, recipient_email FROM final_send_plan WHERE outreach_batch_date=? AND status='planned' ORDER BY planned_sequence",
    (BATCH_ID,)
).fetchall()

# Add auth entries (plan_entry_id = fsp row id, INTEGER)
for fsp in fsp_rows:
    entry_hash = hashlib.sha256(f"{fsp['lead_id']}:{fsp['recipient_email']}".encode()).hexdigest()[:12]
    c.execute("""
        INSERT INTO send_authorization_entries
        (authorization_id, plan_entry_id, lead_id, recipient_email, entry_hash, status)
        VALUES (?,?,?,?,?,?)
    """, (auth_id, fsp['id'], fsp['lead_id'], fsp['recipient_email'], entry_hash, 'pending'))

print(f'  Auth: {auth_id} ({len(fsp_rows)} entries)')

# ═══════════════════════════════════════════════════════════
# STEP 8: Set preflight_status='planned' in system_config
# ═══════════════════════════════════════════════════════════
print('\n── STEP 8: Set preflight_status=planned ──')
c.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?,?,datetime('now'))",
          ('preflight_status', 'planned'))
c.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?,?,datetime('now'))",
          ('preflight_batch_id', BATCH_ID))
c.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?,?,datetime('now'))",
          ('preflight_plan_count', str(len(selected))))
c.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?,?,datetime('now'))",
          ('preflight_follow_up', '0'))
c.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?,?,datetime('now'))",
          ('preflight_at', now_str))
print(f'  system_config.preflight_status -> "planned"')

conn.commit()

# ═══════════════════════════════════════════════════════════
# Verify
# ═══════════════════════════════════════════════════════════
print('\n── VERIFY ──')
verify = c.execute(
    "SELECT COUNT(*) FROM final_send_plan WHERE outreach_batch_date=? AND status='planned'",
    (BATCH_ID,)
).fetchone()[0]
auth_verify = c.execute(
    "SELECT COUNT(*) FROM send_authorization_entries WHERE authorization_id=? AND status='pending'",
    (auth_id,)
).fetchone()[0]
print(f'  Plan entries (planned): {verify}')
print(f'  Auth entries (pending): {auth_verify}')
print(f'  Match: {"✅" if verify == auth_verify == len(selected) else "❌"}')

conn.close()

# ═══════════════════════════════════════════════════════════
# Generate report
# ═══════════════════════════════════════════════════════════
print(f'\n── REPORT: {PLAN_REPORT_PATH} ──')

report_lines = [
    f"# BD Pre-Send Report — {NOW.strftime('%Y-%m-%d %H:%M')} CST",
    "",
    f"**Batch:** `{BATCH_ID}`",
    f"**Auth:** `{auth_id}`",
    f"**Status:** `planned` | **SMTP:** 0 (no SMTP in pre-send)",
    "",
    "## Summary",
    "",
    f"- **Organizations selected:** {len(selected)} / {MAX_SELECT} max",
    f"- **Follow-up:** 0",
    f"- **Skipped — invalid email:** {skipped_invalid}",
    f"- **Skipped — suppressed/bounced:** {skipped_suppressed}",
    f"- **Skipped — already sent (org):** {skipped_sent_org}",
    f"- **Skipped — duplicate:** {skipped_dupe}",
    f"- **Skipped — negative reply:** {skipped_neg}",
    "",
    "## State Distribution",
    "",
]
for st, cnt in sorted(state_counts.items(), key=lambda x: -x[1]):
    report_lines.append(f"- **{st}:** {cnt}")
report_lines.extend([
    "",
    "## Template Routing",
    "",
])
for tpl, cnt in sorted(template_counts.items(), key=lambda x: -x[1]):
    tpl_short = 'RETAIL' if 'retail' in tpl else 'CUSTOM'
    report_lines.append(f"- **{tpl_short}** ({tpl}): {cnt}")

report_lines.extend([
    "",
    "## Selected Organizations",
    "",
    "| # | Company | City | State | Template | Email |",
    "|---|---------|------|-------|----------|-------|",
])
for pe in plan_entries:
    tpl_tag = 'R' if 'retail' in pe['template'] else 'C'
    report_lines.append(
        f"| {pe['sequence']} | {pe['company']} | {pe['city']} | {pe['state']} | {tpl_tag} | {pe['recipient_email']} |"
    )

report_lines.extend([
    "",
    "## Gates",
    "",
    "- ✅ No previous sent email/org",
    "- ✅ No suppression",
    "- ✅ No bounce (hard/policy/permanent)",
    "- ✅ No negative reply",
    "- ✅ Valid email format",
    "- ✅ Organization deduplicated",
    "- ✅ TN → AR → KY priority",
    "",
    "## Configuration",
    "",
    f"- `preflight_status`: `planned`",
    f"- `preflight_batch_id`: `{BATCH_ID}`",
    f"- `preflight_plan_count`: `{len(selected)}`",
    f"- `preflight_follow_up`: `0`",
    f"- `preflight_at`: `{now_str}`",
    "",
    "---",
    f"*Generated at {NOW.isoformat()}*",
])

with open(PLAN_REPORT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))

print(f'  Report written: {PLAN_REPORT_PATH}')

# ═══════════════════════════════════════════════════════════
# Final summary
# ═══════════════════════════════════════════════════════════
print('\n' + '=' * 65)
print(f'  PRE-SEND COMPLETE')
print(f'  Batch:   {BATCH_ID}')
print(f'  Orgs:    {len(selected)} / {MAX_SELECT}')
print(f'  Follow-up: 0')
print(f'  SMTP:    0 (no SMTP — Final Send Plan only)')
print(f'  Status:  preflight_status=planned')
print(f'  Report:  {PLAN_REPORT_PATH}')
print('=' * 65)
