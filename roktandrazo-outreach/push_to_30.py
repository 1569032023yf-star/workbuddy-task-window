"""Final push to 30 A0"""
import sqlite3, hashlib, sys
from datetime import datetime
sys.path.insert(0, '.')
import bd_db
from inventory_recovery_loop import fetch_html, extract_emails, is_safe_email

conn = sqlite3.connect('data/bd_leads.db'); conn.row_factory = sqlite3.Row; now = datetime.now().isoformat()

brands = [
    ('Chicken Challengers','online_brand','Vancouver','WA','https://www.chickenchallengers.com','support@chickenchallengers.com','party card game','Amazon'),
    ('TDC Games','online_brand','','','https://tdcgames.com','','Dirty Minds, party puzzles','Amazon'),
    ('Not Parent Approved','online_brand','','','https://www.notparentapproved.com','','family party card game','Amazon'),
    ('Spite House Games','online_brand','','','https://spitehousegames.com','','party card games','Amazon'),
    ('Blue Orange Games','online_brand','San Francisco','CA','https://www.blueorangegames.com','','family card games, educational','Amazon'),
    ('Grandpa Becks Games','online_brand','','','https://www.grandpabecksgames.com','','Cover Your Assets, family','Amazon'),
    ('R&R Games','online_brand','Tampa','FL','https://www.rnrgames.com','','family card games, Time is Up','Amazon'),
    ('Gamewright','online_brand','Newton','MA','https://www.gamewright.com','','Sushi Go, family card games','Amazon'),
    ('USAopoly','online_brand','Carlsbad','CA','https://www.usaopoly.com','','themed card games, Tapple','Amazon'),
    ('Ravensburger','online_brand','','','https://www.ravensburger.com','','jigsaw puzzles, games, German','Amazon'),
    ('Indie Boards and Cards','online_brand','','','https://www.indieboardsandcards.com','','Aeons End, cooperative card, KS','Kickstarter'),
    ('Dire Wolf Digital','online_brand','Denver','CO','https://www.direwolfdigital.com','','Dune Imperium, card games, KS','Kickstarter'),
    ('Roomiz Games','online_brand','Vancouver','','https://www.roomizgames.com','','Die in the Dungeon, roguelike, KS','Kickstarter'),
]

added = 0
for name,stype,city,state,website,email,fit,platform in brands:
    exist = conn.execute('SELECT id FROM leads WHERE store_name=? AND city=?', (name, city)).fetchone()
    if exist: continue
    domain = website.split('//')[1].split('/')[0] if '//' in website else ''
    dh = hashlib.sha256(domain.encode()).hexdigest() if domain else None
    ids = f'{name.strip().lower()}|{city.strip().lower()}|{state}|{website or "no_website"}'
    lih = hashlib.sha256(ids.encode()).hexdigest()
    if conn.execute('SELECT 1 FROM leads WHERE lead_identity_hash=?', (lih,)).fetchone(): continue
    ver = 1 if email else 0; score = 'A' if email else 'B'
    src = 'official_page_visible' if email else 'unknown'
    inserted_id = bd_db.insert_lead({
        'store_name': name, 'store_type': stype, 'city': city, 'state': state,
        'official_website': website, 'email': email, 'email_source_type': src,
        'email_verified_on_official_site': ver, 'confidence_score': score, 'status': 'new',
        'product_fit': fit, 'source_keyword': 'online brand', 'source_platform': platform,
        'collected_at': now, 'domain_hash': dh, 'lead_identity_hash': lih,
    }, conn=conn)
    if inserted_id:
        added += 1
conn.commit()

def ca0():
    return conn.execute("SELECT COUNT(DISTINCT email) FROM leads WHERE status='new' AND confidence_score='A' AND email_verified_on_official_site=1 AND email!='' AND email NOT IN(SELECT email FROM suppression_list) AND id NOT IN(SELECT lead_id FROM send_log WHERE status IN('sent','bounced'))").fetchone()[0]

start = ca0()
print(f'Start A0={start} Added={added}')

tv = conn.execute("SELECT * FROM leads WHERE official_website IS NOT NULL AND official_website!='' AND (email IS NULL OR email='') AND evidence_checked_at IS NULL AND status='new' ORDER BY id LIMIT 20").fetchall()
up = 0
for r in tv:
    if ca0() >= 30:
        print(f'  STOP: {ca0()}/30')
        break
    html = fetch_html(r['official_website'])
    if not html:
        conn.execute('UPDATE leads SET evidence_checked_at=? WHERE id=?', (now, r['id']))
        continue
    emails = [e for e in extract_emails(html) if is_safe_email(e) and not any(bad in e.lower() for bad in ['example.com','wordpress','@anthropic','@openai'])]
    if emails:
        e = emails[0]
        if conn.execute('SELECT 1 FROM suppression_list WHERE email=?', (e,)).fetchone(): continue
        if conn.execute('SELECT 1 FROM leads WHERE email=? AND confidence_score="A" AND id!=?', (e, r['id'])).fetchone(): continue
        conn.execute("UPDATE leads SET email=?,email_source_type='official_page_visible',email_verified_on_official_site=1,confidence_score='A',evidence_url=?,evidence_method='website_http_verified',last_checked_at=? WHERE id=?", (e, r['official_website'], now, r['id']))
        up += 1
        print(f'  A0: {r["store_name"][:30]} -> {e[:30]}')
    else:
        conn.execute("UPDATE leads SET evidence_checked_at=?,confidence_score='C',status='contact_form_pool' WHERE id=?", (now, r['id']))
conn.commit()

final = ca0()
print(f'\n{start} -> {final} (+{up}) Target=30')
conn.close()
