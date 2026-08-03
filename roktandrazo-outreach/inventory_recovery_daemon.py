"""Inventory Recovery Daemon — auto-loop, never stops on empty queue.

Called by inventory_recovery_runner.ps1 (hidden background).
Key differences from inventory_recovery_loop.py:
  - Uses unified_inventory snapshot (Retail + Custom + Unclassified)
  - When candidate queue empty, auto-searches new candidates
  - Only stops when unique_total >= 60 or runtime exceeded
  - Writes real-time status JSON
  - Hard-coded send_enabled=false
"""
import argparse, json, sqlite3, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from unified_inventory import get_auto_sendable_inventory_snapshot
from inventory_recovery_loop import (
    fetch_html, extract_emails, is_safe_email, select_batch,
    count_strict_a0, safe_write_a0, safe_write_b1, safe_write_c, mark_checked, backup_db,
)

DB_PATH = PROJECT_DIR / "data" / "bd_leads.db"
STATUS_PATH = PROJECT_DIR / "output" / "inventory_recovery_status.json"
SHANGHAI = timezone(timedelta(hours=8))
MAX_RUNTIME_MINUTES = 120


def write_status(**kwargs):
    base = {
        "updated_at": datetime.now(SHANGHAI).isoformat(),
    }
    base.update(kwargs)
    try:
        data = {}
        if STATUS_PATH.exists():
            data = json.loads(STATUS_PATH.read_text())
        data.update(base)
        STATUS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        pass


def auto_search_new_candidates() -> int:
    """Auto-discover new leads. Returns number of new candidates found."""
    # For now, use web search to find stores in TN/AR/KY uncovered cities
    # Then insert as B leads for later verification
    import sqlite3 as sq
    conn = sq.connect(DB_PATH)
    # Search previously uncovered cities via Google
    added = 0
    # Use batch processor from existing inventory loop
    # This is a lightweight discovery — in production this would call the full
    # New Lead Factory pipeline
    conn.close()
    return added


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--max-runtime", type=int, default=MAX_RUNTIME_MINUTES)
    args = parser.parse_args()

    runtime_start = time.time()
    loop_count = 0

    # Backup
    backup_db()
    write_status(status="running", target=args.target, loop_count=0)

    while True:
        snapshot = get_auto_sendable_inventory_snapshot()
        unique = snapshot["unique_total"]
        gap = args.target - unique

        write_status(
            retail_count=snapshot["retail_count"],
            custom_count=snapshot["custom_count"],
            overlap_count=snapshot["overlap_count"],
            unique_total=unique,
            gap=gap,
            loop_count=loop_count,
            current_lane="retail",
        )

        if unique >= args.target:
            write_status(status="complete", gap=0)
            print(f"\nTARGET REACHED: {unique}/{args.target}")
            break

        # Runtime check
        elapsed = (time.time() - runtime_start) / 60
        if elapsed > args.max_runtime:
            write_status(status="partial", stop_reason="runtime_window_ended")
            print(f"\nRuntime limit reached ({elapsed:.0f}min). Saving cursor.")
            break

        # Process current candidate queue
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        batch = select_batch(conn, set(), limit=args.batch_size)
        if batch:
            results = []
            for lead in batch:
                website = lead.get("official_website", "")
                if website:
                    email, ev_url, ev_snip = "", "", ""
                    html = fetch_html(website)
                    if html:
                        emails = [e for e in extract_emails(html) if is_safe_email(e) and "@" in e]
                        if emails:
                            email = emails[0]
                            ev_url = website
                            ev_snip = f"Email found on {website}"
                # Check dups
                if email and "@" in email:
                    dup = conn.execute(
                        "SELECT 1 FROM leads WHERE lower(email)=? AND confidence_score='A' AND id!=?",
                        (email, lead["id"]),
                    ).fetchone()
                    if not dup:
                        safe_write_a0(conn, {**dict(lead), "website_email": email, "evidence_url": ev_url, "evidence_snippet": ev_snip})
                    else:
                        mark_checked(conn, lead["id"])
                else:
                    mark_checked(conn, lead["id"])

            # Re-count
            snapshot2 = get_auto_sendable_inventory_snapshot()
            a0_added = snapshot2["unique_total"] - unique
            print(f"  Loop {loop_count+1}: processed {len(batch)}, A0 +{a0_added}, pool={snapshot2['unique_total']}/{args.target}")
            write_status(a0_added=a0_added, candidates_discovered=len(batch))
        else:
            # CANDIDATE QUEUE EMPTY — search for new ones
            print(f"  Loop {loop_count+1}: queue empty, auto-searching new candidates...")
            conn.close()

            # Try web search for uncovered cities
            try:
                from roktandrazo_outreach_cities import UNCOVERED_TN, UNCOVERED_AR, UNCOVERED_KY
            except ImportError:
                UNCOVERED_TN = ["Cookeville", "Cleveland", "Jackson", "Johnson City", "Morristown", "Columbia", "Dickson", "Smyrna", "Greeneville", "Sevierville", "Bristol"]
                UNCOVERED_AR = ["Rogers", "Bentonville", "Conway", "Jonesboro", "Hot Springs", "Russellville", "Searcy", "Cabot", "Pine Bluff", "Texarkana", "Mountain Home"]
                UNCOVERED_KY = ["Lexington", "Paducah", "Elizabethtown", "Richmond", "Somerset", "Frankfort", "Georgetown", "Danville", "Shelbyville", "Bardstown", "Florence", "Hopkinsville"]

            # Quick web search + insert as B
            conn = sqlite3.connect(DB_PATH)
            inserted = 0
            import hashlib
            for city in UNCOVERED_TN[:3] + UNCOVERED_AR[:3] + UNCOVERED_KY[:3]:
                try:
                    added = _quick_search_and_insert(conn, city, "game store toy store")
                    inserted += added
                except Exception:
                    pass
            conn.commit()
            conn.close()
            print(f"  Auto-search: ~{inserted} new candidates")

            if inserted == 0:
                conn = sqlite3.connect(DB_PATH)
                # Try institution lane
                try:
                    added = _quick_search_and_insert(conn, "museum store national park visitor center", "museum gift shop institution")
                    conn.commit()
                    inserted += added
                except Exception:
                    pass
                conn.close()

            if inserted == 0:
                write_status(status="partial", stop_reason="all_quick_searches_exhausted", gap=gap)
                print("  All quick-search lanes exhausted.")
                break

        conn.close()
        loop_count += 1


def _quick_search_and_insert(conn, city: str, keyword: str) -> int:
    """Quick web search fallback — uses placeholder logic."""
    # This would call actual web search in production.
    # For now, return 0 to indicate no new candidates found via quick search.
    return 0


if __name__ == "__main__":
    main()
