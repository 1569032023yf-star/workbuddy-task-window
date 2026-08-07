raise RuntimeError("LEGACY_INVENTORY_ARCHIVED: use inventory_monitor_executor")
"""Scale run: BackerKit, Kickstarter, Gamefound, Amazon. Stop when Unique A0 >= 30."""
import sqlite3, hashlib, sys
from datetime import datetime
sys.path.insert(0, '.')
import bd_db
from inventory_recovery_loop import fetch_html, extract_emails, is_safe_email

conn = sqlite3.connect('data/bd_leads.db')
conn.row_factory = sqlite3.Row
now = datetime.now().isoformat()

# BackerKit + Kickstarter + Gamefound + Amazon candidates
candidates = [
    # BackerKit (10)
    ('Pushing Tin Games','online_brand','','','https://pushingtingames.com','','card games, Halloween Hijinks, BackerKit','BackerKit'),
    ('Wotan Games','online_brand','London','','https://www.wotangames.com','','Pipes card game, Pocketopia, BackerKit','BackerKit'),
    ('Elements of Truth (Veritasium)','online_brand','','','https://www.veritasium.com','','tabletop trivia game, BackerKit trending','BackerKit'),
    ('Mystic Lands AEG','online_brand','','','','','card crafting game, AEG publisher, BackerKit','BackerKit'),
    ('Mausritter Junk City','online_brand','','','','','Mausritter RPG expansion, BackerKit','BackerKit'),
    ('Vampire Survivors Board Game','online_brand','','','','','video game adaptation, BackerKit','BackerKit'),
    ('Dungeons of Drakkenheim','online_brand','','','','','Daggerheart adventure, Ghostfire Gaming, BackerKit','BackerKit'),
    ('River Market','online_brand','','','','','Creature Comforts spinoff, Kids Table BG, BackerKit','BackerKit'),
    ('The Big Squeeze','online_brand','','','','','lemonade apocalypse engine builder, BackerKit','BackerKit'),
    ('Army of Darkness Board Game','online_brand','','','','','Dynamite/Lynnvander, BackerKit','BackerKit'),
    # Kickstarter (10)
    ('Cataclysm Arcade TCG','online_brand','New York','NY','','','TCG pack-opening game, Mothership Games, KS','Kickstarter'),
    ('SHUG','online_brand','London','','','','party dungeon crawler, Wandering Games, KS','Kickstarter'),
    ('Notebook Nations','online_brand','Red Bluff','CA','','','cozy empire builder, Minerva Studio, KS','Kickstarter'),
    ('Weasel Wars','online_brand','','','','','tactical weasel adventure, dartfrog games, KS','Kickstarter'),
    ('Hover Hummingbird Game','online_brand','San Diego','CA','','','educational animal game, KS','Kickstarter'),
    ('Epic Brick Adventures','online_brand','Nanaimo','','','','brick-building RPG, Tinker Troll Games, KS','Kickstarter'),
    ('Die in the Dungeon BG','online_brand','Vancouver','','','','roguelike dice placement, Roomiz Games, KS','Kickstarter'),
    ('Galileos Truth','online_brand','','','','','competitive euro game, Awaken Realms, KS','Kickstarter'),
    ('Aeons End System Overload','online_brand','','','','','standalone expansion, Indie Boards & Cards, KS','Kickstarter'),
    ('The Crucible','online_brand','','','','','coop tactical campaign, Nocturna, KS','Kickstarter'),
    # Gamefound (8)
    ('Jump Masters','online_brand','','','','','drafting combat game, Gamefound 2026','Gamefound'),
    ('Zombicide Dead Men Tales','online_brand','','','','','Fantasy Flight/Asmodee, Gamefound top','Gamefound'),
    ('Onward MOBA Board Game','online_brand','','','','','Skytear Games reprint, Gamefound trending','Gamefound'),
    ('Tamashii Final Amendment','online_brand','','','','','Awaken Realms, Gamefound','Gamefound'),
    ('The Witcher Legacy','online_brand','','','','','Go On Board, Gamefound','Gamefound'),
    ('Last Arc Tactics','online_brand','','','','','Succubus Publishing, Gamefound','Gamefound'),
    ('Agricola Special Edition','online_brand','','','','','Awaken Realms, Gamefound','Gamefound'),
    ('HELLDIVERS 2 Board Game','online_brand','','','','','Steamforged Games, Gamefound','Gamefound'),
    # Amazon (8)
    ('Unstable Games','online_brand','','','https://www.unstablegames.com','','Unstable Unicorns, own brand card games, Amazon','Amazon'),
    ('Cards Against Humanity','online_brand','Chicago','IL','https://www.cardsagainsthumanity.com','','own brand party card game','Amazon'),
    ('What Do You Meme','online_brand','New York','NY','https://whatdoyoumeme.com','','own brand party card games, Amazon bestseller','Amazon'),
    ('CGE Czech Games','online_brand','','','https://czechgames.com','','Codenames, own brand card & board games','Amazon'),
    ('Bezier Games','online_brand','','','https://beziergames.com','','Werewolf, One Night, own brand party games','Amazon'),
    ('Ultra PRO','online_brand','','','https://www.ultrapro.com','','card sleeves, playing cards, accessories, own brand','Amazon'),
    ('Space Cowboys','online_brand','','','https://www.spacecowboys.fr','','Splendor, own brand card games','Amazon'),
    ('Asmodee','online_brand','','','https://www.asmodee.com','','major publisher, distribute many card game brands','Amazon'),
]

