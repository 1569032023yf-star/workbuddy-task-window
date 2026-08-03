"""Bounce-driven lead optimization — IMAP scan + classify + write-back"""
import sys, os, sqlite3, imaplib, email, re, json
from datetime import datetime, timezone, timedelta
from email import policy
ASIA_SH = timezone(timedelta(hours=8))
now = datetime.now(ASIA_SH)
PROJECT_DIR = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach'
sys.path.insert(0, PROJECT_DIR)
DB = os.path.join(PROJECT_DIR, 'data', 'bd_leads.db')
sep = '=' * 65

# Load sent batch Message-IDs
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

batch_msgs = conn.execute("""
    SELECT sl.id, sl.lead_id, sl.email, sl.message_id, sl.sent_at, sl.batch_id,
           l.store_name, l.city, l.state, l.store_type, l.email_source_type, l.organization_key
    FROM send_log sl JOIN leads l ON sl.lead_id = l.id
    WHERE sl.sent_at > '2026-07-28' AND sl.status = 'sent'
    ORDER BY sl.sent_at
""").fetchall()

print(f'{sep}')
print(f'IMAP BOUNCE SCAN — {len(batch_msgs)} sent emails since Jul 29')
print(f'{sep}')

# IMAP
from env_loader import get_imap_config
cfg = get_imap_config()

if not cfg.get('user'):
    print('IMAP not configured')
    conn.close(); exit()

