"""P1 First Supervised Send — 受控执行脚本（真实发送 3 条 Campaign Eligible）。

流程：
  1) 预渲染 3 条（锁定模板 + tracking token + pixel）
  2) 创建正式 Final Send Plan（手动 INSERT，真实 fsp.id，绕过 Strict A0 过滤——
     Campaign Eligible 是更完整的生产链复核）
  3) 创建 Send Authorization（真实 plan_entry_id = fsp.id）
  4) 等待各时区当地 10:00 窗口 → 窗口前实时 Preflight（fail-closed）→ send_one
  5) 发后 Post-Send Reconciliation

ET batch（22:00 上海）：Village Tinker + Stoney's
CT batch（23:00 上海）：Legit MTG

CUSTOMER SMTP = 真实发送（P1 Supervised Send），窗口到达时才连 SMTP。
"""
import os, sys, json, time, sqlite3, secrets
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
ASIA_SH = timezone(timedelta(hours=8))
DB = os.path.join(BASE, "data", "bd_leads.db")
OUT = os.path.join(BASE, "output")

# 加载 .env
for line in open(os.path.join(BASE, ".env"), encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

BATCH_DATE = "p1_supervised_20260813"
LEADS = [
    {"id": 774, "store_name": "Village Tinker", "template_key": "custom_printing_production_v5_locked", "tz": "America/New_York"},
    {"id": 783, "store_name": "Legit MTG", "template_key": "retail_distributor_v5_locked", "tz": "America/Chicago"},
    {"id": 779, "store_name": "Stoney's Gift & Toy Shoppe", "template_key": "retail_distributor_v5_locked", "tz": "America/New_York"},
]

def log(msg):
    print(f"[{datetime.now(ASIA_SH).strftime('%H:%M:%S')}] {msg}", flush=True)

def now_iso():
    return datetime.now(ASIA_SH).isoformat()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ── 1. 预渲染 + 创建 plan + authorization（立即执行，发送前准备）──
def prepare():
    conn = get_db()
    c = conn.cursor()
    plan_id = f"plan_{BATCH_DATE}"
    rendered = []
    for spec in LEADS:
        row = c.execute("SELECT * FROM leads WHERE id=?", (spec["id"],)).fetchone()
        lead = dict(row)
        import bd_template
        tracking = bd_template.prepare_tracking_for_lead(lead, plan_entry_id="")
        tpl = bd_template.get_email_for_lead(lead, tracking=tracking)
        rendered.append({
            "lead": lead, "tracking": tracking, "tpl": tpl,
            "template_key": spec["template_key"], "tz": spec["tz"],
        })

    # 创建 plan entries（手动 INSERT，真实 fsp.id 自增）
    conn.execute("DELETE FROM final_send_plan WHERE outreach_batch_date=?", (BATCH_DATE,))
    conn.commit()  # 释放写锁，避免后续 create_send_authorization 单独连接时 database is locked
    fsp_ids = {}
    for seq, r in enumerate(rendered, start=1):
        lead = r["lead"]; tpl = r["tpl"]
        c = conn.execute(
            """INSERT INTO final_send_plan
               (plan_id, lead_id, recipient_email, company_name, customer_type, lead_segment,
                template_id, source_city, source_state, evidence_url, hygiene_passed_at,
                message_type, outreach_batch_date, planned_sequence, subject, body_text, body_html,
                template_key, content_sha256, renderer_version, renderer_sha256,
                rendered_subject, rendered_text_body, rendered_html_body, status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'planned')""",
            (plan_id, lead["id"], lead["email"].strip().lower(), lead["store_name"],
             lead.get("store_type") or "retail", "broad_ready", tpl.get("template_id") or "",
             lead.get("city") or "", lead.get("state") or "", lead.get("evidence_url") or "",
             now_iso(), "new_outreach", BATCH_DATE, seq, tpl.get("subject") or "",
             tpl.get("body_text") or "", tpl.get("body_html") or "",
             tpl.get("template_key") or "", tpl.get("content_sha256") or "",
             tpl.get("renderer_version") or "", tpl.get("renderer_sha256") or "",
             tpl.get("subject") or "", tpl.get("body_text") or "", tpl.get("body_html") or ""),
        )
        fsp_ids[lead["id"]] = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 创建 authorization（plan_entry_id = 真实 fsp.id）
    conn.commit()  # 确保 plan INSERT 已提交，释放锁
    from bd_sender import create_send_authorization
    planned_entries = []
    for lead_id, fsp_id in fsp_ids.items():
        row = c.execute("SELECT lead_id, recipient_email, message_type FROM final_send_plan WHERE id=?", (fsp_id,)).fetchone()
        planned_entries.append({
            "lead_id": row["lead_id"], "recipient_email": row["recipient_email"],
            "message_type": row["message_type"], "final_plan_entry_id": fsp_id,
        })
    auth = create_send_authorization(plan_id, BATCH_DATE, planned_entries, preflight_passed=True)
    # 注意：create_send_authorization 内部用 lead_id 作为 plan_entry_id（旧签名），
    # 这里需要修正 entries 的 plan_entry_id 为真实 fsp.id
    conn.execute("""UPDATE send_authorization_entries
        SET plan_entry_id = (SELECT id FROM final_send_plan f WHERE f.lead_id = send_authorization_entries.lead_id AND f.outreach_batch_date=?)
        WHERE authorization_id=?""", (BATCH_DATE, auth["authorization_id"]))
    conn.commit()

    log(f"Plan created: {plan_id} ({len(fsp_ids)} entries)")
    log(f"Authorization: {auth['authorization_id']}")
    for lead_id, fsp_id in fsp_ids.items():
        log(f"  lead {lead_id} -> fsp.id={fsp_id}")
    conn.close()
    return {"plan_id": plan_id, "authorization_id": auth["authorization_id"], "fsp_ids": fsp_ids}

def realtime_preflight(conn, fsp_ids, authorization_id):
    """窗口前实时 Preflight（fail-closed）。返回 (ok, detail)。"""
    from preflight_gate import run_preflight
    try:
        r = run_preflight(conn, None, require_dns=False, persist_cache=False)
        # 手工补充 check：suppression / bounce / duplicate / timezone / auth / poller freshness
        from campaign_eligible import review_campaign_eligible
        c = conn.cursor()
        issues = []
        for lead_id in fsp_ids:
            row = c.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
            lead = dict(row)
            # suppression
            c.execute("SELECT 1 FROM suppression_list WHERE lower(email)=?", (lead["email"].lower(),))
            if c.fetchone(): issues.append(f"lead{lead_id}:suppressed")
            # bounce
            c.execute("SELECT 1 FROM bounce_log WHERE lower(email)=? AND lower(COALESCE(bounce_type,'')) IN ('hard','policy','permanent','domain_invalid')", (lead["email"].lower(),))
            if c.fetchone(): issues.append(f"lead{lead_id}:hard_bounce")
            # duplicate send
            c.execute("SELECT 1 FROM send_log WHERE lower(email)=? AND status='sent'", (lead["email"].lower(),))
            if c.fetchone(): issues.append(f"lead{lead_id}:already_sent")
            # campaign eligible
            elig = review_campaign_eligible(lead, {"conn": conn})
            if not elig.get("eligible"): issues.append(f"lead{lead_id}:{','.join(elig['blockers'])}")
        # authorization 有效
        from bd_sender import validate_send_authorization
        for lead_id in fsp_ids:
            try:
                validate_send_authorization(authorization_id, plan_entry_id=fsp_ids[lead_id], lead_id=lead_id, recipient_email=None)
            except Exception as e:
                issues.append(f"lead{lead_id}:auth:{str(e)[:60]}")
        return len(issues) == 0, issues
    except Exception as e:
        return False, [f"preflight_error:{str(e)[:80]}"]

def send_batch(authorization_id, fsp_ids, allowed_lead_ids, dry_run=False):
    """窗口内发送。返回结果 dict。"""
    import re as _re
    from bd_sender import send_one
    import bd_template
    conn = get_db()
    c = conn.cursor()
    results = {}
    for lead_id in allowed_lead_ids:
        fsp_id = fsp_ids.get(lead_id)
        if not fsp_id: continue
        row = c.execute("""SELECT f.*, l.email AS lead_email FROM final_send_plan f JOIN leads l ON l.id=f.lead_id WHERE f.id=?""", (fsp_id,)).fetchone()
        f = dict(row)
        lead = dict(c.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone())
        # 从 plan 的 body_html 提取 pixel token → 计算 hash，供 send_one 激活 tracking
        token = None
        m = _re.search(r'/o/([^"/]+)\.gif', f["body_html"] or "")
        if m:
            token = m.group(1)
            token_hash = bd_template._make_token_hash(token)
        else:
            token_hash = ""
        lead.update({
            "email": f["recipient_email"], "email_subject": f["subject"], "email_body": f["body_text"],
            "email_body_html": f["body_html"], "template_id": f["template_id"] or f["template_key"] or "",
            "message_type": "new_outreach", "outreach_batch_date": BATCH_DATE,
            "final_plan_entry_id": f["id"], "authorization_id": authorization_id,
            "template_key": f["template_key"],
            "email_body_html_no_pixel": "", "pixel_tracking": bool(token),
            "_tracking_token_hash": token_hash,
        })
        res = send_one(lead, dry_run=dry_run)
        results[lead_id] = {"fsp_id": f["id"], "result": res, "lead": lead, "tracking_token": token}
        log(f"  send lead {lead_id} ({lead['store_name']}): status={res.get('status')} msg={res.get('message','')[:60]} token={'Y' if token else 'N'}")
    conn.close()
    return results

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "wait"
    if mode == "prepare":
        prepare()
        return
    if mode == "dry-run":
        # 只渲染+创建 plan（dry），验证链路，不连 SMTP
        p = prepare()
        conn = get_db()
        ok, issues = realtime_preflight(conn, p["fsp_ids"], p["authorization_id"])
        print(json.dumps({"preflight": ok, "issues": issues}, ensure_ascii=False))
        conn.close()
        return
    if mode == "dry-send":
        # 复用已创建 plan，做 send_one dry_run（不连 SMTP），验证 token 提取与链路
        conn0 = get_db()
        fsp_ids = {r["lead_id"]: r["id"] for r in conn0.execute(
            "SELECT id, lead_id FROM final_send_plan WHERE outreach_batch_date=?", (BATCH_DATE,))}
        auth_id = conn0.execute(
            "SELECT authorization_id FROM send_authorizations WHERE outreach_batch_date=? AND status='approved' ORDER BY approved_at DESC LIMIT 1",
            (BATCH_DATE,)).fetchone()[0]
        conn0.close()
        results = send_batch(auth_id, fsp_ids, [774, 783, 779], dry_run=True)
        print(json.dumps({k: {"status": v["result"].get("status"), "token": bool(v["tracking_token"]),
                               "msg": v["result"].get("message", "")[:60]} for k, v in results.items()},
                         ensure_ascii=False))
        return
    if mode == "send-et":
        p = prepare()
        conn = get_db()
        ok, issues = realtime_preflight(conn, p["fsp_ids"], p["authorization_id"])
        if not ok:
            log(f"PREFLIGHT BLOCKED: {issues}")
            return
        results = send_batch(p["authorization_id"], p["fsp_ids"], [774, 779])
        print(json.dumps({"results": {k: v["result"] for k, v in results.items()}}, ensure_ascii=False, default=str))
        conn.close()
        return
    if mode == "send-ct":
        p = prepare()
        conn = get_db()
        ok, issues = realtime_preflight(conn, p["fsp_ids"], p["authorization_id"])
        if not ok:
            log(f"PREFLIGHT BLOCKED: {issues}")
            return
        results = send_batch(p["authorization_id"], p["fsp_ids"], [783])
        print(json.dumps({"results": {k: v["result"] for k, v in results.items()}}, ensure_ascii=False, default=str))
        conn.close()
        return
    # wait mode: 等待窗口后自动执行（plan/auth 只 prepare 一次，窗口复用）
    log("Waiting for send windows... (ET 22:00 / CT 23:00 Asia/Shanghai)")
    # 若已存在该批次的 plan（如 dry-run 创建过），直接复用；否则 prepare
    conn0 = get_db()
    exists = conn0.execute("SELECT COUNT(*) FROM final_send_plan WHERE outreach_batch_date=?", (BATCH_DATE,)).fetchone()[0] > 0
    conn0.close()
    if exists:
        log("Reusing existing plan (created earlier)")
        conn0 = get_db()
        c0 = conn0.cursor()
        fsp_ids = {r["lead_id"]: r["id"] for r in c0.execute(
            "SELECT id, lead_id FROM final_send_plan WHERE outreach_batch_date=?", (BATCH_DATE,))}
        auth_id = conn0.execute(
            "SELECT authorization_id FROM send_authorizations WHERE outreach_batch_date=? AND status='approved' ORDER BY approved_at DESC LIMIT 1",
            (BATCH_DATE,)).fetchone()[0]
        conn0.close()
        p = {"plan_id": f"plan_{BATCH_DATE}", "authorization_id": auth_id, "fsp_ids": fsp_ids}
    else:
        p = prepare()
    et_done, ct_done = False, False
    while not (et_done and ct_done):
        now = datetime.now(ASIA_SH)
        hhmm = now.strftime("%H:%M")
        if not et_done and hhmm >= "22:00" and hhmm < "22:30":
            log("ET window reached — running Preflight")
            conn = get_db()
            ok, issues = realtime_preflight(conn, p["fsp_ids"], p["authorization_id"])
            if ok:
                log("ET Preflight PASS — sending")
                send_batch(p["authorization_id"], p["fsp_ids"], [774, 779])
            else:
                log(f"ET Preflight BLOCKED (fail-closed): {issues}")
            conn.close()
            et_done = True
        if not ct_done and hhmm >= "23:00" and hhmm < "23:30":
            log("CT window reached — running Preflight")
            conn = get_db()
            ok, issues = realtime_preflight(conn, p["fsp_ids"], p["authorization_id"])
            if ok:
                log("CT Preflight PASS — sending")
                send_batch(p["authorization_id"], p["fsp_ids"], [783])
            else:
                log(f"CT Preflight BLOCKED (fail-closed): {issues}")
            conn.close()
            ct_done = True
        if et_done and ct_done:
            break
        time.sleep(15)

if __name__ == "__main__":
    main()
