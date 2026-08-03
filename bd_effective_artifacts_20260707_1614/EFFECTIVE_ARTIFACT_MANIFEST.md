# Effective Artifact Manifest / 有效产物清单

**Date / 日期**: 2026-07-07 16:30 Asia/Shanghai

---

## PROJECT_RULES/ (5 files)

| File | Source | Purpose | Trusted | Codex Read | Write-back |
|---|---|---|---|---|---|
| BD_CONTEXT_DIGEST_FOR_CODEX.md | workbuddy_report_reexport | BD 项目上下文摘要 | ✅ | ✅ | ❌ |
| WORKBUDDY_TRUSTED_SOURCE_INDEX.md | workbuddy_report_reexport | 可信源索引 | ✅ | ✅ | ❌ |
| GUARDRAILS.md | roktandrazo-outreach | 项目护栏 | ✅ | ✅ | ❌ |
| CURRENT_STATUS.md | codex_handoff | 当前状态 | ✅ | ✅ | ❌ |
| CODEX_GUARDRAILS.md | codex_handoff | Codex 护栏 | ✅ | ✅ | ❌ |

---

## RUNBOOK/ (3 files)

| File | Source | Purpose | Trusted | Codex Read | Write-back |
|---|---|---|---|---|---|
| RUNBOOK.md | codex_handoff | 运行手册 | ✅ | ✅ | ❌ |
| FILE_MANIFEST.md | codex_handoff | 文件清单 | ✅ | ✅ | ❌ |
| ARCHITECTURE_MAP.md | codex_handoff | 架构图 | ✅ | ✅ | ❌ |

---

## REPORTS_TRUSTED/ (6 files)

| File | Source | Purpose | Trusted | Codex Read | Write-back |
|---|---|---|---|---|---|
| FAST_INVENTORY_EXPANSION_TOOL_PLAN_UTF8.md | workbuddy_report_reexport | 扩池工具计划 | ✅ | ✅ | ❌ |
| FAST_INVENTORY_EXPANSION_EXECUTION_REPORT_UTF8.md | workbuddy_report_reexport | 扩池执行报告 | ✅ | ✅ | ❌ |
| STRICT_SENDABLE_POOL_AFTER_EXPANSION_UTF8.md | workbuddy_report_reexport | 扩池后发送池 | ✅ | ✅ | ❌ |
| LEAD_POOL_RESCUE_BACKFILL_REPORT_UTF8.md | workbuddy_report_reexport | 线索池救援回填 | ✅ | ✅ | ❌ |
| REPORT_ENCODING_SOURCE_DIAGNOSIS.md | workbuddy_report_reexport | 编码诊断 | ✅ | ✅ | ❌ |
| WORKBUDDY_OUTPUT_READABILITY_AUDIT.md | workbuddy_report_reexport | 可读性审计 | ✅ | ✅ | ❌ |

---

## REPORTS_ARCHIVE_REFERENCE/ (1 file)

| File | Source | Purpose | Trusted | Codex Read | Write-back |
|---|---|---|---|---|---|
| SENSITIVE_EXCLUSION_AUDIT.md | codex_handoff | 敏感信息审计 | ✅ reference_only | ✅ | ❌ |

---

## CODE_CURRENT/ (7 files)

| File | Source | Purpose | Trusted | Codex Read | Write-back |
|---|---|---|---|---|---|
| bd_sender.py | roktandrazo-outreach | 邮件发送 | ✅ | ✅ | ❌ |
| bd_db.py | roktandrazo-outreach | 数据库操作 | ✅ | ✅ | ❌ |
| bd_template.py | roktandrazo-outreach | V5 模板 | ✅ | ✅ | ❌ |
| daily_operator_auto.py | roktandrazo-outreach | 每日编排 | ✅ | ✅ | ❌ |
| daily_session.py | roktandrazo-outreach | 每日会话 | ✅ | ✅ | ❌ |
| agent_bounce_auditor.py | roktandrazo-outreach | 退信审计 | ✅ | ✅ | ❌ |
| fast_lead_discovery.py | roktandrazo-outreach | 快速发现 | ✅ | ✅ | ❌ |

---

## DB_SCHEMA/ (2 files)

| File | Source | Purpose | Trusted | Codex Read | Write-back |
|---|---|---|---|---|---|
| schema.sql | DB export | 表结构 | ✅ | ✅ | ❌ |
| system_config.md | DB export | 系统配置 | ✅ | ✅ | ❌ |

---

## DATA_EXPORTS_MASKED/ (1 file)

| File | Source | Purpose | Trusted | Codex Read | Write-back |
|---|---|---|---|---|---|
| pool_stats.md | DB export | 池统计（脱敏） | ✅ | ✅ | ❌ |

---

## CODEX_HANDOFF/ (1 file)

| File | Source | Purpose | Trusted | Codex Read | Write-back |
|---|---|---|---|---|---|
| README.md | codex_handoff | 交接说明 | ✅ | ✅ | ❌ |

---

## Total / 合计

| Category | Count |
|---|---|
| PROJECT_RULES | 5 |
| RUNBOOK | 3 |
| REPORTS_TRUSTED | 6 |
| REPORTS_ARCHIVE_REFERENCE | 1 |
| CODE_CURRENT | 7 |
| DB_SCHEMA | 2 |
| DATA_EXPORTS_MASKED | 1 |
| CODEX_HANDOFF | 1 |
| Root files | 5 |
| **Total** | **31** |
