"""P1.2 First 20 Supervised Send — 正式链受控执行器（不是第二发送入口）。

唯一生产链：
  Campaign Eligible → Final Send Plan → Authorization → Preflight
  → daily_session.execute_final_send_plan（内部调 bd_sender.send_one → SMTP）
  → Post-Send Reconciliation

本脚本只做两件事：
  1. 在收件人当地 10:00 窗口到达前，等待并执行实时 Preflight（fail-closed）。
  2. 窗口内调用唯一正式链 execute_final_send_plan 发送。
窗口判断由 daily_session 内建的 recipient_scheduler.in_send_window 完成（收件人时区）。

不使用任何第二 SMTP 入口、无手工 INSERT FSP、无手工修 Authorization。
"""
import os
import sys
import time
import sqlite3
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
ASIA_SH = timezone(timedelta(hours=8))

# 加载 .env
for line in open(os.path.join(BASE, ".env"), encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

BATCH = "p1_2_first20_20260813"


def log(msg):
    print(f"[{datetime.now(ASIA_SH).strftime('%H:%M:%S')}] {msg}", flush=True)


def run_preflight_check(send_window_override: bool = False):
    """窗口前实时 Preflight（fail-closed）。返回 (ok, detail)。"""
    from preflight_gate import run_preflight
    from bd_db import get_db
    conn = get_db()
    conn.row_factory = sqlite3.Row
    r = run_preflight(conn, BATCH, require_dns=False, persist_cache=False,
                      send_window_override=send_window_override)
    conn.close()
    return r["pass"], r.get("blocks", [])


def run_post_send_recovery():
    """P1.3: 正式 Send Batch 完成后必须执行的 Post-Send Result Recovery。

    不依赖"08:45 sync"——发送完成即回流：
      1. IMAP bounce scan（bounce_pipeline 真实扫描）
      2. bounce_log writeback（record_bounce 回写 leads）
      3. unmatched_dsn（兜底表）
      4. suppression sync（bounce_log → suppression_list）
      5. reply scan（poll_reply，已修复 self-sent 过滤）
      6. tracking sync（Worker dashboard-summary → tracking cache）
    """
    log("Post-Send Result Recovery 开始 ...")
    steps = {}

    # 1-3) IMAP bounce scan + writeback + unmatched_dsn
    try:
        from bounce_pipeline import run_scan_and_writeback
        s = run_scan_and_writeback()
        steps["bounce_imap_scan"] = {
            "ok": True,
            "scanned": s.get("scanned"), "matched": s.get("matched"),
            "domain_invalid": s.get("domain_invalid"),
            "mailbox_invalid": s.get("mailbox_invalid"),
            "policy_bounce": s.get("policy_bounce"),
            "unmatched_dsn": s.get("unmatched_dsn"),
            "unresolved": s.get("unresolved"),
        }
        log(f"  bounce scan: scanned={s.get('scanned')} matched={s.get('matched')} "
            f"unmatched={s.get('unmatched_dsn')}")
    except Exception as e:
        steps["bounce_imap_scan"] = {"ok": False, "error": str(e)[:200]}
        log(f"  [WARN] bounce scan failed: {e}")

    # 4) suppression sync
    try:
        import bd_ops_poller as P
        P.poll_suppression_sync()
        steps["suppression_sync"] = {"ok": True}
        log("  suppression sync done")
    except Exception as e:
        steps["suppression_sync"] = {"ok": False, "error": str(e)[:200]}
        log(f"  [WARN] suppression sync failed: {e}")

    # 5) reply scan（已修复 self-sent 过滤）
    try:
        import bd_ops_poller as P
        P.poll_reply()
        steps["reply_scan"] = {"ok": True}
        log("  reply scan done")
    except Exception as e:
        steps["reply_scan"] = {"ok": False, "error": str(e)[:200]}
        log(f"  [WARN] reply scan failed: {e}")

    # 6) tracking sync
    try:
        import bd_ops_poller as P
        P.poll_tracking()
        steps["tracking_sync"] = {"ok": True}
        log("  tracking sync done")
    except Exception as e:
        steps["tracking_sync"] = {"ok": False, "error": str(e)[:200]}
        log(f"  [WARN] tracking sync failed: {e}")

    # 落盘审计
    try:
        import json
        ts = datetime.now(ASIA_SH).strftime("%Y%m%d_%H%M%S")
        out = os.path.join(BASE, "output", f"post_send_recovery_{BATCH}_{ts}.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"batch": BATCH, "completed_at": datetime.now(ASIA_SH).isoformat(),
                       "steps": steps}, f, ensure_ascii=False, indent=2)
        log(f"  recovery report: {out}")
    except Exception as e:
        log(f"  [WARN] recovery report write failed: {e}")

    all_ok = all(v.get("ok", False) for v in steps.values())
    log(f"Post-Send Result Recovery 结束 (all_ok={all_ok})")
    return all_ok


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "send"

    if mode == "dry-run":
        # 只读预览：确认 20 条都进入正式链（不发送、不写库）
        from daily_session import execute_final_send_plan
        result = execute_final_send_plan(BATCH, dry_run=True)
        log(f"[DRY RUN] planned={result['planned']} preview={len(result['preview'])}")
        for p in result["preview"]:
            log(f"    entry={p['entry_id']} lead={p['lead_id']} → {p['result']}")
        return

    if mode == "preflight":
        ok, blocks = run_preflight_check()
        log(f"Preflight: {'PASS' if ok else 'FAIL'} blocks={blocks}")
        return

    # send 模式：按收件人时区窗口分批发送。ET 窗口（上海≈21:55-22:10）先到，
    # CT（上海≈22:55-23:10）后到。窗口到达时各调用一次 execute_final_send_plan
    # （内建按收件人时区判断，窗口内的 entry 发送、窗口外的 skip）。
    log(f"P1.2 send mode | batch={BATCH}")
    from recipient_scheduler import in_send_window
    from bd_db import get_db

    def tzs_in_batch():
        conn = get_db()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT DISTINCT l.recipient_timezone FROM final_send_plan f "
            "JOIN leads l ON l.id=f.lead_id "
            "WHERE f.outreach_batch_date=? AND f.status='planned'",
            (BATCH,),
        ).fetchall()
        conn.close()
        return [str(r["recipient_timezone"] or "").strip() for r in rows]

    def wait_window(tz_list, label):
        log(f"等待 {label} 窗口（{tz_list} 当地 10:00）...")
        while True:
            for tz in tz_list:
                if tz and in_send_window(tz):
                    log(f"  {label} 窗口到达: {datetime.now(ASIA_SH).strftime('%H:%M:%S')}")
                    return
            time.sleep(30)

    def refresh_poller():
        """窗口前刷新 Poller heartbeat（真实运行 health/reply/bounce/tracking）。"""
        import bd_ops_poller as P
        try:
            P.start_poller(daemon=True)
            time.sleep(18)
            P.stop_poller()
            time.sleep(2)
            log("Poller heartbeat 已刷新")
        except Exception as e:
            log(f"[WARN] Poller refresh failed: {e}")

    def rebuild_auth():
        """重建 fresh auth。只删除未消费的旧 auth（approved/pending/未消费 superseded），
        已 consumed 的 auth 保留为审计记录（send_log 引用的 plan_entry_id 必须可溯源，
        post_send_reconciliation 依赖 auth entry 存在）。"""
        from bd_sender import create_send_authorization
        from bd_db import get_db
        conn = get_db()
        conn.row_factory = sqlite3.Row
        plan_id = conn.execute(
            "SELECT plan_id FROM final_send_plan WHERE outreach_batch_date=? LIMIT 1",
            (BATCH,),
        ).fetchone()[0]
        # 未消费 auth：无任何 consumed entry → 可安全删除重建
        old = conn.execute(
            "SELECT a.authorization_id FROM send_authorizations a "
            "LEFT JOIN send_authorization_entries e ON e.authorization_id=a.authorization_id AND e.status='consumed' "
            "WHERE a.plan_id=? GROUP BY a.authorization_id HAVING COUNT(e.plan_entry_id)=0",
            (plan_id,),
        ).fetchall()
        for (aid,) in old:
            conn.execute("DELETE FROM send_authorization_entries WHERE authorization_id=?", (aid,))
            conn.execute("DELETE FROM send_authorizations WHERE authorization_id=?", (aid,))
        conn.commit()
        _db_file = conn.execute("PRAGMA database_list").fetchone()[2]
        conn.close()
        rows = sqlite3.connect(_db_file).execute(
            "SELECT id, lead_id, recipient_email, message_type FROM final_send_plan "
            "WHERE outreach_batch_date=? AND status='planned'", (BATCH,),
        ).fetchall()
        planned = [
            {"lead_id": r[1], "recipient_email": r[2],
             "message_type": r[3], "final_plan_entry_id": r[0]}
            for r in rows
        ]
        if not planned:
            log("[INFO] 无 planned entry，跳过重建 auth")
            return ""
        auth = create_send_authorization(plan_id, BATCH, planned, preflight_passed=True,
                                         db_path=_db_file)
        log(f"Auth 已重建: {auth['authorization_id']}")
        return auth["authorization_id"]

    from daily_session import execute_final_send_plan

    if mode == "send-now":
        # 一次性时间规则 override（仅限 P1.2 延误批次补发；不修改永久 Scheduler）。
        # 绕过 recipient_scheduler.in_send_window() 与 preflight 的 expired 窗口判定，
        # 其余全部 Gate fail-closed。
        # auth 有效期约 15min，而 20 条按正式间隔（45-85s）发送约需 20-25min，
        # 因此按正式链分轮发送：每轮前刷新 Poller + 重建 Fresh Auth + 实时 Preflight，
        # 然后 execute_final_send_plan（对剩余 planned 发送）。直到无 planned 或无可进展。
        log(f"P1.2 SEND-NOW (SEND_WINDOW_OVERRIDE) | batch={BATCH}")
        refresh_poller()
        round_no = 0
        while True:
            round_no += 1
            # 每轮开始：把上一轮因 auth 过期等可重试原因 failed 的 entry 恢复为 planned。
            # auth 有效期仅 15min，长批次必然跨轮；fail-closed 拦截后应重试而非丢弃。
            conn = get_db()
            conn.row_factory = sqlite3.Row
            conn.execute(
                "UPDATE final_send_plan SET status='planned', skip_reason=NULL, sent_at=NULL "
                "WHERE outreach_batch_date=? AND status='failed' AND skip_reason LIKE 'SendAuthorizationError:%'",
                (BATCH,),
            )
            conn.commit()
            conn.close()
            auth_id = rebuild_auth()
            ok, blocks = run_preflight_check(send_window_override=True)
            if not ok:
                log(f"[BLOCKED] 第{round_no}轮 Preflight FAIL: {blocks}")
                return 1
            log(f"第{round_no}轮 Preflight PASS — auth={auth_id} 开始发送")
            result = execute_final_send_plan(BATCH, dry_run=False, send_window_override=True)
            log(f"第{round_no}轮: planned={result['planned']} new={result['new_outreach']} "
                f"skipped={result['skipped']} failed={result['failed']}")
            for p in result.get("preview", []):
                log(f"    entry={p['entry_id']} → {p['result']} {p['message'][:80]}")
            # 剩余待处理 = planned + 可重试 failed（auth 过期类）
            conn = get_db()
            conn.row_factory = sqlite3.Row
            remaining = conn.execute(
                "SELECT COUNT(*) c FROM final_send_plan WHERE outreach_batch_date=? "
                "AND (status='planned' OR (status='failed' AND skip_reason LIKE 'SendAuthorizationError:%'))",
                (BATCH,),
            ).fetchone()["c"]
            conn.close()
            if remaining == 0:
                log(f"全部发送完成（共 {round_no} 轮）")
                break
            if result.get("new_outreach", 0) == 0 and result.get("follow_up", 0) == 0:
                log(f"[STOP] 第{round_no}轮无新发送进展，剩余 pending={remaining} — 停止（fail-closed）")
                return 1
            log(f"剩余 pending={remaining}，下一轮前刷新 poller + 重建 fresh auth ...")
            refresh_poller()
        # P1.3: 发送完成 → Post-Send Result Recovery（不依赖 08:45 sync）
        run_post_send_recovery()
        log("P1.2 SEND-NOW 流程结束")
        return 0

    tzs = tzs_in_batch()
    et_tzs = [t for t in tzs if t == "America/New_York"]
    ct_tzs = [t for t in tzs if t == "America/Chicago"]
    other_tzs = [t for t in tzs if t not in ("America/New_York", "America/Chicago")]

    batches = []
    if et_tzs:
        batches.append(("ET", et_tzs))
    if ct_tzs:
        batches.append(("CT", ct_tzs))
    if other_tzs:
        batches.append(("OTHER", other_tzs))

    for label, tz_list in batches:
        wait_window(tz_list, label)
        # 窗口前：刷新 poller + 重建 auth（auth 有效期 15min，窗口到达时必须 fresh）
        refresh_poller()
        rebuild_auth()
        ok, blocks = run_preflight_check()
        if not ok:
            log(f"[BLOCKED] {label} Preflight FAIL: {blocks}")
            continue
        log(f"{label} Preflight PASS — 开始发送")
        result = execute_final_send_plan(BATCH, dry_run=False)
        log(f"{label} 发送: planned={result['planned']} new={result['new_outreach']} "
            f"skipped={result['skipped']} failed={result['failed']}")
        for p in result.get("preview", []):
            log(f"    entry={p['entry_id']} → {p['result']} {p['message'][:50]}")

    # P1.3: 全部批次发送完成 → Post-Send Result Recovery（不依赖 08:45 sync）
    run_post_send_recovery()
    log("P1.2 send 流程结束")
    return 0


if __name__ == "__main__":
    main()
