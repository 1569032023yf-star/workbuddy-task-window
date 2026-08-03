# Project Memory

## Roktandrazo US Retail Store Lead Collection

### Project Goal
为 roktandrazo 拼图类产品寻找美国线下零售门店的公开商务联系邮箱或联系表单。

### Target Store Types
独立玩具店 / 桌游拼图店 / 卡牌店 / 礼品店 / 博物馆商店 / 书店礼品区 / 国家公园游客中心礼品店 / 手工艺爱好店 / 小镇综合商店 / 乡村商店 / 旅游区综合商店 / 邮政+礼品混合店

### Collection Strategy: State Deep Coverage V2
- **主攻州**：Tennessee (TN), Arkansas (AR), Kentucky (KY)
- **第二批（暂不主攻）**：Florida (FL), Utah (UT), South Carolina (SC)
- 不随机跨州，不全美泛扫；临时跨州须标记 emergency_recovery
- 下午库存班次 Asia/Shanghai 13:30–17:30，目标 sendable_pool >= 60
- 采集入口：Google Maps → Facebook → Official Website → Chamber of Commerce → Tourism Directory → Web Search
- source_channel: google_maps / facebook_page / official_website / chamber_directory / tourism_directory / main_street_directory / web_search / manual_seed / emergency_recovery

### Lead Scoring V2
- **A0**: 官网可访问 + 官网邮箱(非第三方) + 实体零售 + 产品匹配 + evidence_url + evidence_snippet + 未suppress + 未发送
- **A1**: MX有效猜测邮箱
- **B/B2**: 猜测邮箱(不可自动发，需审核) / 只有contact form
- **C**: 非实体零售 / 制造商 / 官网不完整 / contact_form_pool

### Status Fields
new / reviewed / drafted / sent / replied / bounced / unsubscribed / do_not_contact

### City Strategy (Updated 2026-07-24)
"农村包围城市"：small towns > tourist towns > national park gateways > college towns > historic towns > affluent suburbs > large city outskirts. 已覆盖 60+ 城市（Phase 0-3 + Phase 3 扩容，详见 daily logs）。规则文档: CITY_EXPANSION_RULES.md

### Discovery Architecture (2026-07-24)
- **discovery/ package**: SearchProvider ABC → GooglePlacesProvider / BrowserMapsProvider / MockPlacesProvider
- **browser_maps provider**: Playwright-based Google Maps scraper, no API key needed
  - `discovery/providers/browser_maps_scraper.py`: standalone scraper (user runs manually)
  - `discovery/providers/browser_maps.py`: SearchProvider-compatible interface
  - Two modes: FILE (read JSON) / DIRECT (scrape inline with Playwright)
- **Pipeline**: browser_maps → lead_discovery_results → dedup → website visit → email extract → history_crosscheck → bd_db.insert_lead()
- **Provider activation**: `$env:DISCOVERY_PROVIDER = "browser_maps"` or registered in base.py load_provider()
- **Integration test**: `test_browser_maps_integration.py` (test DB only, safe)
- **Runbook**: `RUNBOOK_BROWSER_MAPS_DISCOVERY.md`
- Status: 代码就绪，待用户在本地终端执行采集验证
- 约束: 无 API key，无付费 API，仅浏览器采集

### Outreach Automation System
- 主目录: `roktandrazo-outreach/`（SQLite + scoring + email drafting + SMTP sending + dashboard）
- Pipeline: scrape → score → draft → send → track
- SMTP: ianyf@roktandrazo.com (腾讯企业邮箱 465/SSL)，Sender: Ian
- Active template: **V5** (premium_puzzles_card_games_v5) — 4 bullets, catalogue mention, no Zoom
- Backup: backup/bd_template_v4_backup_20260706.py
- BCC-to-self: ✅ 发送时自动 BCC
- fast_lead_discovery.py: HTTP-first 采集（3.1s/lead），已替代 Browser Verifier 和 Google Maps scraper

### Production Scheduling (2026-07-23 架构)
- **调度权威**: WorkBuddy Automation（Windows Task Scheduler 不可用，安全策略阻止）
- **架构**: 五阶段独立自动化（替代旧的单一 daily_operator_auto.py 串联模式）

| 时间 | 名称 | Automation ID |
|------|------|---------------|
| 08:30 | BD Morning | automation-1784775215334 |
| 09:00 | BD Outreach | automation-1782800192924 |
| 13:10 | BD Post-Send | automation-1784775222119 |
| 15:00 | BD Inventory | automation-1784775229336 |
| 17:30 | BD End-of-Day | automation-1784775236108 |

- Timezone: Asia/Shanghai，Send window: 09:00–13:00
- Daily target: **20 emails**（never reduce）
- A0 池耗尽时 Inventory 自动启动 New City Lead Factory 补池
- A0 upgrade rules: 官网可访问、邮箱出现在官网、evidence_url 存在、不在 suppression_list
- 旧 automation-1782369770937 已 ARCHIVED/PAUSED
- Follow-up: 110 final sendable, 5/day cap, 每天 09:00 触发

### Risk Circuit Breaker v3.0 (2026-07-16)
- 状态模型: execution_mode, standing_authorization, manual_pause, risk_gate_status, run_lock
- **Risk stops current RUN only, NEVER pauses the scheduler**
- Only user can set manual_pause=true
- today_sent reads ONLY from send_log（not execution context）
- temporary_risk_block (20h cooldown) 替代 permanent send_pause
- bd_db.py 新增 12 函数（set_risk_gate, clear_risk_gate, can_send_live, acquire_run_lock, get_scheduler_state 等）
- daily_operator_auto.py v3.0: step_inbox_risk_recovery(), run_lock, catch-up-only mode
- production_adapter.py (workbuddy_candidate_modules/): 映射 14 gate fields，推荐 Option B (parallel validation) 起步
- b_pool_enrichment.py: DO NOT MERGE（import mismatch, schema gaps）

### Key Bug Fixes & Lessons
- **email_source_type whitelist (2026-07-13)**: get_sendable_leads() 需包含 'manual_lookup'，否则人工验证 lead 被过滤
- **guessed_email 不可自动发送**
- **check_bounce_history()**: 列名应为 bounce_received_at/diagnostic_code（非 created_at/diag）
- **WebFetch 对 Shopify/Wix/Squarespace JS 渲染站失败率高** → 由 browser_verifier.py 接管
- 新增 source_type 时务必验证是否在 sendable query 的 IN 子句中

### 工作空间清理 (2026-07-20)
- 工作空间从 ~91M 瘦身到 9.4M，释放 81M
- 删除：5个旧副本目录 + 39个根目录过期文件 + tools/google-maps-scraper(57M) + outreach内部旧备份(backup_t1/staging/20个循环备份/__pycache__/旧DB)
- 保留核心: roktandrazo-outreach/(8.5M) + bd_effective_artifacts_20260707_1614/ + codex_handoff_bd_automation_20260707_1129/
- 审计方案: WORKSPACE_AUDIT_CLEANUP_PLAN_20260720.md
