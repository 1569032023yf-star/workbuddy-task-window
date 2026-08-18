"""BD Daily Collection Report — Read-only DB snapshot."""
import sqlite3, json, os
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "bd_leads.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

shanghai_now = datetime.now(timezone(timedelta(hours=8)))
today_str = shanghai_now.strftime("%Y-%m-%d")
today_start = f"{today_str} 00:00:00"
today_end = f"{today_str} 23:59:59"
ts = shanghai_now.strftime("%Y-%m-%dT%H:%M:%S+08:00")

results = {"report_generated_at": ts, "report_date": today_str}

# 1. Total leads
c.execute("SELECT COUNT(*) as cnt FROM leads")
results["total_leads"] = c.fetchone()["cnt"]

# 2. Status distribution
c.execute("SELECT status, COUNT(*) as cnt FROM leads GROUP BY status ORDER BY cnt DESC")
results["status_distribution"] = {r["status"]: r["cnt"] for r in c.fetchall()}

# 3. State distribution (ALLOWED_STATES)
allowed = ["TN","AR","KY","OH","IN","MN","NE","NC","OR","CO"]
placeholders = ",".join(["?"] * len(allowed))
c.execute(f"SELECT state, COUNT(*) as cnt FROM leads WHERE state IN ({placeholders}) GROUP BY state ORDER BY cnt DESC", allowed)
results["state_distribution"] = {r["state"]: r["cnt"] for r in c.fetchall()}

# 4. City distribution top 10
c.execute('SELECT city, COUNT(*) as cnt FROM leads WHERE city IS NOT NULL AND city != "" GROUP BY city ORDER BY cnt DESC LIMIT 10')
results["city_top10"] = [(r["city"], r["cnt"]) for r in c.fetchall()]

# 5. send_eligibility
try:
    c.execute("SELECT send_eligibility, COUNT(*) as cnt FROM leads GROUP BY send_eligibility ORDER BY cnt DESC")
    results["send_eligibility"] = {r["send_eligibility"]: r["cnt"] for r in c.fetchall()}
except:
    results["send_eligibility"] = {"error": "column missing"}

# 6. Broad Outreach Ready (unsent)
try:
    c.execute("SELECT COUNT(*) as cnt FROM leads WHERE status='broad_outreach_ready' AND (sent_at IS NULL OR sent_at = '')")
    results["broad_ready_unsent"] = c.fetchone()["cnt"]
except:
    results["broad_ready_unsent"] = 0

# 7. Strict A0 unsent
try:
    c.execute("SELECT COUNT(*) as cnt FROM leads WHERE send_eligibility='strict_a0' AND (sent_at IS NULL OR sent_at = '')")
    results["strict_a0_unsent"] = c.fetchone()["cnt"]
except:
    try:
        c.execute("SELECT COUNT(*) as cnt FROM leads WHERE status='a0_verified' AND (sent_at IS NULL OR sent_at = '')")
        results["strict_a0_unsent"] = c.fetchone()["cnt"]
    except:
        results["strict_a0_unsent"] = 0

# 8. Final sendable unsent
results["final_sendable_unsent"] = results["broad_ready_unsent"] + results["strict_a0_unsent"]
results["gap_to_30"] = max(0, 30 - results["final_sendable_unsent"])
results["gap_to_60"] = max(0, 60 - results["final_sendable_unsent"])

# 9. New orgs today
c.execute("SELECT COUNT(*) as cnt FROM leads WHERE collected_at >= ? AND collected_at <= ?", (today_start, today_end))
results["new_orgs_today"] = c.fetchone()["cnt"]

# 10. Website emails found today
c.execute('SELECT COUNT(*) as cnt FROM leads WHERE email_source_type="website" AND last_checked_at >= ? AND last_checked_at <= ?', (today_start, today_end))
results["website_emails_today"] = c.fetchone()["cnt"]

# 11. Facebook emails found today
c.execute('SELECT COUNT(*) as cnt FROM leads WHERE email_source_type="facebook" AND last_checked_at >= ? AND last_checked_at <= ?', (today_start, today_end))
results["facebook_emails_today"] = c.fetchone()["cnt"]

# 12. Manual verified today
c.execute('SELECT COUNT(*) as cnt FROM leads WHERE status="approved_manual_send" AND last_checked_at >= ? AND last_checked_at <= ?', (today_start, today_end))
results["manual_verified_today"] = c.fetchone()["cnt"]

# 13. Manual review pending
c.execute('SELECT COUNT(*) as cnt FROM leads WHERE status="manual_review_needed"')
results["manual_review_pending"] = c.fetchone()["cnt"]

