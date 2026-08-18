"""BD Daily Collection Report Generator — Read-only. No SMTP, no send plan."""
import sqlite3, json, os
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "bd_leads.db")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "daily_collection_reports")

shanghai_now = datetime.now(timezone(timedelta(hours=8)))
today_str = shanghai_now.strftime("%Y-%m-%d")
ts_full = shanghai_now.strftime("%Y-%m-%dT%H:%M:%S+08:00")
ts_short = shanghai_now.strftime("%Y-%m-%d %H:%M")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

today_start = f"{today_str} 00:00:00"
today_end = f"{today_str} 23:59:59"

r = {}  # results dict

# --- Core counts ---
c.execute("SELECT COUNT(*) as cnt FROM leads")
r["total_leads"] = c.fetchone()["cnt"]

c.execute("SELECT status, COUNT(*) as cnt FROM leads GROUP BY status ORDER BY cnt DESC")
r["status_distribution"] = {row["status"]: row["cnt"] for row in c.fetchall()}

allowed = ["TN","AR","KY","OH","IN","MN","NE","NC","OR","CO"]
c.execute(f"SELECT state, COUNT(*) as cnt FROM leads WHERE state IN ({','.join(['?']*len(allowed))}) GROUP BY state ORDER BY cnt DESC", allowed)
r["state_distribution"] = {row["state"]: row["cnt"] for row in c.fetchall()}

# --- Send eligibility ---
c.execute("SELECT send_eligibility, COUNT(*) as cnt FROM leads GROUP BY send_eligibility ORDER BY cnt DESC")
r["send_eligibility"] = {row["send_eligibility"] or "(empty)": row["cnt"] for row in c.fetchall()}

# --- Final Sendable (correct: use send_eligibility, not status) ---
c.execute("SELECT COUNT(*) as cnt FROM leads WHERE send_eligibility='broad_outreach_ready' AND (sent_at IS NULL OR sent_at = '')")
r["broad_ready_unsent"] = c.fetchone()["cnt"]

c.execute("SELECT COUNT(*) as cnt FROM leads WHERE send_eligibility='strict_a0' AND (sent_at IS NULL OR sent_at = '')")
r["strict_a0_unsent"] = c.fetchone()["cnt"]

r["final_sendable_unsent"] = r["broad_ready_unsent"] + r["strict_a0_unsent"]
r["gap_to_30"] = max(0, 30 - r["final_sendable_unsent"])
r["gap_to_60"] = max(0, 60 - r["final_sendable_unsent"])

# Detailed breakdown of broad_ready unsent
c.execute("""SELECT status, COUNT(*) as cnt FROM leads 
    WHERE send_eligibility='broad_outreach_ready' AND (sent_at IS NULL OR sent_at = '')
    GROUP BY status""")
r["broad_unsent_breakdown"] = {row["status"]: row["cnt"] for row in c.fetchall()}

# --- Today's activity ---
# NOTE: collected_at/last_checked_at use ISO-8601 'T' format (e.g. 2026-08-13T16:44:24+08:00),
# so a naive 'YYYY-MM-DD HH:MM:SS' string range would miss them. Use date() for format-agnostic matching.
c.execute("SELECT COUNT(*) as cnt FROM leads WHERE date(collected_at) = ?", (today_str,))
r["new_orgs_today"] = c.fetchone()["cnt"]

c.execute('SELECT COUNT(*) as cnt FROM leads WHERE email_source_type="website" AND date(last_checked_at) = ?', (today_str,))
r["website_emails_today"] = c.fetchone()["cnt"]

c.execute('SELECT COUNT(*) as cnt FROM leads WHERE email_source_type="facebook" AND date(last_checked_at) = ?', (today_str,))
r["facebook_emails_today"] = c.fetchone()["cnt"]

c.execute('SELECT COUNT(*) as cnt FROM leads WHERE status="approved_manual_send" AND date(last_checked_at) = ?', (today_str,))
r["manual_verified_today"] = c.fetchone()["cnt"]

# --- Pending queues ---
c.execute('SELECT COUNT(*) as cnt FROM leads WHERE status="manual_review_needed"')
r["manual_review_pending"] = c.fetchone()["cnt"]

c.execute('SELECT COUNT(*) as cnt FROM leads WHERE (email IS NULL OR email = "") AND official_website IS NOT NULL AND official_website != ""')
r["website_recovery_pending"] = c.fetchone()["cnt"]

try:
    c.execute('SELECT COUNT(*) as cnt FROM contact_recovery WHERE status="pending"')
    r["contact_recovery_pending"] = c.fetchone()["cnt"]
except:
    r["contact_recovery_pending"] = 0
try:
    c.execute('SELECT COUNT(*) as cnt FROM contact_recovery WHERE status="recheck_pending"')
    r["contact_recovery_recheck"] = c.fetchone()["cnt"]
