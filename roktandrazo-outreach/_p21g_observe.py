"""P2.1G — First Real Automated Send OBSERVATION (read-only verifier).

Does NOT modify code, does NOT create FSP, does NOT trigger tasks.
Compares live DB state against the pre-run baseline (output/p21g_baseline.json)
and attributes activity to TONIGHT's scheduled run window only:
    PreSend  2026-08-20 22:30
    Outreach 2026-08-20 23:00  (inside 23:00-23:59:30 send window)
    PostSend 2026-08-21 00:10

Usage:
    _p21g_observe.py            # one-shot report
    _p21g_observe.py --watch    # loop until post-send observed or hard timeout
"""
from __future__ import annotations
import sqlite3, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data", "bd_leads.db")
BASELINE = os.path.join(HERE, "output", "p21g_baseline.json")
RESULT = os.path.join(HERE, "output", "p21g_observation_result.json")

WINDOW_START = "2026-08-20 22:00:00"
WINDOW_END = "2026-08-21 02:00:00"
ACTIVE_BATCH = "2026-08-20"

# send window gate (Asia/Shanghai) for reference
SEND_WIN_START = "23:00"
SEND_WIN_END = "23:59:30"


def load_baseline():
    if not os.path.exists(BASELINE):
        return None
    return json.load(open(BASELINE, encoding="utf-8"))


def q1(conn, sql, params=()):
    return conn.execute(sql, params).fetchone()[0]


def planned(conn, batch):
    return q1(conn, "SELECT COUNT(*) FROM final_send_plan WHERE outreach_batch_date=? AND status='planned'", (batch,))


def dup_pairs(conn, batch):
    return q1(conn,
        "SELECT COUNT(*) FROM (SELECT lead_id,message_type FROM final_send_plan "
        "WHERE outreach_batch_date=? AND status='planned' GROUP BY lead_id,message_type HAVING COUNT(*)>1)",
        (batch,))


def count_by_type(conn, batch, mtype):
    return q1(conn,
        "SELECT COUNT(*) FROM final_send_plan WHERE outreach_batch_date=? AND status='planned' AND message_type=?",
        (batch, mtype))


def job_runs_in_window(conn, stage):
    rows = conn.execute(
        "SELECT run_id, started_at, finished_at, status, target, actual, stop_reason, dry_run "
        "FROM job_runs WHERE stage=? AND started_at >= ? AND started_at < ? ORDER BY started_at",
        (stage, WINDOW_START, WINDOW_END)).fetchall()
    return [dict(r) for r in rows]


def link_col(conn, table):
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    for c in ("email", "recipient_email", "lead_id"):
        if c in cols:
            return c
    return cols[0] if cols else None


