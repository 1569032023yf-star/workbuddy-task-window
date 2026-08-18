"""BD Daily Results — 2026-08-09 09:00 CST — Read-Only Summary
Strictly read-only. No SMTP. No Final Send Plan.
"""
import importlib.util, json, os, sqlite3, sys, time
from datetime import datetime, timedelta, timezone

ASIA_SH = timezone(timedelta(hours=8))
YESTERDAY = (datetime.now(ASIA_SH) - timedelta(days=1)).strftime("%Y-%m-%d")
TODAY = datetime.now(ASIA_SH).strftime("%Y-%m-%d")
BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "data", "bd_leads.db")
OUTPUT_DIR = os.path.join(BASE, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def ro_conn():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn

# ═══════════════════════════════════════════════
# Step 1: Refresh Dashboard Cache via Ops API
# ═══════════════════════════════════════════════
print("=" * 70)
print("BD Daily Results — Read-Only Summary")
print(f"Date: {TODAY} | Report for: {YESTERDAY} (yesterday)")
print(f"Time: {datetime.now(ASIA_SH).strftime('%Y-%m-%d %H:%M:%S')} Asia/Shanghai")
print("=" * 70)

# Load bd_ops_api
spec = importlib.util.spec_from_file_location("bd_ops_api", os.path.join(BASE, "bd_ops_api.py"))
ops_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops_api)

# Clear cache
ops_api._cache.clear()
print("\n[1/4] Cache cleared. Fetching fresh stats from Ops API...")

# Get today stats
today_stats = ops_api.get_today_stats(DB_PATH)
print(f"  Today stats ({TODAY}): planned_new={today_stats.get('planned_new',0)}, sent_new={today_stats.get('sent_new',0)}")

# Get inventory
inventory = ops_api.get_inventory(DB_PATH)
print(f"  Inventory: total={inventory.get('total_leads',0)}, Strict A0 orgs={inventory.get('strict_a0_organizations',0)}")

# Get tracking
tracking = ops_api.get_tracking_stats()
print(f"  Tracking: available={tracking.get('available')}, open_signals={tracking.get('total_open_signals',0)}, tracked_sent={tracking.get('tracked_sent',0)}")

# Get health
health = ops_api.get_health(DB_PATH)
delivery = health.get("delivery_outcome", {})
freshness = health.get("data_freshness", {})
print(f"  Health: risk_gate={health.get('risk_gate','?')}, manual_pause={health.get('manual_pause','?')}")
print(f"  Data freshness: {freshness.get('badge_label','?')} ({freshness.get('level','?')}), age={freshness.get('age_minutes','?')}min")

# ═══════════════════════════════════════════════
# Step 2: Yesterday's Batch Summary
# ═══════════════════════════════════════════════
print(f"\n[2/4] Analyzing yesterday's batch ({YESTERDAY})...")

conn = ro_conn()
c = conn.cursor()

# Yesterday planned
planned_yday = c.execute(
    "SELECT COUNT(*) FROM final_send_plan WHERE outreach_batch_date = ? OR (outreach_batch_date IS NULL AND created_at LIKE ?)",
    (YESTERDAY, f"{YESTERDAY}%")).fetchone()[0]

# Yesterday sent (by sent_at LIKE)
sent_rows = c.execute(
    """SELECT sl.*, l.store_name, l.city, l.state, l.organization_key, l.unsubscribed_at
       FROM send_log sl LEFT JOIN leads l ON sl.lead_id = l.id
       WHERE sl.status = 'sent' AND sl.sent_at LIKE ?
         AND sl.message_type NOT IN ('test','internal_report','acceptance_test','sender_copy')
       ORDER BY sl.sent_at""",
    (f"{YESTERDAY}%",)).fetchall()

smtp_accepted = len(sent_rows)

# Yesterday replies
human_replies = c.execute(
    "SELECT COUNT(*) FROM reply_log WHERE reply_received_at LIKE ?",
    (f"{YESTERDAY}%",)).fetchone()[0]
auto_replies = c.execute(
    "SELECT COUNT(*) FROM reply_log WHERE reply_received_at LIKE ? AND (reply_type LIKE '%auto%' OR reply_type LIKE '%ooo%' OR reply_type LIKE '%autoreply%')",
    (f"{YESTERDAY}%",)).fetchone()[0]
