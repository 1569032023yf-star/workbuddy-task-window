"""catchup_outreach_20260731 — Calculate eligible orgs, create plan, send"""
import sys, os, sqlite3, json, hashlib, subprocess, time
from datetime import datetime, timezone, timedelta

ASIA_SH = timezone(timedelta(hours=8))
PROJECT_DIR = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach'
sys.path.insert(0, PROJECT_DIR)
DB = os.path.join(PROJECT_DIR, 'data', 'bd_leads.db')
now = datetime.now(ASIA_SH)
BATCH_ID = 'catchup_outreach_20260731'
W = 'https://roktandrazo-email-tracker.1569032023yf.workers.dev/internal/mx-check'
AUTH_HDR = 'Bearer roktandrazo-dk-45llgR7F_BKGU3RzW6Qq8ieVW4BE3XXjMo_J6LQtzEw'
sep = '=' * 65

# ═══════════════════════════════════
# STEP 1: Freeze and calculate
# ═══════════════════════════════════
print(f'{sep}\nSTEP 1: INVENTORY SNAPSHOT + ELIGIBLE CALCULATION\n{sep}')
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# Save snapshot
snap_file = os.path.join(PROJECT_DIR, 'output', f'inventory_snapshot_{BATCH_ID}.json')
snap = {'batch_id': BATCH_ID, 'frozen_at': now.isoformat(),
    'database_sha256': hashlib.sha256(open(DB, 'rb').read()).hexdigest()[:16]}
with open(snap_file, 'w') as f: json.dump(snap, f, indent=2)
print(f'  Snapshot: {snap_file}')

# Build exclusion sets
se = frozenset(r[0] for r in conn.execute("SELECT DISTINCT email FROM suppression_list"))
se2 = frozenset((r[0] or '').lower() for r in conn.execute("SELECT DISTINCT email FROM send_log WHERE status='sent'"))
so = frozenset()
for r in conn.execute("SELECT DISTINCT COALESCE(NULLIF(l.organization_key,''),'org:'||l.id) FROM send_log sl JOIN leads l ON sl.lead_id=l.id WHERE sl.status='sent'"):
    so = so|{r[0]}
for r in conn.execute("SELECT DISTINCT COALESCE(NULLIF(l.organization_key,''),'org:'||l.id) FROM send_log sl JOIN leads l ON sl.lead_id=l.id WHERE sl.status='sent' AND (sl.message_type IS NULL OR sl.message_type='')"):
    so = so|{r[0]}
be = frozenset(r[0] for r in conn.execute("SELECT DISTINCT email FROM bounce_log WHERE bounce_type='hard'"))
nr = frozenset(r[0] for r in conn.execute("SELECT DISTINCT lead_id FROM reply_log"))

# Invalid email patterns
import re
invalid_pat = re.compile(r'(\.png|\.jpg|\.gif|\.webp|\.jpeg|\.svg|\.css|\.js\b|sentry\.io|noreply|no-reply|donotreply|example\.com|@2x|\d+x\d+|^www\.|^xxx@)')

def mx_check(domain):
    try:
        r = subprocess.run(['curl','-s','--max-time','8','-X','POST',W,
            '-H',f'Authorization: {AUTH_HDR}','-H','Content-Type: application/json',
            '-d',json.dumps({'domain':domain})],
            capture_output=True, text=True, timeout=10)
        data = json.loads(r.stdout) if r.stdout else {}
        return data.get('mx_status', 'error')
    except: return 'retry_pending'

eligible = {'TN': [], 'AR': [], 'KY': []}
stats = {'checked': 0, 'mx_pass': 0, 'implicit': 0, 'mx_fail': 0, 'blocked_history': 0, 'blocked_suppression': 0,
         'blocked_bounce': 0, 'blocked_reply': 0, 'blocked_invalid': 0, 'blocked_contact_form': 0,
         'blocked_org_sent': 0, 'blocked_email_sent': 0, 'blocked_no_org': 0}

