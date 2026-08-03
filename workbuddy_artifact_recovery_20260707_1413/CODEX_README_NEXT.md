# CODEX_README_NEXT.md

> **Codex Next Steps — Reading List & Recommendations**
> Generated: 2026-07-07T14:13+08:00
> Purpose: Guide Codex through the historical artifacts and recommend next steps

---

## 1. Priority Reading List

### 1.1 MUST READ FIRST (Critical Context)

| # | File | Path | Why |
|---|------|------|-----|
| 1 | MEMORY.md | `.workbuddy/memory/MEMORY.md` | Master project rules — pool definitions, daily target, state strategy |
| 2 | CURRENT_STATUS.md | `codex_handoff_bd_automation_20260707_1129/` | Current system status, Message-ID issue |
| 3 | ARCHITECTURE_MAP.md | `codex_handoff_bd_automation_20260707_1129/` | System architecture, email chain |
| 4 | RUNBOOK.md | `codex_handoff_bd_automation_20260707_1129/` | Message-ID fix guide |
| 5 | GUARDRAILS.md | `codex_handoff_bd_automation_20260707_1129/` | Safety rules |

### 1.2 MUST READ (Core Scripts)

| # | File | Path | Why |
|---|------|------|-----|
| 6 | daily_operator_auto.py | `roktandrazo-outreach/` | Daily orchestrator — the brain |
| 7 | daily_session.py | `roktandrazo-outreach/` | Batch send session |
| 8 | bd_sender.py | `roktandrazo-outreach/` | SMTP sender — Message-ID fix needed here |
| 9 | bd_db.py | `roktandrazo-outreach/` | Database layer — pool queries |
| 10 | agent_bounce_auditor.py | `roktandrazo-outreach/` | Bounce classification — message_id_missing type needed |

### 1.3 SHOULD READ (Lead Factory)

| # | File | Path | Why |
|---|------|------|-----|
| 11 | fast_lead_discovery.py | `roktandrazo-outreach/` | HTTP-first + browser fallback — 19x faster than Browser Verifier |
| 12 | browser_verifier.py | `roktandrazo-outreach/` | Playwright verification — critical for A0 upgrades |
| 13 | pool_analysis.py | `roktandrazo-outreach/` | Pool statistics + CSV generation |
| 14 | city_selector_v2.py | `roktandrazo-outreach/` | State filtering — TN/AR/KY logic |
| 15 | b_pool_import.py | `roktandrazo-outreach/` | B pool CSV → approved_manual_send |

### 1.4 SHOULD READ (Monitoring)

| # | File | Path | Why |
|---|------|------|-----|
| 16 | agent_reply_monitor.py | `roktandrazo-outreach/` | IMAP scan → classify replies/bounces |
| 17 | agent_daily_report.py | `roktandrazo-outreach/` | Daily report generator |
| 18 | scorer_v2.py | `roktandrazo-outreach/` | Lead scoring (A/B/C) |

### 1.5 SHOULD READ (Reports)

| # | File | Path | Why |
|---|------|------|-----|
| 19 | BD_WEEKLY_REVIEW_FOR_NEIL_BILINGUAL.md | workspace root | Weekly review — business context |
| 20 | CITY_EXPANSION_RULES.md | workspace root | City strategy — "农村包围城市" |
| 21 | INVENTORY_SHIFT_PLAN_TN_AR_KY.md | workspace root | TN/AR/KY priority cities |
| 22 | GOOGLE_MAPS_BRANCH_POC_REPORT.md | workspace root | Google Maps POC results |
| 23 | BRANCH_B_MANUAL_CONTACT_TOP20.md | workspace root | Top 20 manual contact candidates |

---

## 2. Historical Artifacts Reference

### 2.1 Codex Handoff Packages

| Package | Path | Purpose | Read? |
|---------|------|---------|-------|
| Handoff 2026-06-29 | `codex_handoff_bd_automation_20260629_1559/` | Original handoff — architecture, DB schema, timeline | ✅ YES |
| Handoff 2026-07-07 | `codex_handoff_bd_automation_20260707_1129/` | Message-ID fix handoff | ✅ YES |
| Codex Lab 2026-07-07 | `roktandrazo-outreach_codex_lab_20260707/` | Message-ID fix implementation | ✅ YES |

### 2.2 Backup Files

| File | Path | Purpose | Read? |
|------|------|---------|-------|
| SOURCE_SNAPSHOT.zip | `codex_handoff_bd_automation_20260629_1559/` | Full source snapshot | ⚠️ Optional |
| bd_template_v4_backup_20260706.py | `roktandrazo-outreach/backup/` | V4 template backup | ⚠️ Optional |
| bd_template_v3_backup_20260630.py | `roktandrazo-outreach/backup/` | V3 template backup | ⚠️ Optional |

