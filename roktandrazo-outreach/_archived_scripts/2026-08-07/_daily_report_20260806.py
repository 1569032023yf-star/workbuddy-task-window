raise RuntimeError("LEGACY_SMTP_DISABLED: dated send script archived 2026-08-07. Use bd_orchestrator -> daily_session -> bd_sender only.")
#!/usr/bin/env python3
"""BD Daily Results — 2026-08-06 09:00 — Read-Only Summary for batch 2026-08-05."""
import os, sys, json, sqlite3
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
WORKSPACE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(WORKSPACE, "data", "bd_leads.db")
sys.path.insert(0, WORKSPACE)

import bd_ops_api

# ── 1. Refresh Dashboard Cache ──────────────────────────
print("=" * 72)
print("📊 BD DAILY RESULTS — 2026-08-06 09:00 Asia/Shanghai")
print("=" * 72)

today_stats = bd_ops_api.get_today_stats(DB_PATH)
inventory = bd_ops_api.get_inventory(DB_PATH)

print("\n── 1a. Today Stats ──")
for k, v in today_stats.items():
    print(f"  {k}: {v}")

print("\n── 1b. Inventory ──")
for k, v in inventory.items():
    if isinstance(v, dict):
        print(f"  {k}:")
        for kk, vv in v.items():
            print(f"    {kk}: {vv}")
    else:
        print(f"  {k}: {v}")

# ── 2. Yesterday Batch (2026-08-05) ─────────────────────
YESTERDAY = "2026-08-05"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Check which tables exist
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

# 2a. Planned count
planned = conn.execute(
    "SELECT COUNT(*) as cnt FROM final_send_plan WHERE outreach_batch_date = ?",
    (YESTERDAY,)
).fetchone()["cnt"]

# 2b. SMTP accepted
smtp_accepted = conn.execute(
    """SELECT COUNT(*) as cnt FROM send_log 
       WHERE (outreach_batch_date = ? OR (outreach_batch_date IS NULL AND sent_at LIKE ?))
       AND status = 'sent'
       AND (message_type IS NULL OR message_type NOT IN ('test','internal_report','acceptance_test','sender_copy'))""",
    (YESTERDAY, YESTERDAY + "%")
).fetchone()["cnt"]

# 2c. Full send records
sent_rows = conn.execute(
    """SELECT sl.id as send_id, sl.lead_id, sl.email, sl.subject, sl.sent_at, sl.status,
              sl.message_type, sl.outreach_batch_date,
              l.store_name, l.city, l.state, l.organization_key, l.email as lead_email
       FROM send_log sl
       LEFT JOIN leads l ON sl.lead_id = l.id
       WHERE (sl.outreach_batch_date = ? OR (sl.outreach_batch_date IS NULL AND sl.sent_at LIKE ?))
         AND sl.status = 'sent'
         AND (sl.message_type IS NULL OR sl.message_type NOT IN ('test','internal_report','acceptance_test','sender_copy'))
       ORDER BY sl.sent_at""",
    (YESTERDAY, YESTERDAY + "%")
).fetchall()

# 2d. Open signals from email_tracking_messages / poller cache
# Try email_tracking_messages table
open_data = {}
if 'email_tracking_messages' in tables:
    # Check schema
    cols = [r[1] for r in conn.execute("PRAGMA table_info(email_tracking_messages)").fetchall()]
    print(f"\n  email_tracking_messages columns: {cols}")

    # Try to match leads via email
    for sr in sent_rows:
        lead_id = sr["lead_id"]
        email = sr["email"] or sr["lead_email"] or ""
        if not email:
            continue
        opens = conn.execute(
            """SELECT open_signal_count, first_open_at, last_open_at 
               FROM email_tracking_messages 
               WHERE recipient_email = ?""",
            (email,)
        ).fetchall()
        if opens:
            total = sum(o["open_signal_count"] or 0 for o in opens)
            first = min((o["first_open_at"] for o in opens if o["first_open_at"]), default=None)
            last = max((o["last_open_at"] for o in opens if o["last_open_at"]), default=None)
            open_data[lead_id] = {"count": total, "first": first, "last": last}