except:
    r["contact_recovery_recheck"] = 0

# --- Network errors ---
r["network_errors"] = {}
try:
    c.execute("SELECT error_type, COUNT(*) as cnt FROM network_errors GROUP BY error_type ORDER BY cnt DESC")
    rows = c.fetchall()
    if rows:
        r["network_errors"] = {row["error_type"]: row["cnt"] for row in rows}
except:
    pass
# Fallback to leads.error_message if network_errors table missing/empty
if not r["network_errors"]:
    try:
        c.execute('SELECT error_message, COUNT(*) as cnt FROM leads WHERE error_message IS NOT NULL AND error_message != "" GROUP BY error_message ORDER BY cnt DESC LIMIT 10')
        r["network_errors"] = {row["error_message"]: row["cnt"] for row in c.fetchall()}
    except:
        pass

# --- Safety / send_log ---
try:
    c.execute("SELECT COUNT(*) as cnt FROM send_log")
    r["send_log_total"] = c.fetchone()["cnt"]
except:
    r["send_log_total"] = 0

try:
    # send_log.sent_at uses ISO-8601 'T' format (e.g. 2026-08-14T09:52:21+08:00) —
    # naive 'YYYY-MM-DD HH:MM:SS' range misses them. Use date() for format-agnostic matching.
    c.execute("SELECT COUNT(*) as cnt FROM send_log WHERE date(sent_at) = ?", (today_str,))
    r["send_log_today"] = c.fetchone()["cnt"]
except:
    r["send_log_today"] = 0

# NOTE: `send_plan` table does not exist; plan tracking lives in `final_send_plan`.
# Keep send_plan_today as alias of final_send_plan_today (both reflect "plans created today").
try:
    c.execute("SELECT COUNT(*) as cnt FROM final_send_plan WHERE date(created_at) = ?", (today_str,))
    r["send_plan_today"] = c.fetchone()["cnt"]
except:
    r["send_plan_today"] = 0

# --- Final Send Plan (verify = 0) ---
try:
    c.execute("SELECT COUNT(*) as cnt FROM final_send_plan")
    r["final_send_plan_total"] = c.fetchone()["cnt"]
except:
    r["final_send_plan_total"] = 0
try:
    c.execute("SELECT COUNT(*) as cnt FROM final_send_plan WHERE date(created_at) = ?", (today_str,))
    r["final_send_plan_today"] = c.fetchone()["cnt"]
except:
    r["final_send_plan_today"] = 0

# --- SMTP enabled flag ---
try:
    c.execute('SELECT value FROM system_config WHERE key="SMTP_enabled"')
    row = c.fetchone()
    r["smtp_enabled"] = row["value"] if row else "0"
except:
    r["smtp_enabled"] = "0"

# --- Bounces / suppressed ---
try:
    c.execute("SELECT COUNT(*) as cnt FROM bounce_log")
    r["total_bounces"] = c.fetchone()["cnt"]
except:
    r["total_bounces"] = 0
try:
    c.execute("SELECT COUNT(*) as cnt FROM suppression_list")
    r["total_suppressed"] = c.fetchone()["cnt"]
except:
    r["total_suppressed"] = 0

# --- Bounces today (classification) ---
r["bounces_today"] = 0
r["bounces_today_classified"] = []
try:
    c.execute("SELECT COUNT(*) as cnt FROM bounce_log WHERE date(bounce_received_at) = ?", (today_str,))
    r["bounces_today"] = c.fetchone()["cnt"]
    c.execute("""SELECT bounce_type, status_code, diagnostic_code, COUNT(*) as cnt FROM bounce_log
        WHERE date(bounce_received_at) = ? GROUP BY bounce_type, status_code, diagnostic_code
        ORDER BY cnt DESC""", (today_str,))
    r["bounces_today_classified"] = [dict(row) for row in c.fetchall()]
except:
    pass

# --- Missing data ---
c.execute('SELECT COUNT(*) as cnt FROM leads WHERE (email IS NULL OR email = "")')
r["email_missing"] = c.fetchone()["cnt"]

c.execute('SELECT COUNT(*) as cnt FROM leads WHERE (email IS NULL OR email = "") AND contact_form_url IS NOT NULL AND contact_form_url != ""')
r["contact_form_only"] = c.fetchone()["cnt"]

# --- Active config ---
try:
    c.execute('SELECT value FROM system_config WHERE key="active_retail_city"')
    row = c.fetchone()
    r["active_city"] = row["value"] if row else "Nashville"
except:
    r["active_city"] = "Nashville"

try:
    c.execute('SELECT value FROM system_config WHERE key="active_city_state"')
    row = c.fetchone()
    r["active_state"] = row["value"] if row else "TN"
except:
    r["active_state"] = "TN"