try:
    imap = imaplib.IMAP4_SSL(cfg['host'], cfg['port'], timeout=20)
    imap.login(cfg['user'], cfg['password'])
    print(f'Connected: {cfg["host"]}')
    
    all_bounces = []
    all_replies = []
    
    for folder in ['INBOX', 'Junk']:
        try:
            imap.select(f'"{folder}"', readonly=True)
            s, data = imap.search(None, '(SINCE "28-Jul-2026")')
            if s != 'OK' or not data[0]: continue
            
            uids = data[0].split()
            print(f'\n  {folder}: {len(uids)} messages, scanning...')
            
            for num in uids:
                try:
                    _, raw = imap.fetch(num, '(BODY.PEEK[] FLAGS)')
                    if not raw or not raw[0]: continue
                    
                    msg_bytes = raw[0][1]
                    if not msg_bytes: continue
                    
                    m = email.message_from_bytes(msg_bytes, policy=policy.default)
                    
                    # Extract headers
                    mid = (m.get('Message-ID') or '').strip()
                    irt = (m.get('In-Reply-To') or '').strip()
                    refs = (m.get('References') or '').strip()
                    subj = (m.get('Subject') or '').strip()
                    frm = (m.get('From') or '').strip()
                    to = (m.get('To') or '').strip()
                    
                    # Check against batch Message-IDs
                    found_match = None
                    for b in batch_msgs:
                        bmid = (b['message_id'] or '').strip()
                        if not bmid: continue
                        # Match by: In-Reply-To, References, or Message-ID origin
                        if bmid in irt or bmid in refs or mid.lower() == bmid.lower():
                            found_match = b
                            break
                        # Also check recipient email in To/Return-Path
                        if b['email'] and b['email'].lower() in to.lower():
                            found_match = b
                            break
                    
                    if not found_match:
                        # Check for DSN-specific headers
                        content_type = m.get_content_type()
                        if 'delivery-status' in content_type or 'report' in content_type:
                            # DSN bounce — extract body
                            body_text = ''
                            if m.is_multipart():
                                for part in m.walk():
                                    if part.get_content_type() == 'text/plain':
                                        try:
                                            body_text = part.get_content()
                                        except: pass
                            else:
                                try:
                                    body_text = m.get_content()
                                except: pass
                            
                            # Find recipient email in body
                            body_lower = body_text.lower() if body_text else ''
                            for b in batch_msgs:
                                if b['email'] and b['email'].lower() in body_lower:
                                    found_match = b
                                    break
                    
                    if found_match:
                        subj_lower = subj.lower()
                        is_auto = any(k in subj_lower for k in ['auto', 'out of office', 'automatic reply', 'vacation'])
                        is_bounce = any(k in subj_lower for k in ['undeliver', 'returned mail', 'delivery status', 'failure', 'bounce', 'mail delivery', 'returned']) or 'delivery-status' in content_type
                        is_unsub = 'unsubscribe' in subj_lower
                        
                        f = folder
                        bm = found_match
                        
                        if is_bounce:
                            # Extract DSN details
                            body_text = ''
                            if m.is_multipart():
                                for part in m.walk():
                                    if part.get_content_type() in ('text/plain', 'message/delivery-status'):
                                        try: body_text = part.get_content()
                                        except: pass
                            else:
                                try: body_text = m.get_content()
                                except: pass
                            
                            body_lower = (body_text or '').lower()
                            
                            # Classify
                            bounce_type = 'unknown_bounce'
                            if any(k in body_lower for k in ['user unknown','no such user','recipient not found','invalid recipient','mailbox disabled','address rejected','not found','does not exist']):
                                bounce_type = 'mailbox_invalid'
                            elif any(k in body_lower for k in ['domain not found','no mx','nxdomain','host not found','name or service not known']):
                                bounce_type = 'domain_invalid'
                            elif any(k in body_lower for k in ['spam','reputation','blocked','blacklisted','rejected','policy','5.7']) or 'policy' in subj_lower:
                                bounce_type = 'policy_bounce'
                            elif any(k in body_lower for k in ['quota','mailbox full','over quota']):
                                bounce_type = 'mailbox_full'
                            elif any(k in body_lower for k in ['try again','temporary','greylist','rate limit','4.']) and '5.' not in body_lower:
                                bounce_type = 'temporary_failure'
                            
                            all_bounces.append({
                                'lead_id': bm['lead_id'], 'email': bm['email'],
                                'store_name': bm['store_name'], 'state': bm['state'], 'city': bm['city'],
                                'org_key': bm['organization_key'], 'bounce_type': bounce_type,
                                'subject': subj[:80], 'folder': f,
                                'message_id': bm['message_id'][:50] if bm['message_id'] else ''
                            })
                            print(f'    BOUNCE [{bounce_type}] {bm["email"][:35]:35s} {bm["store_name"][:25]} [{f}]')
                        elif is_auto:
                            all_replies.append({'lead_id': bm['lead_id'], 'type': 'auto', 'store': bm['store_name']})
                            print(f'    AUTO: {frm[:40]} → {bm["store_name"][:25]}')
                        elif is_unsub:
                            all_replies.append({'lead_id': bm['lead_id'], 'type': 'unsub', 'store': bm['store_name']})
                            print(f'    UNSUB: {frm[:40]} → {bm["store_name"][:25]}')
                        else:
                            all_replies.append({'lead_id': bm['lead_id'], 'type': 'human', 'store': bm['store_name']})
                            print(f'    REPLY: {frm[:40]} → {bm["store_name"][:25]}')
                except Exception as e:
                    pass
            
        except Exception as e:
            print(f'  {folder}: error {str(e)[:50]}')
    
    imap.logout()
    
    # Summary
    b_stats = {}
    for b in all_bounces:
        b_stats[b['bounce_type']] = b_stats.get(b['bounce_type'], 0) + 1
    
    r_stats = {'auto': 0, 'human': 0, 'unsub': 0}
    for r in all_replies: r_stats[r['type']] = r_stats.get(r['type'], 0) + 1
    
    print(f'\n{sep}')
    print(f'RESULTS')
    print(f'{sep}')
    print(f'  Sent examined: {len(batch_msgs)}')
    print(f'  Bounces: {len(all_bounces)}  {b_stats}')
    print(f'  Replies: {len(all_replies)}  {r_stats}')
    print(f'  Outcome Unresolved: {len(batch_msgs) - len(all_bounces) - len(all_replies)}')
    
    # Per-source
    if all_bounces:
        src_stats = {}
        for b in all_bounces:
            src = conn.execute('SELECT email_source_type FROM leads WHERE id=?', (b['lead_id'],)).fetchone()
            src_key = src[0][:25] if src and src[0] else 'unknown'
            if src_key not in src_stats: src_stats[src_key] = {'sent':0,'bounce':0}
            src_stats[src_key]['bounce'] += 1
        
        # Count sent per source
        for b in batch_msgs:
            src = conn.execute('SELECT email_source_type FROM leads WHERE id=?', (b['lead_id'],)).fetchone()
            src_key = src[0][:25] if src and src[0] else 'unknown'
            if src_key not in src_stats: src_stats[src_key] = {'sent':0,'bounce':0}
            src_stats[src_key]['sent'] += 1
        
        print(f'\n  Per source:')
        for src, v in sorted(src_stats.items()):
            rate = f'{v["bounce"]/max(v["sent"],1)*100:.0f}%'
            print(f'    {src:30s} sent={v["sent"]:3d} bounce={v["bounce"]:3d} rate={rate}')
    
    # Write back to leads
    for b in all_bounces:
        bt = b['bounce_type']
        lid = b['lead_id']
        
        if bt == 'mailbox_invalid':
            conn.execute('''UPDATE leads SET status='bounced', follow_up_eligible=0, contact_recovery_required=1,
                notes=COALESCE(notes,'') || ? WHERE id=?''',
                (f' [B:{bt}:{now.date()}]', lid))
            conn.execute('''INSERT OR IGNORE INTO bounce_log (lead_id, email, bounce_type, bounce_received_at, diagnostic_code)
                VALUES (?,?,?,?,?)''', (lid, b['email'], 'hard', now.isoformat(), bt[:100]))
        
        elif bt == 'domain_invalid':
            conn.execute('''UPDATE leads SET follow_up_eligible=0, contact_recovery_required=1,
                notes=COALESCE(notes,'') || ? WHERE id=?''',
                (f' [B:domain_invalid:{now.date()}]', lid))
            conn.execute('''INSERT OR IGNORE INTO bounce_log (lead_id, email, bounce_type, bounce_received_at, diagnostic_code)
                VALUES (?,?,?,?,?)''', (lid, b['email'], 'hard', now.isoformat(), 'domain_invalid'))
        
        elif bt == 'policy_bounce':
            conn.execute('''UPDATE leads SET notes=COALESCE(notes,'') || ? WHERE id=?''',
                (f' [B:policy_review:{now.date()}]', lid))
        
        elif bt in ('mailbox_full', 'temporary_failure'):
            defer = (now + timedelta(days=3)).isoformat()
            conn.execute('''UPDATE leads SET notes=COALESCE(notes,'') || ? WHERE id=?''',
                (f' [B:{bt}:defer:{defer[:10]}]', lid))
    
    conn.commit()
    
except Exception as e:
    print(f'IMAP error: {e}')

conn.close()
print(f'\nDone. {now.strftime("%Y-%m-%d %H:%M")} CST')
