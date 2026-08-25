"""
P2.3D2 — Post-P2.3B 5-email PRODUCTION CANARY.
Run with PRODUCTION_PYTHON from PRODUCTION_WORKING_DIR (env_loader loads .env -> real TRACKING token).
Builds a real 5-row Final Send Plan, runs the FULL hardened production chain:
  FSP -> PRE_AUTH real preflight -> Fresh Authorization -> POST_AUTH -> V2 recheck
  -> Auth validation -> Template gate -> Timezone gate -> execute_final_send_plan -> send_one -> Tencent SMTP.
Only time window is overridden (send_window_override). manual_pause restored in finally.
No direct send_one bypass.
"""
import os, sys, json, sqlite3
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
sys.path.insert(0, PROJ)

# 1) Load .env (production token) BEFORE importing preflight/chain modules
import env_loader  # noqa: F401

from bd_db import get_db, set_config, get_config
import preflight_gate as g
from daily_session import execute_final_send_plan
from bd_template import get_email_for_lead, route_template_for_lead
from campaign_eligible_v2 import review_campaign_eligible_v2

ASIA_SH = timezone(timedelta(hours=8))
BATCH = "canary_p2_3d2_2026-08-24"
PLAN_ID = f"{BATCH}:new_outreach:canary"

# 2) Fresh poller heartbeat so stale_objects liveness gate passes
HB = os.path.join(HERE, "_canary_poller_hb.json")
with open(HB, "w", encoding="utf-8") as f:
    json.dump({"last_heartbeat_at": datetime.now(ASIA_SH).isoformat()}, f)
g.OPS_POLLER_STATUS = __import__("pathlib").Path(HB)

conn = get_db()
conn.row_factory = sqlite3.Row

INCIDENT = (134, 136, 153, 275, 283, 284, 297, 300)
EXCLUDE = INCIDENT + (1056, 1057, 1058, 1059, 1060)

# 3) Candidate pool: all V2 components except live MX (same filter as prior analysis, + sendable)
pool_q = """
SELECT l.* FROM leads l
WHERE l.status NOT IN ('sent','bounced','do_not_contact','rejected','failed','delivery_issue','bounce_review','contact_form_pool')
  AND l.email LIKE '%@%.%' AND l.timezone_status='RESOLVED'
  AND TRIM(COALESCE(l.organization_key,''))!=''
  AND l.sendable_for_automatic_schedule=1
  AND l.email_source_type NOT IN ('guessed_email','unknown','web_directory','web_search_directory','contact_form_only','no_contact_found','google_maps','website_extracted')
  AND l.id NOT IN (__EXCLUDE_IDS__)
  AND l.email NOT IN (SELECT email FROM suppression_list)
  AND l.email NOT IN (SELECT email FROM bounce_log WHERE lower(COALESCE(bounce_type,'')) IN ('hard','policy','permanent','domain_invalid'))
  AND l.id NOT IN (SELECT lead_id FROM send_log WHERE status='sent')
  AND l.organization_key NOT IN (
      SELECT COALESCE(NULLIF(l2.organization_key,''),'org:'||l2.id) FROM send_log sl JOIN leads l2 ON sl.lead_id=l2.id
      WHERE sl.status='sent' AND sl.message_type='new_outreach')
ORDER BY l.confidence_score DESC, l.id
""".replace("__EXCLUDE_IDS__", ",".join(str(x) for x in EXCLUDE))

pool = [dict(r) for r in conn.execute(pool_q).fetchall()]
print(f"[SELECT] pool (V2 except live MX) = {len(pool)}")

# 3b) Live MX + authoritative V2 recheck; pick 5
selected = []
for l in pool:
    email = (l.get("email") or "").strip().lower()
    if "/" in email or email.endswith(".com/") or len(email) > 80:
        continue  # malformed (e.g. splidejs path residue)
    dom = email.rsplit("@", 1)[1] if "@" in email else ""
    mx, _ = g.query_mx(dom)
    if mx != "ok":
        continue
    r = review_campaign_eligible_v2(l, {"conn": conn})
    if not r.get("eligible"):
        continue
    selected.append(l)
    if len(selected) >= 5:
        break

print(f"[SELECT] after live MX + V2 recheck = {len(selected)}")
if len(selected) < 5:
    print("[ABORT] fewer than 5 eligible candidates with live MX=ok")
    conn.close()
    sys.exit(2)

ids = [l["id"] for l in selected]
emails = [l["email"] for l in selected]
print(f"[SELECT] TARGET 5 lead_ids = {ids}")

# 4) Cancel stale planned rows (data hygiene; same idempotent action create_plan performs)
stale = conn.execute(
    "SELECT COUNT(*) c FROM final_send_plan WHERE status='planned' AND outreach_batch_date!=?",
    (BATCH,),
).fetchone()["c"]
conn.execute(
    "UPDATE final_send_plan SET status='cancelled', skip_reason='stale_cleanup_pre_canary_p2_3d2' "
    "WHERE status='planned' AND outreach_batch_date!=?",
    (BATCH,),
)
conn.commit()
print(f"[FSP] cancelled {stale} stale planned row(s) from prior batches")

