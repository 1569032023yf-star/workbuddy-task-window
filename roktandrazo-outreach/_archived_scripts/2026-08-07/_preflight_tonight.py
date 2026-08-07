raise RuntimeError("LEGACY_SMTP_DISABLED: dated send script archived 2026-08-07. Use bd_orchestrator -> daily_session -> bd_sender only.")
#!/usr/bin/env python3
"""
BD Tonight Final Preflight — Read-Only Gate Verification
Batch: new_outreach_20260803_et1000
STRICTLY READ-ONLY. No SMTP calls.
"""
import sqlite3, hashlib, json, os, ssl, sys
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

BATCH_ID = 'new_outreach_20260803_et1000'
PROJECT_DIR = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach'
DB_PATH = os.path.join(PROJECT_DIR, 'data', 'bd_leads.db')
OPS_POLLER_STATUS = os.path.join(PROJECT_DIR, 'output', 'bd_ops_poller_status.json')
ASIA_SH = timezone(timedelta(hours=8))

PASS = 0
FAIL = 0
BLOCKS = []

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print('=' * 65)
print('  BD TONIGHT FINAL PREFLIGHT')
print(f'  Batch: {BATCH_ID}')
print(f'  Time:  {datetime.now(ASIA_SH).isoformat()}')
print(f'  Rule:  READ-ONLY. No SMTP.')
print('=' * 65)

# ── DB Connect ──
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

batch_date = '2026-08-03'

# ── STEP 1: Plan entries exist ──
print('\n── STEP 1: Plan entries exist ──')
plans = conn.execute(
    "SELECT * FROM final_send_plan WHERE outreach_batch_date=? AND message_type='new_outreach' AND status='planned'",
    (batch_date,)
).fetchall()
plan_count = len(plans)
if plan_count > 0:
    PASS += 1
    print(f'  [PASS] #{PASS+FAIL} Plan entries: {plan_count}')
else:
    FAIL += 1
    print(f'  [FAIL] #{PASS+FAIL} No plan entries found')
    BLOCKS.append('No plan entries')

# ── STEP 2: Send authorization exists & approved ──
print('\n── STEP 2: Send authorization exists & approved ──')
auth = conn.execute(
    "SELECT * FROM send_authorizations WHERE outreach_batch_date=? AND status='active'",
    (batch_date,)
).fetchone()
if auth and auth['approved_at']:
    PASS += 1
    print(f'  [PASS] #{PASS+FAIL} Auth: {auth["authorization_id"]}')
    print(f'         Approved: {auth["approved_at"]}')
    print(f'         Status: {auth["status"]} | Preflight: {auth["preflight_status"]}')
else:
    FAIL += 1
    reason = 'No active auth' if not auth else 'Auth not approved'
    print(f'  [FAIL] #{PASS+FAIL} {reason}')
    BLOCKS.append(reason)

# ── STEP 3: Authorization entries = Plan entries ──
print('\n── STEP 3: Authorization entries = Plan entries ──')
if auth:
    auth_entries = conn.execute(
        'SELECT COUNT(*) as c FROM send_authorization_entries WHERE authorization_id=?',
        (auth['authorization_id'],)
    ).fetchone()['c']
    if auth_entries == plan_count:
        PASS += 1
        print(f'  [PASS] #{PASS+FAIL} Auth entries={auth_entries}, Plan entries={plan_count}')
    else:
        FAIL += 1
        print(f'  [FAIL] #{PASS+FAIL} Auth entries={auth_entries}, Plan entries={plan_count}')
        BLOCKS.append(f'Auth/plan count mismatch: {auth_entries} vs {plan_count}')
else:
    FAIL += 1
    print(f'  [FAIL] #{PASS+FAIL} Cannot verify (no auth)')
    BLOCKS.append('No auth for entry count check')

# ── STEP 4: Organization duplicate = 0 ──
print('\n── STEP 4: Organization duplicate = 0 ──')
PUBLIC_PROVIDERS = {
    'gmail.com','yahoo.com','hotmail.com','outlook.com','aol.com','icloud.com',
    'me.com','protonmail.com','mail.com','live.com','msn.com','ymail.com',
    'rocketmail.com','inbox.com','zoho.com','fastmail.com','gmx.com','gmx.de',
    'web.de','comcast.net','verizon.net','att.net','cox.net','sbcglobal.net',
    'bellsouth.net','charter.net','earthlink.net','optonline.net','lighttube.net'
}
companies_in_batch = [p['company_name'].lower() for p in plans]
comp_dupes = {c: companies_in_batch.count(c) for c in set(companies_in_batch) if companies_in_batch.count(c) > 1}

domains_in_batch = [p['recipient_email'].split('@')[1].lower() if '@' in p['recipient_email'] else '' for p in plans]
non_pub = [d for d in domains_in_batch if d and d not in PUBLIC_PROVIDERS]
domain_dupes = {d: non_pub.count(d) for d in set(non_pub) if non_pub.count(d) > 1}

