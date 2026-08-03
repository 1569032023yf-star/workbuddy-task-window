# Inventory Tool Patch Report / 库存扩池工具改造报告

Generated / 生成时间: 2026-07-07 15:45 Asia/Shanghai

## Report Self-Check / 报告自检

中文：
本报告生成前已检查：中英双语、包含中文解释、包含英文版本、未输出敏感信息、包含执行结果、包含未执行事项、包含风险、包含下一步、未把未完成事项写成已完成，并符合 Roktandrazo BD 自动化项目口径。

English:
Before this report was generated, it was checked for bilingual Chinese-English content, Chinese explanation, English version, no sensitive information, execution results, non-executed items, risks, next steps, no unfinished work marked complete, and alignment with the Roktandrazo BD automation project framing.


## Executive Summary / 执行摘要

中文：
本轮新增受控 wrapper：`inventory_expansion_runner.py`。它默认 dry-run、默认 masked output、默认 TN/AR/KY 过滤、默认不写库、不发信、不做 canary。该工具用于在 canary 之前验证库存扩池候选，而不是恢复自动群发。

English:
This run added a controlled wrapper: `inventory_expansion_runner.py`. It defaults to dry-run, masked output, TN/AR/KY filtering, no DB writes, no sending, and no canary. The tool is for validating inventory expansion candidates before canary, not for restoring automated bulk sending.

## Files Changed / 已改造文件

中文：
新增文件：`inventory_expansion_runner.py`。未直接大改 `fast_lead_discovery.py` 或 `browser_verifier.py`。相关原文件和报告已备份到 `C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\backups\tool_patch_20260707_153659`。

English:
Added file: `inventory_expansion_runner.py`. `fast_lead_discovery.py` and `browser_verifier.py` were not broadly modified. Related original files and reports were backed up to `C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\backups\tool_patch_20260707_153659`.

## Supported Controls / 已支持控制项

中文：
工具支持 `--states TN,AR,KY`、`--dry-run`、`--write-safe`、`--confirm-write-safe CONFIRM_WRITE_SAFE`、`--mask-output`、`--batch-limit 50`、`--require-official-domain`、`--write-evidence-snippet`，以及三类来源：`existing_evidence_url_missing_snippet`、`historical_google_maps_candidates`、`b2_official_website`。

English:
The tool supports `--states TN,AR,KY`, `--dry-run`, `--write-safe`, `--confirm-write-safe CONFIRM_WRITE_SAFE`, `--mask-output`, `--batch-limit 50`, `--require-official-domain`, `--write-evidence-snippet`, and the three sources: `existing_evidence_url_missing_snippet`, `historical_google_maps_candidates`, and `b2_official_website`.

## Browser Verification / 浏览器验证

中文：
工具支持 HTTP-first 验证，并在需要时使用 Playwright browser fallback。dry-run 中发现的可写 A0 candidate 来自 browser verification，说明浏览器路径可用。

English:
The tool supports HTTP-first verification and uses Playwright browser fallback when needed. The writable A0 candidate found in dry-run came from browser verification, confirming the browser path is usable.

## Write-Safe Separation / 写库隔离

中文：
默认不写库。`--write-safe` 必须同时提供 `--confirm-write-safe CONFIRM_WRITE_SAFE` 才能写库。写库路径会备份 DB，并写入 `evidence_url`、`evidence_snippet`、`evidence_checked_at`、`evidence_method=website_browser_verified`、`email_verified_on_official_site=1` 等字段。

English:
The default mode does not write to DB. `--write-safe` requires `--confirm-write-safe CONFIRM_WRITE_SAFE` before any DB write. The write path backs up the DB and writes fields including `evidence_url`, `evidence_snippet`, `evidence_checked_at`, `evidence_method=website_browser_verified`, and `email_verified_on_official_site=1`.

## Sensitive Output Protection / 敏感输出保护

中文：
输出 JSON 删除内部写库邮箱字段，只保留 masked email，并对 `evidence_snippet` 中的邮箱做掩码。本轮 dry-run JSON 的完整邮箱正则匹配数为 0。

English:
The output JSON removes the internal write-email field, keeps only masked email, and masks emails inside `evidence_snippet`. The full-email regex match count in this dry-run JSON was 0.

## Non-Executed Items / 未执行事项

中文：
未执行 write-safe 写库；未执行客户 live send；未执行 canary；未运行 Google Maps scraping；未恢复 daily live 20。

English:
No write-safe DB write was performed; no customer live send was performed; no canary was performed; Google Maps scraping was not run; daily live 20 was not restored.

## Risks / 风险

中文：
wrapper 是新工具，已通过 `py_compile` 和 50 条 dry-run，但在正式写库前仍需要用户确认，并建议先审阅 dry-run 输出。

English:
The wrapper is a new tool. It passed `py_compile` and a 50-record dry-run, but user confirmation is still required before any production DB write, and the dry-run output should be reviewed first.

## Next Steps / 下一步

中文：
下一步如你确认写库，可对 dry-run 中 1 条 would_write A0 candidate 执行 write-safe；写库后仍预计 strict pool 只有 7，不足以 canary。

English:
If you confirm DB write, the next step is to run write-safe for the 1 would-write A0 candidate from dry-run. Even after that write, strict pool is estimated to be only 7, still below canary requirements.
