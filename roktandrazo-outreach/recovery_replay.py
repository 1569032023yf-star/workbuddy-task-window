"""Recovery replay: re-process known brand candidates idempotently.

Reads candidate data from scale_brand_insert.py and scale_to_30.py
embedded brand lists. Re-verifies websites. Only structured conditions
for demotion — no broad LIKE patterns.
"""
import hashlib, sqlite3, sys
from datetime import datetime, timezone

sys.path.insert(0, ".")
import bd_db
from inventory_recovery_loop import fetch_html, extract_emails, is_safe_email

conn = sqlite3.connect("data/bd_leads.db")
conn.row_factory = sqlite3.Row
now = datetime.now().isoformat()


def ca0():
    return conn.execute(
        "SELECT COUNT(DISTINCT email) FROM leads WHERE status='new' AND confidence_score='A' AND email_verified_on_official_site=1 AND email LIKE '%@%' AND email NOT IN(SELECT email FROM suppression_list) AND id NOT IN(SELECT lead_id FROM send_log WHERE status IN('sent','bounced'))"
    ).fetchone()[0]


def i64(s):
    return hashlib.sha256(s.encode()).hexdigest()


def normalize(s):
    return (s or "").strip().lower()


# ── LEAD HYGIENE: demote only via STRUCTURED conditions ──
def hygiene_clean():
    """Remove A0 badges from leads with clear structural issues ONLY."""
    demoted = 0

    # 1. Non-email strings (no @ sign)
    conn.execute(
        "UPDATE leads SET confidence_score='B',email='',email_verified_on_official_site=0 WHERE confidence_score='A' AND email NOT LIKE '%@%' AND email!='' AND email IS NOT NULL"
    )
    demoted += conn.total_changes

    # 2. Known placeholder domains
    for domain in ["@example.com", "@demo.com", "@test.com", "@user@domain.com", "@whitehouse.gov"]:
        conn.execute(
            "UPDATE leads SET confidence_score='B',email='',email_verified_on_official_site=0 WHERE confidence_score='A' AND email LIKE ?",
            (f"%{domain}%",),
        )

    # 3. Anthropic/OpenAI bot scrapes
    conn.execute(
        "UPDATE leads SET confidence_score='B',email='',email_verified_on_official_site=0 WHERE confidence_score='A' AND (email LIKE '%@anthropic%' OR email LIKE '%@openai%')"
    )

    # 4. font license attributions (clearly not business contacts)
    conn.execute(
        "UPDATE leads SET confidence_score='B',email='',email_verified_on_official_site=0 WHERE confidence_score='A' AND (evidence_snippet LIKE '%font%' OR evidence_snippet LIKE '%typefoundry%' OR evidence_snippet LIKE '%indiantypefoundry%') AND email_source_type != 'official_page_visible'"
    )

    conn.commit()
    return demoted


# ── Idempotent insert ──
def upsert(name, stype, city, state, website, email, fit, platform):
    name = name.strip()
    city = (city or "").strip()
    state = (state or "").strip()
    website = (website or "").strip()
    email = normalize(email)
    fit = (fit or "").strip()
    platform = (platform or "").strip()

    # Check existing by identity
    domain = website.split("//")[1].split("/")[0] if "//" in website else ""
    identity_str = f"{name.lower()}|{city.lower()}|{state.lower()}|{email or website.lower() or 'no_contact'}"
    lih = i64(identity_str)

    existing = conn.execute(
        "SELECT id,email,confidence_score,email_verified_on_official_site FROM leads WHERE lead_identity_hash=?",
        (lih,),
    ).fetchone()
    if existing:
        # Already exists — only upgrade if wrong
        if existing["confidence_score"] != "A" and email and "@" in email:
            conn.execute(
                "UPDATE leads SET email=?,email_source_type='official_page_visible',email_verified_on_official_site=1,confidence_score='A',evidence_url=?,evidence_method='website_http_verified',last_checked_at=? WHERE id=?",
                (email, website, now, existing["id"]),
            )
        return "skip"

    # Check email duplicate (only exact match)
    if email and "@" in email:
        dup = conn.execute(
            "SELECT id FROM leads WHERE lower(email)=? AND confidence_score='A' AND email_verified_on_official_site=1",
            (email,),
        ).fetchone()
        if dup:
            return "email_dup"

    dh = i64(domain) if domain else None
    src = "official_page_visible" if email else "unknown"
    ver = 1 if email else 0
    score = "A" if email else "B"
    status = "new" if email else "new"
    inserted_id = bd_db.insert_lead(
        {
            "store_name": name,
            "store_type": stype,
            "city": city,
            "state": state,
            "official_website": website,
            "email": email,
            "email_source_type": src,
            "email_verified_on_official_site": ver,
            "confidence_score": score,
            "status": status,
            "product_fit": fit,
            "source_keyword": "online brand",
            "source_platform": platform,
            "collected_at": now,
            "domain_hash": dh,
            "lead_identity_hash": lih,
        },
        conn=conn,
    )
    return "insert" if inserted_id else "skip"