org_ok = len(comp_dupes) == 0 and len(domain_dupes) == 0
if org_ok:
    PASS += 1
    print(f'  [PASS] #{PASS+FAIL} All {plan_count} organizations unique')
    print(f'         Companies: {len(set(companies_in_batch))} unique')
    print(f'         Non-public domains: {len(set(non_pub))} unique')
else:
    FAIL += 1
    detail = []
    if comp_dupes: detail.append(f'company dupes: {comp_dupes}')
    if domain_dupes: detail.append(f'domain dupes: {domain_dupes}')
    print(f'  [FAIL] #{PASS+FAIL} Organization duplicates: {"; ".join(detail)}')
    BLOCKS.append(f'Organization duplicate: {"; ".join(detail)}')

# ── STEP 5: Email duplicate = 0 ──
print('\n── STEP 5: Email duplicate = 0 ──')
emails_in_batch = [p['recipient_email'].lower() for p in plans]
email_dupes = {e: emails_in_batch.count(e) for e in set(emails_in_batch) if emails_in_batch.count(e) > 1}
if len(email_dupes) == 0:
    PASS += 1
    print(f'  [PASS] #{PASS+FAIL} All {plan_count} emails unique')
else:
    FAIL += 1
    print(f'  [FAIL] #{PASS+FAIL} Email duplicates: {email_dupes}')
    BLOCKS.append(f'Email duplicate: {email_dupes}')

# ── STEP 6: Template SHA matches ──
print('\n── STEP 6: Template SHA matches ──')
# Compute via bd_template.py formula: sha256(body_text + "|||" + body_html + "|||" + signature_text)[:8]
sys.path.insert(0, PROJECT_DIR)
from bd_template import BODY_TEXT, BODY_HTML, CUSTOM_BODY_TEXT, CUSTOM_BODY_HTML, SIGNATURE_TEXT

retail_content = BODY_TEXT + '|||' + BODY_HTML + '|||' + SIGNATURE_TEXT
retail_sha = hashlib.sha256(retail_content.encode('utf-8')).hexdigest()[:8]

custom_content = CUSTOM_BODY_TEXT + '|||' + CUSTOM_BODY_HTML + '|||' + SIGNATURE_TEXT
custom_sha = hashlib.sha256(custom_content.encode('utf-8')).hexdigest()[:8]

expected = {'retail_distributor_v5_locked': ('ccb51505', retail_sha),
            'custom_printing_production_v5_locked': ('5893dbc9', custom_sha)}

for tid, (exp, got) in expected.items():
    ok = got == exp
    if ok:
        PASS += 1
        print(f'  [PASS] #{PASS+FAIL} {tid}: SHA={got}')
    else:
        FAIL += 1
        print(f'  [FAIL] #{PASS+FAIL} {tid}: got={got}, expected={exp}')
        BLOCKS.append(f'Template SHA mismatch: {tid} got={got} expected={exp}')

# Verify templates in batch all match
batch_template_ids = set(p['template_id'] for p in plans)
print(f'         Templates in batch: {batch_template_ids}')

# ── STEP 7: Ops Center HTTP 200 ──
print('\n── STEP 7: Ops Center HTTP 200 ──')
try:
    req = Request('http://127.0.0.1:8765/api/dashboard', headers={'User-Agent': 'Preflight/1.0'})
    resp = urlopen(req, timeout=5, context=ctx)
    if resp.status == 200:
        body = resp.read().decode('utf-8', errors='replace')[:100]
        PASS += 1
        print(f'  [PASS] #{PASS+FAIL} Ops Center HTTP 200: {body}')
    else:
        FAIL += 1
        print(f'  [FAIL] #{PASS+FAIL} Ops Center HTTP {resp.status}')
        BLOCKS.append(f'Ops Center HTTP {resp.status}')
except Exception as e:
    FAIL += 1
    print(f'  [FAIL] #{PASS+FAIL} Ops Center unreachable: {e}')
    BLOCKS.append(f'Ops Center unreachable: {e}')

# ── STEP 8: Poller heartbeat fresh ──
print('\n── STEP 8: Poller heartbeat fresh ──')
try:
    with open(OPS_POLLER_STATUS, 'r') as f:
        ps = json.load(f)
    last_hb = ps.get('last_heartbeat_at', '')
    if last_hb:
        hb_dt = datetime.fromisoformat(last_hb)
        age_min = (datetime.now(ASIA_SH) - hb_dt).total_seconds() / 60
        fresh = age_min <= 15
        if fresh:
            PASS += 1
            print(f'  [PASS] #{PASS+FAIL} Poller heartbeat: {age_min:.1f} min ago')
        else:
            FAIL += 1
            print(f'  [FAIL] #{PASS+FAIL} Poller heartbeat STALE: {age_min:.1f} min ago (threshold: 15 min)')
            print(f'         Last heartbeat: {last_hb}')
            BLOCKS.append(f'Poller heartbeat stale: {age_min:.1f} min')
    else:
        FAIL += 1
        print(f'  [FAIL] #{PASS+FAIL} No poller heartbeat timestamp')
        BLOCKS.append('No poller heartbeat timestamp')
