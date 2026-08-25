"""
P2.3D3 — NORMAL PRODUCTION QUOTA READINESS / TONIGHT RUN (READ-ONLY AUDIT + permitted DNS warm).
Run with PRODUCTION_PYTHON from PRODUCTION_WORKING_DIR.
Reads real quota config, recomputes live V2 inventory + SAFE_FSP + Preflight-ready.
DNS freshness refreshed via the EXISTING production mechanism (query_mx + mx_cache_<domain> write,
identical to preflight_gate.check_dns_freshness internals). Does NOT send, does NOT create FSP/Auth,
does NOT modify manual_pause/scheduler/code.
"""
import os, sys, json, sqlite3
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
sys.path.insert(0, PROJ)

import env_loader  # noqa: F401  (load .env -> real TRACKING token, matching production)
from bd_db import get_db, get_config
import preflight_gate as g
from campaign_eligible_v2 import review_campaign_eligible_v2, _domain_of_email, _ALLOWED_MX
import outreach_control as oc

ASIA_SH = timezone(timedelta(hours=8))
NOW = datetime.now(ASIA_SH)

conn = get_db()
conn.row_factory = sqlite3.Row

# ── A. QUOTA CONFIG (list sources, indicate canonical) ──────────────
db_daily_target = int(get_config("daily_run_target") or "40")
db_daily_send = int(get_config("daily_send_target") or "40")
oc_new_outreach = oc.NEW_OUTREACH_TARGET
oc_follow_up = oc.FOLLOW_UP_MAX
# execution host policy
exec_max_new = None
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "bd_execution_host_service",
        os.path.join(PROJ, "bd_execution_host_service.py"))
    ehs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ehs)
    exec_max_new = ehs.SEND_POLICY.get("max_new_outreach")
except Exception as e:
    exec_max_new = f"<read-error:{e}>"

print("===== A. PRODUCTION QUOTA CONFIG (sources) =====")
print(f"src1_system_config.daily_run_target = {db_daily_target}  (read by bd_db.get_daily_target(); runtime target)")
print(f"src1b_system_config.daily_send_target = {db_daily_send}")
print(f"src2_outreach_control.NEW_OUTREACH_TARGET = {oc_new_outreach}  (used by bd_orchestrator to build plan)")
print(f"src3_bd_execution_host_service.SEND_POLICY.max_new_outreach = {exec_max_new}  (execution host cap)")
print(f"src4_agent_daily_report/auto_replenish_loop.DAILY_TARGET = 20  (report/replenish constant, also reads daily_run_target)")

# Canonical authority: get_daily_target() returns daily_run_target (live runtime config) = authoritative tonight target.
CONFIGURED_DAILY_SEND_QUOTA = db_daily_target          # canonical runtime target
CONFIGURED_NEW_OUTREACH_QUOTA = db_daily_target        # tonight new_outreach ceiling = runtime target
CONFIGURED_FOLLOW_UP_QUOTA = oc_follow_up              # only follow_up hard cap in code
print(f"CANONICAL_AUTHORITY = bd_db.get_daily_target() -> system_config.daily_run_target = {db_daily_target}")

# ── B/C. LIVE V2 INVENTORY ─────────────────────────────────────────
# Base leads: not already terminal, valid email. V2 gating done by review_campaign_eligible_v2.
base_rows = conn.execute(
    """SELECT * FROM leads
       WHERE status NOT IN ('sent','bounced','do_not_contact','rejected','failed',
                            'delivery_issue','bounce_review','contact_form_pool')
         AND email IS NOT NULL AND email != '' AND email LIKE '%@%.%'
       ORDER BY id"""
).fetchall()

domains = set()
for r in base_rows:
    d = _domain_of_email(str(r["email"] or ""))
    if d:
        domains.add(d)

# batch live MX (one Worker call per domain) — same as select_candidates_for_plan_v2
mx_lookup = {}
for d in sorted(domains):
    try:
        st, _ = g.query_mx(d)
    except Exception:
        st = "dns_error"
    mx_lookup[d] = st

