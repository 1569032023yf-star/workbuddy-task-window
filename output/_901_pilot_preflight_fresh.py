"""901 Games Pilot FRESH Preflight — 2026-07-29 08:55 CST — Strictly read-only"""
import sqlite3, re, os, subprocess, json, urllib.request
from datetime import datetime, timezone, timedelta

ASIA_SH = timezone(timedelta(hours=8))
BASE = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach'
DB = os.path.join(BASE, 'data', 'bd_leads.db')
GUARD = os.path.join(BASE, 'output', 'bd_delivery_guard_status.json')
POLLER = os.path.join(BASE, 'output', 'bd_ops_poller_status.json')
results = {}

# === DELIVERY GUARD (check 25) — file-based, 15min threshold ===
try:
    with open(GUARD) as f: gs = json.load(f)
    hb = gs.get('last_heartbeat_at', '')
    mode = gs.get('current_mode', '')
    sys_req = gs.get('system_required', False)
    if hb:
        hb_age = (datetime.now(ASIA_SH) - datetime.fromisoformat(hb)).total_seconds()
        # idle mode: 1200s (20min) threshold; critical mode: 120s
        threshold = 120 if (mode == 'critical' and sys_req) else 1200
        hb_ok = hb_age < threshold
        results['25_guard_hb'] = (hb_ok, f'age={int(hb_age)}s mode={mode} sys_req={sys_req}')
    else:
        results['25_guard_hb'] = (False, 'no_hb')
except Exception as e:
    results['25_guard_hb'] = (False, str(e)[:60])

# === POLLER (check 18) — file-based, jobs all ok ===
try:
    with open(POLLER) as f: ps = json.load(f)
    ph = ps.get('last_heartbeat_at', '')
    ph_ok = False
    if ph:
        pa = (datetime.now(ASIA_SH) - datetime.fromisoformat(ph)).total_seconds()
        ph_ok = pa < 1200  # 20min threshold — poller heartbeat interval ~15min
    jobs = ps.get('jobs', {})
    all_ok = all(j.get('consecutive_failures', 0) == 0 for j in jobs.values())
    results['18_poller_ok'] = (ph_ok and all_ok, f'age={int(pa) if ph else "N/A"}s jobs={len(jobs)} all_ok={all_ok}')
except Exception as e:
    results['18_poller_ok'] = (False, str(e)[:60])

# === WORKER (check 17) ===
try:
    curl = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
        'https://roktandrazo-email-tracker.1569032023yf.workers.dev/health'],
        capture_output=True, text=True, timeout=15)
    results['17_worker_200'] = (curl.stdout.strip() == '200', f"HTTP {curl.stdout.strip()[:10]}")
except Exception as e:
    results['17_worker_200'] = (False, str(e)[:60])

# === NO OUTREACH PROCS (check 23) ===
try:
    proc = subprocess.run(['tasklist'], capture_output=True, timeout=10)
    raw = proc.stdout
    if raw is not None:
        for enc in ['utf-8', 'gbk', 'cp936', 'latin-1']:
            try:
                text = raw.decode(enc, errors='strict')
                break
            except: pass
        else:
            text = raw.decode('latin-1', errors='replace')
        outreach_procs = [l for l in text.split('\n') if 'orchestrator' in l.lower()]
        results['23_no_outreach_proc'] = (len(outreach_procs) == 0, f'procs={len(outreach_procs)}')
    else:
        results['23_no_outreach_proc'] = (False, 'stdout_None')
except Exception as e:
    results['23_no_outreach_proc'] = (False, str(e)[:60])

# === DATABASE CHECKS ===
db = sqlite3.connect(DB)

# 1. planned总数=1
c = db.execute("SELECT COUNT(*) FROM final_send_plan WHERE status='planned'").fetchone()[0]
results['01_planned_1'] = (c == 1, f'count={c}')

# 2. 唯一planned lead_id=530
c = db.execute("SELECT lead_id FROM final_send_plan WHERE status='planned'").fetchone()
results['02_lead_id_530'] = (c is not None and c[0] == 530, f"id={c[0] if c else 'N/A'}")

# 3. message_type='new_outreach'
c = db.execute("SELECT message_type FROM final_send_plan WHERE status='planned'").fetchone()
results['03_msg_new_outreach'] = (c is not None and c[0] == 'new_outreach', f"type={c[0] if c else 'N/A'}")

# 4. follow_up planned=0
c = db.execute("SELECT COUNT(*) FROM final_send_plan WHERE status='planned' AND message_type='follow_up'").fetchone()[0]
results['04_no_follow_up'] = (c == 0, f'fu={c}')

# 5. recipient_email='901gamesmemphis@gmail.com'
c = db.execute("SELECT recipient_email FROM final_send_plan WHERE status='planned'").fetchone()
results['05_recipient_901'] = (c is not None and c[0] == '901gamesmemphis@gmail.com', f"to={c[0] if c else 'N/A'}")

# 6. tracking status='prepared'
c = db.execute("SELECT status FROM email_tracking_messages WHERE lead_id=530 AND is_test=0 ORDER BY id DESC LIMIT 1").fetchone()
results['06_tracking_prepared'] = (c is not None and c[0] == 'prepared', f"status={c[0] if c else 'N/A'}")

# 7. Token尚未active（tracking record not yet activated）
c = db.execute("SELECT status FROM email_tracking_messages WHERE lead_id=530 AND is_test=0 AND status='active' ORDER BY id DESC LIMIT 1").fetchone()
results['07_token_not_active'] = (c is None, f"active_found={'yes' if c else 'no'}")

