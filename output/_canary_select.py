import sqlite3
DB=r'C:/Users/15690/WorkBuddy/2026-06-05-15-31-42/roktandrazo-outreach/data/bd_leads.db'
c=sqlite3.connect(DB); cur=c.cursor()

print('--- suppression_list schema ---')
cur.execute('PRAGMA table_info(suppression_list)')
print([r[1] for r in cur.fetchall()])
print('--- send_log schema ---')
cur.execute('PRAGMA table_info(send_log)')
print([r[1] for r in cur.fetchall()])

# planned FSPs for today
cur.execute("""SELECT fsp.id, fsp.lead_id, fsp.recipient_email, l.store_name, l.state, l.city,
                      l.evidence_url, l.evidence_snippet, l.email_verified_on_official_site,
                      l.mx_provider, l.recipient_timezone, l.timezone_status,
                      l.email_sendable, l.sendable_for_automatic_schedule, l.send_eligibility,
                      l.sent_at
               FROM final_send_plan fsp JOIN leads l ON l.id=fsp.lead_id
               WHERE fsp.outreach_batch_date='2026-08-20' AND fsp.status='planned'
               ORDER BY fsp.id""")
rows=cur.fetchall()
cols=[d[0] for d in cur.description]
print(f'\n--- {len(rows)} planned FSPs for 2026-08-20 ---')

# suppression set
cur.execute("SELECT * FROM suppression_list")
supp_cols=[d[0] for d in cur.description]
print('suppression rows:', len(cur.fetchall()), '| cols:', supp_cols)

# send_log lead_ids
cur.execute("SELECT DISTINCT lead_id FROM send_log")
sent_leads=set(r[0] for r in cur.fetchall())

# domain counts among planned
from collections import Counter
domains=Counter()
for r in rows:
    email=r[2] or ''
    dom=email.split('@')[-1] if '@' in email else ''
    domains[dom]+=1

print('\n--- CANARY CANDIDATE SCREENING ---')
cands=[]
for r in rows:
    d=dict(zip(cols,r))
    email=d['recipient_email'] or ''
    dom=email.split('@')[-1] if '@' in email else ''
    # checks
    official_evidence = bool(d['evidence_url']) and bool(d['evidence_snippet']) and (d['email_verified_on_official_site']==1)
    mx_pass = bool(d['mx_provider'])  # proxy
    tz_resolved = bool(d['recipient_timezone']) and d['timezone_status'] not in (None,'TIMEZONE_UNRESOLVED','unresolved')
    unsent = (d['sent_at'] is None) and (d['lead_id'] not in sent_leads)
    # suppression: check by email or domain in suppression_list (try common cols)
    suppressed=False
    try:
        cur.execute("SELECT 1 FROM suppression_list WHERE email=? OR domain=? LIMIT 1", (email, dom))
        suppressed = cur.fetchone() is not None
    except Exception:
        pass
    dup = domains[dom] > 1
    ok = official_evidence and mx_pass and tz_resolved and unsent and not suppressed and not dup
    if ok:
        cands.append((d['id'], d['lead_id'], d['store_name'], d['state'], d['city'], email, dom, d['mx_provider'], d['recipient_timezone']))
        print(f"  OK fsp={d['id']} lead={d['lead_id']} {d['store_name']} ({d['state']}/{d['city']}) {email} mx={d['mx_provider']} tz={d['recipient_timezone']}")

print(f'\n=== VIABLE CANARY CANDIDATES: {len(cands)} ===')
if cands:
    top=cands[0]
    print('TOP CANARY -> fsp_id=%s lead_id=%s %s (%s/%s) %s' % top[:6])
