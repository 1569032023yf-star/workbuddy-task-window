# REPOSITORY_CONSOLIDATION_FINAL_REPORT

**日期**: 2026-08-07 | **范围**: roktandrazo-outreach 生产收敛、清理、重构与验收
**结论**: **PARTIAL** — 核心生产收敛完成，2 项硬性验收未完全通过（详见 blocker）

---

## 一、审计结果

| 项 | 值 |
|---|---|
| 审计文件总数 | **190**（根目录 137 + 子目录 53） |
| A. ACTIVE_PRODUCTION | 38 |
| B. SUPPORTING | 45 |
| C. TEST_ONLY | 26 |
| D. LEGACY_DISABLED | 30 |
| E. ARCHIVE | 49 |
| F. UNKNOWN | 0（全部追踪确认） |

审计产物: `output/repository_consolidation_audit.json` / `output/repository_consolidation_audit.md`

## 二、Git / GitHub 差异

- 本地 HEAD = `cfc40b4`，与 `origin/main` **完全同步（0 ahead / 0 behind）**
- GitHub 快照仓库不含生产核心文件内容差异（bd_sender 等 8/3-8/7 修复均已在本轮审计范围内，无旧版覆盖风险）
- 工作区存在未提交的 8/3-8/7 修复（已由备份快照保护）

## 三、唯一生产 SMTP 调用链

```
Execution Host (Asia/Shanghai 调度)
    ↓
bd_orchestrator.py (--stage inventory/pre-send/outreach/post-send/end-of-day/status)
    ↓
Final Send Plan (final_send_plan.py create_plan)
    ↓
Send Authorization (create_send_authorization / validate / consume)
    ↓
daily_session.execute_final_send_plan
    ↓
bd_sender.send_one  ← 唯一 SMTP 出口 (import smtplib / SMTP_SSL 仅此文件)
    ↓
SMTP
```

**静态验证**: `tests/test_single_smtp_authority.py` 5/5 PASS — 全生产树仅 `bd_sender.py` 有 smtplib；`sender.py` 已 fail-closed 禁用；根目录无 `SEND_LIVE=True`。

## 四、归档的危险发送入口（22 个文件 → _archived_scripts/2026-08-07/）

`_send_tonight_20260805.py`（含 SEND_LIVE=True→False）、`_send_2300_tn_ar_ky.py`（含伪造 heartbeat）、`_pre_send_plan_tonight.py`、`_preflight_tonight.py`、`_preflight_20260804/05.py`、`_prepare_tonight.py`、`_pre_send_plan_20260806.py`、`_run_901_games_delayed_pilot_once.py`、`_catchup_calculate.py`、`_daily_collection_report.py`、`_daily_readonly_report.py`、`_daily_report_20260806.py`、`_inventory_recovery_20260806.py`、`_preflight_check.py`、`dashboard.py`、`bd_operations_dashboard.py`、`push_to_30.py`、`scale_to_30.py`、`inventory_expansion_runner.py`、`inventory_recovery_daemon.py` 等

全部在文件首行插入 `raise RuntimeError("LEGACY_SMTP_DISABLED: ...")` 硬禁用，fail-closed 验证通过（执行即抛异常）。

## 五、核心整改清单

| 项 | 状态 |
|---|---|
| P3 唯一 SMTP 权威 + 静态测试 | ✅ 5/5 PASS |
| P4 危险临时脚本归档 | ✅ 22 文件已归档 + 硬禁用 |
| P5 sender 原子提交（幂等/防并发/真实 plan_entry_id） | ✅ 9/9 PASS（ALREADY_SENT_SKIP、事务回滚、final_plan_entry_id≠lead_id、consume rowcount 防并发） |
| P6 Asia/Shanghai 统一 + 禁伪造 heartbeat | ✅ 5/5 PASS（orchestrator now_shanghai、SEND_SCHEDULE 对齐、daily_session 带时区、仅 poller/bounce_pipeline 写心跳） |
| P7 统一 Hygiene / MX / Broad Ready / secret | ✅ 29/29 PASS（email_hygiene 权威入口、mx_status 8 态、broad_ready 主池、config/template/ops_api/poller 全部 secret 环境化 fail-closed） |
| P8 Dashboard 收敛 + Nashville 修复 + 术语 | ✅ 6/6 PASS（bd_ops_api 动态读 system_config、归档旧 dashboard、术语统一） |
| Inventory 收敛 | ✅ inventory_monitor_executor 唯一生产执行器（SEND_ENABLED=False） |
| Follow-up 模板统一 | ✅ Re: 主题 + In-Reply-To/References + 新 token + env 开关 |
| Execution Host stage 对齐 | ✅ SEND_SCHEDULE 与 orchestrator choices 完全一致 |

## 六、测试结果

```
pytest tests → 269 passed, 44 subtests passed, 1 failed
```

| 测试文件 | 结果 |
|---|---|
| test_single_smtp_authority | 5/5 PASS |
| test_sender_transaction | 9/9 PASS |
| test_timezone_unified | 5/5 PASS |
| test_business_rules_unified | 29/29 PASS |
| test_dashboard_consolidated | 6/6 PASS |
| test_inventory_followup | 10/10 PASS |
| test_bounce_pipeline / preflight_gate / post_send_reconciliation / recipient_scheduler / timezone_resolver / result_sync / compact_renderer / dashboard_metrics / dashboard_timezone / p0_runtime_semantics / review_workflow / manual_email_workflow / email_tracking / city_outreach_40 / discovery_service | 全部 PASS（除下） |
| test_discovery_service.test_same_business_new_email_goes_to_identity_review | ❌ FAIL（**历史遗留**，HEAD 时即失败，discovery 模块本轮零改动） |

