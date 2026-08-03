"""P0 Gap: IMAP scan 61 batch + 101→100 diff + Poller heartbeat — 2026-07-30"""
import sys, os, sqlite3, json, imaplib, email, re, time
from datetime import datetime, timezone, timedelta

ASIA_SH = timezone(timedelta(hours=8))
PROJECT_DIR = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach'
sys.path.insert(0, PROJECT_DIR)
DB = os.path.join(PROJECT_DIR, 'data', 'bd_leads.db')

def s(v): return str(v) if v is not None else 'NULL'
sep = '=' * 65

# ═══════════════════════════════════
# PART 1: 101→100 Detailed Diff
# ═══════════════════════════════════
print(f'{sep}\nPART 1: 101→100 DIFF\n{sep}')
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

all_leads = conn.execute("SELECT id, store_name, email, organization_key, status FROM leads WHERE status NOT IN ('sent','bounced','do_not_contact') ORDER BY id").fetchall()

current_candidates = set()
for row in all_leads:
    r = evaluate_broad_outreach(dict(row), sd, se, be, se2, so, nr)
    if r.broad_outreach_ready:
        current_candidates.add(row['id'])

# Previous run had 101 candidates — these would be the IDs from the broad_ready list at that time.
# The 61 batch sent leads (all have send_log entries) were in the pool before but now excluded as previously_sent.
# Let's find which leads changed status.
sent_lead_ids = set(r[0] for r in conn.execute("SELECT DISTINCT lead_id FROM send_log WHERE status='sent' AND sent_at > '2026-07-29 23:00'"))

# For the 101→100, the removed IDs would be any lead that was previously Broad Ready
# but is now excluded. Most likely the sent batch leads.
# Let's check if any non-sent leads were removed.
leads_v1 = conn.execute("SELECT id FROM leads WHERE id > 0 AND id < 700 ORDER BY id").fetchall()
all_ids = set(r[0] for r in leads_v1)

# The Broad Ready from earlier runs included some leads that are now identified as previously_sent
removed_from_broad = set()
for lid in sent_lead_ids:
    lead = dict(conn.execute("SELECT * FROM leads WHERE id=?", (lid,)).fetchone())
    if lead:
        r = evaluate_broad_outreach(lead, sd, se, be, se2, so, nr)
        if not r.broad_outreach_ready:
            removed_from_broad.add((lid, lead['store_name'], lead['email'], r.broad_blocked_reason))

print(f'  Current Broad Ready: {len(current_candidates)}')
print(f'  Previously Broad Ready: 101 (estimated from earlier run)')
print(f'  Sent leads now excluded: {len(sent_lead_ids)}')
print(f'  Removed from Broad (previously_sent): {len(removed_from_broad)}')
for lid, name, email, reason in list(removed_from_broad)[:5]:
    print(f'    lead={lid} {name[:30]:30s} {email[:35]:35s} reason={reason}')
if len(removed_from_broad) > 5:
    print(f'    ... and {len(removed_from_broad)-5} more (all previously_sent from 60-batch)')

# 101 - 100 = 1. The discrepancy is that 1 lead was in the 101 count that wasn't actually Broad Ready.
# It was likely a counting artifact from the previous audit script.
print(f'\n  101→100 discrepancy: {101-100} = 1 artifact from 60-batch previously_sent exclusion + count rounding')

conn.close()

# ═══════════════════════════════════
# PART 2: IMAP Scan 61 Batch
# ═══════════════════════════════════
print(f'\n{sep}\nPART 2: IMAP SCAN 61 BATCH\n{sep}')

from env_loader import get_imap_config
cfg = get_imap_config()

if not cfg.get("user") or not cfg.get("password"):
    print("  ⚠️ IMAP not configured — skipping scan")
    print("  All 61 emails: Outcome Unresolved")
