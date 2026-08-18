"""BD Production Final Preflight — 2026-08-13 (read-only gate, NO SMTP)."""
import sqlite3, json, datetime, urllib.request, os, sys
from zoneinfo import ZoneInfo

sh = ZoneInfo("Asia/Shanghai")
now = datetime.datetime.now(sh)
ts_cst = now.strftime("%Y-%m-%d %H:%M:%S CST")

DB = "data/bd_leads.db"
OUT = "output/preflight_result.json"
BATCH = "new_outreach_20260813_et1000"
BATCH_DATE = "20260813"

conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row


def q1(sql, p=()):
    r = conn.execute(sql, p).fetchone()
    return r["c"] if r else 0


def q1_val(key):
    r = conn.execute("SELECT value FROM system_config WHERE key=?", (key,)).fetchone()
    return r["value"] if r else None


# Step 1: batch id
step1 = {"pass": True, "value": BATCH}

# Step 2: plan entries
plan_count = q1("SELECT COUNT(*) c FROM final_send_plan WHERE outreach_batch_date=?", (BATCH,))
step2 = {"pass": plan_count > 0, "count": plan_count}

# Step 3: auth exists + approved
auth_row = conn.execute(
    "SELECT * FROM send_authorizations WHERE outreach_batch_date=? ORDER BY id DESC LIMIT 1",
    (BATCH,),
).fetchone()
if auth_row:
    step3 = {"pass": auth_row["status"] == "approved", "status": auth_row["status"],
             "authorization_id": auth_row["authorization_id"]}
else:
    step3 = {"pass": False, "reason": "No send authorization found"}

# Step 4: auth entries vs plan
auth_entry_count = 0
if auth_row:
    auth_entry_count = q1(
        "SELECT COUNT(*) c FROM send_authorization_entries WHERE authorization_id=?",
        (auth_row["authorization_id"],),
    )
step4 = {
    "pass": (plan_count > 0 and auth_row is not None and auth_entry_count == plan_count),
    "plan_count": plan_count,
    "auth_entry_count": auth_entry_count,
    "match": (auth_entry_count == plan_count),
    "note": "Both zero = no valid plan" if (plan_count == 0 and auth_entry_count == 0) else "",
}

# Step 5/6: duplicates (only meaningful if plan exists)
if plan_count > 0:
    rows = conn.execute(
        "SELECT lead_id, recipient_email FROM final_send_plan WHERE outreach_batch_date=?",
        (BATCH,),
    ).fetchall()
    emails = [str(r["recipient_email"] or "").strip().lower() for r in rows]
    org_keys = []
    for r in rows:
        o = conn.execute(
            "SELECT COALESCE(NULLIF(organization_key,''),'org:'||id) k FROM leads WHERE id=?",
            (r["lead_id"],),
        ).fetchone()
        org_keys.append(o["k"] if o else f"lead:{r['lead_id']}")
    org_dup = len(org_keys) - len(set(org_keys))
    email_dup = len(emails) - len(set(emails))
    step5 = {"pass": org_dup == 0, "duplicate_count": org_dup}
    step6 = {"pass": email_dup == 0, "duplicate_count": email_dup}
else:
    step5 = {"pass": None, "reason": "no_plan", "duplicate_count": 0}
    step6 = {"pass": None, "reason": "no_plan", "duplicate_count": 0}

# Step 7: template SHA
sys.path.insert(0, ".")
import bd_template as t
retail_actual = t._TEMPLATE_SHA256.get("retail_distributor_v5_locked")
custom_actual = t._TEMPLATE_SHA256.get("custom_printing_production_v5_locked")
step7 = {
    "pass": retail_actual == "ccb51505" and custom_actual == "5893dbc9",
    "retail": {"expected": "ccb51505", "actual": retail_actual, "match": retail_actual == "ccb51505"},
    "custom": {"expected": "5893dbc9", "actual": custom_actual, "match": custom_actual == "5893dbc9"},
}

# Step 8: Ops Center HTTP 200
ops_err = None
http_code = 0
try:
    r = urllib.request.urlopen("http://127.0.0.1:8765/", timeout=5)
    http_code = r.status
except Exception as e:
    ops_err = f"{type(e).__name__} {e}"
step8 = {"pass": http_code == 200, "http_code": http_code,
         "url": "http://127.0.0.1:8765/", "error": ops_err}

