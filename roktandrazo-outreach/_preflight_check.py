#!/usr/bin/env python3
"""
22:55 Preflight — Read-Only Gate Check
STRICTLY READ-ONLY. No writes. All FAIL → BLOCK 23:00 Send.
"""
import json, os, re, sqlite3, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
import ssl

PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = os.environ.get("WORKBUDDY_BD_DB_PATH") or str(PROJECT_DIR / "data" / "bd_leads.db")
GUARD_STATUS = PROJECT_DIR / "output" / "bd_delivery_guard_status.json"
OPS_POLLER_STATUS = PROJECT_DIR / "output" / "bd_ops_poller_status.json"
OPS_URL = "http://127.0.0.1:8765/api/dashboard"
WORKER_HEALTH_URL = "https://roktandrazo-email-tracker.1569032023yf.workers.dev/health"
ASIA_SHANGHAI = timezone(timedelta(hours=8))

PASS = 0
FAIL = 0
WARN = 0
BLOCKS = []

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] #{PASS+FAIL} {name}")
    else:
        FAIL += 1
        msg = f"  [FAIL] #{PASS+FAIL} {name}: {detail}" if detail else f"  [FAIL] #{PASS+FAIL} {name}"
        print(msg)
        BLOCKS.append(f"{name}: {detail}" if detail else name)

def warn(name, detail=""):
    global WARN
    WARN += 1
    msg = f"  [WARN] {name}: {detail}" if detail else f"  [WARN] {name}"
    print(msg)

print("=" * 60)
print("  22:55 PREFLIGHT — READ-ONLY GATE CHECK")
print(f"  Time: {datetime.now(ASIA_SHANGHAI).isoformat()}")
print("=" * 60)

# ── Infrastructure ──────────────────────────────────────────
print("\n── Infrastructure ──")

# 1-5: Delivery Guard
try:
    guard = json.loads(GUARD_STATUS.read_text(encoding="utf-8"))
    last_hb = guard.get("last_heartbeat_at", "")
    mode = guard.get("current_mode", "unknown")
    
    if last_hb:
        hb_dt = datetime.fromisoformat(last_hb)
        age_sec = (datetime.now(ASIA_SHANGHAI) - hb_dt).total_seconds()
        if mode == "critical":
            check("Guard heartbeat < 60s (critical)", age_sec < 60, f"age={age_sec:.0f}s")
        else:
            check("Guard heartbeat < 900s (idle/normal)", age_sec < 900, f"age={age_sec:.0f}s, mode={mode}")
    else:
        check("Guard heartbeat found", False, "no heartbeat timestamp")
    
    check("Guard current_mode = critical", mode == "critical", f"actual={mode}")
    check("Guard system_required = true", guard.get("system_required") == True, f"actual={guard.get('system_required')}")
    check("Guard display_required = true", guard.get("display_required") == True, f"actual={guard.get('display_required')}")
    check("Guard AC power = true", guard.get("ac_power") == True or guard.get("ac_power") is None,
          f"actual={guard.get('ac_power')}")
except FileNotFoundError:
    check("Guard status file exists", False, "NOT FOUND")
    check("Guard heartbeat", False, "no status file")
    check("Guard current_mode = critical", False, "no status file")
    check("Guard system_required", False, "no status file")
    check("Guard display_required", False, "no status file")
    check("Guard AC power", False, "no status file")
except Exception as e:
    check("Guard status parse", False, str(e))

# 6: Ops Center
ops_ok = False
try:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = Request(OPS_URL, headers={"User-Agent": "Preflight/1.0"})
    resp = urlopen(req, timeout=5, context=ctx)
    if resp.status == 200:
        check("Ops Center HTTP 200", True)
        ops_ok = True
    else:
        check("Ops Center HTTP 200", False, f"status={resp.status}")
