# Inventory Rebuild To 60 Report / 库存补池到 60 报告

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
本轮没有把 sendable_pool 补到 60，也没有执行会写库的库存恢复。原因是当前合规 gate 未通过：缺失必读规则文件、数据库无 evidence_snippet 字段、现有自动 verifier 没有州过滤参数，直接运行会有跨州或全量处理风险。

English:
This run did not rebuild sendable_pool to 60 and did not perform inventory restoration writes. The reason is that compliant gates did not pass: required rule files were missing, the database has no evidence_snippet field, and the existing automatic verifier has no state filter parameter, so running it directly risks cross-state or broad processing.

## Inventory Counts / 库存数量

中文：
项目现有 sendable_pool 为 14；带 evidence_url 的候选为 13；严格要求 evidence_snippet 字段时为 0。TN/AR/KY 中可作为人工/网站验证来源的 manual_review_needed 且有官网候选共 13 条。

English:
The existing project sendable_pool is 14; candidates with evidence_url count 13; if the evidence_snippet field is strictly required, the count is 0. In TN/AR/KY, there are 13 manual_review_needed candidates with official websites that could be used as manual or website-verification sources.

| Metric / 指标 | Count / 数量 |
|---|---:|
| Existing project sendable_pool / 项目现有可发池 | 14 |
| Strict evidence_url candidates / 有 evidence_url 的候选 | 13 |
| Strict evidence_snippet-compliant candidates / evidence_snippet 合规候选 | 0 |
| Target / 目标 | 60 |
| Gap to 60 by project definition / 按项目口径到 60 的缺口 | 46 |
| Gap to 60 by strict evidence_snippet / 按 evidence_snippet 口径到 60 的缺口 | 60 |
| New A0 added by this run / 本轮新增 A0 | 0 |
| New B2 added by this run / 本轮新增 B2 | 0 |
| New C added by this run / 本轮新增 C | 0 |

## Primary State Source Pool / 主攻州来源池

| State / 州 | manual_review_needed with website / 有官网待人工审核 |
|---|---:|
| TN | 7 |
| AR | 2 |
| KY | 4 |
| Total / 合计 | 13 |

## Tooling Assessment / 工具评估

中文：
rowser_verifier.py 会写库升级 A0，但没有州过滤参数。ast_lead_discovery.py 有 --from-cities 参数说明，但当前主流程没有实现该分支；--from-b2 是随机抽取，会违反只做 TN/AR/KY 的约束。因此本轮没有运行这些会导致范围偏移的流程。

English:
rowser_verifier.py can write database A0 upgrades but has no state filter parameter. ast_lead_discovery.py documents --from-cities, but the current main flow does not implement that branch; --from-b2 samples randomly and would violate the TN/AR/KY-only constraint. Therefore, this run did not execute those workflows that could drift out of scope.

## Non-Executed Items / 未执行事项

中文：
没有执行 Google Maps scraping；没有全美泛扫；没有随机跨州；没有把 FL/UT/SC 混入主攻州；没有把 Google Maps 候选直接升级 A0；没有把 B2 或 guessed email 当作 A0；没有写入库存恢复结果。

English:
No Google Maps scraping was performed; no nationwide broad scan was performed; no random cross-state processing was performed; FL/UT/SC were not mixed into the primary states; Google Maps candidates were not directly upgraded to A0; B2 or guessed email was not treated as A0; no inventory restoration results were written.

## Risks / 风险

中文：
如果直接运行现有 verifier，可能跨州处理或写入没有 evidence_snippet 字段的 A0，违反本次补池规则。当前库存未到 60。

English:
Running the current verifier directly could process out-of-state leads or write A0 records without an evidence_snippet field, violating this rebuild rule. The inventory has not reached 60.

## Next Step / 下一步

中文：
建议先增加受控补池工具能力：支持 TN/AR/KY 过滤、写入 evidence_snippet 字段或明确 notes 片段映射、只将官网真实邮箱 + evidence_url + evidence_snippet 升级 A0。完成后再执行补池到 60。

English:
Recommended next step is to add controlled rebuild tooling: support TN/AR/KY filtering, write an evidence_snippet field or explicitly map snippets from 
notes, and only upgrade official-site real emails with evidence_url and evidence_snippet to A0. After that, rebuild to 60 can be executed.