# Get all sendable candidates (A0 + Manual A0 + all with valid email)
candidates = conn.execute("""
    SELECT * FROM leads WHERE state IN ('TN','AR','KY')
    AND status NOT IN ('sent','bounced','do_not_contact')
    AND email IS NOT NULL AND email != '' AND email LIKE '%@%.%'
    AND (email_source_type != 'contact_form' OR email_source_type IS NULL)
    ORDER BY 
        CASE WHEN state='TN' THEN 1 WHEN state='AR' THEN 2 ELSE 3 END,
        CASE WHEN confidence_score='A' THEN 1 ELSE 2 END
""").fetchall()

print(f'  Candidates: {len(candidates)}')

for row in candidates:
    lead = dict(row)
    lid = lead['id']; email = (lead['email'] or '').lower().strip()
    org_key = lead['organization_key'] or ''
    state = lead['state']
    stats['checked'] += 1
    
    # Hard gates
    if not email or '@' not in email:
        stats['blocked_invalid'] += 1; continue
    if invalid_pat.search(email):
        stats['blocked_invalid'] += 1; continue
    if not org_key:
        stats['blocked_no_org'] += 1; continue
    if email in se:
        stats['blocked_suppression'] += 1; continue
    if email in se2:
        stats['blocked_email_sent'] += 1; continue
    if email in be:
        stats['blocked_bounce'] += 1; continue
    if org_key in so:
        stats['blocked_org_sent'] += 1; continue
    if lid in nr:
        stats['blocked_reply'] += 1; continue
    if lead['status'] == 'contact_form_pool':
        stats['blocked_contact_form'] += 1; continue
    
    # MX check
    domain = email.split('@')[1]
    mx_status = mx_check(domain)
    if mx_status in ('mx_pass', 'implicit_mail_route'):
        if mx_status == 'mx_pass': stats['mx_pass'] += 1
        else: stats['implicit'] += 1
        eligible[state].append({'id': lid, 'email': email, 'org': org_key, 'name': lead['store_name'],
                                'score': lead['confidence_score'], 'city': lead['city'] or ''})
    else:
        stats['mx_fail'] += 1

# Dedup by org within each state, TN priority
selected = []
seen_orgs = set()
seen_emails = set()
for st in ['TN', 'AR', 'KY']:
    st_selected = 0
    # A0 first, then Broad
    for entry in sorted(eligible[st], key=lambda e: (0 if e['score']=='A' else 1)):
        if len(selected) >= 60: break
        if entry['org'] in seen_orgs: continue
        if entry['email'] in seen_emails: continue
        selected.append({**entry, 'state': st})
        seen_orgs.add(entry['org'])
        seen_emails.add(entry['email'])
        st_selected += 1
    if len(selected) >= 60: break

print(f'\n  TN eligible: {len(eligible["TN"])} | AR: {len(eligible["AR"])} | KY: {len(eligible["KY"])}')
print(f'  Selected for batch: {len(selected)}')
print(f'  Blocks: history={stats["blocked_org_sent"]} supp={stats["blocked_suppression"]} bounce={stats["blocked_bounce"]} reply={stats["blocked_reply"]} invalid={stats["blocked_invalid"]} no_org={stats["blocked_no_org"]} mx_fail={stats["mx_fail"]}')
print(f'  MX: pass={stats["mx_pass"]} implicit={stats["implicit"]} fail={stats["mx_fail"]}')

# Per state selection count
for st in ['TN','AR','KY']:
    st_cnt = sum(1 for s in selected if s['state']==st)
    print(f'  {st} selected: {st_cnt}')

# Save eligible list
with open(os.path.join(PROJECT_DIR, 'output', f'{BATCH_ID}_eligible.json'), 'w') as f:
    json.dump(selected, f, indent=2, default=str)

conn.close()
print(f'\n  Eligible saved. Proceeding to plan creation...')
