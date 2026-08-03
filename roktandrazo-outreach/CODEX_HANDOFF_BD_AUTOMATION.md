# CODEX_HANDOFF_BD_AUTOMATION.md

> **Roktandrazo US Retail BD Automation — System Handoff**
> Generated: 2026-06-29T15:33+08:00 | Owner: Ian | SMTP: ianyf@roktandrazo.com

---

## 1. Project Goal

This is a **US brick-and-mortar store BD automation system**, not just an email sender.

End state:
- Auto-collect store leads
- Auto-verify official website emails
- Auto-send outreach emails
- Auto-scan replies / bounces / unsubscribes
- Auto-generate daily reports
- Human only handles hot replies and edge-case exceptions

---

## 2. Current Business Targets

| Stage | Daily Sends | A0 Inventory Floor | Lead Factory Target |
|-------|------------|-------------------|---------------------|
| Current | **20/day** | 60 | 30-50 new A0/day |
| Mid-term | 40-50/day | 150-200 | — |
| End goal | 70-80/day | 300-500 | — |

**Priority cities (Tier 2/3):** Small US cities, tourist towns, college towns, affluent suburbs — NOT major metros.
**Priority store types:** independent toy stores, board game stores, card game shops, puzzle stores, bookstore gift sections, museum stores, gift shops.
**File:** `output/tier2_cities.json` (41 cities in 3 priority tiers)

---

## 3. File Structure

```
roktandrazo-outreach/
├── data/
│   └── bd_leads.db              # SQLite — all leads, logs, config
├── output/
│   ├── b2_high_value_manual_review.csv  # B pool manual review
│   ├── b_pool_manual_review.csv         # B pool source data
│   ├── tier2_cities.json               # 41 priority cities
│   ├── daily_report_*.md               # Session reports
│   └── auto_report_*.md                # Auto operator reports
│
├── [Core Scripts]
│   ├── bd_db.py                 # Database layer (connection, CRUD, pool queries)
│   ├── bd_sender.py             # SMTP sender (Tencent Enterprise email, SSL:465)
│   ├── bd_template.py           # Email template system
│   ├── drafter.py               # Personalized email drafting
│   ├── daily_session.py         # Batch send + scan session (08:30-12:00 window)
│   ├── daily_operator_auto.py   # Orchestrator (preflight→top-up→plan→send→monitor→report)
│   ├── browser_verifier.py      # Playwright-based browser verification agent
│   ├── env_loader.py            # SMTP/IMAP credential loader
│   ├── config.py                # Brand constants (product name, lines, tags)
│
├── [Lead Factory]
│   ├── collection_pipeline.py   # City selector → search → verify → extract → score
│   ├── city_selector.py         # City pool management
│   ├── search_engine.py         # Search result processing (filter, dedup, rank)
│   ├── contact_extractor.py     # Extract contact info from web pages
│   ├── website_verifier.py      # Website reachability + email detection
│   ├── website_audit.py         # Website content audit
│   ├── auto_collector.py        # Auto-collect leads for a city
│   ├── agent_email_verifier.py  # Email verification pipeline
│   ├── scorer_v2.py             # Lead scoring (A/B/C)
│
├── [Monitoring]
│   ├── agent_reply_monitor.py   # IMAP scan → classify replies/bounces/unsubscribes
│   ├── agent_bounce_auditor.py  # Bounce detection + classification
│   ├── bounce_diag.py           # Bounce diagnostic parser
│   ├── bounce_deep.py           # Deep bounce analysis
│   ├── agent_daily_report.py    # Daily report generator
│   └── agent_supervisor.py      # System health supervisor
│
├── [Pool Management]
│   ├── pool_analysis.py         # Pool statistics + CSV generation
│   ├── b_pool_import.py         # B pool CSV → approved_manual_send import
│   └── b_pool_audit_v2.py       # B pool website audit categorizer
│
└── [Configuration]
    └── WorkBuddy Automation: ID=automation-1782369770937 (daily 08:30 trigger)
```

---

