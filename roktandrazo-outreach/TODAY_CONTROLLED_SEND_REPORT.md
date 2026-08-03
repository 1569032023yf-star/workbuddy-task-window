# Today Controlled Send Report / 今日受控发信报告

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
本轮没有执行客户 live send。虽然当前时间在发送窗口内，但 preflight 和 dry-run 均未通过，原因是必读项目文件缺失、evidence_snippet schema 缺失、严格可发池不足 20。

English:
No customer live send was performed in this run. Although the current time was inside the sending window, both preflight and dry-run failed because required project files were missing, the evidence_snippet schema was missing, and the strictly compliant sendable pool was below 20.

## Send Result / 发信结果

| Metric / 指标 | Value / 值 |
|---|---|
| In send window / 是否在发信窗口 | Yes / 是 |
| Live send attempted / 是否尝试 live | No / 否 |
| Customer emails sent by this run / 本轮客户发信数 | 0 |
| Existing today sent_log records / 今日数据库已有 sent_log sent | 2 |
| send_log entries added by this run / 本轮新增 send_log | 0 |
| New bounces observed by this run / 本轮发现新退信 | 0 |
| New Message-ID issue observed / 本轮再次出现 Message-ID 问题 | No / 否 |
| send_pause final state / send_pause 最终状态 | false |

## Actions Executed / 已执行动作

中文：
执行了规则读取、preflight 只读审计、scheduled task 只读审计、sendable_pool 只读统计、dry-run 候选计划生成、py_compile 验证和双语报告生成。

English:
Executed rule reading, read-only preflight audit, read-only scheduled task audit, read-only sendable pool counting, dry-run candidate plan generation, py_compile verification, and bilingual report generation.

## Non-Executed Items / 未执行事项

中文：
未发送客户邮件；未调用 live send；未修改数据库发送状态；未写入 suppression；未修改 scheduled task；未恢复或启动全自动群发；未输出任何敏感凭据。

English:
No customer email was sent; live send was not invoked; database send state was not modified; suppression was not written; scheduled tasks were not modified; full automation was not restored or started; no sensitive credentials were output.

## Risks / 风险

中文：
若用户希望今天继续补发到 20，需要先确认缺失文件和 evidence snippet 口径。否则 live send 不符合本次任务 gate。

English:
If the user wants to continue toward 20 sends today, the missing files and evidence snippet policy must be confirmed first. Otherwise, live send does not comply with this task's gates.

## Next Step / 下一步

中文：
等待用户确认：是否先创建缺失规则文件，并是否新增 evidence_snippet 字段或允许使用 
notes 中的验证片段。

English:
Wait for user confirmation on whether to create the missing rule files and whether to add an evidence_snippet column or allow using verification snippets stored in 
notes.