# Also try poller cache
poller_cache = os.path.join(WORKSPACE, "data", "poller_tracking_cache.json")
if os.path.exists(poller_cache):
    with open(poller_cache, 'r', encoding='utf-8') as f:
        poller_data = json.load(f)
    print(f"  Poller cache entries: {len(poller_data)}")
    # Supplement open data from poller cache if not already found
    for sr in sent_rows:
        lead_id = sr["lead_id"]
        if lead_id in open_data:
            continue
        email = sr["email"] or sr["lead_email"] or ""
        if email in poller_data:
            pd = poller_data[email]
            open_data[lead_id] = {
                "count": pd.get("open_count", pd.get("open_signal_count", 0)),
                "first": pd.get("first_open_at", pd.get("first_open", "")),
                "last": pd.get("last_open_at", pd.get("last_open", ""))
            }

# 2e. Replies from reply_log
reply_data = {}
if sent_rows:
    lead_ids = [r["lead_id"] for r in sent_rows]
    placeholders = ','.join(['?'] * len(lead_ids))
    
    if 'reply_log' in tables:
        replies = conn.execute(
            f"""SELECT lead_id, summary, suggested_action, created_at
                FROM reply_log WHERE lead_id IN ({placeholders})
                ORDER BY created_at""",
            lead_ids
        ).fetchall()
        for r in replies:
            lid = r["lead_id"]
            if lid not in reply_data:
                reply_data[lid] = []
            reply_data[lid].append({
                "summary": r["summary"] or "",
                "action": r["suggested_action"] or "",
                "at": r["created_at"] or ""
            })

# 2f. Bounces
bounce_data = {}
if sent_rows and 'bounce_log' in tables:
    bounces = conn.execute(
        f"""SELECT lead_id, bounce_type, bounce_received_at
            FROM bounce_log WHERE lead_id IN ({placeholders})
            ORDER BY bounce_received_at""",
        lead_ids
    ).fetchall()
    for b in bounces:
        lid = b["lead_id"]
        if lid not in bounce_data:
            bounce_data[lid] = []
        bounce_data[lid].append({"type": b["bounce_type"], "at": b["bounce_received_at"]})

# Count human vs auto replies (global for yesterday batch)
human_replies = 0
auto_replies = 0
if 'reply_log' in tables:
    human_replies = conn.execute(
        f"""SELECT COUNT(DISTINCT rl.lead_id) FROM reply_log rl
            WHERE rl.lead_id IN ({placeholders})
              AND (rl.suggested_action IS NULL OR rl.suggested_action NOT IN ('auto_reply','out_of_office','vacation'))""",
        lead_ids
    ).fetchone()[0] if sent_rows else 0

    auto_replies = conn.execute(
        f"""SELECT COUNT(DISTINCT rl.lead_id) FROM reply_log rl
            WHERE rl.lead_id IN ({placeholders})
              AND rl.suggested_action IN ('auto_reply','out_of_office','vacation')""",
        lead_ids
    ).fetchone()[0] if sent_rows else 0

hard_bounces = 0
if sent_rows and 'bounce_log' in tables:
    hard_bounces = conn.execute(
        f"""SELECT COUNT(DISTINCT lead_id) FROM bounce_log
            WHERE lead_id IN ({placeholders})
              AND bounce_type IN ('hard','policy','permanent')""",
        lead_ids
    ).fetchone()[0]

unsubs = 0
if sent_rows:
    unsubs = conn.execute(
        f"""SELECT COUNT(DISTINCT id) FROM leads
            WHERE id IN ({placeholders}) AND unsubscribed_at IS NOT NULL""",
        lead_ids
    ).fetchone()[0]

