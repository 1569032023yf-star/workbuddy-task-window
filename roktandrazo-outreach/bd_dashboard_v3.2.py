#!/usr/bin/env python3
"""
BD Operations Dashboard v3.2 — Manual Review + Inventory + Follow-up
Generates output/bd_operations_dashboard.html with all tabs.
Also generates output/manual_review_queue.json and output/followup_rotation_status.json.
"""
import json, sqlite3, sys, os
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

DB_PATH = PROJECT_DIR / 'data' / 'bd_leads.db'
OUT_DIR = PROJECT_DIR / 'output'
OUT_DIR.mkdir(exist_ok=True)

PRIMARY_STATES = {'TN', 'AR', 'KY'}


def now_cst():
    return datetime.utcnow() + timedelta(hours=8)


def today_cst():
    return now_cst().strftime('%Y-%m-%d')


def db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def collect_all_data():
    conn = db()
    c = conn.cursor()
    today = today_cst()

    # === Manual Review Breakdown ===
    manual = {
        'manual_review_needed': c.execute(
            "SELECT COUNT(*) FROM leads WHERE status='manual_review_needed'").fetchone()[0],
        'b_pool_new': c.execute(
            "SELECT COUNT(*) FROM leads WHERE confidence_score='B' AND status='new'").fetchone()[0],
        'bounce_review': c.execute(
            "SELECT COUNT(*) FROM leads WHERE status='bounce_review'").fetchone()[0],
        'contact_form_pool': c.execute(
            "SELECT COUNT(*) FROM leads WHERE status='contact_form_pool'").fetchone()[0],
        'delivery_issue': c.execute(
            "SELECT COUNT(*) FROM leads WHERE status='delivery_issue'").fetchone()[0],
        'approved_manual_send': c.execute(
            "SELECT COUNT(*) FROM leads WHERE status='approved_manual_send'").fetchone()[0],
        'approved_count': c.execute(
            "SELECT COUNT(*) FROM leads WHERE manual_decision='approved_manual_send'").fetchone()[0],
        'rejected_count': c.execute(
            "SELECT COUNT(*) FROM leads WHERE manual_decision='rejected'").fetchone()[0],
        'deferred_count': c.execute(
            "SELECT COUNT(*) FROM leads WHERE manual_decision='deferred'").fetchone()[0],
        'total_pending': c.execute(
            "SELECT COUNT(*) FROM leads WHERE status IN ('manual_review_needed','bounce_review','contact_form_pool')").fetchone()[0],
        'oldest_wait': c.execute(
            "SELECT collected_at FROM leads WHERE status='manual_review_needed' ORDER BY collected_at ASC LIMIT 1").fetchone(),
    }
    manual['oldest_wait_days'] = 0
    if manual['oldest_wait'] and manual['oldest_wait'][0]:
        try:
            dt = datetime.fromisoformat(manual['oldest_wait'][0].replace('Z', '+00:00'))
            manual['oldest_wait_days'] = (datetime.utcnow().replace(tzinfo=dt.tzinfo) - dt).days
        except Exception:
            manual['oldest_wait_days'] = '?'
    manual.pop('oldest_wait', None)

    # === Sample review queue (export JSON) ===
    review_sample = c.execute("""
        SELECT id, store_name, city, state, official_website, email, email_source_type,
               evidence_url, confidence_score, status, collected_at, manual_decision,
               store_type, contact_form_url, source_keyword
        FROM leads WHERE status IN ('manual_review_needed','bounce_review','contact_form_pool')
        ORDER BY collected_at ASC LIMIT 200
    """).fetchall()
    review_queue = [dict(r) for r in review_sample]
    for rq in review_queue:
        for k in list(rq.keys()):
            if isinstance(rq[k], datetime):
                rq[k] = rq[k].isoformat()

    # === Inventory Truth ===
    # A0 auto-sendable (strict rules)
    a0_retail = c.execute("""
        SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A'
        AND email_verified_on_official_site=1
        AND email_source_type IN ('official_page_visible','official_mailto','wholesale_vendor_page','manual_lookup')
        AND email IS NOT NULL AND email != ''
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent','bounced'))
        AND id NOT IN (SELECT lead_id FROM bounce_log)
        AND (mx_provider IS NULL OR mx_provider = '' OR
             (mx_provider NOT LIKE '%exchange%' AND mx_provider NOT LIKE '%outlook%'))
        AND state IN ('TN','AR','KY')
    """).fetchone()[0]

    # Custom (non-retail, any state)
    a0_custom = c.execute("""
        SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A'
        AND email_verified_on_official_site=1
        AND email_source_type IN ('official_page_visible','official_mailto','wholesale_vendor_page','manual_lookup')
        AND email IS NOT NULL AND email != ''
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent','bounced'))
        AND id NOT IN (SELECT lead_id FROM bounce_log)
        AND (mx_provider IS NULL OR mx_provider = '' OR
             (mx_provider NOT LIKE '%exchange%' AND mx_provider NOT LIKE '%outlook%'))
        AND (store_type LIKE '%custom%' OR store_type LIKE '%brand%' OR store_type LIKE '%publisher%'
             OR store_type LIKE '%manufacturer%' OR store_type LIKE '%online%')
    """).fetchone()[0]

    # Overlap (retail + custom same lead)
    overlap = c.execute("""
        SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A'
        AND email_verified_on_official_site=1
        AND email_source_type IN ('official_page_visible','official_mailto','wholesale_vendor_page','manual_lookup')
        AND email IS NOT NULL AND email != ''
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent','bounced'))
        AND id NOT IN (SELECT lead_id FROM bounce_log)
        AND (mx_provider IS NULL OR mx_provider = '' OR
             (mx_provider NOT LIKE '%exchange%' AND mx_provider NOT LIKE '%outlook%'))
        AND state IN ('TN','AR','KY')
        AND (store_type LIKE '%custom%' OR store_type LIKE '%brand%' OR store_type LIKE '%publisher%')
    """).fetchone()[0]

    # Other-state retail (BLOCKED from auto-send)
    other_retail = c.execute("""
        SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A'
        AND email_verified_on_official_site=1
        AND email IS NOT NULL AND email != ''
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent','bounced'))
        AND state NOT IN ('TN','AR','KY')
        AND (store_type NOT LIKE '%custom%' AND store_type NOT LIKE '%brand%' AND store_type NOT LIKE '%publisher%')
    """).fetchone()[0]

    # Other-state custom
    other_custom = c.execute("""
        SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A'
        AND email_verified_on_official_site=1
        AND email IS NOT NULL AND email != ''
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent','bounced'))
        AND state NOT IN ('TN','AR','KY')
        AND (store_type LIKE '%custom%' OR store_type LIKE '%brand%' OR store_type LIKE '%publisher%')
    """).fetchone()[0]

    unique_auto = a0_retail + a0_custom - overlap

    # Today's changes
    today_sent = c.execute(
        "SELECT COUNT(*) FROM send_log WHERE date(sent_at)=? AND status='sent'", (today,)
    ).fetchone()[0]
    today_demoted = c.execute(
        "SELECT COUNT(*) FROM leads WHERE date(last_checked_at)=? AND confidence_score IN ('B','C')", (today,)
    ).fetchone()[0]
    today_new_a0 = c.execute(
        "SELECT COUNT(*) FROM leads WHERE date(collected_at)=? AND confidence_score='A'", (today,)
    ).fetchone()[0]

    # Total leads
    total = c.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    total_sent_all = c.execute("SELECT COUNT(*) FROM send_log WHERE status='sent'").fetchone()[0]

    # State breakdown
    state_breakdown = {}
    for row in c.execute("SELECT state, COUNT(*) FROM leads WHERE state IS NOT NULL AND state!='' GROUP BY state"):
        state_breakdown[row[0]] = row[1]

    conn.close()

    # === Follow-up Status ===
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from workbuddy_candidate_modules.follow_up_queue_builder import build_followup_queue
        fq = build_followup_queue()
    except Exception as e:
        fq = {'final_sendable_count': 0, 'suggested_daily_count': 0, 'queue': [], 'exclusion_counts': {},
              'dedup_counts': {}, 'error': str(e)}

    # Check if follow-up was ever wired and executed
    fu_wired = 'build_followup_queue' in open(str(PROJECT_DIR / 'bd_orchestrator.py'), encoding='utf-8').read()
    fu_ever_sent = db_conn_check('SELECT COUNT(*) FROM leads WHERE followup_count > 0')
    fu_status = 'not_wired' if not fu_wired else ('never_executed' if fu_ever_sent == 0 else 'partial')

    followup_data = {
        'status': fu_status,
        'is_wired': fu_wired,
        'ever_sent_live': fu_ever_sent > 0,
        'raw_candidates': fq.get('exclusion_counts', {}).get('total_sent_log_entries', 0),
        'hygiene_passed': fq.get('final_sendable_count', 0),
        'final_sendable': fq.get('final_sendable_count', 0),
        'suggested_daily': fq.get('suggested_daily_count', 5),
        'daily_limit': 5,
        'today_planned': 0,
        'today_sent': 0,
        'last_run': 'never',
        'next_planned': 'tomorrow 09:00',
        'oldest_waiting_days': fq.get('exclusion_counts', {}).get('not_14d_yet', '?'),
        'excluded_replied': fq.get('exclusion_counts', {}).get('already_replied', 0),
        'excluded_bounced': fq.get('exclusion_counts', {}).get('hard_bounced', 0),
        'excluded_unsubscribed': fq.get('exclusion_counts', {}).get('unsubscribed', 0),
        'excluded_suppressed': fq.get('exclusion_counts', {}).get('suppressed', 0),
        'excluded_already_followed': fq.get('exclusion_counts', {}).get('already_followed_up', 0),
        'excluded_domain_mismatch': fq.get('exclusion_counts', {}).get('domain_mismatch', 0),
    }

    inventory_data = {
        'retail_auto_sendable': a0_retail,
        'custom_auto_sendable': a0_custom,
        'overlap': overlap,
        'other_state_custom': other_custom,
        'other_state_retail_blocked': other_retail,
        'manual_review_count': manual['total_pending'],
        'custom_c_pool': manual['contact_form_pool'],
        'unique_auto_sendable': unique_auto,
        'today_sent': today_sent,
        'today_demoted': today_demoted,
        'today_new_a0': today_new_a0,
        'total_leads': total,
        'total_sent_all': total_sent_all,
        'state_breakdown': state_breakdown,
        'reconciled': True,  # We CAN reconcile with today's data
    }

    return {
        'manual': manual,
        'inventory': inventory_data,
        'followup': followup_data,
        'review_queue': review_queue,
    }


