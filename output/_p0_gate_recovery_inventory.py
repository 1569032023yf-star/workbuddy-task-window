"""P0 Gate Recovery — Full Inventory Recalculation + Regression Tests — 2026-07-30"""
import sys, os, sqlite3, re
PROJECT_DIR = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach'
sys.path.insert(0, PROJECT_DIR)
DB = os.path.join(PROJECT_DIR, 'data', 'bd_leads.db')

from broad_outreach_gate import (
    evaluate_broad_outreach,
    _has_valid_business_email,
    _gen_organization_key,
    BroadOutreachDecision,
)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# ═══════════════════════════════
# Build exclusion sets
# ═══════════════════════════════
sup_emails = frozenset(r[0] for r in conn.execute("SELECT DISTINCT email FROM suppression_list"))
sent_emails = frozenset(r[0] for r in conn.execute("SELECT DISTINCT email FROM send_log WHERE status='sent'"))
sent_orgs = frozenset()
for r in conn.execute("SELECT DISTINCT COALESCE(NULLIF(l.organization_key,''),'org:'||l.id) FROM send_log sl JOIN leads l ON sl.lead_id=l.id WHERE sl.status='sent'"):
    sent_orgs = sent_orgs | {r[0]}
for r in conn.execute("SELECT DISTINCT COALESCE(NULLIF(l.organization_key,''),'org:'||l.id) FROM send_log sl JOIN leads l ON sl.lead_id=l.id WHERE sl.status='sent' AND (sl.message_type IS NULL OR sl.message_type='')"):
    sent_orgs = sent_orgs | {r[0]}
bounced_emails = frozenset(r[0] for r in conn.execute("SELECT DISTINCT email FROM bounce_log WHERE bounce_type='hard'"))
neg_reply_ids = frozenset(r[0] for r in conn.execute("SELECT DISTINCT lead_id FROM reply_log"))
sent_domains = frozenset(r[0] for r in conn.execute("SELECT DISTINCT domain_hash FROM leads l JOIN send_log sl ON sl.lead_id=l.id WHERE sl.status='sent' AND l.domain_hash IS NOT NULL"))

# ═══════════════════════════════
# REGRESSION TESTS
# ═══════════════════════════════
print('='*70)
print('REGRESSION TESTS')
print('='*70)

test_cases = [
    # (email, expected_blocked, description)
    ('tbs_rev_hz_type_110x@2x.png', True, 'image dim + @2x'),
    ('certificate1_235x235@2x.jpg', True, 'image cert 235x235'),
    ('www.kll@toystoreandgifts.com', True, 'www prefix'),
    ('79baaa8e09c746d2b7401643b99792e0@sentry.io', True, 'hash + sentry'),
    ('diane@sevendaysvt.com', False, 'normal email (third-party check separate)'),
    ('bsidegames.info@gmail.com', False, 'normal Gmail'),
    ('info@uncommonsnyc.com', False, 'normal info@'),
    ('contactus@thegreatescapeonline.com', False, 'normal contactus@'),
    ('green-orange-and-yellow-ink_192x@2x.png', True, 'image filename + @2x'),
    ('sales@idahotaters.com', False, 'normal sales@'),
    ('13e49d785d8d4f828038b6136f3b48ba@sentry.io', True, 'hash + sentry'),
    ('noreply@example.com', True, 'noreply + example'),
    ('xxx@xxx.xxx', True, 'placeholder'),
]

passed = 0
failed = 0
for email, expected_blocked, desc in test_cases:
    lead = {'email': email, 'email_source_type': 'official_page_visible',
            'store_name': 'Test Store', 'official_website': 'https://test.com',
            'id': 99999, 'domain_hash': 'test_com'}
    has_email, reason, conf = _has_valid_business_email(lead)
    actually_blocked = not has_email
    status = 'PASS' if actually_blocked == expected_blocked else 'FAIL'
    if actually_blocked == expected_blocked:
        passed += 1
    else:
        failed += 1
    print(f'  [{status}] {desc:40s} email={email[:45]:45s} blocked={actually_blocked} expected={expected_blocked} reason={reason}')

print(f'\n  Regression: {passed}/{len(test_cases)} passed, {failed} failed')

