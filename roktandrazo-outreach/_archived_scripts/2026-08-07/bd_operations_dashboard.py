"""BD Operations Dashboard v2 — single rolling HTML, real-data driven.

Fixes:
  - Real send_log fields (message_id, template_id, customer_type, etc.)
  - Asia/Shanghai timezone
  - HTML escaping
  - Read-only DB connections
  - Monthly archive uses old file's data (bug fix)
  - Dynamic anomalies, not hardcoded
  - Retail A0 + Custom A0 split
  - Atomic archive writes
"""
from __future__ import annotations
raise RuntimeError("LEGACY_DASHBOARD_ARCHIVED: use bd_dashboard_v3.2 + bd_review_server")

import html as html_mod
import json
import os
import re
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from outreach_control import INVENTORY_TARGET, NEW_OUTREACH_TARGET, outreach_batch_date
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_HTML = PROJECT_DIR / "output" / "bd_operations_dashboard.html"
OUTPUT_JSON = PROJECT_DIR / "output" / "latest_operations_report.json"
ARCHIVE_DIR = PROJECT_DIR / "output" / "report_archive"
MONTHLY_DIR = PROJECT_DIR / "output" / "report_monthly"
DB_PATH = PROJECT_DIR / "data" / "bd_leads.db"
SHANGHAI_OFFSET = timedelta(hours=8)
SHANGHAI_TZ = timezone(SHANGHAI_OFFSET)


def _mask_email(email_addr: str) -> str:
    if "@" not in email_addr:
        return "***"
    local, domain = email_addr.rsplit("@", 1)
    return f"{local[:3]}***@{domain}"


def _db_readonly():
    return sqlite3.connect(f"file:{DB_PATH.resolve().as_posix()}?mode=ro", uri=True)


def _safe_str(val: str | None) -> str:
    return html_mod.escape(str(val or ""))


def _today_range():
    """Return (start_utc_iso, end_utc_iso) for today Asia/Shanghai."""
    now_sh = datetime.now(timezone.utc) + SHANGHAI_OFFSET
    start_sh = now_sh.replace(hour=0, minute=0, second=0, microsecond=0)
    end_sh = start_sh + timedelta(days=1)
    start_utc = (start_sh - SHANGHAI_OFFSET).isoformat()
    end_utc = (end_sh - SHANGHAI_OFFSET).isoformat()
    return start_utc, end_utc


