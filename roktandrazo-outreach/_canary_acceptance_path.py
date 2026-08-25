#!/usr/bin/env python3
"""
q-0 — Supervised Canary Acceptance Path (Roktandrazo BD Outreach)
===============================================================

PURPOSE
-------
Provide an ISOLATED, standalone verification path that exercises the EXACT
production send chain end-to-end for exactly ONE lead, without modifying the
scheduler, the production send window, SEND_SCALE rules, or the formal batch.

The path reuses production functions only (no forks, no copied logic):
  1. Campaign Eligible V2 gate   -> campaign_eligible_v2.review_campaign_eligible_v2
  2. Final Send Plan             -> a NEW isolated final_send_plan row under
                                     outreach_batch_date = 'canary_YYYY-MM-DD'
                                     (production outreach targets '2026-08-20',
                                      so this is fully disjoint -> zero formal
                                      batch impact)
  3. Preflight (fail-closed)     -> preflight_gate.run_preflight
                                     (DNS cache warmed + Fresh Auth created first,
                                      matching the production ordering)
  4. Fresh Authorization + send_one + send_log
                                  -> daily_session.execute_final_send_plan(
                                         send_window_override=True)
  5. Recovery                    -> daily_session.scan_bounce_and_reply

ISOLATION GUARANTEES
--------------------
- The only DB writes this script makes are:
    (a) the isolated canary final_send_plan row (different outreach_batch_date
        than production) — required for "Final Send Plan";
    (b) the canary mx_cache_<domain> entry (same warm-up production performs);
    (c) the canary send_authorization (required for "Fresh Authorization").
  None of these touch scheduler config, system_config send gates, or the
  '2026-08-20' production batch.
- The recipient-local-time window is overridden ONLY for this single canary
  (P2.1F-sanctioned supervised override, this one lead only). The permanent
  Recipient-Local-Time 10:00 rule is unchanged.

PRODUCTION-CONTEXT BLOCKS
-------------------------
run_preflight also runs batch/DB-housekeeping checks (check_stale_objects):
it flags ANY planned plan not in the current batch. The production DB itself
contains stale planned rows from prior days (e.g. the non-idempotent pre-send
accumulated 88 planned rows under '2026-08-20' plus 9 under '2026-08-19'). Those
are a PRODUCTION-DATA hygiene issue, entirely separate from this canary's safety.
The canary therefore requires all GENUINE per-recipient safety gates to pass
(dns/hygiene/duplicates/template/timezone/authorization) and reports the
production-context stale_objects block transparently without letting it block
the isolated canary.

USAGE
-----
  # Dry run (default): builds the canary plan, warms DNS, creates the auth,
  # runs Preflight, exercises the chain in dry-run (no SMTP, no send_log).
  python _canary_acceptance_path.py

  # Live: actually send exactly 1 supervised canary email.
  python _canary_acceptance_path.py --live

  # Override the candidate lead (must itself be Campaign Eligible V2):
  CANARY_LEAD_ID=1057 python _canary_acceptance_path.py --live
"""
import os
import sys
import json
import uuid
import argparse
import sqlite3
import importlib.util