# 2g. Current sendable inventory — Broad Outreach Ready
broad_ready = conn.execute(
    """SELECT COUNT(*) as cnt FROM leads l
       WHERE l.status = 'new' 
         AND l.email IS NOT NULL AND l.email != ''
         AND l.email NOT LIKE '%@example%'
         AND l.id NOT IN (SELECT COALESCE(lead_id,0) FROM send_log WHERE status='sent' AND lead_id IS NOT NULL)
         AND l.id NOT IN (SELECT COALESCE(lead_id,0) FROM bounce_log WHERE bounce_type IN ('hard','policy','permanent') AND lead_id IS NOT NULL)
         AND l.unsubscribed_at IS NULL
         AND l.review_status != 'rejected'
         AND l.confidence_score IS NOT NULL""",
).fetchone()["cnt"]

strict_a0 = conn.execute(
    """SELECT COUNT(*) as cnt FROM leads l
       WHERE l.status = 'new' 
         AND l.confidence_score = 'A'
         AND l.auto_sendable = 1
         AND l.email_verified_on_official_site = 1
         AND l.email IS NOT NULL AND l.email != ''
         AND l.id NOT IN (SELECT COALESCE(lead_id,0) FROM send_log WHERE status='sent' AND lead_id IS NOT NULL)
         AND l.id NOT IN (SELECT COALESCE(lead_id,0) FROM bounce_log WHERE bounce_type IN ('hard','policy','permanent') AND lead_id IS NOT NULL)
         AND l.unsubscribed_at IS NULL""",
).fetchone()["cnt"]

manual_pending = conn.execute(
    """SELECT COUNT(*) as cnt FROM leads
       WHERE (review_status = 'pending' OR manual_review_needed = 1)
         AND status != 'suppressed'""",
).fetchone()["cnt"]

# 2h. Active states
active_states = conn.execute(
    """SELECT state, COUNT(*) as cnt, COUNT(DISTINCT city) as city_cnt
       FROM leads WHERE state IN ('TN','AR','KY','OH','IN','MN','NE','NC','OR','CO')
         AND status != 'suppressed'
       GROUP BY state ORDER BY cnt DESC"""
).fetchall()

# Sendable by state (Broad Outreach Ready per state)
sendable_by_state = conn.execute(
    """SELECT l.state, COUNT(*) as cnt
       FROM leads l
       WHERE l.status = 'new' 
         AND l.email IS NOT NULL AND l.email != ''
         AND l.email NOT LIKE '%@example%'
         AND l.id NOT IN (SELECT COALESCE(lead_id,0) FROM send_log WHERE status='sent' AND lead_id IS NOT NULL)
         AND l.id NOT IN (SELECT COALESCE(lead_id,0) FROM bounce_log WHERE bounce_type IN ('hard','policy','permanent') AND lead_id IS NOT NULL)
         AND l.unsubscribed_at IS NULL
         AND l.review_status != 'rejected'
         AND l.confidence_score IS NOT NULL
         AND l.state IN ('TN','AR','KY','OH','IN','MN','NE','NC','OR','CO')
       GROUP BY l.state ORDER BY cnt DESC"""
).fetchall()

print("\n── 2. Yesterday Batch Summary (2026-08-05) ──")
print(f"  昨日计划数: {planned}")
print(f"  SMTP 已接受数: {smtp_accepted}")
print(f"  有打开信号的商家数: {sum(1 for lid in open_data if open_data[lid]['count'] > 0)}")
print(f"  暂无打开信号的商家数: {len(sent_rows) - sum(1 for lid in open_data if open_data[lid]['count'] > 0)}")
print(f"  打开信号总次数: {sum(open_data[lid]['count'] for lid in open_data)}")
print(f"  人工回复数: {human_replies}")
print(f"  自动回复数: {auto_replies}")
print(f"  Hard Bounce 数: {hard_bounces}")
print(f"  Unsubscribe 数: {unsubs}")
print(f"  Broad Outreach Ready (可发送): {broad_ready}")
print(f"  Strict A0 (可发送): {strict_a0}")
print(f"  人工待处理 (manual_review_needed + review_status=pending): {manual_pending}")

