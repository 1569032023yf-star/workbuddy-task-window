# WorkBuddy Trusted Source Index / WorkBuddy 可信资料源索引

**Date / 日期**: 2026-07-07 16:01 Asia/Shanghai

---

## Tier 1: Trusted Original Sources (WorkBuddy Generated) / 一级可信源

| 文件路径 | 用途 | Codex 可读 | 可复制到 D:\CODEX | 禁止写回 | 备注 |
|----------|------|-----------|------------------|---------|------|
| `workbuddy_report_reexport_20260707_1551/FAST_INVENTORY_EXPANSION_TOOL_PLAN_UTF8.md` | 扩池工具计划 | ✅ | ✅ | ✅ | UTF-8 BOM，中文完整 |
| `workbuddy_report_reexport_20260707_1551/FAST_INVENTORY_EXPANSION_EXECUTION_REPORT_UTF8.md` | 扩池执行报告 | ✅ | ✅ | ✅ | UTF-8 BOM，中文完整 |
| `workbuddy_report_reexport_20260707_1551/STRICT_SENDABLE_POOL_AFTER_EXPANSION_UTF8.md` | 扩池后发送池 | ✅ | ✅ | ✅ | UTF-8 BOM，中文完整 |
| `workbuddy_report_reexport_20260707_1551/LEAD_POOL_RESCUE_BACKFILL_REPORT_UTF8.md` | 线索池救援回填 | ✅ | ✅ | ✅ | UTF-8 BOM，中文完整 |
| `workbuddy_report_reexport_20260707_1551/REPORT_ENCODING_SOURCE_DIAGNOSIS.md` | 编码诊断 | ✅ | ✅ | ✅ | UTF-8 |
| `workbuddy_report_reexport_20260707_1551/WORKBUDDY_OUTPUT_READABILITY_AUDIT.md` | 可读性审计 | ✅ | ✅ | ✅ | UTF-8 |
| `workbuddy_report_reexport_20260707_1551/WORKBUDDY_TRUSTED_SOURCE_INDEX.md` | 本索引 | ✅ | ✅ | ✅ | UTF-8 |
| `workbuddy_report_reexport_20260707_1551/BD_CONTEXT_DIGEST_FOR_CODEX.md` | BD 上下文摘要 | ✅ | ✅ | ✅ | UTF-8 |

---

## Tier 2: Codex Handoff Sources (WorkBuddy Generated, English) / 二级交接源

| 文件路径 | 用途 | Codex 可读 | 可复制到 D:\CODEX | 禁止写回 | 备注 |
|----------|------|-----------|------------------|---------|------|
| `codex_handoff_bd_automation_20260707_1129/CURRENT_STATUS.md` | 当前状态 | ✅ | ✅ | ✅ | 英文为主 |
| `codex_handoff_bd_automation_20260707_1129/RUNBOOK.md` | 运行手册 | ✅ | ✅ | ✅ | 英文为主 |
| `codex_handoff_bd_automation_20260707_1129/FILE_MANIFEST.md` | 文件清单 | ✅ | ✅ | ✅ | 英文为主 |
| `codex_handoff_bd_automation_20260707_1129/GUARDRAILS.md` | 项目护栏 | ✅ | ✅ | ✅ | 中英双语 |
| `codex_handoff_bd_automation_20260707_1129/ARCHITECTURE_MAP.md` | 架构图 | ✅ | ✅ | ✅ | 英文为主 |
| `codex_handoff_bd_automation_20260707_1129/SENSITIVE_EXCLUSION_AUDIT.md` | 敏感信息审计 | ✅ | ✅ | ✅ | 英文为主 |

---

## Tier 3: Production Files (Read-Only for Codex) / 三级生产文件

| 文件路径 | 用途 | Codex 可读 | 可复制到 D:\CODEX | 禁止写回 | 备注 |
|----------|------|-----------|------------------|---------|------|
| `roktandrazo-outreach/FAST_INVENTORY_EXPANSION_TOOL_PLAN.md` | 扩池工具计划（原始） | ✅ | ✅ | ✅ | UTF-8，中文完整 |
| `roktandrazo-outreach/FAST_INVENTORY_EXPANSION_EXECUTION_REPORT.md` | 扩池执行报告（原始） | ✅ | ✅ | ✅ | UTF-8，中文完整 |
| `roktandrazo-outreach/STRICT_SENDABLE_POOL_AFTER_EXPANSION.md` | 扩池后发送池（原始） | ✅ | ✅ | ✅ | UTF-8，中文完整 |
| `roktandrazo-outreach/LEAD_POOL_RESCUE_BACKFILL_REPORT.md` | 线索池救援回填（原始） | ✅ | ✅ | ✅ | UTF-8，中文完整 |
| `roktandrazo-outreach/GUARDRAILS.md` | 项目护栏 | ✅ | ✅ | ✅ | UTF-8 BOM |
| `roktandrazo-outreach/data/bd_leads.db` | 生产数据库 | ✅ | ❌ | ✅ | 禁止复制/写回 |

---

## Tier 4: Codex-Generated (Caution) / 四级 Codex 生成（需谨慎）

| 文件路径 | 用途 | Codex 可读 | 可复制到 D:\CODEX | 禁止写回 | 备注 |
|----------|------|-----------|------------------|---------|------|
| `roktandrazo-outreach/LEAD_POOL_RESCUE_AUDIT_REPORT.md` | 线索池救援审计 | ⚠️ 中文不可读 | ✅ | ✅ | ASCII，中文为 `????` |

---

## Rules for Codex / Codex 使用规则

1. **只读原则**: Codex 不得写回本目录中的任何文件
2. **复制原则**: Codex 可以将 Tier 1-3 文件复制到 `D:\CODEX` 作为参考
3. **禁止复制**: `data/bd_leads.db`（生产数据库）
4. **编码原则**: 复制时保持 UTF-8 BOM 编码
5. **事实原则**: 以 Tier 1 文件为最高可信源，Tier 4 文件仅供参考英文部分
