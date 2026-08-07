# Repository Consolidation Audit — Roktandrazo Outreach

**审计类型**: 只读全量分类审计（未修改任何代码、未运行任何发送）
**项目路径**: `C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\`
**审计时间**: 2026-08-07
**输出**: 本文件 `output/repository_consolidation_audit.md` + `output/repository_consolidation_audit.json`

---

## 1. 扫描范围与目录情况

### 1.1 文件总量统计

| 范围 | py 文件数 | 说明 |
|---|---|---|
| 根目录 `*.py` | **137** | 全部逐一分类 |
| `tests/` | 16 | 全部为 C.TEST_ONLY |
| `discovery/`（含 providers/） | 11 | 10 个 A（生产发现链），`mock_provider.py` 为 C |
| `facebook_enrichment/` | 4 | 全部 B（辅助富集） |
| `email_engagement/` | 5 | provider 体系；2 个 B、1 个 D(disabled)、1 个 E(POC) |
| `workbuddy_candidate_modules/` | 12 | 列出不深读；3 个 A（生产引用）、3 个 B、1 个 E、5 个 C |
| `follow_up_test/` | 1 | B（候选副本，与 candidate 版本有差异） |
| `migrations/` | 2 | 记录但不分类为生产（MIGRATION） |
| `_archived_scripts/` | 1 | E（危险手工发送脚本，已归档） |
| `backup/` | 1 | E（备份，不分类为生产） |
| **本次分类小计** | **190** | 188 个 A–F + 2 个 MIGRATION |
| `backups/` | 11 | 记录不分类（历史备份） |
| `data/production_acceptance_backup_20260727/code/` | 141 | 记录不分类（全量代码快照备份） |
| `cloudflare/` | JS/SQL | 记录存在（`src/index.js` 为 tracking worker、`schema.sql`、`wrangler.toml`），不分类 |
| **仓库 py 总计** | **343** | 含备份/快照 |

### 1.2 非 py 脚本文件（列出）

| 文件 | 用途 |
|---|---|
| `install_windows_tasks.ps1` | 生产调度安装脚本（5 个 bd_orchestrator 计划任务） |
| `inventory_recovery_runner.ps1` | 库存恢复 runner |
| `_elevated_install.bat` | BD Execution Host 服务安装脚本 |
| `_elevate_install.vbs` / `_elevated_install.vbs` | 提权安装辅助 |
| `install_bd_execution_host_admin.cmd` | 执行主机安装 |
| `start_bd_delivery_guard.cmd` / `stop_bd_delivery_guard.cmd` / `status_bd_delivery_guard.cmd` | 守卫启停查 |
| `start_bd_ops_center.cmd` / `stop_bd_ops_center.cmd` | Ops Center 启停 |
| `restore_original_power_settings.cmd` | 电源设置还原 |
| `run_modern_standby_test.cmd` | 测试辅助 |

---

## 2. 分类总览

| 分类 | 含义 | 数量 |
|---|---|---|
| **A** ACTIVE_PRODUCTION | 当前正式生产模块（被生产调用链引用） | **38** |
| **B** SUPPORTING | 生产辅助（无 SMTP 权限，被上层调用） | **45** |
| **C** TEST_ONLY | 仅用于测试 | **26** |
| **D** LEGACY_DISABLED | 旧实现不允许生产用 | **30** |
| **E** ARCHIVE | 历史/一次性/日期脚本/归档 | **49** |
| **F** UNKNOWN | 无法确认用途 | **0** |
| （MIGRATION） | 迁移脚本，记录不分类 | 2 |
| **合计** | | **190** |

---

## 3. 分类明细表

### 3.1 A. ACTIVE_PRODUCTION（38）

| 文件 | SMTP | send_one | FSP写 | send_log写 | 心跳 | 备注 |
|---|---|---|---|---|---|---|
| bd_orchestrator.py | 0 | 0 | 0 | 0 | 0 | **生产调度入口**（计划任务 5 阶段 + Execution Host） |
| daily_session.py | 0 | 2 | 0 | 1 | 0 | execute_final_send_plan 消费 FSP |
| bd_sender.py | **3** | 0 | 0 | 0 | 0 | **唯一生产 SMTP 模块**；定义 send_one / create_send_authorization |
| bd_template.py | 0 | 0 | 0 | 0 | 0 | 模板/渲染引擎 |
| bd_db.py | 0 | 0 | 0 | 1 | 0 | 生产 DB 层；log_send 写 send_log |
| bd_delivery_guard.py | 0 | 0 | 0 | 0 | 0 | 防休眠守卫（执行主机启动） |
| bd_execution_host_service.py | 0 | 0 | 0 | 0 | 1 | Windows 服务；调度 poller/review/guard/orchestrator |
| bd_ops_poller.py | 0 | 0 | 0 | 0 | **2** | 心跳主写者（bd_ops_poller_status.json） |
| bd_review_server.py | 0 | 0 | 0 | 0 | 1 | Ops Center :8765 |
| bd_ops_api.py | 0 | 0 | 0 | 0 | 1 | 只读运维 API |
| preflight_gate.py | 0 | 0 | 0 | 0 | 1 | P0 只读门禁 |
| bounce_pipeline.py | 0 | 0 | 0 | 0 | **2** | 退信扫描；更新心跳 jobs.bounce |
| post_send_reconciliation.py | 0 | 0 | 0 | 0 | 0 | FSP/auth/send_log 三方对账 |
| recipient_scheduler.py | 0 | 0 | 0 | 0 | 0 | 收件人当地时间窗口 |
| timezone_resolver.py | 0 | 0 | 0 | 0 | 0 | 时区解析（当前仅 tests 引用；任务列为 A） |
| email_hygiene.py | 0 | 0 | 0 | 0 | 0 | 邮箱校验（当前无生产 import；任务列为 A） |
| final_send_plan.py | 0 | 0 | **1** | 0 | 0 | create_plan 生产写 FSP |
| outreach_control.py | 0 | 0 | 0 | 0 | 0 | 纯控制常量，被 orchestrator/FSP 引用 |
| history_crosscheck.py | 0 | 0 | 0 | 0 | 0 | 身份/投递查重，被 bd_db/review_server 引用 |
| env_loader.py | 0 | 0 | 0 | 0 | 0 | SMTP/IMAP 配置，被 bd_sender/bounce 引用 |
| agent_reply_monitor.py | 0 | 0 | 0 | 0 | 0 | IMAP 扫描，被 orchestrator post-send/EOD 调用 |
| result_recovery_sync.py | 0 | 0 | 0 | 0 | 0 | 08:45 结果同步入口（automation） |
| lead_hygiene_gate.py | 0 | 0 | 0 | 0 | 0 | A0 门禁，被 orchestrator pre_send 调用 |
| production_adapter.py | 0 | 0 | 0 | 0 | 0 | 门禁上下文适配，被 orchestrator pre_send 调用 |
| _start_poller_inline.py | 0 | 0 | 0 | 0 | 0 | 安装时生成，启动 poller 的生产引导 |
| discovery/__init__.py | 0 | 0 | 0 | 0 | 0 | 生产发现包 |
| discovery/discovery_service.py | 0 | 0 | 0 | 0 | 0 | 被 orchestrator inventory 调用 |
| discovery/models.py | 0 | 0 | 0 | 0 | 0 | 发现模型 |
| discovery/normalizer.py | 0 | 0 | 0 | 0 | 0 | 标准化 |
| discovery/providers/__init__.py | 0 | 0 | 0 | 0 | 0 | provider 包 |
| discovery/providers/base.py | 0 | 0 | 0 | 0 | 0 | provider 基类 |
| discovery/providers/browser_maps.py | 0 | 0 | 0 | 0 | 0 | Maps 浏览器 provider |
| discovery/providers/browser_maps_scraper.py | 0 | 0 | 0 | 0 | 0 | 抓取器 |
| discovery/providers/google_places.py | 0 | 0 | 0 | 0 | 0 | Google Places provider |
| discovery/providers/serpapi_maps.py | 0 | 0 | 0 | 0 | 0 | SerpAPI provider |
| workbuddy_candidate_modules/follow_up_queue_builder.py | 0 | 0 | 0 | 0 | 0 | 被 orchestrator pre_send 调用 |
| workbuddy_candidate_modules/lead_hygiene_gate.py | 0 | 0 | 0 | 0 | 0 | 根目录门禁副本 |
| workbuddy_candidate_modules/production_adapter.py | 0 | 0 | 0 | 0 | 0 | 根目录适配副本 |

### 3.2 B. SUPPORTING（45）

| 文件 | 说明 |
|---|---|
| bd_dashboard_v3.2.py | Dashboard 生成器（无 SMTP，读 poller 心跳/对账） |
| bd_operations_dashboard.py | Dashboard v2，被 orchestrator post-send 调用 |
| dashboard.py | Dashboard，被 orchestrator EOD 调用 |
| bd_review_cli.py / bd_status_cli.py | 运维 CLI |
| manual_email_workflow.py | 人工邮件提交（无 SMTP 权限），被 review_server 调用 |
| review_workflow.py | 评审动作应用，被 review_server 调用 |
| retail_city_queue.py | 城市队列，被 orchestrator inventory 调用 |
| inventory_monitor_executor.py | 库存监控执行引擎，被 orchestrator inventory 调用 |
| inventory_recovery_loop.py / inventory_recovery_daemon.py / inventory_expansion_runner.py / unified_inventory.py | 库存辅助 |
| daily_results_0900.py | 09:00 只读日报（automation 入口） |
| agent_daily_report.py / gen_visual_report.py | 报告生成 |
| email_tracking_server.py | 本地一手方 tracking HTTP 服务器（cloudflare 的本地替代） |
| coverage_registry.py | 搜索覆盖登记 |
| collection_pipeline.py | 采集流水线（automation 记忆确认仍用于补库） |
| city_selector.py / city_selector_v2.py / search_engine.py / website_verifier.py / contact_extractor.py / scorer.py / scorer_v2.py | 采集栈库 |
| new_lead_factory.py | Lead Factory 批量入库（automation 确认使用） |
| brand_candidate_importer.py / b_pool_import.py / legacy_lead_insert_guard.py | 数据导入辅助 |
| fb_worker.py / fb_fallback_recovery.py | FB 富集辅助 |
| configure_bios_power.py / verify_bios_closure.py | 运维电源配置（无 SMTP） |
| email_engagement/__init__.py / provider.py / local_first_party_provider.py | tracking provider 体系 |
| facebook_enrichment/fb_enrich.py / fb_batch_runner.py / fb_rate_limiter.py / b_pool_recovery_runner.py | FB 富集工具 |
| workbuddy_candidate_modules/b_pool_enrichment.py / inbox_polling_monitor.py / shadow_mode.py | 候选模块（未深读） |
| follow_up_test/inbox_polling_monitor.py | 候选副本 |

### 3.3 C. TEST_ONLY（26）

- `tests/` 全部 16 个：`__init__.py`, `test_bounce_pipeline.py`, `test_city_outreach_40.py`, `test_compact_renderer.py`, `test_dashboard_metrics.py`, `test_dashboard_timezone.py`, `test_discovery_service.py`, `test_email_tracking.py`, `test_manual_email_workflow.py`, `test_p0_runtime_semantics.py`, `test_post_send_reconciliation.py`, `test_preflight_gate.py`, `test_recipient_scheduler.py`, `test_result_sync.py`, `test_review_workflow.py`, `test_timezone_resolver.py`
- 根目录：`test_45min_delivery_guard.py`, `test_browser_maps_integration.py`, `test_unattended_delivery_v2.py`, `modern_standby_guard_test.py`
- 候选模块：`test_b_pool_enrichment.py`, `test_hygiene_gate_production.py`, `test_lead_hygiene_gate.py`, `test_positive_samples.py`, `test_production_adapter.py`
- 发现 mock：`discovery/providers/mock_provider.py`

### 3.4 D. LEGACY_DISABLED（30）

| 文件 | 危险标记 |
|---|---|
| sender.py | **含 smtplib/SMTP/sendmail（旧 SMTP 发送器），P0 硬禁用（LegacySMTPDisabledError）** |
| send_phase2.py / send_phase3.py | import send_one，P0 硬禁用 |
| auto_replenish_loop.py | import send_one，P0 硬禁用 |
| pipeline.py / main.py / drafter.py | 旧 pipeline（drafter+sender 栈） |
| outreach_templates.py | 旧模板系统 |
| pipeline_orchestrator.py | 旧 agent 编排器 |
| bd_main.py | import send_one/batch_send（旧入口） |
| daily_operator_auto.py | 旧每日编排器（无禁用块，但已被 bd_orchestrator 取代；仍 import bd_sender._create_connection，**具 SMTP 能力，勿运行**） |
| auto_collector.py | 旧独立采集器 |
| db.py / config.py / phase1_db.py | 旧 DB/配置层 |
| bounce_audit.py / bounce_deep.py / bounce_diag.py / update_bounce_db.py | 旧退信工具（被 bounce_pipeline 取代） |
| agent_sender.py / agent_email_verifier.py / agent_bounce_auditor.py / agent_lead_collector.py / agent_supervisor.py | 旧 agent 体系 |
| broad_outreach_gate.py | 旧广撒门禁（仅被 _ 归档脚本引用） |
| fast_lead_discovery.py | 旧 B2 发现 |
| dryrun_phase2.py / dryrun_phase3.py | 旧 phase dry-run |
| browser_verifier.py | 仅旧编排引用 |
| email_engagement/disabled_provider.py | 被禁 provider |

### 3.5 E. ARCHIVE（49）

**危险发送入口（特别标记，详见 §4）**：
- `_send_tonight_20260805.py` — **SEND_LIVE=True（全库唯一）**，send_one + create_send_authorization + FSP 直写
- `_send_2300_tn_ar_ky.py` — send_one + create_send_authorization + FSP/send_log 直写
- `_run_901_games_delayed_pilot_once.py` — pilot 发送（send_one + send_log）
- `_prepare_tonight.py` — FSP 直写 + create_send_authorization
- `_pre_send_plan_tonight.py` / `_pre_send_plan_20260806.py` — FSP 直写
- `_archived_scripts/_manual_send_60.py` — send_one + send_log + FSP 更新
- `_tri_state_send_now.py.ARCHIVED_20260803`（扩展名非 .py，已归档的发送脚本）

**日期/一次性脚本**：
`_daily_report_20260806.py`, `_inventory_recovery_20260806.py`, `_preflight_20260804.py`, `_preflight_20260805.py`, `_preflight_tonight.py`, `_preflight_check.py`, `_catchup_calculate.py`, `_run_broad_analysis.py`, `_daily_collection_report.py`, `_daily_readonly_report.py`, `_inventory_report_gen.py`, `_import_nashville_master.py`, `_nashville_clean_import_v2.py`, `_safe_import.py`, `_simple_check.py`, `_test_nashville.py`, `_bak.py`

**一次性导入/扩容/对账**：
`import_new_leads.py`, `import_pilot.py`, `import_phase2.py`, `import_phase3.py`, `import_phase4.py`, `import_phase4_b2.py`, `import_phase4_b3.py`, `import_phase4_b4.py`, `scale_brand_insert.py`, `scale_to_30.py`, `push_to_30.py`, `recovery_replay.py`, `reconcile_a0.py`, `render_dryrun_eml.py`, `final_audit.py`, `pool_analysis.py`, `website_audit.py`, `b_pool_audit_v2.py`, `lead_audit_cleanup.py`, `export_backup.py`, `db_migration_v2.py`, `install_service_elevate.py`

**备份/实验**：
`backup/bd_template_v4_backup_20260706.py`, `email_engagement/plunk_poc_provider.py`, `workbuddy_candidate_modules/dry_run_all.py`

### 3.6 F. UNKNOWN（0）

无未分类文件。

---

## 4. 危险特征汇总

### 4.1 SEND_LIVE=True（1 处）

| 文件 | 行 | 说明 |
|---|---|---|
| `_send_tonight_20260805.py` | 17 | **全库唯一 SEND_LIVE=True**；属 E.ARCHIVE 危险发送入口，禁止直接运行 |

### 4.2 SMTP 能力（2 个文件）

| 文件 | import smtplib | SMTP_SSL(/SMTP( | sendmail( | 分类 |
|---|---|---|---|---|
| `bd_sender.py` | L13 | L252 | L426, L445 | **A（生产唯一 SMTP 通道）** |
| `sender.py` | L12 | L91 | L96 | **D（P0 硬禁用）** |

（备份副本：`backups/p0_patch1_legacy_live_disable_20260710_1053/sender.py`、`backups/message_id_fix_20260707_1155/bd_sender.py`、`data/production_acceptance_backup_20260727/code/...` 等，均非当前代码。）

### 4.3 bd_sender.send_one 调用点（按文件+行）

| 文件 | 行 | 分类 | 说明 |
|---|---|---|---|
| daily_session.py | 102 | A | 生产 dry-run 路径 |
| daily_session.py | 345 | A | **生产 live 发送路径** |
| bd_sender.py | 530 | A | batch_send 内部转发 |
| _send_tonight_20260805.py | 248 | E | 危险（SEND_LIVE=True） |
| _send_2300_tn_ar_ky.py | 145 | E | 危险 |
| _run_901_games_delayed_pilot_once.py | 351 | E | 危险 pilot |
| _archived_scripts/_manual_send_60.py | 74 | E | 危险（已归档） |
| send_phase2.py | 94 | D | 硬禁用 |
| send_phase3.py | 146 | D | 硬禁用 |
| bd_main.py | 143 | D | 旧入口 |
| auto_replenish_loop.py | 206 | D | 硬禁用 |

### 4.4 create_send_authorization 调用点

| 文件 | 行 | 分类 |
|---|---|---|
| _prepare_tonight.py | 115 | E（危险） |
| _send_2300_tn_ar_ky.py | 117 | E（危险） |
| _send_tonight_20260805.py | 193 | E（危险，SEND_LIVE=True） |

### 4.5 直接写 final_send_plan（INSERT）

| 文件 | 行 | 分类 |
|---|---|---|
| final_send_plan.py | 61 | **A（生产 create_plan，合法）** |
| _prepare_tonight.py | 98 | E（危险） |
| _pre_send_plan_tonight.py | 304 | E（危险） |
| _pre_send_plan_20260806.py | 304 | E（危险） |
| _send_tonight_20260805.py | 167 | E（危险） |
| _send_2300_tn_ar_ky.py | 95 | E（危险） |

### 4.6 直接写 send_log（INSERT / INSERT OR IGNORE）

| 文件 | 行 | 分类 |
|---|---|---|
| bd_db.py | 407 | **A（生产 log_send，合法）** |
| daily_session.py | 133 | **A（生产，合法）** |
| _archived_scripts/_manual_send_60.py | 86 | E（危险） |
| _run_901_games_delayed_pilot_once.py | 225 | E（危险） |
| _send_2300_tn_ar_ky.py | 170 | E（危险，INSERT OR IGNORE） |

### 4.7 心跳 bd_ops_poller_status.json（写入方）

| 文件 | 行 | 说明 |
|---|---|---|
| bd_ops_poller.py | 49 | **生产主写者**（A） |
| bounce_pipeline.py | 664 | 更新 jobs.bounce（A） |
| bd_execution_host_service.py | 66 | 心跳路径定义/监控（A） |

（`bd_dashboard_v3.2.py`/`bd_ops_api.py`/`bd_review_server.py`/`preflight_gate.py` 及 `_preflight_*.py` 为读取方，不计写入。）

### 4.8 日期型/危险命名脚本（date_scripts，共 31 个）

根目录匹配 `_20\d{6}`、`_send_`、`_preflight_`、`_prepare_`、`catchup`、`pilot`、`phase`：
`_daily_report_20260806.py`, `_inventory_recovery_20260806.py`, `_pre_send_plan_20260806.py`, `_preflight_20260804.py`, `_preflight_20260805.py`, `_send_tonight_20260805.py`, `_pre_send_plan_tonight.py`, `_preflight_tonight.py`, `_preflight_check.py`, `_prepare_tonight.py`, `_send_2300_tn_ar_ky.py`, `_catchup_calculate.py`, `_run_901_games_delayed_pilot_once.py`, `_archived_scripts/_manual_send_60.py`, `backup/bd_template_v4_backup_20260706.py`, `send_phase2.py`, `send_phase3.py`, `import_pilot.py`, `import_phase2.py`, `import_phase3.py`, `import_phase4.py`, `import_phase4_b2.py`, `import_phase4_b3.py`, `import_phase4_b4.py`, `dryrun_phase2.py`, `dryrun_phase3.py`, `phase1_db.py`, `pipeline.py`, `pipeline_orchestrator.py`, `post_send_reconciliation.py`, `final_send_plan.py`
另：`_tri_state_send_now.py.ARCHIVED_20260803`（非 .py 扩展，已归档危险发送）。

---

## 5. 唯一生产调用链初步推断

### 5.1 调度来源（证据）

1. **Windows 计划任务**（`install_windows_tasks.ps1`）——5 个任务全部指向：
   `bd_orchestrator.py --stage <inventory|pre-send|outreach|post-send|end-of-day> --live`
2. **Windows 服务 BDExecutionHost**（`_elevated_install.bat` / `bd_execution_host_service.py`）——
   持续拉起/守护：`bd_ops_poller.py`（线程）、`bd_delivery_guard.py`、`bd_review_server.py`、并按小时表调用 `bd_orchestrator.py`。
3. **WorkBuddy automations**（`.workbuddy/automations/*/memory.md`）——确认的入口：
   `result_recovery_sync.py`（08:45）、`daily_results_0900.py`（09:00）、`bounce_pipeline.py --once`。

### 5.2 生产调用链（A 集合，唯一）

```
[Windows 计划任务 15:00/22:30/23:00/00:10/00:25]
   └─> bd_orchestrator.py ─┬─> bd_db.py ─> history_crosscheck.py
                           ├─> outreach_control.py
                           ├─> bd_template.py
                           ├─> final_send_plan.py ─> outreach_control.py
                           ├─> lead_hygiene_gate.py / production_adapter.py
                           ├─> workbuddy_candidate_modules.follow_up_queue_builder.py
                           ├─> daily_session.py ──> final_send_plan.py
                           │                     └─> bd_sender.py ─> bd_db.py / env_loader.py / bd_template.py
                           │                          └─ SMTP_SSL + sendmail（唯一 SMTP 出口）
                           ├─> agent_reply_monitor.py（IMAP）
                           ├─> bd_operations_dashboard.py / dashboard.py
                           ├─> retail_city_queue.py
                           ├─> discovery.discovery_service.py（providers/*）
                           ├─> inventory_monitor_executor.py
                           └─> manual_email_workflow.py（候选入库/人工邮件）

[BDExecutionHost 服务]
   └─> bd_ops_poller.py（写心跳 bd_ops_poller_status.json）─> 拉起 bd_delivery_guard.py
   └─> bd_review_server.py ─> review_workflow.py / history_crosscheck.py / manual_email_workflow.py / bd_ops_api.py / bd_ops_poller.py

[WorkBuddy automations]
   └─> result_recovery_sync.py ─> bounce_pipeline.py（退信扫描，更新心跳）
   └─> daily_results_0900.py（只读日报）

[独立生产模块]（任务列 A；当前无 import 引用，以 CLI/库方式使用或待接线）
   post_send_reconciliation.py / preflight_gate.py / recipient_scheduler.py / timezone_resolver.py / email_hygiene.py / bounce_pipeline.py
```

### 5.3 关键结论

- **生产唯一 SMTP 出口 = `bd_sender.py`**（仅它含 `import smtplib` + `SMTP_SSL` + `sendmail`，且为 A）。
- **生产唯一 FSP 写入 = `final_send_plan.create_plan()`**（经 `bd_orchestrator --stage pre-send` 触发）；唯一 send_log 生产写入 = `bd_db.log_send()`（经 `daily_session` live 路径）。
- **心跳唯一主写者 = `bd_ops_poller.py`**；`bounce_pipeline.py` 更新其 `jobs.bounce` 子项。
- **`timezone_resolver.py` 与 `email_hygiene.py` 当前未发现生产 import 引用（仅 tests）**，按任务要求列 A，但建议在合并时确认其被 CLI/子进程使用的实际情况。
- **`daily_operator_auto.py` 是最危险的非生产脚本**：无 P0 禁用块，仍可 `import bd_sender._create_connection` 建立 SMTP 连接，且不是当前调度目标——合并时必须降级/删除。

---

## 6. 合并建议（仅提示，未改动）

1. **E 类危险发送入口一律不进生产包**：`_send_tonight_20260805.py`（SEND_LIVE=True）、`_send_2300_tn_ar_ky.py`、`_run_901_games_delayed_pilot_once.py`、`_prepare_tonight.py`、`_pre_send_plan_*.py`、`_archived_scripts/_manual_send_60.py`。
2. **D 类保留但禁止 import**：`sender.py`/`send_phase2/3`/`auto_replenish_loop.py` 已有硬禁用；`daily_operator_auto.py` 建议补禁用块或删除。
3. **A 类 38 个为生产核心**，全部保留；`timezone_resolver`/`email_hygiene` 若确认无生产引用可降为 B 或归档。
4. `backups/`（11）与 `data/production_acceptance_backup_20260727/`（141）为历史快照，不纳入合并。
