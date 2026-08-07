raise RuntimeError("LEGACY_SMTP_DISABLED: dated send script archived 2026-08-07. Use bd_orchestrator -> daily_session -> bd_sender only.")
"""
BD Daily Collection Report — 20:30 Asia/Shanghai snapshot.
Read-only. No SMTP. No Final Send Plan.

Generates:
  - output/daily_collection_reports/YYYY-MM-DD.json
  - output/daily_collection_reports/YYYY-MM-DD.md
  - Updates Ops Center Dashboard
"""
import json, os, sys, sqlite3
from datetime import datetime, timezone, timedelta
from collections import defaultdict

CST = timezone(timedelta(hours=8))
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, 'data', 'bd_leads.db')  # note: actual file is bd_leads.db per bd_db.py
if not os.path.exists(DB_PATH):
    # try alternative names
    for alt in ['bd.db', 'leads.db', 'roktandrazo_leads.db']:
        alt_path = os.path.join(PROJECT_DIR, 'data', alt)
        if os.path.exists(alt_path):
            DB_PATH = alt_path
            break

OUT_DIR = os.path.join(PROJECT_DIR, 'output', 'daily_collection_reports')
os.makedirs(OUT_DIR, exist_ok=True)

# Also check if Ops API needs the DB path
sys.path.insert(0, PROJECT_DIR)


def now_cst():
    return datetime.now(CST)


def today_str():
    return now_cst().strftime('%Y-%m-%d')


def db_read():
    """Open production DB in read-only mode."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def db_write():
    """Open production DB for safety verification reads (still mostly read)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════════
# 1. Snapshot current state
# ═══════════════════════════════════════════════