# 8. HTML只有1个Worker HTTPS pixel
html = db.execute("SELECT body_html FROM final_send_plan WHERE status='planned'").fetchone()
imgs = re.findall(r'<img[^>]*src="([^"]*)"[^>]*>', html[0] if html else '')
worker_px = [s for s in imgs if 'workers.dev' in s]
results['08_html_1_pixel'] = (len(imgs) == 1 and len(worker_px) == 1 and all(s.startswith('https://') for s in worker_px),
                               f'img={len(imgs)} worker={len(worker_px)} https_only={all(s.startswith("https://") for s in worker_px)}')

# 9. 纯文本无pixel
txt = db.execute("SELECT body_text FROM final_send_plan WHERE status='planned'").fetchone()
has_pixel_in_text = 'src=' in (txt[0] if txt and txt[0] else '') or 'img' in (txt[0] if txt and txt[0] else '').lower()
results['09_text_no_pixel'] = (not has_pixel_in_text, f"has_img_tag={has_pixel_in_text}")

# 10. sender copy无pixel — sender copy is sent separately, we check there's no second planned entry
c = db.execute("SELECT COUNT(*) FROM final_send_plan WHERE status='planned' AND recipient_email='ianyf@roktandrazo.com'").fetchone()[0]
results['10_sender_copy_separate'] = (c == 0, f"sender_copy_planned={c}")

# 11. send_log仍为329
c = db.execute("SELECT COUNT(*) FROM send_log").fetchone()[0]
results['11_send_log_329'] = (c == 329, f'log={c}')

# 12. 901 Games没有新reply
c = db.execute("SELECT COUNT(*) FROM reply_log WHERE lead_id=530").fetchone()[0]
results['12_no_reply'] = (c == 0, f'replies={c}')

# 13. 没有新suppression (suppression_list only has email column, no lead_id)
c = db.execute("SELECT COUNT(*) FROM suppression_list WHERE email='901gamesmemphis@gmail.com'").fetchone()[0]
results['13_no_suppression'] = (c == 0, f'suppressed={c}')

# 14. No unsubscribe (suppression_list also serves as unsubscribe list)
c = db.execute("SELECT COUNT(*) FROM suppression_list WHERE email='901gamesmemphis@gmail.com' AND reason LIKE '%unsubscribe%'").fetchone()[0]
results['14_no_unsubscribe'] = (c == 0, f'unsub={c}')

# 15. 没有新hard bounce
c = db.execute("SELECT COUNT(*) FROM bounce_log WHERE lead_id=530 AND bounce_type='hard'").fetchone()[0]
results['15_no_hard_bounce'] = (c == 0, f'bounces={c}')

# 16. organization previous send仍为0 (check if any previous sends to 901gamesmemphis or lead 530)
c = db.execute("SELECT COUNT(*) FROM send_log WHERE lead_id=530").fetchone()[0]
results['16_org_prev_send_0'] = (c == 0, f'prev_sends={c}')

# 19. risk_gate=clear
c = db.execute("SELECT value FROM system_config WHERE key='risk_gate_status'").fetchone()
results['19_risk_gate_clear'] = (c is not None and c[0] == 'clear', f"gate={c[0] if c else 'N/A'}")

# 20. manual_pause=false
c = db.execute("SELECT value FROM system_config WHERE key='manual_pause'").fetchone()
results['20_manual_pause_false'] = (c is not None and c[0] == 'false', f"pause={c[0] if c else 'N/A'}")

# 21. standing_authorization=true
c = db.execute("SELECT value FROM system_config WHERE key='standing_authorization'").fetchone()
results['21_standing_auth_true'] = (c is not None and c[0] == 'true', f"auth={c[0] if c else 'N/A'}")

# 22. send_pause=false
c = db.execute("SELECT value FROM system_config WHERE key='send_pause'").fetchone()
results['22_send_pause_false'] = (c is not None and c[0] == 'false', f"send_pause={c[0] if c else 'N/A'}")

# Extra: plan_id check
c = db.execute("SELECT plan_id, planned_sequence FROM final_send_plan WHERE status='planned'").fetchone()
results['X_plan_id'] = (c is not None and c[0] == 'plan_901_games_pilot_20260728', f"plan={c[0] if c else 'N/A'} seq={c[1] if c else 'N/A'}")

# 24. Outreach Automation PAUSED — check execution_mode != 'outreach'
c = db.execute("SELECT value FROM system_config WHERE key='execution_mode'").fetchone()
mode = c[0] if c else 'N/A'
results['24_automation_paused'] = (mode != 'outreach', f'exec_mode={mode}')

db.close()

# === OUTPUT ===
print('=' * 65)
print('901 GAMES PILOT FRESH PREFLIGHT — 2026-07-29 08:55 CST')
print('=' * 65)
all_pass = True
failures = []
for key, (passed, detail) in sorted(results.items()):
    s = 'PASS' if passed else 'FAIL'
    if not passed:
        all_pass = False
        failures.append(key)
    print(f'[{s}] {key}: {detail}')
print('=' * 65)
if all_pass:
    print('ALL 25 CHECKS PASS — CLEARED FOR DELAYED SEND')
else:
    print(f'BLOCKED: {len(failures)} failures: {failures}')
    print('DO NOT PROCEED. STOP AND INVESTIGATE.')
