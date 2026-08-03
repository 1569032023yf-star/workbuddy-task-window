"""Production Inventory Audit V2 — 2026-07-29 — Strict Read-Only"""
import sqlite3
from collections import defaultdict

def s(v):
    """Safe string conversion for None values"""
    return str(v) if v is not None else 'NULL'

DB = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\data\bd_leads.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

def q(sql, params=()):
    return conn.execute(sql, params).fetchall()

def q1(sql, params=()):
    r = conn.execute(sql, params).fetchone()
    return r[0] if r else 0

def qv(sql, params=()):
    r = conn.execute(sql, params).fetchone()
    return r[0] if r else None

sep = "=" * 70

# ═══════════════════════════════════════
# SECTION 1: RAW DATABASE INVENTORY
# ═══════════════════════════════════════
print(sep)
print("SECTION 1: RAW DATABASE INVENTORY")
print(sep)

total_leads = q1("SELECT COUNT(*) FROM leads")
print(f"\n  Total Leads: {total_leads}")

statuses = q("SELECT status, COUNT(*) as cnt FROM leads GROUP BY status ORDER BY cnt DESC")
print(f"\n  Leads by Status:")
for r in statuses:
    print(f"    {s(r['status']):30s} {r['cnt']:5d}")

scores = q("SELECT confidence_score, COUNT(*) as cnt FROM leads GROUP BY confidence_score ORDER BY cnt DESC")
print(f"\n  Leads by Score:")
for r in scores:
    print(f"    {s(r['confidence_score']):10s} {r['cnt']:5d}")

auto = q("SELECT auto_sendable, COUNT(*) as cnt FROM leads GROUP BY auto_sendable ORDER BY cnt DESC")
print(f"\n  auto_sendable:")
for r in auto:
    print(f"    {s(r['auto_sendable']):45s} {r['cnt']:5d}")

sc = q("SELECT status, confidence_score, COUNT(*) as cnt FROM leads GROUP BY status, confidence_score ORDER BY cnt DESC")
print(f"\n  status x score:")
for r in sc:
    print(f"    {s(r['status']):25s} {s(r['confidence_score']):6s} {r['cnt']:5d}")

# ═══════════════════════════════════════
# SECTION 2: EXCLUSION POOLS
# ═══════════════════════════════════════
print(f"\n{sep}")
print("SECTION 2: EXCLUSION POOLS")
print(sep)

supp_count = q1("SELECT COUNT(DISTINCT email) FROM suppression_list")
print(f"\n  Suppressed (unique emails):  {supp_count}")

sent_total = q1("SELECT COUNT(*) FROM send_log WHERE status='sent'")
sent_leads = q1("SELECT COUNT(DISTINCT lead_id) FROM send_log WHERE status='sent'")
sent_emails = q1("SELECT COUNT(DISTINCT email) FROM send_log WHERE status='sent'")
print(f"  Previously Sent: records={sent_total}, leads={sent_leads}, emails={sent_emails}")

reply_count = q1("SELECT COUNT(*) FROM reply_log")
reply_leads = q1("SELECT COUNT(DISTINCT lead_id) FROM reply_log")
print(f"  Replied: {reply_count} replies, {reply_leads} leads")

bh = q1("SELECT COUNT(*) FROM bounce_log WHERE bounce_type='hard'")
bs = q1("SELECT COUNT(*) FROM bounce_log WHERE bounce_type='soft'")
print(f"  Bounces: hard={bh}, soft={bs}")

unsub = q1("SELECT COUNT(*) FROM suppression_list WHERE reason LIKE '%unsubscribe%'")
print(f"  Unsubscribed: {unsub}")

# ═══════════════════════════════════════
# SECTION 3: STRICT A0
# ═══════════════════════════════════════
print(f"\n{sep}")
print("SECTION 3: STRICT A0")
print(sep)

a0_locs = q1("SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A' AND auto_sendable=1")
print(f"\n  Strict A0 Locations (status=new, score=A, auto_sendable=1): {a0_locs}")

a0_orgs = q1("""
    SELECT COUNT(DISTINCT COALESCE(NULLIF(organization_key,''), 'org_'||id))
    FROM leads WHERE status='new' AND confidence_score='A' AND auto_sendable=1
""")
print(f"  Strict A0 Organizations (unique org_key):                  {a0_orgs}")

# Also: A0 is defined differently. Let me check what the actual scoring means
# In practice, "A0" = status='new' + evidence exists + email from website
# Let me check: score A + status new = 19 leads. But auto_sendable=1 only has 2!
# This means auto_sendable is very restrictive.
# Let me list the 19 score A + new leads
print(f"\n  All score='A' + status='new' leads (19):")
a0_all = q("""
    SELECT id, store_name, city, state, organization_key, email, auto_sendable,
           official_website, evidence_url, email_source_type
    FROM leads WHERE status='new' AND confidence_score='A'
    ORDER BY city, store_name
""")
for i, r in enumerate(a0_all):
    ws = (r['official_website'] or '')[:30]
    es = (r['evidence_url'] or '')[:30]
    print(f"    [{i+1:2d}] id={r['id']:3d} auto={s(r['auto_sendable']):30s} {s(r['store_name'])[:25]:25s} {s(r['city']):12s} {s(r['state']):3s} org={s(r['organization_key'])[:20]:20s} web={ws} ev={es} email={s(r['email'])[:30]}")