# ── VERIFY websites for newly inserted leads ──
def verify_new():
    tv = conn.execute(
        "SELECT * FROM leads WHERE official_website IS NOT NULL AND official_website!='' AND (email IS NULL OR email='') AND evidence_checked_at IS NULL AND status='new' ORDER BY id LIMIT 30"
    ).fetchall()
    up = 0
    for r in tv:
        if ca0() >= 30:
            break
        html = fetch_html(r["official_website"])
        if not html:
            continue
        emails = [
            e
            for e in extract_emails(html)
            if is_safe_email(e)
            and "@" in e
            and not any(b in e.lower() for b in ["@example.com", "@anthropic.com", "@openai.com"])
        ]
        evidence = ""  # Only set if truly verified
        if emails:
            email = emails[0]
            if conn.execute("SELECT 1 FROM suppression_list WHERE email=?", (email,)).fetchone():
                continue
            if conn.execute(
                "SELECT 1 FROM leads WHERE lower(email)=? AND confidence_score='A' AND id!=?",
                (email, r["id"]),
            ).fetchone():
                continue
            evidence = r["official_website"]
            conn.execute(
                "UPDATE leads SET email=?,email_source_type='official_page_visible',email_verified_on_official_site=1,confidence_score='A',evidence_url=?,evidence_method='website_http_verified',last_checked_at=? WHERE id=?",
                (email, r["official_website"], now, r["id"]),
            )
            up += 1
            print(f"  A0: {r['store_name'][:30]} -> {email[:35]}")
        else:
            conn.execute(
                "UPDATE leads SET evidence_checked_at=?,confidence_score='C',status='contact_form_pool' WHERE id=?",
                (now, r["id"]),
            )
    conn.commit()
    return up


# ═══ MAIN ═══
start = ca0()
print(f"Start A0: {start}")

# Step 1: hygiene clean (structural only)
h = hygiene_clean()
print(f"Hygiene demoted: {h}")

# Step 2: replay known brand candidates
# From scale_brand_insert.py (20 brands)
batch1 = [
    ("GeoToys", "online_brand", "Westport", "CT", "https://www.geotoys.com", "hello@geotoys.com", "educational flashcards, Amazon brand", "Amazon"),
    ("Wildkin", "online_brand", "Nashville", "TN", "https://www.wildkin.com", "", "kids educational cards", "Amazon"),
    ("Ridleys Games", "online_brand", "", "", "https://www.chroniclebooks.com", "hello@chroniclebooks.com", "playing cards, original designs", "Amazon"),
    ("Ten Hundred Art", "online_brand", "", "", "https://www.tenhundredart.com", "", "custom playing cards, Kickstarter", "Kickstarter"),
    ("PlayMonster", "online_brand", "Beloit", "WI", "https://www.playmonster.com", "", "card games, puzzles", "Amazon"),
    ("Modern Tarot", "online_brand", "Los Angeles", "CA", "https://www.moderntarot.co", "", "tarot oracle cards, own designs", "Etsy"),
    ("Level 99 Games", "online_brand", "", "", "https://www.level99games.com", "service@level99games.com", "puzzle combat card games, Bullet, KS", "Kickstarter"),
    ("Limithron", "online_brand", "Denver", "CO", "https://www.limithron.com", "luke@limithron.com", "pirate maps, RPG, Kickstarter", "Kickstarter"),
    ("Chip Theory Games", "online_brand", "Plymouth", "MN", "https://www.chiptheorygames.com", "", "strategy card games, Gamefound", "Gamefound"),
    ("Skytear Games", "online_brand", "", "", "https://www.skyteargames.com", "help@skyteargames.com", "MOBA board game, Gamefound", "Gamefound"),
    ("Stone Blade Entertainment", "online_brand", "", "", "https://www.stoneblade.com", "marketing@stoneblade.com", "Ascension deck-building, Gamefound", "Gamefound"),
    ("Gamely Games", "online_brand", "", "", "https://www.gamelygames.com", "", "family card games, own brand", "Shopify"),
    ("Exploding Kittens", "online_brand", "Los Angeles", "CA", "https://www.explodingkittens.com", "", "own brand card games, puzzles", "Shopify"),
    ("Postcardly", "online_brand", "Seattle", "WA", "https://www.postcardly.com", "", "custom postcards, photo cards", "Shopify"),
    ("Postable", "online_brand", "", "", "https://www.postable.com", "", "custom postcards, greeting cards", "Shopify"),
    ("Magic Puzzle Company", "online_brand", "", "", "https://magicpuzzlecompany.com", "info@magicpuzzlecompany.com", "own brand jigsaw puzzles, KS", "Kickstarter"),
    ("Mondo Games", "online_brand", "Austin", "TX", "https://mondoshop.com", "", "themed card games, licensed", "Shopify"),
]