## 4. Database Structure

### SQLite: `data/bd_leads.db` (389 KB)

### leads table (43 columns — key fields only)
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | PK |
| store_name | TEXT | Store name |
| store_type | TEXT | e.g. "independent toy store" |
| city / state | TEXT | Location |
| official_website | TEXT | Store URL |
| contact_page | TEXT | Contact page URL |
| wholesale_or_vendor_page | TEXT | Wholesale page URL |
| email | TEXT | Email address |
| email_type | TEXT | business_email / guessed_email / contact_form_only |
| email_source_type | TEXT | official_page_visible / official_mailto / wholesale_vendor_page / guessed_email |
| email_verified_on_official_site | INTEGER | 0/1 |
| contact_form_url | TEXT | |
| evidence_url | TEXT | URL proving email source |
| confidence_score | TEXT | A / B / C |
| status | TEXT | new / sent / bounced / approved_manual_send / do_not_contact |
| mx_provider | TEXT | MX check result |
| domain_hash | TEXT | Hashed domain for duplicate detection |
| email_subject / email_body | TEXT | Drafted email content |
| product_fit | TEXT | card_games / puzzles / both |
| fit_reason | TEXT | Why this store matches |
| manual_* (7 fields) | TEXT | Human approval fields |

### Other tables
| Table | Key Fields | Approx Count |
|-------|-----------|-------------|
| **send_log** | lead_id, email, subject, status, sent_at | ~100 rows |
| **bounce_log** | lead_id, email, bounce_type (hard/policy/soft), diagnostic_code | ~12 rows |
| **reply_log** | lead_id, email, reply_type, summary | ~1 row |
| **suppression_list** | email, reason, added_at | ~22 rows |
| **system_config** | key, value, updated_at | ~25 entries |

### Live Counts (2026-06-29)
| Metric | Count |
|--------|-------|
| Total leads | **323** |
| A0 (verified, sendable) | **3** |
| B (guessed email) | **200** |
| C (contact form) | **29** |
| approved_manual_send | **0** |
| Total sent (lifetime) | ~100 |
| Hard bounced | ~12 |
| Suppressed | ~22 |

---

## 5. Confirmed Conclusions

1. **SPF/DKIM/DMARC** — authenticated, email deliverability is NOT the bottleneck
2. **Sending works** — SMTP (Tencent Enterprise, smtp.exmail.qq.com:465 SSL) successfully delivers
3. **Real bottleneck** — A0 inventory (verified official email) is too small. Lead Factory throughput is insufficient.
4. **`guessed_email` CANNOT be auto-sent** — only official page-verified emails (A0)
5. **B pool (200 leads) CANNOT be dumped on the user** for manual review — needs browser verification first
6. **WebFetch is inadequate** for JS-rendered sites (Shopify/Wix/Squarespace) — real browser required
7. **Send system must shift from approval mode to autonomous mode** within safety boundaries
8. **Exchange / Microsoft 365 MX** is high-risk and excluded from auto-send by default

---

## 6. Pool Definitions (Final)

| Pool | Definition | Auto-send? |
|------|-----------|------------|
| **A0** | Verified Official Email — email visible on official website (footer/contact/about/wholesale) with evidence_url | ✅ Yes |
| **A1** | High-confidence but high-risk (Exchange/MS365 MX) | ❌ Default no, manual override |
| **B** | Guessed email (info@domain.com) — needs browser verification, NOT given to user raw | ❌ No |
| **B2** | High-value manual candidates — max Top 30 after browser audit | Requires human approval |
| **C** | Contact form only — no visible email | ❌ Future contact form agent |
| **D1** | Risk-guess candidates (domain match, high value, no email found) — max 5/day test | ⚠️ Capped risk pool |
| **Invalid** | Dead sites, domain parking, store type mismatch | ❌ Discarded |

---

## 7. Known Pain Points