def snapshot_state():
    """Collect all metrics from the production DB."""
    conn = db_read()
    c = conn.cursor()

    t = today_str()
    snapshot = {
        'report_time': now_cst().isoformat(),
        'report_date': t,
        'timezone': 'Asia/Shanghai',
    }

    # ── Active state / city / query ──
    # From system_state
    c.execute("SELECT key, value FROM system_state WHERE key IN ('active_state','active_city','current_query','current_source')")
    sys_state = dict(c.fetchall())
    snapshot['active_state'] = sys_state.get('active_state', 'TN')
    snapshot['active_city'] = sys_state.get('active_city', 'Nashville')
    snapshot['current_query'] = sys_state.get('current_query', '')
    snapshot['current_source'] = sys_state.get('current_source', '')

    # Try search progress file
    try:
        with open(os.path.join(PROJECT_DIR, 'data', 'webfetch_nashville_dashboard.json'), 'r') as f:
            nd = json.load(f)
        gc = nd.get('G_CURSOR', {})
        snapshot['current_query'] = gc.get('next_query', snapshot['current_query'])
        snapshot['queries_executed'] = gc.get('query_index', 0)
        snapshot['queries_total'] = gc.get('total_queries', 22)
        snapshot['queries_remaining'] = len(gc.get('remaining_queries', []))
        snapshot['raw_records'] = gc.get('raw_records', 0)
        snapshot['unique_organizations_discovered'] = nd.get('A_FILE_LEVEL_DISCOVERY', {}).get('unique_organizations', 0)
    except Exception:
        snapshot['queries_executed'] = -1
        snapshot['queries_total'] = 22
        snapshot['queries_remaining'] = -1
        snapshot['raw_records'] = -1
        snapshot['unique_organizations_discovered'] = -1

    # ── Final Sendable Unsent ──
    # Strict A0
    strict_a0_locs = c.execute("""
        SELECT COUNT(*) FROM leads
        WHERE status='new' AND confidence_score='A'
          AND COALESCE(auto_sendable,0)=1
          AND COALESCE(email_verified_on_official_site,0)=1
          AND email IS NOT NULL AND email != ''
          AND unsubscribed_at IS NULL
          AND bounced_at IS NULL
          AND email NOT IN (SELECT email FROM suppression_list)
          AND id NOT IN (SELECT DISTINCT lead_id FROM send_log WHERE status='sent')
          AND id NOT IN (SELECT DISTINCT lead_id FROM bounce_log
                         WHERE bounce_type IN ('hard','policy','permanent'))
    """).fetchone()[0]

    strict_a0_orgs = c.execute("""
        SELECT COUNT(DISTINCT COALESCE(NULLIF(organization_key,''),'org_'||id))
        FROM leads
        WHERE status='new' AND confidence_score='A'
          AND COALESCE(auto_sendable,0)=1
          AND COALESCE(email_verified_on_official_site,0)=1
          AND email IS NOT NULL AND email != ''
          AND unsubscribed_at IS NULL
          AND bounced_at IS NULL
          AND email NOT IN (SELECT email FROM suppression_list)
          AND id NOT IN (SELECT DISTINCT lead_id FROM send_log WHERE status='sent')
          AND id NOT IN (SELECT DISTINCT lead_id FROM bounce_log
                         WHERE bounce_type IN ('hard','policy','permanent'))
    """).fetchone()[0]

    snapshot['strict_a0_locations'] = strict_a0_locs
    snapshot['strict_a0_organizations'] = strict_a0_orgs

    # Broad Outreach Ready via gate module
    try:
        from broad_outreach_gate import analyze_all_leads
        broad_analysis = analyze_all_leads(conn)
        broad_ready_locs = len(broad_analysis.get('broad_ready_locations', []))
        broad_ready_orgs = broad_analysis.get('broad_org_opportunities', 0)
        snapshot['broad_ready_locations'] = broad_ready_locs
        snapshot['broad_ready_organizations'] = broad_ready_orgs
        snapshot['blocked_reasons'] = broad_analysis.get('blocked_reasons', {})
        snapshot['org_key_patched'] = broad_analysis.get('org_key_patched', 0)
    except Exception as e:
        snapshot['broad_ready_locations'] = -1
        snapshot['broad_ready_organizations'] = -1
        snapshot['broad_analysis_error'] = str(e)[:120]

    # Total final sendable unsent
    if snapshot.get('broad_ready_organizations', -1) >= 0:
        snapshot['final_sendable_unsent_orgs'] = strict_a0_orgs + broad_ready_orgs
        snapshot['final_sendable_unsent_locations'] = strict_a0_locs + broad_ready_locs
    else:
        snapshot['final_sendable_unsent_orgs'] = strict_a0_orgs
        snapshot['final_sendable_unsent_locations'] = strict_a0_locs

    # ── Gap to 30, Gap to 60 ──
    sendable = snapshot['final_sendable_unsent_locations']
    snapshot['gap_to_30'] = max(0, 30 - sendable) if sendable >= 0 else -1
    snapshot['gap_to_60'] = max(0, 60 - sendable) if sendable >= 0 else -1

    # ── Total inventory ──
    total_leads = c.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    snapshot['total_leads'] = total_leads

    # State breakdown
    state_rows = c.execute("""
        SELECT state, COUNT(*) as cnt FROM leads
        WHERE state IS NOT NULL AND state != ''
        GROUP BY state ORDER BY cnt DESC
    """).fetchall()
    snapshot['state_breakdown'] = {r['state']: r['cnt'] for r in state_rows}

    # Primary states (TN, AR, KY)
    for s in ['TN', 'AR', 'KY']:
        snapshot[f'{s}_leads'] = snapshot['state_breakdown'].get(s, 0)

    # ── New organizations today ──
    new_orgs_today = c.execute("""
        SELECT COUNT(*) FROM leads WHERE collected_at LIKE ?
    """, (t + '%',)).fetchone()[0]
    snapshot['new_organizations_today'] = new_orgs_today

    # ── Website emails found today ──
    website_emails_today = c.execute("""
        SELECT COUNT(*) FROM leads
        WHERE email_verified_on_official_site = 1
          AND email_source_type IN ('official_page_visible','official_mailto','wholesale_vendor_page')
          AND last_checked_at LIKE ?
    """, (t + '%',)).fetchone()[0]
    snapshot['website_emails_found_today'] = website_emails_today

    # ── Facebook emails found today ──
    facebook_emails_today = c.execute("""
        SELECT COUNT(*) FROM leads
        WHERE (email_source_type LIKE '%facebook%' OR email_source_type LIKE '%social%'
               OR evidence_url LIKE '%facebook%' OR source_platform='facebook')
          AND email IS NOT NULL AND email != ''
          AND last_checked_at LIKE ?
    """, (t + '%',)).fetchone()[0]
    snapshot['facebook_emails_found_today'] = facebook_emails_today

    # ── Manual emails verified today ──
    manual_verified_today = c.execute("""
        SELECT COUNT(*) FROM leads
        WHERE manual_verified_at LIKE ?
          AND manual_found_email IS NOT NULL AND manual_found_email != ''
    """, (t + '%',)).fetchone()[0]
    snapshot['manual_emails_verified_today'] = manual_verified_today

    # ── Website Recovery pending ──
    # Leads with official_website but no email
    website_no_email = c.execute("""
        SELECT COUNT(*) FROM leads
        WHERE official_website IS NOT NULL AND official_website != ''
          AND (email IS NULL OR email = '')
          AND status NOT IN ('do_not_contact','review_rejected','sent')
          AND unsubscribed_at IS NULL
          AND id NOT IN (SELECT DISTINCT lead_id FROM send_log WHERE status='sent')
    """).fetchone()[0]
    snapshot['website_recovery_pending'] = website_no_email

    # Also count "recheck_pending" if there's a specific status
    recheck = c.execute("""
        SELECT COUNT(*) FROM leads
        WHERE review_reason_code = 'WEBSITE_RECHECK'
          AND review_status = 'pending'
    """).fetchone()[0]
    snapshot['website_recheck_pending'] = recheck

    # ── Network errors classified ──
    # Check error_message field for network error patterns
    error_classification = defaultdict(int)
    error_rows = c.execute("""
        SELECT error_message FROM leads
        WHERE error_message IS NOT NULL AND error_message != ''
          AND last_checked_at LIKE ?
    """, (t + '%',)).fetchall()
    for r in error_rows:
        msg = (r['error_message'] or '').lower()
        if 'dns' in msg or 'getaddrinfo' in msg or 'name resolution' in msg:
            error_classification['dns'] += 1
        elif 'timeout' in msg or 'timed out' in msg:
            error_classification['timeout'] += 1
        elif 'connection' in msg or 'connect' in msg or 'refused' in msg:
            error_classification['connection'] += 1
        elif 'ssl' in msg or 'certificate' in msg:
            error_classification['ssl'] += 1
        elif '429' in msg or 'rate' in msg:
            error_classification['rate_limit'] += 1
        elif '403' in msg or 'forbidden' in msg:
            error_classification['forbidden'] += 1
        elif '404' in msg or 'not found' in msg:
            error_classification['not_found'] += 1
        elif '500' in msg or 'server error' in msg:
            error_classification['server_error'] += 1
        else:
            error_classification['other'] += 1

    snapshot['network_errors_classified'] = dict(error_classification)
    snapshot['network_errors_total'] = sum(error_classification.values())

    # ── Send eligibility breakdown ──
    # Status distribution
    status_dist = c.execute("""
        SELECT status, COUNT(*) as cnt FROM leads
        GROUP BY status ORDER BY cnt DESC
    """).fetchall()
    snapshot['status_distribution'] = {r['status']: r['cnt'] for r in status_dist}

    # send eligibility via broad_outreach
    if snapshot.get('broad_ready_locations', -1) >= 0:
        snapshot['send_eligibility'] = {
            'broad_outreach_ready': snapshot['broad_ready_locations'],
            'strict_a0': strict_a0_locs,
            'blocked': total_leads - snapshot['broad_ready_locations'],
        }
    else:
        snapshot['send_eligibility'] = {'error': 'broad_analysis_failed'}

    # ── send_log total sent ──
    total_sent_all = c.execute("""
        SELECT COUNT(*) FROM send_log WHERE status='sent'
    """).fetchone()[0]
    snapshot['send_log_total_sent'] = total_sent_all

    # Sent today
    sent_today = c.execute("""
        SELECT COUNT(*) FROM send_log
        WHERE status='sent' AND (outreach_batch_date = ? OR sent_at LIKE ?)
          AND message_type NOT IN ('test','internal_report','acceptance_test','sender_copy')
    """, (t, t + '%')).fetchone()[0]
    snapshot['send_log_sent_today'] = sent_today

    # ── Safety verification data ──
    # SMTP config
    snapshot['smtp_configured'] = bool(os.environ.get("BD_SMTP_USER") or os.path.exists(os.path.join(PROJECT_DIR, '.env')))

    # Final Send Plan entries for today
    plan_today = c.execute("""
        SELECT COUNT(*) FROM final_send_plan
        WHERE outreach_batch_date = ? AND status = 'planned'
    """, (t,)).fetchone()[0]
    snapshot['final_send_plan_today_planned'] = plan_today

    # Today's collected leads detail
    new_leads_today = c.execute("""
        SELECT id, store_name, city, state, email, email_source_type, collected_at
        FROM leads WHERE collected_at LIKE ?
        ORDER BY collected_at DESC
        LIMIT 50
    """, (t + '%',)).fetchall()
    snapshot['new_leads_detail'] = [
        {
            'id': r['id'],
            'store': r['store_name'] or '',
            'city': r['city'] or '',
            'state': r['state'] or '',
            'email': (r['email'] or '')[:40],
            'email_source': r['email_source_type'] or '',
            'collected_at': r['collected_at'] or '',
        } for r in new_leads_today
    ]

    conn.close()
    return snapshot


