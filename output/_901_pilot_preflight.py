"""901 Games Pilot Preflight V2 - Strictly read-only"""
import sqlite3, re, os, subprocess, json, time, urllib.request
from datetime import datetime, timezone, timedelta

ASIA_SH = timezone(timedelta(hours=8))
BASE = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach'
DB = os.path.join(BASE, 'data', 'bd_leads.db')
GUARD = os.path.join(BASE, 'output', 'bd_delivery_guard_status.json')
POLLER = os.path.join(BASE, 'output', 'bd_ops_poller_status.json')
results = {}

# === DELIVERY GUARD ===
try:
    with open(GUARD) as f:
        gs = json.load(f)
    hb = gs.get('last_heartbeat_at', '')
    if hb:
        hb_age = (datetime.now(ASIA_SH) - datetime.fromisoformat(hb)).total_seconds()
        results['guard_hb_lt_60s'] = (hb_age < 60, f'hb_age={int(hb_age)}s')
    else:
        results['guard_hb_lt_60s'] = (False, 'no_heartbeat')
    results['guard_mode_critical'] = (gs.get('current_mode') == 'critical', f"mode={gs.get('current_mode')}")
    results['system_required'] = (gs.get('system_required') is True, f"system_required={gs.get('system_required')}")
    results['display_required'] = (gs.get('display_required') is True, f"display_required={gs.get('display_required')}")
    results['ac_power'] = (gs.get('ac_power') is True, f"ac_power={gs.get('ac_power')}")
except Exception as e:
    results['guard_read'] = (False, str(e)[:80])

# === OPS CENTER ===
try:
    r = urllib.request.urlopen('http://127.0.0.1:8765/api/dashboard', timeout=5)
    results['ops_center_200'] = (r.status == 200, f'HTTP {r.status}')
except Exception as e:
    results['ops_center_200'] = (False, str(e)[:80])

# === POLLER ===
try:
    with open(POLLER) as f:
        ps = json.load(f)
    ph = ps.get('last_heartbeat_at', '')
    if ph:
        pa = (datetime.now(ASIA_SH) - datetime.fromisoformat(ph)).total_seconds()
        results['poller_fresh'] = (pa < 120, f'poller_age={int(pa)}s')
    else:
        results['poller_fresh'] = (False, 'no_heartbeat')
    jobs = ps.get('jobs', {})
    all_ok = all(j.get('consecutive_failures', 0) == 0 for j in jobs.values())
    results['poller_jobs_ok'] = (all_ok, f'jobs={len(jobs)}')
except Exception as e:
    results['poller_fresh'] = (False, str(e)[:80])

# === WORKER ===
try:
    curl = subprocess.run(
        ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
         'https://roktandrazo-email-tracker.1569032023yf.workers.dev/health'],
        capture_output=True, text=True, timeout=15)
    results['worker_health'] = (curl.stdout.strip() in ('200', ''), f"HTTP {curl.stdout.strip()[:10]}")
except Exception as e:
    results['worker_health'] = (False, str(e)[:80])

# === DATABASE ===
db = sqlite3.connect(DB)

c = db.execute("SELECT COUNT(*) FROM final_send_plan WHERE status='planned'").fetchone()[0]
results['planned_total_1'] = (c == 1, f'planned={c}')

c = db.execute("SELECT lead_id FROM final_send_plan WHERE status='planned'").fetchone()
results['lead_id_530'] = (c is not None and c[0] == 530, f"lead_id={c[0] if c else 'N/A'}")

c = db.execute("SELECT message_type FROM final_send_plan WHERE status='planned'").fetchone()
results['msg_type_new_outreach'] = (c is not None and c[0] == 'new_outreach', f"type={c[0] if c else 'N/A'}")

c = db.execute("SELECT COUNT(*) FROM final_send_plan WHERE status='planned' AND message_type='follow_up'").fetchone()[0]
results['follow_up_zero'] = (c == 0, f'follow_up_planned={c}')

c = db.execute("SELECT status FROM email_tracking_messages WHERE lead_id=530 AND is_test=0 ORDER BY id DESC LIMIT 1").fetchone()
results['tracking_prepared'] = (c is not None and c[0] == 'prepared', f"tracking={c[0] if c else 'N/A'}")

html = db.execute("SELECT body_html FROM final_send_plan WHERE status='planned'").fetchone()
imgs = re.findall(r'<img[^>]*src="([^"]*)"[^>]*>', html[0] if html else '')
worker_px = [s for s in imgs if 'workers.dev' in s]
results['html_one_worker_pixel'] = (len(imgs) == 1 and len(worker_px) == 1, f'total_imgs={len(imgs)} worker={len(worker_px)}')

c = db.execute("SELECT COUNT(*) FROM send_log").fetchone()[0]
results['send_log_329'] = (c == 329, f'send_log={c}')

c = db.execute("SELECT value FROM system_config WHERE key='risk_gate_status'").fetchone()
results['risk_gate_clear'] = (c is not None and c[0] == 'clear', f"risk_gate={c[0] if c else 'N/A'}")

c = db.execute("SELECT value FROM system_config WHERE key='manual_pause'").fetchone()
results['manual_pause_false'] = (c is not None and c[0] == 'false', f"pause={c[0] if c else 'N/A'}")

c = db.execute("SELECT value FROM system_config WHERE key='standing_authorization'").fetchone()
results['standing_auth_true'] = (c is not None and c[0] == 'true', f"auth={c[0] if c else 'N/A'}")

c = db.execute("SELECT value FROM system_config WHERE key='inventory_status'").fetchone()
results['inventory_not_critical'] = (c is None or c[0] != 'critical', f"inv={c[0] if c else 'N/A'}")

c = db.execute("SELECT value FROM system_config WHERE key='send_pause'").fetchone()
results['send_pause_false'] = (c is not None and c[0] == 'false', f"send_pause={c[0] if c else 'N/A'}")

# no outreach processes
try:
    proc = subprocess.run(['tasklist'], capture_output=True, timeout=10)
    raw = proc.stdout
    if raw is not None:
        for enc in ['utf-8', 'gbk', 'cp936', 'latin-1']:
            try:
                text = raw.decode(enc, errors='strict')
                break
            except Exception:
                pass
        else:
            text = raw.decode('latin-1', errors='replace')
        outreach_procs = [l for l in text.split('\n') if 'orchestrator' in l.lower()]
        results['no_outreach_proc'] = (len(outreach_procs) == 0, f'orchestrator_procs={len(outreach_procs)}')
    else:
        results['no_outreach_proc'] = (False, 'stdout_None')
except Exception as e:
    results['no_outreach_proc'] = (False, str(e)[:80])

db.close()

# === OUTPUT ===
print('=' * 60)
print('901 GAMES PILOT 22:55 PREFLIGHT V2')
print('=' * 60)
all_pass = True
for key, (passed, detail) in results.items():
    s = 'PASS' if passed else 'FAIL'
    if not passed:
        all_pass = False
    print(f'[{s}] {key}: {detail}')
print('=' * 60)
if all_pass:
    print('ALL PASS - READY FOR 901 GAMES PILOT SEND')
else:
    print('HAS FAILURES - PILOT SEND BLOCKED')
    print('DO NOT CALL SMTP. STOP AND INVESTIGATE.')