print("\n── Active States ──")
for row in active_states:
    sendable = next((s["cnt"] for s in sendable_by_state if s["state"] == row["state"]), 0)
    print(f"  {row['state']}: {row['cnt']} leads in {row['city_cnt']} cities ({sendable} sendable)")

# ── 3. Per-Email Results ─────────────────────────────────
print("\n── 3. Per-Email Results (2026-08-05) ──")
print(f"\n  {'Store':<35} {'Recipient':<40} {'Sent At':<20} {'Open':<25} {'Reply':<20} {'Bounce':<12}")
print(f"  {'-'*35} {'-'*40} {'-'*20} {'-'*25} {'-'*20} {'-'*12}")

total_opens = 0
stores_with_opens = 0
stores_without_opens = 0

for sr in sent_rows:
    store_name = sr["store_name"] or "Unknown"
    city = sr["city"] or "?"
    state = sr["state"] or "?"
    store_display = f"{store_name} ({city}, {state})"
    if len(store_display) > 35:
        store_display = store_display[:32] + "..."
    
    email = (sr["email"] or sr["lead_email"] or "N/A")
    recipient = email if len(email) <= 40 else email[:37] + "..."
    
    sent_at = sr["sent_at"] or "N/A"
    
    lead_id = sr["lead_id"]
    
    # Open signal
    if lead_id in open_data and open_data[lead_id]["count"] > 0:
        od = open_data[lead_id]
        first_str = od["first"][:16] if od["first"] else "N/A"
        open_display = f"✓ {od['count']}x (1st: {first_str})"
        total_opens += od["count"]
        stores_with_opens += 1
    else:
        open_display = "暂无打开信号"
        stores_without_opens += 1
    
    # Reply
    if lead_id in reply_data and reply_data[lead_id]:
        rd = reply_data[lead_id]
        reply_parts = []
        for rp in rd[:2]:  # max 2 replies
            action = rp["action"] or "?"
            summary = (rp["summary"] or "")[:15]
            reply_parts.append(f"{action}")
        reply_display = "; ".join(reply_parts)
        if len(reply_display) > 20:
            reply_display = reply_display[:17] + "..."
    else:
        reply_display = "—"
    
    # Bounce
    if lead_id in bounce_data and bounce_data[lead_id]:
        bd = bounce_data[lead_id]
        bounce_display = ", ".join(bp["type"] for bp in bd)
        if len(bounce_display) > 12:
            bounce_display = bounce_display[:9] + "..."
    else:
        bounce_display = "—"
    
    print(f"  {store_display:<35} {recipient:<40} {sent_at:<20} {open_display:<25} {reply_display:<20} {bounce_display:<12}")

print(f"\n  📊 打开信号: {stores_with_opens} 商家有打开信号, {stores_without_opens} 商家暂无打开信号")
print(f"  📊 打开信号总次数: {total_opens}")

# ── 4. Dashboard Update ──────────────────────────────────
print("\n── 4. Dashboard Update ──")
dashboard_script = os.path.join(WORKSPACE, "bd_operations_dashboard.py")
if os.path.exists(dashboard_script):
    import importlib.util
    spec = importlib.util.spec_from_file_location("bd_operations_dashboard", dashboard_script)
    dash_module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(dash_module)
        if hasattr(dash_module, 'main'):
            dash_module.main()
            print("  Dashboard regenerated via main().")
        elif hasattr(dash_module, 'gather_data') and hasattr(dash_module, 'render_html'):
            data = dash_module.gather_data()
            dash_module.render_html(data)
            print("  Dashboard rendered via gather_data/render_html.")
        else:
            print("  No main() or gather_data/render_html found in bd_operations_dashboard.py")
    except Exception as e:
        print(f"  Dashboard script error: {e}")
else:
    print("  bd_operations_dashboard.py not found.")

conn.close()
print("\n✅ Read-only summary complete.")
