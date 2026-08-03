# Inventory Rebuild To 60 Execution Report / 补池到 60 执行报告

Generated / 生成时间: 2026-07-07 13:06 Asia/Shanghai

## Report Self-Check / 报告自检

中文：
本报告生成前已检查：中英双语、中文解释、英文版本、无敏感信息、包含执行结果、包含未执行事项、包含风险、包含下一步、未把未完成事项写成已完成，并符合 BD 自动化项目口径。

English:
Before this report was generated, it was checked for bilingual Chinese-English content, Chinese explanation, English version, no sensitive information, execution results, non-executed items, risks, next steps, no unfinished work marked complete, and alignment with the BD automation project framing.

## Executive Summary / 执行摘要

中文：
已执行受控 TN/AR/KY 官网验证补池尝试，没有执行 Google Maps 泛扫，也没有全美随机跨州。共检查 20 条 TN/AR/KY B2/manual_review_needed 官网候选，初步识别 7 条可升级，但经过邮箱域名纠偏后保留 4 条为 A0，3 条因第三方邮箱域名降回 B2。最终严格 sendable_pool 为 5，未补到 60。

English:
A controlled TN/AR/KY official-site verification rebuild attempt was executed. No Google Maps broad scan and no nationwide random cross-state processing was performed. 20 TN/AR/KY B2/manual_review_needed official-site candidates were checked. 7 were initially identified as upgrade candidates, but after email-domain correction only 4 remained A0 and 3 were downgraded back to B2 because of third-party email domains. Final strict sendable_pool is 5, so the pool was not rebuilt to 60.

## Execution Result / 执行结果

| Metric / 指标 | Count / 数量 |
|---|---:|
| Primary-state B2 checked / 检查 TN/AR/KY B2 | 20 |
| Initial A0 upgrades / 初步升级 A0 | 7 |
| Domain audit downgraded / 域名纠偏降级 | 3 |
| Net new A0 kept / 净新增保留 A0 | 4 |
| Kept or returned to B2 / 保留或退回 B2 | 16 |
| New C / 新增 C | 0 |
| Final strict sendable_pool / 最终严格可发池 | 5 |
| Inventory target / 库存目标 | 60 |

## Kept A0 Examples / 保留 A0 示例

| store_name / 店铺 | masked_email / 脱敏邮箱 | state / 州 | city / 城市 |
|---|---|---|---|
| BigBoyToys | i***@bigboytoysus.com | TN | Gatlinburg |
| Hoth Toys | h***@gmail.com | TN | Johnson City |
| Kindness and Joy Toys | h***@kindnessandjoytoys.com | AR | Fayetteville |
| Kindness and Joy Toys Mountain View | h***@kindnessandjoytoys.com | AR | Mountain View |

## Downgraded Examples / 降级示例

| store_name / 店铺 | masked_email / 脱敏邮箱 | reason / 原因 |
|---|---|---|
| Kryptonite Character Store | i***@kryptonitecharacterstore.zendesk.com | third_party_email_domain / 第三方邮箱域名 |
| Gear Gaming Store Fayetteville | f***@geargamingstore.com | third_party_email_domain / 第三方邮箱域名 |
| Wooden Ogre Games | i***@indiantypefoundry.com | third_party_email_domain / 第三方邮箱域名 |

## Non-Executed Items / 未执行事项

中文：
未执行 Google Maps scraping；未全美泛扫；未随机跨州；未把 Google Maps 候选直接升级 A0；未把 B2、C、guessed_email 直接发送；未客户 live send。

English:
No Google Maps scraping was performed; no nationwide broad scan was performed; no random cross-state processing was performed; Google Maps candidates were not directly upgraded to A0; B2, C, or guessed_email were not sent; no customer live send was performed.

## Risks / 风险

中文：
HTTP 官网验证会漏掉需要浏览器渲染或人工判断的邮箱。当前严格池仍只有 5，离 60 差 55。部分通用邮箱虽然在官网页面出现，但后续 live send 前仍建议人工抽查。

English:
HTTP official-site verification may miss emails that require browser rendering or manual judgment. The strict pool is still only 5, short of 60 by 55. Some generic emails appeared on official pages, but manual spot checks are still recommended before live send.

## Next Step / 下一步

中文：
需要继续补池：要么增加受控浏览器验证并支持 TN/AR/KY 过滤，要么人工审核 Top B2。达到严格池 >=20 且在发信窗口内后，才可重新 dry-run 并考虑 live send；达到 >=60 才算完成库存目标。

English:
Inventory rebuild must continue: either add controlled browser verification with TN/AR/KY filtering, or manually review top B2 candidates. Only after strict pool is >=20 and the send window is open may dry-run be regenerated and live send considered; inventory target is complete only when strict pool is >=60.
