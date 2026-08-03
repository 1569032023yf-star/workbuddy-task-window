# Evidence Snippet Backfill Report / evidence_snippet 回填报告

Generated / 生成时间: 2026-07-07 13:06 Asia/Shanghai

## Report Self-Check / 报告自检

中文：
本报告生成前已检查：中英双语、中文解释、英文版本、无敏感信息、包含执行结果、包含未执行事项、包含风险、包含下一步、未把未完成事项写成已完成，并符合 BD 自动化项目口径。

English:
Before this report was generated, it was checked for bilingual Chinese-English content, Chinese explanation, English version, no sensitive information, execution results, non-executed items, risks, next steps, no unfinished work marked complete, and alignment with the BD automation project framing.

## Executive Summary / 执行摘要

中文：
已完成 DB 备份、最小 schema 迁移和现有 13 条 evidence_url 候选的 evidence_snippet 回填审计。新增字段为 evidence_snippet TEXT、evidence_checked_at TEXT、evidence_method TEXT。本轮没有盲目从 notes 全量复制；只在官方 evidence_url 页面能确认邮箱时回填。

English:
DB backup, minimal schema migration, and evidence_snippet audit for the existing 13 evidence_url candidates were completed. Added fields were evidence_snippet TEXT, evidence_checked_at TEXT, and evidence_method TEXT. This run did not blindly copy all notes; snippets were backfilled only when the email could be confirmed on the official evidence_url page.

## DB Backup / DB 备份

中文：
迁移前已使用 SQLite backup API 创建一致性备份。

English:
Before migration, a consistent backup was created using the SQLite backup API.

C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\backups\evidence_snippet_schema_20260707_125936\bd_leads_backup.db

## Schema Migration / Schema 迁移

中文：
已确认主表为 leads，并在缺失时添加了 evidence_snippet、evidence_checked_at、evidence_method。未删除旧字段，未覆盖 notes，未重命名现有字段。

English:
The main table was confirmed as leads, and evidence_snippet, evidence_checked_at, and evidence_method were added when missing. No old fields were deleted, notes were not overwritten, and existing fields were not renamed.

| Field / 字段 | Status / 状态 |
|---|---|
| evidence_snippet | Added / 已新增 |
| evidence_checked_at | Added / 已新增 |
| evidence_method | Added / 已新增 |

## Backfill Result / 回填结果

中文：
对现有 13 条有 evidence_url 的候选逐条审计。4 条可在官方 evidence_url 确认邮箱并回填，9 条因第三方 evidence_url、抓取失败、403 或 evidence_url 未出现精确邮箱而降为 B2/manual_review_needed。

English:
The existing 13 candidates with evidence_url were audited one by one. 4 were confirmed on official evidence_url pages and backfilled; 9 were downgraded to B2/manual_review_needed because of third-party evidence_url, fetch failure, 403, or no exact email found on the evidence_url.

| Metric / 指标 | Count / 数量 |
|---|---:|
| total_checked / 检查总数 | 13 |
| backfilled_count / 回填数 | 4 |
| rejected_count / 拒绝数 | 9 |
| downgraded_to_B2_count / 降为 B2 数 | 9 |
| kept_A0_count / 保留 A0 数 | 4 |

## Masked Examples / 脱敏示例

| Example / 示例 | Result / 结果 | Reason / 原因 |
|---|---|---|
| f***@geargamingstore.com | Downgraded to B2 / 降为 B2 | evidence_url_not_official_domain |
| i***@thetoyshopweha.com | Backfilled and kept A0 / 已回填并保留 A0 | exact_email_found_on_official_evidence_url |
| i***@knighthoodgames.com | Backfilled and kept A0 / 已回填并保留 A0 | exact_email_found_on_official_evidence_url |
| h***@kindnessandjoytoys.com | Downgraded to B2 in original pass / 原回填批次降为 B2 | exact_email_not_found_on_evidence_url |

## Non-Executed Items / 未执行事项

中文：
未发送客户邮件；未输出完整客户邮箱；未输出完整 DB 内容；未输出 .env、SMTP/IMAP 密码、token、cookie 或 auth json。

English:
No customer email was sent; no full customer email list was output; no full DB content was output; and no .env, SMTP/IMAP password, token, cookie, or auth json was output.

## Risks / 风险

中文：
HTTP 抓取可能受站点防护影响，部分真实邮箱可能因 fetch 失败而进入 B2，需要人工或浏览器复核。第三方目录页不作为 A0 证据。

English:
HTTP fetching may be affected by site protections, so some real emails may have been moved to B2 because fetch failed and may need manual or browser review. Third-party directory pages were not accepted as A0 evidence.

## Next Step / 下一步

中文：
继续使用严格 evidence gate 重算 sendable_pool，并只在严格池满足 >=20 且发信窗口打开时考虑 live send。

English:
Continue by recounting sendable_pool with the strict evidence gate, and only consider live send when strict pool is >=20 and the send window is open.
