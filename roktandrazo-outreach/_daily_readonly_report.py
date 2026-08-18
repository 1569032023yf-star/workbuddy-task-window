"""
BD Daily Results — Read-Only Summary (2026-08-08 auto)
No SMTP. No Final Send Plan. Strictly read-only.
"""
import sqlite3, json, os, sys
from datetime import datetime, timezone, timedelta

ASIA_SH = timezone(timedelta(hours=8))
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "bd_leads.db")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

YESTERDAY = (datetime.now(ASIA_SH) - timedelta(days=1)).strftime("%Y-%m-%d")
TODAY = datetime.now(ASIA_SH).strftime("%Y-%m-%d")
NOW_STR = datetime.now(ASIA_SH).strftime("%Y-%m-%d %H:%M:%S")

print(f"=== BD Daily Results — Read-Only Summary ===")
print(f"Generated: {NOW_STR} Asia/Shanghai")
print(f"Yesterday: {YESTERDAY}")
print()

# ═══════════════════════════════════════════════
# 1. Clear Ops API cache & refresh stats
# ═══════════════════════════════════════════════
print("--- 1. Refreshing Dashboard Cache ---")
sys.path.insert(0, os.path.dirname(__file__))
import bd_ops_api
bd_ops_api._cache.clear()
print("  Cache cleared.")

conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

# ═══════════════════════════════════════════════
# 2. Yesterday's batch from send_log
# ═══════════════════════════════════════════════
print(f"\n--- 2. Yesterday's Batch: {YESTERDAY} ---")

# Count sends by sent_at LIKE
sent_rows = conn.execute("""
    SELECT sl.*, l.store_name, l.city, l.state, l.email_type,
           COALESCE(NULLIF(l.organization_key,''),'org_'||sl.lead_id) as org_key
    FROM send_log sl
    LEFT JOIN leads l ON sl.lead_id = l.id
    WHERE sl.status = 'sent'
      AND sl.sent_at LIKE ?
      AND sl.message_type NOT IN ('test','internal_report','acceptance_test','sender_copy')
    ORDER BY sl.sent_at
""", (f"{YESTERDAY}%",)).fetchall()

planned_count = conn.execute("""
    SELECT COUNT(*) FROM final_send_plan
    WHERE outreach_batch_date = ? AND status = 'planned'
""", (YESTERDAY,)).fetchone()[0]

# Also try fallback: outreach_batch_date
sent_by_batch = conn.execute("""
    SELECT COUNT(*) FROM send_log
    WHERE status = 'sent' AND outreach_batch_date = ?
      AND message_type NOT IN ('test','internal_report','acceptance_test','sender_copy')
""", (YESTERDAY,)).fetchone()[0]

print(f"  Planned: {planned_count}")
print(f"  SMTP Accepted (sent_at LIKE): {len(sent_rows)}")
print(f"  SMTP Accepted (outreach_batch_date): {sent_by_batch}")

# Use the larger count
smtp_accepted = max(len(sent_rows), sent_by_batch)

# If sent_rows empty but sent_by_batch has data, re-query by batch_date
if len(sent_rows) == 0 and sent_by_batch > 0:
    sent_rows = conn.execute("""
        SELECT sl.*, l.store_name, l.city, l.state, l.email_type,
               COALESCE(NULLIF(l.organization_key,''),'org_'||sl.lead_id) as org_key
        FROM send_log sl
        LEFT JOIN leads l ON sl.lead_id = l.id
        WHERE sl.status = 'sent'
          AND sl.outreach_batch_date = ?
          AND sl.message_type NOT IN ('test','internal_report','acceptance_test','sender_copy')
        ORDER BY sl.sent_at
    """, (YESTERDAY,)).fetchall()

# ═══════════════════════════════════════════════
# 3. Tracking data — poller cache
# ═══════════════════════════════════════════════
print(f"\n--- 3. Tracking Data ---")
tracking_data = {"available": False, "messages_with_open": 0, "total_open_signals": 0, "breakdown": {}}

# Try poller cache
try:
    cache_path = os.path.join(OUTPUT_DIR, "bd_ops_poller_tracking_cache.json")
    with open(cache_path, "r") as f:
        td = json.load(f)
    if td.get("available"):
        tracking_data = td
        print(f"  Source: poller_cache (synced {td.get('synced_at','?')})")
    else:
        print(f"  Poller cache unavailable — checking D1 directly...")
except Exception:
    print(f"  Poller cache not found — checking D1 directly...")

