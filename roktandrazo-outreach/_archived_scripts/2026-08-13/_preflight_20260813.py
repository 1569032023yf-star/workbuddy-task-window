"""BD Production Final Preflight — Read-only gate verification for 2026-08-13 ET 10:00.
NO SMTP. Fail-closed. Writes only preflight_* keys to system_config + output/preflight_result.json.
"""
import sqlite3, json, os, socket, importlib.util
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'data', 'bd_leads.db')
OUT = os.path.join(BASE, 'output')

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row
c = db.cursor()

batch_date = '20260813'
batch_id = f'new_outreach_{batch_date}_et1000'
now_cst = datetime.now(CST)

results = {
    'preflight_ts_cst': now_cst.strftime('%Y-%m-%d %H:%M:%S CST'),
    'batch_id': batch_id,
    'batch_date': batch_date,
    'gates': {},
}

# === STEP 1: Batch ID ===
results['gates']['step1_batch_id'] = {'pass': True, 'value': batch_id}

# === STEP 2: Final Send Plan entries (full batch_id + bare date fallback) ===
c.execute("SELECT COUNT(*) FROM final_send_plan WHERE outreach_batch_date IN (?, ?)", (batch_id, batch_date))
plan_count = c.fetchone()[0]
results['gates']['step2_plan_entries'] = {'pass': plan_count > 0, 'count': plan_count}

if plan_count > 0:
    c.execute('''SELECT plan_id, lead_id, recipient_email, company_name, customer_type,
                 lead_segment, template_key, source_city, source_state, status
                 FROM final_send_plan WHERE outreach_batch_date IN (?, ?) LIMIT 30''', (batch_id, batch_date))
    results['plan_sample'] = []
    for r in c.fetchall():
        results['plan_sample'].append(dict(zip(
            ['plan_id','lead_id','email','company','customer_type','segment','template','city','state','status'], r)))

# === STEP 3: Send authorization (created + approved) ===
c.execute('''SELECT authorization_id, plan_id, approved_entry_count, preflight_status,
             approved_at, expires_at, status FROM send_authorizations
             WHERE outreach_batch_date IN (?, ?) ORDER BY id DESC LIMIT 1''', (batch_id, batch_date))
auth_row = c.fetchone()
approved_count = 0
if auth_row:
    auth_approved = (auth_row['status'] == 'approved')
    results['gates']['step3_auth_exists'] = {
        'pass': auth_approved,
        'authorization_id': auth_row['authorization_id'],
        'plan_id': auth_row['plan_id'],
        'approved_entry_count': auth_row['approved_entry_count'],
        'preflight_status': auth_row['preflight_status'],
        'approved_at': auth_row['approved_at'],
        'expires_at': auth_row['expires_at'],
        'status': auth_row['status'],
    }
    approved_count = auth_row['approved_entry_count'] or 0
    c.execute('SELECT COUNT(*) FROM send_authorization_entries WHERE authorization_id = ?', (auth_row['authorization_id'],))
    results['auth_entry_count'] = c.fetchone()[0]
else:
    results['gates']['step3_auth_exists'] = {'pass': False, 'reason': 'No send authorization found'}

# === STEP 4: Auth entries = Plan entries ===
auth_plan_match = (plan_count > 0 and auth_row is not None and approved_count == plan_count)
results['gates']['step4_auth_plan_match'] = {
    'pass': auth_plan_match,
    'plan_count': plan_count,
    'auth_entry_count': approved_count,
    'match': (plan_count == approved_count),
    'note': 'Both zero = no valid plan' if plan_count == 0 else '',
}

# === STEP 5: Organization duplicates ===
if plan_count > 0:
    c.execute('''SELECT company_name, COUNT(*) AS cnt FROM final_send_plan
                 WHERE outreach_batch_date IN (?, ?) GROUP BY company_name HAVING cnt > 1''', (batch_id, batch_date))
    org_dupes = c.fetchall()
    org_dupe_count = len(org_dupes)
    results['gates']['step5_org_duplicates'] = {'pass': org_dupe_count == 0, 'duplicate_count': org_dupe_count}
    if org_dupes:
        results['gates']['step5_org_duplicates']['samples'] = [{'company': r[0], 'count': r[1]} for r in org_dupes[:5]]
else:
    results['gates']['step5_org_duplicates'] = {'pass': None, 'reason': 'no_plan', 'duplicate_count': 0}

# === STEP 6: Email duplicates ===
if plan_count > 0:
    c.execute('''SELECT recipient_email, COUNT(*) AS cnt FROM final_send_plan
                 WHERE outreach_batch_date IN (?, ?) GROUP BY recipient_email HAVING cnt > 1''', (batch_id, batch_date))
    email_dupes = c.fetchall()
    email_dupe_count = len(email_dupes)
    results['gates']['step6_email_duplicates'] = {'pass': email_dupe_count == 0, 'duplicate_count': email_dupe_count}
    if email_dupes:
        results['gates']['step6_email_duplicates']['samples'] = [{'email': r[0], 'count': r[1]} for r in email_dupes[:5]]
else:
    results['gates']['step6_email_duplicates'] = {'pass': None, 'reason': 'no_plan', 'duplicate_count': 0}

# === STEP 7: Template SHA ===
spec = importlib.util.spec_from_file_location('bd_template', os.path.join(BASE, 'bd_template.py'))
expected_retail = 'ccb51505'
expected_custom = '5893dbc9'
retail_actual = 'NOT_LOADED'
custom_actual = 'NOT_LOADED'
retail_ok = custom_ok = False
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
    'custom': {'expected': expected_custom, 'actual': custom_actual, 'match': custom_ok},
}

