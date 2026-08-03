"""
Roktandrazo Outreach - Dashboard Generator
生成 HTML 监控面板：线索状态、评分分布、发送进度
"""

import os
from datetime import datetime
from bd_db import get_db


def get_stats():
    """获取统计概览 - 使用 bd_leads.db"""
    conn = get_db()
    c = conn.cursor()
    stats = {}

    # 线索总数
    c.execute("SELECT COUNT(*) FROM leads")
    stats["total_leads"] = c.fetchone()[0]

    # 按状态
    c.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
    stats["by_status"] = dict(c.fetchall())

    # 按评分
    c.execute("SELECT confidence_score, COUNT(*) FROM leads GROUP BY confidence_score")
    stats["by_score"] = dict(c.fetchall())

    # 按门店类型
    c.execute("SELECT store_type, COUNT(*) FROM leads GROUP BY store_type ORDER BY COUNT(*) DESC")
    stats["by_store_type"] = dict(c.fetchall())

    # 按州
    c.execute("SELECT state, COUNT(*) FROM leads GROUP BY state ORDER BY COUNT(*) DESC")
    stats["by_state"] = dict(c.fetchall())

    # 有邮箱的
    c.execute("SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND email != ''")
    stats["with_email"] = c.fetchone()[0]

    # 邮件统计 - 使用 send_log 表
    c.execute("SELECT status, COUNT(*) FROM send_log GROUP BY status")
    stats["email_stats"] = dict(c.fetchall())

    conn.close()
    return stats