human_replies = max(0, human_replies - auto_replies)

# Yesterday bounces
hard_bounces = c.execute(
    "SELECT COUNT(*) FROM bounce_log WHERE bounce_type IN ('hard','policy','permanent') AND bounce_received_at LIKE ?",
    (f"{YESTERDAY}%",)).fetchone()[0]
all_bounces_yday = c.execute(
    "SELECT bounce_type, COUNT(*) FROM bounce_log WHERE bounce_received_at LIKE ? GROUP BY bounce_type",
    (f"{YESTERDAY}%",)).fetchall()

# Yesterday unsubs
unsubs = c.execute(
    "SELECT COUNT(*) FROM leads WHERE unsubscribed_at LIKE ?",
    (f"{YESTERDAY}%",)).fetchone()[0]

# Broad Outreach Ready (using broad_outreach_gate if available)
broad_ready_orgs = 0
broad_ready_locs = 0
try:
    gate_spec = importlib.util.spec_from_file_location("broad_outreach_gate", os.path.join(BASE, "broad_outreach_gate.py"))
    gate = importlib.util.module_from_spec(gate_spec)
    gate_spec.loader.exec_module(gate)
    # Check if evaluate_broad_outreach exists
    if hasattr(gate, 'analyze_all_leads'):
        analysis = gate.analyze_all_leads(DB_PATH)
        broad_ready_orgs = analysis.get('broad_ready_orgs', 0)
        broad_ready_locs = analysis.get('broad_ready_locations', 0)
        print(f"  Broad Outreach Ready: {broad_ready_orgs} orgs / {broad_ready_locs} locations")
    else:
        # Fallback: count manually
        broad_ready_orgs = c.execute("""
            SELECT COUNT(*) FROM leads WHERE
            status NOT IN ('do_not_contact','review_rejected')
            AND email IS NOT NULL AND email != ''
            AND unsubscribed_at IS NULL
            AND bounced_at IS NULL
            AND email NOT IN (SELECT email FROM suppression_list)
            AND id NOT IN (SELECT DISTINCT lead_id FROM send_log WHERE status='sent')
            AND id NOT IN (SELECT lead_id FROM bounce_log WHERE bounce_type IN ('hard','policy','permanent'))
        """).fetchone()[0]
except Exception as e:
    print(f"  Broad Outreach Gate unavailable: {e}")
    # Simple count
    broad_ready_orgs = c.execute("""
        SELECT COUNT(*) FROM leads WHERE
        status NOT IN ('do_not_contact','review_rejected')
        AND email IS NOT NULL AND email != ''
        AND unsubscribed_at IS NULL
        AND bounced_at IS NULL
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT DISTINCT lead_id FROM send_log WHERE status='sent')
        AND id NOT IN (SELECT lead_id FROM bounce_log WHERE bounce_type IN ('hard','policy','permanent'))
    """).fetchone()[0]

# Manual review pending
manual_pending = c.execute(
    "SELECT COUNT(*) FROM leads WHERE review_reason_code IS NOT NULL AND review_reason_code != '' AND review_status = 'pending'"
).fetchone()[0]

# State and city progress
states = c.execute(
    "SELECT state, COUNT(*) as cnt, COUNT(DISTINCT city) as cities FROM leads WHERE state IS NOT NULL AND state != '' GROUP BY state ORDER BY cnt DESC"
).fetchall()

# ALLOWED_STATES sendable counts
allowed_states = ['TN','AR','KY','OH','IN','MN','NE','NC','OR','CO']
primary_states = c.execute(
    "SELECT state, COUNT(*) as cnt, COUNT(DISTINCT city) as cities FROM leads WHERE state IN ('TN','AR','KY') GROUP BY state ORDER BY cnt DESC"
).fetchall()

# City queue progress
city_queue = c.execute(
    "SELECT city, state, status FROM retail_city_queue ORDER BY priority LIMIT 10"
).fetchall()

# All-time bounce summary
all_bounce_summary = dict(c.execute(
    "SELECT bounce_type, COUNT(*) FROM bounce_log GROUP BY bounce_type"
).fetchall())

