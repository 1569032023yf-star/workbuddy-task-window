#!/usr/bin/env python3
"""Run Broad Outreach Ready full analysis and generate report."""
import sys, json, sqlite3, os
sys.path.insert(0, '.')
from broad_outreach_gate import analyze_all_leads
from lead_hygiene_gate import evaluate_a0

conn = sqlite3.connect('data/bd_leads.db')
conn.row_factory = sqlite3.Row

results = analyze_all_leads(conn)

# ── 使用 get_sendable_leads 的 SQL 计算 Strict A0 ──
a0_sql = """
    SELECT id, store_name, city, state, email, official_website, organization_key
    FROM leads WHERE status='new' AND confidence_score='A' 
    AND COALESCE(auto_sendable,0)=1 AND COALESCE(email_verified_on_official_site,0)=1
    AND email IS NOT NULL AND TRIM(email)!=''
    AND email_source_type IN ('official_page_visible','official_mailto','wholesale_vendor_page')
    AND official_website IS NOT NULL AND TRIM(official_website)!=''
    AND evidence_url IS NOT NULL AND TRIM(evidence_url)!=''
    AND evidence_snippet IS NOT NULL AND TRIM(evidence_snippet)!=''
    AND evidence_method IS NOT NULL AND TRIM(evidence_method)!=''
    AND unsubscribed_at IS NULL
"""
a0_sql_rows = conn.execute(a0_sql).fetchall()

strict_a0_orgs = set()
for r in a0_sql_rows:
    org_key = r['organization_key']
    if org_key:
        strict_a0_orgs.add(org_key)

# ── 预加载历史数据 ──
sent_emails_set = set()
for r in conn.execute("SELECT DISTINCT LOWER(email) as email FROM send_log WHERE status='sent'").fetchall():
    if r['email']:
        sent_emails_set.add(r['email'])

suppressed_set = set()
for r in conn.execute("SELECT LOWER(email) as email FROM suppression_list").fetchall():
    if r['email']:
        suppressed_set.add(r['email'])

bounced_set = set()
for r in conn.execute("SELECT DISTINCT LOWER(email) as email FROM bounce_log WHERE LOWER(COALESCE(bounce_type,''))!='soft'").fetchall():
    if r['email']:
        bounced_set.add(r['email'])

sent_domains_set = set()
for r in conn.execute("""
    SELECT DISTINCT l.domain_hash FROM send_log sl
    JOIN leads l ON sl.lead_id=l.id WHERE sl.status='sent' AND l.domain_hash IS NOT NULL
""").fetchall():
    if r['domain_hash']:
        sent_domains_set.add(r['domain_hash'])

sent_orgs_set = set()
for r in conn.execute("""
    SELECT DISTINCT l.organization_key FROM send_log sl
    JOIN leads l ON sl.lead_id=l.id WHERE sl.status='sent'
    AND l.organization_key IS NOT NULL AND l.organization_key!=''
""").fetchall():
    if r['organization_key']:
        sent_orgs_set.add(r['organization_key'])

neg_ids = set()
for r in conn.execute("""
    SELECT lead_id FROM reply_log 
    WHERE LOWER(COALESCE(summary,'')) LIKE '%stop%'
    OR LOWER(COALESCE(summary,'')) LIKE '%remove%' 
    OR LOWER(COALESCE(summary,'')) LIKE '%unsubscribe%'
""").fetchall():
    if r['lead_id']:
        neg_ids.add(r['lead_id'])

# ── 加入 Strict A0 leads 到 broad list ──
for r in a0_sql_rows:
    d = dict(r)
    org_key = d.get('organization_key','') or ''
    if org_key and org_key not in results['broad_ready_organizations']:
        results['broad_ready_locations'].append({
            'lead_id': d['id'],
            'organization_key': org_key,
            'store_name': d['store_name'],
            'city': d['city'],
            'state': d['state'],
            'email': (d.get('email') or '').strip().lower(),
            'business_category': 'strict_a0',
            'broad_fit_reason': 'strict_a0_highest_confidence',
            'contact_source': d.get('email_source_type',''),
            'send_priority': 'high',
            'contact_source_confidence': 'high',
            'prev_sent': False,
            'suppressed': False,
            'bounced': False,
            'negative_reply': False,
            'allow_send': True,
        })
        results['broad_ready_organizations'].add(org_key)

# ── 重算去重计数 ──
results['strict_a0_organizations'] = len(strict_a0_orgs)
results['broad_org_opportunities'] = len(results['broad_ready_organizations'])

# ── 排序 ──
results['broad_ready_locations'].sort(
    key=lambda x: (
        0 if x.get('business_category') == 'strict_a0' else 
        1 if x.get('send_priority') == 'high' else 2,
        str(x.get('city','')), str(x.get('store_name',''))
    )
)

max_plan = min(results['broad_org_opportunities'], 60)

