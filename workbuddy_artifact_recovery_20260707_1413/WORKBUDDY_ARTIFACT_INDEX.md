# WORKBUDDY_ARTIFACT_INDEX.md

> **WorkBuddy Artifact Recovery — Historical Product Index**
> Generated: 2026-07-07T14:13+08:00
> Scope: Read-only audit of WorkBuddy historical artifacts for Codex context

---

## 1. Project Memory & Skills

### 1.1 Project Memory (`.workbuddy/memory/MEMORY.md`)

| Item | Details |
|------|---------|
| **Path** | `C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\.workbuddy\memory\MEMORY.md` |
| **Type** | Project rules & conventions |
| **Modified** | 2026-07-06 |
| **Purpose** | Long-term project rules: pool definitions, scoring, city strategy, orchestrator config |
| **Sensitive** | No (no credentials) |
| **Codex Read?** | ✅ YES — primary reference for project rules |
| **Merge to Prod?** | N/A (read-only reference) |
| **Notes** | Contains A0/B2/C definitions, daily target=20, inventory_floor=60, TN/AR/KY primary states, V5 template rules |

### 1.2 Daily Memory Logs (`.workbuddy/memory/`)

| File | Date | Key Content |
|------|------|-------------|
| `2026-06-05.md` | Jun 5 | Initial project setup |
| `2026-06-10.md` | Jun 10 | Pilot phase |
| `2026-06-15.md` | Jun 15 | Scoring V2 |
| `2026-06-17.md` | Jun 17 | Phase 3 metros, SPF/DKIM issues |
| `2026-06-23.md` | Jun 23 | B pool audit |
| `2026-06-24.md` | Jun 24 | B pool import |
| `2026-06-25.md` | Jun 25 | Daily operator design, first 20-send live |
| `2026-06-26.md` | Jun 26 | Underfilled day, bulk update incident |
| `2026-06-29.md` | Jun 29 | Browser verifier deployed, Phase 2 safety test |
| `2026-06-30.md` | Jun 30 | Inventory live, fast_lead_discovery, Phase 3 throughput |
| `2026-07-01.md` | Jul 1 | A0 replenishment, task rename |
| `2026-07-02.md` | Jul 2 | B2 pool analysis |
| `2026-07-03.md` | Jul 3 | State deep coverage, TN report |
| `2026-07-06.md` | Jul 6 | V5 template, timezone fix, Google Maps POC, AR/KY collection |
| `2026-07-07.md` | Jul 7 | Orchestrator blocked (9/20), Codex handoff package |

### 1.3 Automation Memory (`roktandrazo-outreach/.workbuddy/automations/`)

| Automation ID | Name | Status | Last Run |
|--------------|------|--------|----------|
| `automation-1782369770937` | BD Daily Send — 08:30 Auto Operator | PAUSED | 2026-06-30 |
| `automation-1782800192924` | Roktandrazo BD Daily Orchestrator - 09:00 China Time | ACTIVE | 2026-07-07 |

**Key finding**: Active automation runs `daily_operator_auto.py` daily at 09:00 Asia/Shanghai.

### 1.4 Outreach Memory (`roktandrazo-outreach/.workbuddy/memory/`)

| File | Date | Key Content |
|------|------|-------------|
| `2026-06-26.md` | Jun 26 | Outreach-specific notes |
| `2026-06-29.md` | Jun 29 | Browser verifier test |
| `2026-06-30.md` | Jun 30 | Inventory live results |
| `2026-07-01.md` | Jul 1 | A0 replenishment |
| `2026-07-03.md` | Jul 3 | State coverage audit |
| `2026-07-06.md` | Jul 6 | V5 template, Google Maps, AR/KY |
| `2026-07-07.md` | Jul 7 | Orchestrator blocked, Lead Factory findings |

---

## 2. Handoff Packages

### 2.1 Codex Handoff 2026-06-29 (`codex_handoff_bd_automation_20260629_1559/`)

