# -*- coding: utf-8 -*-
"""
P2.3F — DNS freshness self-bootstrap regression test.

只读/无副作用测试：
- 使用临时 sqlite DB（不触碰生产 bd_leads.db）。
- 仅调用 preflight_gate.check_dns_freshness / run_preflight，绝不发生真实邮件。
- manual_pause 不受影响（本测试不读也不改它）。
- 真实 MX 路径（TEST_2/3/6/7/8）走真实 Worker（先 import env_loader 加载 token）。
- 受控路径（TEST_4/5）monkeypatch query_mx 强制返回指定状态。
"""
import os, sys, json, tempfile, sqlite3
from datetime import datetime, timedelta

# 把项目根目录加入 sys.path，使 env_loader / preflight_gate 可导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 必须先加载 .env 让 WORKER_AUTH_TOKEN 取到真实 token（与 Windows 生产一致）
import env_loader  # noqa: F401  (import 即执行 _load_env)
import preflight_gate as pg

ASIA_SH = pg.ASIA_SH

# ── 临时 DB ────────────────────────────────────────────────
tmp = tempfile.mkstemp(suffix=".db", prefix="p23f_")[1]
conn = sqlite3.connect(tmp)
conn.row_factory = sqlite3.Row
conn.execute("CREATE TABLE system_config (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)")
conn.execute("""CREATE TABLE final_send_plan (
    plan_id TEXT, lead_id INTEGER, recipient_email TEXT, status TEXT,
    outreach_batch_date TEXT, planned_sequence INTEGER)""")
conn.commit()

def reset(domain, cache_status=None, cache_age_h=None, batch="B"):
    conn.execute("DELETE FROM final_send_plan")
    conn.execute("DELETE FROM system_config WHERE key LIKE 'mx_cache_%'")
    conn.commit()
    conn.execute(
        "INSERT INTO final_send_plan (plan_id,lead_id,recipient_email,status,outreach_batch_date,planned_sequence) "
        "VALUES (?,?,?,?,?,?)",
        (batch + ":" + domain, 1, "store@" + domain, "planned", batch, 1))
    conn.commit()
    if cache_status is not None:
        ca = (datetime.now(ASIA_SH) - timedelta(hours=(cache_age_h or 0))).isoformat()
        conn.execute(
            "INSERT INTO system_config (key,value,updated_at) VALUES (?,?,?)",
            ("mx_cache_" + domain, json.dumps({"status": cache_status, "checked_at": ca}), ca))
        conn.commit()

# 非 DNS 检查桩（TEST_8 用，隔离 DNS self-bootstrap 验证）
def _pass_check(name):
    return {"name": name, "status": "pass", "detail": "test-stub"}
_stubs = {
    "check_hygiene": lambda c, rows: _pass_check("hygiene"),
    "check_duplicates": lambda c, rows: _pass_check("duplicates"),
    "check_template": lambda c, rows: _pass_check("template"),
    "check_snapshot_plan_hash": lambda c, sp, rows: _pass_check("snapshot"),
    "check_stale_objects": lambda c, b, n: _pass_check("stale_objects"),
    "check_timezones": lambda c, rows, n, send_window_override=False:
        {"check": _pass_check("timezones"), "timezone_blocks": []},
}
_orig = {k: getattr(pg, k) for k in _stubs}

results = []

def record(name, passed, detail):
    results.append((name, passed, detail))
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")

# 真实可投递域名（P2.3D2 已验证）
OK_DOMAIN = "fantasyfactory.com"
OK_DOMAIN2 = "hobby-hole.com"
BLOCK_DOMAIN = "falloutcomics.com"

# ── TEST_1: fresh cache + MX ok → PASS ─────────────────────
reset(OK_DOMAIN, cache_status="ok", cache_age_h=1)
res = pg.check_dns_freshness(conn, batch_id="B")
info = res.get(OK_DOMAIN, {})
record("TEST_1 fresh_cache_ok", (info.get("fresh") is True and info.get("stale") is False and info.get("mx_status") == "ok"),
       f"fresh={info.get('fresh')} stale={info.get('stale')} mx={info.get('mx_status')}")

# ── TEST_2: no cache + live MX ok → PASS IN SAME RUN ───────
reset(OK_DOMAIN, cache_status=None)
res = pg.check_dns_freshness(conn, batch_id="B")
info = res.get(OK_DOMAIN, {})
record("TEST_2 no_cache_live_ok", (info.get("fresh") is True and info.get("stale") is False and info.get("mx_status") == "ok"),
       f"fresh={info.get('fresh')} stale={info.get('stale')} mx={info.get('mx_status')} (live, single run)")

