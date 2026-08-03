# FILE_MANIFEST.md

> **Codex Handoff — Complete File Manifest**
> Production directory: `roktandrazo-outreach/`

---

## Core Email Chain (本次修复涉及)

| File | Lines | Purpose | Fix? |
|------|-------|---------|------|
| `bd_sender.py` | 201 | SMTP 发信 + IMAP 存档 | **YES — add Message-ID** |
| `agent_bounce_auditor.py` | 128 | 退信解析 + 分类 | **YES — add message_id_missing** |
| `daily_session.py` | 668 | 批次发送 + 扫描 + 风控 | **YES — add message_id_missing handling** |
| `daily_operator_auto.py` | 920 | 主编排器 (7步流程) | NO |
| `bd_db.py` | 473 | SQLite 数据层 | NO |
| `bd_template.py` | 116 | V5 邮件模板 | NO |
| `env_loader.py` | 87 | .env 配置加载 | NO (含敏感引用) |

## Legacy Sender (不在活跃链路中)

| File | Lines | Purpose | Notes |
|------|-------|---------|-------|
| `sender.py` | 201 | 旧版 SMTP 发送 | 使用 config.py + db.py，也缺 Message-ID |
| `config.py` | — | 旧版品牌常量 | 被 sender.py / drafter.py 引用 |
| `db.py` | 312 | 旧版 SQLite 层 | 使用 leads.db (非 bd_leads.db) |
| `drafter.py` | 248 | 旧版个性化草稿 | 被 sender.py 引用 |
| `pipeline.py` | — | 旧版 pipeline | 不在活跃链路 |

## Lead Factory (采集)

| File | Lines | Purpose |
|------|-------|---------|
| `collection_pipeline.py` | — | 城市选择 → 搜索 → 验证 → 提取 → 评分 |
| `city_selector.py` | — | 城市池管理 |
| `city_selector_v2.py` | — | V2 版城市选择 |
| `search_engine.py` | — | 搜索结果处理 |
| `contact_extractor.py` | — | 网页联系信息提取 |
| `website_verifier.py` | — | 网站可达性 + 邮箱检测 |
| `website_audit.py` | — | 网站内容审计 |
| `auto_collector.py` | — | 自动采集 |
| `agent_email_verifier.py` | — | 邮箱验证 |
| `scorer.py` / `scorer_v2.py` | — | 线索评分 (A/B/C) |
| `browser_verifier.py` | — | Playwright 浏览器验证 |
| `fast_lead_discovery.py` | — | 快速线索发现 |

## Monitoring (监控)

| File | Lines | Purpose |
|------|-------|---------|
| `agent_reply_monitor.py` | 144 | IMAP 扫描 → 分类回复/退信/退订 |
| `agent_daily_report.py` | — | 日报告生成 |
| `agent_supervisor.py` | — | 系统健康监控 |
| `bounce_audit.py` | — | 退信审计 |
| `bounce_deep.py` | — | 深度退信分析 |
| `bounce_diag.py` | — | 退信诊断解析 |

## Pool Management (池管理)

| File | Lines | Purpose |
|------|-------|---------|
| `pool_analysis.py` | 232 | 池统计 + CSV 生成 |
| `b_pool_import.py` | — | B pool CSV → approved_manual_send |
| `b_pool_audit_v2.py` | — | B pool 网站审计分类 |
| `lead_audit_cleanup.py` | — | 线索清理 |

## Import Scripts (导入)

| File | Purpose |
|------|---------|
| `import_pilot.py` | 试点导入 |
| `import_new_leads.py` | 新线索导入 |
| `import_phase2.py` | Phase 2 导入 |
| `import_phase3.py` | Phase 3 导入 |
| `import_phase4.py` | Phase 4 导入 |
| `import_phase4_b2.py` | Phase 4 B2 导入 |
| `import_phase4_b3.py` | Phase 4 B3 导入 |
| `import_phase4_b4.py` | Phase 4 B4 导入 |

## Testing / Dry-Run

| File | Purpose |
|------|---------|
| `dryrun_phase2.py` | Phase 2 干跑 |
| `dryrun_phase3.py` | Phase 3 干跑 |
| `send_phase2.py` | Phase 2 发送测试 |
| `send_phase3.py` | Phase 3 发送测试 |

## Other

| File | Purpose |
|------|---------|
| `agent_sender.py` | Agent 发送器 (包装 bd_sender) |
| `dashboard.py` | 仪表盘 |
| `db_migration_v2.py` | DB 迁移脚本 |
| `export_backup.py` | 导出备份 |
| `update_bounce_db.py` | 退信 DB 更新 |
| `pipeline_orchestrator.py` | Pipeline 编排器 |
| `CODEX_HANDOFF_BD_AUTOMATION.md` | 旧版交接文档 (2026-06-29) |

---

## Directories

| Directory | Purpose | Sensitive? |
|-----------|---------|-----------|
| `data/` | SQLite 数据库 | **YES — contains real customer data** |
| `output/` | 报告、CSV、日志 | Partial — contains email addresses |
| `backup/` | 备份文件 | YES — historical data |
| `backup_t1/` | 备份文件 | YES |
| `staging/` | 暂存区 | Check contents |
| `templates/` | 模板目录 | Empty |
| `__pycache__/` | Python 缓存 | NO |

---

## Sensitive Files (DO NOT COPY)

| File | Contains |
|------|----------|
| `.env` | SMTP_PASSWORD, IMAP_PASSWORD, SMTP_USER |
| `data/bd_leads.db` | Real customer emails, store data, send logs |
| `data/leads.db` | Legacy DB (also real data) |
| `data/phase1_leads.db` | Phase 1 DB (real data) |
| `data/searched_cities.json` | Search history |
