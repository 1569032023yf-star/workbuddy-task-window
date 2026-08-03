# Today Preflight Report / 今日发信前检查报告

Generated / 生成时间: 2026-07-07 12:25 Asia/Shanghai

## Report Self-Check / 报告自检

中文：
本报告生成前已检查：中英双语、中文解释、英文版本、无敏感信息、包含执行结果、包含未执行事项、包含风险、包含下一步、未把未完成事项写成已完成，并符合 BD 自动化项目口径。

English:
Before this report was generated, it was checked for bilingual Chinese-English content, Chinese explanation, English version, no sensitive information, execution results, non-executed items, risks, next steps, no unfinished work marked complete, and alignment with the BD automation project framing.

| Check / 检查项 | Status / 状态 |
|---|---|
| Bilingual content / 中英双语 | Pass / 通过 |
| No sensitive secrets / 无敏感密钥 | Pass / 通过 |
| Execution results included / 包含执行结果 | Pass / 通过 |
| Non-executed items included / 包含未执行事项 | Pass / 通过 |
| Risks and next steps included / 包含风险和下一步 | Pass / 通过 |
| No unfinished item marked complete / 未把未完成事项写成已完成 | Pass / 通过 |
| BD automation framing / BD 自动化项目口径 | Pass / 通过 |

## Executive Summary / 执行摘要

中文：
今日处于 Asia/Shanghai 09:00-13:00 发信窗口内，但 preflight 未通过，因此本轮没有执行客户 live send。阻断原因包括：必读项目文件 CURRENT_STATUS.md、RUNBOOK.md、FILE_MANIFEST.md 缺失；数据库没有 evidence_snippet 字段；严格合规可发池不足 20；系统存在 Roktandrazo_Daily_Outreach scheduled task（Ready，action 为 dry-run，下一次为 2026-07-08 10:00）。

English:
The current time was inside the Asia/Shanghai 09:00-13:00 sending window, but preflight did not pass, so no customer live send was performed in this run. Blocking reasons included missing required project files (CURRENT_STATUS.md, RUNBOOK.md, FILE_MANIFEST.md), no evidence_snippet column in the database, fewer than 20 strictly compliant sendable leads, and the presence of the Roktandrazo_Daily_Outreach scheduled task (Ready, dry-run action, next run at 2026-07-08 10:00).

## Required Files / 必读文件

中文：
已读取 GUARDRAILS.md、PRODUCTION_MESSAGE_ID_FIX_AND_RESEND_REPORT.md、YESTERDAY_MESSAGE_ID_RESEND_CANDIDATES.md。未找到 CURRENT_STATUS.md、RUNBOOK.md、FILE_MANIFEST.md、PROJECT_SKILLS.md、BD_AUTOMATION_SKILL.md。按本次任务要求，缺少前三个必读文件时不得直接 live send。

English:
GUARDRAILS.md, PRODUCTION_MESSAGE_ID_FIX_AND_RESEND_REPORT.md, and YESTERDAY_MESSAGE_ID_RESEND_CANDIDATES.md were read. CURRENT_STATUS.md, RUNBOOK.md, FILE_MANIFEST.md, PROJECT_SKILLS.md, and BD_AUTOMATION_SKILL.md were not found. Per this task's requirements, live send must not proceed directly when the first three required files are missing.

| File / 文件 | Status / 状态 |
|---|---|
| CURRENT_STATUS.md | Missing / 缺失 |
| GUARDRAILS.md | Found / 已读取 |
| RUNBOOK.md | Missing / 缺失 |
| FILE_MANIFEST.md | Missing / 缺失 |
| PRODUCTION_MESSAGE_ID_FIX_AND_RESEND_REPORT.md | Found / 已读取 |
| YESTERDAY_MESSAGE_ID_RESEND_CANDIDATES.md | Found / 已读取 |
| PROJECT_SKILLS.md | Missing optional / 可选文件缺失 |
| BD_AUTOMATION_SKILL.md | Missing optional / 可选文件缺失 |

## Preflight Checks / Preflight 检查

