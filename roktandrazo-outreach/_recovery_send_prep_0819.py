"""ONE-TIME SUPERVISED RECOVERY SEND — prepare 10th FSP + dry-run + live send.
Ian 已授权 ONE_TIME_SEND_WINDOW_OVERRIDE=true，仅豁免 recipient local 10:00 窗口。
其余安全门全部保留：V2/MX/evidence/suppression/bounce/sent/dup-org/timezone/FSP/Authorization/Preflight/V5/send_one P0。
"""
import os, sys, sqlite3, json, importlib.util
BASE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, BASE)

def _load_env(p):
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass

_load_env(os.path.join(BASE, ".env"))

import bd_template, final_send_plan
from env_loader import is_configured

DB = os.path.join(BASE, "data", "bd_leads.db")
SPEC = importlib.util.spec_from_file_location("cev2", os.path.join(BASE, "campaign_eligible_v2.py"))
cev2 = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(cev2)

conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
BATCH_DATE = "2026-08-18"
TENTH_LEAD_ID = 1069   # Blue Bridge Games — store-domain email, ET, official_page_visible

assert is_configured(), "SMTP not configured (env_loader.is_configured False)"

# ---------- 0) existing planned FSPs ----------
planned = conn.execute(
    "SELECT id, lead_id, recipient_email, status FROM final_send_plan WHERE status='planned' ORDER BY id"
).fetchall()
print(f"=== EXISTING PLANNED FSP: {len(planned)} ===")
for p in planned:
    print(f"  FSP{p['id']} lead={p['lead_id']} {p['recipient_email']}")

# ---------- 1) verify 9 planned leads still V2 PASS (fresh gate) ----------
existing_ids = [p["lead_id"] for p in planned]
res = cev2.scan_v2_inventory(existing_ids, conn=conn)
print("\n=== RE-VERIFY 9 PLANNED LEADS (canonical V2, live) ===")
ok9 = True
for lead_id, r in zip(existing_ids, res):
    st = "PASS" if r.get("eligible") else "FAIL:" + str(r.get("reasons"))
    if not r.get("eligible"):
        ok9 = False
    print(f"  lead={lead_id:<5} V2={st}")
if not ok9:
    print("\nABORT: some planned leads failed V2 re-verification")
    sys.exit(2)

# ---------- 2) prepare 10th FSP (only if lead 1069 not already planned) ----------
in_plan = any(p["lead_id"] == TENTH_LEAD_ID for p in planned)
print(f"\n=== 10TH LEAD {TENTH_LEAD_ID} already planned? {in_plan} ===")
if not in_plan:
    row = conn.execute("SELECT * FROM leads WHERE id=?", (TENTH_LEAD_ID,)).fetchone()
    assert row, f"lead {TENTH_LEAD_ID} not found"
    lead = dict(row)
    res10 = cev2.scan_v2_inventory([TENTH_LEAD_ID], conn=conn)
    v2 = res10[0]
    assert v2.get("eligible"), f"lead {TENTH_LEAD_ID} V2 FAIL: {v2.get('reasons')}"
    print(f"  lead {TENTH_LEAD_ID} V2 PASS: {lead['store_name']} | {lead['email']} | {lead['recipient_timezone']}")
    bd_template.apply_email_to_lead(lead)
    plan_id = final_send_plan.create_plan(conn, [lead], BATCH_DATE, "new_outreach",
                                          eligible_check=lambda l: True)
    conn.commit()
    fsp = conn.execute(
        "SELECT id FROM final_send_plan WHERE lead_id=? AND outreach_batch_date=? AND status='planned' ORDER BY id DESC LIMIT 1",
        (TENTH_LEAD_ID, BATCH_DATE)).fetchone()
    print(f"  CREATED FSP id={fsp['id']} for lead {TENTH_LEAD_ID} (plan_id={plan_id})")

# ---------- 3) final planned list ----------
planned2 = conn.execute(
    "SELECT id, lead_id, recipient_email, template_id FROM final_send_plan WHERE status='planned' ORDER BY id"
).fetchall()
print(f"\n=== FINAL PLANNED ({len(planned2)}) ===")
for p in planned2:
    print(f"  FSP{p['id']} lead={p['lead_id']} {p['recipient_email']} tmpl={p['template_id']}")
conn.close()
print("\nPREP_DONE planned_count=", len(planned2))