1. System frequently asks "continue?" instead of autonomously executing within safety boundaries
2. When pool is insufficient, Lead Factory does NOT auto-produce A0 — only checks B pool CSV for pre-approved rows
3. B pool contains many dead/inaccessible websites still passed to user
4. A0 inventory shortage causes daily UNDERFILLED status
5. **Risk:** Previous bulk `UPDATE` mistakenly upgraded 186 B→A0 without verification (rolled back)
6. Missing state machine: `target → deficit → top-up → send → monitor → report`

---

## 8. Required State Machine

```
Daily cycle (08:30 trigger):
  1. Check today_target_count
  2. Check today_sent_count
  3. Check sendable_pool = A0 + approved_manual_send
  4. IF sendable_pool < target:
     → Auto Launch Lead Factory (do not ask)
     → Browser verify B pool leads
     → Upgrade verified A0
  5. IF today_sent < target AND within window AND pool sufficient:
     → Auto-send remaining (do not ask)
  6. IF outside window:
     → Queue for next window
  7. ONLY pause and ask user on:
     - hard_bounce >= 1
     - total_bounce >= 2
     - unsubscribe >= 1
     - template variable error
     - SMTP/IMAP failure
     - About to send guessed_email or B/C leads
  8. End-of-day status: completed / underfilled / paused / failed
```

---

## 9. Auto Pool Top-up Logic

```
B pool (200 leads) processing pipeline:
  1. Website Reachability Audit → exclude dead/irrelevant
  2. Browser Verification (Playwright/Chromium)
     - Check: footer, contact, about, wholesale, vendor, buyer, mailto links
     - Extract visible emails with evidence_url + evidence_snippet
  3. Classification:
     - Email found on official site → A0 (auto-upgrade)
     - Site alive but no email → B2 candidate (Top 30 only)
     - Site alive, contact form only → C pool
     - Dead/wrong → Invalid (discard)
  4. DO NOT: dump entire B pool to user, batch-upgrade guessed emails, skip browser step
```

---

## 10. Strictly Forbidden

- ❌ Send `guessed_email`
- ❌ Send B/C leads
- ❌ Send `delivery_issue` / `bounced` / `suppression_list` entries
- ❌ Send same domain twice
- ❌ Dump WebFetch failures on user
- ❌ Batch-mark unknown emails as verified
- ❌ Mark underfilled tasks as completed

---

## 11. Codex Phase 1 — Code Audit (no changes)

1. Map all file call chains (daily_operator_auto.py → daily_session.py → bd_sender.py → SMTP)
2. Identify state machine gaps (where does `target → deficit → top-up → send` break?)
3. Why does `step_lead_factory()` only check B pool CSV and not auto-collect?
4. Why are B pool 200 leads passed to user instead of browser-verified?
5. Trace `send_pause` / `auto_send_enabled` / `operator_window` logic paths
6. Output a refactoring plan

---

## 12. Codex Phase 2 — Implementation

1. **Lead Factory inventory-first mode** — auto-launch collection when pool < target
2. **Browser Verification Agent** — batch-verify B pool with Playwright, upgrade found emails
3. **B pool cleaner** — audit 200 B leads, categorize into A0/B2/C/Invalid
4. **`post_a0_upgrade_recovery_check()`** — after browser upgrade, auto-send if underfilled
5. **Daily inventory report** — A0 count, AMS count, gap, tomorrow readiness
6. **`underfilled` status tracking** — never mark as completed when below target
7. **Top 30 B2 CSV** — max 30 high-value manual review candidates
8. **Auto-recovery send loop** — close the gap without asking

---

## 13. Acceptance Criteria

- [ ] 3 consecutive days ≥20 sends
- [ ] Hard bounce rate <5%
- [ ] Total bounce rate <10%
- [ ] Daily new A0 ≥20
- [ ] End-of-day inventory ≥60
- [ ] B pool NOT shown as 200-row raw table
- [ ] Only Top 30 high-value candidates for human review
- [ ] Daily report includes: target, actual, gap, root cause, tomorrow readiness

---

## 14. Incident Timeline / Key Events