# ── TEST_3: stale >24h cache + live MX ok → PASS IN SAME RUN ─
reset(OK_DOMAIN, cache_status="ok", cache_age_h=25)
res = pg.check_dns_freshness(conn, batch_id="B")
info = res.get(OK_DOMAIN, {})
record("TEST_3 stale_cache_live_ok", (info.get("fresh") is True and info.get("stale") is False and info.get("mx_status") == "ok"),
       f"fresh={info.get('fresh')} stale={info.get('stale')} mx={info.get('mx_status')} (was >24h stale, live refresh pass in same run)")

# ── TEST_4: stale cache + live dns_error → FAIL CLOSED ─────
_orig_qmx = pg.query_mx
pg.query_mx = lambda d: ("dns_error", datetime.now(ASIA_SH).isoformat())
reset(OK_DOMAIN, cache_status="ok", cache_age_h=25)
res = pg.check_dns_freshness(conn, batch_id="B")
info = res.get(OK_DOMAIN, {})
record("TEST_4 stale_cache_live_dns_error", (info.get("fresh") is False and info.get("stale") is True and info.get("mx_status") == "dns_error"),
       f"fresh={info.get('fresh')} stale={info.get('stale')} mx={info.get('mx_status')} (FAIL CLOSED)")
pg.query_mx = _orig_qmx

# ── TEST_5: no cache + no_mail_route → FAIL CLOSED ─────────
pg.query_mx = lambda d: ("no_mail_route", datetime.now(ASIA_SH).isoformat())
reset("example.com", cache_status=None)
res = pg.check_dns_freshness(conn, batch_id="B")
info = res.get("example.com", {})
record("TEST_5 no_cache_no_mail_route", (info.get("fresh") is False and info.get("stale") is True and info.get("mx_status") == "no_mail_route"),
       f"fresh={info.get('fresh')} stale={info.get('stale')} mx={info.get('mx_status')} (FAIL CLOSED)")
pg.query_mx = _orig_qmx

# ── TEST_6: Fallout Comics (real) → no_mail_route / BLOCK ──
reset(BLOCK_DOMAIN, cache_status=None)
res = pg.check_dns_freshness(conn, batch_id="B")
info = res.get(BLOCK_DOMAIN, {})
record("TEST_6 falloutcomics_real", (info.get("fresh") is False and info.get("stale") is True and info.get("mx_status") == "no_mail_route"),
       f"fresh={info.get('fresh')} stale={info.get('stale')} mx={info.get('mx_status')} (real Worker, BLOCK)")

# ── TEST_7: known valid MX domain (real) → PASS ────────────
reset(OK_DOMAIN2, cache_status=None)
res = pg.check_dns_freshness(conn, batch_id="B")
info = res.get(OK_DOMAIN2, {})
record("TEST_7 valid_mx_domain_real", (info.get("fresh") is True and info.get("stale") is False and info.get("mx_status") == "ok"),
       f"fresh={info.get('fresh')} stale={info.get('stale')} mx={info.get('mx_status')} (real Worker, PASS)")

# ── TEST_8: run_preflight on valid planned batch, cold cache → FIRST run PASS ──
for k, fn in _stubs.items():
    setattr(pg, k, fn)
reset(OK_DOMAIN, cache_status=None, batch="B8")
pf = pg.run_preflight(conn, "B8", require_dns=True, persist_cache=True, include_auth_entries=False)
dns_check = next((c for c in pf["checks"] if c["name"] == "dns_freshness"), None)
dns_pass = bool(dns_check and dns_check["status"] == "pass")
first_run_ok = dns_pass and pf.get("smtp_blocked") is False
record("TEST_8 run_preflight_cold_cache_first_run", first_run_ok,
       f"dns_freshness.status={dns_check['status'] if dns_check else 'NONE'} smtp_blocked={pf.get('smtp_blocked')} (no 2nd run needed)")
for k, fn in _orig.items():
    setattr(pg, k, fn)

# ── 汇总 ───────────────────────────────────────────────────
passed = sum(1 for _, p, _ in results if p)
total = len(results)
all_pass = (passed == total)

# 关键指标（来自实时测试运行）
COLD = any("TEST_2" in n or "TEST_3" in n for n, _, _ in results)
STALE = any("TEST_3" in n for n, _, _ in results)
print("\n=== SUMMARY ===")
print(f"REGRESSION_PASS = {all_pass} ({passed}/{total})")

conn.close()
try:
    os.remove(tmp)
except OSError:
    pass  # 临时文件被 mkstemp 句柄占用时跳过清理，不影响测试结果

# 退出码：全过=0，否则=1（供 CI/调度判定）
sys.exit(0 if all_pass else 1)
