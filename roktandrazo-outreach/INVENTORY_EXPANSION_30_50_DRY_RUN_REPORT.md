# Inventory Expansion 30-50 Dry-Run Report / 库存扩池 30-50 条 Dry-Run 报告

Generated / 生成时间: 2026-07-07 15:45 Asia/Shanghai

## Report Self-Check / 报告自检

中文：
本报告生成前已检查：中英双语、包含中文解释、包含英文版本、未输出敏感信息、包含执行结果、包含未执行事项、包含风险、包含下一步、未把未完成事项写成已完成，并符合 Roktandrazo BD 自动化项目口径。

English:
Before this report was generated, it was checked for bilingual Chinese-English content, Chinese explanation, English version, no sensitive information, execution results, non-executed items, risks, next steps, no unfinished work marked complete, and alignment with the Roktandrazo BD automation project framing.


## Executive Summary / 执行摘要

中文：
已使用 `inventory_expansion_runner.py` 执行 50 条受控 dry-run。范围严格限制为 TN/AR/KY，来源包括现有 evidence_url 缺 snippet、历史 Google Maps 候选和 B2 官网候选。本轮没有写库，没有发信，没有 canary。

English:
A controlled 50-record dry-run was executed with `inventory_expansion_runner.py`. The scope was strictly limited to TN/AR/KY, using existing records missing snippets, historical Google Maps candidates, and B2 official-website candidates. This run did not write to DB, send email, or run canary.

## Command / 执行命令

中文：
执行时设置 `PYTHONIOENCODING=utf-8`，并输出到 `C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\output\inventory_expansion_30_50_dry_run_20260707_1544.json`。

English:
The run used `PYTHONIOENCODING=utf-8` and wrote output to `C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\output\inventory_expansion_30_50_dry_run_20260707_1544.json`.

```text
python inventory_expansion_runner.py --states TN,AR,KY --dry-run --mask-output --batch-limit 50 --require-official-domain --write-evidence-snippet --source existing_evidence_url_missing_snippet --source historical_google_maps_candidates --source b2_official_website --output output\inventory_expansion_30_50_dry_run_20260707_1544.json
```

## Results / 执行结果

| Metric / 指标 | Value / 数值 |
|---|---:|
| total_checked / 检查总数 | 50 |
| browser_verified_count / 浏览器验证 A0 数 | 1 |
| http_verified_count / HTTP 验证 A0 数 | 0 |
| new_A0_candidate_count / 新 A0 候选数 | 1 |
| still_B2_count / 仍为 B2 数 | 47 |
| C/contact_form_count / C 表单池数 | 0 |
| invalid_count / 无效数 | 1 |
| blocked_cloudflare_count / Cloudflare 或 403 阻断数 | 0 |
| duplicate_domain_count / 重复域名数 | 0 |
| would_write_count / 可写库候选数 | 1 |
| gap_to_20 / 写库后距 20 缺口 | 13 |
| gap_to_60 / 写库后距 60 缺口 | 53 |

## Masked Example / 脱敏示例

中文：
本轮发现 1 条可写库 A0 candidate：来源为 `existing_evidence_url_missing_snippet`，城市为 Cleveland, TN，masked email 为 `sa***@dicehead.com`，验证方式为 browser，原因是 `official_email_visible`。

English:
This run found 1 would-write A0 candidate: source `existing_evidence_url_missing_snippet`, city Cleveland, TN, masked email `sa***@dicehead.com`, method browser, reason `official_email_visible`.

## Sensitive Output Check / 敏感输出检查

中文：
dry-run JSON 中完整邮箱正则匹配数为 0。报告未输出 `.env`、SMTP/IMAP 密码、token、cookie 或 auth json。

English:
The dry-run JSON had 0 full-email regex matches. The report does not output `.env`, SMTP/IMAP password, token, cookie, or auth json.

## Non-Executed Items / 未执行事项

中文：
未执行 write-safe 写库；未执行客户 live send；未执行 canary；未运行 Google Maps scraping；未把 Google Maps 候选直接升级 A0。

English:
No write-safe DB write was performed; no customer live send was performed; no canary was performed; Google Maps scraping was not run; Google Maps candidates were not directly upgraded to A0.

## Risks / 风险

中文：
即使写入 1 条候选，strict pool 预计只有 7，仍低于 20 和 60。大多数候选仍是 B2，说明需要更多官网来源和更强的候选发现策略。

English:
Even if the 1 candidate is written, the strict pool is estimated to be only 7, still below 20 and 60. Most candidates remain B2, showing that more official-site sources and stronger candidate discovery are needed.

## Next Steps / 下一步

中文：
请先确认是否允许对这 1 条 would_write A0 candidate 执行 write-safe 写库；写库后仍不能 canary，需要继续扩池。

English:
Please confirm whether write-safe DB write is allowed for this 1 would-write A0 candidate. Even after writing it, canary is still not allowed and pool expansion must continue.
