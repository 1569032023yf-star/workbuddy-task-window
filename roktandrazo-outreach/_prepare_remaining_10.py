import sqlite3, importlib.util, os, json
for line in open(".env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

import bd_template, final_send_plan
from env_loader import is_configured

DB = "data/bd_leads.db"
SPEC = importlib.util.spec_from_file_location("cev2", "campaign_eligible_v2.py")
cev2 = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(cev2)

conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
batch_date = "2026-08-18"
remaining = [727,802,814,815,839,883,923,1018,1053,1054]  # 11 V2 minus canary 1055

assert is_configured(), "SMTP not configured"

prepared = []
for lead_id in remaining:
    row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    if not row:
        print("SKIP id=%d NOT FOUND" % lead_id); continue
    lead = dict(row)
    res = cev2.scan_v2_inventory([lead_id], conn=conn)
    v2 = res[0]
    if not v2.get("eligible"):
        print("SKIP id=%d V2 FAIL reasons=%s" % (lead_id, v2.get("reasons"))); continue
    bd_template.apply_email_to_lead(lead)
    plan_id = final_send_plan.create_plan(conn, [lead], batch_date, "new_outreach",
                                          eligible_check=lambda l: True)
    conn.commit()
    fsp = conn.execute(
        "SELECT id FROM final_send_plan WHERE lead_id=? AND outreach_batch_date=? AND status='planned' ORDER BY id DESC LIMIT 1",
        (lead_id, batch_date)).fetchone()
    fsp_id = fsp["id"]
    tz = lead.get("recipient_timezone") or ""
    bucket = 'PT' if 'Los_Angeles' in tz else 'MT' if 'Denver' in tz else 'CT' if 'Chicago' in tz else 'ET' if 'New_York' in tz else '?'
    prepared.append({"lead_id": lead_id, "store_name": lead["store_name"], "email": lead["email"],
                     "fsp_id": fsp_id, "bucket": bucket, "subject": lead.get("email_subject")})
    print("PREPARED id=%d %s | %s | fsp=%d | %s" % (lead_id, lead["store_name"], lead["email"], fsp_id, bucket))

with open("tonight_pending_20260818.json", "w") as f:
    json.dump({"batch_date": batch_date, "prepared": prepared,
               "windows_shanghai": {"ET": "22:00", "CT": "23:00"}}, f, indent=2, default=str)
print("\nTOTAL PREPARED =", len(prepared))
from collections import Counter
print("BUCKETS =", dict(Counter(p["bucket"] for p in prepared)))
