# Fast Inventory Expansion Tool Plan / 快速库存扩池工具计划

Generated / 生成时间: 2026-07-07 15:45 Asia/Shanghai

## Report Self-Check / 报告自检

中文：
本报告生成前已检查：中英双语、包含中文解释、包含英文版本、未输出敏感信息、包含执行结果、包含未执行事项、包含风险、包含下一步、未把未完成事项写成已完成，并符合 Roktandrazo BD 自动化项目口径。

English:
Before this report was generated, it was checked for bilingual Chinese-English content, Chinese explanation, English version, no sensitive information, execution results, non-executed items, risks, next steps, no unfinished work marked complete, and alignment with the Roktandrazo BD automation project framing.


## Executive Summary / 执行摘要

中文：
当前工具可以复用，但不能直接大规模写库。`fast_lead_discovery.py` 支持 HTTP-first 和 Playwright fallback，并能产生 `evidence_url` 与 `evidence_snippet`；`browser_verifier.py` 支持浏览器验证，但旧升级路径不适合直接大规模使用。本轮选择新增 wrapper 做最小改造。

English:
The current tools are reusable but should not be used for broad direct DB writes. `fast_lead_discovery.py` supports HTTP-first scanning plus Playwright fallback and can produce `evidence_url` and `evidence_snippet`; `browser_verifier.py` supports browser verification, but its legacy upgrade path is not suitable for broad direct use. This run chose a new wrapper as the minimal patch.

## Required Capabilities / 必须能力

中文：
扩池工具必须支持 TN/AR/KY 过滤、city queue、keyword queue、HTTP-first verification、browser fallback、email extraction、`evidence_snippet` extraction、A0/B2/C/Invalid 分类、duplicate domain 排除、write-safe mode、dry-run mode 和 batch limit。

English:
The expansion tool must support TN/AR/KY filtering, city queue, keyword queue, HTTP-first verification, browser fallback, email extraction, `evidence_snippet` extraction, A0/B2/C/Invalid classification, duplicate-domain exclusion, write-safe mode, dry-run mode, and batch limit.

## Current Tool Status / 当前工具状态

中文：
`fast_lead_discovery.py` 可以通过受控 `--input` 实现 TN/AR/KY 过滤，但 `--from-b2` 当前是随机抽样，不适合作为正式补池入口。`browser_verifier.py` 可运行 Playwright，但需要脱敏输出和新字段写入保护。

English:
`fast_lead_discovery.py` can enforce TN/AR/KY filtering through controlled `--input`, but current `--from-b2` randomly samples and is not suitable as the formal rebuild entry point. `browser_verifier.py` can run Playwright but needs masked output and new-field write protection.

## Proposed Changes / 建议改造

中文：
采用 `inventory_expansion_runner.py` 作为受控入口，支持 `--states`、`--source`、`--batch-limit`、`--dry-run`、`--write-safe`、`--mask-output` 和 `--require-official-domain`。

English:
Use `inventory_expansion_runner.py` as the controlled entry point, supporting `--states`, `--source`, `--batch-limit`, `--dry-run`, `--write-safe`, `--mask-output`, and `--require-official-domain`.

## Non-Executed Items / 未执行事项

中文：
计划阶段未写库、未发信、未运行 Google Maps scraping、未恢复长期自动群发。

English:
The planning stage did not write to DB, send email, run Google Maps scraping, or restore long-term automated bulk sending.

## Risks / 风险

中文：
如果直接运行旧 `browser_verifier.py --batch`，仍可能输出完整邮箱且不符合新字段 gate；如果直接运行 `fast_lead_discovery.py --from-b2`，可能绕过 TN/AR/KY 过滤。

English:
Running legacy `browser_verifier.py --batch` directly may still output full emails and fail the new-field gate; running `fast_lead_discovery.py --from-b2` directly may bypass TN/AR/KY filtering.

## Next Steps / 下一步

中文：
使用 wrapper 先跑 30-50 条 dry-run，再由用户确认是否 write-safe 写库。

English:
Use the wrapper to run a 30-50 record dry-run first, then ask the user to confirm whether write-safe DB writing is allowed.