suppressed = {str(r["email"]).strip().lower() for r in conn.execute("SELECT email FROM suppression_list")}
hard_bounce = {str(r["email"]).strip().lower() for r in conn.execute(
    "SELECT email FROM bounce_log WHERE lower(COALESCE(bounce_type,'')) IN ('hard','policy','permanent','domain_invalid')")}
sent_lead_ids = {r["lead_id"] for r in conn.execute("SELECT lead_id FROM send_log WHERE status='sent'")}
sent_orgs = {str(r["org"] or "").strip().lower()
             for r in conn.execute("SELECT COALESCE(NULLIF(l.organization_key,''),'org:'||l.id) org FROM send_log sl JOIN leads l ON sl.lead_id=l.id WHERE sl.status='sent' AND sl.message_type='new_outreach'")}

FREE_MAIL = {"gmail.com","googlemail.com","yahoo.com","yahoo.co.uk","hotmail.com","outlook.com",
             "live.com","msn.com","aol.com","icloud.com","me.com","mac.com","gmx.com","gmx.net",
             "proton.me","protonmail.com","yandex.com","mail.com","zoho.com","comcast.net",
             "cox.net","att.net","sbcglobal.net","verizon.net","earthlink.net"}

def official_domain(website):
    if not website:
        return None
    w = website.strip().lower()
    w = w.replace("https://","").replace("http://","").replace("www.","")
    w = w.split("/")[0].split("?")[0]
    return w or None

v2_eligible = []   # CURRENT_V2_UNSENT candidates (pool==CAMPAIGN_ELIGIBLE_V2)
for r in base_rows:
    lead = dict(r)
    res = review_campaign_eligible_v2(lead, {"conn": conn, "mx_lookup": mx_lookup})
    if res.get("pool") == "CAMPAIGN_ELIGIBLE_V2":
        v2_eligible.append((lead, res))

CURRENT_V2_UNSENT = len(v2_eligible)

# SAFE_FSP = V2 eligible minus send-readiness exclusions
safe = []
for lead, res in v2_eligible:
    email = (lead.get("email") or "").strip().lower()
    org_key = (lead.get("organization_key") or "").strip()
    tz_status = lead.get("timezone_status")
    # exclusions
    if email in suppressed: continue
    if email in hard_bounce: continue
    if lead["id"] in sent_lead_ids: continue
    eff_org = org_key.lower() if org_key else f"org:{lead['id']}"
    if eff_org in sent_orgs: continue
    if tz_status != "RESOLVED": continue
    if not org_key: continue
    safe.append((lead, res))

SAFE_FSP_CANDIDATES = len(safe)

# breakdown by tier/domain + timezone
e1_store = e1_free = other_v2 = 0
tz_bucket = {"ET":0,"CT":0,"MT":0,"PT":0,"OTHER":0}
for lead, res in safe:
    email = (lead.get("email") or "").strip().lower()
    edom = _domain_of_email(email) or ""
    tier = res.get("tier")
    odom = official_domain(lead.get("official_website"))
    is_e1 = (tier == "E1")
    if is_e1:
        if edom == odom and odom:
            e1_store += 1
        elif edom in FREE_MAIL:
            e1_free += 1
        else:
            other_v2 += 1
    else:
        other_v2 += 1
    tz = lead.get("recipient_timezone")
    if tz == "America/New_York": tz_bucket["ET"] += 1
    elif tz == "America/Chicago": tz_bucket["CT"] += 1
    elif tz in ("America/Denver","America/Phoenix"): tz_bucket["MT"] += 1
    elif tz == "America/Los_Angeles": tz_bucket["PT"] += 1
    else: tz_bucket["OTHER"] += 1