| Item | Details |
|------|---------|
| **Path** | `codex_handoff_bd_automation_20260629_1559/` |
| **Type** | Handoff package (original) |
| **Created** | 2026-06-29 |
| **Purpose** | First Codex handoff — system architecture, DB schema, incident timeline |
| **Contents** | ARCHITECTURE_MAP.md, BUSINESS_RULES.md, CODEX_GUARDRAILS.md, CURRENT_STATUS_SNAPSHOT.md, DB_SCHEMA_AND_COUNTS.md, FILE_MANIFEST.md, INCIDENT_TIMELINE.md, RUN_COMMANDS.md, ACCEPTANCE_CRITERIA.md |
| **DB Export** | schema.sql, sample_redacted_leads.csv, latest_pool_counts.json |
| **Output Samples** | daily_report, b_pool CSV, tier2_cities.json |
| **Source Snapshot** | SOURCE_SNAPSHOT.zip (381KB) |
| **Sensitive** | Contains sample_redacted_leads.csv (redacted but real structure) |
| **Codex Read?** | ✅ YES — foundational reference |

### 2.2 Codex Handoff 2026-07-07 (`codex_handoff_bd_automation_20260707_1129/`)

| Item | Details |
|------|---------|
| **Path** | `codex_handoff_bd_automation_20260707_1129/` |
| **Type** | Handoff package (Message-ID focus) |
| **Created** | 2026-07-07 |
| **Purpose** | Message-ID header fix handoff |
| **Contents** | README.md, CURRENT_STATUS.md, ARCHITECTURE_MAP.md, RUNBOOK.md, GUARDRAILS.md, FILE_MANIFEST.md, SENSITIVE_EXCLUSION_AUDIT.md |
| **Sensitive** | No (clean) |
| **Codex Read?** | ✅ YES — Message-ID fix reference |

### 2.3 Codex Lab 2026-07-07 (`roktandrazo-outreach_codex_lab_20260707/`)

| Item | Details |
|------|---------|
| **Path** | `roktandrazo-outreach_codex_lab_20260707/` |
| **Type** | Isolated Codex lab |
| **Created** | 2026-07-07 |
| **Purpose** | Message-ID fix implementation + tests |
| **Contents** | src/bd_sender.py, src/agent_bounce_auditor.py, src/daily_session.py, tests/test_message_id_header_fix.py, reports/MESSAGE_ID_HEADER_FIX_REPORT.md |
| **Sensitive** | No (uses .env.example only) |
| **Codex Read?** | ✅ YES — Message-ID fix implementation |

---

## 3. Workspace Root Reports

### 3.1 Audit Reports

| File | Date | Topic | Codex Read? |
|------|------|-------|-------------|
| `B2_MANUAL_REVIEW_POOL_AUDIT.md` | Jul 7 | B2 pool = manual_review_needed = 167 | ✅ |
| `CITY_COVERAGE_STATUS_AUDIT.md` | Jul 7 | 183 cities, only 4 deep_covered | ✅ |
| `STATE_DEEP_COVERAGE_SCOPE_AUDIT.md` | Jul 7 | Today's 3 leads from CT/ID/ME = emergency | ✅ |
| `INVENTORY_SHIFT_PLAN_TN_AR_KY.md` | Jul 7 | City priority for TN/AR/KY | ✅ |
| `STATE_V2_A0_COUNT_AUDIT.md` | Jul 6 | A0 count by state | ✅ |
| `SEND_WINDOW_CONFIG_AUDIT.md` | Jul 3 | Send window config verification | ✅ |
| `NETWORK_PROXY_DIAGNOSIS_REPORT.md` | Jul 6 | VPN/proxy diagnosis | ✅ |
| `TEMPLATE_V5_SYNC_REPORT.md` | Jul 6 | V5 template sync | ✅ |
| `DAILY_ORCHESTRATOR_TRIGGER_DECISION_REPORT.md` | Jul 7 | Orchestrator decision logic | ✅ |