# ═══════════════════════════════
# FULL INVENTORY RE-EVALUATION
# ═══════════════════════════════
print(f'\n{"="*70}')
print('FULL INVENTORY RE-EVALUATION')
print('='*70)

leads = conn.execute("SELECT * FROM leads WHERE status NOT IN ('sent','bounced','do_not_contact') ORDER BY id").fetchall()
print(f'  Active leads: {len(leads)}')

cats = {
    'Strict A0': [], 'Broad Ready': [], 'Exception Review': [],
    'Contact Recovery': [], 'Contact Form Only': [], 'Permanently Blocked': []
}

for row in leads:
    lead = dict(row)
    result = evaluate_broad_outreach(
        lead, sent_domains, sup_emails, bounced_emails, sent_emails, sent_orgs, neg_reply_ids
    )
    
    if result.broad_outreach_ready:
        # Check if also Strict A0
        score = lead.get('confidence_score', '')
        auto = lead.get('auto_sendable')
        ev_url = lead.get('evidence_url') or ''
        if score == 'A' and auto == 1 and ev_url:
            cats['Strict A0'].append(result)
        else:
            cats['Broad Ready'].append(result)
    else:
        reason = result.broad_blocked_reason
        if 'email_missing' in reason or 'invalid_email' in reason or 'invalid_email_pattern' in reason or 'url_like' in reason or 'resource_extension' in reason or 'hash_like' in reason or 'system_email' in reason:
            cats['Contact Recovery'].append(result)
        elif reason == 'contact_form_only':
            cats['Contact Form Only'].append(result)
        elif 'suppressed' in reason or 'bounced' in reason or 'unsubscribed' in reason or 'negative_reply' in reason or 'status_blocked' in reason:
            cats['Permanently Blocked'].append(result)
        else:
            cats['Exception Review'].append(result)

# Dedup Broad Ready by org_key
broad_orgs = set()
unique_broad = []
for d in cats['Broad Ready']:
    ok = d.organization_key
    if ok not in broad_orgs:
        broad_orgs.add(ok)
        unique_broad.append(d)

# Dedup Strict A0 by org_key
a0_orgs = set()
unique_a0 = []
for d in cats['Strict A0']:
    ok = d.organization_key
    if ok not in a0_orgs:
        a0_orgs.add(ok)
        unique_a0.append(d)

# Output
print(f'\n  Strict A0 Organizations:                    {len(unique_a0)}')
print(f'  Broad Outreach Ready Organizations:         {len(unique_broad)}')
print(f'  Broad Org Outreach Opportunities (deduped): {len(unique_broad)}')

print(f'\n  --- Category Breakdown ---')
for cat, items in cats.items():
    raw = len(items)
    if cat == 'Broad Ready':
        deduped = len(unique_broad)
        print(f'  {cat:25s}: {raw:4d} raw, {deduped:4d} deduped')
    elif cat == 'Strict A0':
        deduped = len(unique_a0)
        print(f'  {cat:25s}: {raw:4d} raw, {deduped:4d} deduped')
    else:
        print(f'  {cat:25s}: {raw:4d}')

# Exception Review breakdown
print(f'\n  --- Exception Review Reasons ---')
er_reasons = {}
for d in cats['Exception Review']:
    r = d.broad_blocked_reason
    er_reasons[r] = er_reasons.get(r, 0) + 1
for r, c in sorted(er_reasons.items(), key=lambda x: -x[1]):
    print(f'    {r}: {c}')

# Organization key statistics
no_org_in_broad = sum(1 for d in unique_broad if d.organization_key.startswith('org:'))
print(f'\n  Auto-generated org_keys in Broad: {no_org_in_broad}')

# Final sendability check
max_tonight = len(unique_a0) + min(len(unique_broad), 60 - len(unique_a0))
meets_60 = 'YES' if max_tonight >= 60 else f'NO (max={max_tonight})'
print(f'\n  Tonight max (A0 + Broad): {max_tonight}')
print(f'  Meets 60: {meets_60}')

print(f'\n  send_log: {conn.execute("SELECT COUNT(*) FROM send_log").fetchone()[0]} (unchanged)')
print(f'  New SMTP calls: 0 (this audit is read-only)')
print(f'  Pre-Send/Outreach: PAUSED')

conn.close()
