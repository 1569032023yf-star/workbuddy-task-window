"""Unified Auto-Sendable Inventory Snapshot — single source of truth."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "bd_leads.db"

EXCLUDED_NAMES = frozenset({
    "Cards Against Humanity", "What Do You Meme",
    "Ridleys Games", "Ultra PRO",
})


def get_auto_sendable_inventory_snapshot() -> dict:
    conn = sqlite3.connect(f"file:{DB_PATH.resolve().as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT DISTINCT id, store_name, city, state, email, store_type,
               source_platform, lead_identity_hash
        FROM leads
        WHERE status = 'new'
          AND confidence_score = 'A'
          AND email_verified_on_official_site = 1
          AND email IS NOT NULL AND email != ''
          AND email LIKE '%@%'
          AND email NOT IN (SELECT email FROM suppression_list WHERE email IS NOT NULL)
          AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent', 'bounced'))
          AND (mx_provider IS NULL OR mx_provider = ''
               OR (mx_provider NOT LIKE '%exchange%'
                   AND mx_provider NOT LIKE '%outlook%'
                   AND mx_provider NOT LIKE '%microsoft%'))
    """).fetchall()
    conn.close()

    # ── Dedup by identity + email ──
    seen_lih = {}
    seen_email = {}
    deduped = []
    for r in rows:
        lih = r["lead_identity_hash"] or ""
        email = (r["email"] or "").strip().lower()
        if lih and lih in seen_lih:
            continue
        if email and email in seen_email:
            continue
        seen_lih[lih] = r["id"]
        seen_email[email] = r["id"]
        deduped.append(r)

    # ── Exclude manual review brands, then classify ──
    retail_ids = set()
    custom_ids = set()

    for r in deduped:
        name = r["store_name"] or ""
        if name in EXCLUDED_NAMES:
            continue
        eid = r["id"]
        st = r["state"] or ""
        sty = r["store_type"] or ""
        if st in ("TN", "AR", "KY"):
            retail_ids.add(eid)
        if sty in (
            "museum_store", "national_park_store", "visitor_center",
            "school_store", "university_store", "aquarium_store",
            "historic_site", "foundation_store",
            "online_brand", "crowdfunding", "independent_creator",
        ):
            custom_ids.add(eid)

    overlap_ids = retail_ids & custom_ids
    all_classified = {r["id"] for r in deduped if r["store_name"] not in EXCLUDED_NAMES}
    unclassified_ids = all_classified - retail_ids - custom_ids
    unique_ids = retail_ids | custom_ids | unclassified_ids

    unique_total = len(unique_ids)
    formula = len(retail_ids) + len(custom_ids) - len(overlap_ids) + len(unclassified_ids)

    return {
        "retail_ids": retail_ids,
        "custom_ids": custom_ids,
        "overlap_ids": overlap_ids,
        "unclassified_ids": unclassified_ids,
        "retail_count": len(retail_ids),
        "custom_count": len(custom_ids),
        "overlap_count": len(overlap_ids),
        "unclassified_count": len(unclassified_ids),
        "unique_total": unique_total,
        "target": 60,
        "safety_target": 30,
        "gap": 60 - unique_total,
        "verified_formula": formula == unique_total,
        "raw_before_dedup": len(rows),
        "dedup_removed": len(rows) - len(deduped),
        "manual_review_excluded": len(EXCLUDED_NAMES),
    }


if __name__ == "__main__":
    s = get_auto_sendable_inventory_snapshot()
    print(
        f"Retail={s['retail_count']} Custom={s['custom_count']} "
        f"Overlap={s['overlap_count']} Unclass={s['unclassified_count']}"
    )
    print(f"Unique={s['unique_total']} Target={s['target']} Gap={s['gap']}")
    print(f"Formula verified: {s['verified_formula']} (raw={s['raw_before_dedup']} dedup={s['dedup_removed']})")