### 3.2 Branch B Reports

| File | Date | Topic | Codex Read? |
|------|------|-------|-------------|
| `BRANCH_B_A0_UPGRADE_LOG.csv` | Jul 7 | A0 upgrade log | ✅ |
| `BRANCH_B_BLOCKED_REASON_SUMMARY.md` | Jul 7 | Blocked reasons | ✅ |
| `BRANCH_B_MANUAL_CONTACT_TOP20.md` | Jul 7 | Top 20 manual contact | ✅ |
| `BRANCH_B_VERIFICATION_BATCH_REPORT.md` | Jul 7 | Verification batch | ✅ |
| `BRANCH_B_VERIFICATION_RESULTS.csv` | Jul 7 | Verification results | ✅ |

### 3.3 Collection & Inventory Reports

| File | Date | Topic | Codex Read? |
|------|------|-------|-------------|
| `BD_DAILY_COLLECTION_REPORT_20260706.md` | Jul 6 | Daily collection report | ✅ |
| `BD_DAILY_ORCHESTRATION_REPORT_BILINGUAL.md` | Jul 6 | Daily orchestration | ✅ |
| `BD_SAME_DAY_DEFICIT_RECOVERY_REPORT_BILINGUAL.md` | Jul 6 | Deficit recovery | ✅ |
| `BD_WEEKLY_REVIEW_FOR_NEIL_BILINGUAL.md` | Jul 2 | Weekly review | ✅ |
| `BD_WEEKLY_REVIEW_FOR_NEIL_CN.md` | Jul 2 | Weekly review (CN) | ✅ |
| `TN_STATE_DEEP_COVERAGE_REPORT.md` | Jul 3 | TN state coverage | ✅ |
| `STATE_DEEP_COVERAGE_INVENTORY_SHIFT_REPORT.md` | Jul 6 | Inventory shift | ✅ |
| `GOOGLE_MAPS_BRANCH_POC_REPORT.md` | Jul 6 | Google Maps POC | ✅ |
| `GOOGLE_MAPS_ANTI_SCRAPE_NOTE_CN.md` | Jul 6 | Anti-scrape notes | ✅ |

### 3.4 Manual Contact Queue

| File | Date | Topic | Codex Read? |
|------|------|-------|-------------|
| `MANUAL_CONTACT_FETCH_QUEUE.csv` | Jul 6 | 217 candidates → 30 for manual lookup | ✅ |
| `MANUAL_CONTACT_FETCH_QUEUE_CN.md` | Jul 6 | Queue description (CN) | ✅ |
| `MANUAL_CONTACT_FETCH_TOP30_CN.md` | Jul 6 | Top 30 details | ✅ |
| `MANUAL_CONTACT_IMPORT_INSTRUCTIONS_CN.md` | Jul 6 | Import instructions | ✅ |

### 3.5 Inventory Data

| File | Date | Topic | Codex Read? |
|------|------|-------|-------------|
| `INVENTORY_SHIFT_AR_KY_CANDIDATES.csv` | Jul 6 | AR/KY candidates (234KB) | ✅ |
| `INVENTORY_SHIFT_TN_AR_KY_LIVE.csv` | Jul 7 | TN/AR/KY live data (203KB) | ✅ |
| `GOOGLE_MAPS_CANDIDATES_TN_SAMPLE.csv` | Jul 6 | TN sample (88KB) | ✅ |

---

## 4. Production Scripts (`roktandrazo-outreach/`)

### 4.1 Core Sending Chain

