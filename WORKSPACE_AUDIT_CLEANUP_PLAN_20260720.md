# 工作空间审计清理方案 / Workspace Audit & Cleanup Plan

**日期 / Date**: 2026-07-20 11:00 Asia/Shanghai
**扫描范围**: `C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\` 全部内容

---

## 一、总览 / Overview

| 类别 | 数量 | 大小估算 | 处理建议 |
|---|---|---|---|
| 当前在用（保留） | 1 主目录 + 2 参考目录 | ~28M | 🟢 保留 |
| 旧代码副本/快照 | 5 个目录 | ~5.5M | 🔴 删除 |
| 7/7 已整合产物 | 2 个目录 | ~150K | 🟡 归档或删除 |
| 根目录过期报告/log | ~30 个文件 | ~700K | 🔴 删除 |
| 根目录保留参考 | 3 个文件 | ~30K | 🟢 保留 |
| outreach 内部旧备份 | backup/backup_t1/staging + 22循环备份 | ~1.5M | 🟡 归档大部分 |
| tools/google-maps-scraper | 1 个目录 | 57M | ⚠️ 待确认 |

---

## 二、🟢 必须保留（当前在用）

| 路径 | 说明 | 最后修改 |
|---|---|---|
| `roktandrazo-outreach/` | **主代码库**，含 bd_db.py / daily_operator_auto.py / bd_orchestrator.py 等核心脚本 | 今天 10:51 |
| `roktandrazo-outreach/data/bd_leads.db` | **主数据库**（1.1M） | 今天 10:51 |
| `bd_effective_artifacts_20260707_1614/` | 7/7 有效产物索引（含 DEPRECATED 清单，审计参考） | 7/7 |
| `codex_handoff_bd_automation_20260707_1129/` | 7/7 最新 Codex 交接包 | 7/7 |

---

## 三、🔴 建议直接删除（明显废弃的旧副本/快照）

| 路径 | 大小 | 废弃原因 |
|---|---|---|
| `roktandrazo-outreach_backup_before_phase2_20260629_1732/` | 2.6M | Phase2 上线前备份，Phase2 已上线近 1 个月，当前主库已远超此版本 |
| `roktandrazo-outreach_phase2_staging_20260629_1732/` | 2.2M | Phase2 临时 staging，已上线，仅含一个嵌套 outreach 副本 |
| `roktandrazo-outreach_codex_lab_20260707/` | 147K | Codex 实验沙箱，仅含 sandbox_data/src/tests 空骨架 |
| `codex_handoff_bd_automation_20260629_1559/` | 573K | 6/29 旧交接包，已被 7/7 版本（`_20260707_1129`）替代 |
| `roktandrazo-leads/` | 16K | 6/5 Week1 早期 leads，已导入主库，仅 1 csv + 1 md |

**小计 ~5.5M**

---

## 四、🔴 建议删除（根目录过期报告 / log / 一次性产物）

> 以下文件均为 6/29–7/7 期间的过程性日报、测试 log、一次性 shift 产物。已被 `bd_effective_artifacts` 的 DEPRECATED_ARTIFACTS_INDEX.md 明确标注，或属一次性执行残留。

### Phase2 测试报告（6/29，Phase2 已上线）
- `phase2_py_compile_report.txt`
- `phase2_orchestrator_dryrun_report.txt`
- `phase2_browser_verifier_test_report.txt`
- `phase2_post_overwrite_dryrun.txt`
- `phase2_post_overwrite_browser_test.txt`
- `phase2_post_overwrite_daily_report.txt`

### 一次性 browser verification log（6/30）
- `inventory_live_browser_verification.log`
- `inventory_live_browser_verification_test.log`
- `inventory_live_browser_verification_batch2.log`
- `inventory_live_browser_verification_batch3.log`

### 过期日报 / 周报（7/2–7/6）
- `BD_DAILY_ORCHESTRATION_REPORT_BILINGUAL.md`
- `BD_DAILY_COLLECTION_REPORT_20260706.md`
- `BD_SAME_DAY_DEFICIT_RECOVERY_REPORT_BILINGUAL.md`
- `BD_WEEKLY_REVIEW_FOR_NEIL_BILINGUAL.md`
- `BD_WEEKLY_REVIEW_FOR_NEIL_CN.md`
- `DAILY_ORCHESTRATOR_TRIGGER_DECISION_REPORT.md`

### Branch B 已合并产物（7/7，5 个文件）
- `BRANCH_B_A0_UPGRADE_LOG.csv`
- `BRANCH_B_VERIFICATION_BATCH_REPORT.md`
- `BRANCH_B_MANUAL_CONTACT_TOP20.md`
- `BRANCH_B_BLOCKED_REASON_SUMMARY.md`
- `BRANCH_B_VERIFICATION_RESULTS.csv`

### Google Maps POC 产物（7/6，DEPRECATED 标注）
- `GOOGLE_MAPS_BRANCH_POC_REPORT.md`
- `GOOGLE_MAPS_ANTI_SCRAPE_NOTE_CN.md`
- `GOOGLE_MAPS_CANDIDATES_TN_SAMPLE.csv` (88K)

### INVENTORY SHIFT 一次性产物（7/6–7/7，含 2 个大 CSV）
- `INVENTORY_SHIFT_AR_KY_CANDIDATES.csv` (234K)
- `INVENTORY_SHIFT_TN_AR_KY_LIVE.csv` (203K)
- `INVENTORY_SHIFT_PLAN_TN_AR_KY.md`
- `STATE_DEEP_COVERAGE_INVENTORY_SHIFT_REPORT.md`

### MANUAL CONTACT 一次性产物（7/6）
- `MANUAL_CONTACT_FETCH_QUEUE.csv` (22K)
- `MANUAL_CONTACT_FETCH_QUEUE_CN.md`
- `MANUAL_CONTACT_FETCH_TOP30_CN.md`
- `MANUAL_CONTACT_IMPORT_INSTRUCTIONS_CN.md`

### 过期审计 / 状态报告（7/6–7/7）
- `STATE_DEEP_COVERAGE_SCOPE_AUDIT.md`
- `STATE_V2_A0_COUNT_AUDIT.md`
- `CITY_COVERAGE_STATUS_AUDIT.md`
- `TN_STATE_DEEP_COVERAGE_REPORT.md`（DEPRECATED 标注）
- `SEND_WINDOW_CONFIG_AUDIT.md`（DEPRECATED 旧配置）
- `TEMPLATE_V5_SYNC_REPORT.md`（DEPRECATED 已完成）
- `NETWORK_PROXY_DIAGNOSIS_REPORT.md`
- `B2_MANUAL_REVIEW_POOL_AUDIT.md`

**小计 ~30 个文件，约 700K**

---

## 五、🟢 根目录建议保留（长期参考）

| 文件 | 保留原因 |
|---|---|
| `CITY_EXPANSION_RULES.md` | 城市扩张规则文档，策略参考 |
| `CODEX_HANDOFF_ASSESSMENT_REPORT.md` | 7/13 交接评估报告，审计参考 |
| `LEAD_HYGIENE_PREFLIGHT_GATE_MERGE_REPORT.md` | 7/13 较新卫生门禁合并报告 |
| `LEAD_HYGIENE_PRODUCTION_ADAPTER_REPORT.md` | 7/13 生产适配器报告 |

---

## 六、🟡 roktandrazo-outreach 内部旧备份（建议清理）

### `roktandrazo-outreach/backup/`（6/23–7/6 旧 CSV + 模板备份，520K）
- `a_grade_sendable_20260623_*.csv` × 2
- `all_leads_20260623_*.csv` × 2
- `b_grade_20260623_*.csv` × 2
- `bounce_log_20260623_*.csv` × 2
- `suppression_list_20260623_*.csv` × 2
- `bd_template_v3_backup_20260630.py`
- `bd_template_v4_backup_20260706.py` ← **V5 已上线，但保留 1 个 V4 备份作回滚**

**建议**: 删除 6/23 的 10 个 CSV（主库已含更新数据），保留 `bd_template_v4_backup_20260706.py` 作回滚保险。

### `roktandrazo-outreach/backup_t1/`（6/23 旧 DB + CSV，496K）
- `bd_leads_20260623_162515.db` (258K) ← 旧数据库快照
- 其余 6 个 CSV 同期

**建议**: 整目录删除（主库 `data/bd_leads.db` 已远超此版本）。

### `roktandrazo-outreach/staging/`（6/30–7/2 旧 batch JSON，340K）
- 21 个 `b2_*.json` / `batch*_*.json` / `new_city_batch*.json` / `test_*.json`
- `imap_check.js`

**建议**: 整目录删除（一次性 batch 产物，已入主库）。

### `roktandrazo-outreach/backups/`（22 个 inventory_recovery_loop 时间戳目录）
- 时间跨度 7/13–7/19，每个是 inventory_recovery_loop 的快照
- 另有 `inventory_20260714`、`fb_fallback_20260713`、`lead_hygiene_preflight_gate_*`、`message_id_fix_*`、`p0_patch1_*`、`tool_patch_*`、`lead_pool_rescue_*`、`evidence_snippet_schema_*` 等

**建议**: 保留最新 2 个循环备份（`inventory_recovery_loop_20260719_1608`、`inventory_recovery_loop_20260718_1609`），其余 20 个循环备份删除；其他非循环备份保留（数量少、有节点意义）。

### `roktandrazo-outreach/__pycache__/`（172K）
- 7 个 `.pyc` 文件

**建议**: 直接删除（Python 自动重生，无保留价值）。

### `roktandrazo-outreach/logs/`
- 空目录

**建议**: 保留（运行时需要）。

### `roktandrazo-outreach/output/`（含旧 auto_report）
- `auto_report_2026-06-25.md` ~ `auto_report_2026-07-08.md`（9 个旧日报）
- `a0_inventory_reconciliation.json`、`a0_safety_inventory_30.json`（7/15）
- `.inventory_recovery.lock`

**建议**: 删除 9 个 6/25–7/8 的旧 `auto_report_*.md`；保留 7/15 的 a0 JSON 和 lock 文件。

### `roktandrazo-outreach/data/`（旧 DB）
- `leads.db` (94K, 6/8) ← Phase1 旧库
- `phase1_leads.db` (36K, 6/10) ← Phase1 旧库
- `bd_leads.db` (1.1M, 今天) ← **主库保留**
- `searched_cities.json` (7/2)

**建议**: 删除 `leads.db` 和 `phase1_leads.db`（已被 `bd_leads.db` 取代）；保留 `searched_cities.json`。

---

## 七、⚠️ 待确认

### `tools/google-maps-scraper/`（57M）
- `gmaps-scraper.exe` (59M) ← 占空间最大
- `gmaps_fast_poc.py`、`gmaps_playwright_poc.py` ← POC 脚本
- `inventory_shift_ar_ky.py`、`inventory_shift_live.py` ← shift 工具
- `queries_tn.txt`、`queries_test.txt`、`test_output.csv`（空）

**背景**: 主流程已用 `roktandrazo-outreach/fast_lead_discovery.py`（HTTP-first）替代 Google Maps scraping。此目录是 7/6 POC 残留，`.exe` 占 57M。

**待确认**: 是否还在用？若不用，删掉可释放 57M（C 盘紧张）。

---

## 八、_archive/ 现有内容（不动）

`_archive/` 已有 32 个 6/29–7/3 的归档文件（phase2 报告、B2 评审、早期日报等）。本次清理**不改动** `_archive/`，新归档项可选择追加或单独存放。

---

## 九、预计释放空间

| 操作 | 释放 |
|---|---|
| 删除 5 个旧副本目录 | ~5.5M |
| 删除根目录 ~30 个过期文件 | ~700K |
| 清理 outreach 内部旧备份 | ~1.5M |
| 删除 __pycache__ | 172K |
| 删除 output 旧 auto_report | ~7K |
| 删除 data 旧 DB | 130K |
| （待确认）删除 tools/google-maps-scraper | 57M |
| **合计（不含 tools）** | **~8M** |
| **合计（含 tools）** | **~65M** |

---

## 十、执行方式

1. 先执行无争议项（旧副本目录 + 过期报告 + __pycache__ + 旧 DB）
2. `tools/google-maps-scraper` 待确认后再处理
3. 所有删除操作前会再次列出确切路径，确认后批量执行
4. 不动 `roktandrazo-outreach/` 主代码、主库、当前 automation 配置

---

## 十一、执行确认 / Execution Confirmation

**执行时间**: 2026-07-20 11:00 Asia/Shanghai
**执行状态**: ✅ 全部完成（用户确认全部按推荐方案）

### 已删除清单

| 批次 | 内容 | 结果 |
|---|---|---|
| 1 | 5 个旧副本目录（Phase2备份/staging/codex_lab/6·29旧交接包/Week1 leads） | ✅ 释放 5.5M |
| 2 | 根目录 39 个过期文件（phase2测试报告/browser log/日报周报/BranchB/GoogleMaps POC/INVENTORY SHIFT/MANUAL CONTACT/过期审计） | ✅ 释放 700K |
| 3 | outreach 内 `backup/` 删 6/23 CSV 留 v4 模板；`backup_t1/` 全删；`staging/` 全删 | ✅ 释放 1.3M |
| 4 | outreach `backups/` 22 个循环备份删 20 留 2（最新 7/18、7/19）+ 保留 8 个非循环节点备份 | ✅ |
| 5 | outreach `__pycache__/` 全删；`output/` 删 9 个旧 auto_report；`data/` 删 leads.db + phase1_leads.db | ✅ |
| 6 | `tools/google-maps-scraper/` 全删（含 59M .exe），`tools/` 空目录清除 | ✅ 释放 57M |

### 保留的核心资产（已验证完好）

| 文件 | 大小 | 修改时间 |
|---|---|---|
| `roktandrazo-outreach/bd_db.py` | 31K | 2026-07-20 10:49 |
| `roktandrazo-outreach/bd_orchestrator.py` | 31K | 2026-07-20 10:47 |
| `roktandrazo-outreach/daily_operator_auto.py` | 47K | 2026-07-16 14:33 |
| `roktandrazo-outreach/data/bd_leads.db` | 1.1M | 2026-07-20 10:52 |
| `roktandrazo-outreach/.env` | 883B | 2026-06-12 |

### 保留的参考目录

| 目录 | 大小 | 用途 |
|---|---|---|
| `_archive/` | 233K | 原有归档（未改动） |
| `bd_effective_artifacts_20260707_1614/` | 297K | 7/7 有效产物索引（含 DEPRECATED 清单，审计参考） |
| `codex_handoff_bd_automation_20260707_1129/` | 60K | 7/7 最新 Codex 交接包 |
| `workbuddy_artifact_recovery_20260707_1413/` | 100K | 7/7 产物恢复（effective_artifacts 源材料） |
| `workbuddy_report_reexport_20260707_1551/` | 52K | 7/7 报告重导出（effective_artifacts 源材料） |
| `roktandrazo-outreach/` | 8.5M | 主代码库（从 28M 瘦身到 8.5M） |

### 空间释放汇总

| 指标 | 清理前 | 清理后 |
|---|---|---|
| 工作空间总大小 | ~91M | **9.4M** |
| 根目录文件数 | 50+ | 5 |
| outreach 内 backups 循环备份 | 22 | 2 |
| **总释放** | — | **~81M** |

### 备注

- `roktandrazo-outreach/output/` 内仍有部分历史 `daily_report_*.md` 和 `b2_browser_manual_*.csv`，本次未清理（不在方案范围内）。如需进一步瘦身可单独处理。
- `workbuddy_artifact_recovery_20260707_1413/` 和 `workbuddy_report_reexport_20260707_1551/` 已被 `bd_effective_artifacts` 整合，体积小（150K），保留作审计源材料。如确认不再需要可随时删除。