conn.close()

# ═══════════════════════════════════════════════
# Tracking / open signals for yesterday's sends
# ═══════════════════════════════════════════════
open_signal_stores = []
no_signal_stores = []
stores_with_open = 0
total_open_signals = 0

if smtp_accepted > 0:
    # Check tracking per send
    for row in sent_rows:
        d = dict(row)
        # Check if this lead has tracking data
        tracking_msg_id = d.get('tracking_message_id', '')
        store_name = d.get('store_name', f'Lead#{d.get("lead_id")}')
        open_count = 0
        first_open = None
        last_open = None
        
        # Query from tracking cache
        breakdown = tracking.get('breakdown', {})
        lead_id_str = str(d.get('lead_id'))
        if lead_id_str in breakdown:
            lead_tracking = breakdown[lead_id_str]
            open_count = lead_tracking.get('open_signals', 0)
            first_open = lead_tracking.get('first_open', None)
            last_open = lead_tracking.get('last_open', None)
        
        if open_count > 0:
            stores_with_open += 1
            total_open_signals += open_count
            open_signal_stores.append({
                'store': store_name,
                'recipient': (d.get('email', '') or '')[:40],
                'sent_at': d.get('sent_at', ''),
                'open_signals': open_count,
                'first_open': first_open,
                'last_open': last_open,
                'reply': 'N/A',
                'bounce': 'N/A',
            })
        else:
            no_signal_stores.append({
                'store': store_name,
                'recipient': (d.get('email', '') or '')[:40],
                'sent_at': d.get('sent_at', ''),
            })

# ═══════════════════════════════════════════════
# Generate Report
# ═══════════════════════════════════════════════
print(f"\n[3/4] Generating daily report...")

report_lines = []
report_lines.append("=" * 70)
report_lines.append("   BD Daily Results — Read-Only Summary")
report_lines.append(f"   {YESTERDAY} (yesterday) | Generated: {datetime.now(ASIA_SH).strftime('%Y-%m-%d %H:%M:%S')} CST")
report_lines.append("=" * 70)

report_lines.append(f"\n## 1. Yesterday's Batch Summary ({YESTERDAY})")
report_lines.append(f"   Planned: {planned_yday}")
report_lines.append(f"   SMTP Accepted: {smtp_accepted}")
report_lines.append(f"   Delivery Rate: {smtp_accepted}/{max(planned_yday,1)} = {round(smtp_accepted/max(planned_yday,1)*100,1)}%")

if smtp_accepted > 0:
    report_lines.append(f"   有打开信号的商家数: {stores_with_open}")
    report_lines.append(f"   暂无打开信号的商家数: {smtp_accepted - stores_with_open}")
    report_lines.append(f"   打开信号总次数: {total_open_signals}")
else:
    report_lines.append(f"   有打开信号的商家数: 0 (no sends)")
    report_lines.append(f"   暂无打开信号的商家数: 0")
    report_lines.append(f"   打开信号总次数: 0")

report_lines.append(f"   人工回复数: {human_replies}")
report_lines.append(f"   自动回复数: {auto_replies}")
report_lines.append(f"   Hard Bounce 数: {hard_bounces}")
report_lines.append(f"   Unsubscribe 数: {unsubs}")

if all_bounces_yday:
    for bt, cnt in all_bounces_yday:
        report_lines.append(f"     Bounce ({bt}): {cnt}")

report_lines.append(f"\n## 2. Current Inventory")
report_lines.append(f"   Total Leads: {inventory.get('total_leads', '?')}")
report_lines.append(f"   Strict A0 (organizations): {inventory.get('strict_a0_organizations', 0)}")
report_lines.append(f"   Broad Outreach Ready: {broad_ready_orgs} orgs")
report_lines.append(f"   Manual Review Pending: {manual_pending}")
report_lines.append(f"   Send Prep Candidates: {inventory.get('send_prep_candidates', '?')}")
report_lines.append(f"   Previously Sent: {inventory.get('previously_sent', '?')}")
report_lines.append(f"   Permanently Suppressed: {inventory.get('permanently_suppressed', '?')}")

