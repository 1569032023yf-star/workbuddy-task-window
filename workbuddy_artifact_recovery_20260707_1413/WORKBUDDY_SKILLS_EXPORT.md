# WORKBUDDY_SKILLS_EXPORT.md

> **WorkBuddy Skills Export — BD Automation Rules**
> Generated: 2026-07-07T14:13+08:00
> Source: Reconstructed from `.workbuddy/memory/MEMORY.md`, daily logs, handoff packages, and project reports

---

## ⚠️ Notice

**Original WorkBuddy skills not found.** No `skills/` directory exists in the project workspace (`.workbuddy/skills/` is empty). This file is reconstructed from available project reports, memory logs, and conversation handoff documents.

---

## 1. Pool Definitions (A0 / B / B2 / C / Suppression)

### A0 — Verified Official Email (Auto-sendable)

**Definition**:
- Email visible on official website (footer, contact, about, wholesale, vendor, buyer page)
- Has `evidence_url` proving email source
- `email_verified_on_official_site = 1`
- `email_source_type IN ('official_page_visible', 'official_mailto', 'wholesale_vendor_page')`
- NOT in `suppression_list`
- NOT already sent (`send_log` check)
- NOT Exchange/Microsoft 365 MX (unless manually approved)
- `confidence_score = 'A'`

**Auto-send**: ✅ YES

### A1 — High-Confidence but High-Risk (Exchange MX)

**Definition**:
- Same as A0 but MX is Exchange/Microsoft 365
- `mx_provider LIKE '%exchange%' OR '%outlook%' OR '%microsoft%'`

**Auto-send**: ❌ Default no, manual override required

### B — Guessed Email

**Definition**:
- Email exists but NOT verified on official website
- `email_source_type = 'guessed_email'`
- Typically `info@domain.com` pattern
- `confidence_score = 'B'`

**Auto-send**: ❌ NO — never auto-send guessed emails

### B2 — High-Value Manual Candidates

**Definition**:
- B-grade leads that passed website audit
- Status: `manual_review_needed`
- Max Top 30 for human review
- Must have `official_website` accessible

**Auto-send**: ❌ Requires human approval

### C — Contact Form Only

**Definition**:
- No visible email on website
- Only contact form available
- `confidence_score = 'C'`

**Auto-send**: ❌ Future contact form agent

### Suppression List

**Definition**:
- Emails that have hard bounced
- Emails that have unsubscribed
- Emails with `do_not_contact` status
- Stored in `suppression_list` table

**Rule**: Once suppressed, NEVER re-send. Period.

---

## 2. Daily Target & Inventory

### Daily Target

- **Target**: 20 emails/day (never reduce)
- **Mid-term**: 40-50/day
- **End goal**: 70-80/day

### Inventory Floor

- **Healthy**: ≥ 60 A0 sendable
- **Low**: 20-59 A0 sendable
- **Critical**: < 20 A0 sendable

### Send Window

- **Timezone**: Asia/Shanghai
- **Window**: 09:00–13:00 Asia/Shanghai
- **Batches**: 4 batches, 2-3 minute intervals
- **Outside window**: Queue for next window

---

## 3. State Deep Coverage Strategy

### Primary States (First Batch)

- **Tennessee (TN)** — 10 cities
- **Arkansas (AR)** — 8 cities
- **Kentucky (KY)** — 4 cities

### Backup States (Second Batch)

- **Florida (FL)**
- **Utah (UT)**
- **South Carolina (SC)**

### Collection Mode

- **Mode**: State Deep Coverage — no random cross-state, no nationwide sweep
- **Emergency Out-of-State Recovery**: If Same-day Deficit Recovery requires cross-state, must mark as `emergency_recovery`

### City Strategy

- **Philosophy**: "农村包围城市" (rural surrounds city)
- **Priority**: small towns > tourist towns > national park gateways > college towns > historic towns > affluent suburbs > large city outskirts
- **NOT**: major metros (Manhattan, LA, SF main districts)

---

## 4. Collection Pipeline

### Entry Points (Priority Order)

1. **Google Maps** — Playwright scraper, candidate discovery
2. **Facebook** — Store pages
3. **Official Website** — Direct verification
4. **Chamber of Commerce** — Directory listings
5. **Tourism Directory** — Local tourism sites
6. **Web Search** — Fallback

