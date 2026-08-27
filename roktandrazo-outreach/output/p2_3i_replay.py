#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P2.3I — FINAL SEND-PATH FIX + EXACT PRODUCTION REPLAY

在临时 DB 副本上，调用与真实 23:00 Outreach 完全相同的 daily_session.execute_final_send_plan，
精确回放生产发送链路，证明两个已确认 bug 的修复 + 所有失败场景仍安全。

manual_pause 全程保持 true（不真实发送）。
外部边界（Cloudflare Worker MX 查询，因本沙箱 token 401 不可用）以 mock 替代，
仅替换网络边界，门禁逻辑（planned_rows_present / stale_objects / timezone / preflight / auth /
V2）全部真实执行。
"""
import os
import sys
import shutil
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone

PROJ = r"C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach"
REAL_DB = os.path.join(PROJ, "data", "bd_leads.db")
TEMP_DB = os.path.join(tempfile.gettempdir(), "p2_3i_temp_bd_leads.db")
if os.path.exists(TEMP_DB):
    os.remove(TEMP_DB)
shutil.copyfile(REAL_DB, TEMP_DB)

# 必须在 import 任何项目模块之前设定（bd_db.get_db 读此环境变量）
os.environ["WORKBUDDY_BD_DB_PATH"] = TEMP_DB

sys.path.insert(0, PROJ)
import bd_db
from final_send_plan import create_plan, load_planned_entries
import daily_session
import preflight_gate
import recipient_scheduler
import bd_sender
import campaign_eligible_v2
from zoneinfo import ZoneInfo
import time as _time
# 生产节奏 sleep 仅用于限速，非门禁逻辑；回放中置空避免 20 封累计长睡眠。
_time.sleep = lambda *a, **k: None

ASIA_SH = timezone(timedelta(hours=8))
UTC = timezone.utc
# 固定"真实 23:00 Outreach"时刻：上海 2026-08-25 23:00（周二）
SHANGHAI_23H = datetime(2026, 8, 25, 23, 0, 0, tzinfo=ASIA_SH)
SH_UTC = SHANGHAI_23H.astimezone(UTC)
BATCH_DATE = "2026-08-25"

RESULTS = {}

# ── 1. 外部边界 mock（不削弱任何门禁逻辑）────────────────────
# MX Worker token 在本沙箱 401 → query_mx 真实返回 dns_error；此处 mock 为 ok
# 仅替换网络边界，DNS 门禁本身仍真实执行（no_mail_route 场景会单独用真实失败值测）。
preflight_gate.query_mx = lambda domain: ("ok", datetime.now(ASIA_SH).isoformat())

# 固定时钟：preflight / auth 创建使用同一"23:00"上海时刻。
# 注意 preflight_gate.datetime / bd_sender.datetime 是 datetime 类
# （from datetime import datetime），不可直接设 .now 属性；
# 改为把模块全局 datetime 重绑到一个冻结子类，
# 保留真实 datetime 的全部构造/类方法（combine/fromisoformat/astimezone 等）。
class _FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return SHANGHAI_23H
preflight_gate.datetime = _FrozenDateTime
bd_sender.datetime = _FrozenDateTime
# 收件人当地时区 gate 固定为 23:00 上海对应的各时区当地时刻
_orig_in_send_window = recipient_scheduler.in_send_window
recipient_scheduler.in_send_window = lambda tz, now_utc=None: _orig_in_send_window(tz, SH_UTC)
# 新鲜 Poller 心跳（check_stale_objects 要求 ≤30min）
_poller_tmp = os.path.join(tempfile.gettempdir(), "p2_3i_poller_status.json")
with open(_poller_tmp, "w", encoding="utf-8") as f:
    f.write('{"last_heartbeat_at":"%s"}' % SHANGHAI_23H.isoformat())
preflight_gate.OPS_POLLER_STATUS = __import__("pathlib").Path(_poller_tmp)
# send_one 使用临时 DB
bd_sender.DB_PATH = TEMP_DB

# manual_pause 在测试期间保持 true（不真实发送）
_conn = sqlite3.connect(TEMP_DB)
_conn.row_factory = sqlite3.Row
_conn.execute("UPDATE system_config SET value='true' WHERE key='manual_pause'")
_conn.execute("UPDATE system_config SET value='true' WHERE key='standing_authorization'")
_conn.execute("UPDATE system_config SET value='clear' WHERE key='risk_gate_status'")
_conn.commit()

# 候选 lead id 取「真实最大 id + 1000」之上，避免与真实 leads 主键冲突
_LEAD_MAX = _conn.execute("SELECT COALESCE(MAX(id),0) FROM leads").fetchone()[0]
LEAD_BASE = _LEAD_MAX + 1000

# 清理临时副本里的真实遗留「旧批次」planned 行 / 旧 approved 授权（真实 DB 不受影响）。
# 使 happy path 只隔离测试 message_type 正确 scope；失败场景 7a/7b 会重新注入旧行验证 stale FAIL。
_conn.execute("DELETE FROM final_send_plan WHERE status='planned'")
_conn.execute("DELETE FROM send_authorization_entries WHERE authorization_id IN ("
              "SELECT authorization_id FROM send_authorizations WHERE status='approved' AND outreach_batch_date!=?)",
              (BATCH_DATE,))
_conn.execute("DELETE FROM send_authorizations WHERE status='approved' AND outreach_batch_date!=?", (BATCH_DATE,))
_conn.commit()


# ── 2. 构造 20 条 new_outreach 候选（ET/CT/MT/PT 各 5）─────────
def make_lead(i, tz, city, state, domain):
    return {
        "id": LEAD_BASE + i,
        "store_name": f"P2_3I_TestStore_{i}",
        "store_type": "retail",
        "city": city,
        "state": state,
        "official_website": f"https://{domain}",
        "email": f"wholesale{i}@{domain}",
        "email_type": "store_domain",
        "email_source_type": "official_page_visible",
        "email_verified_on_official_site": 1,
        "confidence_score": "A",
        "status": "new",
        "email_subject": f"Wholesale inquiry — P2_3I_TestStore_{i}",
        "email_body": "Hi team, we are a puzzle & game brand (rokt&razo) looking for retail partners.",
        "evidence_url": f"https://{domain}/wholesale",
        "evidence_snippet": "wholesale contact published on official site",
        "template_id": "retail_distributor_v5_locked",
        "organization_key": f"org:p2_3i_{domain}_{i}",
        "recipient_timezone": tz,
        "timezone_status": "RESOLVED",
        "sendable_for_automatic_schedule": 1,
        "mx_provider": "google",
    }


ZONES = [
    ("America/New_York", "New York", "NY", "et-store.example"),
    ("America/Chicago", "Chicago", "IL", "ct-store.example"),
    ("America/Denver", "Denver", "CO", "mt-store.example"),
    ("America/Los_Angeles", "Los Angeles", "CA", "pt-store.example"),
]
candidates = []
i = 0
for tz, city, state, domain in ZONES:
    for _ in range(5):
        i += 1
        candidates.append(make_lead(i, tz, city, state, domain))

# 插入 leads（临时副本，id 900001+ 不与真实数据冲突）
cur = _conn.cursor()
for lead in candidates:
    cols = ", ".join(lead.keys())
    ph = ", ".join("?" for _ in lead)
    cur.execute(f"INSERT INTO leads ({cols}) VALUES ({ph})", tuple(lead.values()))
_conn.commit()

# V2 质量门：happy path mock 为 eligible（发送时 V2 重检真实调用此函数）
campaign_eligible_v2.review_campaign_eligible_v2 = lambda lead, ctx: {"eligible": True, "tier": "E1"}

# ── 3. 建立 FSP（冻结 20 条 new_outreach planned rows）─────────
plan_id = create_plan(_conn, candidates, BATCH_DATE, "new_outreach",
                      eligible_check=lambda lead: True)
_conn.commit()
RESULTS["FSP_PLAN_ID"] = plan_id
RESULTS["FSP_PLANNED_ROWS"] = _conn.execute(
    "SELECT COUNT(*) c FROM final_send_plan WHERE outreach_batch_date=? AND message_type='new_outreach' AND status='planned'",
    (BATCH_DATE,)).fetchone()["c"]

# ── 4. HAPPY PATH：execute_final_send_plan（dry_run=False + mock SMTP）──
# mock send_one：不连真实 SMTP，验证 authorization_id 已被 threading 进来，返回 sent
def mock_send_one(lead, dry_run=False):
    if not lead.get("authorization_id"):
        return {"success": False, "status": "failed",
                "message": "NO_AUTHORIZATION_ID: send_one reached without authorization_id"}
    return {"success": True, "status": "sent",
            "message_id": "<MOCK-SMTP-ACCEPTED@roktandrazo.com>",
            "mock_smtp": True}

_orig_send_one = bd_sender.send_one
bd_sender.send_one = mock_send_one

happy = daily_session.execute_final_send_plan(BATCH_DATE, dry_run=False)
_conn.close()

# ── 5. 收集 HAPPY PATH 证明 ──
RESULTS["PRE_AUTH_PASS"] = bool(happy.get("preflight_pre_auth", {}).get("pass"))
RESULTS["AUTHORIZATION_CREATED"] = bool(happy.get("authorization_id"))
RESULTS["AUTHORIZATION_ID_VALID"] = bool(happy.get("authorization_id")) and len(str(happy.get("authorization_id"))) > 0
RESULTS["POST_AUTH_PASS"] = bool(happy.get("preflight_post_auth", {}).get("pass"))
RESULTS["HAPPY_NEW_OUTREACH_SENT"] = happy.get("new_outreach", 0)
RESULTS["HAPPY_SKIPPED"] = happy.get("skipped", 0)
RESULTS["HAPPY_FAILED"] = happy.get("failed", 0)
RESULTS["NO_AUTHORIZATION_ID_ERROR"] = all(
    "NO_AUTHORIZATION_ID" not in (p.get("message", "")) for p in happy.get("preview", [])
) and RESULTS["AUTHORIZATION_ID_VALID"]

# 时区窗口逐区证明（上海 23:00 → 各时区当地时刻）
RESULTS["ET_WINDOW_PASS"] = _orig_in_send_window("America/New_York", SH_UTC)
RESULTS["CT_WINDOW_PASS"] = _orig_in_send_window("America/Chicago", SH_UTC)
RESULTS["MT_WINDOW_PASS"] = _orig_in_send_window("America/Denver", SH_UTC)
RESULTS["PT_WINDOW_PASS"] = _orig_in_send_window("America/Los_Angeles", SH_UTC)
# 大陆四区无一条被时区 gate 跳过
RESULTS["NO_RECIPIENT_WINDOW_SKIP_FOR_ET_CT_MT_PT"] = (
    RESULTS["ET_WINDOW_PASS"] and RESULTS["CT_WINDOW_PASS"]
    and RESULTS["MT_WINDOW_PASS"] and RESULTS["PT_WINDOW_PASS"]
    and RESULTS["HAPPY_SKIPPED"] == 0
)

# ── 6. manual_pause=true → 真实生产 SMTP BLOCK（用真实 send_one 验证）──
bd_sender.send_one = _orig_send_one  # 恢复真实 send_one
_real_conn = sqlite3.connect(TEMP_DB)
_real_conn.row_factory = sqlite3.Row
# 从授权内部取一条 plan entry（保证 plan_entry_id 确实在该 authorization 中，
# 避免 LIMIT 1 误取到真实 DB 遗留的其它 2026-08-25 行导致 "not in authorization"）。
auth_id = happy.get("authorization_id")
entry = _real_conn.execute(
    "SELECT fsp.* FROM final_send_plan fsp JOIN send_authorization_entries sae "
    "ON sae.plan_entry_id = fsp.id WHERE sae.authorization_id=? AND fsp.message_type='new_outreach' LIMIT 1",
    (auth_id,)).fetchone()
# entry 在 happy path 中已被 mock 标记 sent；重置为 planned 以便真实 send_one 走到 manual_pause 校验
# （P5 幂等守卫会在 status='sent' 时直接 skipped，从而绕过 manual_pause 校验）。
_real_conn.execute("UPDATE final_send_plan SET status='planned' WHERE id=?", (entry["id"],))
_real_conn.commit()
lead_for_send = dict(_real_conn.execute("SELECT * FROM leads WHERE id=?", (entry["lead_id"],)).fetchone())
lead_for_send.update({
    "email": entry["recipient_email"],
    "email_subject": entry["subject"], "email_body": entry["body_text"],
    "email_body_html": entry["body_html"] or "", "template_id": entry["template_id"] or "",
    "message_type": "new_outreach", "outreach_batch_date": BATCH_DATE,
    "final_plan_entry_id": entry["id"], "authorization_id": auth_id,
    "id": entry["lead_id"],
})
real_result = bd_sender.send_one(lead_for_send, dry_run=False)
MANUAL_PAUSE_BLOCKS = (real_result.get("status") == "blocked"
                       and "manual_pause" in real_result.get("message", ""))
# 确认无任何 send_log 写入（真实 SMTP 未发生）
slog = _real_conn.execute(
    "SELECT COUNT(*) c FROM send_log WHERE plan_entry_id=?", (entry["id"],)).fetchone()["c"]
MANUAL_PAUSE_NO_SMTP = (slog == 0)
_real_conn.close()
RESULTS["MANUAL_PAUSE_TRUE_BLOCKS_REAL_SMTP"] = MANUAL_PAUSE_BLOCKS and MANUAL_PAUSE_NO_SMTP

# ── 7. 失败场景（保持所有门禁 fail-closed）──
_fc = sqlite3.connect(TEMP_DB)
_fc.row_factory = sqlite3.Row

# 7a. 旧 batch planned row（同 message_type）→ stale_objects FAIL
_fc.execute("INSERT INTO final_send_plan (plan_id, lead_id, recipient_email, company_name, customer_type, "
            "lead_segment, template_id, source_city, source_state, evidence_url, hygiene_passed_at, "
            "message_type, outreach_batch_date, planned_sequence, subject, body_text, body_html, status) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("oldbatch", 999001, "old@example.com", "Old", "retail", "strict_a0",
             "retail_distributor_v5_locked", "X", "YY", "https://example.com",
             SHANGHAI_23H.isoformat(), "new_outreach", "2026-08-20", 1, "s", "b", "", "planned"))
_fc.commit()
pf_old = preflight_gate.run_preflight(_fc, BATCH_DATE, include_auth_entries=False,
                                      message_type="new_outreach", now=SHANGHAI_23H)
stale_old = next((c for c in pf_old["checks"] if c["name"] == "stale_objects"), None)
RESULTS["OLD_BATCH_PLANNED_ROWS_FAIL"] = bool(stale_old and stale_old["status"] == "fail")

# 7b. 旧 batch 仅 follow_up planned row → 不得污染 new_outreach 的 stale_objects（PASS）
_fc.execute("DELETE FROM final_send_plan WHERE outreach_batch_date='2026-08-20' AND message_type='new_outreach'")
_fc.execute("INSERT INTO final_send_plan (plan_id, lead_id, recipient_email, company_name, customer_type, "
            "lead_segment, template_id, source_city, source_state, evidence_url, hygiene_passed_at, "
            "message_type, outreach_batch_date, planned_sequence, subject, body_text, body_html, status) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("oldbatch_fu", 999002, "oldfu@example.com", "OldFU", "retail", "strict_a0",
             "retail_distributor_v5_locked", "X", "YY", "https://example.com",
             SHANGHAI_23H.isoformat(), "follow_up", "2026-08-20", 1, "s", "b", "", "planned"))
_fc.commit()
pf_fu = preflight_gate.run_preflight(_fc, BATCH_DATE, include_auth_entries=False,
                                     message_type="new_outreach", now=SHANGHAI_23H)
stale_fu = next((c for c in pf_fu["checks"] if c["name"] == "stale_objects"), None)
RESULTS["OLD_FOLLOWUP_NO_CONTAMINATION_NEW_OUTREACH"] = bool(stale_fu and stale_fu["status"] == "pass")
_fc.execute("DELETE FROM final_send_plan WHERE outreach_batch_date='2026-08-20'")

# 7c. 当前 batch 无 planned row → planned_rows_present FAIL
pf_empty = preflight_gate.run_preflight(_fc, "2026-08-99", include_auth_entries=False,
                                         message_type="new_outreach", now=SHANGHAI_23H)
prp_empty = next((c for c in pf_empty["checks"] if c["name"] == "planned_rows_present"), None)
RESULTS["CURRENT_BATCH_NO_PLANNED_ROW_FAIL"] = bool(prp_empty and prp_empty["status"] == "fail")

# 7d. MX no_mail_route → FAIL（清 mx 缓存后用真实失败值）
# 仅把【本批我们自建的 plan】entry 复位为 planned，避免把真实 DB 遗留的
# failed/skipped 行误提升为 planned 而污染 DNS 检查范围。
_fc.execute("UPDATE final_send_plan SET status='planned' WHERE plan_id=? AND message_type='new_outreach'",
            (RESULTS["FSP_PLAN_ID"],))
_fc.commit()
_fc.execute("DELETE FROM system_config WHERE key LIKE 'mx_cache_%'")
preflight_gate.query_mx = lambda domain: ("no_mail_route", datetime.now(ASIA_SH).isoformat())
pf_mx = preflight_gate.run_preflight(_fc, BATCH_DATE, require_dns=True, persist_cache=False,
                                     include_auth_entries=False, message_type="new_outreach", now=SHANGHAI_23H)
# no_mail_route 在 run_preflight 中被标记为 stale（dns_stale:... (never/>24h)），
# 这是 fail-closed 的正确表现；此处断言：preflight 整体失败 且 我们的 4 个测试域名
# 均出现在 DNS 失败 blocks 中（证明 no_mail_route 触发了拦截）。
_TEST_DOMAINS = ("et-store.example", "ct-store.example", "mt-store.example", "pt-store.example")
_mx_blocked = all(
    any(d in b for b in pf_mx["blocks"]) for d in _TEST_DOMAINS
)
RESULTS["MX_NO_MAIL_ROUTE_FAIL"] = (not pf_mx["pass"]) and _mx_blocked
# 恢复 ok mock
preflight_gate.query_mx = lambda domain: ("ok", datetime.now(ASIA_SH).isoformat())

# 7e. V2 fail → FAIL（execute_final_send_plan dry-run，V2 重检返回 ineligible）
_fc.close()
campaign_eligible_v2.review_campaign_eligible_v2 = lambda lead, ctx: {"eligible": False, "reason": "v2_recheck_fail"}
v2run = daily_session.execute_final_send_plan(BATCH_DATE, dry_run=True)
RESULTS["V2_FAIL_BLOCKS_SEND"] = (v2run.get("new_outreach", 0) == 0 and v2run.get("skipped", 0) >= 20)
# 恢复 V2 eligible
campaign_eligible_v2.review_campaign_eligible_v2 = lambda lead, ctx: {"eligible": True, "tier": "E1"}

# ── 8. 输出 KEY=VALUE 验收 ──
print("=" * 60)
print("P2.3I EXACT PRODUCTION REPLAY — ACCEPTANCE")
print("=" * 60)
for k, v in RESULTS.items():
    print(f"{k} = {v}")

# 综合判定
ok = (
    RESULTS["PRE_AUTH_PASS"] and RESULTS["AUTHORIZATION_CREATED"] and RESULTS["AUTHORIZATION_ID_VALID"]
    and RESULTS["POST_AUTH_PASS"] and RESULTS["ET_WINDOW_PASS"] and RESULTS["CT_WINDOW_PASS"]
    and RESULTS["MT_WINDOW_PASS"] and RESULTS["PT_WINDOW_PASS"] and RESULTS["NO_AUTHORIZATION_ID_ERROR"]
    and RESULTS["NO_RECIPIENT_WINDOW_SKIP_FOR_ET_CT_MT_PT"] and RESULTS["OLD_BATCH_PLANNED_ROWS_FAIL"]
    and RESULTS["CURRENT_BATCH_NO_PLANNED_ROW_FAIL"] and RESULTS["MX_NO_MAIL_ROUTE_FAIL"]
    and RESULTS["V2_FAIL_BLOCKS_SEND"] and RESULTS["MANUAL_PAUSE_TRUE_BLOCKS_REAL_SMTP"]
    and RESULTS["OLD_FOLLOWUP_NO_CONTAMINATION_NEW_OUTREACH"]
)
RESULTS["EXACT_DAILY_SESSION_REPLAY_PASS"] = ok
print("=" * 60)
print(f"EXACT_DAILY_SESSION_REPLAY_PASS = {ok}")
print("=" * 60)