### 2.3 Data Files

| File | Path | Purpose | Read? |
|------|------|---------|-------|
| b2_all.json | `roktandrazo-outreach/staging/` | All B2 leads | ✅ YES |
| b2_top30_scored.json | `roktandrazo-outreach/staging/` | Top 30 scored | ✅ YES |
| primary_state_cities.json | `roktandrazo-outreach/` | TN/AR/KY cities | ✅ YES |
| searched_cities.json | `roktandrazo-outreach/data/` | Search history | ✅ YES |

---

## 3. What NOT to Use Directly

### 3.1 Legacy Scripts (Reference Only)

| File | Why Not Use Directly |
|------|---------------------|
| `sender.py` | Legacy sender — may lack Message-ID, use bd_sender.py instead |
| `db.py` | Legacy DB — use bd_db.py instead |
| `scorer.py` | Legacy scorer — use scorer_v2.py instead |
| `main.py` | Legacy main — use daily_operator_auto.py instead |
| `pipeline.py` | Legacy pipeline — use daily_session.py instead |

### 3.2 Sensitive Files (DO NOT READ)

| File | Why Not |
|------|---------|
| `.env` | Contains SMTP/IMAP passwords |
| `data/bd_leads.db` | Real customer data |
| `backup/*.csv` | Contains real email addresses |
| `Documents/线下bd/.env` | Contains credentials |

---

## 4. Tools That Can Be Migrated

### 4.1 High Priority (Critical for Operations)

| Tool | Legacy Path | Current Status | Migration Difficulty |
|------|-------------|----------------|---------------------|
| `pool_analysis.py` | `roktandrazo-outreach/` | ❌ Missing | LOW — standalone script |
| `browser_verifier.py` | `roktandrazo-outreach/` | ❌ Missing | MEDIUM — needs Playwright |
| `fast_lead_discovery.py` | `roktandrazo-outreach/` | ❌ Missing | MEDIUM — needs Playwright |
| `b_pool_import.py` | `roktandrazo-outreach/` | ❌ Missing | LOW — standalone script |
| `agent_bounce_auditor.py` | `roktandrazo-outreach/` | ❌ Missing | LOW — standalone script |

### 4.2 Medium Priority (Important for Efficiency)

| Tool | Legacy Path | Current Status | Migration Difficulty |
|------|-------------|----------------|---------------------|
| `city_selector_v2.py` | `roktandrazo-outreach/` | ❌ Missing | LOW — standalone script |
| `agent_reply_monitor.py` | `roktandrazo-outreach/` | ❌ Missing | LOW — standalone script |
| `agent_daily_report.py` | `roktandrazo-outreach/` | ❌ Missing | LOW — standalone script |
| `scorer_v2.py` | `roktandrazo-outreach/` | ❌ Missing | LOW — standalone script |

### 4.3 Low Priority (Nice to Have)

| Tool | Legacy Path | Current Status | Migration Difficulty |
|------|-------------|----------------|---------------------|
| `b_pool_audit_v2.py` | `roktandrazo-outreach/` | ❌ Missing | LOW — standalone script |
| `website_audit.py` | `roktandrazo-outreach/` | ❌ Missing | LOW — standalone script |
| `contact_extractor.py` | `roktandrazo-outreach/` | ❌ Missing | LOW — standalone script |

---

## 5. Tools That Need Modification

### 5.1 bd_sender.py (CRITICAL)

**Current issue**: Missing Message-ID header
**Fix**: Apply the fix from Codex Lab (`roktandrazo-outreach_codex_lab_20260707/src/bd_sender.py`)
**Steps**:
1. Add `from email.utils import make_msgid`
2. Add `msg["Message-ID"] = make_msgid(domain="roktandrazo.com")` in `_build_email()`
3. Test with dry-run

### 5.2 agent_bounce_auditor.py (CRITICAL)

**Current issue**: No message_id_missing type
**Fix**: Apply the fix from Codex Lab
**Steps**:
1. Add message_id_missing detection before hard/policy classification
2. Return type: 'message_id_missing'
3. Action: 'Message-ID header missing - fix sender, do NOT suppress'

### 5.3 daily_session.py (CRITICAL)

**Current issue**: No message_id_missing handling
**Fix**: Apply the fix from Codex Lab
**Steps**:
1. Add handling for `b.get('type') == 'message_id_missing'`
2. Count under policy_bounces
3. Do NOT trigger suppression

---

## 6. Next Steps for Codex

### 6.1 Immediate (Today)

