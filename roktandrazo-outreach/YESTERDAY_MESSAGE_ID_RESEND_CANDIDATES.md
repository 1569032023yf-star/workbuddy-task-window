# Yesterday Message-ID Resend Candidates / 昨日 Message-ID 重发候选清单

中文：
原始生成时间：2026-07-07 12:06:09 Asia/Shanghai。本文件已重写为中英双语版本；事实、数量和执行结果未改变。

English:
Original generation time: 2026-07-07 12:06:09 Asia/Shanghai. This file has been rewritten as a bilingual Chinese-English version; facts, counts, and execution results were not changed.

## Report Self-Check / 报告自检

中文：
本报告生成前已按项目报告自检清单检查：包含中英双语、中文解释、英文版本、执行结果、未执行事项、风险、下一步；未包含敏感信息；未把未完成事项写成已完成；符合 BD 自动化项目口径。

English:
Before this report was generated, it was checked against the project report checklist: it includes bilingual Chinese-English content, Chinese explanations, an English version, execution results, non-executed items, risks, and next steps; it does not include sensitive information; it does not present unfinished work as completed; and it follows the BD automation project framing.

| Check / 检查项 | Status / 状态 |
|---|---|
| Bilingual Chinese-English / 中英双语 | Pass / 通过 |
| Chinese explanation included / 包含中文解释 | Pass / 通过 |
| English version included / 包含英文版本 | Pass / 通过 |
| No sensitive information / 无敏感信息 | Pass / 通过 |
| Execution results included / 包含执行结果 | Pass / 通过 |
| Non-executed items included / 包含未执行事项 | Pass / 通过 |
| Risks included / 包含风险 | Pass / 通过 |
| Next steps included / 包含下一步 | Pass / 通过 |
| No unfinished work marked complete / 未将未完成事项写成已完成 | Pass / 通过 |
| BD automation framing followed / 符合 BD 自动化项目口径 | Pass / 通过 |

## Audit Scope / 审计范围

中文：
审计窗口为 `2026-07-06 Asia/Shanghai`。本次只查找昨日因 Message-ID/header 缺陷导致技术退信的客户候选，不混入 hard bounce、suppression、退订、delivery_issue、B/B2/C/guessed_email 或非 Message-ID 退信。

English:
The audited window was `2026-07-06 Asia/Shanghai`. This audit only looked for customer candidates with yesterday's sender-side technical bounce caused by a Message-ID/header defect, without mixing in hard bounces, suppression entries, unsubscribes, delivery issues, B/B2/C/guessed_email pools, or non-Message-ID bounces.

## Execution Result / 执行结果

中文：
生产 `bounce_log` 中没有找到 `2026-07-06` 的 Message-ID 技术退信候选。因此，本次客户重发候选数为 0，实际客户重发数为 0。

English:
No Message-ID technical-bounce candidates for `2026-07-06` were found in production `bounce_log`. Therefore, the customer resend candidate count was 0, and the actual customer resend count was 0.

| Metric / 指标 | Count / 数量 |
|---|---:|
| 2026-07-06 bounce rows / 2026-07-06 退信行数 | 0 |
| 2026-07-06 rows containing message/header/Message-ID keywords / 2026-07-06 含 message/header/Message-ID 关键词行数 | 0 |
| Eligible Message-ID technical-bounce resend candidates / 符合条件的 Message-ID 技术退信重发候选 | 0 |
| Excluded candidates / 排除候选 | 0 |
| Actual customer resends / 实际客户重发 | 0 |

## Candidate Table / 候选表

中文：
没有符合条件的候选。下表保留字段结构，用于证明本次没有输出完整客户邮箱表，也没有产生客户重发名单。

English:
There were no eligible candidates. The table structure is retained to show that no full customer email table was output and no customer resend list was produced.

| store_name / 店铺名 | masked_email / 脱敏邮箱 | domain / 域名 | original_send_time / 原发送时间 | original_bounce_time / 原退信时间 | bounce_reason / 退信原因 | resend_eligibility / 重发资格 | exclusion_reason_if_any / 排除原因 |
|---|---|---|---|---|---|---|---|
| - | - | - | - | - | No 2026-07-06 Message-ID technical bounce rows found / 未找到 2026-07-06 Message-ID 技术退信行 | none / 无 | no candidate rows / 无候选行 |

## Exclusion Policy Applied / 已应用排除规则

中文：
本次受控重发排除了 hard bounce、unsubscribe、suppression、customer_invalid_email、domain_invalid、mailbox/user unknown、spam rejection、delivery_issue、already replied、already resent、duplicate domain，以及 B/B2/C/guessed_email 类型池。

English:
This controlled resend excluded hard bounce, unsubscribe, suppression, customer_invalid_email, domain_invalid, mailbox/user unknown, spam rejection, delivery_issue, already replied, already resent, duplicate domain, and B/B2/C/guessed_email style pools.

## Non-Executed Items / 未执行事项

中文：
由于候选数为 0，本次没有执行客户邮件重发；没有执行 Google Maps scraping；没有执行库存恢复；没有修改 Windows scheduled task；没有写入 suppression；没有输出 `.env`、SMTP/IMAP 密码、token、cookie 或 auth json。

English:
Because the candidate count was 0, no customer resend was performed; no Google Maps scraping was performed; no inventory restoration was performed; no Windows scheduled task was modified; no suppression entry was written; and no `.env`, SMTP/IMAP password, token, cookie, or auth json was output.

## Risks / 风险

中文：
主要剩余风险是生产 `bounce_log` 当前没有昨日 Message-ID 技术退信行，因此无法执行或验证客户重发批次；如果外部邮箱系统存在未入库退信，本报告不会把它们纳入候选。

English:
The main remaining risk is that production `bounce_log` currently contains no yesterday Message-ID technical-bounce rows, so no customer resend batch can be executed or verified. If external mailbox systems contain bounces that were not recorded in the database, this report does not include them as candidates.

## Next Step / 下一步

中文：
无需对 2026-07-06 执行客户重发。下一步应在正常 BD 操作窗口内继续使用已修复的发信代码；如需重新审计外部邮箱未入库退信，需要用户单独确认范围。

English:
No customer resend should be executed for 2026-07-06. The next step is to continue using the fixed sender code during the normal BD operator window. If external mailbox bounces that were not recorded in the database need to be audited, the user must confirm that scope separately.