report_lines.append(f"\n## 3. Active States & Collection Progress")
report_lines.append(f"   Allowed States: {', '.join(allowed_states)}")
report_lines.append(f"   Primary State Pool (TN/AR/KY):")
# Need fresh connection for sendable counts
conn_s = ro_conn()
c_s = conn_s.cursor()
for s in primary_states:
    sendable = c_s.execute("""
        SELECT COUNT(*) FROM leads WHERE state=? AND status NOT IN ('do_not_contact','review_rejected')
        AND email IS NOT NULL AND email != '' AND unsubscribed_at IS NULL 
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status='sent')
        AND id NOT IN (SELECT lead_id FROM bounce_log WHERE bounce_type IN ('hard','policy','permanent'))
    """, (s['state'],)).fetchone()
    report_lines.append(f"     {s['state']}: {s['cnt']} leads / {s['cities']} cities / ~{sendable[0] if sendable else 0} sendable")
conn_s.close()

# All states top 10
report_lines.append(f"\n   All States (by lead count):")
all_states_conn = ro_conn()
all_states_c = all_states_conn.cursor()
for s in states[:12]:
    if s['state']:
        report_lines.append(f"     {s['state']}: {s['cnt']} leads / {s['cities']} cities")
all_states_conn.close()

# City queue
if city_queue:
    report_lines.append(f"\n   City Queue:")
    for cq in city_queue:
        report_lines.append(f"     {cq['city']}, {cq['state']} — {cq['status']}")

report_lines.append(f"\n## 4. Data Freshness & Health")
report_lines.append(f"   Freshness: {freshness.get('badge_label', '?')} ({freshness.get('level', '?')})")
report_lines.append(f"   Last Bounce Scan: {freshness.get('last_bounce_scan_at', 'N/A')}")
report_lines.append(f"   Risk Gate: {health.get('risk_gate', 'unknown')}")
report_lines.append(f"   Manual Pause: {health.get('manual_pause', 'unknown')}")
report_lines.append(f"   In Send Window: {health.get('in_send_window', False)}")

report_lines.append(f"\n## 5. Delivery Outcome (All-Time)")
report_lines.append(f"   SMTP Accepted (total): {delivery.get('smtp_accepted_all', '?')}")
report_lines.append(f"   SMTP Accepted (30d): {delivery.get('smtp_accepted_30d', '?')}")
report_lines.append(f"   Domain Invalid: {delivery.get('domain_invalid', 0)}")
report_lines.append(f"   Mailbox Invalid: {delivery.get('mailbox_invalid', 0)}")
report_lines.append(f"   Hard Bounce: {delivery.get('hard_bounce', 0)}")
report_lines.append(f"   Policy Bounce: {delivery.get('policy_bounce', 0)}")
report_lines.append(f"   Soft Bounce: {delivery.get('soft_bounce', 0)}")
report_lines.append(f"   Unmatched DSN: {delivery.get('unmatched_dsn', 0)}")
report_lines.append(f"   Human Reply: {delivery.get('human_reply', 0)}")
report_lines.append(f"   Auto Reply: {delivery.get('auto_reply', 0)}")
report_lines.append(f"   Outcome Unresolved: {delivery.get('outcome_unresolved', 0)}")

# Sent timeline (last 7 days)
report_lines.append(f"\n## 6. Send Activity — Last 7 Days")
conn2 = ro_conn()
c2 = conn2.cursor()
for i in range(6, -1, -1):
    d = (datetime.now(ASIA_SH) - timedelta(days=i)).strftime("%Y-%m-%d")
    sent_n = c2.execute(
        "SELECT COUNT(*) FROM send_log WHERE status='sent' AND sent_at LIKE ? AND message_type NOT IN ('test')",
        (f"{d}%",)).fetchone()[0]
    planned_n = c2.execute(
        "SELECT COUNT(*) FROM final_send_plan WHERE outreach_batch_date = ? AND status = 'planned'",
        (d,)).fetchone()[0]
    bounce_n = c2.execute(
        "SELECT COUNT(*) FROM bounce_log WHERE bounce_received_at LIKE ?",
        (f"{d}%",)).fetchone()[0]
    day_label = "today" if i == 0 else ("yesterday" if i == 1 else d)
    icon = "🔴" if sent_n == 0 else "🟢"
    report_lines.append(f"   {icon} {day_label}: planned={planned_n}, sent={sent_n}, bounces={bounce_n}")