| File | Lines | Purpose | Codex Read? |
|------|-------|---------|-------------|
| `daily_operator_auto.py` | 37782 | Daily orchestrator (7 steps) | ✅ CRITICAL |
| `daily_session.py` | 28025 | Batch send session | ✅ CRITICAL |
| `bd_sender.py` | 7631 | SMTP sender | ✅ CRITICAL |
| `bd_db.py` | 16673 | Database layer | ✅ CRITICAL |
| `bd_template.py` | 4792 | Email template (V5) | ✅ |
| `env_loader.py` | 2496 | Credential loader | ⚠️ Contains .env path |

### 4.2 Lead Factory

| File | Lines | Purpose | Codex Read? |
|------|-------|---------|-------------|
| `fast_lead_discovery.py` | 18833 | HTTP-first + browser fallback | ✅ |
| `browser_verifier.py` | 13483 | Playwright verification | ✅ |
| `collection_pipeline.py` | 10921 | City → search → verify → extract → score | ✅ |
| `city_selector.py` | 11274 | City pool management | ✅ |
| `city_selector_v2.py` | 3900 | V2 with state filtering | ✅ |
| `search_engine.py` | 8862 | Search result processing | ✅ |
| `contact_extractor.py` | 13142 | Contact info extraction | ✅ |
| `website_verifier.py` | 10522 | Website reachability | ✅ |
| `website_audit.py` | 9311 | Website content audit | ✅ |
| `agent_email_verifier.py` | 16586 | Email verification | ✅ |
| `scorer_v2.py` | 12939 | Lead scoring (A/B/C) | ✅ |

### 4.3 Monitoring

| File | Lines | Purpose | Codex Read? |
|------|-------|---------|-------------|
| `agent_reply_monitor.py` | 5152 | IMAP scan → classify | ✅ |
| `agent_bounce_auditor.py` | 5161 | Bounce detection + classification | ✅ |
| `agent_daily_report.py` | 9857 | Daily report generator | ✅ |
| `bounce_audit.py` | 15995 | Bounce analysis | ✅ |
| `bounce_deep.py` | 5064 | Deep bounce analysis | ✅ |
| `bounce_diag.py` | 3339 | Bounce diagnostic parser | ✅ |

### 4.4 Pool Management

| File | Lines | Purpose | Codex Read? |
|------|-------|---------|-------------|
| `pool_analysis.py` | 9893 | Pool statistics + CSV | ✅ |
| `b_pool_import.py` | 10466 | B pool CSV → approved_manual_send | ✅ |
| `b_pool_audit_v2.py` | 4130 | B pool website audit | ✅ |

### 4.5 Import Scripts

| File | Lines | Purpose | Codex Read? |
|------|-------|---------|-------------|
| `import_new_leads.py` | 18153 | New lead import | ✅ |
| `import_phase2.py` | 15345 | Phase 2 import | ✅ |
| `import_phase3.py` | 33940 | Phase 3 import | ✅ |
| `import_phase4.py` | 41984 | Phase 4 import | ✅ |
| `import_phase4_b2.py` | 18523 | Phase 4 B2 import | ✅ |
| `import_phase4_b3.py` | 19878 | Phase 4 B3 import | ✅ |
| `import_phase4_b4.py` | 17749 | Phase 4 B4 import | ✅ |
| `import_pilot.py` | 11622 | Pilot import | ✅ |

### 4.6 Legacy / Backup

| File | Lines | Purpose | Codex Read? |
|------|-------|---------|-------------|
| `sender.py` | 6538 | Legacy sender (pre-bd_sender) | ⚠️ May lack Message-ID |
| `db.py` | 9970 | Legacy DB (pre-bd_db) | ⚠️ Reference only |
| `scorer.py` | 7570 | Legacy scorer (pre-scorer_v2) | ⚠️ Reference only |
| `main.py` | 5583 | Legacy main | ⚠️ Reference only |
| `pipeline.py` | 5846 | Legacy pipeline | ⚠️ Reference only |
| `dashboard.py` | 9681 | Dashboard | ⚠️ Reference only |

---

## 5. Google Maps Scraper Tool (`tools/google-maps-scraper/`)