# Fallback: check D1 via worker API
if not tracking_data.get("available"):
    try:
        import urllib.request
        token = os.environ.get("DASHBOARD_API_KEY", "")
        sql = "SELECT COUNT(DISTINCT message_id) as msgs, COUNT(*) as signals FROM email_tracking_events WHERE event_type = 'open'"
        req = urllib.request.Request(
            "https://roktandrazo-email-tracker.1569032023yf.workers.dev/internal/query",
            data=json.dumps({"sql": sql}).encode(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        if data and data.get("results"):
            tracking_data["available"] = True
            tracking_data["total_open_signals"] = int(data["results"][0].get("signals", 0))
            tracking_data["messages_with_open"] = int(data["results"][0].get("msgs", 0))
            tracking_data["source"] = "D1_direct"
            print(f"  Source: D1 direct (messages with open: {tracking_data['messages_with_open']}, signals: {tracking_data['total_open_signals']})")
    except Exception as e:
        print(f"  D1 query failed: {e}")

# Check tracking_message_id linkage for yesterday's sends
lead_ids = [r["lead_id"] for r in sent_rows if r["lead_id"]]
tracking_ids = conn.execute(f"""
    SELECT lead_id, tracking_message_id FROM leads
    WHERE id IN ({','.join('?' for _ in lead_ids)})
""", lead_ids).fetchall() if lead_ids else []

tracking_map = {r["lead_id"]: r["tracking_message_id"] for r in tracking_ids if r["tracking_message_id"]}
print(f"  Leads with tracking_message_id: {len(tracking_map)}/{len(lead_ids)}")

# ═══════════════════════════════════════════════
# 4. Open signals per send (check D1 per tracking_message_id)
# ═══════════════════════════════════════════════
print(f"\n--- 4. Open Signal Analysis ---")
open_data = {}  # lead_id -> {has_open, first_open, last_open, count}

# Try per-message D1 query
if tracking_data.get("available") and tracking_map:
    try:
        tracking_ids_str = "','".join(tracking_map.values())
        sql = f"""
            SELECT message_id, MIN(event_at) as first_open, MAX(event_at) as last_open, COUNT(*) as opens
            FROM email_tracking_events
            WHERE event_type = 'open' AND message_id IN ('{tracking_ids_str}')
            GROUP BY message_id
        """
        import urllib.request
        token = os.environ.get("DASHBOARD_API_KEY", "")
        req = urllib.request.Request(
            "https://roktandrazo-email-tracker.1569032023yf.workers.dev/internal/query",
            data=json.dumps({"sql": sql}).encode(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        if data and data.get("results"):
            for r in data["results"]:
                msg_id = r.get("message_id", "")
                # Reverse map to lead_id
                for lid, mid in tracking_map.items():
                    if mid == msg_id:
                        open_data[lid] = {
                            "has_open": True if r.get("opens", 0) > 0 else False,
                            "first_open": r.get("first_open", ""),
                            "last_open": r.get("last_open", ""),
                            "count": r.get("opens", 0),
                        }
                        break
        print(f"  D1 tracked messages with opens: {sum(1 for v in open_data.values() if v['has_open'])}")
    except Exception as e:
        print(f"  D1 per-message query failed: {e}")

# ═══════════════════════════════════════════════
# 5. Replies & Bounces for yesterday
# ═══════════════════════════════════════════════
print(f"\n--- 5. Replies & Bounces ---")

human_replies = conn.execute("""
    SELECT COUNT(*) FROM reply_log
    WHERE reply_received_at LIKE ? AND (reply_type NOT LIKE '%auto%' AND reply_type NOT LIKE '%ooo%' AND reply_type NOT LIKE '%autoreply%' AND reply_type NOT LIKE '%notification%' OR reply_type IS NULL)
""", (f"{YESTERDAY}%",)).fetchone()[0]

auto_replies = conn.execute("""
    SELECT COUNT(*) FROM reply_log
    WHERE reply_received_at LIKE ? AND (reply_type LIKE '%auto%' OR reply_type LIKE '%ooo%' OR reply_type LIKE '%autoreply%' OR reply_type LIKE '%notification%')
""", (f"{YESTERDAY}%",)).fetchone()[0]

hard_bounces = conn.execute("""
    SELECT COUNT(*) FROM bounce_log
    WHERE bounce_type IN ('hard','policy','permanent') AND bounce_received_at LIKE ?
""", (f"{YESTERDAY}%",)).fetchone()[0]

soft_bounces = conn.execute("""
    SELECT COUNT(*) FROM bounce_log
    WHERE bounce_type IN ('soft','transient') AND bounce_received_at LIKE ?
""", (f"{YESTERDAY}%",)).fetchone()[0]

unsubs = conn.execute("""
    SELECT COUNT(*) FROM leads WHERE unsubscribed_at LIKE ?
""", (f"{YESTERDAY}%",)).fetchone()[0]

print(f"  Human replies: {human_replies}")
print(f"  Auto replies: {auto_replies}")
print(f"  Hard bounces: {hard_bounces}")
print(f"  Soft bounces: {soft_bounces}")
print(f"  Unsubscribes: {unsubs}")

# ═══════════════════════════════════════════════
# 6. Inventory
# ═══════════════════════════════════════════════
print(f"\n--- 6. Current Inventory ---")

total_leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]

# Broad Outreach Ready count using module
try:
    from broad_outreach_gate import analyze_all_leads
    broad_conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    broad_result = analyze_all_leads(broad_conn)
    broad_ready = broad_result.get("broad_org_opportunities", 0)  # org-level count
    broad_locations = broad_result.get("broad_ready_locations", [])
    broad_ready_locs = len(broad_locations) if isinstance(broad_locations, list) else 0
    broad_high = broad_result.get("contact_role_uncertain_unblocked", 0)
    broad_conn.close()
except Exception as e:
    print(f"  broad_outreach_gate error: {e}")
    import traceback; traceback.print_exc()
    broad_ready = "N/A"
    broad_high = "N/A"

strict_a0 = conn.execute("""
    SELECT COUNT(*) FROM leads WHERE
    status='new' AND confidence_score='A' AND auto_sendable=1
    AND email_verified_on_official_site=1 AND email IS NOT NULL AND email != ''
    AND email NOT IN (SELECT email FROM suppression_list)
    AND id NOT IN (SELECT lead_id FROM send_log WHERE status='sent')
    AND id NOT IN (SELECT lead_id FROM bounce_log WHERE bounce_type IN ('hard','policy','permanent'))
""").fetchone()[0]

manual_pending = conn.execute("""
    SELECT COUNT(*) FROM leads
    WHERE review_reason_code IS NOT NULL AND review_reason_code != ''
    AND review_status = 'pending'
""").fetchone()[0]

prev_sent = conn.execute("""
    SELECT COUNT(DISTINCT lead_id) FROM send_log WHERE status='sent'
""").fetchone()[0]

suppressed = conn.execute("""
    SELECT COUNT(*) FROM leads WHERE
    email IN (SELECT email FROM suppression_list)
    OR status='do_not_contact' OR unsubscribed_at IS NOT NULL
""").fetchone()[0]

print(f"  Total leads: {total_leads}")
print(f"  Broad Outreach Ready: {broad_ready} orgs / {broad_ready_locs} locations")
print(f"  Broad High Priority: {broad_high}")
print(f"  Strict A0: {strict_a0}")
print(f"  Manual review pending: {manual_pending}")
print(f"  Previously sent: {prev_sent}")
print(f"  Suppressed: {suppressed}")

# 7. Active states/cities
print(f"\n--- 7. Active States & Collection Progress ---")
state_stats = conn.execute("""
    SELECT state, COUNT(*) as cnt, COUNT(DISTINCT city) as cities
    FROM leads
    WHERE state IN ('TN','AR','KY','OH','IN','MN','NE','NC','OR','CO')
    GROUP BY state ORDER BY cnt DESC
""").fetchall()

for r in state_stats:
    state = r["state"]
    sendable = conn.execute("""
        SELECT COUNT(*) FROM leads WHERE state = ?
        AND id NOT IN (SELECT DISTINCT lead_id FROM send_log WHERE status='sent')
        AND status NOT IN ('do_not_contact','review_rejected')
        AND email IS NOT NULL AND email != ''
        AND email NOT IN (SELECT email FROM suppression_list)
    """, (state,)).fetchone()[0]
    print(f"  {state}: {r['cnt']} leads in {r['cities']} cities ({sendable} unsent/sendable)")

# ═══════════════════════════════════════════════
# 8. Per-send detail
# ═══════════════════════════════════════════════
print(f"\n{'='*80}")
print(f"  YESTERDAY'S SEND RESULTS — {YESTERDAY}")
print(f"{'='*80}")

opens_count = 0
no_open_count = 0

for idx, r in enumerate(sent_rows, 1):
    lid = r["lead_id"]
    store = r.get("store_name", f"Lead #{lid}")
    email = r.get("email", "")[:40]
    sent_at = r.get("sent_at", "")
    city = r.get("city", "")
    state = r.get("state", "")
    org = r.get("org_key", "")

    o = open_data.get(lid, {})
    has_open = o.get("has_open", False)
    first_open = o.get("first_open", "")[:19] if o.get("first_open") else ""
    last_open = o.get("last_open", "")[:19] if o.get("last_open") else ""
    open_count = o.get("count", 0)

    if has_open:
        opens_count += 1
        signal = "Open Signal"
    else:
        no_open_count += 1
        signal = "No Open Signal Yet"

    # Check reply
    reply = conn.execute("""
        SELECT COUNT(*) FROM reply_log WHERE lead_id = ? AND reply_received_at LIKE ?
    """, (lid, f"{YESTERDAY}%")).fetchone()[0]

    # Check bounce
    bounce = conn.execute("""
        SELECT COUNT(*) FROM bounce_log WHERE lead_id = ? AND bounce_received_at LIKE ?
    """, (lid, f"{YESTERDAY}%")).fetchone()[0]

    print(f"\n#{idx}. {store}")
    print(f"   Org: {org}")
    print(f"   Recipient: {email}")
    print(f"   Sent At: {sent_at}")
    print(f"   Location: {city}, {state}")
    print(f"   {signal}")
    if has_open:
        print(f"   First Open Signal: {first_open}")
        print(f"   Last Open Signal: {last_open}")
        print(f"   Open Signals: {open_count}")
    if reply > 0:
        print(f"   Reply: Yes ({reply})")
    else:
        print(f"   Reply: No")
    if bounce > 0:
        print(f"   Bounce: Yes ({bounce})")
    else:
        print(f"   Bounce: No")

print(f"\n{'='*80}")
print(f"  OPEN SIGNAL SUMMARY:")
print(f"  有打开信号 (Open Signal): {opens_count}")
print(f"  暂无打开信号 (No Open Signal Yet): {no_open_count}")
print(f"  Total: {len(sent_rows)}")

# ═══════════════════════════════════════════════
# 9. Ops API refresh
# ═══════════════════════════════════════════════
print(f"\n--- 9. Ops API Data ---")
stats = bd_ops_api.get_today_stats(DB_PATH)
inv = bd_ops_api.get_inventory(DB_PATH)
print(f"  Today stats: planned_new={stats['planned_new']}, sent_new={stats['sent_new']}")
print(f"  Inventory: strict_a0_orgs={inv['strict_a0_organizations']}, manual_review={inv['manual_review']}")

# ═══════════════════════════════════════════════
# 10. Save report
# ═══════════════════════════════════════════════
report_path = os.path.join(OUTPUT_DIR, f"auto_report_{TODAY}.md")
report_json_path = os.path.join(OUTPUT_DIR, f"auto_report_{TODAY}.json")

report_lines = [
    f"# BD Daily Results — {YESTERDAY} Batch Summary",
    f"Generated: {NOW_STR} Asia/Shanghai",
    "",
    f"## Metrics",
    f"- **Planned**: {planned_count}",
    f"- **SMTP Accepted**: {smtp_accepted}",
    f"- **Open Signal**: {opens_count}",
    f"- **No Open Signal Yet**: {no_open_count}",
    f"- **Total Open Signals**: {tracking_data.get('total_open_signals', 0)}",
    f"- **Human Replies**: {human_replies}",
    f"- **Auto Replies**: {auto_replies}",
    f"- **Hard Bounces**: {hard_bounces}",
    f"- **Unsubscribes**: {unsubs}",
    "",
    f"## Inventory",
    f"- **Total Leads**: {total_leads}",
    f"- **Broad Outreach Ready**: {broad_ready}",
    f"- **Strict A0**: {strict_a0}",
    f"- **Manual Review Pending**: {manual_pending}",
    "",
    f"## Store Details",
]

for idx, r in enumerate(sent_rows, 1):
    lid = r["lead_id"]
    store = r.get("store_name", f"Lead #{lid}")
    email = r.get("email", "")[:40]
    sent_at = r.get("sent_at", "")
    city = r.get("city", "")
    state = r.get("state", "")
    o = open_data.get(lid, {})
    has_open = o.get("has_open", False)
    signal = "Open Signal" if has_open else "No Open Signal Yet"
    report_lines.append(f"{idx}. **{store}** ({city}, {state}) — {email} — {signal}")

with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

report_json = {
    "generated_at": NOW_STR,
    "yesterday": YESTERDAY,
    "planned": planned_count,
    "smtp_accepted": smtp_accepted,
    "opens": opens_count,
    "no_opens": no_open_count,
    "human_replies": human_replies,
    "auto_replies": auto_replies,
    "hard_bounces": hard_bounces,
    "unsubs": unsubs,
    "total_leads": total_leads,
    "broad_ready": broad_ready,
    "strict_a0": strict_a0,
    "manual_pending": manual_pending,
}
with open(report_json_path, "w", encoding="utf-8") as f:
    json.dump(report_json, f, indent=2, ensure_ascii=False)

print(f"\n  Report saved: {report_path}")
print(f"  JSON saved: {report_json_path}")

conn.close()
print(f"\nDone.")