def gather_data() -> dict:
    start_utc, end_utc = _today_range()
    source_health = {"database": True, "inbox": True, "followup": True, "coverage": True}

    conn = _db_readonly()
    conn.row_factory = sqlite3.Row
    now_sh = datetime.now(timezone.utc) + SHANGHAI_OFFSET
    today_str = outreach_batch_date(now_sh)
    post_send_row = conn.execute("""
        SELECT status FROM job_runs WHERE stage='post-send' AND business_date=?
        ORDER BY started_at DESC LIMIT 1
    """, (today_str,)).fetchone()
    post_send_state = post_send_row['status'] if post_send_row else 'stage_not_run'

    # ── Send stats ──
    send_rows = conn.execute("""
        SELECT sl.sent_at, sl.lead_id, sl.email, sl.subject, sl.status,
               sl.message_id, sl.template_id, sl.customer_type, sl.routing_reason,
               sl.batch_id, sl.source_platform,
               l.store_name, l.city, l.state, l.store_type
        FROM send_log sl JOIN leads l ON sl.lead_id = l.id
        WHERE sl.outreach_batch_date = ? AND sl.message_type = 'new_outreach' AND sl.status = 'sent'
        ORDER BY sl.sent_at
    """, (today_str,)).fetchall()

    sent_today = len(send_rows)

    # Counts from real data
    hybrid_count = 0
    custom_count = 0
    legacy_count = 0
    msg_id_present = 0
    msg_id_missing = 0

    send_list = []
    states_map = {}
    city_map = {}
    ctype_map = {}
    platform_map = {}
    batch_map = {}

    for r in send_rows:
        template = (r["template_id"] or "")
        if template == "hybrid_wholesale_custom_v1":
            hybrid_count += 1
        elif template == "custom_production_v1":
            custom_count += 1
        else:
            legacy_count += 1

        mid = r["message_id"] or ""
        if mid:
            msg_id_present += 1
        else:
            msg_id_missing += 1

        store = r["store_name"] or ""
        city = r["city"] or "Online"
        state = r["state"] or ""
        ctype = r["customer_type"] or r["store_type"] or "retail_store"
        platform = r["source_platform"] or "Website"

        states_map[state] = states_map.get(state, 0) + 1
        city_key = f"{state}|{city}"
        city_map[city_key] = city_map.get(city_key, 0) + 1
        ctype_map[ctype] = ctype_map.get(ctype, 0) + 1
        platform_map[platform] = platform_map.get(platform, 0) + 1
        batch_map[r["batch_id"] or "—"] = batch_map.get(r["batch_id"] or "—", 0) + 1

        send_list.append({
            "time": (r["sent_at"] or "")[-8:] if r["sent_at"] else "",
            "store": store, "city": city, "state": state,
            "type": ctype, "template": template or "legacy_template_unknown",
            "email": _mask_email(r["email"] or ""),
            "msg_id": (mid[:40] + "…") if len(mid) > 40 else (mid or "historical_unavailable"),
            "batch": r["batch_id"] or "—",
            "platform": platform,
            "reason": (r["routing_reason"] or "")[:50],
            "status": r["status"] or "",
        })

    # ── A0 pools ──
    retail_a0 = conn.execute("""
        SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A'
        AND state IN ('TN','AR','KY') AND email_verified_on_official_site=1
        AND email IS NOT NULL AND email !=''
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN('sent','bounced'))
    """).fetchone()[0]

    custom_a0 = conn.execute("""
        SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A'
        AND email_verified_on_official_site=1
        AND email IS NOT NULL AND email !=''
        AND store_type IN ('online_brand','crowdfunding','independent_creator')
        AND email NOT IN (SELECT email FROM suppression_list)
        AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN('sent','bounced'))
    """).fetchone()[0]

    total_a0 = retail_a0 + custom_a0
    afternoon_gap = max(0, 60 - total_a0)

    # ── Manual review: all counts are derived from persisted lead/review records. ──
    review = {key: 0 for key in (
        'pending_manual_review', 'b1_social_verified', 'b2_review', 'contact_form',
        'review_recovery', 'deferred', 'approved_auto', 'approved_manual', 'rejected',
        'recheck_pending', 'reviewed_today', 'a0_created_after_review',
    )}
    try:
        rows = conn.execute("""
            SELECT COALESCE(review_status, 'pending') AS review_status,
                   COALESCE(review_reason_code, '') AS reason_code,
                   COALESCE(status, '') AS lead_status, COUNT(*) AS cnt
            FROM leads GROUP BY review_status, reason_code, lead_status
        """).fetchall()
        for row in rows:
            status, code, lead_status, count = row['review_status'], row['reason_code'], row['lead_status'], row['cnt']
            if status == 'pending': review['pending_manual_review'] += count
            if status == 'deferred': review['deferred'] += count
            if status == 'approved_auto': review['approved_auto'] += count
            if status == 'approved_manual': review['approved_manual'] += count
            if status == 'rejected': review['rejected'] += count
            if status == 'recheck_pending': review['recheck_pending'] += count
            if code in {'B1_SOCIAL_VERIFIED', 'SOCIAL_VERIFIED'} or 'FACEBOOK' in code: review['b1_social_verified'] += count
            if code.startswith('B2') or lead_status in {'manual_review_needed', 'bounce_review'}: review['b2_review'] += count
            if code == 'CONTACT_FORM_ONLY' or lead_status == 'contact_form_pool': review['contact_form'] += count
            if 'RECOVERY' in code: review['review_recovery'] += count
        review['reviewed_today'] = conn.execute("""
            SELECT COUNT(*) FROM review_log WHERE date(reviewed_at) = date(?)
        """, (now_sh.isoformat(),)).fetchone()[0]
        review['a0_created_after_review'] = conn.execute("""
            SELECT COUNT(*) FROM review_log WHERE decision='approve_auto'
              AND date(reviewed_at) = date(?) AND whether_auto_sendable=1
        """, (now_sh.isoformat(),)).fetchone()[0]
    except sqlite3.Error:
        source_health['database'] = False

    # ── Follow-up ──
    fu = {"raw": 0, "hygiene": 0, "final": 0, "planned": 0, "sent": 0}
    fu_path = PROJECT_DIR / "output" / "followup_queue_14d.json"
    if fu_path.exists():
        try:
            fu_data = json.loads(fu_path.read_text())
            fu["raw"] = fu_data.get("raw_candidate_count", 0)
            fu["hygiene"] = fu_data.get("hygiene_pass_count", 0)
            fu["final"] = fu_data.get("final_sendable_count", 0)
            fu["planned"] = min(5, fu["final"])
        except Exception as e:
            source_health["followup"] = False

    # follow-up sent today
    fu["sent"] = conn.execute("""
        SELECT COUNT(*) FROM send_log WHERE message_type='follow_up' AND outreach_batch_date=? AND status='sent'
    """, (today_str,)).fetchone()[0]

    # ── Inbox ──
    inbox = {"normal_reply": 0, "hot_reply": 0, "auto_reply": 0, "ignored_platform": 0,
             "hard_bounce": 0, "soft_bounce": 0, "unsubscribe": 0,
             "stop_required": False, "stop_reasons": [], "source_ok": True}
    poll_path = PROJECT_DIR / "output" / "inbox_poll_result.json"
    if poll_path.exists():
        try:
            p = json.loads(poll_path.read_text()).get("poll", {})
            for k in inbox:
                if k in p:
                    inbox[k] = p[k]
        except Exception:
            source_health["inbox"] = False
    else:
        source_health["inbox"] = False

    # ── Coverage ──
    cov = {"states_covered": 0, "cities_searched": 0, "cities_pending": 0, "cities": [], "platforms": []}
    cov_path = PROJECT_DIR / "output" / "search_coverage_registry.json"
    if cov_path.exists():
        try:
            cov_data = json.loads(cov_path.read_text())
            cov["states_covered"] = cov_data.get("stats", {}).get("states_covered", 0)
            cov["cities_searched"] = cov_data.get("stats", {}).get("cities_searched", 0)
            cov["cities_pending"] = cov_data.get("stats", {}).get("cities_pending", 0)
            cov["cities"] = cov_data.get("cities", [])[:50]
            cov["platforms"] = cov_data.get("platforms", [])
        except Exception:
            source_health["coverage"] = False
    else:
        source_health["coverage"] = False

    conn.close()

    # ── Anomalies ──
    anomalies = []
    if sent_today < NEW_OUTREACH_TARGET:
        anomalies.append(f"今日新开发 {sent_today}/{NEW_OUTREACH_TARGET} — 未达日标")
    if msg_id_missing > 0:
        anomalies.append(f"Message-ID 缺失: {msg_id_missing}/{sent_today} 封")
    if legacy_count > 0:
        anomalies.append(f"模板未记录: {legacy_count}/{sent_today} 封 (legacy)")
    if total_a0 < INVENTORY_TARGET:
        anomalies.append(f"Strict A0 库存不足: {total_a0} (目标 {INVENTORY_TARGET})")
    if not source_health["inbox"]:
        anomalies.append("Inbox 数据过期或无结果")
    if not source_health["followup"]:
        anomalies.append("Follow-up 队列数据异常")
    if not source_health["coverage"]:
        anomalies.append("Coverage registry 数据异常")

    followup_sent = fu["sent"]

    return {
        "generated_at": now_sh.isoformat(),
        "today": today_str,
        "timezone": "Asia/Shanghai",
        "sent_today": sent_today,
        "daily_target": NEW_OUTREACH_TARGET,
        "remaining": max(0, NEW_OUTREACH_TARGET - sent_today),
        "hybrid_count": hybrid_count,
        "custom_count": custom_count,
        "legacy_count": legacy_count,
        "followup_sent": followup_sent,
        "followup_planned": fu["planned"],
        "replies": inbox["normal_reply"] + inbox["hot_reply"],
        "hard_bounce": inbox["hard_bounce"],
        "unsubscribe": inbox["unsubscribe"],
        "msg_id_present": msg_id_present,
        "msg_id_missing": msg_id_missing,
        "retail_a0": retail_a0,
        "custom_a0": custom_a0,
        "total_a0": total_a0,
        "afternoon_target": 60,
        "afternoon_gap": afternoon_gap,
        "today_complete": sent_today >= NEW_OUTREACH_TARGET,
        "post_send_state": post_send_state,
        "review": review,
        "inbox": inbox,
        "followup": fu,
        "coverage": cov,
        "source_health": source_health,
        "state_detail": {k: v for k, v in sorted(states_map.items(), key=lambda x: -x[1])},
        "city_detail": [{"key": k, "count": v} for k, v in sorted(city_map.items(), key=lambda x: -x[1])],
        "ctype_detail": ctype_map,
        "platform_detail": platform_map,
        "batch_detail": batch_map,
        "send_list": send_list,
        "anomalies": anomalies,
    }