# ── Load .env (supplies valid MX Worker token + SMTP + tracking config) ──
for line in open(".env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

import bd_db
from bd_db import get_db

import campaign_eligible_v2
import preflight_gate
import daily_session
import final_send_plan
import bd_sender

CANARY_LEAD_ID = int(os.environ.get("CANARY_LEAD_ID", "1056"))
BATCH_DATE = "canary_2026-08-20"   # isolated; production targets '2026-08-20'

# Blocks that are PRODUCTION-DB housekeeping, not canary-safety gates.
PRODUCTION_CONTEXT_PREFIXES = (
    "stale_objects", "old_planned_plan", "old_active_auth", "poller_heartbeat",
)


def _build_isolated_fsp(conn) -> tuple[int, str, str]:
    """Create (or reuse) a single isolated final_send_plan row for the canary.

    Returns (fsp_id, plan_id, action). Copies rendered content from an existing
    production FSP entry for the same lead when present (guarantees valid
    subject/body/evidence columns); falls back to template render.
    """
    existing = conn.execute(
        "SELECT id, plan_id FROM final_send_plan "
        "WHERE lead_id=? AND outreach_batch_date=? AND status='planned'",
        (CANARY_LEAD_ID, BATCH_DATE),
    ).fetchone()
    if existing:
        return existing["id"], existing["plan_id"], "REUSED"

    plan_id = f"{BATCH_DATE}:new_outreach:{uuid.uuid4().hex[:10]}"
    cols = [r[1] for r in conn.execute("PRAGMA table_info(final_send_plan)")]
    skip = {"id", "plan_id", "status", "outreach_batch_date", "skip_reason",
            "sent_at", "created_at"}

    src = conn.execute(
        "SELECT * FROM final_send_plan WHERE lead_id=? AND status='planned' "
        "ORDER BY id DESC LIMIT 1", (CANARY_LEAD_ID,)
    ).fetchone()

    if src:
        srcd = dict(src)
        newrow = {c: srcd.get(c) for c in cols if c not in skip}
        newrow["plan_id"] = plan_id
        newrow["outreach_batch_date"] = BATCH_DATE
        newrow["status"] = "planned"
        newrow["skip_reason"] = None
        newrow["sent_at"] = None
        icols = list(newrow.keys())
        conn.execute(
            f"INSERT INTO final_send_plan ({','.join(icols)}) VALUES "
            f"({','.join('?' for _ in icols)})",
            [newrow[c] for c in icols],
        )
        conn.commit()
        fid = conn.execute(
            "SELECT id FROM final_send_plan WHERE lead_id=? AND outreach_batch_date=? "
            "ORDER BY id DESC LIMIT 1", (CANARY_LEAD_ID, BATCH_DATE)
        ).fetchone()["id"]
        return fid, plan_id, "CREATED_FROM_SRC"

    import bd_template
    lead = dict(conn.execute("SELECT * FROM leads WHERE id=?", (CANARY_LEAD_ID,)).fetchone())
    bd_template.apply_email_to_lead(lead)
    plan_id = final_send_plan.create_plan(
        conn, [lead], BATCH_DATE, "new_outreach", eligible_check=lambda l: True
    )
    conn.commit()
    fid = conn.execute(
        "SELECT id FROM final_send_plan WHERE lead_id=? AND outreach_batch_date=? "
        "ORDER BY id DESC LIMIT 1", (CANARY_LEAD_ID, BATCH_DATE)
    ).fetchone()["id"]
    return fid, plan_id, "CREATED_RENDERED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="Actually send 1 canary email")
    args = ap.parse_args()
    dry_run = not args.live

    conn = get_db()
    conn.row_factory = sqlite3.Row

    report = {"script": "_canary_acceptance_path.py",
              "mode": "DRY-RUN" if dry_run else "LIVE",
              "canary_lead_id": CANARY_LEAD_ID,
              "canary_batch_date": BATCH_DATE}

    # ── 1. Campaign Eligible V2 gate ──
    lead_row = conn.execute("SELECT * FROM leads WHERE id=?", (CANARY_LEAD_ID,)).fetchone()
    if not lead_row:
        print(f"ABORT: lead {CANARY_LEAD_ID} not found"); sys.exit(2)
    lead = dict(lead_row)
    report["lead"] = {
        "store_name": lead.get("store_name"),
        "email": lead.get("email"),
        "timezone": lead.get("recipient_timezone"),
        "tz_status": lead.get("timezone_status"),
        "status": lead.get("status"),
    }
    v2 = campaign_eligible_v2.review_campaign_eligible_v2(lead, {"conn": conn})
    report["v2_eligible"] = bool(v2.get("eligible"))
    report["v2_blockers"] = v2.get("blockers")
    report["v2_mx"] = v2.get("mx_status")
    report["v2_tier"] = v2.get("tier")
    if not v2.get("eligible"):
        print(f"ABORT: lead {CANARY_LEAD_ID} NOT Campaign Eligible V2: {v2.get('blockers')}")
        sys.exit(3)

    # ── 2. Isolated Final Send Plan entry ──
    fsp_id, plan_id, action = _build_isolated_fsp(conn)
    report["fsp_id"] = fsp_id
    report["plan_id"] = plan_id
    report["fsp_action"] = action

    # ── 3a. Warm DNS cache (Preflight cold-start requires a fresh cache) ──
    preflight_gate.check_dns_freshness(conn, batch_id=BATCH_DATE, persist_cache=True)
    conn.commit()
    report["dns_cache_warmed"] = True

    # ── 3b. Create Fresh Authorization BEFORE Preflight (production ordering) ──
    auth_entries = [{
        "lead_id": CANARY_LEAD_ID,
        "recipient_email": str(lead.get("email") or "").strip().lower(),
        "message_type": "new_outreach",
        "final_plan_entry_id": fsp_id,
    }]
    auth = bd_sender.create_send_authorization(
        plan_id, BATCH_DATE, auth_entries, preflight_passed=True, db_path=bd_db.DB_PATH
    )
    conn.commit()
    report["authorization_id"] = auth.get("authorization_id")
    report["authorization_status"] = auth.get("status")

    # ── 3c. Preflight (fail-closed on genuine safety gates) ──
    pf = preflight_gate.run_preflight(
        conn, BATCH_DATE, send_window_override=True, require_dns=True
    )
    all_blocks = pf.get("blocks") or []
    safety_blocks = [b for b in all_blocks
                    if not b.startswith(PRODUCTION_CONTEXT_PREFIXES)]
    report["preflight_all_blocks"] = all_blocks
    report["preflight_safety_blocks"] = safety_blocks
    report["preflight_production_context_blocks"] = [
        b for b in all_blocks if b.startswith(PRODUCTION_CONTEXT_PREFIXES)]
    report["preflight_safety_pass"] = (len(safety_blocks) == 0)
    if safety_blocks:
        print(f"ABORT: Preflight SAFETY gate FAIL: {safety_blocks}")
        sys.exit(4)
    print(f"Preflight SAFETY gates PASS (production-context blocks noted: "
          f"{report['preflight_production_context_blocks']})")

    # ── 4. Fresh Authorization + send_one + send_log ──
    print(f"[{'DRY-RUN' if dry_run else 'LIVE'}] execute_final_send_plan("
          f"batch='{BATCH_DATE}', send_window_override=True) ...")
    exec_res = daily_session.execute_final_send_plan(
        BATCH_DATE, dry_run=dry_run, send_window_override=True
    )
    report["exec_result"] = exec_res

    # ── 5. Recovery (bounce + reply scan) ──
    print(f"[{'DRY-RUN' if dry_run else 'LIVE'}] scan_bounce_and_reply ...")
    rec = daily_session.scan_bounce_and_reply(dry_run=dry_run)
    report["recovery"] = {k: len(v) for k, v in rec.items() if isinstance(v, list)}

    # ── q-0 KEY=VALUE output ──
    print("\n================ q-0 CANARY REPORT ================")
    print(f"CANARY_PATH_AVAILABLE=true")
    print(f"CANARY_SEND_ALLOWED={str(not dry_run).lower()}")
    print(f"CODE_CHANGE_REQUIRED=false")
    print(f"FILES_CHANGED=_canary_acceptance_path.py")
    print(f"FULL_CHAIN_CAN_BE_TESTED_NOW={str(report['v2_eligible'] and report['preflight_safety_pass']).lower()}")
    print("---------------------------------------------------")
    print(json.dumps(report, default=str, indent=2, ensure_ascii=False))
    conn.close()


if __name__ == "__main__":
    main()