### Source Channels

```
google_maps / facebook_page / official_website / chamber_directory / 
tourism_directory / main_street_directory / web_search / manual_seed / emergency_recovery
```

### Google Maps Rules

- Google Maps is **candidate discovery only** — NOT verification
- Must verify via official website before upgrading to A0
- Anti-scrape: rate limiting, rotating queries, respecting robots.txt

---

## 5. Email Verification Rules

### Website Verification is Required for A0

- **Domain matching alone is NOT sufficient** — `email_domain == website_domain` does NOT prove email appears on official site
- **Must use browser rendering** to confirm email appears on official site footer/contact/about/wholesale page
- **Evidence required**: `evidence_url` (URL where email was found) + `evidence_snippet` (text snippet proving email location)

### Evidence Fields

- **`evidence_url`**: URL where email was found on official website
- **`evidence_snippet`** (new): Text snippet proving email location (e.g., "Contact us: info@store.com" from footer)
- **`notes`** (legacy): Previously used for evidence, now superseded by `evidence_snippet`

### Upgrade Rules

- `email_verified_on_official_site = 1` ONLY when email found on official site via browser
- `email_source_type` must be set correctly
- `confidence_score` must match verification level

---

## 6. Email Template Rules

### V5 Template (Current)

- **Subject**: "Premium puzzles & card games for {store} (Low MOQ / DDP)"
- **Body**: "puzzle and family card game brand"
- **Bullets**: 4 (Low MOQ, Premium puzzles, Custom, Supply chain)
- **Catalogue**: Mentioned
- **Zoom**: NOT included
- **Slogan**: NOT "Play, Learn, Laugh!"

### Template Safety

- No `{{`, `}}`, `undefined`, `None`, `null` in email body/subject
- All variables must be replaced before sending
- Dry-run must pass template safety check

### Sender Identity

- **From**: Ian <ianyf@roktandrazo.com>
- **Reply-To**: ianyf@roktandrazo.com
- **BCC-to-self**: ✅ Always enabled

---

## 7. Bounce Classification Rules

### Bounce Types

| Type | Action | Suppress? |
|------|--------|-----------|
| **hard** | Permanent failure (550, user unknown) | ✅ YES — auto-suppress |
| **policy** | Receiving server policy rejection | ❌ NO — count but don't suppress |
| **message_id_missing** | Message-ID header missing | ❌ NO — fix sender, don't suppress |
| **soft** | Temporary failure (4xx) | ❌ NO — retry later |
| **unknown** | Unclassified | ❌ NO — manual review |

### Message-ID Header Requirement

- **CRITICAL**: `bd_sender.py:_build_email()` MUST set `Message-ID` header
- **Format**: `make_msgid(domain="roktandrazo.com")`
- **Bounce handling**: Missing Message-ID bounces are `message_id_missing` type, NOT `hard`
- **Suppression rule**: `message_id_missing` NEVER triggers suppression

### Bounce Detection Signals

```
# Hard bounce signals
['550 ', '5.1.1', 'user unknown', 'no such user', 'mailbox not found']

# Policy bounce signals  
['5.4.1', '5.7.1', 'access denied', 'relaying denied', 'rejected by policy', 'blocked']

# Message-ID bounce signals
['message-id', 'missing message-id', 'malformed message-id', 'missing required headers']
```

---

## 8. Reply Classification Rules

### Reply Types

| Type | Signals | Action |
|------|---------|--------|
| **hot_reply** | catalog, pricing, wholesale, MOQ, sample, interested | Priority follow-up |
| **warm_reply** | maybe, later, send details, more information | Standard follow-up |
| **negative_reply** | not interested, no thanks, remove me | Add to suppression |
| **auto_reply** | out of office, vacation, automatic reply | Log, no action |
| **unsubscribe** | unsubscribe, remove me, do not contact | Add to suppression |

---

## 9. Safety Rules (Guardrails)

### Absolute Prohibitions

1. ❌ Send `guessed_email` (B-grade)
2. ❌ Send B/C leads
3. ❌ Send `delivery_issue` / `bounced` / `suppression_list` entries
4. ❌ Send same domain twice
5. ❌ Dump WebFetch failures on user
6. ❌ Batch-mark unknown emails as verified
7. ❌ Mark underfilled tasks as completed
8. ❌ Modify `.env` or expose SMTP password
9. ❌ Drop/truncate/clear production database
10. ❌ Batch-update `confidence_score` without per-lead browser verification
11. ❌ Create cron/automation tasks that auto-send without user approval

