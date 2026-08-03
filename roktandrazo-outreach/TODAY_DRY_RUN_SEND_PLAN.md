# Today Dry-Run Send Plan / 今日 Dry-run 发信计划

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
本次 dry-run 只生成候选审计和发送计划，没有发送客户邮件。候选审计发现 13 条有 evidence_url 的候选，但数据库无 evidence_snippet 字段，且候选数少于 20，所以 dry-run gate 未通过，planned_send_count 设为 0。

English:
This dry-run only generated candidate audit and send planning; no customer email was sent. The audit found 13 candidates with evidence_url, but the database has no evidence_snippet column and the candidate count is below 20, so the dry-run gate did not pass and planned_send_count was set to 0.

## Dry-Run Result / Dry-run 结果

| Field / 字段 | Value / 值 |
|---|---|
| candidate_count / 候选审计数 | 13 |
| planned_send_count / 计划发送数 | 0 |
| dry-run gate / dry-run gate | Failed / 未通过 |
| header_check_result / header 检查 | Passed in production builder / 生产构造器通过 |
| unique_message_id_check_result / Message-ID 唯一性 | Passed previously and still compiled / 已通过且代码编译通过 |
| reason / 原因 | Missing required evidence_snippet schema and underfilled candidate count / 缺少必需 evidence_snippet schema 且候选不足 |

## Candidate Table / 候选表

| # | store_name / 店铺 | masked_email / 脱敏邮箱 | domain / 域名 | state / 州 | city / 城市 | evidence_url | evidence_snippet / 证据片段 | exclusion_summary / 排除摘要 |
|---:|---|---|---|---|---|---|---|---|
| 1 | Gear Gaming Store Fayetteville | f***@geargamingstore.com | geargamingstore.com | AR | Fayetteville | https://hcunits.net/venues/63/ | unavailable: no evidence_snippet column / 不可用：无 evidence_snippet 字段 | excluded from live / 不进入 live |
| 2 | Game Cave Hot Springs | i***@thegamecavehs.com | thegamecavehs.com | AR | Hot Springs | https://thegamecavehs.com/ | unavailable: no evidence_snippet column / 不可用：无 evidence_snippet 字段 | excluded from live / 不进入 live |
| 3 | Game Quest Russellville | g***@gmail.com | gmail.com | AR | Russellville | https://gamequestar.com/ | unavailable: no evidence_snippet column / 不可用：无 evidence_snippet 字段 | duplicate-domain risk later / 后续有重复域名风险 |
| 4 | The Toy Shop WeHa | i***@thetoyshopweha.com | thetoyshopweha.com | CT | West Hartford | https://thetoyshopweha.com/pages/contact | unavailable: no evidence_snippet column / 不可用：无 evidence_snippet 字段 | outside primary rebuild states; excluded from live / 非补池主攻州；不进入 live |
| 5 | Treehouse Toys | f***@treehousetoys.com | treehousetoys.com | ME | Portland | https://treehousetoys.us/pages/contact-us | unavailable: no evidence_snippet column / 不可用：无 evidence_snippet 字段 | outside primary rebuild states; excluded from live / 非补池主攻州；不进入 live |
| 6 | Idaho Taters | s***@idahotaters.com | idahotaters.com | ID | Boise | https://www.idahotaters.com/ | unavailable: no evidence_snippet column / 不可用：无 evidence_snippet 字段 | outside primary rebuild states; excluded from live / 非补池主攻州；不进入 live |
| 7 | Dicehead Games and Comics | s***@dicehead.com | dicehead.com | TN | Cleveland | https://www.dicehead.com/service/ | unavailable: no evidence_snippet column / 不可用：无 evidence_snippet 字段 | excluded from live / 不进入 live |
| 8 | Knighthood Games | i***@knighthoodgames.com | knighthoodgames.com | TN | Cookeville | https://knighthoodgames.com/about-us/ | unavailable: no evidence_snippet column / 不可用：无 evidence_snippet 字段 | excluded from live / 不进入 live |
| 9 | Wooden Ogre Games | s***@woodenogregames.com | woodenogregames.com | KY | Paducah | https://legacy.fabtcg.com/en/locator/wooden-ogre-games/ | unavailable: no evidence_snippet column / 不可用：无 evidence_snippet 字段 | excluded from live / 不进入 live |
| 10 | Good Game Russellville | g***@gmail.com | gmail.com | AR | Russellville | https://legacy.fabtcg.com/en/locator/good-game/ | unavailable: no evidence_snippet column / 不可用：无 evidence_snippet 字段 | duplicate domain gmail.com / 重复域名 gmail.com |
| 11 | BigBoyToys | m***@gmail.com | gmail.com | TN | Gatlinburg | https://bigboytoysus.com/ | unavailable: no evidence_snippet column / 不可用：无 evidence_snippet 字段 | duplicate domain gmail.com / 重复域名 gmail.com |
| 12 | Kindness and Joy Toys Mountain View | h***@kindnessandjoytoys.com | kindnessandjoytoys.com | AR | Mountain View | https://kindnessandjoytoys.com/ | unavailable: no evidence_snippet column / 不可用：无 evidence_snippet 字段 | excluded from live / 不进入 live |
| 13 | Learning Railroad Toy and Teaching Store | l***@hotmail.com | hotmail.com | KY | Paducah | https://learningrailroad.com/ | unavailable: no evidence_snippet column / 不可用：无 evidence_snippet 字段 | excluded from live / 不进入 live |

## Header Check / Header 检查

中文：
生产代码已通过 header-only dry-run 和自有邮箱验证；当前 py_compile 再次通过。由于本次 dry-run gate 未通过，没有为客户候选生成 live-send 原始邮件。

English:
Production code previously passed header-only dry-run and owner-mailbox verification; current py_compile passed again. Because this dry-run gate failed, no live-send raw customer messages were generated.

## Non-Executed Items / 未执行事项

中文：
没有执行客户发信，没有写入 send_log，没有补发昨日退信，没有发送 B/B2/C/guessed_email，没有发送 suppression/hard bounce/delivery_issue/unsubscribe/duplicate domain。

English:
No customer email was sent, no send_log entry was written, no yesterday bounce resend was performed, and no B/B2/C/guessed_email, suppression, hard bounce, delivery_issue, unsubscribe, or duplicate-domain recipient was sent.

## Risks / 风险

中文：
候选不足 20，且缺少 evidence_snippet 字段。若强行发送，会违反本次明确规则。

English:
The candidate count is below 20 and the evidence_snippet field is missing. Sending anyway would violate this task's explicit rules.

## Next Step / 下一步

中文：
先补齐 evidence snippet 的数据结构或确认可使用 
notes 中的 snippet，再重新生成 dry-run 计划。

English:
First add the evidence snippet data structure or confirm that the snippet stored in 
notes may be used, then regenerate the dry-run plan.

