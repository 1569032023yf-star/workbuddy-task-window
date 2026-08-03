"""Batch insert online brand leads and verify websites for email."""
import sqlite3, hashlib, sys
from datetime import datetime
sys.path.insert(0, '.')
import bd_db

conn = sqlite3.connect('data/bd_leads.db')
now = datetime.now().isoformat()

brands = [
    ('GeoToys','online_brand','Westport','CT','https://www.geotoys.com','','educational flashcards, Amazon brand','Amazon'),
    ('Wildkin','online_brand','Nashville','TN','https://www.wildkin.com','','kids educational cards, memory games','Amazon'),
    ('Ridleys Games','online_brand','Bath','UK','https://www.chroniclebooks.com','','playing cards, trivia games, original designs','Amazon'),
    ('Ten Hundred Art','online_brand','','','https://www.tenhundredart.com','','custom playing cards, artist brand, Kickstarter','Kickstarter'),
    ('PlayMonster','online_brand','Beloit','WI','https://www.playmonster.com','','card games, board games, puzzles','Amazon'),
    ('Modern Tarot','online_brand','Los Angeles','CA','https://www.moderntarot.co','','tarot oracle cards, own designs','Etsy'),
    ('The Laughing Giraffe','online_brand','','','https://www.thelaughinggiraffe.com','','kids flash cards, educational','Etsy'),
    ('Level 99 Games','online_brand','','','https://www.level99games.com','','puzzle combat card games, Bullet game, Kickstarter','Kickstarter'),
    ('Limithron','online_brand','Denver','CO','https://www.limithron.com','','pirate maps, RPG, Kickstarter creator','Kickstarter'),
    ('Chip Theory Games','online_brand','Plymouth','MN','https://www.chiptheorygames.com','','strategy card games, premium components, Gamefound','Gamefound'),
    ('Skytear Games','online_brand','','','https://www.skyteargames.com','','MOBA board game, card game publisher','Gamefound'),
    ('Go On Board','online_brand','','','https://goonboard.eu','','The Witcher board game, Gamefound','Gamefound'),
    ('Stone Blade Entertainment','online_brand','','','https://www.stoneblade.com','','Ascension deck-building game, card games','Gamefound'),
    ('Gamely Games','online_brand','','','https://www.gamelygames.com','','family card games, own brand','Shopify'),
    ('Exploding Kittens','online_brand','Los Angeles','CA','https://www.explodingkittens.com','','own brand card games, puzzles','Shopify'),
    ('Postcardly','online_brand','Seattle','WA','https://www.postcardly.com','','custom postcards, photo cards','Shopify'),
    ('Postable','online_brand','New York','NY','https://www.postable.com','','custom postcards, greeting cards','Shopify'),
    ('Magic Puzzle Company','online_brand','','','https://magicpuzzlecompany.com','','own brand jigsaw puzzles, Kickstarter','Kickstarter'),
    ('Mondo Games','online_brand','Austin','TX','https://mondoshop.com','','themed card games, licensed games','Shopify'),
    ('Curious Correspondence','online_brand','','','https://www.curiouscorrespondence.com','','subscription puzzle games, own brand','Shopify'),
]

added = 0
for name,stype,city,state,website,email,fit,platform in brands:
    exist = conn.execute("SELECT id FROM leads WHERE store_name=? AND city=?", (name, city)).fetchone()
    if exist: continue
    domain = website.split('//')[1].split('/')[0] if '//' in website else ''
    dh = hashlib.sha256(domain.encode()).hexdigest() if domain else None
    identity_str = f'{name.strip().lower()}|{city.strip().lower()}|{state}|{website or "no_website"}'
    lih = hashlib.sha256(identity_str.encode()).hexdigest()
    if conn.execute('SELECT 1 FROM leads WHERE lead_identity_hash=?', (lih,)).fetchone(): continue
    inserted_id = bd_db.insert_lead({
        'store_name': name, 'store_type': stype, 'city': city, 'state': state,
        'official_website': website, 'email': '', 'email_source_type': 'unknown',
        'email_verified_on_official_site': 0, 'confidence_score': 'B', 'status': 'new',
        'product_fit': fit, 'source_keyword': 'online brand', 'source_platform': platform,
        'collected_at': now, 'domain_hash': dh, 'lead_identity_hash': lih,
    }, conn=conn)
    if inserted_id:
        added += 1
        print(f'  + {name} ({platform})')