### Safe Operations

1. ✅ Read files, trace call chains, analyze logic
2. ✅ Run dry-run commands only
3. ✅ Query database (read-only with `SELECT`)
4. ✅ Generate reports

### Send Safety

- All send-related changes MUST pass dry-run first
- `--live` flag is the only way to trigger real sends
- `send_pause=true` blocks all real sends regardless of flags
- Every send logged to `send_log` table

---

## 10. Orchestrator Logic

### Daily Orchestrator Steps

```
1. Preflight — check SMTP, check pools
2. Inventory Recovery — if sendable_pool < target, auto-recover
3. Dry-run — preview sends
4. Live — send if within window and pool sufficient
5. Monitor — scan bounces/replies
6. Risk Check — stop if hard_bounce >= 1 or total_bounce >= 2
7. Report — generate daily report
```

### Same-day Deficit Recovery

```
while actual_sent < 20:
    1. Check existing pool (A0 + AMS)
    2. If insufficient → Lead Factory (new city collection)
    3. Recheck pool
    4. If still insufficient → report underfilled
    5. If sufficient → dry-run → live send
```

### Stop Conditions

- Hard bounce ≥ 1 → stop sending
- Total bounce ≥ 2 → stop sending
- Unsubscribe ≥ 1 → stop sending
- Template variable error → stop sending
- SMTP/IMAP failure → stop sending
- About to send guessed_email or B/C leads → stop sending

---

## 11. Reporting Rules

### Daily Report Must Include

- Target count
- Actual sent count
- Gap (target - actual)
- Root cause (if underfilled)
- Tomorrow readiness (A0 count, AMS count)
- Risk triggers (bounces, unsubs)

### Bilingual Requirement

- All reports must be **中英双语** (Chinese + English)
- Headers in both languages
- Key findings in both languages

### Report Types

- **Daily orchestration report** — generated by `agent_daily_report.py`
- **Collection report** — new leads found
- **Bounce report** — bounce classification
- **Inventory report** — pool statistics
- **Weekly review** — summary for Neil

---

## 12. Database Schema (Key Tables)

### leads table (43+ columns)

Key fields:
- `id`, `store_name`, `store_type`, `city`, `state`
- `official_website`, `contact_page`, `wholesale_or_vendor_page`
- `email`, `email_type`, `email_source_type`
- `email_verified_on_official_site`, `evidence_url`, `evidence_snippet` (new)
- `confidence_score` (A/B/C), `status`
- `mx_provider`, `domain_hash`
- `email_subject`, `email_body`
- `manual_*` (7 fields for human approval)

### Other tables

- `send_log` — send history
- `bounce_log` — bounce history
- `reply_log` — reply history
- `suppression_list` — suppressed emails
- `system_config` — key-value config

---

## 13. Key Configuration Values

| Key | Value | Source |
|-----|-------|--------|
| `daily_target` | 20 | system_config |
| `inventory_floor` | 60 | system_config |
| `send_window` | 09:00-13:00 | system_config |
| `send_window_timezone` | Asia/Shanghai | system_config |
| `inventory_shift` | 13:30-17:30 | system_config |
| `primary_state_pool` | ['TN', 'AR', 'KY'] | system_config |
| `backup_state_pool` | ['FL', 'UT', 'SC'] | system_config |
| `city_selector_mode` | primary_state_only | system_config |
| `auto_send_enabled` | true | system_config |
| `send_pause` | false | system_config |

---

## 14. Automation Tasks

### Active Automation

- **ID**: `automation-1782800192924`
- **Name**: "Roktandrazo BD Daily Orchestrator - 09:00 China Time"
- **Schedule**: Daily 09:00 Asia/Shanghai
- **Script**: `daily_operator_auto.py`
- **Logic**: Same-day Deficit Recovery Loop

### Paused Automation

- **ID**: `automation-1782369770937`
- **Name**: "BD Daily Send — 08:30 Auto Operator"
- **Status**: PAUSED (replaced by newer automation)