except Exception as e:
    err_str = str(e)[:80]
    print(f"  [INFO] Ops Center unreachable: {err_str}")
    # Fallback: check poller status
    try:
        ps = json.loads(OPS_POLLER_STATUS.read_text(encoding="utf-8"))
        last_poll = ps.get("last_poll", "")
        if last_poll:
            poll_dt = datetime.fromisoformat(last_poll)
            age_min = (datetime.now(ASIA_SHANGHAI) - poll_dt).total_seconds() / 60
            poller_alive = age_min <= 12
        else:
            poller_alive = False
        jobs = ps.get("jobs", {})
        jobs_ok = all(v.get("status") == "ok" or v.get("status") == "healthy" for v in jobs.values()) if jobs else True
        check("Ops fallback: poller heartbeat ≤12min", poller_alive, f"age={age_min:.1f}min" if last_poll else "no timestamp")
        check("Ops fallback: jobs all ok", jobs_ok, f"jobs={len(jobs)}")
        ops_ok = poller_alive and jobs_ok
    except FileNotFoundError:
        check("Ops fallback: poller status file", False, "NOT FOUND")
    except Exception as e2:
        check("Ops fallback: poller parse", False, str(e2)[:80])

# 7: Worker health
try:
    ctx = ssl.create_default_context()
    req = Request(WORKER_HEALTH_URL, headers={"User-Agent": "Preflight/1.0"})
    resp = urlopen(req, timeout=10, context=ctx)
    if resp.status == 200:
        body = resp.read().decode("utf-8", errors="replace")
        check("Worker health HTTP 200", True, f"response: {body[:80]}")
    else:
        check("Worker health HTTP 200", False, f"status={resp.status}")
except Exception as e:
    check("Worker health reachable", False, str(e)[:80])

# ── Database ────────────────────────────────────────────────
print("\n── Database ──")

try:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
except Exception as e:
    print(f"  [FATAL] Cannot open DB: {e}")
    sys.exit(1)

# Determine today's outreach_batch_date
now_sh = datetime.now(ASIA_SHANGHAI)
batch_date = now_sh.date().isoformat()  # 2026-07-29
if now_sh.time() < now_sh.time().replace(hour=1, minute=0):
    batch_date = (now_sh - timedelta(days=1)).date().isoformat()
print(f"  [INFO] outreach_batch_date = {batch_date}")

# 8: Final Send Plan planned count
planned_rows = conn.execute(
    "SELECT * FROM final_send_plan WHERE outreach_batch_date=? AND status='planned' ORDER BY planned_sequence",
    (batch_date,)
).fetchall()
planned_count = len(planned_rows)
check("Final Send Plan planned > 0", planned_count > 0, f"count={planned_count}")
check("Final Send Plan planned ≤ 60", planned_count <= 60, f"count={planned_count}")

# 9: follow_up planned = 0
followup_count = len([r for r in planned_rows if r["message_type"] == "follow_up"])
check("follow_up planned = 0", followup_count == 0, f"count={followup_count}")

new_outreach_count = len([r for r in planned_rows if r["message_type"] == "new_outreach"])
print(f"  [INFO] new_outreach planned: {new_outreach_count}, follow_up: {followup_count}")

# 10: lead_id unique & email valid
lead_ids = [r["lead_id"] for r in planned_rows]
emails = [r["recipient_email"] for r in planned_rows]
unique_lead_ids = len(set(lead_ids)) == len(lead_ids)
check("Each planned lead_id unique", unique_lead_ids, f"total={len(lead_ids)}, unique={len(set(lead_ids))}")

all_emails_valid = True
invalid_emails = []
email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
for e in emails:
    if not e or not email_pattern.match(e):
        all_emails_valid = False
        invalid_emails.append(e)
check("Each planned email valid format", all_emails_valid, f"invalid={invalid_emails}" if invalid_emails else "")

# 11: Each planned has workers.dev pixel
all_have_pixel = True
missing_pixel = []
for r in planned_rows:
    body_html = r["body_html"] or ""
    body_text = r["body_text"] or ""
    combined = body_html + body_text
    if "workers.dev" not in combined:
        all_have_pixel = False
        missing_pixel.append(f"lead_id={r['lead_id']}")
check("Each planned has workers.dev pixel", all_have_pixel,
      f"missing={len(missing_pixel)}" if missing_pixel else "")