def observe(conn, baseline):
    out = {}
    # ---- 1. AUTOMATED_RUN: did tonight's scheduler fire? ----
    pre = job_runs_in_window(conn, "pre-send")
    out_runs = job_runs_in_window(conn, "outreach")
    post = job_runs_in_window(conn, "post-send")
    out["PRESEND_JOB"] = pre[0] if pre else None
    out["OUTREACH_JOB"] = out_runs[0] if out_runs else None
    out["POSTSEND_JOB"] = post[0] if post else None

    if not pre:
        out["AUTOMATED_RUN"] = "pending"          # tonight's run not yet executed
    elif pre and not out_runs:
        out["AUTOMATED_RUN"] = "pre_send_done_outreach_pending"
    elif out_runs and not post:
        out["AUTOMATED_RUN"] = "outreach_done_postsend_pending"
    else:
        out["AUTOMATED_RUN"] = "observed"

    # ---- 2. PRESEND_OK + FSP state (idempotency) ----
    p_now = planned(conn, ACTIVE_BATCH)
    d_now = dup_pairs(conn, ACTIVE_BATCH)
    fu_now = count_by_type(conn, ACTIVE_BATCH, "follow_up")
    no_now = count_by_type(conn, ACTIVE_BATCH, "new_outreach")
    out["PRESEND_OK"] = "true" if (pre and pre[0]["status"] == "completed") else "false"
    out["FSP_CREATED"] = p_now
    out["FSP_NEW_OUTREACH"] = no_now
    out["FSP_FOLLOW_UP"] = fu_now
    out["DUPLICATE_FSP"] = d_now
    # idempotency proof: tonight's pre-send must NOT have doubled the plan
    base_planned = (baseline or {}).get("batches", {}).get(ACTIVE_BATCH, {}).get("planned")
    out["IDEMPOTENT"] = "true" if (base_planned is None or p_now <= base_planned + 5) and d_now == 0 else "false"

    # ---- 3. OUTREACH_OK: fresh auth + preflight + send_one ----
    auths = conn.execute(
        "SELECT id, plan_id, outreach_batch_date, status, created_at FROM send_authorizations "
        "WHERE outreach_batch_date=? AND created_at >= ? ORDER BY id DESC",
        (ACTIVE_BATCH, WINDOW_START)).fetchall()
    out["FRESH_AUTH"] = [dict(r) for r in auths]
    out["OUTREACH_OK"] = "true" if (out_runs and any(a["status"] in ("approved", "in_progress", "consumed") for a in auths)) else "false"

    # ---- 4. SMTP_ACCEPTED (tonight, by message_type) ----
    sl = conn.execute(
        "SELECT message_type, COUNT(*) c FROM send_log "
        "WHERE outreach_batch_date=? AND (smtp_accepted_at >= ? OR sent_at >= ?) GROUP BY message_type",
        (ACTIVE_BATCH, WINDOW_START, WINDOW_START)).fetchall()
    sl_map = {r["message_type"]: r["c"] for r in sl}
    sent_emails = [r[0] for r in conn.execute(
        "SELECT DISTINCT email FROM send_log WHERE outreach_batch_date=? AND (smtp_accepted_at >= ? OR sent_at >= ?)",
        (ACTIVE_BATCH, WINDOW_START, WINDOW_START)).fetchall()]
    out["SMTP_ACCEPTED"] = sum(sl_map.values())
    out["SMTP_NEW_OUTREACH"] = sl_map.get("new_outreach", 0)
    out["SMTP_FOLLOW_UP"] = sl_map.get("follow_up", 0)
    out["SENT_EMAILS"] = sent_emails

    # ---- 5. BOUNCE / REPLY (linked to tonight's sent leads) ----
    bcol = link_col(conn, "bounce_log")
    rcol = link_col(conn, "reply_log")
    bounce = 0
    reply = 0
    if sent_emails and bcol:
        ph = ",".join("?" * len(sent_emails))
        bounce = q1(conn, f"SELECT COUNT(*) FROM bounce_log WHERE {bcol} IN ({ph})", sent_emails)
    if sent_emails and rcol:
        ph = ",".join("?" * len(sent_emails))
        reply = q1(conn, f"SELECT COUNT(*) FROM reply_log WHERE {rcol} IN ({ph})", sent_emails)
    out["BOUNCE"] = bounce
    out["REPLY"] = reply

    # ---- 6. POSTSEND_OK ----
    out["POSTSEND_OK"] = "true" if (post and post[0]["status"] == "completed") else "false"

    # ---- 7. FULL_LOOP_PASS ----
    full = (
        out["AUTOMATED_RUN"] == "observed"
        and out["PRESEND_OK"] == "true"
        and out["DUPLICATE_FSP"] == 0
        and out["OUTREACH_OK"] == "true"
        and out["SMTP_ACCEPTED"] >= 1
        and out["POSTSEND_OK"] == "true"
    )
    out["FULL_LOOP_PASS"] = "true" if full else "false"
    out["_captured_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    return out


def print_report(out, baseline):
    print("=" * 64)
    print("P2.1G — FIRST REAL AUTOMATED SEND OBSERVATION")
    print("=" * 64)
    print(f"AUTOMATED_RUN      = {out['AUTOMATED_RUN']}")
    print(f"PRESEND_OK         = {out['PRESEND_OK']}")
    print(f"FSP_CREATED        = {out['FSP_CREATED']}  (new_outreach={out['FSP_NEW_OUTREACH']}, follow_up={out['FSP_FOLLOW_UP']})")
    print(f"DUPLICATE_FSP      = {out['DUPLICATE_FSP']}  (idempotent={out['IDEMPOTENT']})")
    print(f"OUTREACH_OK        = {out['OUTREACH_OK']}")
    print(f"SMTP_ACCEPTED      = {out['SMTP_ACCEPTED']}  (new={out['SMTP_NEW_OUTREACH']}, fu={out['SMTP_FOLLOW_UP']})")
    print(f"BOUNCE             = {out['BOUNCE']}")
    print(f"REPLY              = {out['REPLY']}")
    print(f"POSTSEND_OK        = {out['POSTSEND_OK']}")
    print(f"FULL_LOOP_PASS     = {out['FULL_LOOP_PASS']}")
    print("-" * 64)
    if out["PRESEND_JOB"]:
        print(f"  pre-send  : {out['PRESEND_JOB']['started_at']} status={out['PRESEND_JOB']['status']} tgt={out['PRESEND_JOB']['target']} act={out['PRESEND_JOB']['actual']}")
    if out["OUTREACH_JOB"]:
        print(f"  outreach  : {out['OUTREACH_JOB']['started_at']} status={out['OUTREACH_JOB']['status']} reason={out['OUTREACH_JOB']['stop_reason']}")
    if out["POSTSEND_JOB"]:
        print(f"  post-send : {out['POSTSEND_JOB']['started_at']} status={out['POSTSEND_JOB']['status']}")
    if out["FRESH_AUTH"]:
        print(f"  fresh auth: " + ", ".join(f"auth={a['id']}({a['status']})" for a in out["FRESH_AUTH"]))
    if out["SENT_EMAILS"]:
        print(f"  sent({len(out['SENT_EMAILS'])}): " + ", ".join(out["SENT_EMAILS"][:10]))
    print("=" * 64)


def main():
    watch = "--watch" in sys.argv
    baseline = load_baseline()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    if not watch:
        out = observe(conn, baseline)
        json.dump(out, open(RESULT, "w"), indent=2, default=str)
        print_report(out, baseline)
        return

    # ---- watch mode: poll until post-send observed or hard timeout ----
    hard_end = time.mktime(time.strptime(WINDOW_END, "%Y-%m-%d %H:%M:%S")) + 1800  # +30min grace
    print(f"[watch] observing window {WINDOW_START} .. {WINDOW_END}; hard stop +30min")
    while True:
        out = observe(conn, baseline)
        if out["AUTOMATED_RUN"] == "observed" and out["POSTSEND_OK"] == "true":
            json.dump(out, open(RESULT, "w"), indent=2, default=str)
            print_report(out, baseline)
            print("[watch] FINALIZED — run complete.")
            break
        now = time.time()
        if now > hard_end:
            json.dump(out, open(RESULT, "w"), indent=2, default=str)
            print_report(out, baseline)
            print("[watch] HARD TIMEOUT — final state captured (run may not have completed).")
            break
        time.sleep(180)  # poll every 3 min


if __name__ == "__main__":
    main()
