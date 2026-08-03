"""New Lead Factory — batch insert TN/AR/KY store discoveries."""
import hashlib
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))
import bd_db

DB_PATH = PROJECT_DIR / "data" / "bd_leads.db"

NEW_LEADS = [
    # ===== TENNESSEE =====
    {
        "store_name": "Phillips Toy Mart",
        "store_type": "toy_store",
        "city": "Nashville",
        "state": "TN",
        "official_website": "https://phillipstoymart.com/",
        "email": "support@phillipstoymart.com",
        "email_source_type": "official_page_visible",
        "email_verified_on_official_site": 1,
        "confidence_score": "A",
        "evidence_url": "https://phillipstoymart.com/",
        "evidence_snippet": "Phillips Toy Mart family-owned since 1946, puzzles games toys, Nashville TN",
        "evidence_method": "web_search_manual_seed",
        "product_fit": "puzzles_games_toys",
        "source_keyword": "nashville toy store puzzle",
        "status": "new",
    },
    {
        "store_name": "Smart Toys & Books",
        "store_type": "toy_store",
        "city": "Knoxville",
        "state": "TN",
        "official_website": "https://www.smarttoysandbooks.com/",
        "email": "",
        "email_source_type": "unknown",
        "confidence_score": "B",
        "product_fit": "puzzles_games_toys_books",
        "source_keyword": "knoxville toy store puzzle",
        "status": "manual_review_needed",
    },
    {
        "store_name": "Mast General Store",
        "store_type": "general_store",
        "city": "Knoxville",
        "state": "TN",
        "official_website": "https://www.mastgeneralstore.com/",
        "email": "",
        "email_source_type": "unknown",
        "confidence_score": "B",
        "product_fit": "puzzles_gifts_outdoor",
        "source_keyword": "knoxville general store puzzle",
        "status": "manual_review_needed",
    },

    # ===== ARKANSAS =====
    {
        "store_name": "Treasure Chest Games",
        "store_type": "game_store",
        "city": "Conway",
        "state": "AR",
        "official_website": "https://www.tcgames.net/",
        "email": "tcgamesconway@gmail.com",
        "email_source_type": "official_page_visible",
        "email_verified_on_official_site": 1,
        "confidence_score": "A",
        "evidence_url": "https://www.tcgames.net/",
        "evidence_snippet": "Treasure Chest Games Conway AR, board card family games, free in-store play",
        "evidence_method": "web_search_manual_seed",
        "product_fit": "board_games_card_games",
        "source_keyword": "conway arkansas game store",
        "status": "new",
    },
    {
        "store_name": "Sugar & Spite",
        "store_type": "gift_shop",
        "city": "Eureka Springs",
        "state": "AR",
        "official_website": "",
        "email": "",
        "email_source_type": "unknown",
        "confidence_score": "B",
        "product_fit": "gifts_toys",
        "source_keyword": "eureka springs gift shop",
        "status": "manual_review_needed",
    },

    # ===== KENTUCKY =====
    {
        "store_name": "Playthings Toy Shoppe",
        "store_type": "toy_store",
        "city": "Louisville",
        "state": "KY",
        "official_website": "https://playthingstoyshoppe.com/",
        "email": "",
        "email_source_type": "unknown",
        "confidence_score": "B",
        "product_fit": "toys_games_puzzles",
        "source_keyword": "louisville toy store",
        "status": "manual_review_needed",
    },
    {
        "store_name": "The Treasured Child",
        "store_type": "toy_store",
        "city": "La Grange",
        "state": "KY",
        "official_website": "",
        "email": "",
        "email_source_type": "unknown",
        "confidence_score": "B",
        "product_fit": "toys_games_puzzles",
        "source_keyword": "la grange kentucky toy store",
        "status": "manual_review_needed",
    },
    {
        "store_name": "Legendary Games",
        "store_type": "game_store",
        "city": "Lexington",
        "state": "KY",
        "official_website": "",
        "email": "",
        "email_source_type": "unknown",
        "confidence_score": "B",
        "product_fit": "board_games_card_games",
        "source_keyword": "lexington game store puzzle",
        "status": "manual_review_needed",
    },
    {
        "store_name": "D20 Hobbies",
        "store_type": "game_store",
        "city": "Lexington",
        "state": "KY",
        "official_website": "",
        "email": "",
        "email_source_type": "unknown",
        "confidence_score": "B",
        "product_fit": "board_games_tcg_rpg",
        "source_keyword": "lexington hobby game store",
        "status": "manual_review_needed",
    },
    {
        "store_name": "Joseph-Beth Booksellers",
        "store_type": "bookstore",
        "city": "Lexington",
        "state": "KY",
        "official_website": "https://www.josephbeth.com/",
        "email": "",
        "email_source_type": "unknown",
        "confidence_score": "B",
        "product_fit": "books_puzzles_gifts",
        "source_keyword": "lexington bookstore puzzle",
        "status": "manual_review_needed",
    },
    {
        "store_name": "Heart Strings",
        "store_type": "gift_shop",
        "city": "Bowling Green",
        "state": "KY",
        "official_website": "",
        "email": "",
        "email_source_type": "unknown",
        "confidence_score": "B",
        "product_fit": "gifts_jewelry_puzzles",
        "source_keyword": "bowling green gift shop puzzle",
        "status": "manual_review_needed",
    },
]


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    now = datetime.now().isoformat()

    inserted = 0
    skipped = 0

    for lead in NEW_LEADS:
        # Duplicate check: store_name + city + state
        existing = c.execute(
            "SELECT id FROM leads WHERE store_name = ? AND city = ? AND state = ?",
            (lead['store_name'], lead['city'], lead['state'])
        ).fetchone()

        if existing:
            print(f"  SKIP: {lead['store_name']} ({lead['city']}, {lead['state']}) — already in DB (id={existing['id']})")
            skipped += 1
            continue

        # Domain hash — NULL for leads without website
        website_url = lead.get('official_website', '')
        domain = website_url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0] if website_url else ''
        dh = hashlib.sha256(domain.encode()).hexdigest() if domain else None

        # Domain uniqueness check (only if domain exists)
        if domain:
            dup = c.execute("SELECT id FROM leads WHERE domain_hash = ?", (dh,)).fetchone()
            if dup:
                print(f"  SKIP: {lead['store_name']} — domain already exists (id={dup['id']})")
                skipped += 1
                continue

        inserted_id = bd_db.insert_lead(
            {
                **lead,
                "evidence_method": lead.get("evidence_method", "web_search_manual_seed"),
                "collected_at": now,
                "last_checked_at": now,
                "domain_hash": dh,
            },
            conn=conn,
        )
        if inserted_id:
            inserted += 1
            print(f"  ADDED: {lead['store_name']} ({lead['city']}, {lead['state']}) | {lead['confidence_score']} | {lead.get('email','no email')[:30]}")
        else:
            skipped += 1

    conn.commit()

    # Final count
    total = c.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    a0s = c.execute("""
        SELECT COUNT(*) FROM leads WHERE status='new' AND confidence_score='A'
        AND email_verified_on_official_site=1
        AND email IS NOT NULL AND email != ''
    """).fetchone()[0]

    conn.close()

    print(f"\nInserted: {inserted}  |  Skipped: {skipped}  |  Total leads now: {total}  |  A0 with email: {a0s}")


if __name__ == '__main__':
    main()
