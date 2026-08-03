# WorkBuddy Evidence Crosscheck Report / WorkBuddy 证据交叉验证报告

Generated / 生成时间: 2026-07-07 14:45 Asia/Shanghai

## Report Self-Check / 报告自检

中文：
本报告生成前已检查：中英双语、中文解释、英文版本、无敏感信息、包含执行结果、包含未执行事项、包含风险、包含下一步、未把未完成事项写成已完成，并符合 BD 自动化项目口径。

English:
Before this report was generated, it was checked for bilingual Chinese-English content, Chinese explanation, English version, no sensitive information, execution results, non-executed items, risks, next steps, no unfinished work marked complete, and alignment with the BD automation project framing.

## Executive Summary / 执行摘要

中文：
已读取 WorkBuddy artifact recovery 目录中的 7 份恢复文档，并用当前目录、脚本存在性、skill 目录、工具目录、package 配置和历史产物文件做交叉验证。验证结果显示：生产目录实际存在关键工具；Google Maps 工具是普通工具而非 skill；Playwright/httpx/BeautifulSoup 已安装；项目级 `.workbuddy/skills` 不存在；用户级 `.workbuddy/skills` 存在 94 个目录。本轮未执行 live send、未采集、未修改 DB。

English:
The 7 documents in the WorkBuddy artifact recovery directory were read, then crosschecked against current directories, script existence, skill directories, tool directories, package configuration, and historical artifact files. Results show that key tools actually exist in the production directory; Google Maps tools are plain tools, not skills; Playwright/httpx/BeautifulSoup are installed; project-level `.workbuddy/skills` does not exist; and user-level `.workbuddy/skills` contains 94 directories. This run did not perform live send, collection, or DB modification.

## Files Read / 已读取文件

中文：
已读取恢复目录中的 `CODEX_README_NEXT.md`、`HISTORICAL_REPORTS_MAP.md`、`LEGACY_TO_CURRENT_DIFF.md`、`PROJECT_SKILLS_RECONSTRUCTED.md`、`SKILLS_SELF_CHECK_REPORT.md`、`WORKBUDDY_ARTIFACT_INDEX.md`、`WORKBUDDY_SKILLS_EXPORT.md`。

English:
Read `CODEX_README_NEXT.md`, `HISTORICAL_REPORTS_MAP.md`, `LEGACY_TO_CURRENT_DIFF.md`, `PROJECT_SKILLS_RECONSTRUCTED.md`, `SKILLS_SELF_CHECK_REPORT.md`, `WORKBUDDY_ARTIFACT_INDEX.md`, and `WORKBUDDY_SKILLS_EXPORT.md` from the recovery directory.

## Evidence Checked / 已检查证据

| Evidence / 证据 | Result / 结果 |
|---|---|
| `.workbuddy/memory` directory / `.workbuddy/memory` 目录 | Found; actual memory file is UUID-named, not `MEMORY.md` / 已找到；实际 memory 文件为 UUID 命名，不是 `MEMORY.md` |
| Project `.workbuddy/skills` | Not found / 未找到 |
| `roktandrazo-outreach/.workbuddy/automations` | Found / 已找到 |
| Core scripts in production / 生产核心脚本 | Found / 已找到 |
| `tools/google-maps-scraper` | Found / 已找到 |
| User WorkBuddy skills / 用户级 WorkBuddy skills | 94 directories / 94 个目录 |
| Playwright package / Playwright 包 | 1.60.0 installed / 已安装 |
| httpx package / httpx 包 | 0.28.1 installed / 已安装 |
| beautifulsoup4 package / beautifulsoup4 包 | 4.15.0 installed / 已安装 |
| Scrapy/Crawlee/Selenium package / Scrapy/Crawlee/Selenium 包 | Not shown by pip check / pip 检查未显示 |
| PowerShell command history matching gmaps/playwright / 命令历史匹配 | No matching lines returned / 未返回匹配行 |

## Confirmed Findings / 已确认发现

中文：
生产目录实际存在 `browser_verifier.py`、`fast_lead_discovery.py`、`pool_analysis.py`、`city_selector_v2.py`、`b_pool_import.py`、`b_pool_audit_v2.py`、`agent_reply_monitor.py`、`agent_daily_report.py`、`scorer_v2.py`、`daily_operator_auto.py` 和 `agent_bounce_auditor.py`。这与部分恢复文档中“当前系统缺少这些工具”的表述不一致，应以当前目录为准。