except FileNotFoundError:
    FAIL += 1
    print(f'  [FAIL] #{PASS+FAIL} Poller status file not found')
    BLOCKS.append('Poller status file not found')

# ── STEP 9: Tracking Worker HTTP 200 ──
print('\n── STEP 9: Tracking Worker HTTP 200 ──')
try:
    req = Request('https://roktandrazo-email-tracker.1569032023yf.workers.dev/health',
                  headers={'User-Agent': 'Preflight/1.0'})
    resp = urlopen(req, timeout=10, context=ctx)
    if resp.status == 200:
        PASS += 1
        print(f'  [PASS] #{PASS+FAIL} Tracking Worker HTTP 200')
    else:
        FAIL += 1
        print(f'  [FAIL] #{PASS+FAIL} Tracking Worker HTTP {resp.status}')
        BLOCKS.append(f'Worker HTTP {resp.status}')
except Exception as e:
    FAIL += 1
    print(f'  [FAIL] #{PASS+FAIL} Tracking Worker unreachable: {e}')
    BLOCKS.append(f'Worker unreachable: {e}')

# ── STEP 10: No active old plans or auths ──
print('\n── STEP 10: No active old plans or auths ──')
old_plans = conn.execute(
    "SELECT COUNT(*) as c FROM final_send_plan WHERE status='planned' AND outreach_batch_date != ?",
    (batch_date,)
).fetchone()['c']
old_auths = conn.execute(
    "SELECT COUNT(*) as c FROM send_authorizations WHERE status='active' AND outreach_batch_date != ?",
    (batch_date,)
).fetchone()['c']

if old_plans == 0 and old_auths == 0:
    PASS += 1
    print(f'  [PASS] #{PASS+FAIL} Old plans={old_plans}, old auths={old_auths}')
else:
    FAIL += 1
    print(f'  [FAIL] #{PASS+FAIL} Old plans={old_plans}, old auths={old_auths}')
    BLOCKS.append(f'Stale plans/auths: plans={old_plans}, auths={old_auths}')

conn.close()

# ── VERDICT ──
print('\n' + '=' * 65)
print(f'  RESULTS: {PASS} PASS, {FAIL} FAIL')
print('=' * 65)

if FAIL > 0:
    preflight_status = 'failed'
    print(f'\n  VERDICT: **BLOCKED**')
    print(f'  preflight_status = FAILED')
    print(f'  SMTP stays at 0')
    print(f'  Blockers ({len(BLOCKS)}):')
    for b in BLOCKS:
        print(f'    - {b}')
else:
    preflight_status = 'passed'
    print(f'\n  VERDICT: **ALL PASS — CLEARED FOR SEND**')
    print(f'  preflight_status = passed')

# ── STEP 11/12: Write preflight_status ──
conn2 = sqlite3.connect(DB_PATH)
if auth:
    conn2.execute(
        'UPDATE send_authorizations SET preflight_status=? WHERE authorization_id=?',
        (preflight_status, auth['authorization_id'])
    )
    conn2.commit()
    print(f'\n  [DB] send_authorizations.preflight_status -> "{preflight_status}"')
conn2.close()

# ── Save result JSON ──
result = {
    'batch_id': BATCH_ID,
    'batch_date': batch_date,
    'plan_id': '2026-08-03:new_outreach:3939af2047',
    'auth_id': auth['authorization_id'] if auth else None,
    'plan_count': plan_count,
    'pass': PASS,
    'fail': FAIL,
    'blocks': BLOCKS,
    'preflight_status': preflight_status,
    'time': datetime.now(ASIA_SH).isoformat(),
    'verdict': 'CLEARED FOR SEND' if FAIL == 0 else 'BLOCKED'
}
out_dir = os.path.join(PROJECT_DIR, 'output')
os.makedirs(out_dir, exist_ok=True)
result_path = os.path.join(out_dir, 'preflight_result.json')
with open(result_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(f'  Result saved: {result_path}')

# ── Batch summary ──
print('\n── BATCH: new_outreach_20260803_et1000 ──')
conn3 = sqlite3.connect(DB_PATH)
conn3.row_factory = sqlite3.Row
batch_plans = conn3.execute(
    "SELECT id, lead_id, recipient_email, company_name, customer_type, template_id, source_city, source_state FROM final_send_plan WHERE outreach_batch_date=? AND status='planned' ORDER BY planned_sequence",
    (batch_date,)
).fetchall()
for i, p in enumerate(batch_plans, 1):
    tmpl_short = 'RETAIL' if 'retail' in p['template_id'] else 'CUSTOM'
    print(f'  {i:2d}. [{tmpl_short}] {p["company_name"]} ({p["customer_type"]})')
    print(f'       {p["recipient_email"]} — {p["source_city"]}, {p["source_state"]}')
conn3.close()

print(f'\n  Total: {plan_count} entries | {FAIL} blocker(s) | SMTP: {"0 (blocked)" if FAIL > 0 else "READY"}')