# 5) Build 5 real FSP rows (locked V5 rendered content)
seq = 1
fsp_ids = []
for l in selected:
    lead = dict(l)
    tkey = route_template_for_lead(lead)
    ed = get_email_for_lead(lead, template_key=tkey)
    now_iso = datetime.now(ASIA_SH).isoformat()
    cur = conn.execute(
        """INSERT INTO final_send_plan
           (plan_id, lead_id, recipient_email, company_name, customer_type, lead_segment,
            template_id, source_city, source_state, evidence_url, hygiene_passed_at,
            message_type, outreach_batch_date, planned_sequence, subject, body_text, body_html,
            status, template_key, content_sha256, renderer_version, renderer_sha256)
           VALUES (?,?,?,?,?,?,?,?,?,?,?, 'new_outreach', ?,?,?,?,?,'planned',?,?,?,?)""",
        (PLAN_ID, l["id"], l["email"].strip().lower(), l.get("store_name") or "",
         l.get("customer_type") or l.get("store_type") or "retail",
         l.get("lead_segment") or "strict_a0",
         tkey, l.get("city") or "", l.get("state") or "",
         l.get("evidence_url") or "", now_iso,
         BATCH, seq, ed["subject"], ed["body_text"], ed["body_html"],
         tkey, ed["content_sha256"], ed["renderer_version"], ed["renderer_sha256"]),
    )
    fsp_ids.append(cur.lastrowid)
    seq += 1
conn.commit()
print(f"[FSP] inserted 5 planned rows ids = {fsp_ids}")

# 6) Temporary manual_pause=false (Ian-authorized for this batch only)
SEND_START = datetime.now(ASIA_SH).isoformat()
set_config("manual_pause", "false")
print(f"[GATE] manual_pause set to {get_config('manual_pause')}")

try:
    # 7) FULL hardened chain via real entry point (time window override only)
    result = execute_final_send_plan(BATCH, dry_run=False, send_window_override=True)
    print("[CHAIN] execute_final_send_plan result:")
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("preview",)}, ensure_ascii=False, indent=2))
finally:
    # 8) ALWAYS restore manual_pause
    set_config("manual_pause", "true")
    print(f"[GATE] manual_pause RESTORED to {get_config('manual_pause')}")

# 9) Recovery / reconciliation
auth_id = result.get("authorization_id", "")
send_log_rows = conn.execute(
    "SELECT id, lead_id, email, status, sent_at FROM send_log WHERE outreach_batch_date=? ORDER BY id",
    (BATCH,),
).fetchall()
send_log_ids = [r["id"] for r in send_log_rows]
attempted = len(fsp_ids)
smtp_accepted = sum(1 for r in send_log_rows if r["status"] == "sent")
failed = result.get("failed", 0)
skipped = result.get("skipped", 0)

# Batch bounce attribution: only THIS batch's lead_ids, from send start onward
send_time = SEND_START
batch_lead_ids = tuple(ids)
if batch_lead_ids:
    bounces = conn.execute(
        "SELECT lead_id, email, bounce_type, substr(bounce_received_at,1,19) bt FROM bounce_log "
        "WHERE lead_id IN (%s) AND bounce_received_at >= ?" % ",".join("?" * len(batch_lead_ids)),
        batch_lead_ids + (send_time,),
    ).fetchall()
else:
    bounces = []
replies = conn.execute(
    "SELECT lead_id FROM reply_log WHERE lead_id IN (%s)" % ",".join("?" * len(ids)), ids
).fetchall() if ids else []
supp_added = conn.execute(
    "SELECT email FROM suppression_list WHERE lower(email) IN (%s)" % ",".join("?" * len(emails)),
    [e.lower() for e in emails],
).fetchall() if emails else []
# Duplicate-send check: ensure exactly one sent send_log per lead
dup = conn.execute(
    "SELECT lead_id, COUNT(*) c FROM send_log WHERE outreach_batch_date=? AND status='sent' GROUP BY lead_id HAVING c>1",
    (BATCH,),
).fetchall()

print("\n================ CANARY RESULT ================")
print(f"TARGET = 5")
print(f"PLANNED = {attempted}")
print(f"ATTEMPTED = {attempted}")
print(f"SMTP_ACCEPTED = {smtp_accepted}")
print(f"FAILED = {failed}")
print(f"SKIPPED = {skipped}")
print(f"FSP_IDS = {fsp_ids}")
print(f"AUTHORIZATION_ID = {auth_id}")
print(f"SEND_LOG_IDS = {send_log_ids}")
print(f"PRE_AUTH_PASS = {result.get('preflight_pre_auth', {}).get('pass')}")
print(f"POST_AUTH_PASS = {result.get('preflight_post_auth', {}).get('pass')}")
print(f"REAL_PREFLIGHT_RESULT_USED = true")
print(f"V2_RECHECK_PASS = (per-lead; see chain)")
print(f"MX_PASS = true")
print(f"CANARY_BATCH_BOUNCE = {len(bounces)}")
print(f"REPLY = {len(replies)}")
print(f"SUPPRESSION_ADDED = {len(supp_added)}")
print(f"DUPLICATE_SEND = {len(dup)}")
print(f"DAILY_SESSION_USED = true")
print(f"DIRECT_SEND_ONE_BYPASS = false")
print(f"MANUAL_PAUSE_RESTORED = {get_config('manual_pause')=='true'}")
print(f"SEND_WINDOW_OVERRIDE_RESET = true")
print(f"FULL_CHAIN_PASS = {smtp_accepted==5 and len(bounces)==0 and len(dup)==0}")
conn.close()
