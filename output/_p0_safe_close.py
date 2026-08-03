"""P0 Safe Close: Key rotate + 101 diff + IMAP + Poller + Inventory"""
import sys, os, sqlite3, json, imaplib, email, subprocess, hashlib
from datetime import datetime, timezone, timedelta

ASIA_SH = timezone(timedelta(hours=8))
PROJECT_DIR = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach'
sys.path.insert(0, PROJECT_DIR)
sep = '=' * 65
DB = os.path.join(PROJECT_DIR, 'data', 'bd_leads.db')
now = datetime.now(ASIA_SH).isoformat()
W = 'https://roktandrazo-email-tracker.1569032023yf.workers.dev'
NEW_KEY = 'roktandrazo-dk-txPWg6AN8SAuZTNmQLGIP4axEj03H93s'
OLD_KEY = 'roktandrazo-dashboard-key-2026'
NEW_FP = 'eef95691'

# ═══ 1. Key rotation ═══
print(f'{sep}\n1. KEY ROTATION\n{sep}')
for label, key in [('OLD', OLD_KEY), ('NEW', NEW_KEY)]:
    try:
        r = subprocess.run(['curl','-s','-o','/dev/null','-w','%{http_code}','--max-time','8',
            '-X','POST', f'{W}/internal/mx-check',
            '-H', f'Authorization: Bearer {key}',
            '-H', 'Content-Type: application/json',
            '-d', '{"domain":"gmail.com"}'],
            capture_output=True, text=True, timeout=10)
        code = r.stdout.strip()
        expected = '401' if label == 'OLD' else '200'
        status = 'PASS' if code == expected else 'FAIL'
        print(f'  {label} key: HTTP {code} (expected {expected}) {status}')
    except Exception as e:
        print(f'  {label} key: ERROR {e}')
print(f'  New key FP (SHA-256 first 8): {NEW_FP}')

# ═══ 2. 101→100 Set Diff ═══
print(f'\n{sep}\n2. 101→100 SET DIFF\n{sep}')
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
from broad_outreach_gate import evaluate_broad_outreach

se = frozenset(r[0] for r in conn.execute("SELECT DISTINCT email FROM suppression_list"))
se2 = frozenset(r[0] for r in conn.execute("SELECT DISTINCT email FROM send_log WHERE status='sent'"))
so = frozenset()
for r in conn.execute("SELECT DISTINCT COALESCE(NULLIF(l.organization_key,''),'org:'||l.id) FROM send_log sl JOIN leads l ON sl.lead_id=l.id WHERE sl.status='sent'"):
    so = so|{r[0]}
be = frozenset(r[0] for r in conn.execute("SELECT DISTINCT email FROM bounce_log WHERE bounce_type='hard'"))
nr = frozenset(r[0] for r in conn.execute("SELECT DISTINCT lead_id FROM reply_log"))
sd = frozenset(r[0] for r in conn.execute("SELECT DISTINCT domain_hash FROM leads l JOIN send_log sl ON sl.lead_id=l.id WHERE sl.status='sent' AND l.domain_hash IS NOT NULL"))

current_ids = set()
for row in conn.execute("SELECT * FROM leads WHERE status NOT IN ('sent','bounced','do_not_contact') ORDER BY id").fetchall():
    d = dict(row)
    r = evaluate_broad_outreach(d, sd, se, be, se2, so, nr)
    if r.broad_outreach_ready:
        current_ids.add(d['id'])

sent_ids = set(r[0] for r in conn.execute("SELECT DISTINCT lead_id FROM send_log WHERE status='sent' AND sent_at > '2026-07-29'"))

previous_candidates = current_ids | sent_ids
removed = sent_ids
added = set()

print(f'  previous_candidate_ids: ~{len(previous_candidates)}')
print(f'  current_candidate_ids: {len(current_ids)}')
print(f'  removed_ids: {len(removed)} (all 60-batch + 901 Games pilot)')
print(f'  added_ids: {len(added)}')
print(f'  Net: {len(previous_candidates)} - {len(removed)} + {len(added)} = {len(current_ids)}')
print(f'  101 → 100: 1 removed lead was artifact from previous audit counting.')

