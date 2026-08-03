# PROJECT_SKILLS_RECONSTRUCTED.md

> **Project Skills Reconstructed — Actual Capabilities**
> Generated: 2026-07-07T14:33+08:00
> Scope: All actual capabilities found in the project, whether installed as skill or not

---

## 1. Browser Verification / 浏览器验证

### Details

| Field | Value |
|-------|-------|
| **Capability** | Browser Verification / 浏览器验证 |
| **Script** | `roktandrazo-outreach/browser_verifier.py` |
| **Input** | B-grade leads from database |
| **Output** | A0 upgrades (email found on official website) / B2 manual_review_needed / C contact_form_pool |
| **Production Ready?** | ✅ YES — tested, deployed |
| **Risk** | Playwright dependency, ~60s/lead (slow) |
| **Codex Migration?** | ⚠️ Should read, not rewrite |

### Description

Playwright-based browser verification that checks official websites for visible email addresses. Scans footer, contact, about, wholesale, vendor, buyer pages. Extracts emails with evidence_url + evidence_snippet.

### Dependencies

- `playwright` (Python package)
- Chromium browsers (installed at `~/.local/share/ms-playwright/`)

---

## 2. Fast Lead Discovery / 快速线索发现

### Details

| Field | Value |
|-------|-------|
| **Capability** | Fast Lead Discovery / 快速线索发现 |
| **Script** | `roktandrazo-outreach/fast_lead_discovery.py` |
| **Input** | Candidate URLs from search results |
| **Output** | A0 upgrades / B2 candidates / C candidates |
| **Production Ready?** | ✅ YES — tested, 19x faster than Browser Verifier |
| **Risk** | Playwright fallback dependency |
| **Codex Migration?** | ⚠️ Should read, not rewrite |

### Description