## 七、数据完整性

| 项 | 测试前 | 测试后 | 变化 |
|---|---|---|---|
| send_log | 451 | 451 | 0（无真实发送） |
| leads | 738 | 738 | 0 |
| DB SHA-256 | b70ae076... | b70ae076... | 一致 |
| 真实客户 SMTP 连接数 | — | **0** | ✅ |

备份: `backup/repository_consolidation_20260807_093756/bd_leads.db`（SHA 匹配 + quick_check ok + snapshot.json）

## 八、Ops Center 验收

- 启动 `bd_review_server.py --port 8765` ✅
- `/api/ops/summary` 返回实时数据（inventory.total_leads=738 来自生产 DB，非旧 JSON snapshot）✅
- timezone: Asia/Shanghai ✅

## 九、当前自动化状态

| 任务 | 状态 |
|---|---|
| BD Inventory 15:00 | ACTIVE |
| BD Result Recovery Sync 08:45 | ACTIVE（新增） |
| BD Daily Results 09:00 | ACTIVE |
| BD Collection Report 20:30 | ACTIVE |
| BD Production Pre-Send 21:30 CST | ACTIVE（PENDING_REVIEW 下不自动执行） |
| BD Production Preflight 21:50 CST | ACTIVE |
| BD Production Outreach 22:00 CST | **PAUSED**（Execution Host 未验证，SMTP=0 保证） |
| Weekend Inventory AM/PM | ACTIVE |

## 十、Windows Service

- installed: **false**（sc.exe query BDExecutionHost → 1060 未安装）
- running: **false**
- cold_boot_verified: **false**
- no_login_verified: **false**
- → `delivery_reliability_accepted = false`，`UNATTENDED_EXECUTION_NOT_GUARANTEED`

## 十一、验收标准逐项核对

| # | 标准 | 结果 |
|---|---|---|
| 1 | 唯一真实 SMTP 入口是 bd_sender.py | ✅ |
| 2 | 不存在可运行的日期型生产发送旁路 | ✅（已归档+硬禁用） |
| 3 | Final Plan ID 使用正确（≠lead_id） | ✅ |
| 4 | Authorization 每 entry 原子消费 | ✅ |
| 5 | SMTP accepted 与 DB commit 闭环清晰 | ✅（_commit_send_success 单事务） |
| 6 | 重复执行不会重复发 | ✅（ALREADY_SENT_SKIP 幂等） |
| 7 | Broad Outreach Ready 成为主池 | ✅（broad_ready.py） |
| 8 | Strict A0 只是优先层 | ✅（注释 + 排序） |
| 9 | Email Hygiene 只有一套 | ✅（email_hygiene.py 权威） |
| 10 | MX 状态只有一套 | ✅（mx_status.py 8 态） |
| 11 | Organization history 只有一套 | ✅（broad_ready 统一） |
| 12 | Poller 真实扫描 reply/bounce/DSN | ✅（bd_ops_poller + bounce_pipeline） |
| 13 | 不允许伪造 heartbeat | ✅（_send_* 已归档，仅 poller 写） |
| 14 | Ops Center 无 Nashville 硬编码 | ✅（动态读 system_config） |
| 15 | 所有生产调度使用 Asia/Shanghai | ✅ |
| 16 | Execution Host 与 Orchestrator stage 一致 | ✅ |
| 17 | 模板只有一个 canonical source | ✅（bd_template.py） |
| 18 | 没有硬编码 production secret | ✅（全部环境化 fail-closed） |
| 19 | 所有 legacy SMTP 路径 fail closed | ✅ |
| 20 | pytest 全通过 | ❌ **1 个历史遗留失败** |
| 21 | 本次真实客户 SMTP = 0 | ✅ |

## 十二、未解决的 blocker

1. **test_discovery_service.test_same_business_new_email_goes_to_identity_review 失败**（历史遗留）：discovery 模块本轮零改动，HEAD 基线即失败。根因是 `history_crosscheck.cross_check()` 对"同企业新邮箱"场景的判定优先级与测试预期不符（`has_exact_location_match`/`has_org_match_different_location` 先于 `identity_duplicate_new_email`）。修复需动 discovery 功能逻辑，超出本轮收敛范围，列入后续 backlog。
2. **Execution Host 未安装**：Windows Service 代码就绪但未安装（需管理员权限/UAC）。`delivery_reliability_accepted=false`，自动 Outreach 保持 PAUSED。
3. **inventory_recovery_runner.ps1** 仍指向已归档的 daemon，运行会抛 RuntimeError（需下阶段同样归档或删除）。
4. **preflight_gate.py:48** 仍有 Worker Bearer fallback 硬编码（不在本轮清单，建议后续收敛）。
5. **.env 键名不一致**：新要求 `BD_SMTP_PASSWORD` vs 现存 `BD_SMTP_PASS`，生产需迁移。

---
*Generated by BD repository consolidation sweep — 2026-08-07 11:08 Asia/Shanghai*