def render_html(data: dict) -> str:
    d = data
    cov = d["coverage"]

    # City table
    city_rows = ""
    for c in cov.get("cities", [])[:40]:
        status_raw = c.get("search_status", "?")
        status_map = {"complete": "✅ 完成", "pending": "⏳ 待搜索", "dry_run": "📋 试运行",
                      "partial": "⚠ 部分", "blocked": "🚫 暂停",
                      "historical_data_unavailable": "📂 历史未记录"}
        st_label = status_map.get(status_raw, _safe_str(status_raw))
        city_rows += f"""<tr>
            <td>{_safe_str(c.get('state',''))}</td><td>{_safe_str(c.get('city',''))}</td>
            <td>{c.get('candidates_found',0)}</td><td>{c.get('official_sites_found',0)}</td>
            <td>{c.get('emails_found',0)}</td><td>{c.get('hygiene_passed',0)}</td>
            <td>{c.get('leads_added',0)}</td><td>{st_label}</td></tr>"""

    # Platform table
    plat_rows = ""
    for p in cov.get("platforms", [])[:10]:
        status_raw = p.get("search_status", "planned_not_started")
        status_label = "已规划，尚未开始" if status_raw == "planned_not_started" else _safe_str(status_raw)
        plat_rows += f"""<tr>
            <td>{_safe_str(p.get('platform',''))}</td><td>{_safe_str(p.get('category',''))}</td>
            <td>{p.get('candidates_found',0)}</td><td>{p.get('own_brand_verified',0)}</td>
            <td>{p.get('non_cn_verified',0)}</td><td>{p.get('official_sites_found',0)}</td>
            <td>{status_label}</td></tr>"""

    # Send detail table
    send_rows = ""
    for s in d["send_list"][:30]:
        send_rows += f"""<tr>
            <td>{_safe_str(s['time'])}</td><td>{_safe_str(s['store'])}</td>
            <td>{_safe_str(s['city'])}</td><td>{_safe_str(s['state'])}</td>
            <td>{_safe_str(s['type'])}</td><td>{_safe_str(s['template'])}</td>
            <td class=\"em\">{_safe_str(s['email'])}</td>
            <td class=\"msgid\">{_safe_str(s['msg_id'])}</td>
            <td>{_safe_str(s['status'])}</td></tr>"""

    # State detail
    state_rows = "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>"
        for k, v in sorted(d.get("state_detail", {}).items(), key=lambda x: -x[1])
    )

    # Anomalies
    anomaly_html = ""
    for a in d.get("anomalies", []):
        anomaly_html += f'<div class="anomaly">⚠ {_safe_str(a)}</div>'
    if not anomaly_html:
        anomaly_html = '<div style="color:#27ae60;padding:8px">✓ 无异常</div>'

    sh = d.get("source_health", {})
    health_html = "".join(
        f"<span style=\"{'color:#27ae60' if v else 'color:#e74c3c'}\">{k}: {'✓' if v else '✗'}</span> "
        for k, v in sh.items()
    )

    tab_count = 6  # send, city, platform, followup, inbox, anomalies

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>BD Dashboard | rokt&razo</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;color:#333;padding:20px;font-size:14px}}
.c{{max-width:1240px;margin:0 auto}}
h1{{font-size:22px;margin-bottom:4px}}
.sub{{color:#888;font-size:12px;margin-bottom:16px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;margin-bottom:20px}}
.card{{background:#fff;border-radius:8px;padding:12px 14px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.card .n{{font-size:24px;font-weight:700}}
.card .l{{font-size:10px;color:#888;margin-top:2px}}
.card.warn .n{{color:#e67e22}}.card.ok .n{{color:#27ae60}}.card.info .n{{color:#1a73e8}}.card.danger .n{{color:#e74c3c}}
.tabs{{display:flex;gap:0}}
.tab{{padding:10px 16px;background:#e0e0e0;border-radius:8px 8px 0 0;cursor:pointer;font-size:13px;font-weight:500;color:#666;border:none}}
.tab.active{{background:#fff;color:#333}}
.content{{background:#fff;border-radius:0 8px 8px 8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.06);min-height:300px}}
.section{{display:none}}.section.active{{display:block}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{background:#fafafa;text-align:left;padding:8px 10px;font-size:11px;color:#999;border-bottom:1px solid #eee;white-space:nowrap}}
td{{padding:7px 10px;border-bottom:1px solid #f2f2f2}}
td.em{{font-family:monospace;font-size:11px;color:#1a73e8}}
td.msgid{{font-family:monospace;font-size:10px;color:#888;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
tr:hover{{background:#f8f9ff}}
.anomaly{{background:#fef3e0;color:#c06000;padding:8px 12px;border-radius:4px;margin:4px 0;font-size:12px}}
.footer{{text-align:center;color:#bbb;font-size:11px;padding:20px 0}}
h3{{font-size:15px;margin-bottom:12px;color:#555}}
.env{{background:#fafafa;padding:8px 12px;border-radius:4px;font-size:11px;margin-bottom:12px}}
</style></head>
<body><div class="c">
<h1>BD Operations Dashboard</h1>
<p class="sub">生成: {d['generated_at'][:19]} ({d['timezone']}) · 日期: {d['today']} · Tab 数量: {tab_count} · 数据源: {health_html}</p>

<div class="cards">
<div class="card info"><div class="n">{d['daily_target']}</div><div class="l">今日新开发目标</div></div>
<div class="card {'ok' if d['sent_today']>=20 else 'warn'}"><div class="n">{d['sent_today']}</div><div class="l">今日已发送</div></div>
<div class="card"><div class="n">{d['remaining']}</div><div class="l">今日剩余</div></div>
<div class="card"><div class="n">{d['hybrid_count']}</div><div class="l">Hybrid</div></div>
<div class="card"><div class="n">{d['custom_count']}</div><div class="l">Custom Prod</div></div>
<div class="card"><div class="n">{d['followup_sent']}</div><div class="l">Follow-up已发</div></div>
<div class="card"><div class="n">{d['replies']}</div><div class="l">回复</div></div>
<div class="card {'danger' if d['hard_bounce'] else ''}"><div class="n">{d['hard_bounce']}</div><div class="l">Hard Bounce</div></div>
<div class="card {'danger' if d['unsubscribe'] else ''}"><div class="n">{d['unsubscribe']}</div><div class="l">退订</div></div>
<div class="card info"><div class="n">{d['retail_a0']}</div><div class="l">Retail A0</div></div>
<div class="card info"><div class="n">{d['custom_a0']}</div><div class="l">Custom A0</div></div>
<div class="card"><div class="n">{d['total_a0']}</div><div class="l">Total A0</div></div>
<div class="card {'ok' if d['afternoon_gap']==0 else 'warn'}"><div class="n">{d['afternoon_gap']}</div><div class="l">下午缺口</div></div>
<div class="card {'ok' if d['today_complete'] else 'warn'}"><div class="n">{"✓ 完成" if d['today_complete'] else "✗"}</div><div class="l">今日闭环</div></div>
<div class="card"><div class="n">{d['msg_id_present']}</div><div class="l">Message-ID</div></div>
</div>
<h3>人工审核 / Manual Review</h3>
<div class="cards">
<div class="card"><div class="n">{d['review']['pending_manual_review']}</div><div class="l">Pending Manual Review</div></div>
<div class="card"><div class="n">{d['review']['b1_social_verified']}</div><div class="l">B1 Social Verified</div></div>
<div class="card"><div class="n">{d['review']['b2_review']}</div><div class="l">B2 Review</div></div>
<div class="card"><div class="n">{d['review']['contact_form']}</div><div class="l">Contact Form</div></div>
<div class="card"><div class="n">{d['review']['review_recovery']}</div><div class="l">Review Recovery</div></div>
<div class="card"><div class="n">{d['review']['deferred']}</div><div class="l">Deferred</div></div>
<div class="card"><div class="n">{d['review']['approved_auto']}</div><div class="l">Approved Auto</div></div>
<div class="card"><div class="n">{d['review']['approved_manual']}</div><div class="l">Approved Manual</div></div>
<div class="card"><div class="n">{d['review']['rejected']}</div><div class="l">Rejected</div></div>
<div class="card"><div class="n">{d['review']['recheck_pending']}</div><div class="l">Recheck Pending</div></div>
<div class="card"><div class="n">{d['review']['reviewed_today']}</div><div class="l">今日审核 / Reviewed Today</div></div>
<div class="card"><div class="n">{d['review']['a0_created_after_review']}</div><div class="l">审核后 Strict A0</div></div>
</div>

<div class="tabs">
<button class="tab active" onclick="showTab('sent',this)">发送明细</button>
<button class="tab" onclick="showTab('city',this)">城市覆盖</button>
<button class="tab" onclick="showTab('platform',this)">平台品牌</button>
<button class="tab" onclick="showTab('followup',this)">Follow-up</button>
<button class="tab" onclick="showTab('inbox',this)">Inbox</button>
<button class="tab" onclick="showTab('anomalies',this)">异常 ({len(d.get('anomalies',[]))})</button>
</div>

<div class="content">
<div class="section active" id="sent">
<h3>今日发送明细 ({len(d['send_list'])} 封) | 州分布: {state_rows or '<span style=\"color:#999\">—</span>'}</h3>
<div style="overflow-x:auto">
<table><thead><tr>
<th>时间</th><th>商家</th><th>城市</th><th>州</th><th>类型</th><th>模板</th><th>邮箱</th><th>Message-ID</th><th>状态</th>
</tr></thead><tbody>{send_rows}</tbody></table>
</div>
</div>

<div class="section" id="city">
<h3>城市检索覆盖 · 已覆盖 {cov['cities_searched']} · 待搜索 {cov['cities_pending']}</h3>
<div style="overflow-x:auto">
<table><thead><tr>
<th>州</th><th>城市</th><th>候选</th><th>官网</th><th>邮箱</th><th>Hygiene</th><th>A0</th><th>状态</th>
</tr></thead><tbody>{city_rows or '<tr><td colspan="8" style="color:#999;text-align:center">暂无城市记录</td></tr>'}</tbody></table>
</div>
</div>

<div class="section" id="platform">
<h3>平台品牌采集</h3>
<div style="overflow-x:auto">
<table><thead><tr>
<th>平台</th><th>类别</th><th>候选</th><th>自有品牌</th><th>非中国</th><th>官网</th><th>状态</th>
</tr></thead><tbody>{plat_rows or '<tr><td colspan="7" style="color:#999;text-align:center">已规划，尚未开始</td></tr>'}</tbody></table>
</div>
</div>

<div class="section" id="followup">
<h3>14-Day Follow-up Queue</h3>
<div class="cards">
<div class="card"><div class="n">{d['followup']['raw']}</div><div class="l">raw candidates</div></div>
<div class="card"><div class="n">{d['followup']['hygiene']}</div><div class="l">Hygiene pass</div></div>
<div class="card info"><div class="n">{d['followup']['final']}</div><div class="l">final sendable</div></div>
<div class="card"><div class="n">{d['followup']['planned']}</div><div class="l">今日计划</div></div>
<div class="card ok"><div class="n">{d['followup']['sent']}</div><div class="l">今日已发</div></div>
</div>
</div>

<div class="section" id="inbox">
<h3>Inbox 风险状态</h3>
<table><thead><tr><th>指标</th><th>数量</th></tr></thead><tbody>
<tr><td>普通回复</td><td>{d['inbox']['normal_reply']}</td></tr>
<tr><td>Hot 回复</td><td>{d['inbox']['hot_reply']}</td></tr>
<tr><td>自动回复</td><td>{d['inbox']['auto_reply']}</td></tr>
<tr><td>平台忽略</td><td>{d['inbox']['ignored_platform']}</td></tr>
<tr><td>Hard Bounce</td><td>{d['inbox']['hard_bounce']}</td></tr>
<tr><td>Soft Bounce</td><td>{d['inbox']['soft_bounce']}</td></tr>
<tr><td>退订</td><td>{d['inbox']['unsubscribe']}</td></tr>
<tr><td style="font-weight:600">Stop Required</td>
<td style="{'color:#e74c3c;font-weight:700' if d['inbox']['stop_required'] else 'color:#27ae60'}">{d['inbox']['stop_required']}</td></tr>
</tbody></table>
</div>

<div class="section" id="anomalies">
<h3>异常与待处理</h3>
{anomaly_html}
</div>
</div>

<p class="footer">rokt&razo BD Operations · 单文件自包含 · 双击打开 · 无需 Web Server · {d['timezone']}</p>
<script>
function showTab(id,el){{var ss=document.querySelectorAll('.section');var ts=document.querySelectorAll('.tab');for(var s of ss)s.classList.remove('active');for(var t of ts)t.classList.remove('active');document.getElementById(id).classList.add('active');el.classList.add('active')}}
</script>
</div></body></html>"""


def archive_reports(data: dict):
    """Archive daily JSON. Monthly rollup uses OLD file's data (no cross-contamination)."""
    today = data["today"]
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    MONTHLY_DIR.mkdir(parents=True, exist_ok=True)

    # Write current daily JSON (overwrite)
    daily_path = ARCHIVE_DIR / f"{today}.json"
    daily_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    # Process old files (>30 days)
    cutoff = ((datetime.now(timezone.utc) + SHANGHAI_OFFSET) - timedelta(days=30)).strftime("%Y-%m-%d")
    for f in sorted(ARCHIVE_DIR.glob("*.json")):
        try:
            date_str = f.stem
            if len(date_str) != 10 or date_str >= cutoff:
                continue
            # Read the ARCHIVED file's own data (BUG FIX: not current data)
            archived = json.loads(f.read_text())
            month_key = date_str[:7]
            monthly_path = MONTHLY_DIR / f"{month_key}.json"

            # Load existing monthly, upsert by date
            entries = {}
            if monthly_path.exists():
                try:
                    existing = json.loads(monthly_path.read_text())
                    for e in existing:
                        entries[e["date"]] = e
                except Exception:
                    pass

            entries[date_str] = {
                "date": date_str,
                "sent_today": archived.get("sent_today", 0),
                "followup_sent": archived.get("followup_sent", 0),
                "hybrid_count": archived.get("hybrid_count", 0),
                "custom_count": archived.get("custom_count", 0),
                "replies": archived.get("replies", 0),
                "hard_bounce": archived.get("hard_bounce", 0),
                "unsubscribe": archived.get("unsubscribe", 0),
            }

            # Atomic write: temp → rename
            tmp = monthly_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(
                sorted(entries.values(), key=lambda x: x["date"]), indent=2, ensure_ascii=False
            ))
            os.replace(str(tmp), str(monthly_path))
            f.unlink()  # Delete old daily only AFTER successful monthly write

        except Exception as e:
            print(f"  [ARCHIVE WARNING] {f.name}: {e}")


def main():
    print("BD Operations Dashboard v2")
    data = gather_data()

    html = render_html(data)
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"  HTML: {OUTPUT_HTML} ({len(html)} bytes)")

    OUTPUT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"  JSON: {OUTPUT_JSON}")

    archive_reports(data)
    print(f"  Archive daily: {ARCHIVE_DIR / data['today']}.json")

    # Summary
    print(f"\n  Sent: {data['sent_today']} | Hybrid: {data['hybrid_count']} | Custom: {data['custom_count']} | Legacy: {data['legacy_count']}")
    print(f"  A0: retail={data['retail_a0']} custom={data['custom_a0']} total={data['total_a0']}")
    print(f"  Message-ID present: {data['msg_id_present']} missing: {data['msg_id_missing']}")
    print(f"  Anomalies: {len(data['anomalies'])}")
    print("  Done.")


if __name__ == "__main__":
    main()
