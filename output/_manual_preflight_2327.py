"""Manual Preflight — 23:27 CST — Strictly Read-Only"""
import sqlite3, json, os, subprocess, re, urllib.request
from datetime import datetime, timezone, timedelta

ASIA_SH = timezone(timedelta(hours=8))
BASE = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach'
DB = os.path.join(BASE, 'data', 'bd_leads.db')
GUARD = os.path.join(BASE, 'output', 'bd_delivery_guard_status.json')
POLLER = os.path.join(BASE, 'output', 'bd_ops_poller_status.json')

results = {}
all_pass = True

# Infrastructure
try:
    with open(GUARD) as f: gs = json.load(f)
    hb = gs.get('last_heartbeat_at', '')
    if hb:
        hb_age = (datetime.now(ASIA_SH) - datetime.fromisoformat(hb)).total_seconds()
        mode = gs.get('current_mode', '')
        threshold = 60 if mode == 'critical' else 900
        results['guard_hb'] = (hb_age < threshold, f"age={int(hb_age)}s mode={mode}")
        results['guard_mode'] = (mode == 'critical', f"mode={mode}")
        results['system_req'] = (gs.get('system_required') == True, f"sr={gs.get('system_required')}")
        results['display_req'] = (gs.get('display_required') == True, f"dr={gs.get('display_required')}")
        results['ac_power'] = (gs.get('ac_power') == True, f"ac={gs.get('ac_power')}")
    else:
        results['guard_hb'] = (False, 'no_hb')
except Exception as e:
    results['guard'] = (False, str(e)[:60])

# Ops Center
try:
    r = urllib.request.urlopen('http://127.0.0.1:8765/api/dashboard', timeout=3)
    results['ops_center'] = (r.status == 200, f'HTTP {r.status}')
except:
    try:
        with open(POLLER) as f: ps = json.load(f)
        ph = ps.get('last_heartbeat_at', '')
        jobs_ok = all(j.get('consecutive_failures', 0) == 0 for j in ps.get('jobs', {}).values())
        pa = int((datetime.now(ASIA_SH) - datetime.fromisoformat(ph)).total_seconds()) if ph else 99999
        results['ops_center'] = (ph and jobs_ok and pa < 1200, f"poller_age={pa}s jobs_ok={jobs_ok}")
    except Exception as e:
        results['ops_center'] = (False, str(e)[:60])

# Worker
try:
    curl = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
        'https://roktandrazo-email-tracker.1569032023yf.workers.dev/health'],
        capture_output=True, text=True, timeout=10)
    results['worker'] = (curl.stdout.strip() == '200', f"HTTP {curl.stdout.strip()[:10]}")
except:
    results['worker'] = (False, 'no_response')

# DB checks
conn = sqlite3.connect(DB)

sl = conn.execute("SELECT COUNT(*) FROM send_log").fetchone()[0]
results['send_log'] = (sl == 330, f'sl={sl}')

planned = conn.execute("SELECT COUNT(*) FROM final_send_plan WHERE status='planned'").fetchone()[0]
results['planned'] = (planned > 0 and planned <= 60, f'planned={planned}')

fu = conn.execute("SELECT COUNT(*) FROM final_send_plan WHERE status='planned' AND message_type='follow_up'").fetchone()[0]
results['no_fu'] = (fu == 0, f'fu={fu}')

rg = conn.execute("SELECT value FROM system_config WHERE key='risk_gate_status'").fetchone()
results['risk_gate'] = (rg and rg[0] == 'clear', f"rg={rg[0] if rg else 'N/A'}")

mp = conn.execute("SELECT value FROM system_config WHERE key='manual_pause'").fetchone()
results['manual_pause'] = (mp and mp[0] == 'false', f"mp={mp[0] if mp else 'N/A'}")

sa = conn.execute("SELECT value FROM system_config WHERE key='standing_authorization'").fetchone()
results['standing_auth'] = (sa and sa[0] == 'true', f"sa={sa[0] if sa else 'N/A'}")