def get_leads(limit: int = 500):
    """查询线索 - 使用 bd_leads.db"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM leads ORDER BY collected_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    # Convert tuples to dicts using cursor description
    col_names = [desc[0] for desc in c.description]
    conn.close()
    return [dict(zip(col_names, row)) for row in rows]


def generate_dashboard(output_path: str = None) -> str:
    """生成 HTML 仪表盘"""
    if not output_path:
        output_path = os.path.join(os.path.dirname(__file__), "output", "dashboard.html")

    stats = get_stats()
    all_leads = get_leads(limit=500)

    # 按评分统计
    by_score = stats.get("by_score", {})
    a_count = by_score.get("A", 0)
    b_count = by_score.get("B", 0)
    c_count = by_score.get("C", 0)

    # 按状态统计
    by_status = stats.get("by_status", {})

    # 按门店类型
    by_store_type = stats.get("by_store_type", {})

    # 按州
    by_state = stats.get("by_state", {})

    # 邮件统计
    email_stats = stats.get("email_stats", {})

    # 生成线索表格行
    table_rows = ""
    for lead in all_leads:
        score_color = {"A": "#16a34a", "B": "#d97706", "C": "#dc2626"}.get(lead.get("confidence_score", ""), "#6b7280")
        status_color = {
            "new": "#3b82f6", "reviewed": "#8b5cf6", "drafted": "#f59e0b",
            "sent": "#16a34a", "replied": "#059669", "bounced": "#dc2626",
            "unsubscribed": "#6b7280", "do_not_contact": "#1f2937"
        }.get(lead.get("status", ""), "#6b7280")
        
        table_rows += f"""
        <tr>
            <td><span class="badge" style="background:{score_color}">{lead.get('confidence_score', '?')}</span></td>
            <td><strong>{lead.get('store_name', '')}</strong></td>
            <td>{lead.get('store_type', '')}</td>
            <td>{lead.get('city', '')}, {lead.get('state', '')}</td>
            <td>{lead.get('email', '') or '<em style="color:#999">No email</em>'}</td>
            <td><span class="badge" style="background:{status_color}">{lead.get('status', '')}</span></td>
            <td><a href="{lead.get('official_website', '#')}" target="_blank">🌐</a></td>
        </tr>"""

    # 生成门店类型图表 (简单条形)
    store_type_bars = ""
    max_st = max(by_store_type.values()) if by_store_type else 1
    for stype, count in by_store_type.items():
        pct = int((count / max_st) * 100)
        store_type_bars += f"""
        <div class="bar-row">
            <span class="bar-label">{stype}</span>
            <div class="bar-fill" style="width:{pct}%">{count}</div>
        </div>"""

    # 生成州分布图表
    state_bars = ""
    max_state = max(by_state.values()) if by_state else 1
    for state, count in list(by_state.items())[:15]:
        pct = int((count / max_state) * 100)
        state_bars += f"""
        <div class="bar-row">
            <span class="bar-label">{state}</span>
            <div class="bar-fill" style="width:{pct}%">{count}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roktandrazo Outreach Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; color: #1e293b; padding: 24px; }}
        .header {{ text-align: center; margin-bottom: 32px; }}
        .header h1 {{ font-size: 28px; font-weight: 700; color: #0f172a; }}
        .header p {{ color: #64748b; margin-top: 4px; }}
        
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 32px; }}
        .stat-card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
        .stat-card .number {{ font-size: 36px; font-weight: 700; }}
        .stat-card .label {{ font-size: 13px; color: #64748b; margin-top: 4px; }}
        .stat-card.total .number {{ color: #0f172a; }}
        .stat-card.a-grade .number {{ color: #16a34a; }}
        .stat-card.b-grade .number {{ color: #d97706; }}
        .stat-card.c-grade .number {{ color: #dc2626; }}
        .stat-card.emails .number {{ color: #3b82f6; }}

        .section {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 24px; }}
        .section h2 {{ font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #0f172a; }}
        
        .bar-row {{ display: flex; align-items: center; margin-bottom: 8px; }}
        .bar-label {{ width: 200px; font-size: 13px; text-align: right; padding-right: 12px; color: #475569; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .bar-fill {{ background: #3b82f6; border-radius: 4px; padding: 4px 8px; color: white; font-size: 12px; font-weight: 600; min-width: 30px; }}

        .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }}
        @media (max-width: 768px) {{ .charts-grid {{ grid-template-columns: 1fr; }} }}

        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th {{ text-align: left; padding: 10px 8px; border-bottom: 2px solid #e2e8f0; color: #64748b; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }}
        td {{ padding: 10px 8px; border-bottom: 1px solid #f1f5f9; }}
        tr:hover {{ background: #f8fafc; }}
        
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 9999px; color: white; font-size: 11px; font-weight: 600; min-width: 20px; text-align: center; }}
        a {{ color: #3b82f6; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}

        .score-donut {{ display: flex; gap: 24px; align-items: center; justify-content: center; padding: 16px 0; }}
        .donut-segment {{ text-align: center; }}
        .donut-segment .count {{ font-size: 32px; font-weight: 700; }}
        .donut-segment .type {{ font-size: 12px; color: #64748b; }}

        .status-bar {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }}
        .status-item {{ background: #f1f5f9; padding: 6px 12px; border-radius: 8px; font-size: 12px; }}
        .status-item strong {{ color: #0f172a; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧩 Roktandrazo Outreach Dashboard</h1>
        <p>US Retail Store Lead Collection & Email Outreach</p>
        <p style="font-size:12px; color:#94a3b8;">最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card total">
            <div class="number">{stats.get('total_leads', 0)}</div>
            <div class="label">总线索数</div>
        </div>
        <div class="stat-card a-grade">
            <div class="number">{a_count}</div>
            <div class="label">A 级 (高质量)</div>
        </div>
        <div class="stat-card b-grade">
            <div class="number">{b_count}</div>
            <div class="label">B 级 (中等)</div>
        </div>
        <div class="stat-card c-grade">
            <div class="number">{c_count}</div>
            <div class="label">C 级 (待补)</div>
        </div>
        <div class="stat-card emails">
            <div class="number">{stats.get('with_email', 0)}</div>
            <div class="label">有邮箱</div>
        </div>
    </div>

    <div class="charts-grid">
        <div class="section">
            <h2>🏪 门店类型分布</h2>
            {store_type_bars if store_type_bars else '<p style="color:#999">暂无数据</p>'}
        </div>
        <div class="section">
            <h2>📍 州分布 (Top 15)</h2>
            {state_bars if state_bars else '<p style="color:#999">暂无数据</p>'}
        </div>
    </div>

    <div class="section">
        <h2>📊 状态分布</h2>
        <div class="status-bar">
            {''.join(f'<div class="status-item"><strong>{v}</strong> {k}</div>' for k, v in by_status.items()) if by_status else '<p style="color:#999">暂无数据</p>'}
        </div>
    </div>

    <div class="section">
        <h2>📧 邮件发送统计</h2>
        <div class="status-bar">
            {''.join(f'<div class="status-item"><strong>{v}</strong> {k}</div>' for k, v in email_stats.items()) if email_stats else '<p style="color:#999">尚未发送邮件</p>'}
        </div>
    </div>

    <div class="section">
        <h2>📋 全部线索 ({len(all_leads)})</h2>
        <div style="overflow-x: auto;">
        <table>
            <thead>
                <tr>
                    <th>评分</th>
                    <th>门店名</th>
                    <th>类型</th>
                    <th>城市</th>
                    <th>邮箱</th>
                    <th>状态</th>
                    <th>官网</th>
                </tr>
            </thead>
            <tbody>
                {table_rows if table_rows else '<tr><td colspan="7" style="text-align:center;color:#999;padding:24px;">暂无线索数据</td></tr>'}
            </tbody>
        </table>
        </div>
    </div>

    <div style="text-align:center; padding:24px; color:#94a3b8; font-size:12px;">
        Roktandrazo Outreach System · Powered by WorkBuddy
    </div>
</body>
</html>"""

    # 写入文件
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[Dashboard] 已生成: {output_path}")
    return output_path


if __name__ == "__main__":
    from db import init_db
    init_db()
    path = generate_dashboard()
    print(f"打开浏览器查看: file:///{path}")