English:
The production directory actually contains `browser_verifier.py`, `fast_lead_discovery.py`, `pool_analysis.py`, `city_selector_v2.py`, `b_pool_import.py`, `b_pool_audit_v2.py`, `agent_reply_monitor.py`, `agent_daily_report.py`, `scorer_v2.py`, `daily_operator_auto.py`, and `agent_bounce_auditor.py`. This conflicts with some recovery-document statements that the current system lacks those tools, so current directory evidence should take precedence.

## Google Maps Finding / Google Maps 发现

中文：
`tools/google-maps-scraper` 中存在 `gmaps_fast_poc.py`、`gmaps_playwright_poc.py`、`inventory_shift_ar_ky.py`、`inventory_shift_live.py`、`queries_tn.txt` 和 `gmaps-scraper.exe`。这些是普通工具，不是 skill。历史 POC 报告和 CSV 存在，但 Google Maps 只允许候选发现，不能直接升级 A0。

English:
`tools/google-maps-scraper` contains `gmaps_fast_poc.py`, `gmaps_playwright_poc.py`, `inventory_shift_ar_ky.py`, `inventory_shift_live.py`, `queries_tn.txt`, and `gmaps-scraper.exe`. These are plain tools, not skills. Historical POC reports and CSV files exist, but Google Maps may only be used for candidate discovery and must not directly upgrade to A0.

## Skill Finding / Skill 发现

中文：
用户级 skill 目录中已验证 `us-retail-lead-collector`、IMAP/SMTP skill、`cn-ecommerce-search` 和 `ecommerce-copywriter` 的 `SKILL.md` 存在。其中 `us-retail-lead-collector` 标记为 `disable: true`，不得未经确认启用。

English:
The user-level skill directory was verified to contain `SKILL.md` for `us-retail-lead-collector`, the IMAP/SMTP skill, `cn-ecommerce-search`, and `ecommerce-copywriter`. `us-retail-lead-collector` is marked `disable: true` and must not be enabled without confirmation.

## Actions Taken / 已执行动作

中文：
已更新生产项目的 `PROJECT_SKILLS.md`，将已验证的 16 项实际能力、Google Maps 工具定位、skill 目录状态、证据 gate 和报告规则写入当前项目文档。

English:
Updated production `PROJECT_SKILLS.md` with the verified 16 actual capabilities, Google Maps tool status, skill directory status, evidence gate, and report rules.

## Non-Executed Items / 未执行事项

中文：
未执行客户 live send；未运行 Google Maps；未运行 browser verifier；未修改 DB；未启用 disabled skill；未读取或输出 `.env`、SMTP/IMAP 密码、token、cookie 或 auth json。

English:
No customer live send was performed; Google Maps was not run; browser verifier was not run; DB was not modified; disabled skills were not enabled; no `.env`, SMTP/IMAP password, token, cookie, or auth json was read or output.

## Risks / 风险

中文：
恢复包文档中存在 mojibake 和部分过期判断，不能无条件照搬。某些历史 CSV 包含完整邮箱，后续读取时必须脱敏。Google Maps POC 产物是候选来源，不是 A0 证据。

English:
Recovery-package documents contain mojibake and some outdated judgments, so they must not be copied blindly. Some historical CSV files contain full email addresses and must be masked if read later. Google Maps POC artifacts are candidate sources, not A0 evidence.

## Next Step / 下一步

中文：
下一步如要继续补池到 60，应先基于当前 `PROJECT_SKILLS.md` 设计受控迁移/集成：给 `browser_verifier.py` 或 fast discovery 添加 TN/AR/KY 过滤、evidence_snippet 写入和敏感输出保护；然后 dry-run，再决定是否写库。

English:
For the next rebuild-to-60 step, design controlled migration/integration based on the current `PROJECT_SKILLS.md`: add TN/AR/KY filtering, evidence_snippet writing, and sensitive-output protection to `browser_verifier.py` or fast discovery; then dry-run before deciding whether to write DB.