# ═══════════════════════════════════════
# SECTION 4: ORGANIZATION OUTREACH OPPORTUNITIES
# ═══════════════════════════════════════
print(f"\n{sep}")
print("SECTION 4: ORGANIZATION OUTREACH OPPORTUNITIES (FULL GATE)")
print(sep)

# Build exclusion sets
suppressed_emails = set(r[0] for r in q("SELECT DISTINCT email FROM suppression_list"))
sent_emails_set = set(r[0] for r in q("SELECT DISTINCT email FROM send_log WHERE status='sent'"))
sent_leads_set = set(r[0] for r in q("SELECT DISTINCT lead_id FROM send_log WHERE status='sent'"))
sent_orgs_set = set()
for r in q("""SELECT DISTINCT COALESCE(NULLIF(l.organization_key,''), 'org_'||sl.lead_id) 
              FROM send_log sl JOIN leads l ON sl.lead_id = l.id WHERE sl.status='sent'"""):
    sent_orgs_set.add(r[0])
# Also include legacy sends where message_type is NULL
for r in q("""SELECT DISTINCT COALESCE(NULLIF(l.organization_key,''), 'org_'||sl.lead_id)
              FROM send_log sl JOIN leads l ON sl.lead_id = l.id 
              WHERE sl.status='sent' AND (sl.message_type IS NULL OR sl.message_type='')"""):
    sent_orgs_set.add(r[0])

replied_leads = set(r[0] for r in q("SELECT DISTINCT lead_id FROM reply_log"))
hard_bounced_leads = set(r[0] for r in q("SELECT DISTINCT lead_id FROM bounce_log WHERE bounce_type='hard'"))
hard_bounced_emails = set(r[0] for r in q("SELECT DISTINCT email FROM bounce_log WHERE bounce_type='hard'"))

test_patterns = ['test@', 'example@', 'noreply@', 'no-reply@']

# Get candidates: status='new', score='A', auto_sendable=1
candidates = q("""
    SELECT id, store_name, city, state, organization_key, email,
           official_website, evidence_url,
           COALESCE(evidence_snippet,'') as evidence_snippet,
           COALESCE(email_source_type,'') as email_source_type
    FROM leads
    WHERE status='new' AND confidence_score='A' AND auto_sendable=1
    ORDER BY city, store_name
""")

print(f"\n  Input candidates (status=new, score=A, auto_sendable=1): {len(candidates)}")

valid_sources = {'official_website', 'manual_lookup', 'google_maps',
                 'facebook_page', 'chamber_directory', 'tourism_directory',
                 'main_street_directory', 'web_search', 'manual_seed'}

opportunities = []
blocked = defaultdict(list)
cf_only = 0

for c in candidates:
    lid = c['id']
    email_str = (c['email'] or '').strip().lower()
    org_raw = c['organization_key'] or ''
    org_key = org_raw.strip() if org_raw.strip() else f'org_{lid}'
    website = (c['official_website'] or '').strip()
    ev_url = (c['evidence_url'] or '').strip()
    ev_snip = c['evidence_snippet'].strip()
    email_src = c['email_source_type'].strip()

    reasons = []

    if not org_raw or not org_raw.strip():
        reasons.append('no_org_key')
    if not website:
        reasons.append('no_website')
    if not ev_url:
        reasons.append('no_evidence_url')
    if not ev_snip:
        reasons.append('no_evidence_snippet')
    if email_src == 'contact_form':
        reasons.append('contact_form_only')
        cf_only += 1
        for r in reasons:
            blocked[r].append(lid)
        continue
    if email_src and email_src not in valid_sources:
        reasons.append(f'invalid_source:{email_src}')
    if not email_str or '@' not in email_str:
        reasons.append('invalid_email')
    if any(p in email_str for p in test_patterns):
        reasons.append('test_email')
    if email_str in suppressed_emails:
        reasons.append('suppressed')
    if email_str in sent_emails_set:
        reasons.append('email_previously_sent')
    if lid in sent_leads_set:
        reasons.append('lead_previously_sent')
    if org_key in sent_orgs_set:
        reasons.append('org_previously_sent')
    if lid in replied_leads:
        reasons.append('replied')
    if lid in hard_bounced_leads or email_str in hard_bounced_emails:
        reasons.append('hard_bounced')

    if not reasons:
        opportunities.append({
            'lead_id': lid, 'organization_key': org_key,
            'store_name': c['store_name'], 'city': c['city'], 'state': c['state'],
            'email': c['email'], 'website': website, 'evidence_url': ev_url,
            'evidence_snippet': ev_snip[:80], 'email_source_type': email_src,
        })
    else:
        for r in reasons:
            blocked[r].append(lid)

# Dedup by org_key
seen = set()
unique_opps = []
for opp in opportunities:
    if opp['organization_key'] not in seen:
        seen.add(opp['organization_key'])
        unique_opps.append(opp)