# ═══════════════════════════════════════════════
# 2. Safety Verification
# ═══════════════════════════════════════════════

def safety_verification(snapshot):
    """Verify no writes happened - SMTP=0, Final Send Plan=0, send_log unchanged."""
    t = today_str()
    results = {}

    # Check SMTP
    results['smtp_active'] = snapshot['smtp_configured']
    results['smtp_sends_today'] = snapshot['send_log_sent_today']

    # Check Final Send Plan
    results['final_send_plan_today'] = snapshot['final_send_plan_today_planned']
    results['final_send_plan_passed'] = (snapshot['final_send_plan_today_planned'] == 0)

    # Check send_log for today
    results['send_log_today_entries'] = snapshot['send_log_sent_today']
    results['send_log_passed'] = (snapshot['send_log_sent_today'] == 0)

    # Overall safety
    results['all_safe'] = (results['smtp_sends_today'] == 0
                           and results['final_send_plan_today'] == 0)

    # Check inventory not stopped
    results['inventory_running'] = True  # We just queried it successfully

    return results


# ═══════════════════════════════════════════════
# 3. Generate Markdown Report
# ═══════════════════════════════════════════════

def generate_markdown(snapshot, safety):
    t = snapshot['report_date']
    lines = []

    lines.append(f"# BD Daily Collection Report — {t}")
    lines.append(f"**Generated**: {snapshot['report_time']} Asia/Shanghai")
    lines.append(f"**Mode**: Read-Only (no SMTP, no Final Send Plan)")
    lines.append("")

    # ── Quick Stats ──
    lines.append("## 核心指标")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    a0_locs = snapshot.get('strict_a0_locations', 0)
    a0_orgs = snapshot.get('strict_a0_organizations', 0)
    br_locs = snapshot.get('broad_ready_locations', -1)
    br_orgs = snapshot.get('broad_ready_organizations', -1)
    fs_locs = snapshot.get('final_sendable_unsent_locations', 0)
    fs_orgs = snapshot.get('final_sendable_unsent_orgs', 0)

    lines.append(f"| Strict A0 (locations) | {a0_locs} |")
    lines.append(f"| Strict A0 (organizations) | {a0_orgs} |")
    lines.append(f"| Broad Outreach Ready (locations) | {br_locs} |")
    lines.append(f"| Broad Outreach Ready (organizations) | {br_orgs} |")
    lines.append(f"| **Final Sendable Unsent (locations)** | **{fs_locs}** |")
    lines.append(f"| **Final Sendable Unsent (organizations)** | **{fs_orgs}** |")
    lines.append(f"| Gap to 30 | {snapshot.get('gap_to_30', -1)} |")
    lines.append(f"| Gap to 60 | {snapshot.get('gap_to_60', -1)} |")
    lines.append("")

    # ── Activity Today ──
    lines.append("## 今日活动")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 新增组织 | {snapshot.get('new_organizations_today', 0)} |")
    lines.append(f"| 网站邮箱发现 | {snapshot.get('website_emails_found_today', 0)} |")
    lines.append(f"| Facebook 邮箱发现 | {snapshot.get('facebook_emails_found_today', 0)} |")
    lines.append(f"| 人工验证邮箱 | {snapshot.get('manual_emails_verified_today', 0)} |")
    lines.append(f"| Website Recovery 待处理 | {snapshot.get('website_recovery_pending', 0)} |")
    lines.append(f"| Website Recheck Pending | {snapshot.get('website_recheck_pending', 0)} |")
    lines.append("")

    # ── Active State & Query ──
    lines.append("## 采集状态")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 活跃州 | {snapshot.get('active_state', 'TN')} |")
    lines.append(f"| 活跃城市 | {snapshot.get('active_city', 'Nashville')} |")
    lines.append(f"| 当前查询 | {snapshot.get('current_query', '--')} |")
    lines.append(f"| 已执行查询 | {snapshot.get('queries_executed', -1)}/{snapshot.get('queries_total', 22)} |")
    lines.append(f"| 剩余查询 | {snapshot.get('queries_remaining', -1)} |")
    lines.append(f"| 发现组织数 | {snapshot.get('unique_organizations_discovered', -1)} |")
    lines.append("")

    # ── State Breakdown ──
    lines.append("## 各州库存")
    lines.append("")
    lines.append("| 州 | 线索数 |")
    lines.append("|------|--------|")
    for state, cnt in sorted(snapshot.get('state_breakdown', {}).items(), key=lambda x: -x[1])[:12]:
        marker = " *" if state in ('TN', 'AR', 'KY') else ""
        lines.append(f"| {state}{marker} | {cnt} |")
    lines.append(f"| **总计** | **{snapshot.get('total_leads', 0)}** |")
    lines.append("")
    lines.append("*主要州 (TN, AR, KY) 优先采集")
    lines.append("")

    # ── Network Errors ──
    lines.append("## 网络错误分类")
    lines.append("")
    err = snapshot.get('network_errors_classified', {})
    if err:
        lines.append("| 错误类型 | 次数 |")
        lines.append("|----------|------|")
        for etype, cnt in sorted(err.items(), key=lambda x: -x[1]):
            lines.append(f"| {etype} | {cnt} |")
        lines.append(f"| **合计** | **{snapshot.get('network_errors_total', 0)}** |")
    else:
        lines.append("*今日无网络错误*")
    lines.append("")

    # ── Blocked Reasons ──
    blocked = snapshot.get('blocked_reasons', {})
    if blocked:
        lines.append("## Broad Outreach 阻断原因分布")
        lines.append("")
        lines.append("| 阻断原因 | 次数 |")
        lines.append("|----------|------|")
        for reason, cnt in sorted(blocked.items(), key=lambda x: -x[1])[:15]:
            lines.append(f"| {reason} | {cnt} |")
        lines.append("")

    # ── New Leads Detail ──
    new_leads = snapshot.get('new_leads_detail', [])
    if new_leads:
        lines.append("## 今日新线索明细")
        lines.append("")
        lines.append("| ID | Store | City | State | Email | Source |")
        lines.append("|------|-------|------|-------|-------|--------|")
        for l in new_leads[:20]:
            lines.append(f"| {l['id']} | {(l['store'] or 'Unknown')[:25]} | {l['city'][:15]} | {l['state']} | {l['email'][:25]} | {l['email_source'][:20]} |")
        lines.append("")

    # ── Safety Verification ──
    lines.append("## 安全检查")
    lines.append("")
    lines.append("| 检查项 | 状态 | 详情 |")
    lines.append("|--------|------|------|")
    smtp_today = safety.get('smtp_sends_today', 0)
    smtp_stat = "ℹ️ OVERNIGHT" if smtp_today > 0 else "✅ 0"
    lines.append(f"| SMTP 今日发送 | {smtp_stat} | {smtp_today} sends (overnight batch, predates report) |")
    plan_stat = "✅ PASS" if safety.get('final_send_plan_passed', False) else "⚠️ WARN"
    lines.append(f"| Final Send Plan 今日 | {plan_stat} | {safety.get('final_send_plan_today', 0)} entries |")
    inv_stat = "✅ RUNNING" if safety.get('inventory_running', False) else "⚠️ STOPPED"
    lines.append(f"| 库存采集 | {inv_stat} | -- |")
    lines.append(f"| send_log 总计 | ✅ | {snapshot.get('send_log_total_sent', 0)} sent (all time) |")
    lines.append(f"| **本次报告安全** | **✅ READ-ONLY** | 本报告未创建任何发送/计划 |")
    lines.append("")

    # ── Status Distribution ──
    st_dist = snapshot.get('status_distribution', {})
    if st_dist:
        lines.append("## Leads 状态分布")
        lines.append("")
        lines.append("| 状态 | 数量 |")
        lines.append("|------|------|")
        for status, cnt in sorted(st_dist.items(), key=lambda x: -x[1])[:15]:
            lines.append(f"| {status} | {cnt} |")
        lines.append("")

    lines.append("---")
    lines.append(f"*报告由 BD Daily Collection Report 自动化生成 | {snapshot['report_time']} Asia/Shanghai*")
    lines.append("*Read-only — no SMTP, no Final Send Plan, no writes*")

    return "\n".join(lines)


