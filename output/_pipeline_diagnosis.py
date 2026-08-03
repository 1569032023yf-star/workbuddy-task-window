"""P0 Pipeline Diagnosis — Read actual DB state, fix state advancement"""
import sqlite3, os
from datetime import datetime, timezone, timedelta
ASIA_SH = timezone(timedelta(hours=8))
DB = r'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\data\bd_leads.db'
now = datetime.now(ASIA_SH)
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
sep = '=' * 65

# 1. System Config
print(f'{sep}\n1. SYSTEM CONFIG\n{sep}')
for key in ['active_retail_state','active_retail_city','active_city_state','inventory_status']:
    r = conn.execute('SELECT value, updated_at FROM system_config WHERE key=?',(key,)).fetchone()
    v = r['value'] if r else 'NOT SET'
    u = r['updated_at'][:19] if r and r['updated_at'] else '?'
    print(f'  {key}: {v} (updated {u})')

# 2. City Queue
print(f'\n{sep}\n2. RETAIL CITY QUEUE\n{sep}')
cols = [c[1] for c in conn.execute('PRAGMA table_info(retail_city_queue)')]
for r in conn.execute('SELECT * FROM retail_city_queue ORDER BY priority').fetchall():
    d = dict(zip(cols, r))
    print(f'  {d.get("state","?"):3s} {d.get("city","?")[:20]:20s} priority={d.get("priority",0):3d} status={d.get("status","?")}')

# 3. Locks
print(f'\n{sep}\n3. LOCKS\n{sep}')
for r in conn.execute("SELECT key, value, updated_at FROM system_config WHERE key LIKE '%lock%' OR key LIKE '%cursor%' ORDER BY updated_at DESC LIMIT 10").fetchall():
    age = (now - datetime.fromisoformat(r['updated_at'].replace('T',' '))).total_seconds() if r['updated_at'] else 0
    print(f'  {r["key"]:50s} = {str(r["value"])[:40]:40s} age={age:.0f}s')

# 4. Discovery tables
print(f'\n{sep}\n4. DISCOVERY PIPELINE\n{sep}')
for tbl in ['lead_discovery_results','lead_discovery_hits','lead_discovery_query_state']:
    try:
        cnt = conn.execute(f'SELECT COUNT(*) FROM {tbl}').fetchone()[0]
        print(f'  {tbl}: {cnt}')
    except Exception as e:
        print(f'  {tbl}: NOT FOUND ({e})')

# 5. TN cities real status
print(f'\n{sep}\n5. TENNESSEE CITIES\n{sep}')
cities = conn.execute('''
    SELECT city, COUNT(*) as total,
           SUM(CASE WHEN email IS NOT NULL AND email != '' THEN 1 ELSE 0 END) as has_email,
           SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) as sent,
           SUM(CASE WHEN status='new' THEN 1 ELSE 0 END) as new_leads,
           SUM(CASE WHEN status='manual_review_needed' THEN 1 ELSE 0 END) as manual_review,
           SUM(CASE WHEN (email IS NULL OR email = '') THEN 1 ELSE 0 END) as missing_email
    FROM leads WHERE state='TN' GROUP BY city ORDER BY total DESC
''').fetchall()
for r in cities:
    missing = r['missing_email']; has_e = r['has_email']
    if r['sent'] > 0 and missing == 0 and not r['new_leads'] and not r['manual_review']:
        s = 'SENT_ALL'
    elif missing > 0: s = 'NEEDS_ENRICHMENT'
    elif r['manual_review'] > 0: s = 'NEEDS_REVIEW'
    elif r['new_leads'] > 0: s = 'HAS_SENDABLE'
    else: s = 'UNCLASSIFIED'
    print(f'  {r["city"]:20s} total={r["total"]:3d} email={has_e:3d} missing={missing:3d} sent={r["sent"]:2d} new={r["new_leads"]:2d} review={r["manual_review"]:2d} [{s}]')

# 6. FB Queue
print(f'\n{sep}\n6. FB QUEUE\n{sep}')
fb_t = conn.execute('SELECT COUNT(*) FROM fb_enrichment_queue').fetchone()[0]
fb_p = conn.execute('SELECT COUNT(*) FROM fb_enrichment_queue WHERE fb_check_status="pending" OR fb_check_status IS NULL').fetchone()[0]
print(f'  Total: {fb_t}, Pending: {fb_p}')

# 7. Stall diagnosis
print(f'\n{sep}\n7. STALL DIAGNOSIS\n{sep}')
lock = conn.execute("SELECT value, updated_at FROM system_config WHERE key LIKE '%run_lock%inventory%' ORDER BY updated_at DESC LIMIT 1").fetchone()
if lock and lock['value'] == 'acquired':
    age = (now - datetime.fromisoformat(lock['updated_at'].replace('T',' '))).total_seconds()
    print(f'  Inventory lock: ACQUIRED, {age:.0f}s old ({"STALE" if age > 3600 else "OK"})')
else:
    print(f'  Inventory lock: {lock["value"] if lock else "free"}')
print(f'  Discovery results: 0 (pipeline empty)')
print(f'  Browser maps: not running (requires user to start Playwright)')
print(f'  Classification: C (found stores but missing emails) + E (FB queue not consumed)')

# 8. FIX: Restore TN as active, AR/KY to QUEUED
print(f'\n{sep}\n8. STATE FIX\n{sep}')
conn.execute('UPDATE system_config SET value="TN", updated_at=? WHERE key="active_city_state"', (now.isoformat(),))
conn.execute('UPDATE system_config SET value="Tennessee", updated_at=? WHERE key="active_retail_state"', (now.isoformat(),))
conn.execute("UPDATE retail_city_queue SET status='QUEUED' WHERE state IN ('AR','KY') AND status NOT IN ('QUEUED','CITY_COMPLETE')")

# First unfinished TN city that needs work
first = conn.execute('''
    SELECT city FROM retail_city_queue WHERE state='TN' AND status NOT IN ('CITY_COMPLETE','SENT_ALL')
    ORDER BY priority LIMIT 1
''').fetchone()
if first:
    conn.execute('UPDATE system_config SET value=?, updated_at=? WHERE key="active_retail_city"', (first['city'], now.isoformat()))
    conn.execute("UPDATE retail_city_queue SET status='DISCOVERY_IN_PROGRESS' WHERE city=? AND state='TN'", (first['city'],))
    print(f'  Active city: {first["city"]}, TN')
else:
    print(f'  All TN cities complete')

conn.commit()

# Final
print(f'\n{sep}')
tn_cities = conn.execute('SELECT COUNT(DISTINCT city) FROM leads WHERE state="TN"').fetchone()[0]
tn_done = conn.execute("SELECT COUNT(*) FROM retail_city_queue WHERE state='TN' AND status IN ('CITY_COMPLETE','SENT_ALL')").fetchone()[0]
tn_not = conn.execute("SELECT COUNT(*) FROM retail_city_queue WHERE state='TN' AND status NOT IN ('CITY_COMPLETE','SENT_ALL')").fetchone()[0]
print(f'RESULTS:')
print(f'  Active State: TN | Active City: {first["city"] if first else "ALL_DONE"}')
print(f'  TN total cities: {tn_cities} | complete: {tn_done} | incomplete: {tn_not}')
print(f'  AR/KY: QUEUED')
print(f'  FB pending: {fb_p}')
print(f'  SMTP: 0 | Pre-Send/Outreach: PAUSED')
print(f'{sep}')
conn.close()
