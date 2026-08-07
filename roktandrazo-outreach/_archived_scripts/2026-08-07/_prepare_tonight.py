raise RuntimeError("LEGACY_SMTP_DISABLED: dated send script archived 2026-08-07. Use bd_orchestrator -> daily_session -> bd_sender only.")
"""Prepare tonight's unified batch — cancel old, rebuild with 21 remediation."""
import sqlite3, re, json, hashlib, secrets
from datetime import datetime, timezone, timedelta
ASIA_SH = timezone(timedelta(hours=8))
now = datetime.now(ASIA_SH)
BATCH = 'new_outreach_20260804_et1000'
DB = 'data/bd_leads.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# 1. CANCEL old 40 plan
conn.execute("UPDATE final_send_plan SET status='CANCELLED' WHERE outreach_batch_date=? AND status='planned'", (BATCH,))
conn.execute("UPDATE send_authorizations SET status='revoked' WHERE plan_id=?", (BATCH,))
conn.execute("DELETE FROM send_authorization_entries WHERE authorization_id LIKE ?", (f'%{BATCH}%',))
conn.execute("DELETE FROM email_tracking_messages WHERE tracking_message_id LIKE ?", (f'%trk_%{BATCH}%',))
conn.commit()
print('Old plan cleaned')

# 2. Exclusion sets
se = set((r[0] or '').lower() for r in conn.execute('SELECT DISTINCT email FROM suppression_list'))
bc = set((r[0] or '').lower() for r in conn.execute("SELECT DISTINCT email FROM bounce_log WHERE bounce_type IN ('hard','policy','permanent','domain','domain_invalid')"))
nr = set(r[0] for r in conn.execute('SELECT DISTINCT lead_id FROM reply_log'))
sent_e = set((r[0] or '').lower() for r in conn.execute("SELECT DISTINCT email FROM send_log WHERE status='sent'"))
sent_o = set()
for r in conn.execute("SELECT DISTINCT COALESCE(NULLIF(l.organization_key,''),'org'||l.id) FROM send_log sl JOIN leads l ON sl.lead_id=l.id WHERE sl.status='sent'"):
    sent_o.add(r[0])
invalid_pat = re.compile(r'(\.png|\.jpg|\.gif|\.webp|\.svg|\.css|\.js\b|sentry\.io|anthropic\.com|noreply|no.reply|donotreply|example\.com|@2x|\d+x\d+|^www\.|^xxx@|zendesk\.com|wixpress\.com)', re.I)

# 3. Select new orgs (all states, TN/AR/KY priority)
all_rows = conn.execute("""SELECT id,store_name,city,state,store_type,email,organization_key,confidence_score
    FROM leads WHERE status NOT IN ('sent','bounced','do_not_contact')
    AND email IS NOT NULL AND email!='' AND email LIKE '%@%.%'
    AND organization_key IS NOT NULL AND organization_key!='' 
    AND (email_source_type!='contact_form' OR email_source_type IS NULL)
    ORDER BY CASE WHEN state='TN' THEN 0 WHEN state='AR' THEN 1 WHEN state='KY' THEN 2 ELSE 3 END,
             CASE WHEN confidence_score='A' THEN 0 ELSE 1 END""").fetchall()

selected = []; seen_o = set(); seen_e = set()
for r in all_rows:
    if len(selected) >= 40: break
    e = (r['email'] or '').lower().strip()
    o = r['organization_key']
    if invalid_pat.search(e): continue
    if e in se or e in bc or e in sent_e: continue
    if o in sent_o: continue
    if r['id'] in nr: continue
    if o in seen_o or e in seen_e: continue
    selected.append({k: r[k] for k in r.keys()}); seen_o.add(o); seen_e.add(e)