中文：
Message-ID 修复仍在生产生效，py_compile 通过，V5 模板存在，当前时间在窗口内。send_pause=false，uto_send_enabled=true。但这些通过项不足以覆盖缺失规则文件、evidence_snippet schema 缺口和可发池不足的问题。

English:
The Message-ID fix is still active in production, py_compile passed, the V5 template exists, and the current time was inside the sending window. send_pause=false and uto_send_enabled=true. These passing checks do not override the missing rule files, the missing evidence_snippet schema, or the insufficient sendable pool.

| Check / 检查项 | Result / 结果 |
|---|---|
| Message-ID fix active / Message-ID 修复生效 | Pass / 通过 |
| d_sender.py standard headers / 标准 header | Pass / 通过 |
| missing Message-ID classification / 缺失 Message-ID 分类 | Pass / 通过 |
| message_id_missing not suppressed / 不加入 suppression | Pass / 通过 |
| py_compile | Pass / 通过 |
| V5 template exists / V5 模板存在 | Pass / 通过 |
| Current time in send window / 当前在发信窗口 | Yes / 是 |
| Required rule files / 必读规则文件 | Fail / 未通过 |
| evidence_snippet available / evidence_snippet 可用 | Fail / 未通过 |
| Strict sendable pool >= 20 / 严格可发池 >= 20 | Fail / 未通过 |
| Scheduled task risk reviewed / 定时任务风险已审计 | Reviewed / 已审计 |

## Counts / 数量统计

中文：
项目现有 sendable 口径为 A0 14、approved_manual_send 0、合计 14。若要求必须有 evidence_url，候选为 13。若严格要求必须有 evidence_snippet 字段，则当前 schema 下合规可发数为 0。今日数据库已有 send_log sent 记录 2 条，但本轮没有新增客户发信。

English:
Under the existing project sendable definition, there are 14 A0 leads and 0 approved_manual_send leads, for a total of 14. If evidence_url is required, there are 13 candidates. If the evidence_snippet field is strictly required, the compliant sendable count is 0 under the current schema. The database already had 2 sent records for today, but this run added no customer sends.

| Metric / 指标 | Count / 数量 |
|---|---:|
| Existing project A0 sendable / 项目现有 A0 可发 | 14 |
| approved_manual_send | 0 |
| Existing project sendable total / 项目现有可发合计 | 14 |
| With evidence_url / 有 evidence_url 的候选 | 13 |
| With required evidence_snippet field / 有必需 evidence_snippet 字段的候选 | 0 |
| Today sent_log sent records / 今日 sent_log 已有 sent 记录 | 2 |
| Customer sends performed by this run / 本轮客户发信 | 0 |

## Non-Executed Items / 未执行事项

中文：
未执行客户 live send；未修改 Windows scheduled task；未修改 send_pause；未写入 suppression；未执行 Google Maps scraping；未执行库存恢复写入；未输出 .env、SMTP/IMAP 密码、token、cookie 或 auth json。

English:
No customer live send was performed; no Windows scheduled task was modified; send_pause was not changed; no suppression entry was written; no Google Maps scraping was performed; no inventory restoration write was performed; and no .env, SMTP/IMAP password, token, cookie, or auth json was output.

## Risks / 风险

中文：
如果绕过缺失规则文件和 evidence_snippet 要求直接发信，会违反本次任务 gate。scheduled task 当前是 dry-run，但仍应在恢复自动化前由用户确认。当前 sendable_pool 不足 20，更不足 60。

English:
Bypassing the missing rule files and the evidence_snippet requirement would violate this task's gates. The scheduled task is currently dry-run, but it should still be confirmed by the user before automation is restored. The current sendable pool is below 20 and far below 60.

## Next Step / 下一步

中文：
建议先补齐 CURRENT_STATUS.md、RUNBOOK.md、FILE_MANIFEST.md，并决定是否新增 evidence_snippet 字段或明确允许使用 
notes 中的 browser verification snippet。确认后再进入 live send 或数据库级库存补池。

English:
Recommended next steps are to add CURRENT_STATUS.md, RUNBOOK.md, and FILE_MANIFEST.md, then decide whether to add an evidence_snippet column or explicitly allow using the browser verification snippet stored in 
notes. After confirmation, live send or database-level inventory rebuild can proceed.