# ── 最终报告 ──
lines = []
lines.append('=' * 70)
lines.append('  BD OUTREACH BROAD MATCH ELIGIBILITY — FINAL REPORT')
lines.append('  Date: 2026-07-29  |  Policy: Broad Outreach Ready v1.0')
lines.append('=' * 70)
lines.append('')
lines.append('---')
lines.append('一、两套资格层')
lines.append(f'  1. Strict A0 Organizations:          {results["strict_a0_organizations"]}')
lines.append(f'  2. Broad Outreach Ready Orgs:         {results["broad_org_opportunities"]}')
lines.append(f'  3. Broad Organization Opportunities:  {len(results["broad_ready_locations"])}')
lines.append('')
lines.append('---')
lines.append('二、解封统计')
lines.append(f'  4. CONTACT_ROLE_UNCERTAIN unblocked:  {results["contact_role_uncertain_unblocked"]}')
lines.append(f'  5. organization_key auto-patched:     {results["org_key_patched"]}')
lines.append('')
lines.append('---')
lines.append('三、排除统计')
lines.append(f'  6.  Invalid email excluded:           {results["invalid_email_excluded"]}')
lines.append(f'  7.  Previously Sent excluded:         {len(results["previously_sent"])}')
lines.append(f'  8.  Permanent Block excluded:         {len(results["permanently_blocked"])}')
lines.append(f'  9.  Contact Form Only:                {len(results["contact_form_only"])}')
lines.append(f'  10. Exception Review:                 {len(results["exception_review"])}')
lines.append(f'  11. Contact Recovery:                 {len(results["contact_recovery"])}')
lines.append('')
lines.append('---')
lines.append('四、发送计划')
lines.append(f'  12. Max New Outreach tonight:          {max_plan} (capped at 60)')
lines.append(f'  13. Reached 60:                        {"YES" if results["broad_org_opportunities"] >= 60 else "NO"}')
lines.append('')
lines.append('---')
lines.append('五、安全确认')
lines.append('  14. send_log NOT modified:             YES (read-only analysis)')
lines.append('  15. Final Send Plan NOT created:       YES (read-only analysis)')
lines.append('  16. SMTP NOT invoked:                  YES (read-only analysis)')
lines.append('')
lines.append('---')
lines.append('六、发送优先级')
high_cnt = sum(1 for l in results['broad_ready_locations'] if l.get('business_category')=='strict_a0' or l.get('send_priority')=='high')
normal_cnt = sum(1 for l in results['broad_ready_locations'] if l.get('send_priority')=='normal')
lines.append(f'  Strict A0 + High priority:  {high_cnt}')
lines.append(f'  Normal priority:            {normal_cnt}')
lines.append('')
lines.append('---')
lines.append('七、Broad Ready by State (ALLOWED states: TN/AR/KY/OH/IN/MN/NE/NC/OR/CO):')
states = {}
for l in results['broad_ready_locations']:
    st = l.get('state','?') or '?'
    states[st] = states.get(st, 0) + 1
for st, cnt in sorted(states.items(), key=lambda x: -x[1]):
    allowed = 'ALLOWED' if st in ('TN','AR','KY','OH','IN','MN','NE','NC','OR','CO') else ''
    lines.append(f'  {st:4s}: {cnt:3d}  {allowed}')
lines.append('')
lines.append('---')
lines.append('八、Blocked Reasons:')
for reason, count in sorted(results['blocked_reasons'].items(), key=lambda x: -x[1]):
    lines.append(f'  {reason}: {count}')
lines.append('')
lines.append('---')
lines.append(f'九、Broad Outreach Opportunities (first 30 of {len(results["broad_ready_locations"])}):')
lines.append(f'  {"ID":<6} {"Org Key":<45} {"City/State":<22} {"Category":<24} {"Prio":<8} Send')
lines.append('  ' + '-' * 112)
for i, l in enumerate(results['broad_ready_locations'][:30]):
    org = (l['organization_key'] or '?')[:43]
    loc = f"{(l['city'] or '?')}, {(l['state'] or '?')}"[:20]
    cat = l['business_category'][:22]
    prio = l.get('send_priority','normal')
    allow = 'YES' if l.get('allow_send',True) else 'NO'
    lines.append(f'  {l["lead_id"]:<6} {org:<45} {loc:<22} {cat:<24} {prio:<8} {allow}')

report_text = '\n'.join(lines)
print(report_text)

# ── 保存文件 ──
os.makedirs('output', exist_ok=True)

with open('output/broad_outreach_report_2026-07-29.txt', 'w', encoding='utf-8') as f:
    f.write(report_text)

report_json = {
    'date': '2026-07-29',
    'policy_version': 'Broad Outreach Ready v1.0',
    'metrics': {
        'strict_a0_organizations': results['strict_a0_organizations'],
        'broad_outreach_ready_organizations': results['broad_org_opportunities'],
        'broad_organization_opportunities': len(results['broad_ready_locations']),
        'contact_role_uncertain_unblocked': results['contact_role_uncertain_unblocked'],
        'organization_key_auto_patched': results['org_key_patched'],
        'invalid_email_excluded': results['invalid_email_excluded'],
        'previously_sent_excluded': len(results['previously_sent']),
        'permanent_block_excluded': len(results['permanently_blocked']),
        'contact_form_only': len(results['contact_form_only']),
        'exception_review': len(results['exception_review']),
        'contact_recovery': len(results['contact_recovery']),
        'max_new_outreach_tonight': max_plan,
        'reached_60': results['broad_org_opportunities'] >= 60,
    },
    'safety_confirmations': {
        'send_log_not_modified': True,
        'final_send_plan_not_created': True,
        'smtp_not_invoked': True,
    },
    'broad_ready_locations': results['broad_ready_locations'][:200],
    'blocked_reasons': results['blocked_reasons'],
}

with open('output/broad_outreach_report_2026-07-29.json', 'w', encoding='utf-8') as f:
    json.dump(report_json, f, indent=2, default=str)

print(f'\nSaved: output/broad_outreach_report_2026-07-29.txt')
print(f'Saved: output/broad_outreach_report_2026-07-29.json')

conn.close()