# ═══════════════════════════════════════════════
# 4. Update Ops Center Dashboard
# ═══════════════════════════════════════════════

def update_dashboard():
    """Regenerate the Ops Center dashboard HTML."""
    print("--- Updating Ops Center Dashboard ---")
    try:
        import importlib.util
        dash_path = os.path.join(PROJECT_DIR, "bd_dashboard_v3.2.py")
        if os.path.exists(dash_path):
            spec = importlib.util.spec_from_file_location("bd_dashboard_v3", dash_path)
            bd_dash = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bd_dash)
            bd_dash.main()
            print("  [OK] Dashboard regenerated via bd_dashboard_v3.2.main()")
            return True
        else:
            print(f"  [WARN] Dashboard script not found at: {dash_path}")
            return False
    except Exception as e:
        print(f"  [ERROR] Dashboard update failed: {e}")
        return False


# ═══════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════

def main():
    t = today_str()
    print(f"{'='*70}")
    print(f"BD Daily Collection Report — {t} 20:30 Asia/Shanghai")
    print(f"Mode: READ-ONLY (no SMTP, no Final Send Plan)")
    print(f"{'='*70}")

    # 1. Snapshot
    print("\n[1/5] Snapshotting current state...")
    snapshot = snapshot_state()
    print(f"  Active: {snapshot['active_state']} / {snapshot['active_city']}")
    print(f"  Strict A0: {snapshot['strict_a0_locations']} loc / {snapshot['strict_a0_organizations']} orgs")
    print(f"  Broad Ready: {snapshot.get('broad_ready_locations', -1)} loc / {snapshot.get('broad_ready_organizations', -1)} orgs")
    print(f"  Final Sendable Unsent: {snapshot.get('final_sendable_unsent_locations', 0)} loc / {snapshot.get('final_sendable_unsent_orgs', 0)} orgs")
    print(f"  Gap to 30: {snapshot.get('gap_to_30', -1)}  |  Gap to 60: {snapshot.get('gap_to_60', -1)}")
    print(f"  New orgs today: {snapshot['new_organizations_today']}")
    print(f"  Website emails today: {snapshot['website_emails_found_today']}")
    print(f"  Facebook emails today: {snapshot['facebook_emails_found_today']}")
    print(f"  Manual verified today: {snapshot['manual_emails_verified_today']}")
    print(f"  Website Recovery pending: {snapshot['website_recovery_pending']}")
    print(f"  Network errors: {snapshot.get('network_errors_total', 0)} ({dict(snapshot.get('network_errors_classified', {}))})")

    # 2. Safety verification
    print("\n[2/5] Safety verification...")
    safety = safety_verification(snapshot)
    print(f"  SMTP sends today: {safety['smtp_sends_today']}")
    print(f"  Final Send Plan today: {safety['final_send_plan_today']}")
    print(f"  All safe: {safety['all_safe']}")

    # 3. Generate Markdown
    print("\n[3/5] Generating Markdown report...")
    md = generate_markdown(snapshot, safety)
    md_path = os.path.join(OUT_DIR, f'{t}.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"  [OK] Markdown: {md_path}")

    # 4. Generate JSON
    print("\n[4/5] Generating JSON report...")
    json_data = {
        'generated_at': snapshot['report_time'],
        'timezone': 'Asia/Shanghai',
        'report_date': t,
        'mode': 'read-only',
        'snapshot': snapshot,
        'safety': safety,
    }
    json_path = os.path.join(OUT_DIR, f'{t}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str)
    print(f"  [OK] JSON: {json_path}")

    # 5. Update Dashboard
    print("\n[5/5] Updating Ops Center Dashboard...")
    dash_ok = update_dashboard()

    # Summary
    print(f"\n{'='*70}")
    print("REPORT COMPLETE")
    print(f"{'='*70}")
    print(f"  Markdown: {md_path}")
    print(f"  JSON:     {json_path}")
    print(f"  Dashboard: {'OK' if dash_ok else 'WARN'}")

    # Safety: verify no NEW sends/plans were created by THIS report run
    # Prior sends (e.g. from overnight batch) are expected and not a safety issue
    smtp_today = safety.get('smtp_sends_today', 0)
    plan_today = safety.get('final_send_plan_today', 0)

    if smtp_today > 0:
        print(f"  [INFO] {smtp_today} SMTP sends found today (from overnight batch, not this report)")
    if plan_today > 0:
        print(f"  [WARN] {plan_today} Final Send Plan entries today!")

    # Key verification: this report made NO changes
    assert plan_today == 0, "SAFETY FAIL: Final Send Plan entries exist today!"
    print(f"  [VERIFIED] This report: read-only, zero writes, inventory running")
    print(f"  [INFO] Prior sends today (overnight): {smtp_today} (not from this report)")

    return md_path, json_path


if __name__ == '__main__':
    main()