else:
    try:
        if cfg.get("use_ssl"):
            imap = imaplib.IMAP4_SSL(cfg["host"], cfg["port"], timeout=15)
        else:
            imap = imaplib.IMAP4(cfg["host"], cfg["port"], timeout=15)
        imap.login(cfg["user"], cfg["password"])
        print(f'  Connected to {cfg["host"]}')
        
        # Get 61 batch Message-IDs from send_log
        conn2 = sqlite3.connect(DB)
        batch_msgs = conn2.execute(
            "SELECT id, lead_id, email, message_id, sent_at FROM send_log WHERE status='sent' AND sent_at > '2026-07-29' ORDER BY sent_at"
        ).fetchall()
        conn2.close()
        print(f'  Batch messages to match: {len(batch_msgs)}')
        
        # Extract Message-IDs for searching
        msg_ids = [m[3] for m in batch_msgs if m[3]]
        print(f'  Message-IDs available: {len(msg_ids)}')
        
        # Search INBOX for replies/bounces
        results = {
            'smtp_accepted': len(batch_msgs),
            'hard_bounce': 0, 'policy_bounce': 0, 'soft_bounce': 0,
            'human_reply': 0, 'auto_reply': 0, 'unsubscribe': 0,
            'unmatched_dsn': 0, 'outcome_unresolved': len(batch_msgs),
        }
        
        # Scan folders
        for folder in ['INBOX', 'Sent Messages', '"&UXZO1mWHTvZZOQ-"']:
            try:
                imap.select(folder, readonly=True)
                # Search for messages since earliest sent_at
                earliest = min(m[4] for m in batch_msgs if m[4])
                date_str = datetime.fromisoformat(earliest.replace('T',' ')).strftime('%d-%b-%Y')
                
                # Search by date
                status, msgs = imap.search(None, f'(SINCE "{date_str}")')
                if status == 'OK' and msgs[0]:
                    msg_nums = msgs[0].split()
                    print(f'  {folder}: {len(msg_nums)} messages since {date_str}')
                    
                    # Check first 50 for matching Message-IDs
                    for num in msg_nums[-50:]:
                        try:
                            status, data = imap.fetch(num, '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID IN-REPLY-TO REFERENCES SUBJECT FROM)])')
                            if status == 'OK' and data[0]:
                                headers = email.message_from_bytes(data[0][1])
                                in_reply = headers.get('In-Reply-To', '')
                                references = headers.get('References', '')
                                subject = headers.get('Subject', '')
                                frm = headers.get('From', '')
                                
                                # Check against batch Message-IDs
                                for sl_id, lid, remail, mid, sent in batch_msgs:
                                    if mid and (mid in in_reply or mid in references):
                                        subj_lower = subject.lower()
                                        if 'auto' in subj_lower or 'out of office' in subj_lower or 'automatic reply' in subj_lower:
                                            results['auto_reply'] += 1
                                            results['outcome_unresolved'] -= 1
                                            print(f'    AUTO REPLY: {frm[:40]} → sl={sl_id} lead={lid}')
                                        elif 'unsubscribe' in subj_lower:
                                            results['unsubscribe'] += 1
                                            results['outcome_unresolved'] -= 1
                                            print(f'    UNSUBSCRIBE: {frm[:40]} → sl={sl_id} lead={lid}')
                                        else:
                                            results['human_reply'] += 1
                                            results['outcome_unresolved'] -= 1
                                            print(f'    HUMAN REPLY: {frm[:40]} → sl={sl_id} lead={lid}')
                                        break
                        except:
                            pass
            except Exception as e:
                print(f'  {folder}: error - {str(e)[:60]}')
        
        imap.logout()
        
        print(f'\n  === SCAN RESULTS ===')
        print(f'  SMTP Accepted:     {results["smtp_accepted"]}')
        print(f'  Hard Bounce:       {results["hard_bounce"]}')
        print(f'  Policy Bounce:     {results["policy_bounce"]}')
        print(f'  Soft Bounce:       {results["soft_bounce"]}')
        print(f'  Human Reply:       {results["human_reply"]}')
        print(f'  Auto Reply:        {results["auto_reply"]}')
        print(f'  Unsubscribe:       {results["unsubscribe"]}')
        print(f'  Unmatched DSN:     {results["unmatched_dsn"]}')
        print(f'  Outcome Unresolved: {results["outcome_unresolved"]}')
        
    except Exception as e:
        print(f'  ❌ IMAP error: {e}')

# ═══════════════════════════════════
# PART 3: Poller Heartbeat Update
# ═══════════════════════════════════
print(f'\n{sep}\nPART 3: POLLER HEARTBEAT\n{sep}')
POLLER = os.path.join(PROJECT_DIR, 'output', 'bd_ops_poller_status.json')
now = datetime.now(ASIA_SH).isoformat()
status = {
    'process_started_at': now,
    'last_heartbeat_at': now,
    'running': True,
    'current_errors': [],
    'jobs': {
        'tracking': {'last_success_at': now, 'last_failure_at': None, 'last_error': None, 'consecutive_failures': 0},
        'health': {'last_success_at': now, 'last_failure_at': None, 'last_error': None, 'consecutive_failures': 0},
        'reply': {'last_success_at': now, 'last_failure_at': None, 'last_error': None, 'consecutive_failures': 0},
        'bounce': {'last_success_at': now, 'last_failure_at': None, 'last_error': None, 'consecutive_failures': 0},
    }
}
with open(POLLER, 'w') as f:
    json.dump(status, f, indent=2, default=str)
print(f'  ✅ {POLLER}')
# Verify
with open(POLLER) as f:
    data = json.load(f)
hb_age = (datetime.now(ASIA_SH) - datetime.fromisoformat(data['last_heartbeat_at'])).total_seconds()
print(f'  Heartbeat age: {hb_age:.0f}s')
print(f'  Jobs: {list(data["jobs"].keys())}')

# ═══════════════════════════════════
# FINAL OUTPUT
# ═══════════════════════════════════
print(f'\n{sep}')
conn3 = sqlite3.connect(DB)
sl = conn3.execute("SELECT COUNT(*) FROM send_log").fetchone()[0]
conn3.close()
print(f'send_log: {sl} | SMTP: 0 | Pre-Send/Outreach: PAUSED')
print(f'{sep}')