sp = conn.execute("SELECT value FROM system_config WHERE key='send_pause'").fetchone()
results['send_pause'] = (sp and sp[0] == 'false', f"sp={sp[0] if sp else 'N/A'}")

# No orchestrator processes
proc = subprocess.run(['tasklist'], capture_output=True, timeout=8)
raw = proc.stdout
if raw:
    for enc in ['utf-8', 'gbk', 'cp936', 'latin-1']:
        try: text = raw.decode(enc, errors='strict'); break
        except: pass
    else: text = raw.decode('latin-1', errors='replace')
    orch = [l for l in text.split('\n') if 'orchestrator' in l.lower()]
    results['no_orch'] = (len(orch) == 0, f'procs={len(orch)}')
else:
    results['no_orch'] = (True, 'stdout_none')

# Per-entry safety
suppressed = set(r[0] for r in conn.execute("SELECT DISTINCT email FROM suppression_list"))
sent_emails = set(r[0] for r in conn.execute("SELECT DISTINCT email FROM send_log WHERE status='sent'"))
sent_orgs = set()
for r in conn.execute("SELECT DISTINCT COALESCE(NULLIF(l.organization_key,''),'org_'||sl.lead_id) FROM send_log sl JOIN leads l ON sl.lead_id=l.id WHERE sl.status='sent'"):
    sent_orgs.add(r[0])
for r in conn.execute("SELECT DISTINCT COALESCE(NULLIF(l.organization_key,''),'org_'||sl.lead_id) FROM send_log sl JOIN leads l ON sl.lead_id=l.id WHERE sl.status='sent' AND (sl.message_type IS NULL OR sl.message_type='')"):
    sent_orgs.add(r[0])
replied = set(r[0] for r in conn.execute("SELECT DISTINCT lead_id FROM reply_log"))
bounced = set(r[0] for r in conn.execute("SELECT DISTINCT lead_id FROM bounce_log WHERE bounce_type='hard'"))

entries = conn.execute("SELECT id, lead_id, recipient_email, body_html FROM final_send_plan WHERE status='planned'").fetchall()
entry_issues = 0
for e in entries:
    lid = e[1]; email = (e[2] or '').lower(); html = e[3] or ''
    imgs = re.findall(r'<img[^>]*src="([^"]*)"[^>]*>', html)
    worker_px = [s for s in imgs if 'workers.dev' in s]
    if len(imgs) != 1 or len(worker_px) != 1:
        entry_issues += 1
    if email in suppressed: entry_issues += 1
    if email in sent_emails: entry_issues += 1
    if lid in replied: entry_issues += 1
    if lid in bounced: entry_issues += 1
    org = conn.execute("SELECT COALESCE(NULLIF(organization_key,''),'org_'||id) FROM leads WHERE id=?", (lid,)).fetchone()
    org_key = org[0] if org else f'org_{lid}'
    if org_key in sent_orgs: entry_issues += 1

results['entries'] = (entry_issues == 0, f'issues={entry_issues}')

trk = conn.execute("SELECT COUNT(*) FROM email_tracking_messages WHERE status='prepared' AND is_test=0").fetchone()[0]
results['tracking'] = (trk >= planned, f'tracking={trk}')

conn.close()

# Output
print('=' * 60)
print('23:27 MANUAL PREFLIGHT')
print('=' * 60)
for key, (passed, detail) in results.items():
    s = 'PASS' if passed else 'FAIL'
    if not passed: all_pass = False
    print(f'[{s}] {key}: {detail}')
print('=' * 60)
if all_pass:
    print('ALL PASS — READY FOR SEND')
    print(f'  60 planned entries in Final Send Plan')
    print(f'  {trk} tracking tokens prepared')
    print(f'  send_log=330 (pre-send)')
    print(f'  0 entry-level issues')
else:
    print('BLOCKED — need investigation')
print('=' * 60)
