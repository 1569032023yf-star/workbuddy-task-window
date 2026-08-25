"""Rescan V2 inventory live — read-only, authoritative Source of Truth = bd_leads.db."""
import os, sys, sqlite3
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# Manual .env loader (avoid python-dotenv dependency)
def _load_env(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass
_load_env(os.path.join(BASE, ".env"))

from campaign_eligible_v2 import scan_v2_inventory

DB = os.path.join(BASE, "data", "bd_leads.db")
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# All leads with a real email that are NOT already sent/bounced/do_not_contact etc.
rows = conn.execute(
    """SELECT id FROM leads
       WHERE email IS NOT NULL AND email != '' AND email LIKE '%@%.%'
         AND status NOT IN ('sent','bounced','do_not_contact','rejected','failed','delivery_issue','bounce_review','contact_form_pool')
       ORDER BY id"""
).fetchall()
ids = [r["id"] for r in rows]
print(f"[scan] candidate lead_ids with email (unsent): {len(ids)}")

results = scan_v2_inventory(ids, conn)

eligible = [r for r in results if r["eligible"]]
print(f"[scan] CAMPAIGN_ELIGIBLE_V2 = {len(eligible)}")

# Timezone grouping for eligible V2
from collections import Counter
tz = Counter()
detail = []
for r in eligible:
    row = conn.execute("SELECT recipient_timezone, timezone_status, state, status, email_source_type, email, store_name FROM leads WHERE id=?", (r["lead_id"],)).fetchone()
    tz[row["recipient_timezone"] or "UNSET"] += 1
    detail.append((r["lead_id"], row["store_name"], row["state"], row["recipient_timezone"], row["timezone_status"], r["tier"], r["mx_status"], row["email"]))

print("[scan] timezone distribution:", dict(tz))
print("[scan] eligible V2 detail:")
for d in detail:
    print(f"  id={d[0]:>5} {d[1][:34]:<34} {d[2]:<3} tz={str(d[3]):<6} {d[4]:<9} {d[5]:<4} mx={d[6]:<10} {d[7]}")

# Also report how many are already 'sent' but V2-eligible (should be 0)
conn.close()