### Phase 0 (2026-06-08 ~ 06-12)
- Initial 9 sends via personal Gmail SMTP — 2 hard bounces (Comicazi, Dream Wizards on 06-25)
- Switched to Tencent Enterprise Email (ianyf@roktandrazo.com) SMTP 465 SSL

### Phase 1-3 (2026-06-12 ~ 06-17)
- 10 cities Phase 1, 10 cities Phase 2, 10 metros Phase 3
- **SPF/DKIM auth issue (06-17):** Policy bounces on Outlook/Exchange targets — `550 5.4.1 Access denied. SPF/DKIM auth required`. Resolved by configuring SPF/DKIM/DMARC on roktandrazo.com.
- **6 domain/DNS bounces:** dead domains (dragonslair.com, dicedojo.com, gameparlour.com, catandmousegame.com, gamehaus.com, odysseygames.com) — all added to suppression.
- 18 sends on 06-17, 6 bounced

### Bulk Update Incident (2026-06-26)
- `b_pool_audit.py` mistakenly upgraded **186 B→A0** without actual browser verification (all were `info@domain.com` guessed emails matching website domain pattern)
- **Immediately rolled back** — set back to `confidence_score='B'`, `email_source_type='guessed_email'`
- Root cause: audit script checked `email_domain == website_domain` but did NOT check if email actually appears on the official website page
- Lesson: domain matching alone is NOT sufficient for A0 verification; must use browser rendering to confirm email appears on official site

### First Today Catch-up (2026-06-25)
- User manually approved `send_pause=false` for catch-up session
- Sent 20/20 → later 2 hard bounces detected via IMAP scan (Comicazi, Dream Wizards — both added to suppression)
- 1 auto-reply (Chad @ Emerald City Comics — OOO until June 29)

### Underfilled Day (2026-06-26)
- Morning: only 4/20 sent (pool had 6, filters reduced to 4 sendable)
- Same-day Recovery Mode: +9 sent → total 13/20
- **Underfilled** — A0 pool exhausted; Lead Factory slow (5-8 A0/hour manual collection)
- B Pool Audit v2: 0 auto-upgradeable (all guessed emails), all 216 went to B2 CSV

### Browser Verifier Deployed (2026-06-29)
- Installed Playwright + Chromium
- Batch-verified remaining B pool leads
- **Upgraded 14 B→A0** (verified emails found on official sites via real browser)
- Issue: system still asked "add to send queue?" instead of auto-sending
- Manual recovery: drafted 16 + sent 18 today → total today: 18/20
- **A0 pool at end of day: 3** (most sent today)

### Key System Dates
| Date | Sent | Hard Bounce | Status |
|------|------|------------|--------|
| 06-25 | 20 | 2 | completed |
| 06-26 | **13** | 0 | **underfilled** |
| 06-29 | 18 | 0 | **underfilled** |

---

## 15. Business Rules

### Brand Identity
- **Brand:** Roktandrazo (rokt&razo) — Flower Language Puzzle / 花语拼图
- **Contact:** Ian, ianyf@roktandrazo.com
- **Product website:** roktandrazo.com

### Product Line
- **Primary push:** Card games (Capybara Squad, Math Dinos, party/strategy card games)
- **Secondary:** Mini puzzles (24 National Parks, Butterfly Symphony, Global City Tour, 7 themes)
- **Supplemental:** Custom/OEM puzzles
- **Target wholesale margin:** 40-50%
- **Low minimum order:** 12 units to start

### Sourcing
- **Samples:** US warehouse
- **Bulk orders:** Typically shipped from Wenzhou, China
- **Certification:** CPSIA & CE safety certified
- **Free display stand** with first order

### Outreach Rules
- **Do NOT default to Christmas template** — only seasonal when appropriate
- **Do NOT hardcode MOQ or wholesale price** in templates — keep flexible
- **City strategy:** Tier 2/3 US cities, tourist towns, college towns, family-oriented suburbs (not Manhattan/LA/SF main districts)