conn.commit()

# Now verify websites
from inventory_recovery_loop import fetch_html, extract_emails, is_safe_email
conn.row_factory = sqlite3.Row

to_verify = conn.execute('''SELECT * FROM leads WHERE store_type="online_brand" AND official_website IS NOT NULL AND official_website!="" AND (email IS NULL OR email="") AND status="new" AND id NOT IN(SELECT lead_id FROM send_log) AND evidence_checked_at IS NULL ORDER BY id DESC LIMIT 25''').fetchall()

print(f'\nVerifying {len(to_verify)} brand websites...')
a0 = b2 = c = rej = 0
for r in to_verify:
    html = fetch_html(r['official_website'])
    if not html:
        conn.execute('UPDATE leads SET evidence_checked_at=?, confidence_score="B", status="manual_review_needed" WHERE id=?', (now, r['id']))
        rej += 1; continue
    emails = [e for e in extract_emails(html) if is_safe_email(e) and not any(bad in e.lower() for bad in ['example.com','wordpress','font','typefoundry','user@domain'])]
    if emails:
        email = emails[0]
        if conn.execute('SELECT 1 FROM suppression_list WHERE email=?', (email,)).fetchone(): continue
        conn.execute('''UPDATE leads SET email=?, email_source_type="official_page_visible", email_verified_on_official_site=1, confidence_score="A", evidence_url=?, evidence_snippet=?, evidence_method="website_http_verified", last_checked_at=? WHERE id=?''',
            (email, r['official_website'], f'Email {email[:3]}*** on {r["official_website"]}', now, r['id']))
        a0 += 1
        print(f'  A0: {r["store_name"][:30]} → {email[:30]}')
    else:
        conn.execute('UPDATE leads SET evidence_checked_at=?, confidence_score="C", status="contact_form_pool" WHERE id=?', (now, r['id']))
        c += 1
        print(f'  C:  {r["store_name"][:30]} → no email (contact form)')

conn.commit()

# Final counts
ra0 = conn.execute('''SELECT COUNT(*) FROM leads WHERE status="new" AND confidence_score="A" AND state IN("TN","AR","KY") AND email_verified_on_official_site=1 AND email!=""''').fetchone()[0]
ca0 = conn.execute('''SELECT COUNT(*) FROM leads WHERE status="new" AND confidence_score="A" AND email_verified_on_official_site=1 AND email!="" AND store_type IN("online_brand","museum_store","national_park_store","visitor_center","school_store","university_store","aquarium_store","historic_site","foundation_store","crowdfunding","independent_creator")''').fetchone()[0]
all_a0 = conn.execute('''SELECT COUNT(DISTINCT email) FROM leads WHERE status="new" AND confidence_score="A" AND email_verified_on_official_site=1 AND email!="" AND email NOT IN(SELECT email FROM suppression_list) AND id NOT IN(SELECT lead_id FROM send_log WHERE status IN("sent","bounced"))''').fetchone()[0]
cc = conn.execute('''SELECT COUNT(*) FROM leads WHERE status IN("contact_form_pool","new") AND confidence_score="C" AND evidence_checked_at IS NOT NULL''').fetchone()[0]

conn.close()
print(f'\nResults: A0={a0} B2={b2} C={c} Reject={rej}')
print(f'Inventory: Retail={ra0} Custom={ca0} Unique={all_a0} Custom_C={cc}')