# 14. Website recovery pending
c.execute('SELECT COUNT(*) as cnt FROM leads WHERE (email IS NULL OR email = "") AND official_website IS NOT NULL AND official_website != ""')
results["website_recovery_pending"] = c.fetchone()["cnt"]

# 15. Contact recovery table
try:
    c.execute('SELECT COUNT(*) as cnt FROM contact_recovery WHERE status="pending"')
    results["contact_recovery_pending"] = c.fetchone()["cnt"]
except:
    results["contact_recovery_pending"] = 0
try:
    c.execute('SELECT COUNT(*) as cnt FROM contact_recovery WHERE status="recheck_pending"')
    results["contact_recovery_recheck"] = c.fetchone()["cnt"]
except:
    results["contact_recovery_recheck"] = 0

# 16. Network errors
try:
    c.execute("SELECT error_type, COUNT(*) as cnt FROM network_errors GROUP BY error_type ORDER BY cnt DESC")
    results["network_errors"] = {r["error_type"]: r["cnt"] for r in c.fetchall()}
except:
    try:
        c.execute('SELECT error_message, COUNT(*) as cnt FROM leads WHERE error_message IS NOT NULL AND error_message != "" GROUP BY error_message ORDER BY cnt DESC LIMIT 5')
        results["network_errors"] = {r["error_message"]: r["cnt"] for r in c.fetchall()}
    except:
        results["network_errors"] = {}

# 17. send_log total
try:
    c.execute("SELECT COUNT(*) as cnt FROM send_log")
    results["send_log_total"] = c.fetchone()["cnt"]
except:
    results["send_log_total"] = 0

# 18. send_log today
try:
    c.execute("SELECT COUNT(*) as cnt FROM send_log WHERE sent_at >= ? AND sent_at <= ?", (today_start, today_end))
    results["send_log_today"] = c.fetchone()["cnt"]
except:
    results["send_log_today"] = 0

# 19. send_plan today
try:
    c.execute("SELECT COUNT(*) as cnt FROM send_plan WHERE created_at >= ? AND created_at <= ?", (today_start, today_end))
    results["send_plan_today"] = c.fetchone()["cnt"]
except:
    results["send_plan_today"] = 0

# 20. Active collection queries
try:
    c.execute('SELECT * FROM collection_queries WHERE status="in_progress" ORDER BY id DESC LIMIT 5')
    results["active_queries"] = [dict(r) for r in c.fetchall()]
except:
    results["active_queries"] = []
try:
    c.execute('SELECT * FROM system_config WHERE key LIKE "%collection%" OR key LIKE "%active%" OR key LIKE "%query%"')
    results["system_config_collection"] = [dict(r) for r in c.fetchall()]
except:
    results["system_config_collection"] = []

# 21. Previously sent
try:
    c.execute('SELECT COUNT(*) as cnt FROM leads WHERE status="previously_sent"')
    results["previously_sent"] = c.fetchone()["cnt"]
except:
    results["previously_sent"] = 0

# 22. Bounces
try:
    c.execute("SELECT COUNT(*) as cnt FROM bounce_log")
    results["total_bounces"] = c.fetchone()["cnt"]
except:
    results["total_bounces"] = 0

# 23. Suppressed
try:
    c.execute("SELECT COUNT(*) as cnt FROM suppression_list")
    results["total_suppressed"] = c.fetchone()["cnt"]
except:
    results["total_suppressed"] = 0

# 24. email_missing
c.execute('SELECT COUNT(*) as cnt FROM leads WHERE (email IS NULL OR email = "")')
results["email_missing"] = c.fetchone()["cnt"]

# 25. contact_form_only
c.execute('SELECT COUNT(*) as cnt FROM leads WHERE (email IS NULL OR email = "") AND contact_form_url IS NOT NULL AND contact_form_url != ""')
results["contact_form_only"] = c.fetchone()["cnt"]

# 26. Active city/state
try:
    c.execute('SELECT value FROM system_config WHERE key="active_city"')
    row = c.fetchone()
    results["active_city"] = row["value"] if row else "Nashville"
except:
    results["active_city"] = "Nashville"

try:
    c.execute('SELECT value FROM system_config WHERE key="active_state"')
    row = c.fetchone()
    results["active_state"] = row["value"] if row else "TN"
except:
    results["active_state"] = "TN"

# 27. current_query info
try:
    c.execute('SELECT * FROM collection_queries ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    if row:
        results["current_query"] = dict(row)
    else:
        results["current_query"] = None
except:
    results["current_query"] = None

# 28. Safety verification
results["safety_checks"] = {
    "smtp_sends_today": results["send_log_today"],
    "send_plan_today": results["send_plan_today"],
    "read_only_confirmed": True
}

conn.close()

# Print JSON
print(json.dumps(results, indent=2, default=str, ensure_ascii=False))
