"""Generate BD Inventory HTML report for 2026-07-31."""
import sqlite3, datetime

conn = sqlite3.connect('data/bd_leads.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

today = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d')
now_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M CST')

c.execute('SELECT COUNT(*) FROM leads')
total_leads = c.fetchone()[0]

c.execute("""SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A' 
AND auto_sendable=1 AND email_verified_on_official_site=1""")
strict_a0 = c.fetchone()[0]

c.execute("""SELECT COUNT(DISTINCT l.id) FROM leads l WHERE l.status='new' AND l.confidence_score='A' 
AND l.auto_sendable=1 AND l.email_verified_on_official_site=1 
AND l.id NOT IN (SELECT DISTINCT lead_id FROM send_log WHERE message_type='new_outreach')""")
strict_a0_usable = c.fetchone()[0]

c.execute("""SELECT COUNT(DISTINCT organization_key) FROM leads 
WHERE send_eligibility='broad_outreach_ready' AND organization_key!=''""")
broad_orgs = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM leads WHERE send_eligibility='broad_outreach_ready'")
broad_locs = c.fetchone()[0]

c.execute("""SELECT state, COUNT(*) cnt FROM leads WHERE send_eligibility='broad_outreach_ready' 
AND state IN ('TN','AR','KY','OH','IN','MN','NE','NC','OR','CO') 
GROUP BY state ORDER BY cnt DESC""")
allowed_broad = c.fetchall()

c.execute("""SELECT status, COUNT(*) FROM leads WHERE status IN 
('manual_review_needed','contact_form_pool','exception_review','contact_form_only') GROUP BY status""")
review = dict(c.fetchall())

c.execute("""SELECT COUNT(*) FROM leads WHERE confidence_score='A' AND email IS NOT NULL AND email!='' 
AND (auto_sendable=0 OR auto_sendable IS NULL OR email_verified_on_official_site=0)""")
near_a0 = c.fetchone()[0]

c.execute('SELECT city, status FROM retail_city_queue ORDER BY priority')
city_queue = c.fetchall()

c.execute('SELECT COUNT(DISTINCT lead_id) FROM send_log WHERE substr(sent_at,1,10)=?', (today,))
sends_today = c.fetchone()[0]

c.execute("""SELECT state, COUNT(*) cnt FROM leads WHERE confidence_score='A' AND email IS NOT NULL AND email!='' 
AND (auto_sendable=0 OR auto_sendable IS NULL OR email_verified_on_official_site=0)
AND state IN ('TN','AR','KY','OH','IN','MN','NE','NC','OR','CO')
GROUP BY state ORDER BY cnt DESC""")
near_a0_states = c.fetchall()

conn.close()

# Build HTML
def badge(s):
    if s == 'search_matrix_exhausted': return ('done', 'Completed')
    if s == 'partial_collection_done': return ('active', 'In Progress')
    return ('pending', 'Pending')

city_rows = ''
for c, s in city_queue:
    bclass, blabel = badge(s)
    city_rows += f'<tr><td>{c}</td><td><span class="badge badge-{bclass}">{blabel}</span></td></tr>'

allowed_rows = ''
for s, cnt in allowed_broad:
    allowed_rows += f'<tr><td>{s}</td><td>{cnt}</td></tr>'
if not allowed_rows:
    allowed_rows = '<tr><td colspan="2">0 in allowed states</td></tr>'

review_rows = ''
for k, v in review.items():
    review_rows += f'<tr><td>{k}</td><td>{v}</td></tr>'

near_rows = ''
for s, cnt in near_a0_states:
    near_rows += f'<tr><td>{s}</td><td>{cnt}</td></tr>'

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BD Inventory Report - {today}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#0d1117; color:#c9d1d9; padding:24px; }}
.header {{ text-align:center; padding:32px 0; border-bottom:1px solid #30363d; margin-bottom:24px; }}
.header h1 {{ font-size:24px; color:#58a6ff; }}
.header .sub {{ color:#8b949e; font-size:13px; margin-top:4px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; margin-bottom:24px; }}
.card {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:20px; }}
.card .label {{ font-size:12px; color:#8b949e; text-transform:uppercase; letter-spacing:0.5px; }}
.card .value {{ font-size:32px; font-weight:700; margin-top:4px; }}
.card .subval {{ font-size:13px; color:#8b949e; }}
.critical {{ color:#f85149; }}
.warning {{ color:#d29922; }}
.success {{ color:#3fb950; }}
.info {{ color:#58a6ff; }}
.section {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:20px; margin-bottom:16px; }}
.section h2 {{ font-size:16px; color:#58a6ff; margin-bottom:12px; border-bottom:1px solid #30363d; padding-bottom:8px; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ text-align:left; padding:8px; border-bottom:1px solid #30363d; color:#8b949e; font-weight:600; }}
td {{ padding:8px; border-bottom:1px solid #21262d; }}
.badge {{ padding:3px 8px; border-radius:12px; font-size:11px; font-weight:600; }}
.badge-done {{ background:#1a3a2a; color:#3fb950; }}
.badge-active {{ background:#1a2a3a; color:#58a6ff; }}
.badge-pending {{ background:#1a1a2e; color:#8b949e; }}
.badge-critical {{ background:#3a1a1a; color:#f85149; }}
.footer {{ text-align:center; padding:16px; color:#484f58; font-size:11px; margin-top:16px; }}
.note {{ background:#1a2a3a; border-left:3px solid #58a6ff; padding:12px; margin-top:12px; font-size:13px; border-radius:0 6px 6px 0; }}
.warn {{ background:#2a1a1a; border-left:3px solid #f85149; }}
</style>
</head>
<body>
<div class="header">
  <h1>BD Inventory Report</h1>
  <div class="sub">Generated {now_str} | Business Date: {today} | Run: inventory:2026-07-31:56241114</div>
</div>

<div class="grid">
  <div class="card">
    <div class="label">Strict A0 Organizations</div>
    <div class="value critical">{strict_a0_usable}</div>
    <div class="subval">Target: 120 | Raw eligible: {strict_a0} (all sent 07/29)</div>
  </div>
  <div class="card">
    <div class="label">Organization Outreach Opportunities</div>
    <div class="value info">{broad_orgs}</div>
    <div class="subval">Broad Outreach Ready orgs ({broad_locs} locations)</div>
  </div>
  <div class="card">
    <div class="label">Broad Ready (Allowed States)</div>
    <div class="value warning">{sum(c for _,c in allowed_broad)}</div>
    <div class="subval">In TN/AR/KY/OH/IN/MN/NE/NC/OR/CO</div>
  </div>
  <div class="card">
    <div class="label">Review Center</div>
    <div class="value warning">{sum(review.values())}</div>
    <div class="subval">Pending manual review</div>
  </div>
  <div class="card">
    <div class="label">Total Leads</div>
    <div class="value">{total_leads}</div>
    <div class="subval">In database</div>
  </div>
  <div class="card">
    <div class="label">Sends Today</div>
    <div class="value">{sends_today}</div>
    <div class="subval">{today}</div>
  </div>
</div>

<div class="section">
  <h2>City Queue Status</h2>
  <table>
    <tr><th>City</th><th>Status</th></tr>
    {city_rows}
  </table>
  <div class="note">
    Nashville: search_matrix_exhausted (complete)<br>
    Memphis: partial_collection_done (configuration_blocked - Google Places API)<br>
    Knoxville/Little Rock/Fayetteville: not yet started<br>
    Louisville/Lexington: reset to pending (previously incorrectly activated)
  </div>
</div>

<div class="section">
  <h2>Broad Outreach Ready - Allowed States Only</h2>
  <table>
    <tr><th>State</th><th>Locations</th></tr>
    {allowed_rows}
  </table>
</div>

<div class="section">
  <h2>Review Center</h2>
  <table>
    <tr><th>Status</th><th>Count</th></tr>
    {review_rows}
  </table>
</div>

<div class="section">
  <h2>Near-A0 Candidates in Allowed States</h2>
  <table>
    <tr><th>State</th><th>Count</th></tr>
    {near_rows}
  </table>
  <div class="note">
    Total Near-A0 (all states): {near_a0}. These have A confidence + email but miss strict A0 criteria (auto_sendable=0, email_verified=0, or wrong source_type).
  </div>
</div>

<div class="section">
  <h2>Actions Performed This Run</h2>
  <table>
    <tr><td>Orchestrator --stage inventory --live</td><td>Ran, completed with all_lanes_exhausted</td></tr>
    <tr><td>City queue fix</td><td>Reset Louisville/Lexington to pending; Memphis kept active</td></tr>
    <tr><td>Broad Outreach analysis</td><td>Computed 95 orgs, wrote send_eligibility to 95 leads</td></tr>
    <tr><td>Organization keys</td><td>Patched 569 missing org_keys via _gen_organization_key</td></tr>
    <tr><td>Memphis email extraction</td><td>5 B-grade leads scanned, 0 emails extracted (SSL/VPN issue)</td></tr>
  </table>
</div>

<div class="section">
  <h2>Blockers</h2>
  <div class="note warn">
    <strong>Google Places API</strong>: Not configured, Lane A discovery blocked for all cities<br>
    <strong>Astrill VPN SSL</strong>: HTTPS proxy breaks website verification (EOF errors)<br>
    <strong>Strict A0 pool</strong>: Completely depleted - 3 leads all sent 07/29, excluded by send_log gate<br>
    <strong>No staging imports</strong>: No new leads from external files to process
  </div>
</div>

<div class="footer">
  BD Orchestrator v3.1 | No SMTP invoked | No Final Send Plan created | Inventory only
</div>
</body>
</html>'''

path = 'output/bd_inventory_2026-07-31.html'
with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Report saved to {path}')
print(f'Size: {len(html)} chars')