| File | Size | Purpose | Codex Read? |
|------|------|---------|-------------|
| `gmaps_fast_poc.py` | 8KB | Fast Playwright POC | ✅ |
| `gmaps_playwright_poc.py` | 12KB | Full Playwright POC | ✅ |
| `gmaps-scraper.exe` | 59MB | Go binary scraper | ⚠️ Binary, not readable |
| `inventory_shift_ar_ky.py` | 9KB | AR/KY inventory shift | ✅ |
| `inventory_shift_live.py` | 8KB | Live inventory shift | ✅ |
| `queries_tn.txt` | 781B | TN search queries | ✅ |

---

## 6. Documents/线下bd (Codex Working Directory)

| Item | Details |
|------|---------|
| **Path** | `C:\Users\15690\Documents\线下bd\` |
| **Type** | Codex working directory |
| **Purpose** | Codex's own BD automation workspace |
| **Key Files** | daily_runner.py, bd_db.py, bd_sender.py, bd_template.py, lead_collector.py |
| **DB** | data/bd_leads.db (98KB — separate from production) |
| **Config** | .codex/config.toml (sandbox_mode = "danger-full-access") |
| **Sensitive** | Contains .env (real credentials) |
| **Codex Read?** | ⚠️ Separate workspace — Codex's own context |

---

## 7. Archive (`_archive/`)

| File | Date | Topic | Codex Read? |
|------|------|-------|-------------|
| `ACTIVE_SEND_CONTEXT_REPORT.md` | Jul 6 | Active send context | ✅ |
| `B2_AGENT_PASS2_REPORT_CN.md` | Jun 30 | B2 agent pass 2 | ✅ |
| `B2_C_WEBSITE_SAMPLE_REVIEW_BILINGUAL.md` | Jun 30 | B2/C website review | ✅ |
| `B2_HUMAN_TOP10_REVIEW_CN.md` | Jun 30 | B2 human top 10 | ✅ |
| `B2_TOP30_MANUAL_REVIEW_CN.md` | Jun 30 | B2 top 30 review | ✅ |
| `BD_AUTOMATION_PROGRESS_BILINGUAL_REPORT.md` | Jun 30 | Automation progress | ✅ |
| `BD_COLLECTION_CITY_SUMMARY_BILINGUAL.md` | Jun 30 | City collection summary | ✅ |
| `BD_SEND_LIVE_RECIPIENTS_BILINGUAL_REPORT.md` | Jun 30 | Send live recipients | ✅ |
| `EMAIL_INBOX_SUMMARY_CN.md` | Jun 30 | Email inbox scan | ✅ |
| `INVENTORY_LIVE_FINAL_REPORT.md` | Jun 30 | Inventory live final | ✅ |
| `INVENTORY_PRODUCTION_BATCH_REPORT.md` | Jun 30 | Production batch | ✅ |
| `LEGACY_TASKS_ARCHIVE_REPORT.md` | Jun 30 | Legacy tasks archive | ✅ |
| `PHASE2_SAFE_LANDING_REPORT.md` | Jun 29 | Phase 2 safe landing | ✅ |
| `PHASE3_COLLECTION_THROUGHPUT_REPORT.md` | Jun 30 | Phase 3 throughput | ✅ |
| `PRE_LIVE_READINESS_REPORT.md` | Jun 30 | Pre-live readiness | ✅ |
| `SENDABLE_POOL_DROP_AUDIT.md` | Jun 30 | Sendable pool drop | ✅ |

---

## 8. Backup Files (`roktandrazo-outreach/backup/`)

| File | Date | Purpose | Sensitive? |
|------|------|---------|-----------|
| `a_grade_sendable_*.csv` | Jun 23 | A grade snapshot | YES — real emails |
| `all_leads_*.csv` | Jun 23 | All leads snapshot | YES — real emails |
| `b_grade_*.csv` | Jun 23 | B grade snapshot | YES — real emails |
| `bounce_log_*.csv` | Jun 23 | Bounce log snapshot | YES — real emails |
| `suppression_list_*.csv` | Jun 23 | Suppression snapshot | YES — real emails |
| `bd_template_v3_backup_20260630.py` | Jun 30 | V3 template backup | No |
| `bd_template_v4_backup_20260706.py` | Jul 6 | V4 template backup | No |

---

## 9. Staging Data (`roktandrazo-outreach/staging/`)

| File | Date | Purpose | Codex Read? |
|------|------|---------|-------------|
| `b2_all.json` | Jun 30 | All B2 leads | ✅ |
| `b2_top30_scored.json` | Jun 30 | Top 30 scored | ✅ |
| `b2_human_top10.json` | Jun 30 | Human top 10 | ✅ |
| `b2_pass2_input.json` | Jun 30 | Pass 2 input | ✅ |
| `b2_pass2_results.json` | Jun 30 | Pass 2 results | ✅ |
| `batch_candidates.json` | Jun 30 | Batch candidates | ✅ |
| `batch_results.json` | Jun 30 | Batch results | ✅ |
| `fast_discovery_results.json` | Jun 30 | Fast discovery results | ✅ |
| `new_city_batch*.json` | Jul 2 | New city batches | ✅ |

---

## 10. Output Data (`roktandrazo-outreach/output/`)

### 10.1 Daily Reports

| File | Date | Codex Read? |
|------|------|-------------|
| `daily_report_2026-06-25.md` | Jun 25 | ✅ |
| `daily_report_2026-06-26.md` | Jun 26 | ✅ |
| `daily_report_2026-06-29.md` | Jun 29 | ✅ |
| `daily_report_2026-06-30.md` | Jun 30 | ✅ |
| `daily_report_2026-07-01.md` | Jul 1 | ✅ |
| `daily_report_2026-07-02.md` | Jul 2 | ✅ |
| `daily_report_2026-07-03.md` | Jul 3 | ✅ |
| `daily_report_2026-07-06.md` | Jul 6 | ✅ |
| `auto_report_2026-06-25.md` | Jun 25 | ✅ |
| `auto_report_2026-06-26.md` | Jun 26 | ✅ |
| `auto_report_2026-06-29.md` | Jun 29 | ✅ |
| `auto_report_2026-06-30.md` | Jun 30 | ✅ |
| `auto_report_2026-07-01.md` | Jul 1 | ✅ |
| `auto_report_2026-07-02.md` | Jul 2 | ✅ |
| `auto_report_2026-07-03.md` | Jul 3 | ✅ |
| `auto_report_2026-07-06.md` | Jul 6 | ✅ |

### 10.2 Pool CSVs

| File | Date | Codex Read? |
|------|------|-------------|
| `b_pool_manual_review.csv` | Jun 25 | ✅ |
| `b_pool_approval.csv` | Jun 24 | ✅ |
| `b2_high_value_manual_review.csv` | Jun 26 | ✅ |
| `B2_TOP30_MANUAL_REVIEW.csv` | Jun 30 | ✅ |
| `B2_top30_review.csv` | Jun 30 | ✅ |
| `b2_browser_manual_*.csv` | Jun 29-30 | ✅ |

### 10.3 Design Docs

| File | Date | Codex Read? |
|------|------|-------------|
| `daily_operator_design.md` | Jun 25 | ✅ |
| `system_design.md` | Jun 15 | ✅ |
| `phase1_plan.md` | Jun 10 | ✅ |
| `product_overview.md` | Jun 8 | ✅ |
| `pilot_report.md` | Jun 10 | ✅ |

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Total artifacts found** | 150+ |
| **Reports** | 45+ |
| **Scripts** | 59 |
| **CSVs** | 25+ |
| **JSON data files** | 15+ |
| **Memory logs** | 17 |
| **Handoff packages** | 3 |
| **Sensitive files (excluded)** | 12 |
