# Today Controlled Live Send After Schema Fix Report / Schema 修复后今日受控 live send 报告

Generated / 生成时间: 2026-07-07 13:06 Asia/Shanghai

## Report Self-Check / 报告自检

中文：
本报告生成前已检查：中英双语、中文解释、英文版本、无敏感信息、包含执行结果、包含未执行事项、包含风险、包含下一步、未把未完成事项写成已完成，并符合 BD 自动化项目口径。

English:
Before this report was generated, it was checked for bilingual Chinese-English content, Chinese explanation, English version, no sensitive information, execution results, non-executed items, risks, next steps, no unfinished work marked complete, and alignment with the BD automation project framing.

## Executive Summary / 执行摘要

中文：
本轮 schema 修复后没有执行客户 live send。原因有两个：当前时间 13:05 已超过 Asia/Shanghai 09:00-13:00 客户发信窗口；严格 sendable_pool 只有 5，小于 live send 最低 gate 20。

English:
No customer live send was performed after this schema fix. There were two reasons: current time 13:05 was outside the Asia/Shanghai 09:00-13:00 customer send window, and strict sendable_pool was only 5, below the live send minimum gate of 20.

## Gate Result / Gate 结果

| Gate / Gate | Result / 结果 |
|---|---|
| Rule files created / 规则文件已创建 | Pass / 通过 |
| evidence_snippet schema / evidence_snippet schema | Pass / 通过 |
| DB backup / DB 备份 | Pass / 通过 |
| evidence_snippet backfill / evidence_snippet 回填 | Partial / 部分完成 |
| strict sendable_pool >=20 / 严格池 >=20 | Fail: 5 / 未通过：5 |
| send window open / 发信窗口打开 | Fail: closed at 13:05 / 未通过：13:05 已关闭 |
| live send / live send | Not executed / 未执行 |

## Send Result / 发信结果

中文：
本轮客户 live send = 0。没有写入 send_log，没有发送 B2/C/guessed_email，没有发送 suppression、hard bounce、delivery_issue、unsubscribe 或 duplicate domain。

English:
Customer live send in this run = 0. No send_log was written, no B2/C/guessed_email was sent, and no suppression, hard bounce, delivery_issue, unsubscribe, or duplicate-domain contact was sent.

## send_pause / send_pause

中文：
send_pause 最终状态仍为 alse。本轮没有恢复长期自动群发，也没有修改 scheduled task。

English:
Final send_pause state remains alse. This run did not restore long-term automated bulk sending and did not modify scheduled tasks.

## Non-Executed Items / 未执行事项

中文：
未执行客户 live send；未窗口外发送；未恢复长期自动群发；未修改 Windows scheduled task；未输出敏感信息。

English:
No customer live send was performed; no out-of-window customer send was performed; long-term automated bulk sending was not restored; Windows scheduled tasks were not modified; no sensitive information was output.

## Risks / 风险

中文：
严格池不足 20，不能进行受控发信。即使窗口重新打开，也必须先重新 dry-run 并确认严格池 >=20。

English:
The strict pool is below 20, so controlled send cannot proceed. Even when the window reopens, dry-run must be regenerated and strict pool >=20 must be confirmed first.

## Next Step / 下一步

中文：
继续补池到至少 20 才能考虑下一次发信；继续补到 60 才能完成库存目标。下一步需要用户确认是否允许我修改补池工具以支持 TN/AR/KY 过滤和 browser verification。

English:
Continue rebuilding to at least 20 before considering the next send; continue rebuilding to 60 to complete the inventory target. Next step requires user confirmation on whether I may modify rebuild tooling to support TN/AR/KY filtering and browser verification.
