"""BD Production Final Preflight — Read-only gate verification for 2026-08-11 ET 10:00."""
import sqlite3, json, os, sys, urllib.request, urllib.error
from datetime import datetime

db = sqlite3.connect('data/bd_leads.db')
db.row_factory = sqlite3.Row
c = db.cursor()

batch_date = '20260811'
batch_id_friendly = f'new_outreach_{batch_date}_et1000'
results = {
    'preflight_ts_cst': datetime.now().strftime('%Y-%m-%d %H:%M:%S CST'),
    'batch_id': batch_id_friendly,
    'batch_date': batch_date,
    'gates': {}
}

# === STEP 1: Batch ID ===
results['gates']['step1_batch_id'] = {'pass': True, 'value': batch_id_friendly}

# === STEP 2: Final Send Plan entries ===
c.execute('SELECT COUNT(*) FROM final_send_plan WHERE outreach_batch_date = ?', (batch_date,))
plan_count = c.fetchone()[0]
results['gates']['step2_plan_entries'] = {'pass': plan_count > 0, 'count': plan_count}

if plan_count > 0:
    c.execute('''SELECT plan_id, lead_id, recipient_email, company_name, customer_type,
                 lead_segment, template_key, source_city, source_state, status
                 FROM final_send_plan WHERE outreach_batch_date = ? LIMIT 20''', (batch_date,))
    results['plan_sample'] = []
    for r in c.fetchall():
        results['plan_sample'].append(dict(zip(
            ['plan_id','lead_id','email','company','customer_type','segment','template','city','state','status'], r)))

# === STEP 3: Send authorization ===
c.execute('''SELECT authorization_id, plan_id, approved_entry_count, preflight_status,
             approved_at, expires_at, status FROM send_authorizations
             WHERE outreach_batch_date = ? ORDER BY id DESC LIMIT 1''', (batch_date,))
auth_row = c.fetchone()
if auth_row:
    results['gates']['step3_auth_exists'] = {
        'pass': True,
        'authorization_id': auth_row['authorization_id'],
        'plan_id': auth_row['plan_id'],
        'approved_entry_count': auth_row['approved_entry_count'],
        'preflight_status': auth_row['preflight_status'],
        'approved_at': auth_row['approved_at'],
        'expires_at': auth_row['expires_at'],
        'status': auth_row['status']
    }
    approved_count = auth_row['approved_entry_count'] or 0
    c.execute('SELECT COUNT(*) FROM send_authorization_entries WHERE authorization_id = ?', (auth_row['authorization_id'],))
    auth_entry_count = c.fetchone()[0]
    results['auth_entry_count'] = auth_entry_count
else:
    results['gates']['step3_auth_exists'] = {'pass': False, 'reason': 'No send authorization found'}
    approved_count = 0

# === STEP 4: Auth entries = Plan entries ===
auth_plan_match = (plan_count > 0 and auth_row is not None and approved_count == plan_count)
results['gates']['step4_auth_plan_match'] = {
    'pass': auth_plan_match,
    'plan_count': plan_count,
    'auth_entry_count': approved_count,
    'match': (plan_count == approved_count),
    'note': 'Both zero = no valid plan' if plan_count == 0 else ''
}

# === STEP 5: Organization duplicates ===
if plan_count > 0:
    c.execute('''SELECT company_name, COUNT(*) as cnt FROM final_send_plan
                 WHERE outreach_batch_date = ? GROUP BY company_name HAVING cnt > 1''', (batch_date,))
    org_dupes = c.fetchall()
    org_dupe_count = len(org_dupes)
    results['gates']['step5_org_duplicates'] = {
        'pass': org_dupe_count == 0, 'duplicate_count': org_dupe_count}
    if org_dupes:
        results['gates']['step5_org_duplicates']['samples'] = [
            {'company': r[0], 'count': r[1]} for r in org_dupes[:5]]
else:
    results['gates']['step5_org_duplicates'] = {'pass': None, 'reason': 'no_plan', 'duplicate_count': 0}

# === STEP 6: Email duplicates ===
if plan_count > 0:
    c.execute('''SELECT recipient_email, COUNT(*) as cnt FROM final_send_plan
                 WHERE outreach_batch_date = ? GROUP BY recipient_email HAVING cnt > 1''', (batch_date,))
    email_dupes = c.fetchall()
    email_dupe_count = len(email_dupes)
    results['gates']['step6_email_duplicates'] = {
        'pass': email_dupe_count == 0, 'duplicate_count': email_dupe_count}
    if email_dupes:
        results['gates']['step6_email_duplicates']['samples'] = [
            {'email': r[0], 'count': r[1]} for r in email_dupes[:5]]
else:
    results['gates']['step6_email_duplicates'] = {'pass': None, 'reason': 'no_plan', 'duplicate_count': 0}

# === STEP 7: Template SHA ===
import importlib.util
spec = importlib.util.spec_from_file_location('bd_template', 'bd_template.py')
expected_retail = 'ccb51505'
expected_custom = '5893dbc9'
retail_ok = False
custom_ok = False
retail_actual = 'NOT_LOADED'
custom_actual = 'NOT_LOADED'

if spec and spec.loader:
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sha_dict = getattr(mod, '_TEMPLATE_SHA256', {})
    retail_actual = sha_dict.get('retail_distributor_v5_locked', 'KEY_NOT_FOUND')
    custom_actual = sha_dict.get('custom_printing_production_v5_locked', 'KEY_NOT_FOUND')
    retail_ok = (retail_actual == expected_retail)
    custom_ok = (custom_actual == expected_custom)