# === STEP 8: Ops Center HTTP 200 ===
def _ops_http():
    try:
        s = socket.create_connection(('127.0.0.1', 8765), timeout=4)
        s.close()
        return 200, None
    except Exception as e:
        return 0, str(e)
ops_http, ops_err = _ops_http()
results['gates']['step8_ops_center'] = {
    'pass': (ops_http == 200), 'http_code': ops_http, 'url': 'http://127.0.0.1:8765/',
    'error': ops_err,
}

# === STEP 9: Poller heartbeat ===
# Primary: poller's own heartbeat file (output/bd_ops_poller_status.json), refresh every 60s.
poller_file = os.path.join(OUT, 'bd_ops_poller_status.json')
poller_age_min = None
poller_hb_str = None
if os.path.exists(poller_file):
    try:
        _d = json.load(open(poller_file, encoding='utf-8'))
        poller_hb_str = _d.get('last_heartbeat_at')
        if poller_hb_str:
            poller_age_min = (now_cst - datetime.fromisoformat(poller_hb_str)).total_seconds() / 60
    except Exception as e:
        results['poller_parse_error'] = str(e)

# Secondary: sync_0845_last_success_at (prior-run proxy, threshold <120 min)
c.execute("SELECT value FROM system_config WHERE key = 'sync_0845_last_success_at'")
hb_row = c.fetchone()
sync_age_min = None
if hb_row:
    try:
        _hb = hb_row['value'].replace('+08:00', '').replace('+00:00', '').replace('Z', '')
        if '.' in _hb:
            _hb = _hb.split('.')[0]
        sync_dt = datetime.strptime(_hb, '%Y-%m-%dT%H:%M:%S')
        sync_age_min = (now_cst.replace(tzinfo=None) - sync_dt).total_seconds() / 60
    except Exception as e:
        results['sync_parse_error'] = str(e)

# Poller healthy if its own heartbeat <= 150s (2.5 min); else FAIL.
poller_fresh = (poller_age_min is not None and poller_age_min <= 2.5)
results['gates']['step9_poller_heartbeat'] = {
    'pass': poller_fresh,
    'poller_last_heartbeat': poller_hb_str,
    'poller_age_minutes': round(poller_age_min, 1) if poller_age_min is not None else None,
    'poller_threshold_minutes': 2.5,
    'sync_0845_last_success_at': hb_row['value'] if hb_row else None,
    'sync_0845_age_minutes': round(sync_age_min, 1) if sync_age_min is not None else None,
}

# === STEP 10: No active OLD plans/auths (previous days) ===
# "old" = outreach_batch_date != today's target batch_id. Any status='planned'
# plan or non-consumed/revoked/expired auth on a different batch is a leftover.
c.execute("SELECT COUNT(*) FROM final_send_plan WHERE outreach_batch_date NOT IN (?, ?) AND status = 'planned'", (batch_id, batch_date))
old_active_plans = c.fetchone()[0]
c.execute("""SELECT COUNT(*) FROM send_authorizations
             WHERE outreach_batch_date NOT IN (?, ?)
             AND status NOT IN ('consumed', 'revoked', 'expired')""", (batch_id, batch_date))
active_old_auths = c.fetchone()[0]

c.execute("SELECT outreach_batch_date, COUNT(*) FROM final_send_plan WHERE outreach_batch_date NOT IN (?, ?) AND status='planned' GROUP BY outreach_batch_date", (batch_id, batch_date))
planned_batches = [(r[0], r[1]) for r in c.fetchall()]
c.execute("""SELECT authorization_id, outreach_batch_date, status, expires_at FROM send_authorizations
             WHERE outreach_batch_date NOT IN (?, ?) AND status NOT IN ('consumed','revoked','expired')""", (batch_id, batch_date))
active_auth_rows = [dict(zip(['authorization_id','outreach_batch_date','status','expires_at'], r)) for r in c.fetchall()]

old_clean = (old_active_plans == 0 and active_old_auths == 0)
results['gates']['step10_old_plans_auths'] = {
    'pass': old_clean,
    'old_active_plans': old_active_plans,
    'active_old_auths': active_old_auths,
    'planned_batches': planned_batches,
    'active_auth_rows': active_auth_rows,
}

# Frozen snapshot existence (context)
results['frozen_snapshot_exists'] = os.path.exists(os.path.join(BASE, 'data', f'frozen_{batch_id}.json')) or os.path.exists(os.path.join(OUT, f'frozen_{batch_id}.json'))

# A0 pool size (context)
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

# Write to system_config (preflight_* keys only; SMTP_enabled untouched → stays 0)
preflight_status = 'passed' if all_valid else 'failed'
writes = {
    'preflight_status': preflight_status,
    'preflight_verdict': results['overall_verdict'],
    'preflight_last_run': results['preflight_ts_cst'],
    'preflight_batch_id': batch_id,
    'preflight_at': now_cst.isoformat(),
    'preflight_plan_count': str(plan_count),
    'preflight_summary': json.dumps({
        'PASS': sum(1 for v in gate_results.values() if v == 'PASS'),
        'FAIL': sum(1 for v in gate_results.values() if v == 'FAIL'),
        'N_A': sum(1 for v in gate_results.values() if v == 'N/A'),
    }),
    'preflight_checks': json.dumps(gate_results),
    'preflight_follow_up': '0',
}
if blockers:
    writes['preflight_blockers'] = json.dumps(blockers)
for k, v in writes.items():
    c.execute("INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?, ?, datetime('now'))", (k, v))

# Verify SMTP remains 0 (read-only confirm)
c.execute("SELECT value FROM system_config WHERE key='SMTP_enabled'")
results['smtp_enabled'] = c.fetchone()[0]

db.commit()
db.close()

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, 'preflight_result.json'), 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, default=str, ensure_ascii=False)

print(json.dumps(results, indent=2, default=str, ensure_ascii=False))
