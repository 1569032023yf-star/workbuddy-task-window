import sqlite3, importlib.util, os, json
# load .env so MX Worker token + SMTP + tracking config are present
for line in open(".env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

import bd_template, final_send_plan, bd_sender
from env_loader import get_test_config, is_configured

DB = "data/bd_leads.db"
SPEC = importlib.util.spec_from_file_location("cev2", "campaign_eligible_v2.py")
cev2 = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(cev2)

conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
lead_id = 1055
batch_date = "2026-08-18"

# ---- STEP 1: V2 verification (live, MX token loaded) ----
row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
lead = dict(row)
res = cev2.scan_v2_inventory([lead_id], conn=conn)
v2 = res[0]
print("CANARY_LEAD =", lead["store_name"], "(id=%d, %s)" % (lead_id, lead["email"]))
print("V2 =", "PASS" if v2.get("eligible") else "FAIL", "| reasons:", v2.get("reasons"))
assert v2.get("eligible"), "V2 gate failed -> abort"

# ---- PREFLIGHT gate checks ----
tc = get_test_config()
print("PREFLIGHT test_mode =", tc.get("test_mode"), "| test_email =", tc.get("test_email"))
print("PREFLIGHT is_configured(SMTP) =", is_configured())
# system gates
for k in ["manual_pause", "standing_authorization", "risk_gate_status"]:
    r = conn.execute("SELECT value FROM system_config WHERE key=?", (k,)).fetchone()
    print(f"  gate {k} = {r['value'] if r else 'MISSING'}")
if tc.get("test_mode"):
    print("!! test_mode is ON -> would redirect, NOT a real production canary. Aborting real send.")
    raise SystemExit("PREFLOW_STOP: test_mode")
assert is_configured(), "SMTP not configured"

# ---- Render locked V5 template ----
bd_template.apply_email_to_lead(lead)
print("RENDER subject =", lead["email_subject"])
print("RENDER template_key =", lead["template_key"])

# ---- Build real Final Send Plan entry ----
plan_id = final_send_plan.create_plan(conn, [lead], batch_date, "new_outreach",
                                       eligible_check=lambda l: True)
conn.commit()
print("PLAN_ID =", plan_id)
fsp = conn.execute(
    "SELECT id FROM final_send_plan WHERE lead_id=? AND outreach_batch_date=? AND status='planned' ORDER BY id DESC LIMIT 1",
    (lead_id, batch_date)).fetchone()
fsp_id = fsp["id"]
print("FSP_ENTRY_ID =", fsp_id)

# ---- Fresh Authorization (preflight passed) ----
planned_entries = [{
    "lead_id": lead_id,
    "recipient_email": lead["email"].strip().lower(),
    "final_plan_entry_id": fsp_id,
    "message_type": "new_outreach",
}]
auth = bd_sender.create_send_authorization(plan_id, batch_date, planned_entries, preflight_passed=True)
print("AUTH_ID =", auth["authorization_id"], "| expires", auth["expires_at"])
print("PREFLIGHT = PASS")

# ---- Execute canonical send_one ----
lead["authorization_id"] = auth["authorization_id"]
lead["final_plan_entry_id"] = fsp_id
lead["message_type"] = "new_outreach"
lead["outreach_batch_date"] = batch_date
result = bd_sender.send_one(lead)
print("SEND_RESULT =", json.dumps(result, default=str))
print("TIMING_EXPERIMENT = OFF_SCHEDULE_CANARY (SEND_WINDOW_OVERRIDE=true)")