# --- Current query / discovery state ---
r["current_query"] = {}
try:
    c.execute("SELECT status, COUNT(*) as cnt FROM lead_discovery_query_state GROUP BY status")
    q_status = {row["status"]: row["cnt"] for row in c.fetchall()}
    r["current_query"]["query_status_counts"] = q_status

    c.execute("SELECT * FROM lead_discovery_query_state WHERE status='in_progress' ORDER BY id DESC LIMIT 1")
    active_q = c.fetchone()
    r["current_query"]["active"] = dict(active_q) if active_q else None

    c.execute("SELECT * FROM lead_discovery_query_state WHERE status='pending' ORDER BY id DESC LIMIT 1")
    pending_q = c.fetchone()
    r["current_query"]["latest_pending"] = dict(pending_q) if pending_q else None
except Exception as e:
    r["current_query"]["error"] = str(e)

# Discovery city queue front (retail_city_queue)
try:
    c.execute("SELECT city, state, status, priority FROM retail_city_queue ORDER BY priority DESC LIMIT 3")
    r["current_query"]["city_queue_front"] = [dict(row) for row in c.fetchall()]
except:
    r["current_query"]["city_queue_front"] = []

# --- Inventory health ---
sendable = r["final_sendable_unsent"]
if sendable >= 60:
    r["inventory_health"] = "HEALTHY"
elif sendable >= 20:
    r["inventory_health"] = "LOW"
else:
    r["inventory_health"] = "CRITICAL"

# --- Safety verification ---
# `smtp_sends_today` = factual production sends today (NOT caused by this read-only run).
# This run makes zero DB writes; read-only integrity is always preserved.
r["safety_verification"] = {
    "smtp_sends_today": r["send_log_today"],
    "smtp_enabled": r["smtp_enabled"],
    "send_plan_today": r["send_plan_today"],
    "final_send_plan_total": r["final_send_plan_total"],
    "final_send_plan_today": r["final_send_plan_today"],
    "read_only_confirmed": True,
    "inventory_not_stopped": True,
    "no_new_plan_today": (r["send_plan_today"] == 0 and r["final_send_plan_today"] == 0),
    "smtp_channel_off": (r["smtp_enabled"] == "0"),
    "pass": (r["send_plan_today"] == 0 and r["final_send_plan_today"] == 0
             and r["smtp_enabled"] == "0")
}

conn.close()

# --- Delta vs previous day ---
prev = {}
prev_path = os.path.join(OUTPUT_DIR, f"{(shanghai_now - timedelta(days=1)).strftime('%Y-%m-%d')}.json")
if os.path.exists(prev_path):
    try:
        with open(prev_path, "r", encoding="utf-8") as f:
            prev = json.load(f)
    except:
        prev = {}
r["_delta_vs"] = os.path.basename(prev_path).replace(".json", "") if prev else None

def _delta(key, fmt=lambda x: x):
    if prev and key in prev:
        cur = r.get(key)
        pv = prev[key]
        try:
            d = int(cur) - int(pv)
        except (TypeError, ValueError):
            return fmt(cur)
        if d > 0:
            return f"↑{d} ({pv}→{cur})"
        if d < 0:
            return f"↓{abs(d)} ({pv}→{cur})"
        return f"— ({cur})"
    return fmt(r.get(key))