1. **Read MEMORY.md** — understand project rules
2. **Read current handoff package** — understand current status
3. **Read Codex Lab report** — understand Message-ID fix
4. **Apply Message-ID fix to production** — patch bd_sender.py, agent_bounce_auditor.py, daily_session.py
5. **Run dry-run** — verify fix works
6. **Test with one email** — send to own inbox to verify Message-ID header

### 6.2 Short-term (This Week)

1. **Migrate pool_analysis.py** — get pool statistics
2. **Migrate browser_verifier.py** — enable A0 upgrades
3. **Migrate fast_lead_discovery.py** — enable fast lead collection
4. **Migrate city_selector_v2.py** — enable TN/AR/KY filtering
5. **Audit sendable_pool** — understand why count is only 5

### 6.3 Medium-term (Next Week)

1. **Migrate agent_reply_monitor.py** — enable reply/bounce monitoring
2. **Migrate agent_daily_report.py** — enable comprehensive daily reports
3. **Migrate b_pool_import.py** — enable B pool management
4. **Migrate scorer_v2.py** — enable lead scoring
5. **Implement Same-day Deficit Recovery** — auto-replenish pool

### 6.4 Long-term (Future)

1. **Full daily orchestrator** — migrate daily_operator_auto.py logic
2. **Google Maps integration** — use tools/google-maps-scraper/
3. **Automated city expansion** — "农村包围城市" strategy
4. **Comprehensive reporting** — bilingual daily/weekly reports

---

## 7. Key Questions for Codex

### 7.1 Why is sendable_pool only 5?

**Investigate**:
1. How many A0 leads are in the database?
2. How many are excluded by suppression?
3. How many are excluded by sent_log?
4. How many are excluded by Exchange MX filter?
5. How many are excluded by evidence_snippet requirement?

### 7.2 Why are 167 manual_review_needed not being upgraded?

**Investigate**:
1. What is the definition of manual_review_needed?
2. Why can't they be auto-upgraded?
3. What verification is needed?
4. Is browser verification required?

### 7.3 Why is today's send count 0?

**Investigate**:
1. Was the send window missed?
2. Was send_pause=true?
3. Was pool insufficient?
4. Was there an error?

---

## 8. Critical Files Summary

### 8.1 Files Codex MUST Read

1. `.workbuddy/memory/MEMORY.md` — project rules
2. `codex_handoff_bd_automation_20260707_1129/CURRENT_STATUS.md` — current status
3. `codex_handoff_bd_automation_20260707_1129/RUNBOOK.md` — Message-ID fix guide
4. `roktandrazo-outreach/bd_sender.py` — SMTP sender (needs fix)
5. `roktandrazo-outreach/agent_bounce_auditor.py` — bounce classifier (needs fix)
6. `roktandrazo-outreach/daily_session.py` — batch sender (needs fix)
7. `roktandrazo-outreach/bd_db.py` — database layer
8. `roktandrazo-outreach/daily_operator_auto.py` — daily orchestrator

### 8.2 Files Codex SHOULD Read

9. `roktandrazo-outreach/pool_analysis.py` — pool statistics
10. `roktandrazo-outreach/browser_verifier.py` — browser verification
11. `roktandrazo-outreach/fast_lead_discovery.py` — fast lead discovery
12. `roktandrazo-outreach/city_selector_v2.py` — state filtering
13. `roktandrazo-outreach/b_pool_import.py` — B pool import
14. `roktandrazo-outreach/agent_reply_monitor.py` — reply monitoring
15. `roktandrazo-outreach/agent_daily_report.py` — daily reports

### 8.3 Files Codex CAN Reference

16. `codex_handoff_bd_automation_20260629_1559/` — original handoff
17. `roktandrazo-outreach_codex_lab_20260707/` — Message-ID fix lab
18. `_archive/` — historical reports
19. `tools/google-maps-scraper/` — Google Maps tools
20. `roktandrazo-outreach/staging/` — B2 lead data

---

## 9. Final Recommendation

**Codex should focus on three things:**

1. **Fix Message-ID** — Apply the lab fix to production (3 files, ~10 lines)
2. **Understand the pool** — Why is sendable_pool only 5? Audit the database.
3. **Migrate critical tools** — pool_analysis.py, browser_verifier.py, fast_lead_discovery.py

**The legacy system (WorkBuddy) had a complete, working BD automation pipeline.** Codex should read the legacy tools to understand the full system capabilities, then decide which to migrate and which to rebuild.

**The most critical gap is browser verification.** Without it, Codex cannot upgrade B-grade leads to A0, which means the sendable pool will remain low.

**The second most critical gap is pool statistics.** Without pool_analysis.py, Codex cannot understand why the pool is low or how to fix it.

**The third most critical gap is state filtering.** Without city_selector_v2.py, Codex cannot implement the TN/AR/KY strategy.