### Store Type Priority
1. Independent toy stores
2. Board game / tabletop game stores
3. Card game shops (TCG focus)
4. Puzzle specialty stores
5. Bookstore gift sections
6. Museum stores
7. Gift shops (tourist/family-oriented)

---

## 16. Useful Commands

All commands run from `roktandrazo-outreach/` directory using system Python at:
```
C:\Users\15690\AppData\Local\Programs\Python\Python313\python.exe
```

### Dry-run / Safety
```bash
# Dry-run daily session (no real sends)
python daily_session.py --dry-run

# Dry-run auto operator (full pipeline preview)
python daily_operator_auto.py --dry-run --target-count 20 --allow-topup

# Pool analysis (read-only)
python pool_analysis.py
```

### Live Sending
```bash
# Catch-up mode (immediate, no window restriction, 2-3min intervals)
python daily_session.py --live --today-catchup --target-count 20 --deadline "12:00"

# Full auto operator (with top-up and risk stop)
python daily_operator_auto.py --live --target-count 20 --allow-topup --stop-on-risk --model-report
```

### Scanning / Monitoring
```bash
# Reply/bounce monitor (dry-run by default)
python agent_reply_monitor.py --dry-run

# Daily report generation
python agent_daily_report.py --date 2026-06-29
```

### Pool Management
```bash
# B pool CSV import (default dry-run, --live for real write)
python b_pool_import.py --csv output/b_pool_manual_review.csv
python b_pool_import.py --csv output/b_pool_manual_review.csv --live
```

### Browser Verification
```bash
# Test with 5 B pool leads
python browser_verifier.py --test --timeout 15

# Batch verify 50 leads
python browser_verifier.py --batch 50 --timeout 15

# Full B pool verification (all 200+ leads)
python browser_verifier.py --full --timeout 15
```

### Collection Pipeline (seldom used directly)
```bash
python collection_pipeline.py select-cities
python collection_pipeline.py search
python collection_pipeline.py verify
python collection_pipeline.py extract
python collection_pipeline.py score
python collection_pipeline.py save
python collection_pipeline.py full
```

### Database Quick Check
```bash
python -c "from bd_db import get_db; c=get_db().cursor(); c.execute('SELECT confidence_score,status,COUNT(*) FROM leads GROUP BY 1,2'); [print(r) for r in c.fetchall()]"
```

---

## 17. Codex Guardrails / Execution Boundaries

### Phase 1 (Audit Only)
- ✅ Read files, trace call chains, analyze logic
- ✅ Run dry-run commands only
- ✅ Query database (read-only with `SELECT`)
- ❌ No code changes, no file writes
- ❌ No database writes (`INSERT/UPDATE/DELETE`)
- ❌ No real email sends

### Phase 2 (Implementation)
- ✅ Write new scripts, modify existing ones
- ✅ Run dry-run first, then --live after verification
- ❌ **NEVER send real emails without user explicit `--live` confirmation**
- ❌ **NEVER modify `.env` or expose SMTP password** (stored in `env_loader.py` → environment variables)
- ❌ **NEVER drop/truncate/clear the production database** (`data/bd_leads.db`)
- ❌ **NEVER batch-update `confidence_score` or `email_verified_on_official_site`** without per-lead browser verification
- ❌ **NEVER create cron/automation tasks** that auto-send without user approval
- ❌ **NEVER send `guessed_email`, B/C leads, suppressed, or bounced emails**

### Database Safety
```bash
# Always backup before migration
cp data/bd_leads.db "data/bd_leads_backup_$(date +%Y%m%d_%H%M).db"

# All migrations must be reversible or have rollback path
```

### Send Safety
- All send-related changes MUST pass dry-run first
- `--live` flag is the only way to trigger real sends
- `send_pause=true` blocks all real sends regardless of flags
- Template safety check: no `{{`, `}}`, `undefined`, `None`, `null` in email body/subject
- From: `Ian <ianyf@roktandrazo.com>`, Reply-To: `ianyf@roktandrazo.com`
- BCC-to-self enabled for all sends
- Every send logged to `send_log` table