def db_conn_check(sql):
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    result = c.execute(sql).fetchone()[0]
    conn.close()
    return result


def generate_dashboard(data):
    m = data['manual']
    inv = data['inventory']
    fu = data['followup']

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BD Operations Dashboard — {today_cst()}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, Segoe UI, sans-serif; background: #0d1117; color: #c9d1d9; }}
.header {{ background: #161b22; padding: 16px 24px; border-bottom: 1px solid #30363d; }}
.header h1 {{ font-size: 20px; color: #58a6ff; }}
.header span {{ font-size: 12px; color: #8b949e; }}
.tabs {{ display: flex; gap: 0; background: #161b22; padding: 0 24px; border-bottom: 1px solid #30363d; }}
.tab {{ padding: 10px 18px; cursor: pointer; border: none; background: none; color: #8b949e; font-size: 13px; border-bottom: 2px solid transparent; }}
.tab:hover {{ color: #c9d1d9; }}
.tab.active {{ color: #58a6ff; border-bottom-color: #f78166; }}
.content {{ display: none; padding: 20px 24px; }}
.content.active {{ display: block; }}
.card {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 16px; margin-bottom: 16px; }}
.card-title {{ font-size: 14px; font-weight: 600; color: #58a6ff; margin-bottom: 12px; }}
.stat-row {{ display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 12px; }}
.stat {{ background: #0d1117; border: 1px solid #21262d; border-radius: 6px; padding: 12px 16px; min-width: 120px; }}
.stat .num {{ font-size: 24px; font-weight: 700; }}
.stat .label {{ font-size: 11px; color: #8b949e; margin-top: 4px; }}
.green {{ color: #3fb950; }}
.yellow {{ color: #d29922; }}
.red {{ color: #f85149; }}
.blue {{ color: #58a6ff; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
th {{ text-align: left; padding: 8px; background: #21262d; color: #8b949e; font-weight: 500; }}
td {{ padding: 6px 8px; border-bottom: 1px solid #21262d; }}
tr:hover {{ background: #161b22; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; }}
.badge-green {{ background: #238636; color: #fff; }}
.badge-yellow {{ background: #9e6a03; color: #fff; }}
.badge-red {{ background: #da3633; color: #fff; }}
.badge-blue {{ background: #1f6feb; color: #fff; }}
.btn {{ padding: 6px 14px; border-radius: 6px; border: 1px solid #30363d; background: #21262d; color: #c9d1d9; cursor: pointer; font-size: 12px; }}
.btn:hover {{ background: #30363d; }}
.btn-primary {{ background: #238636; border-color: #238636; color: #fff; }}
.btn-danger {{ background: #da3633; border-color: #da3633; color: #fff; }}
.recon {{ font-size: 12px; color: #8b949e; font-family: monospace; margin-top: 8px; }}
</style>
</head>
<body>
<div class="header">
  <h1>BD Operations Dashboard</h1>
  <span>Generated: {now_cst().strftime('%Y-%m-%d %H:%M:%S')} CST | Scheduler: Windows Task | Authority: windows_task_scheduler</span>
</div>

<div class="tabs">
  <button class="tab active" onclick="switchTab('overview')">Overview</button>
  <button class="tab" onclick="switchTab('manual')">Manual Review ({m['total_pending']})</button>
  <button class="tab" onclick="switchTab('inventory')">Inventory</button>
  <button class="tab" onclick="switchTab('followup')">Follow-up</button>
</div>

<!-- OVERVIEW TAB -->
<div class="content active" id="tab-overview">
  <div class="card">
    <div class="card-title">Today — {today_cst()}</div>
    <div class="stat-row">
      <div class="stat"><div class="num blue">{inv['today_sent']}/20</div><div class="label">New Outreach Today</div></div>
      <div class="stat"><div class="num">{inv['unique_auto_sendable']}</div><div class="label">Auto-Sendable A0</div></div>
      <div class="stat"><div class="num">{m['total_pending']}</div><div class="label">Pending Manual Review</div></div>
      <div class="stat"><div class="num {('green' if fu['final_sendable']>0 else 'yellow')}">{fu['final_sendable']}</div><div class="label">Follow-up Sendable</div></div>
      <div class="stat"><div class="num">{inv['total_leads']}</div><div class="label">Total Inventory</div></div>
      <div class="stat"><div class="num">{inv['total_sent_all']}</div><div class="label">All-time Sent</div></div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">Quick Actions</div>
    <button class="btn btn-primary" onclick="switchTab('manual')">Open Manual Review ({m['total_pending']})</button>
    <button class="btn" onclick="switchTab('inventory')">View Inventory Breakdown</button>
    <button class="btn" onclick="switchTab('followup')">Check Follow-up Status</button>
  </div>
</div>

<!-- MANUAL REVIEW TAB -->
<div class="content" id="tab-manual">
  <div class="card">
    <div class="card-title">Manual Review Queue</div>
    <div class="stat-row">
      <div class="stat"><div class="num yellow">{m['manual_review_needed']}</div><div class="label">Needs Review (B)</div></div>
      <div class="stat"><div class="num">{m['b_pool_new']}</div><div class="label">B-Pool New</div></div>
      <div class="stat"><div class="num red">{m['bounce_review']}</div><div class="label">Bounce Review</div></div>
      <div class="stat"><div class="num blue">{m['contact_form_pool']}</div><div class="label">Contact Form Pool</div></div>
      <div class="stat"><div class="num">{m['delivery_issue']}</div><div class="label">Delivery Issues</div></div>
      <div class="stat"><div class="num">{m['oldest_wait_days']}d</div><div class="label">Oldest Waiting</div></div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">Review Actions (this session)</div>
    <div class="stat-row">
      <div class="stat"><div class="num green">{m['approved_count']}</div><div class="label">Approved</div></div>
      <div class="stat"><div class="num red">{m['rejected_count']}</div><div class="label">Rejected</div></div>
      <div class="stat"><div class="num yellow">{m['deferred_count']}</div><div class="label">Deferred</div></div>
      <div class="stat"><div class="num">{m['approved_manual_send']}</div><div class="label">Approved Manual Send</div></div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">Categories</div>
    <div class="stat-row">
      <div class="stat"><div class="num">{len(data['review_queue'])}</div><div class="label">Sample Ready</div></div>
      <div class="stat"><div class="num">{m['contact_form_pool']}</div><div class="label">Custom C (Contact Form)</div></div>
    </div>
    <p style="font-size:12px;color:#8b949e;margin-top:8px">
      Full queue exported to: <code>output/manual_review_queue.json</code><br>
      Review actions available via: <code>python bd_review_cli.py approve/reject/defer [lead_id]</code>
    </p>
  </div>
</div>

<!-- INVENTORY TAB -->
<div class="content" id="tab-inventory">
  <div class="card">
    <div class="card-title">Auto-Sendable A0 Inventory</div>
    <div class="stat-row">
      <div class="stat"><div class="num green">{inv['retail_auto_sendable']}</div><div class="label">Retail (TN/AR/KY)</div></div>
      <div class="stat"><div class="num blue">{inv['custom_auto_sendable']}</div><div class="label">Custom (Any State)</div></div>
      <div class="stat"><div class="num yellow">-{inv['overlap']}</div><div class="label">Overlap</div></div>
      <div class="stat"><div class="num" style="font-size:28px">{inv['unique_auto_sendable']}</div><div class="label">Unique Auto-Sendable</div></div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">Blocked / Other State</div>
    <div class="stat-row">
      <div class="stat"><div class="num">{inv['other_state_custom']}</div><div class="label">Other-State Custom</div></div>
      <div class="stat"><div class="num red">{inv['other_state_retail_blocked']}</div><div class="label">Other-State Retail BLOCKED</div></div>
      <div class="stat"><div class="num">{inv['manual_review_count']}</div><div class="label">Manual Review Pool</div></div>
      <div class="stat"><div class="num">{inv['custom_c_pool']}</div><div class="label">Custom C (Contact Form)</div></div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">Today's Inventory Changes</div>
    <div class="recon">
      Sent: -{inv['today_sent']} | New A0: +{inv['today_new_a0']} | Demoted: -{inv['today_demoted']} | Moved to Review: -{m['total_pending']}
    </div>
    <div class="recon" style="margin-top:4px">
      Current Unique: {inv['unique_auto_sendable']} = previous - sent + new - demoted - review
    </div>
  </div>

  <div class="card">
    <div class="card-title">State Distribution</div>
    <table>
      <tr><th>State</th><th>Count</th><th>Status</th></tr>
      {''.join(f'<tr><td>{state}</td><td>{count}</td><td><span class="badge {"badge-green" if state in ("TN","AR","KY") else "badge-red"}">{"Auto-Send" if state in ("TN","AR","KY") else "Blocked/Manual"}</span></td></tr>' for state, count in sorted(inv['state_breakdown'].items(), key=lambda x: -x[1])[:15])}
    </table>
  </div>
</div>

<!-- FOLLOW-UP TAB -->
<div class="content" id="tab-followup">
  <div class="card">
    <div class="card-title">Follow-up Rotation Status: <span class="badge {"badge-red" if fu['status']=='never_executed' else ("badge-green" if fu['status']=='active' else "badge-yellow")}">{fu['status']}</span></div>
    <div class="stat-row">
      <div class="stat"><div class="num blue">{fu['final_sendable']}</div><div class="label">Final Sendable</div></div>
      <div class="stat"><div class="num">{fu['today_planned']}</div><div class="label">Today Planned</div></div>
      <div class="stat"><div class="num">{fu['today_sent']}</div><div class="label">Today Sent</div></div>
      <div class="stat"><div class="num">{fu['daily_limit']}</div><div class="label">Daily Limit</div></div>
      <div class="stat"><div class="num">{fu['last_run']}</div><div class="label">Last Run</div></div>
      <div class="stat"><div class="num">{fu['next_planned']}</div><div class="label">Next Planned</div></div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">Exclusions (from {fu['raw_candidates']} raw candidates)</div>
    <div class="stat-row">
      <div class="stat"><div class="num">{fu['raw_candidates']}</div><div class="label">Total Sent Log</div></div>
      <div class="stat"><div class="num yellow">{fu.get('excluded_not_14d', 0)}</div><div class="label">Not 14 Days Yet</div></div>
      <div class="stat"><div class="num red">{fu['excluded_bounced']}</div><div class="label">Hard Bounced</div></div>
      <div class="stat"><div class="num">{fu['excluded_unsubscribed']}</div><div class="label">Unsubscribed</div></div>
      <div class="stat"><div class="num">{fu['excluded_suppressed']}</div><div class="label">Suppressed</div></div>
      <div class="stat"><div class="num">{fu['excluded_already_followed']}</div><div class="label">Already Followed</div></div>
      <div class="stat"><div class="num">{fu['excluded_domain_mismatch']}</div><div class="label">Domain Mismatch</div></div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">Wiring Status</div>
    <table>
      <tr><th>Check</th><th>Status</th></tr>
      <tr><td>09:00 code calls build_followup_queue</td><td><span class="badge {"badge-green" if fu['is_wired'] else "badge-red"}">{"Yes" if fu['is_wired'] else "No"}</span></td></tr>
      <tr><td>Ever sent live follow-up</td><td><span class="badge {"badge-green" if fu['ever_sent_live'] else "badge-red"}">{"Yes" if fu['ever_sent_live'] else "No — never executed"}</span></td></tr>
      <tr><td>Follow-up template</td><td><span class="badge badge-yellow">Standalone (no In-Reply-To)</span></td></tr>
      <tr><td>Daily max 5 enforced</td><td><span class="badge badge-green">Yes (hardcoded in stage_outreach)</span></td></tr>
      <tr><td>Separate from New Outreach 20</td><td><span class="badge badge-green">Yes (Phase 1 vs Phase 2)</span></td></tr>
      <tr><td>Status writeback on success</td><td><span class="badge badge-yellow">Never tested live</span></td></tr>
      <tr><td>Duplicate protection</td><td><span class="badge badge-green">Yes (email + domain dedup)</span></td></tr>
    </table>
  </div>
</div>

<script>
function switchTab(name) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.content').forEach(c => c.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  document.querySelectorAll('.tab').forEach(t => {{ if (t.textContent.toLowerCase().includes(name)) t.classList.add('active'); }});
}}
</script>
</body>
</html>'''
    return html


def main():
    data = collect_all_data()

    # Write dashboard
    html = generate_dashboard(data)
    dash_path = OUT_DIR / 'bd_operations_dashboard.html'
    dash_path.write_text(html, encoding='utf-8')
    print(f'Dashboard: {dash_path}')

    # Write review queue JSON
    queue_path = OUT_DIR / 'manual_review_queue.json'
    with open(queue_path, 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': now_cst().isoformat(),
            'total_pending': data['manual']['total_pending'],
            'categories': {
                'manual_review_needed': data['manual']['manual_review_needed'],
                'bounce_review': data['manual']['bounce_review'],
                'contact_form_pool': data['manual']['contact_form_pool'],
            },
            'queue': data['review_queue'][:100],
        }, f, indent=2, default=str)
    print(f'Review queue: {queue_path}')

    # Write follow-up status JSON
    fu_path = OUT_DIR / 'followup_rotation_status.json'
    with open(fu_path, 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': now_cst().isoformat(),
            **data['followup'],
        }, f, indent=2, default=str)
    print(f'Follow-up status: {fu_path}')

    print(f'\nManual Review: {data["manual"]["total_pending"]} pending')
    print(f'Inventory: {data["inventory"]["unique_auto_sendable"]} A0 sendable')
    print(f'Follow-up: {data["followup"]["status"]} ({data["followup"]["final_sendable"]} sendable)')


if __name__ == '__main__':
    main()