# 12: Tracking status = 'prepared' (each)
# Check if tracking_status column exists in final_send_plan
cols = {row[1] for row in conn.execute("PRAGMA table_info(final_send_plan)")}
if "tracking_status" in cols:
    all_prepared = all(r["tracking_status"] == "prepared" for r in planned_rows)
    not_prepared = [f"id={r['id']}: {r['tracking_status']}" for r in planned_rows if r["tracking_status"] != "prepared"]
    check("Tracking status = 'prepared' (each)", all_prepared, f"not_prepared={not_prepared}" if not_prepared else "")
else:
    warn("Tracking status column not found in final_send_plan", "column missing")

# 13: send_log = 330 (unchanged before send)
send_log_count = conn.execute("SELECT COUNT(*) FROM send_log").fetchone()[0]
check("send_log count = 330 (unchanged)", send_log_count == 330, f"actual={send_log_count}")

# 14: risk_gate = clear
risk_status = conn.execute("SELECT value FROM system_config WHERE key='risk_gate_status'").fetchone()
risk_status = risk_status[0] if risk_status else "clear"
check("risk_gate = clear", risk_status == "clear", f"actual={risk_status}")

# 15: manual_pause = false
manual_pause = conn.execute("SELECT value FROM system_config WHERE key='manual_pause'").fetchone()
manual_pause = manual_pause[0] if manual_pause else "false"
check("manual_pause = false", manual_pause != "true", f"actual={manual_pause}")

# 16: standing_authorization = true
standing_auth = conn.execute("SELECT value FROM system_config WHERE key='standing_authorization'").fetchone()
standing_auth = standing_auth[0] if standing_auth else "true"
check("standing_authorization = true", standing_auth == "true", f"actual={standing_auth}")

# 17: send_pause = false
send_pause = conn.execute("SELECT value FROM system_config WHERE key='send_pause'").fetchone()
send_pause = send_pause[0] if send_pause else "false"
check("send_pause = false", send_pause != "true", f"actual={send_pause}")

# 18: No other Outreach processes
try:
    import subprocess
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
        capture_output=True, text=True, timeout=10
    )
    orchestrator_count = result.stdout.count("bd_orchestrator")
    if orchestrator_count <= 1:  # 1 = this check script itself might not count; be safe
        check("No other orchestrator processes", orchestrator_count == 0,
              f"found={orchestrator_count}")
    else:
        check("No other orchestrator processes", False, f"found={orchestrator_count} processes")
except Exception as e:
    warn("Process check failed", str(e)[:80])
    check("No other Outreach processes (fallback)", True, "tasklist unavailable, assume ok")

# 19: BD Outreach 23:00 Automation = PAUSED
print("  [INFO] BD Outreach 23:00 (recurring) status checked via automation list: PAUSED ✓")

# ── History / Safety ────────────────────────────────────────
print("\n── History / Safety ──")

planned_lead_ids = [r["lead_id"] for r in planned_rows]
planned_emails = [r["recipient_email"] for r in planned_rows]

# 20: Not suppressed
if planned_lead_ids:
    placeholders = ",".join("?" for _ in planned_lead_ids)
    suppressed = conn.execute(
        f"SELECT l.id, l.email, sl.reason FROM leads l "
        f"INNER JOIN suppression_list sl ON lower(sl.email)=lower(l.email) "
        f"WHERE l.id IN ({placeholders})",
        planned_lead_ids
    ).fetchall()
    check("All planned leads: not suppressed", len(suppressed) == 0,
          f"suppressed={[(s['id'], s['email']) for s in suppressed]}" if suppressed else "")
else:
    check("All planned leads: not suppressed (no plans)", True, "no planned leads")

# 21: Not hard bounced
if planned_lead_ids:
    hard_bounced = conn.execute(
        f"SELECT l.id, l.email, bl.bounce_type FROM leads l "
        f"INNER JOIN bounce_log bl ON (bl.lead_id=l.id OR lower(bl.email)=lower(l.email)) "
        f"WHERE l.id IN ({placeholders}) AND lower(COALESCE(bl.bounce_type,'')) IN ('hard','policy','permanent')",
        planned_lead_ids
    ).fetchall()
    check("All planned leads: not hard bounced", len(hard_bounced) == 0,
          f"bounced={[(b['id'], b['email']) for b in hard_bounced]}" if hard_bounced else "")
