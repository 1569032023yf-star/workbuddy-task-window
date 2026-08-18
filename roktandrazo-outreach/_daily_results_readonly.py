"""BD Daily Results — Read-Only Summary (09:00 automation)
No SMTP. No Final Send Plan. Strictly read-only.
Steps: 1) refresh Ops API cache 2) yesterday batch summary 3) per-lead detail 4) dashboard.
"""
import sqlite3, json, os, sys
from datetime import datetime, timezone, timedelta

ASIA_SH = timezone(timedelta(hours=8))
BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "data", "bd_leads.db")
OUTPUT_DIR = os.path.join(BASE, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
sys.path.insert(0, BASE)

YESTERDAY = (datetime.now(ASIA_SH) - timedelta(days=1)).strftime("%Y-%m-%d")
TODAY = datetime.now(ASIA_SH).strftime("%Y-%m-%d")
NOW_STR = datetime.now(ASIA_SH).strftime("%Y-%m-%d %H:%M:%S")

print(f"=== BD Daily Results — Read-Only Summary ===")
print(f"Generated: {NOW_STR} Asia/Shanghai | Yesterday: {YESTERDAY} | Today: {TODAY}")

# ═══ 1. Refresh Ops API cache ═══
import bd_ops_api
bd_ops_api._cache.clear()
today_stats = bd_ops_api.get_today_stats(DB_PATH)
inventory_stats = bd_ops_api.get_inventory(DB_PATH)
print(f"[1] Ops cache cleared. get_today_stats(date={today_stats['date']}) planned_new={today_stats['planned_new']} sent_new={today_stats['sent_new']} replies={today_stats['replies']} hard_bounces={today_stats['hard_bounces']}")
print(f"    get_inventory: total={inventory_stats['total_leads']} strict_a0_orgs={inventory_stats['strict_a0_organizations']} manual_review={inventory_stats['manual_review']} status={inventory_stats['status']}")

conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# ═══ 2. Yesterday's batch ═══
sent_rows = c.execute("""
    SELECT sl.*, l.store_name, l.city, l.state,
           COALESCE(NULLIF(l.organization_key,''),'org_'||sl.lead_id) as org_key
    FROM send_log sl LEFT JOIN leads l ON sl.lead_id = l.id
    WHERE sl.status = 'sent' AND sl.sent_at LIKE ?
      AND sl.message_type NOT IN ('test','internal_report','acceptance_test','sender_copy')
    ORDER BY sl.sent_at
""", (f"{YESTERDAY}%",)).fetchall()

planned_count = c.execute(
    "SELECT COUNT(*) FROM final_send_plan WHERE outreach_batch_date = ? AND status = 'planned'",
    (YESTERDAY,)).fetchone()[0]

smtp_accepted = len(sent_rows)

# Open signal per lead — read local leads.tracking_message_id + poller cache / D1
open_data = {}
tracking_source = "unavailable"

# poller tracking cache (may be stale)
poller_cache_path = os.path.join(OUTPUT_DIR, "bd_ops_poller_tracking_cache.json")
try:
    with open(poller_cache_path, "r", encoding="utf-8") as f:
        pc = json.load(f)
    if pc.get("available"):
        tracking_source = "poller_cache"
except Exception:
    pc = {"available": False}

# per-lead: try D1 for tracking_message_id of yesterday's sends
lead_ids = [r["lead_id"] for r in sent_rows if r["lead_id"]]
tracking_map = {}
if lead_ids:
    ph = ",".join("?" for _ in lead_ids)
    for r in c.execute(f"SELECT id, tracking_message_id FROM leads WHERE id IN ({ph})", lead_ids):
        if r["tracking_message_id"]:
            tracking_map[r["id"]] = r["tracking_message_id"]

if tracking_map:
    try:
        import urllib.request
        token = os.environ.get("DASHBOARD_API_KEY", "")
        ids = "','".join(tracking_map.values())
        sql = ("SELECT message_id, MIN(event_at) first_open, MAX(event_at) last_open, COUNT(*) opens "
               "FROM email_tracking_events WHERE event_type='open' AND message_id IN ('" + ids + "') "
               "GROUP BY message_id")
        req = urllib.request.Request(
            "https://roktandrazo-email-tracker.1569032023yf.workers.dev/internal/query",
            data=json.dumps({"sql": sql}).encode(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, method="POST")
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        if data and data.get("results"):
            tracking_source = "D1_direct"
            rev = {v: k for k, v in tracking_map.items()}
            for r in data["results"]:
                lid = rev.get(r.get("message_id", ""))
                if lid:
                    open_data[lid] = {"has_open": int(r.get("opens", 0)) > 0,
                                      "first_open": r.get("first_open", ""),
                                      "last_open": r.get("last_open", ""),
                                      "count": int(r.get("opens", 0))}
    except Exception as e:
        print(f"    D1 per-message open query failed: {e}")

# ═══ replies / bounces / unsubs ═══
human_replies = c.execute("""
    SELECT COUNT(*) FROM reply_log WHERE reply_received_at LIKE ?
      AND (reply_type IS NULL OR (reply_type NOT LIKE '%auto%' AND reply_type NOT LIKE '%ooo%'
           AND reply_type NOT LIKE '%autoreply%' AND reply_type NOT LIKE '%notification%'))
""", (f"{YESTERDAY}%",)).fetchone()[0]

auto_replies = c.execute("""
    SELECT COUNT(*) FROM reply_log WHERE reply_received_at LIKE ?
      AND (reply_type LIKE '%auto%' OR reply_type LIKE '%ooo%' OR reply_type LIKE '%autoreply%'
           OR reply_type LIKE '%notification%')
""", (f"{YESTERDAY}%",)).fetchone()[0]

hard_bounces = c.execute("""
    SELECT COUNT(*) FROM bounce_log WHERE bounce_type IN ('hard','policy','permanent')
      AND bounce_received_at LIKE ?
""", (f"{YESTERDAY}%",)).fetchone()[0]

unsubs = c.execute("SELECT COUNT(*) FROM leads WHERE unsubscribed_at LIKE ?",
                   (f"{YESTERDAY}%",)).fetchone()[0]

# ═══ inventory ═══
total_leads = c.execute("SELECT COUNT(*) FROM leads").fetchone()[0]

try:
    from broad_outreach_gate import analyze_all_leads
    bc = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    br = analyze_all_leads(bc)
    broad_orgs = br.get("broad_org_opportunities", 0)
    broad_locs = br.get("broad_ready_locations", [])
    broad_locs_n = len(broad_locs) if isinstance(broad_locs, list) else 0
    bc.close()
except Exception as e:
    print(f"    broad_outreach_gate error: {e}")
    broad_orgs = broad_locs_n = "N/A"

strict_a0 = c.execute("""
    SELECT COUNT(*) FROM leads WHERE
    status='new' AND confidence_score='A' AND auto_sendable=1
    AND email_verified_on_official_site=1 AND email IS NOT NULL AND email != ''
    AND email NOT IN (SELECT email FROM suppression_list)
    AND id NOT IN (SELECT lead_id FROM send_log WHERE status='sent')
    AND id NOT IN (SELECT lead_id FROM bounce_log WHERE bounce_type IN ('hard','policy','permanent'))
""").fetchone()[0]

manual_pending_rs = c.execute("""
    SELECT COUNT(*) FROM leads WHERE review_reason_code IS NOT NULL AND review_reason_code != ''
      AND review_status = 'pending'
""").fetchone()[0]

manual_pending_st = c.execute("""
    SELECT COUNT(*) FROM leads WHERE status='manual_review_needed'
""").fetchone()[0]

prev_sent = c.execute("SELECT COUNT(DISTINCT lead_id) FROM send_log WHERE status='sent'").fetchone()[0]

suppressed = c.execute("""
    SELECT COUNT(*) FROM leads WHERE email IN (SELECT email FROM suppression_list)
      OR status='do_not_contact' OR unsubscribed_at IS NOT NULL
""").fetchone()[0]

# ═══ active states ═══
state_stats = c.execute("""
    SELECT state, COUNT(*) cnt, COUNT(DISTINCT city) cities FROM leads
    WHERE state IN ('TN','AR','KY','OH','IN','MN','NE','NC','OR','CO')
    GROUP BY state ORDER BY cnt DESC
""").fetchall()

state_rows = []
for r in state_stats:
    st = r["state"]
    sendable = c.execute("""
        SELECT COUNT(*) FROM leads WHERE state=? AND
        id NOT IN (SELECT DISTINCT lead_id FROM send_log WHERE status='sent')
        AND status NOT IN ('do_not_contact','review_rejected')
        AND email IS NOT NULL AND email != ''
        AND email NOT IN (SELECT email FROM suppression_list)
    """, (st,)).fetchone()[0]
    state_rows.append({"state": st, "total": r["cnt"], "cities": r["cities"], "sendable": sendable})

# ═══ per-lead detail ═══
opens_count = 0
no_open_count = 0
detail = []
for r in sent_rows:
    lid = r["lead_id"]
    o = open_data.get(lid, {})
    has_open = o.get("has_open", False)
    if has_open:
        opens_count += 1
    else:
        no_open_count += 1
    reply_n = c.execute("SELECT COUNT(*) FROM reply_log WHERE lead_id=? AND reply_received_at LIKE ?",
                        (lid, f"{YESTERDAY}%")).fetchone()[0]
    bounce_n = c.execute("SELECT COUNT(*) FROM bounce_log WHERE lead_id=? AND bounce_received_at LIKE ?",
                         (lid, f"{YESTERDAY}%")).fetchone()[0]
    detail.append({
        "store": r.get("store_name") or f"Lead #{lid}",
        "org": r.get("org_key", ""),
        "recipient": (r.get("email") or "")[:40],
        "sent_at": r.get("sent_at", ""),
        "city": r.get("city", ""),
        "state": r.get("state", ""),
        "open_signal": "Open Signal" if has_open else "No Open Signal Yet",
        "first_open": (o.get("first_open") or "")[:19],
        "last_open": (o.get("last_open") or "")[:19],
        "open_count": o.get("count", 0),
        "reply": reply_n,
        "bounce": bounce_n,
    })

# total open signals from poller cache / D1 aggregate
total_open_signals = 0
if tracking_source == "poller_cache":
    total_open_signals = pc.get("total_open_signals", 0)
elif tracking_source == "D1_direct":
    total_open_signals = sum(v["count"] for v in open_data.values())

conn.close()

# ═══ print summary ═══
print(f"\n[2] Yesterday batch ({YESTERDAY}): planned={planned_count} smtp_accepted={smtp_accepted}")
print(f"    opens={opens_count} no_opens={no_open_count} total_open_signals={total_open_signals} (source={tracking_source})")
print(f"    human_replies={human_replies} auto_replies={auto_replies} hard_bounces={hard_bounces} unsubs={unsubs}")
print(f"[3] Inventory: total={total_leads} broad_orgs={broad_orgs}/{broad_locs_n}locs strict_a0={strict_a0} "
      f"manual(rs_pending)={manual_pending_rs} manual(status)={manual_pending_st} prev_sent={prev_sent} suppressed={suppressed}")
for s in state_rows:
    print(f"    {s['state']}: {s['total']} leads / {s['cities']} cities / {s['sendable']} sendable")

# ═══ 4. regenerate dashboard ═══
print(f"\n[4] Regenerating dashboard...")
try:
    import bd_dashboard_v3_2  # placeholder; load via importlib below
except Exception:
    pass
import importlib.util
spec = importlib.util.spec_from_file_location("bd_dashboard_v3_2",
    os.path.join(BASE, "bd_dashboard_v3.2.py"))
dmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dmod)
dmod.main()

# ═══ write report ═══
md_path = os.path.join(OUTPUT_DIR, f"auto_report_{TODAY}.md")
json_path = os.path.join(OUTPUT_DIR, f"auto_report_{TODAY}.json")

lines = [
    f"# BD Daily Results — {YESTERDAY} Batch Summary",
    "",
    f"**Generated**: {NOW_STR} Asia/Shanghai | **DB**: `bd_leads.db` | **Mode**: Read-Only",
    "",
    "## Batch Summary",
    "",
    "| Metric | Value |",
    "|--------|-------|",
    f"| Planned | {planned_count} |",
    f"| SMTP Accepted | {smtp_accepted} |",
    f"| Open Signal | {opens_count} |",
    f"| No Open Signal Yet | {no_open_count} |",
    f"| Total Open Signals | {total_open_signals} ({tracking_source}) |",
    f"| Human Replies | {human_replies} |",
    f"| Auto Replies | {auto_replies} |",
    f"| Hard Bounces | {hard_bounces} |",
    f"| Unsubscribes | {unsubs} |",
    "",
    "## Inventory",
    "",
    "| Metric | Value |",
    "|--------|-------|",
    f"| Total Leads | {total_leads} |",
    f"| Broad Outreach Ready | {broad_orgs} orgs / {broad_locs_n} locations |",
    f"| Strict A0 | {strict_a0} |",
    f"| Manual Review Pending | {manual_pending_rs} (review_status=pending) / {manual_pending_st} (status=manual_review_needed) |",
    f"| Previously Sent | {prev_sent} |",
    f"| Suppressed | {suppressed} |",
    "",
    "## Active States",
    "",
    "| State | Leads | Cities | Sendable |",
    "|-------|-------|--------|----------|",
]
for s in state_rows:
    lines.append(f"| {s['state']} | {s['total']} | {s['cities']} | {s['sendable']} |")

lines += ["", "## Yesterday's Send Details", ""]
if detail:
    for i, d in enumerate(detail, 1):
        lines.append(f"{i}. **{d['store']}** ({d['city']}, {d['state']}) — {d['recipient']} — {d['open_signal']}"
                     + (f" — opens={d['open_count']}" if d['open_count'] else "")
                     + (f" — Reply:{d['reply']}" if d['reply'] else "")
                     + (f" — Bounce:{d['bounce']}" if d['bounce'] else ""))
else:
    lines.append("No sends found for yesterday.")

with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

payload = {
    "generated_at": NOW_STR, "timezone": "Asia/Shanghai",
    "yesterday": YESTERDAY, "today": TODAY,
    "batch": {"planned": planned_count, "smtp_accepted": smtp_accepted,
              "opens": opens_count, "no_opens": no_open_count,
              "total_open_signals": total_open_signals,
              "human_replies": human_replies, "auto_replies": auto_replies,
              "hard_bounces": hard_bounces, "unsubscribes": unsubs},
    "inventory": {"total_leads": total_leads, "broad_outreach_ready_orgs": broad_orgs,
                  "broad_outreach_ready_locs": broad_locs_n, "strict_a0": strict_a0,
                  "manual_review_pending_review_status": manual_pending_rs,
                  "manual_review_needed_status": manual_pending_st,
                  "previously_sent": prev_sent, "suppressed": suppressed},
    "states": state_rows,
    "store_details": detail,
    "tracking_source": tracking_source,
    "ops_today": today_stats,
    "ops_inventory": inventory_stats,
}
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

print(f"\n  Report: {md_path}")
print(f"  JSON:   {json_path}")
print("\nDone.")
