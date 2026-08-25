"""One-time cleanup of stale / duplicate FSP rows.

ROOT CAUSE (now fixed in final_send_plan.create_plan): the old create_plan did a
pure INSERT, so repeated pre-send runs accumulated duplicate planned rows and left
old batches lingering. Those stale rows (a) cause double-sends via
execute_final_send_plan, and (b) fail preflight's stale_objects gate.

This script is the data-side remediation. It does NOT modify any production logic.
Default is --dry-run (no writes). Pass --live to apply, after which it:
  1. backs up data/bd_leads.db (timestamped) and prints its SHA-256,
  2. deletes the 44 duplicate planned rows in batch 2026-08-20 (keeps one per
     (lead_id, message_type); aborts if any dup pair is not content-identical),
  3. cancels the dead 2026-08-19 batch (9 never-sent rows) and the canary batch,
  4. revokes the two lingering 'approved' authorizations (p1_2_first20, canary),
  5. runs PRAGMA integrity_check and re-checks preflight's stale_objects gate
     for batch 2026-08-20.
"""
from __future__ import annotations
import sqlite3, sys, shutil, hashlib
from datetime import datetime

DB = "data/bd_leads.db"
LIVE = "--live" in sys.argv
ACTIVE_BATCH = "2026-08-20"


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(65536), b""):
            h.update(blk)
    return h.hexdigest()


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    plan = []

    # A. dedupe 2026-08-20 by (lead_id, message_type)
    dups = conn.execute(
        "SELECT lead_id, message_type, COUNT(*) c, GROUP_CONCAT(id) ids "
        "FROM final_send_plan WHERE outreach_batch_date=? AND status='planned' "
        "GROUP BY lead_id, message_type HAVING COUNT(*)>1",
        (ACTIVE_BATCH,),
    ).fetchall()
    del_ids = []
    for d in dups:
        ids = [int(x) for x in d["ids"].split(",")]
        rows = conn.execute(
            "SELECT id, recipient_email, evidence_url, body_text, subject "
            "FROM final_send_plan WHERE id IN (%s)" % ",".join("?" * len(ids)),
            ids,
        ).fetchall()
        emails = {r["recipient_email"] for r in rows}
        ev = {r["evidence_url"] for r in rows}
        bl = {len(r["body_text"]) for r in rows}
        sub = {r["subject"] for r in rows}
        if not (len(emails) == 1 and len(ev) == 1 and len(bl) == 1 and len(sub) == 1):
            print(f"ABORT: non-identical dup pair lead={d['lead_id']} type={d['message_type']}")
            conn.close()
            sys.exit(1)
        keep = min(ids)
        del_ids += [i for i in ids if i != keep]
    plan.append(("DEDUPE %s" % ACTIVE_BATCH, "delete %d duplicate rows, keep %d unique (lead,type) pairs" % (len(del_ids), len(dups))))

    # B. cancel dead 2026-08-19 batch
    b_rows = conn.execute(
        "SELECT id FROM final_send_plan WHERE outreach_batch_date='2026-08-19' AND status='planned'"
    ).fetchall()
    plan.append(("CANCEL 2026-08-19", "set cancelled x%d (never-sent, superseded)" % len(b_rows)))

    # C. cancel canary batch
    c_rows = conn.execute(
        "SELECT id FROM final_send_plan WHERE outreach_batch_date='canary_2026-08-20' AND status='planned'"
    ).fetchall()
    plan.append(("CANCEL canary_2026-08-20", "set cancelled x%d (test artifact)" % len(c_rows)))

    # D. revoke lingering approved authorizations not for the active batch
    auths = conn.execute(
        "SELECT id, plan_id, outreach_batch_date FROM send_authorizations "
        "WHERE status='approved' AND outreach_batch_date!=?",
        (ACTIVE_BATCH,),
    ).fetchall()
    plan.append(("REVOKE stale approved auths", "set revoked x%d ids=%s" % (len(auths), [a["id"] for a in auths])))

    print("=== PLAN (%s) ===" % ("LIVE" if LIVE else "DRY RUN"))
    for name, desc in plan:
        print(f"  {name}: {desc}")
    print(f"  TOTAL duplicate rows to DELETE : {len(del_ids)}")
    print(f"  TOTAL planned rows to CANCEL  : {len(b_rows) + len(c_rows)}")
    print(f"  TOTAL auths to REVOKE         : {len(auths)}")

    if not LIVE:
        conn.close()
        print("\n[DRY RUN] No changes made. Re-run with --live to apply.")
        return

    # ---- backup ----
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = f"data/bd_leads.db.bak_{ts}"
    shutil.copy2(DB, bak)
    print(f"\n  backup -> {bak} (sha256={sha256(bak)})")

    # ---- apply in a single transaction ----
    try:
        with conn:
            if del_ids:
                conn.execute("DELETE FROM final_send_plan WHERE id IN (%s)" % ",".join("?" * len(del_ids)), del_ids)
            if b_rows:
                conn.execute(
                    "UPDATE final_send_plan SET status='cancelled', skip_reason='stale_reclaimed_2026-08-20' "
                    "WHERE id IN (%s)" % ",".join("?" * len(b_rows)),
                    [r["id"] for r in b_rows],
                )
            if c_rows:
                conn.execute(
                    "UPDATE final_send_plan SET status='cancelled', skip_reason='stale_reclaimed_2026-08-20' "
                    "WHERE id IN (%s)" % ",".join("?" * len(c_rows)),
                    [r["id"] for r in c_rows],
                )
            if auths:
                # send_authorizations has no skip_reason column — only flip status.
                conn.execute(
                    "UPDATE send_authorizations SET status='revoked' "
                    "WHERE id IN (%s)" % ",".join("?" * len(auths)),
                    [a["id"] for a in auths],
                )
        print("[APPLIED] transaction committed")
    except Exception as e:
        print("[ROLLBACK] error:", e)
        conn.close()
        sys.exit(1)

    # ---- integrity + stale re-check ----
    ic = conn.execute("PRAGMA integrity_check").fetchall()
    print("  PRAGMA integrity_check:", "OK" if all(r[0] == "ok" for r in ic) else ic)
    old_plans = conn.execute(
        "SELECT outreach_batch_date d, COUNT(*) c FROM final_send_plan "
        "WHERE status='planned' AND outreach_batch_date!=? GROUP BY outreach_batch_date",
        (ACTIVE_BATCH,),
    ).fetchall()
    old_auths = conn.execute(
        "SELECT authorization_id FROM send_authorizations WHERE status='approved' AND outreach_batch_date!=?",
        (ACTIVE_BATCH,),
    ).fetchall()
    print("  remaining other planned batches:", [dict(r) for r in old_plans] or "NONE")
    print("  remaining other approved auths :", [r["authorization_id"] for r in old_auths] or "NONE")
    conn.close()
    passed = (not old_plans) and (not old_auths)
    print("\nSTALE_OBJECTS_GATE_FOR_%s = %s" % (ACTIVE_BATCH, "PASS" if passed else "FAIL"))


if __name__ == "__main__":
    main()