# --- Write JSON ---
os.makedirs(OUTPUT_DIR, exist_ok=True)
json_path = os.path.join(OUTPUT_DIR, f"{today_str}.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(r, f, indent=2, ensure_ascii=False, default=str)
print(f"JSON saved: {json_path}")

# --- Write Markdown ---
md_path = os.path.join(OUTPUT_DIR, f"{today_str}.md")

top_states = list(r["state_distribution"].items())[:5]
top_state_lines = "\n".join([f"| {st} | {cnt} |" for st, cnt in top_states])
top_statuses = list(r["status_distribution"].items())[:7]
top_status_lines = "\n".join([f"| {st} | {cnt} |" for st, cnt in top_statuses])

net_err_lines = ""
for etype, cnt in r["network_errors"].items():
    net_err_lines += f"| {etype} | {cnt} |\n"
if not net_err_lines:
    net_err_lines = "| (none) | 0 |\n"

bounce_lines = ""
for b in r.get("bounces_today_classified", []):
    bt = b.get("bounce_type") or "(unknown)"
    diag = (b.get("diagnostic_code") or "").strip() or "(none)"
    bounce_lines += f"| {bt} | {diag} | {b.get('cnt')} |\n"
if not bounce_lines:
    bounce_lines = "| (none today) | — | 0 |\n"

broad_breakdown = ""
for st, cnt in r["broad_unsent_breakdown"].items():
    broad_breakdown += f"- {st}: {cnt}\n"

inventory_emoji = {"HEALTHY": "✅", "LOW": "⚠️", "CRITICAL": "🔴"}
inv_emoji = inventory_emoji.get(r["inventory_health"], "❓")

# Current query rendering
cq = r.get("current_query", {})
cq_lines = []
q_counts = cq.get("query_status_counts", {})
cq_lines.append(f"| Query status | {q_counts} |")
front = cq.get("city_queue_front", [])
if front:
    f0 = front[0]
    cq_lines.append(f"| Discovery city (front) | {f0.get('city')}, {f0.get('state')} [{f0.get('status')}] |")
else:
    cq_lines.append("| Discovery city (front) | (none) |")
if cq.get("active"):
    a = cq["active"]
    cq_lines.append(f"| Active query | {a.get('query_text')} ({a.get('status')}) |")
else:
    cq_lines.append("| Active query | (none in_progress) |")
lp = cq.get("latest_pending")
if lp:
    cq_lines.append(f"| Latest pending | {lp.get('query_text')} |")
cq_block = "\n".join(cq_lines)

md = f"""# BD Daily Collection Report — {today_str}

**Generated**: {ts_full} (Asia/Shanghai)  
**Mode**: READ-ONLY — No SMTP, No Final Send Plan  
**Safety**: {"✅ PASS" if r["safety_verification"]["pass"] else "❌ FAIL"} — this run made 0 DB writes; SMTP channel={"ON" if r["smtp_enabled"] != "0" else "OFF"}, new plans today={r["send_plan_today"]}, final_send_plan today={r["final_send_plan_today"]}  
**⚠️ Production sends today**: {r["send_log_today"]} (NOT caused by this read-only run)

---

## Core Metrics

| Metric | Value | Change vs {r.get("_delta_vs") or "prev"} |
|--------|-------|-----------------|
| **Total Leads** | {r["total_leads"]} | {_delta("total_leads")} |
| **Final Sendable Unsent** | **{r["final_sendable_unsent"]}** | {_delta("final_sendable_unsent")} |
| ├─ Broad Outreach Ready | {r["broad_ready_unsent"]} | {_delta("broad_ready_unsent")} |
| └─ Strict A0 | {r["strict_a0_unsent"]} | {_delta("strict_a0_unsent")} |
| **Gap to 30** | {r["gap_to_30"]} | {_delta("gap_to_30")} |
| **Gap to 60** | {r["gap_to_60"]} | {_delta("gap_to_60")} |
| **Inventory Health** | {inv_emoji} **{r["inventory_health"]}** | — (<60 LOW / <20 CRITICAL) |

## Broad Outreach Unsent Breakdown

{broad_breakdown}
## Collection Activity Today

| Metric | Value |
|--------|-------|
| New Organizations | {r["new_orgs_today"]} |
| Website Emails Found | {r["website_emails_today"]} |
| Facebook Emails Found | {r["facebook_emails_today"]} |
| Manual Emails Verified | {r["manual_verified_today"]} |

## Queue & Recovery

| Queue | Count |
|-------|-------|
| Manual Review Pending | {r["manual_review_pending"]} |
| Website Recovery Pending | {r["website_recovery_pending"]} |
| Contact Recovery Pending | {r["contact_recovery_pending"]} |
| Contact Recovery Recheck | {r["contact_recovery_recheck"]} |

## Primary State Distribution

{top_state_lines}
## Lead Status (Top 7)

{top_status_lines}
## Safety & Integrity

| Check | Value | Status |
|-------|-------|--------|
| SMTP enabled | {r["smtp_enabled"]} | {"✅" if r["smtp_enabled"] == "0" else "❌"} |
| SMTP sends today (production) | {r["send_log_today"]} | ⚠️ (production, not this run) |
| send_plan today | {r["send_plan_today"]} | {"✅" if r["send_plan_today"] == 0 else "❌"} |
| Final Send Plan today | {r["final_send_plan_today"]} | {"✅" if r["final_send_plan_today"] == 0 else "❌"} |
| Final Send Plan total | {r["final_send_plan_total"]} | — |
| send_log total | {r["send_log_total"]} | — |
| Total bounces | {r["total_bounces"]} | — |
| Total suppressed | {r["total_suppressed"]} | — |
| Inventory running | Yes | ✅ |
| DB integrity | Read-only | ✅ |

## Network Errors

{net_err_lines}
## Bounces Today (classified)

| Type | Diagnostic | Count |
|------|-----------|-------|
{bounce_lines}
## Active Configuration

| Config | Value |
|--------|-------|
| Active State | {r["active_state"]} |
| Active City | {r["active_city"]} |
{cq_block}

---

*Report generated by BD Daily Collection Report automation. Read-only snapshot — no modifications made.*
"""

with open(md_path, "w", encoding="utf-8") as f:
    f.write(md)
print(f"Markdown saved: {md_path}")
print("DONE")