# Insert all
added = 0
for name,stype,city,state,website,email,fit,platform in candidates:
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
conn.commit()

# Count current A0
def count_a0():
    return conn.execute('''SELECT COUNT(DISTINCT email) FROM leads WHERE status="new" AND confidence_score="A" AND email_verified_on_official_site=1 AND email!="" AND email NOT IN(SELECT email FROM suppression_list) AND id NOT IN(SELECT lead_id FROM send_log WHERE status IN("sent","bounced"))''').fetchone()[0]

start_a0 = count_a0()
print(f'Start A0: {start_a0}, Added: {added}, Target: 30')

# Verify websites
to_verify = conn.execute('''SELECT * FROM leads WHERE store_type="online_brand" AND official_website IS NOT NULL AND official_website!="" AND (email IS NULL OR email="") AND status="new" AND evidence_checked_at IS NULL AND id NOT IN(SELECT lead_id FROM send_log) ORDER BY id LIMIT 25''').fetchall()

a0_new = b2 = c = rej = 0
for r in to_verify:
    if count_a0() >= 30:
        print(f'  TARGET REACHED ({count_a0()} >= 30), stopping verification')
        break
    
    html = fetch_html(r['official_website'])
    if not html:
        conn.execute('UPDATE leads SET evidence_checked_at=?, confidence_score="B" WHERE id=?', (now, r['id']))
        rej += 1; continue
    
    emails = [e for e in extract_emails(html) if is_safe_email(e) and not any(bad in e.lower() for bad in ['example.com','wordpress','font','typefoundry','user@domain','@anthropic','@openai'])]
    if emails:
        email = emails[0]
        if conn.execute('SELECT 1 FROM suppression_list WHERE email=?', (email,)).fetchone(): continue
        if conn.execute('SELECT 1 FROM leads WHERE email=? AND confidence_score="A" AND id!=?', (email, r['id'])).fetchone(): continue
        conn.execute('''UPDATE leads SET email=?, email_source_type="official_page_visible", email_verified_on_official_site=1, confidence_score="A", evidence_url=?, evidence_snippet=?, evidence_method="website_http_verified", last_checked_at=? WHERE id=?''',
            (email, r['official_website'], f'Email found on {r["official_website"]}', now, r['id']))
        a0_new += 1
        print(f'  A0: {r["store_name"][:30]} → {email[:30]}')
    else:
        conn.execute('UPDATE leads SET evidence_checked_at=?, confidence_score="C", status="contact_form_pool" WHERE id=?', (now, r['id']))
        c += 1

conn.commit()

final = count_a0()
# Platform stats
plats = {}
for p in ['Amazon','Kickstarter','Gamefound','BackerKit','Shopify','Etsy']:
    a = conn.execute('SELECT COUNT(*) FROM leads WHERE source_platform=? AND confidence_score="A" AND email!="" AND email_verified_on_official_site=1 AND id NOT IN(SELECT lead_id FROM send_log)', (p,)).fetchone()[0]
    total = conn.execute('SELECT COUNT(*) FROM leads WHERE source_platform=?', (p,)).fetchone()[0]
    c_count = conn.execute('SELECT COUNT(*) FROM leads WHERE source_platform=? AND confidence_score="C"', (p,)).fetchone()[0]
    plats[p] = (total, a, c_count)

conn.close()
print(f'\nStart={start_a0} → Final={final} (A0_added={a0_new}, C={c})')
for p, (t, a, cc) in plats.items():
    print(f'  {p}: candidates={t} A0={a} C={cc}')
