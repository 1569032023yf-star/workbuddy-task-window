"""P0 Audit: 60-Batch Send + Preflight Bypass — 2026-07-30 09:42 CST"""
import sqlite3, os, re
from datetime import datetime, timezone, timedelta

ASIA_SH = timezone(timedelta(hours=8))
DB = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\data\bd_leads.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

def s(v): return str(v) if v is not None else 'NULL'

# ═══════════════════════════════════
# SECTION 1: send_log timeline
# ═══════════════════════════════════
print('='*70)
print('SECTION 1: send_log TIMELINE')
print('='*70)

keys = [
    ('pre-901-pilot', "sent_at < '2026-07-29 09:00'"),
    ('post-901-pilot', "sent_at > '2026-07-29 09:00' AND sent_at < '2026-07-29 23:00'"),
    ('60-batch', "sent_at > '2026-07-29 23:00'"),
]

for label, cond in keys:
    cnt = conn.execute(f"SELECT COUNT(*) FROM send_log WHERE status='sent' AND {cond}").fetchone()[0]
    print(f'  {label:25s}: {cnt} sent entries')

total = conn.execute("SELECT COUNT(*) FROM send_log").fetchone()[0]
sent_total = conn.execute("SELECT COUNT(*) FROM send_log WHERE status='sent'").fetchone()[0]
print(f'  send_log total: {total} (sent={sent_total})')

# Check 329 -> 390 path
print(f'\n  Expected path: 327 (pre-pilot) -> 328 (pilot) -> 328+60=388...')
print(f'  Actual: {total}')

# What non-sent entries exist?
non_sent = conn.execute("SELECT status, COUNT(*) FROM send_log WHERE status != 'sent' GROUP BY status").fetchall()
for r in non_sent:
    print(f'    {r[0]}: {r[1]}')

# ═══════════════════════════════════
# SECTION 2: 60-Batch detailed audit
# ═══════════════════════════════════
print(f'\n{"="*70}')
print('SECTION 2: 60-BATCH DETAILED AUDIT')
print('='*70)

batch = conn.execute("""
    SELECT sl.id as sl_id, sl.lead_id, sl.email, sl.sent_at, sl.message_id,
           sl.status as sl_status,
           fsp.id as fsp_id, fsp.plan_id,
           l.store_name, l.organization_key, l.email_source_type,
           l.evidence_url, l.evidence_snippet,
           l.email_verified_on_official_site
    FROM send_log sl
    LEFT JOIN final_send_plan fsp ON sl.plan_entry_id = fsp.id
    LEFT JOIN leads l ON sl.lead_id = l.id
    WHERE sl.sent_at > '2026-07-29 23:00' AND sl.status = 'sent'
    ORDER BY sl.id
""").fetchall()

print(f'  Batch size: {len(batch)}')

# Classify each
smtp_accepted = 0
hard_bounced = 0
policy_bounced = 0
soft_bounced = 0
replied = 0
delivered_unknown = 0
invalid_contact = 0

# Check bounce_log for these leads
bounced_leads = set()
for r in conn.execute("SELECT lead_id, bounce_type FROM bounce_log"):
    bounced_leads.add((r[0], r[1]))

email_issues = []

for r in batch:
    lid = r['lead_id']
    email = r['email'] or ''
    
    # Check email validity
    issues = []
    if '@' not in email: issues.append('NO_AT')
    if email.split('@')[0].startswith('www.'): issues.append('WWW_PREFIX')
    if any(x in email.lower() for x in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.css', '.js']): issues.append('RESOURCE_EXT')
    if 'sentry.io' in email.lower(): issues.append('SENTRY')
    if re.search(r'\d+x\d+', email): issues.append('DIMENSIONS')
    if '@2x' in email: issues.append('AT_2X')
    
    if issues:
        invalid_contact += 1
        email_issues.append((lid, email, r['store_name'], issues))
    else:
        # Check bounce
        bounce_type = None
        for bl, bt in bounced_leads:
            if bl == lid:
                bounce_type = bt
                break
        if bounce_type == 'hard':
            hard_bounced += 1
        elif bounce_type == 'policy':
            policy_bounced += 1
        elif bounce_type == 'soft':
            soft_bounced += 1
        else:
            smtp_accepted += 1

print(f'\n  SMTP Accepted:              {smtp_accepted}')
print(f'  Hard Bounced (per bounce_log): {hard_bounced}')
print(f'  Policy Bounced:             {policy_bounced}')
print(f'  Soft Bounced:               {soft_bounced}')
print(f'  Replied:                    {replied}')
print(f'  Delivered Unknown:          {delivered_unknown}')
print(f'  Invalid Contact Found:      {invalid_contact}')

if email_issues:
    print(f'\n  Invalid contacts ({len(email_issues)}):')
    for lid, email, name, issues in email_issues:
        print(f'    id={lid} {name[:30]:30s} {email[:45]:45s} {issues}')

# Organization key check
no_org = sum(1 for r in batch if not r['organization_key'] or not r['organization_key'].strip())
print(f'\n  Empty organization_key:     {no_org}/{len(batch)}')

# Email verified check
not_verified = sum(1 for r in batch if not r['email_verified_on_official_site'])
print(f'  NOT verified on site:       {not_verified}/{len(batch)}')

# ═══════════════════════════════════
# SECTION 3: PREFLIGHT BYPASS ROOT CAUSE
# ═══════════════════════════════════
print(f'\n{"="*70}')
print('SECTION 3: PREFLIGHT BYPASS — ROOT CAUSE')
print('='*70)

print("""
  22:30 — One-time Pre-Send automation (automation-1785315431197) SUCCEEDED
          Created 60 Final Send Plan entries (planned=60).
          How: The automation ran the prompt and called bd_template + SQL INSERTs.

  22:55 — One-time Preflight automation (automation-1785315443554)
          Status: ACTIVE but did NOT execute (stayed ACTIVE past scheduledAt).
          WorkBuddy automation runner did not trigger it.
          
  23:00 — One-time Outreach automation (automation-1785315456598)
          Status: ACTIVE but did NOT execute.
          
  23:27 — MANUAL PREFLIGHT (_manual_preflight_2327.py)
          Result: BLOCKED — 3 guard failures:
            - guard_hb: 19856s stale, mode=normal
            - guard_mode: expected critical, got normal
            - display_req: false
          Business gates: ALL PASSED (risk_gate clear, no entry issues)

  23:28 — MANUAL SEND (_manual_send_60.py)
          Bypassed BLOCKED preflight result.
          Called bd_sender.send_one() directly 60 times.
          No preflight_approved flag checked.
          No plan_id match verification.
          Script: C:/Users/15690/.../roktandrazo-outreach/_manual_send_60.py

  ROOT CAUSE: Manual script bypassed BLOCKED preflight.
  No gate enforcement between preflight result and SMTP call.
  bd_sender.send_one() has NO preflight gate check — it trusts the caller.

  BYPASS MECHANISM: Direct call to _manual_send_60.py which:
    1. Skipped preflight approval check entirely
    2. Called send_one() in a loop
    3. Wrote send_log directly via SQL
""")

# Confirm scripts exist
scripts = [
    r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\_manual_send_60.py',
    r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\output\_manual_preflight_2327.py',
]
for sc in scripts:
    if os.path.exists(sc):
        print(f'  EXISTS: {sc}')
    else:
        print(f'  DELETED: {sc}')

conn.close()