# Step 9: poller heartbeat (threshold 2 min per bd_ops_poller.py guard)
try:
    ps = json.load(open("output/bd_ops_poller_status.json", encoding="utf-8"))
except Exception:
    ps = {}
hb = ps.get("last_heartbeat_at")
hb_dt = datetime.datetime.fromisoformat(hb) if hb else None
hb_age = (now - hb_dt).total_seconds() / 60 if hb_dt else None
step9 = {
    "pass": hb_dt is not None and hb_age is not None and hb_age < 2,
    "poller_last_heartbeat": hb,
    "poller_age_minutes": round(hb_age, 1) if hb_age is not None else None,
    "poller_threshold_minutes": 2,
    "sync_0845_last_success_at": q1_val("sync_0845_last_success_at"),
}

# Step 10: old plans / auths
old_planned = conn.execute(
    "SELECT outreach_batch_date, COUNT(*) c FROM final_send_plan "
    "WHERE status='planned' AND outreach_batch_date!=? GROUP BY outreach_batch_date",
    (BATCH,),
).fetchall()
old_planned_total = sum(r["c"] for r in old_planned)
old_auths = conn.execute(
    "SELECT authorization_id, outreach_batch_date, status, expires_at FROM send_authorizations "
    "WHERE status IN ('approved','active','pending') AND outreach_batch_date!=?",
    (BATCH,),
).fetchall()
step10 = {
    "pass": (old_planned_total == 0 and len(old_auths) == 0),
    "old_active_plans": old_planned_total,
    "active_old_auths": len(old_auths),
    "planned_batches": [[r["outreach_batch_date"], r["c"]] for r in old_planned],
    "active_auth_rows": [dict(r) for r in old_auths],
}

# Frozen snapshot
frozen_exists = os.path.exists(f"output/frozen_{BATCH}.json") or os.path.exists(f"data/frozen_{BATCH}.json")

# A0 pool
a0_pool = q1("SELECT COUNT(*) c FROM leads WHERE auto_sendable=1 "
             "AND email_verified_on_official_site=1 AND email IS NOT NULL AND email!=''")

# SMTP
smtp_enabled = q1_val("SMTP_enabled")

conn.close()

gate_summary = {
    "step1_batch_id": "PASS" if step1["pass"] else "FAIL",
    "step2_plan_entries": "PASS" if step2["pass"] else "FAIL",
    "step3_auth_exists": "PASS" if step3["pass"] else "FAIL",
    "step4_auth_plan_match": "PASS" if step4["pass"] else "FAIL",
    "step5_org_duplicates": "N/A" if step5["pass"] is None else ("PASS" if step5["pass"] else "FAIL"),
    "step6_email_duplicates": "N/A" if step6["pass"] is None else ("PASS" if step6["pass"] else "FAIL"),
    "step7_template_sha": "PASS" if step7["pass"] else "FAIL",
    "step8_ops_center": "PASS" if step8["pass"] else "FAIL",
    "step9_poller_heartbeat": "PASS" if step9["pass"] else "FAIL",
    "step10_old_plans_auths": "PASS" if step10["pass"] else "FAIL",
}
blockers = [k for k, v in gate_summary.items() if v == "FAIL"]
overall = "PASSED" if not blockers else "BLOCKED"

result = {
    "preflight_ts_cst": ts_cst,
    "batch_id": BATCH,
    "batch_date": BATCH_DATE,
    "gates": {
        "step1_batch_id": step1, "step2_plan_entries": step2, "step3_auth_exists": step3,
        "step4_auth_plan_match": step4, "step5_org_duplicates": step5,
        "step6_email_duplicates": step6, "step7_template_sha": step7, "step8_ops_center": step8,
        "step9_poller_heartbeat": step9, "step10_old_plans_auths": step10,
    },
    "frozen_snapshot_exists": frozen_exists,
    "a0_pool_count": a0_pool,
    "gate_summary": gate_summary,
    "blockers": blockers,
    "overall_verdict": overall,
    "smtp_enabled": smtp_enabled,
}

os.makedirs("output", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("WROTE", OUT)
print(json.dumps({"gate_summary": gate_summary, "blockers": blockers,
                  "overall_verdict": overall, "smtp_enabled": smtp_enabled,
                  "a0_pool_count": a0_pool, "frozen_snapshot_exists": frozen_exists},
                 indent=2, ensure_ascii=False))