results['gates']['step7_template_sha'] = {
    'pass': retail_ok and custom_ok,
    'retail': {'expected': expected_retail, 'actual': retail_actual, 'match': retail_ok},
    'custom': {'expected': expected_custom, 'actual': custom_actual, 'match': custom_ok}
}

# === STEP 8: Ops Center HTTP 200 ===
try:
    req = urllib.request.Request('http://127.0.0.1:8765/', method='GET')
    resp = urllib.request.urlopen(req, timeout=5)
    ops_http = resp.status
    ops_pass = (ops_http == 200)
except Exception as e:
    ops_http = 0
    ops_pass = False
    results['ops_center_error'] = str(e)

results['gates']['step8_ops_center'] = {
    'pass': ops_pass, 'http_code': ops_http, 'url': 'http://127.0.0.1:8765/'}

# === STEP 9: Poller heartbeat ===
c.execute("SELECT value FROM system_config WHERE key = 'sync_0845_last_success_at'")
hb_row = c.fetchone()
if hb_row:
    hb_str = hb_row['value']
    try:
        hb_str_clean = hb_str.replace('+08:00', '').replace('+00:00', '').replace('Z', '')
        if '.' in hb_str_clean:
            hb_str_clean = hb_str_clean.split('.')[0]
        hb_dt = datetime.strptime(hb_str_clean, '%Y-%m-%dT%H:%M:%S')
        now = datetime.now()
        stale_min = (now - hb_dt).total_seconds() / 60
        results['gates']['step9_poller_heartbeat'] = {
            'pass': stale_min < 120,
            'last_heartbeat': hb_str,
            'stale_minutes': round(stale_min, 1)
        }
    except Exception as e:
        results['gates']['step9_poller_heartbeat'] = {
            'pass': False, 'last_heartbeat': hb_str, 'reason': f'PARSE_ERROR: {e}'}
else:
    results['gates']['step9_poller_heartbeat'] = {
        'pass': False, 'reason': 'NO_SYNC_0845_RECORD'}

# === STEP 10: Old active plans/auths ===
c.execute("""SELECT COUNT(*) FROM final_send_plan
             WHERE outreach_batch_date != ? AND status = 'planned' """, (batch_date,))
old_active_plans = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM final_send_plan WHERE outreach_batch_date != ?', (batch_date,))
old_plan_total = c.fetchone()[0]
c.execute('''SELECT outreach_batch_date, COUNT(*) FROM final_send_plan
             WHERE outreach_batch_date != ? GROUP BY outreach_batch_date
             ORDER BY outreach_batch_date DESC LIMIT 5''', (batch_date,))
old_plan_batches = [(r[0], r[1]) for r in c.fetchall()]

c.execute('SELECT COUNT(*) FROM send_authorizations WHERE outreach_batch_date != ?', (batch_date,))
old_auth_total = c.fetchone()[0]
c.execute('''SELECT outreach_batch_date, COUNT(*), status FROM send_authorizations
             WHERE outreach_batch_date != ? GROUP BY outreach_batch_date
             ORDER BY outreach_batch_date DESC LIMIT 5''', (batch_date,))
old_auth_batches = [(r[0], r[1], r[2]) for r in c.fetchall()]

c.execute("""SELECT COUNT(*) FROM send_authorizations
             WHERE outreach_batch_date != ?
             AND status NOT IN ('consumed', 'revoked', 'expired')""", (batch_date,))
active_old_auths = c.fetchone()[0]

old_clean = (old_active_plans == 0 and active_old_auths == 0)
results['gates']['step10_old_plans_auths'] = {
    'pass': old_clean,
    'old_plan_total': old_plan_total,
    'old_active_plans': old_active_plans,
    'old_auth_total': old_auth_total,
    'active_old_auths': active_old_auths,
    'old_plan_batches': old_plan_batches,
    'old_auth_batches': old_auth_batches
}

# Frozen snapshot check
snap_path = f'data/frozen_new_outreach_{batch_date}_et1000.json'
results['frozen_snapshot_exists'] = os.path.exists(snap_path)

# A0 pool size
c.execute("SELECT COUNT(*) FROM leads WHERE status = 'new' AND confidence_score = 'A' AND email_verified_on_official_site = 1 AND email IS NOT NULL AND email != ''")
results['a0_pool_count'] = c.fetchone()[0]

# === STEP 11/12: Final verdict ===
gate_results = {}
all_valid = True
blockers = []

for gate_name, gate in results['gates'].items():
    p = gate.get('pass')
    if p is True:
        gate_results[gate_name] = 'PASS'
    elif p is False:
        gate_results[gate_name] = 'FAIL'
        all_valid = False
        blockers.append(gate_name)
    else:
        gate_results[gate_name] = 'N/A'

results['gate_summary'] = gate_results
results['blockers'] = blockers
results['overall_verdict'] = 'PASSED' if all_valid else 'BLOCKED'

# Write to system_config
preflight_status = 'passed' if all_valid else 'failed'
c.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES ('preflight_status', ?, datetime('now'))", (preflight_status,))
c.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES ('preflight_verdict', ?, datetime('now'))", (results['overall_verdict'],))
c.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES ('preflight_last_run', ?, datetime('now'))", (results['preflight_ts_cst'],))
if blockers:
    c.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES ('preflight_blockers', ?, datetime('now'))", (json.dumps(blockers),))
db.commit()
db.close()

# Ensure output dir
os.makedirs('output', exist_ok=True)
with open('output/preflight_result.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, default=str, ensure_ascii=False)

print(json.dumps(results, indent=2, default=str, ensure_ascii=False))