# ── C. DNS / MX FRESHNESS — refresh via EXISTING production mechanism ─
# Write mx_cache_<domain> exactly as preflight_gate.check_dns_freshness does (query_mx + _write_config).
dns_fresh = dns_stale = 0
preflight_ready = 0
refreshed_domains = set()
for lead, res in safe:
    edom = _domain_of_email(str(lead.get("email") or "").strip().lower())
    if not edom or edom in refreshed_domains:
        continue
    refreshed_domains.add(edom)
    status = mx_lookup.get(edom, "dns_error")
    checked_at = NOW.isoformat()
    try:
        g._write_config(conn, f"mx_cache_{edom}", json.dumps({"status": status, "checked_at": checked_at}))
    except sqlite3.Error:
        pass
    if status in _ALLOWED_MX:
        dns_fresh += 1
    else:
        dns_stale += 1

DNS_FRESH_COUNT = dns_fresh
DNS_STALE_COUNT = dns_stale
# PREFLIGHT_READY = SAFE_FSP with live MX ok (cache now fresh within 24h)
for lead, res in safe:
    edom = _domain_of_email(str(lead.get("email") or "").strip().lower())
    if mx_lookup.get(edom) in _ALLOWED_MX:
        preflight_ready += 1
PREFLIGHT_READY_CANDIDATES = preflight_ready

# set informational refresh marker
try:
    g._write_config(conn, "last_preflight_cache_refresh", NOW.isoformat())
except sqlite3.Error:
    pass

# ── B. TONIGHT_TARGET ──
TONIGHT_TARGET = min(CONFIGURED_NEW_OUTREACH_QUOTA, PREFLIGHT_READY_CANDIDATES)

# ── D. RISK GATE (live) ──
mp = get_config("manual_pause")
sa = get_config("standing_authorization")
rg = get_config("risk_gate_status")
sp = get_config("send_pause")
CURRENT_PRODUCTION_SEND_ALLOWED = (mp == "false" and sa == "true" and rg == "clear" and sp == "false")

print("\n===== B/C. LIVE INVENTORY =====")
print(f"CURRENT_V2_UNSENT = {CURRENT_V2_UNSENT}")
print(f"SAFE_FSP_CANDIDATES = {SAFE_FSP_CANDIDATES}")
print(f"E1_OFFICIAL_STORE_DOMAIN = {e1_store}")
print(f"E1_OFFICIAL_FREE_MAILBOX = {e1_free}")
print(f"OTHER_V2 = {other_v2}")
print(f"  ET(America/New_York) = {tz_bucket['ET']}")
print(f"  CT(America/Chicago) = {tz_bucket['CT']}")
print(f"  MT(America/Denver+Phoenix) = {tz_bucket['MT']}")
print(f"  PT(America/Los_Angeles) = {tz_bucket['PT']}")
print(f"DNS_FRESH_COUNT = {DNS_FRESH_COUNT}  (post-refresh; cache warmed via production query_mx+mx_cache_<domain>)")
print(f"DNS_STALE_COUNT = {DNS_STALE_COUNT}")
print(f"PREFLIGHT_READY_CANDIDATES = {PREFLIGHT_READY_CANDIDATES}")
print(f"TONIGHT_TARGET = {TONIGHT_TARGET}")

print("\n===== D. RISK GATE (live) =====")
print(f"manual_pause = {mp}")
print(f"standing_authorization = {sa}")
print(f"risk_gate_status = {rg}")
print(f"send_pause = {sp}")
print(f"CURRENT_PRODUCTION_SEND_ALLOWED = {CURRENT_PRODUCTION_SEND_ALLOWED}")

print("\n===== A. QUOTA (final) =====")
print(f"CONFIGURED_DAILY_SEND_QUOTA = {CONFIGURED_DAILY_SEND_QUOTA}")
print(f"CONFIGURED_NEW_OUTREACH_QUOTA = {CONFIGURED_NEW_OUTREACH_QUOTA}")
print(f"CONFIGURED_FOLLOW_UP_QUOTA = {CONFIGURED_FOLLOW_UP_QUOTA}")

conn.close()