print(f"  Organization Outreach Opportunities (unique orgs):  {len(unique_opps)}")
print(f"  Contact Form Only excluded:                         {cf_only}")

print(f"\n  Blocked breakdown:")
for reason, lids in sorted(blocked.items(), key=lambda x: -len(x[1])):
    print(f"    {reason:30s} {len(lids):4d} leads: {lids[:5]}")

# ═══════════════════════════════════════
# SECTION 5: PIPELINE POOLS
# ═══════════════════════════════════════
print(f"\n{sep}")
print("SECTION 5: PIPELINE POOLS")
print(sep)

manual_review = q1("""SELECT COUNT(*) FROM leads WHERE status='new' 
    AND (confidence_score != 'A' OR auto_sendable != 1 OR auto_sendable IS NULL)""")
print(f"\n  Manual Review (new, not A0):                {manual_review}")

website_lookup = q1("""SELECT COUNT(*) FROM leads WHERE status='new' 
    AND (email IS NULL OR email = '' OR evidence_url IS NULL OR evidence_url = '')""")
print(f"  Website Lookup (new, missing email/ev):      {website_lookup}")

cfo = q1("SELECT COUNT(*) FROM leads WHERE email_source_type='contact_form'")
print(f"  Contact Form Only:                           {cfo}")

low_pri = q1("""SELECT COUNT(*) FROM leads WHERE status='new' 
    AND confidence_score NOT IN ('A', 'A0')""")
print(f"  Low Priority (new, not A):                   {low_pri}")

# Bounce Recovery: leads with bounce but not suppressed
bounce_recovery = q1("""
    SELECT COUNT(DISTINCT l.id) FROM leads l
    JOIN bounce_log b ON l.id = b.lead_id
    WHERE b.bounce_type = 'hard'
    AND l.email NOT IN (SELECT email FROM suppression_list)
""")
print(f"  Bounce Recovery (bounced, not suppressed):    {bounce_recovery}")

# Staging
sr = q1("SELECT COUNT(*) FROM lead_discovery_results")
sh = q1("SELECT COUNT(*) FROM lead_discovery_hits")
print(f"  Staging: discovery_results={sr}, discovery_hits={sh}")

# ═══════════════════════════════════════
# SECTION 6: INTEGRITY
# ═══════════════════════════════════════
print(f"\n{sep}")
print("SECTION 6: SEND INTEGRITY")
print(sep)

slc = q1("SELECT COUNT(*) FROM send_log")
print(f"\n  send_log:               {slc}")
fsp_p = q1("SELECT COUNT(*) FROM final_send_plan WHERE status='planned'")
fsp_s = q1("SELECT COUNT(*) FROM final_send_plan WHERE status='sent'")
print(f"  Final Send Plan:        planned={fsp_p}, sent={fsp_s}")
trk_a = q1("SELECT COUNT(*) FROM email_tracking_messages WHERE status='active'")
trk_p = q1("SELECT COUNT(*) FROM email_tracking_messages WHERE status='prepared'")
print(f"  Tracking:               active={trk_a}, prepared={trk_p}")

# ═══════════════════════════════════════
# SECTION 7: DETAIL
# ═══════════════════════════════════════
print(f"\n{sep}")
print(f"SECTION 7: OPPORTUNITY DETAIL — {len(unique_opps)} organizations")
print(sep)

for i, opp in enumerate(unique_opps):
    print(f"\n  [{i+1}] lead_id={opp['lead_id']} | {s(opp['store_name'])}")
    print(f"       org_key:      {opp['organization_key']}")
    print(f"       location:     {s(opp['city'])}, {s(opp['state'])}")
    print(f"       email:        {s(opp['email'])}")
    print(f"       website:      {opp['website'][:60]}")
    print(f"       evidence_url: {opp['evidence_url'][:60]}")
    print(f"       evidence:     {opp['evidence_snippet']}")
    print(f"       email_src:    {opp['email_source_type']}")
    print(f"       allow_send:   YES")

# ═══════════════════════════════════════
# SECTION 8: 60-SEND READINESS
# ═══════════════════════════════════════
print(f"\n{sep}")
print("SECTION 8: 60-SEND READINESS")
print(sep)

gap = 60 - len(unique_opps)
print(f"\n  Qualified Organizations:        {len(unique_opps)}")
print(f"  Target (60):                    60")
status_60 = "SURPLUS" if gap <= 0 else "GAP"
print(f"  Status:                         {status_60}: {abs(gap)}")
print(f"  Tonight max (no compromises):   {len(unique_opps)}")
print(f"\n  Cannot fill from:")
print(f"    Manual Review:                {manual_review}")
print(f"    Website Lookup:               {website_lookup}")  
print(f"    Contact Form Only:            {cfo}")
print(f"    Low Priority:                 {low_pri}")
print(f"    Staging:                      {sr}")

if gap > 0:
    print(f"\n  ⚠ REAL GAP: {gap} organizations short of 60")

print(f"\n  Proposed thresholds (60/day, for approval):")
print(f"    Critical=60, Warning=120, Target=180")

conn.close()
print(f"\n{sep}")
print("AUDIT COMPLETE — Read-only")
print(sep)