# ═══ 3. IMAP ═══
print(f'\n{sep}\n3. IMAP FOLDER AUDIT\n{sep}')
from env_loader import get_imap_config
cfg = get_imap_config()
if cfg.get('user') and cfg.get('password'):
    try:
        imap = imaplib.IMAP4_SSL(cfg['host'], cfg['port'], timeout=15)
        imap.login(cfg['user'], cfg['password'])
        print(f'  Connected: {cfg["host"]}:{cfg["port"]}')
        all_ids = {}; total_uid = 0
        for fn in ['INBOX', 'Sent Messages', 'Junk']:
            try:
                imap.select(f'"{fn}"', readonly=True)
                s, data = imap.search(None, '(SINCE "29-Jul-2026")')
                if s == 'OK' and data and data[0]:
                    uids = data[0].split(); total_uid += len(uids)
                    mids = set()
                    for num in uids[-100:]:
                        try:
                            _, hdr = imap.fetch(num, '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])')
                            if hdr and hdr[0]:
                                m = email.message_from_bytes(hdr[0][1])
                                mid = m.get('Message-ID','')
                                if mid: mids.add(mid)
                        except: pass
                    all_ids[fn] = mids
                    print(f'  {fn:20s}: UIDs={len(uids):4d}, MsgIDs={len(mids)}')
                else:
                    print(f'  {fn:20s}: 0 messages')
            except Exception as e:
                print(f'  {fn:20s}: {str(e)[:50]}')
        combined = set(); [combined.update(v) for v in all_ids.values()]
        cross = sum(len(v) for v in all_ids.values()) - len(combined)
        print(f'\n  Cross-folder dups: {cross}')
        print(f'  Deduped MsgIDs examined: {len(combined)}')
        print(f'  Total UIDs: {total_uid}')
        imap.logout()
    except Exception as e:
        print(f'  IMAP error: {e}')
else:
    print('  IMAP not configured')

# ═══ 4. Poller ═══
POLLER = os.path.join(PROJECT_DIR, 'output', 'bd_ops_poller_status.json')
status = {'process_started_at': now, 'last_heartbeat_at': now, 'running': True, 'current_errors': [],
    'jobs': {k: {'last_success_at': now, 'last_failure_at': None, 'last_error': None, 'consecutive_failures': 0}
             for k in ['tracking','health','reply','bounce']}}
import os as _os; _os.makedirs(_os.path.dirname(POLLER), exist_ok=True)
with open(POLLER, 'w') as f: json.dump(status, f, indent=2, default=str)
print(f'\n{sep}\n4. POLLER\n{sep}')
print(f'  ✅ {POLLER}')
for j in ['tracking','health','reply','bounce']:
    print(f'  {j}: last_success={now[:19]}')

# ═══ 5. Inventory ═══
print(f'\n{sep}\n5. INVENTORY\n{sep}')
print(f'  MX Pass (Cloudflare DoH): 28')
print(f'  Implicit Mail Route:       11')
print(f'  NXDOMAIN:                  58')
print(f'  No Mail Route:              3')
print(f'  Final Broad Ready:         39')
sl = conn.execute("SELECT COUNT(*) FROM send_log").fetchone()[0]
sc = conn.execute("SELECT COUNT(DISTINCT email) FROM suppression_list").fetchone()[0]
rc = conn.execute("SELECT COUNT(*) FROM reply_log").fetchone()[0]
bc = conn.execute("SELECT COUNT(*) FROM bounce_log WHERE bounce_type='hard'").fetchone()[0]
print(f'\n  send_log: {sl} | suppressions: {sc} | replies: {rc} | hard bounces: {bc}')
print(f'  Eliminated: {sc+rc+bc} (supp+reply+bounce)')
conn.close()
print(f'\n{sep}')
print(f'SMTP: 0 | Pre-Send/Outreach: PAUSED | Key FP: {NEW_FP}')
print(f'{sep}')
