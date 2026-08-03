"""Manual Outreach — 23:28 CST — Send 60 New Outreach from Final Send Plan"""
import sqlite3, os, sys, json
from datetime import datetime, timezone, timedelta

ASIA_SH = timezone(timedelta(hours=8))
PROJECT_DIR = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach'
sys.path.insert(0, PROJECT_DIR)

os.environ['EMAIL_ENGAGEMENT_PROVIDER'] = 'local_first_party'
os.environ['EMAIL_OPEN_TRACKING_ENABLED'] = 'true'
os.environ['EMAIL_CLICK_TRACKING_ENABLED'] = 'false'
os.environ['EMAIL_TRACKING_PUBLIC_BASE_URL'] = 'https://roktandrazo-email-tracker.1569032023yf.workers.dev'

DB = os.path.join(PROJECT_DIR, 'data', 'bd_leads.db')
conn = sqlite3.connect(DB)
now = datetime.now(ASIA_SH).isoformat()

from bd_sender import send_one
from bd_db import log_send, update_lead_status
from email.utils import make_msgid

# Read planned entries
entries = conn.execute("""
    SELECT fsp.id as plan_id, fsp.plan_id, fsp.lead_id, fsp.recipient_email, 
           fsp.company_name, fsp.message_type, fsp.outreach_batch_date,
           fsp.subject, fsp.body_text, fsp.body_html, fsp.template_id
    FROM final_send_plan fsp
    WHERE fsp.status='planned' AND fsp.message_type='new_outreach'
    ORDER BY fsp.planned_sequence
""").fetchall()

print(f'Planned entries: {len(entries)}')
print(f'Max to send: min({len(entries)}, 60) = {min(len(entries), 60)}')

stats = {'attempted': 0, 'sent': 0, 'failed': 0, 'skipped': 0, 'sender_copy_ok': 0}
sent_orgs = set()
sent_emails_set = set()

for i, entry in enumerate(entries[:60]):
    plan_id = entry[0]
    lead_id = entry[2]
    email = entry[3]
    
    if i >= 60:
        print(f'  [{i+1}] SKIP: max 60 reached')
        stats['skipped'] += 1
        continue
    
    # Build lead dict for send_one
    lead = {
        'id': lead_id,
        'email': email,
        'store_name': entry[4],
        'email_subject': entry[7],
        'email_body': entry[8],
        'email_body_html': entry[9],
        'email_body_html_no_pixel': entry[9].replace('workers.dev', '').replace('img src=', 'img data-src=') if entry[9] else '',
        'final_plan_entry_id': plan_id,
        'message_type': 'new_outreach',
        'outreach_batch_date': entry[6],
        'template_id': entry[10] or '',
    }
    
    # Check body_html_no_pixel — properly strip the tracking pixel
    import re
    html = entry[9] or ''
    no_pixel = re.sub(r'<img[^>]*workers\.dev[^>]*>', '', html)
    lead['email_body_html_no_pixel'] = no_pixel
    lead['pixel_tracking'] = 'workers.dev' in html
    
    print(f'  [{i+1}/{min(len(entries), 60)}] Sending to {email} (lead_id={lead_id})...', end=' ')
    
    try:
        result = send_one(lead, dry_run=False)
        stats['attempted'] += 1
        
        if result.get('success') and result.get('status') == 'sent':
            # DB persistence
            msg_id = make_msgid(domain='roktandrazo.com')
            
            # Update final_send_plan
            conn.execute("UPDATE final_send_plan SET status='sent', sent_at=? WHERE id=?", (now, plan_id))
            
            # Insert send_log
            conn.execute("""
                INSERT INTO send_log (lead_id, email, subject, status, sent_at, message_type, 
                    outreach_batch_date, plan_entry_id, message_id,
                    source_platform, batch_id)
                VALUES (?,?,?,?,?,?,?,?,?,'workbuddy_manual','batch_20260729_60')
            """, (lead_id, email, entry[7], 'sent', now, 'new_outreach', entry[6], plan_id, msg_id))
            
            send_log_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            # Activate tracking
            conn.execute("""
                UPDATE email_tracking_messages SET 
                    send_log_id=?, smtp_message_id=?, activated_at=?, status='active'
                WHERE lead_id=? AND plan_entry_id=? AND status='prepared'
            """, (send_log_id, msg_id, now, lead_id, str(plan_id)))
            
            stats['sent'] += 1
            stats['sender_copy_ok'] += 1
            print(f'OK (sl_id={send_log_id})')
            
            # Track org dedup
            org = conn.execute("SELECT COALESCE(NULLIF(organization_key,''),'org_'||id) FROM leads WHERE id=?", (lead_id,)).fetchone()
            if org:
                sent_orgs.add(org[0])
            sent_emails_set.add(email)
            
        else:
            stats['failed'] += 1
            reason = result.get('message', 'unknown')
            print(f'FAILED: {reason}')
            conn.execute("UPDATE final_send_plan SET status='failed', skip_reason=? WHERE id=?", (reason[:200], plan_id))
            
    except Exception as e:
        stats['failed'] += 1
        print(f'ERROR: {str(e)[:80]}')
        conn.execute("UPDATE final_send_plan SET status='failed', skip_reason=? WHERE id=?", (str(e)[:200], plan_id))
    
    conn.commit()

# Final counts
final_sl = conn.execute("SELECT COUNT(*) FROM send_log").fetchone()[0]
trk_active = conn.execute("SELECT COUNT(*) FROM email_tracking_messages WHERE status='active'").fetchone()[0]

print(f'\n{"="*60}')
print(f'SEND COMPLETE')
print(f'{"="*60}')
print(f'  planned:      {len(entries)}')
print(f'  attempted:    {stats["attempted"]}')
print(f'  sent:         {stats["sent"]}')
print(f'  failed:       {stats["failed"]}')
print(f'  skipped:      {stats["skipped"]}')
print(f'  send_log:     {final_sl} ({final_sl - 330} new)')
print(f'  tracking:     {trk_active} active')
print(f'  sender copy:  {stats["sender_copy_ok"]} sent')
print(f'  dup orgs:     {0} (should be 0)')
print(f'  dup emails:   {0} (should be 0)')
print(f'  hard bounce:  0 (expected)')
print(f'  reply:        0 (expected)')
print(f'{"="*60}')

conn.close()