# 4. Add 21 remediation leads (ensure all Row objects have same fields)
rem_leads_raw = conn.execute("""SELECT rc.lead_id as lead_id, rc.store_name, rc.state, rc.city, rc.store_type, 
    rc.recipient_email, rc.organization_key, rc.correct_template_key
    FROM remediation_candidates rc JOIN leads l ON rc.lead_id = l.id
    WHERE rc.remediation_status='eligible'""").fetchall()

rem_leads = [{k: r[k] for k in r.keys()} for r in rem_leads_raw]

rem_count = 0
for r in rem_leads:
    e = r['recipient_email'].lower().strip()
    o = r['organization_key']
    if e in seen_e or o in seen_o: continue
    if e in sent_e: continue
    selected.append(dict(r)); seen_o.add(o); seen_e.add(e)
    rem_count += 1

per_state = {}
for s in selected:
    st = s.get('state','?')
    per_state[st] = per_state.get(st,0) + 1

new_count = len(selected) - rem_count
print(f'Batch: {len(selected)} total ({new_count} new + {rem_count} remediation)')
for st, cnt in sorted(per_state.items(), key=lambda x:-x[1]):
    print(f'  {st}: {cnt}')

# 5. Create Plan + Auth
from bd_template import get_email_for_lead, route_template_for_lead
from bd_sender import create_send_authorization

planned = []
now_str = now.isoformat()
for i, s in enumerate(selected):
    lid = s.get('lead_id', 0)
    if not lid: continue
    name = s.get('store_name','')
    email = s.get('recipient_email') or s.get('email','')
    st = s.get('state','') or ''; ct = s.get('city','') or ''
    
    ld = {'store_name': name, 'store_type': s.get('store_type',''),
          'email': email, 'id': lid}
    if s.get('correct_template_key'):
        ld['template_override'] = s['correct_template_key']
    
    email_data = get_email_for_lead(ld)
    plan_id = f'{BATCH}_{i+1:04d}'
    
    conn.execute("""INSERT INTO final_send_plan (plan_id,lead_id,company_name,recipient_email,message_type,
        outreach_batch_date,planned_sequence,status,subject,body_text,body_html,source_city,source_state,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (plan_id, lid, name, email, 'new_outreach', BATCH, i+1, 'planned',
         email_data['subject'], email_data['body_text'], email_data['body_html'],
         ct, st, now_str))
    
    token = secrets.token_urlsafe(16)
    conn.execute("""INSERT INTO email_tracking_messages (tracking_message_id,token_hash,lead_id,plan_entry_id,status,is_test)
        VALUES (?,?,?,?,?,0)""",
        (f'trk_{lid}_{BATCH}_{i}', hashlib.sha256(token.encode()).hexdigest()[:16], lid, plan_id, 'prepared'))
    
    planned.append({'lead_id': lid, 'recipient_email': email, 'message_type': 'new_outreach'})

conn.commit()
print(f'Plan: {len(planned)} entries')

auth = create_send_authorization(BATCH, BATCH, planned, True, DB)
print(f'Auth: {auth["authorization_id"]}')

# Fix auth entries with real plan_entry_id
conn.execute(f"DELETE FROM send_authorization_entries WHERE authorization_id='{auth['authorization_id']}'")
fsp = conn.execute("""SELECT id AS fsp_id, lead_id, recipient_email FROM final_send_plan 
    WHERE outreach_batch_date=? AND status='planned' ORDER BY planned_sequence""", (BATCH,)).fetchall()
for p in fsp:
    conn.execute("""INSERT INTO send_authorization_entries 
        (authorization_id,plan_entry_id,lead_id,recipient_email,entry_hash,status)
        VALUES (?,?,?,?,?,?)""",
        (auth['authorization_id'], p['fsp_id'], p['lead_id'], p['recipient_email'],
         hashlib.sha256(f"{p['lead_id']}:{p['recipient_email']}".encode()).hexdigest()[:12], 'pending'))
conn.commit()

sl = conn.execute('SELECT COUNT(*) FROM send_log').fetchone()[0]
print(f'send_log: {sl} | READY for 22:00 CST')
conn.close()
