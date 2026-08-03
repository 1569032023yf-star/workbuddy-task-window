# Strict Sendable Pool Recount / 严格可发池重算

Generated / 生成时间: 2026-07-07 13:06 Asia/Shanghai

## Report Self-Check / 报告自检

中文：
本报告生成前已检查：中英双语、中文解释、英文版本、无敏感信息、包含执行结果、包含未执行事项、包含风险、包含下一步、未把未完成事项写成已完成，并符合 BD 自动化项目口径。

English:
Before this report was generated, it was checked for bilingual Chinese-English content, Chinese explanation, English version, no sensitive information, execution results, non-executed items, risks, next steps, no unfinished work marked complete, and alignment with the BD automation project framing.

## Executive Summary / 执行摘要

中文：
schema 修复、原候选回填和 TN/AR/KY B2 官网验证后，严格 sendable_pool 为 5。该数量低于 live send 最低 gate 20，也低于库存目标 60，因此不得执行 live send，库存仍未完成。

English:
After schema fix, original candidate backfill, and TN/AR/KY B2 official-site verification, strict sendable_pool is 5. This is below the live send minimum gate of 20 and below the inventory target of 60, so live send must not run and inventory rebuild is not complete.

## Strict Criteria / 严格标准

中文：
严格池必须同时满足：A0 或 approved_manual_send、有 email、有 evidence_url、有 evidence_snippet、非 guessed_email、未发送、非 suppression、非 bounced、非 delivery_issue、非 duplicate domain、非 duplicate store、非 risky Microsoft 365 / Exchange MX，并且 state 在 TN/AR/KY。

English:
The strict pool must satisfy all conditions: A0 or approved_manual_send, has email, has evidence_url, has evidence_snippet, not guessed_email, not sent, not suppression, not bounced, not delivery_issue, not duplicate domain, not duplicate store, not risky Microsoft 365 / Exchange MX, and state in TN/AR/KY.

## Count / 数量

| Metric / 指标 | Count / 数量 |
|---|---:|
| Strict candidates before domain dedup / 去重前严格候选 | 6 |
| Strict sendable_pool after dedup / 去重后严格可发池 | 5 |
| Required for controlled live send / live send 最低要求 | 20 |
| Inventory target / 库存目标 | 60 |
| Gap to 20 / 距离 20 缺口 | 15 |
| Gap to 60 / 距离 60 缺口 | 55 |

## Strict Candidate List / 严格候选清单

| store_name / 店铺 | masked_email / 脱敏邮箱 | state / 州 | city / 城市 | status / 状态 |
|---|---|---|---|---|
| Kindness and Joy Toys | h***@kindnessandjoytoys.com | AR | Fayetteville | counted / 计入 |
| Kindness and Joy Toys Mountain View | h***@kindnessandjoytoys.com | AR | Mountain View | duplicate domain excluded / 重复域名排除 |
| Learning Railroad Toy and Teaching Store | l***@hotmail.com | KY | Paducah | counted / 计入 |
| Knighthood Games | i***@knighthoodgames.com | TN | Cookeville | counted / 计入 |
| BigBoyToys | i***@bigboytoysus.com | TN | Gatlinburg | counted / 计入 |
| Hoth Toys | h***@gmail.com | TN | Johnson City | counted / 计入 |

## Non-Executed Items / 未执行事项

中文：
未执行 live send；未写入 send_log；未绕过 duplicate domain；未发送 B2/C/guessed_email；未发送 suppression、bounce、delivery_issue 或 unsubscribe。

English:
No live send was performed; no send_log was written; duplicate-domain exclusion was not bypassed; B2/C/guessed_email were not sent; suppression, bounce, delivery_issue, or unsubscribe contacts were not sent.

## Risks / 风险

中文：
严格池只有 5，不能支撑今日 20 封目标。若强发会违反 evidence gate、数量 gate 和窗口 gate。

English:
The strict pool is only 5 and cannot support today's 20-email target. Forcing sends would violate the evidence gate, count gate, and window gate.

## Next Step / 下一步

中文：
继续在 TN/AR/KY 做官网验证补池，优先人工/浏览器复核 B2，直到严格池 >=60；若只为今日发送，至少需要严格池 >=20 且窗口重新打开。

English:
Continue compliant TN/AR/KY official-site verification, prioritizing manual/browser review for B2, until strict pool is >=60. For today-only sending, strict pool must at least be >=20 and the send window must reopen.