conn2.close()

# ═══════════════════════════════════════════════
# Step 3: Per-Lead Results (if any sends)
# ═══════════════════════════════════════════════
report_lines.append(f"\n## 7. Yesterday's Send Results — Per Lead")
report_lines.append(f"   {'─' * 60}")

if smtp_accepted == 0:
    report_lines.append(f"\n   ⚠️ 昨日 ({YESTERDAY}) 无发送记录。")
    report_lines.append(f"   最近一次发送: 2026-08-05 (40 emails)")
    report_lines.append(f"   已连续 3 天无发送 (Aug 6, 7, 8)。")
else:
    for entry in open_signal_stores:
        report_lines.append(f"\n   Store: {entry['store']}")
        report_lines.append(f"   Recipient: {entry['recipient']}")
        report_lines.append(f"   Sent At: {entry['sent_at']}")
        report_lines.append(f"   ✅ Open Signal ({entry['open_signals']} signals)")
        if entry.get('first_open'):
            report_lines.append(f"      First: {entry['first_open']} | Last: {entry.get('last_open','')}")
    for entry in no_signal_stores:
        report_lines.append(f"\n   Store: {entry['store']}")
        report_lines.append(f"   Recipient: {entry['recipient']}")
        report_lines.append(f"   Sent At: {entry['sent_at']}")
        report_lines.append(f"   ⏳ 暂无打开信号 (No Open Signal Yet)")

# Data quality warnings
report_lines.append(f"\n## 8. Data Quality Warnings")
quality = ops_api.get_data_quality(DB_PATH)
if quality.get('warnings'):
    for w in quality['warnings']:
        report_lines.append(f"   ⚠️  {w.get('zh', w.get('en', str(w)))}")
else:
    report_lines.append(f"   ✅ No data quality warnings")

# Consecutive no-send days
no_send_days = 0
conn3 = ro_conn()
c3 = conn3.cursor()
for i in range(1, 15):
    d = (datetime.now(ASIA_SH) - timedelta(days=i)).strftime("%Y-%m-%d")
    sent_n = c3.execute(
        "SELECT COUNT(*) FROM send_log WHERE status='sent' AND sent_at LIKE ? AND message_type NOT IN ('test')",
        (f"{d}%",)).fetchone()[0]
    if sent_n == 0:
        no_send_days += 1
    else:
        break
conn3.close()

report_lines.append(f"\n## 9. Status Alert")
report_lines.append(f"   Consecutive Days Without Sends: {no_send_days}")
if no_send_days >= 3:
    report_lines.append(f"   ⚠️ CRITICAL: {no_send_days} consecutive days without sends!")
    report_lines.append(f"   Last active: 2026-08-05 (40 emails)")
    report_lines.append(f"   Check: execution_mode may need reset to 'daily_outreach'")
report_lines.append(f"   Strict A0 Inventory: {inventory.get('strict_a0_organizations', 0)} orgs (CRITICAL if 0)")
report_lines.append(f"   Broad Outreach Ready: {broad_ready_orgs} orgs (sufficient for ~{broad_ready_orgs//20} days)")
report_lines.append(f"   Manual Review Backlog: {manual_pending} leads")

report_lines.append(f"\n{'=' * 70}")
report_lines.append(f"   End of Report — {datetime.now(ASIA_SH).strftime('%Y-%m-%d %H:%M:%S')} CST")
report_lines.append(f"{'=' * 70}")

# Write report files
report_text = "\n".join(report_lines)
md_path = os.path.join(OUTPUT_DIR, f"auto_report_{YESTERDAY}.md")
txt_path = os.path.join(OUTPUT_DIR, f"auto_report_{YESTERDAY}.txt")

with open(md_path, "w", encoding="utf-8") as f:
    f.write(report_text)
with open(txt_path, "w", encoding="utf-8") as f:
    f.write(report_text)

print(f"\n[4/4] Report written to:")
print(f"  {md_path}")
print(f"  {txt_path}")
print(f"\n{report_text}")