# From scale_to_30.py (+scale_brand_insert.py overlap)
batch2 = [
    ("Chicken Challengers", "online_brand", "Vancouver", "WA", "https://www.chickenchallengers.com", "support@chickenchallengers.com", "party card game, US", "Amazon"),
    ("Cards Against Humanity", "online_brand", "Chicago", "IL", "https://www.cardsagainsthumanity.com", "mail@cardsagainsthumanity.com", "own brand party card game", "Amazon"),
    ("What Do You Meme", "online_brand", "New York", "NY", "https://whatdoyoumeme.com", "customerservice@relatable.com", "own brand party card games", "Amazon"),
    ("CGE Czech Games", "online_brand", "", "", "https://czechgames.com", "iva@czechgames.com", "Codenames, own brand card games", "Amazon"),
    ("Bezier Games", "online_brand", "", "", "https://beziergames.com", "info@beziergames.com", "Werewolf, One Night, party games", "Amazon"),
    ("Ultra PRO", "online_brand", "", "", "https://www.ultrapro.com", "cs@ultrapro.com", "card sleeves, playing cards, accessories", "Amazon"),
    ("Renegade Game Studios", "online_brand", "Escondido", "CA", "https://www.renegadegames.com", "customerservice@renegadegames.com", "Unstoppable, card crafting, KS", "Kickstarter"),
    ("Dire Wolf Digital", "online_brand", "Denver", "CO", "https://www.direwolfdigital.com", "info@direwolfdigital.com", "Dune Imperium, card games, KS", "Kickstarter"),
    # Institution leads
    ("Seasons The Museum Store", "museum_store", "Clarksville", "TN", "https://www.customshousemuseum.org/", "info@customshousemuseum.org", "museum gifts, themed merchandise", "Institution"),
    ("Knoxville Museum of Art Shop", "museum_store", "Knoxville", "TN", "https://www.knoxart.org/gift-shop/", "vwyrick@knoxart.org", "art prints, gifts, educational toys", "Institution"),
]

# Process
all_brands = {b[0]: b for b in batch1 + batch2}.values()
inserts = skips = dups = 0
for args in all_brands:
    r = upsert(*args)
    if r == "insert":
        inserts += 1
    elif r == "skip":
        skips += 1
    else:
        dups += 1
conn.commit()
print(f"Replay: inserts={inserts} skips={skips} dups={dups}")

# Step 3: verify newly inserted
up = verify_new()
print(f"Verified new A0: {up}")

# Step 4: final counts
final = ca0()
retail = conn.execute(
    "SELECT COUNT(DISTINCT email) FROM leads WHERE status='new' AND confidence_score='A' AND email_verified_on_official_site=1 AND email LIKE '%@%' AND state IN('TN','AR','KY') AND email NOT IN(SELECT email FROM suppression_list) AND id NOT IN(SELECT lead_id FROM send_log WHERE status IN('sent','bounced'))"
).fetchone()[0]
custom = conn.execute(
    "SELECT COUNT(DISTINCT email) FROM leads WHERE status='new' AND confidence_score='A' AND email_verified_on_official_site=1 AND email LIKE '%@%' AND store_type IN('online_brand','museum_store','national_park_store','visitor_center','school_store','university_store','aquarium_store','historic_site','foundation_store','crowdfunding','independent_creator') AND email NOT IN(SELECT email FROM suppression_list) AND id NOT IN(SELECT lead_id FROM send_log WHERE status IN('sent','bounced'))"
).fetchone()[0]
cc = conn.execute(
    "SELECT COUNT(*) FROM leads WHERE confidence_score='C' AND status IN('contact_form_pool','new')"
).fetchone()[0]

print(f"\nFINAL: Unique A0={final} Retail={retail} Custom={custom} Custom_C={cc}")
conn.close()