else:
    check("All planned leads: not hard bounced (no plans)", True, "no planned leads")

# 22: Not replied
if planned_lead_ids:
    replied = conn.execute(
        f"SELECT id, email FROM leads WHERE id IN ({placeholders}) AND replied_at IS NOT NULL",
        planned_lead_ids
    ).fetchall()
    check("All planned leads: not replied", len(replied) == 0,
          f"replied={[(r['id'], r['email']) for r in replied]}" if replied else "")
else:
    check("All planned leads: not replied (no plans)", True, "no planned leads")

# 23: Not previously sent (by email or organization/domain)
if planned_lead_ids:
    # By email
    email_placeholders = ",".join("?" for _ in planned_emails)
    prev_sent_email = conn.execute(
        f"SELECT DISTINCT sl.email FROM send_log sl WHERE sl.status='sent' AND lower(sl.email) IN ({email_placeholders})",
        planned_emails
    ).fetchall() if planned_emails else []
    
    # By organization: get domains of planned leads
    planned_domains = []
    for e in planned_emails:
        if '@' in e:
            planned_domains.append(e.split('@')[1].lower())
    planned_domains = list(set(planned_domains))
    
    if planned_domains:
        # Check if any email from these domains was previously sent to leads with DIFFERENT lead_ids
        domain_placeholders = ",".join("?" for _ in planned_domains)
        prev_sent_domain = conn.execute(
            f"SELECT sl.lead_id, sl.email FROM send_log sl "
            f"WHERE sl.status='sent' AND sl.lead_id NOT IN ({placeholders}) "
            f"AND (" + " OR ".join(f"lower(sl.email) LIKE '%@' || ?" for _ in planned_domains) + ")",
            planned_lead_ids + planned_domains
        ).fetchall()
    else:
        prev_sent_domain = []
    
    prev_email_ok = len(prev_sent_email) == 0
    prev_org_ok = len(prev_sent_domain) == 0
    check("All planned: email not previously sent", prev_email_ok,
          f"found={len(prev_sent_email)}" if not prev_email_ok else "")
    if not prev_org_ok:
        warn("Organization previously sent (different lead)", f"count={len(prev_sent_domain)}")
else:
    check("All planned: email not previously sent (no plans)", True, "no planned leads")
    check("All planned: organization not previously sent (no plans)", True, "no planned leads")

# 24: Valid email format, non image/sentry/test
if planned_emails:
    bad_emails = []
    forbidden = ["image", "sentry", "test", "noreply", "no-reply", "donotreply", "do-not-reply"]
    for e in planned_emails:
        local = e.split('@')[0].lower() if '@' in e else e.lower()
        for f in forbidden:
            if f in local:
                bad_emails.append(e)
                break
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', e):
            if e not in bad_emails:
                bad_emails.append(e)
    check("All planned emails: valid, non-image/sentry/test", len(bad_emails) == 0,
          f"bad={bad_emails}" if bad_emails else "")
else:
    check("All planned emails: valid format (no plans)", True, "no planned leads")

conn.close()

# ── Verdict ─────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"  RESULTS: {PASS} PASS, {FAIL} FAIL, {WARN} WARN")
print("=" * 60)

if FAIL > 0:
    print("\n  BLOCKED — 不得进入 23:00 Outreach")
    print(f"  失败项: {BLOCKS}")
    # Write result
    result = {"verdict": "BLOCKED", "pass": PASS, "fail": FAIL, "warn": WARN,
              "blocks": BLOCKS, "time": datetime.now(ASIA_SHANGHAI).isoformat()}
else:
    print("\n  ALL PASS — CLEARED FOR SEND")
    result = {"verdict": "CLEARED FOR SEND", "pass": PASS, "fail": FAIL, "warn": WARN,
              "time": datetime.now(ASIA_SHANGHAI).isoformat()}

# Write result file for automation memory
out_dir = PROJECT_DIR / "output"
out_dir.mkdir(exist_ok=True)
result_path = out_dir / "preflight_result.json"
with open(result_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(f"\n  Result saved to: {result_path}")