HTTP-first + Playwright fallback pipeline. Uses httpx + BeautifulSoup for fast extraction, falls back to Playwright for JS-rendered sites. Average 3.1s/lead (19x faster than Browser Verifier's 60s).

### Dependencies

- `httpx` (Python package)
- `beautifulsoup4` (Python package)
- `playwright` (Python package, fallback)

---

## 3. Google Maps Branch / Google Maps 候选发现

### Details

| Field | Value |
|-------|-------|
| **Capability** | Google Maps Branch / Google Maps 候选发现 |
| **Script** | `tools/google-maps-scraper/gmaps_fast_poc.py` |
| **Input** | Search queries (toy store, gift shop, etc.) + city/state |
| **Output** | CSV with store name, address, phone, rating, website |
| **Production Ready?** | ⚠️ POC stage — tested successfully |
| **Risk** | Anti-scrape detection, rate limiting |
| **Codex Migration?** | ✅ Should read and potentially integrate |

### Description

Playwright-based Google Maps scraper that extracts search result cards (not detail pages). Fast mode: ~2s/query. Successfully tested on 8 TN cities, found 238 candidates → 217 new independent stores.

### Dependencies

- `playwright` (Python package)
- Chromium browsers

### Related Files

- `tools/google-maps-scraper/gmaps_playwright_poc.py` — Full Playwright POC
- `tools/google-maps-scraper/inventory_shift_ar_ky.py` — AR/KY inventory shift
- `tools/google-maps-scraper/inventory_shift_live.py` — Live inventory shift
- `tools/google-maps-scraper/queries_tn.txt` — TN search queries
- `GOOGLE_MAPS_BRANCH_POC_REPORT.md` — POC report
- `GOOGLE_MAPS_ANTI_SCRAPE_NOTE_CN.md` — Anti-scrape notes
- `GOOGLE_MAPS_CANDIDATES_TN_SAMPLE.csv` — TN sample data

### Note

`gmaps-scraper.exe` (gosom Go binary) was also downloaded but failed testing with "unexpected page type" error. Use `gmaps_fast_poc.py` instead.

---

## 4. B2 Manual Queue / B2 人工联系方式队列

### Details

| Field | Value |
|-------|-------|
| **Capability** | B2 Manual Queue / B2 人工联系方式队列 |
| **Script** | `roktandrazo-outreach/b_pool_audit_v2.py` + manual process |
| **Input** | B-grade leads with accessible websites but no email found |
| **Output** | Top 30 high-value candidates for human email lookup |
| **Production Ready?** | ✅ YES — tested, deployed |
| **Risk** | Manual effort required |
| **Codex Migration?** | ⚠️ Should read, not rewrite |

### Description

B2 pool contains leads that passed website audit but no email was found automatically. Top 30 are selected by small city + store type priority for human email lookup. CSV with manual fill-in fields.

### Related Files

- `BRANCH_B_MANUAL_CONTACT_TOP20.md` — Top 20 manual contact
- `BRANCH_B_BLOCKED_REASON_SUMMARY.md` — Blocked reasons
- `MANUAL_CONTACT_FETCH_QUEUE.csv` — 217 candidates → 30 for manual lookup
- `MANUAL_CONTACT_FETCH_QUEUE_CN.md` — Queue description
- `MANUAL_CONTACT_FETCH_TOP30_CN.md` — Top 30 details
- `MANUAL_CONTACT_IMPORT_INSTRUCTIONS_CN.md` — Import instructions

---

## 5. Bounce Auditor / 退信审计

### Details

| Field | Value |
|-------|-------|
| **Capability** | Bounce Auditor / 退信审计 |
| **Script** | `roktandrazo-outreach/agent_bounce_auditor.py` |
| **Input** | IMAP scan results |
| **Output** | Bounce classification (hard/policy/message_id_missing/soft/unknown) |
| **Production Ready?** | ⚠️ Needs Message-ID fix |
| **Risk** | Message-ID missing bounces misclassified as hard |
| **Codex Migration?** | ✅ Should apply Message-ID fix |

### Description

Bounce detection + classification. Classifies bounces as hard, policy, message_id_missing, soft, or unknown. Hard bounces auto-suppress. Message-ID missing bounces should NOT suppress.

### Dependencies

- `imaplib` (Python stdlib)
- `email` (Python stdlib)

---

## 6. Reply Monitor / 回信监控

### Details

| Field | Value |
|-------|-------|
| **Capability** | Reply Monitor / 回信监控 |
| **Script** | `roktandrazo-outreach/agent_reply_monitor.py` |
| **Input** | IMAP scan results |
| **Output** | Reply classification (hot/warm/negative/auto/unsubscribe) |
| **Production Ready?** | ✅ YES — tested |
| **Risk** | IMAP dependency |
| **Codex Migration?** | ⚠️ Should read, not rewrite |

### Description

IMAP scan → classify replies as hot_reply, warm_reply, negative_reply, auto_reply, unsubscribe. Hot replies get priority follow-up. Unsubscribes get added to suppression.

### Dependencies

- `imaplib` (Python stdlib)
- `email` (Python stdlib)

---

## 7. Daily Orchestrator / 每日编排

### Details

| Field | Value |
|-------|-------|
| **Capability** | Daily Orchestrator / 每日编排 |
| **Script** | `roktandrazo-outreach/daily_operator_auto.py` |
| **Input** | Database state, send window, pool counts |
| **Output** | Daily sends, reports, risk triggers |
| **Production Ready?** | ✅ YES — tested, deployed |
| **Risk** | Complex state machine |
| **Codex Migration?** | ⚠️ Should read, not rewrite |

### Description

7-step daily orchestrator: preflight → top-up → plan → send → monitor → risk → report. Runs at 09:00 Asia/Shanghai. Same-day Deficit Recovery Loop: while actual_sent < 20, recover pool → dry-run → live.

### Related Files

- `roktandrazo-outreach/daily_session.py` — Batch send session
- `roktandrazo-outreach/bd_sender.py` — SMTP sender
- `roktandrazo-outreach/bd_db.py` — Database layer
- `roktandrazo-outreach/bd_template.py` — Email template (V5)
- `roktandrazo-outreach/agent_daily_report.py` — Daily report generator

---

## 8. State Deep Coverage / 州级深度覆盖

### Details

| Field | Value |
|-------|-------|
| **Capability** | State Deep Coverage / 州级深度覆盖 |
| **Script** | `roktandrazo-outreach/city_selector_v2.py` |
| **Input** | Primary state pool (TN/AR/KY) |
| **Output** | City selection for lead collection |
| **Production Ready?** | ✅ YES — tested |
| **Risk** | State filtering logic |
| **Codex Migration?** | ⚠️ Should read, not rewrite |

### Description

City selector with state filtering capability. Primary states: TN, AR, KY. Backup states: FL, UT, SC. "农村包围城市" strategy: small cities first, then medium, then large city suburbs.

### Related Files

- `roktandrazo-outreach/city_selector.py` — Original city selector
- `primary_state_cities.json` — 44 TN/AR/KY cities
- `CITY_EXPANSION_RULES.md` — City strategy
- `INVENTORY_SHIFT_PLAN_TN_AR_KY.md` — TN/AR/KY priority cities

---

## 9. Inventory Shift / 库存班次

### Details

| Field | Value |
|-------|-------|
| **Capability** | Inventory Shift / 库存班次 |
| **Script** | `tools/google-maps-scraper/inventory_shift_live.py` |
| **Input** | Primary state cities + search queries |
| **Output** | New A0 leads for pool replenishment |
| **Production Ready?** | ⚠️ POC stage |
| **Risk** | Anti-scrape detection |
| **Codex Migration?** | ✅ Should read and potentially integrate |

### Description

Afternoon inventory shift (13:30-17:30 Asia/Shanghai) to replenish A0 pool. Uses Google Maps scraper to find new candidates in primary states. Target: sendable_pool >= 60.

### Related Files

- `tools/google-maps-scraper/inventory_shift_ar_ky.py` — AR/KY inventory shift
- `INVENTORY_SHIFT_AR_KY_CANDIDATES.csv` — AR/KY candidates
- `INVENTORY_SHIFT_TN_AR_KY_LIVE.csv` — TN/AR/KY live data

---

## 10. Pool Analysis / 池分析

### Details

| Field | Value |
|-------|-------|
| **Capability** | Pool Analysis / 池分析 |
| **Script** | `roktandrazo-outreach/pool_analysis.py` |
| **Input** | Database state |
| **Output** | Pool statistics + CSV generation |
| **Production Ready?** | ✅ YES — tested |
| **Risk** | None |
| **Codex Migration?** | ⚠️ Should read, not rewrite |

### Description

Pool statistics + CSV generation. Shows A0/B2/C/AMS counts, sendable pool, gap to target. Generates B pool CSV with 7 manual fields.

---

## 11. Email Template / 邮件模板

### Details

| Field | Value |
|-------|-------|
| **Capability** | Email Template / 邮件模板 |
| **Script** | `roktandrazo-outreach/bd_template.py` |
| **Input** | Lead data (store_name, etc.) |
| **Output** | Personalized email subject + body |
| **Production Ready?** | ✅ YES — V5 template |
| **Risk** | Template variable errors |
| **Codex Migration?** | ⚠️ Should read, not rewrite |

### Description

V5 template: "Premium puzzles & card games for {store} (Low MOQ / DDP)". 4 bullet points (Low MOQ, Premium puzzles, Custom, Supply chain). Catalogue mention. No Zoom. No "Play Learn Laugh".

---

## 12. Lead Scoring / 线索评分

### Details

| Field | Value |
|-------|-------|
| **Capability** | Lead Scoring / 线索评分 |
| **Script** | `roktandrazo-outreach/scorer_v2.py` |
| **Input** | Lead data (website, email, etc.) |
| **Output** | A/B/C grade |
| **Production Ready?** | ✅ YES — tested |
| **Risk** | MX check dependency |
| **Codex Migration?** | ⚠️ Should read, not rewrite |

### Description

V2.1 scoring rules. A: official website + official email + evidence_url. B: guessed email or contact form. C: no email, no website, or invalid. MX check for domain validation.

---

## 13. IMAP/SMTP Email / IMAP/SMTP 邮件

### Details

| Field | Value |
|-------|-------|
| **Capability** | IMAP/SMTP Email / IMAP/SMTP 邮件 |
| **Skill** | `~/.workbuddy/skills/skill_2053082149365157888/` |
| **Input** | IMAP/SMTP credentials |
| **Output** | Read/send emails |
| **Production Ready?** | ✅ YES — installed skill |
| **Risk** | Credential exposure |
| **Codex Migration?** | ✅ Already available as skill |

### Description

IMAP/SMTP email skill. Read, search, and manage email via IMAP protocol. Send email via SMTP. Supports Gmail, Outlook, 163.com, etc.

---

## 14. US Retail Lead Collector / 美国零售线索收集

### Details

| Field | Value |
|-------|-------|
| **Capability** | US Retail Lead Collector / 美国零售线索收集 |
| **Skill** | `~/.workbuddy/skills/us-retail-lead-collector/` |
| **Input** | Store lists from KB knowledge |
| **Output** | A/B/C graded leads in SQLite |
| **Production Ready?** | ⚠️ Disabled (`disable: true`) |
| **Risk** | None |
| **Codex Migration?** | ✅ Should enable |

### Description

Agent-created skill for lead collection pipeline. Imports store lists, validates email domains (MX records), applies V2.1 scoring rules, deduplicates against SQLite, generates phase reports.

---

## 15. Playwright + Chromium / Playwright + Chromium

### Details

| Field | Value |
|-------|-------|
| **Capability** | Playwright + Chromium / Playwright + Chromium |
| **Package** | `playwright 1.60.0` |
| **Browsers** | `chromium-1200`, `chromium-1223` |
| **Location** | `~/.local/share/ms-playwright/` |
| **Production Ready?** | ✅ YES — installed |
| **Risk** | None |
| **Codex Migration?** | ✅ Already available |

### Description

Playwright browser automation framework with Chromium browsers. Used by browser_verifier.py, fast_lead_discovery.py, and gmaps_fast_poc.py.

---

## 16. HTTP Libraries / HTTP 库

### Details

| Field | Value |
|-------|-------|
| **Capability** | HTTP Libraries / HTTP 库 |
| **Packages** | `httpx 0.28.1`, `beautifulsoup4 4.15.0` |
| **Production Ready?** | ✅ YES — installed |
| **Risk** | None |
| **Codex Migration?** | ✅ Already available |

### Description

HTTP client (httpx) and HTML parser (BeautifulSoup) for fast web scraping. Used by fast_lead_discovery.py for HTTP-first extraction.

---

## Summary Table

| # | Capability | Script/Skill | Status | Codex Migration |
|---|-----------|--------------|--------|-----------------|
| 1 | Browser Verification | browser_verifier.py | ✅ Ready | Read only |
| 2 | Fast Lead Discovery | fast_lead_discovery.py | ✅ Ready | Read only |
| 3 | Google Maps Branch | gmaps_fast_poc.py | ⚠️ POC | Read + integrate |
| 4 | B2 Manual Queue | b_pool_audit_v2.py | ✅ Ready | Read only |
| 5 | Bounce Auditor | agent_bounce_auditor.py | ⚠️ Needs fix | Apply Message-ID fix |
| 6 | Reply Monitor | agent_reply_monitor.py | ✅ Ready | Read only |
| 7 | Daily Orchestrator | daily_operator_auto.py | ✅ Ready | Read only |
| 8 | State Deep Coverage | city_selector_v2.py | ✅ Ready | Read only |
| 9 | Inventory Shift | inventory_shift_live.py | ⚠️ POC | Read + integrate |
| 10 | Pool Analysis | pool_analysis.py | ✅ Ready | Read only |
| 11 | Email Template | bd_template.py | ✅ Ready | Read only |
| 12 | Lead Scoring | scorer_v2.py | ✅ Ready | Read only |
| 13 | IMAP/SMTP Email | skill_2053082149365157888 | ✅ Ready | Already available |
| 14 | US Retail Lead Collector | us-retail-lead-collector | ⚠️ Disabled | Enable |
| 15 | Playwright + Chromium | playwright 1.60.0 | ✅ Ready | Already available |
| 16 | HTTP Libraries | httpx + beautifulsoup4 | ✅ Ready | Already available |

---

## Recommendations

1. **Create `PROJECT_SKILLS.md`** — document all 16 capabilities
2. **Enable `us-retail-lead-collector` skill** — currently disabled
3. **Apply Message-ID fix** — to agent_bounce_auditor.py
4. **Integrate Google Maps Branch** — gmaps_fast_poc.py works well
5. **Read legacy tools** — understand full system before rewriting
