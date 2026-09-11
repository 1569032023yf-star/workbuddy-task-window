# CURRENT_STATUS — roktandrazo BD Production Handoff

> Repository authority:
> - `1569032023yf-star/workbuddy-task-window` (branch `main`) = **PRODUCTION SOURCE / PRODUCTION HANDOFF** ← this repo
> - `1569032023yf-star/roktandrazo-outreach-codex` = **DEVELOPMENT SOURCE / CODEX HANDOFF** (do NOT write production handoff here)
>
> Generated: 2026-09-11T10:00:00+08:00 (Asia/Shanghai)
> Source of truth for live metrics: `bd_leads.db` (read-only query), automations, Windows Task Scheduler.

---

## C. REQUIRED CURRENT STATUS FIELDS

```
CURRENT_PHASE              = PHASE_4A_COMPLETE / PERMANENT_HANDOFF_MODE_SETUP (2026-09-11)
PRODUCTION_STATUS          = FROZEN (P1.9 SYSTEM_FREEZE=true); canonical scheduler ACTIVE;
                             no sends since 2026-09-03 (SAFE_FSP materialized=0, by-design fail-closed)
CURRENT_BLOCKER            = SAFE_FSP materialized pool = 0. V2-eligible read-only proxy = 12 leads / 11 orgs
                             but NOT materialized into Final Send Plan (review gate fail-closed:
                             status=manual_review_needed + auto_sendable=0). Root cause = review gate +
                             BroadReady short-circuit (email-recovery lane skipped). 428 no-email leads
                             need OFFICIAL_EMAIL_ENRICHMENT (separate authorization, not auto).
PRODUCTION_SCHEDULER_AUTHORITY = WorkBuddy Automation (workbuddy_automation) — SOLE scheduler authority.
                             BDExecutionHost Windows Service = Stopped (not scheduler).
                             No second/parallel scheduler. PostSend runs as UNIQUE_REQUIRED Windows task.
WORKBUDDY_AUTOMATIONS      = see section below
WINDOWS_TASKS              = see section below
DUPLICATE_ACTIVE_TRIGGER_COUNT = 0   (PreSend/Outreach Disabled; PostSend is UNIQUE_REQUIRED, not duplicate)
PRODUCTION_CODE_SHA        = da36acfdbd19c896f3fdc0dc1bc1e16ac2b42eb4  (HEAD of workbuddy-task-window/main; unchanged this session)
DATABASE_SCHEMA_CHANGED    = false  (no migrations; P1.9 freeze intact)
FROZEN_FILES_CHANGED       = false  (V2 / MX / Preflight / Sender / final_send_plan / campaign_eligible_v2 untouched;
                                     only automation status toggles on 9/9–9/10, no handoff-code edits this session)
SAFE_METRIC_DEFINITION     = see section D (5 distinct metrics, each with authority)
SAFE_CURRENT               = canonical SAFE_FSP (materialized final_send_plan.status='planned') = 0
                             (read-only V2-eligible unique orgs = 11 — reported separately, NOT as "SAFE")
LAST_INVENTORY_RUN         = 2026-09-10 11:27 (one-off immediate authorized run); daily 15:00 automation ACTIVE.
                             No local execution-log timestamp persisted in DB.
LAST_PRESEND_RUN           = Scheduled Mon-Fri 21:30 (automation-1785804406748, ACTIVE).
                             Last local execution-log timestamp not persisted in DB.
LAST_PREFLIGHT_RUN         = Scheduled Mon-Fri 21:50 (automation-1785804413719, ACTIVE).
                             Last local execution-log timestamp not persisted in DB.
LAST_OUTREACH_RUN          = Scheduled Mon-Fri 22:00 (automation-1785804421539, ACTIVE).
                             Last actual send = 2026-09-03 01:10 (+08:00) per send_log.
LAST_POSTSEND_RUN          = 2026-09-10 00:10:01 (Windows task RoktRazo-BD-PostSend, result 0).
NEXT_ACTION                = (1) Resolve SAFE=0: authorize OFFICIAL_EMAIL_ENRICHMENT for 428 no-email leads
                             OR relax review gate for V2-eligible manual_review_needed leads (user authorization required, not auto).
                             (2) Continue permanent handoff: every future production audit/result synced here.
                             (3) RECOMMENDED: purge already-tracked *.db files from repo history per safe-git rule E
                             (separate destructive authorization — history rewrite).
                             (4) Migrate PostSend Windows task → WorkBuddy automation when new-automation allowed.
```

### WORKBUDDY_AUTOMATIONS (canonical, sole scheduler)
| Automation ID | Name | Schedule | State |
|---|---|---|---|
| 1784775229336 | BD Inventory | daily 15:00 | ACTIVE |
| 1785804406748 | BD Production Pre-Send | Mon–Fri 21:30 | ACTIVE |
| 1785804413719 | BD Production Preflight | Mon–Fri 21:50 | ACTIVE |
| 1785804421539 | BD Production Outreach | Mon–Fri 22:00 | ACTIVE |
| 1786002601925 | Result Recovery Sync | daily 08:45 | ACTIVE (support job, not a stage trigger) |

> No independent PostSend / EndOfDay WorkBuddy automations exist. (PostSend = Windows task, see below.)
> P3D cleanup (2026-09-09) removed 5 legacy automations; canonical trigger count per stage = 1.

### WINDOWS_TASKS
| Task Name | State | Classification |
|---|---|---|
| RoktRazo-BD-PreSend | Disabled | DUPLICATE of canonical Pre-Send (suppressed) |
| RoktRazo-BD-Outreach | Disabled | DUPLICATE of canonical Outreach (suppressed) |
| RoktRazo-BD-PostSend | Ready / Enabled | UNIQUE_REQUIRED — runs `bd_orchestrator.py --stage post-send` 00:10 daily; no WorkBuddy equivalent exists |

---

## D. SAFE / POOL METRICS — EXPLICIT DEFINITIONS (no bare "SAFE = X")

> ⚠️ METRIC_DEFINITION_MISMATCH_FOUND = true. Past reports used "SAFE" for three different things
> (read-only V2 eligibility ≠ materialized Final Send Plan ≠ BroadReady ≠ evidence count).
> All five are reported separately below with their authority.

| Metric | Value (live 2026-09-11) | Authority |
|---|---|---|
| **V2_ELIGIBLE_UNSENT** | **12** leads | `leads` table, read-only SQL proxy (email NOT NULL + `email_verified_on_official_site=1` + status NOT IN terminal + `email_source_type` NOT IN ('guessed') + `evidence_checked_at` ≤90d). **Canonical authority = `campaign_eligible_v2.review_campaign_eligible_v2()` which additionally requires live MX=ok (DNS) — NOT enforced in this proxy. True canonical V2 count ≤ 12 and requires running the Python function with network access.** |
| **READ_ONLY_SAFE_UNIQUE_ORGS** | **11** orgs | distinct `leads.organization_key` among the V2-eligible proxy set above. Authority: `leads.organization_key`. This is the "Phase 4A SAFE=1-ish" read-only eligibility count (lead 1085 entered 1 new org on 2026-09-10). |
| **MATERIALIZED_FSP_PLANNED** | **0** (0 orgs) | `final_send_plan.status='planned'` rows (canonical production SAFE_FSP). Authority: `final_send_plan`. **This is the real "SAFE" the frozen send chain consumes.** |
| **BROAD_READY** | **95** | `leads.send_eligibility='broad_outreach_ready'`. Authority: `leads.send_eligibility`. Separate from SAFE_FSP; satisfies Broad Outreach pool only. |
| **VISIBLE_FIRST_PARTY_EMAILS** | **338** (canonical) | Canonical = `leads.email NOT NULL AND email_verified_on_official_site=1 AND status NOT IN terminal`. Authority: `leads`. ⚠️ Code contains conflicting looser definitions: D1≈914 (excl manual_lookup, all non-null non-terminal) and D2≈983 (incl manual_lookup) — these inflate the count by including `email_source_type='unknown'`(387)/`'guessed_email'`(167). **Do not mix these with the canonical 338.** |

### Supporting live facts (read-only)
- TOTAL_LEADS = 1069 · TOTAL_SENT = 516 · FULL_EVIDENCE_RECORDS (evidence_url NOT NULL) = 897
- LAST_SEND_LOG_TS = 2026-09-03T01:10:35+08:00 · LAST_FSP_CREATED_TS = 2026-09-02 14:32:08
- Manual review backlog: `status='manual_review_needed'` = 480 (dominant blocker to materialization)

### One-line rule
**read-only V2 eligibility (12/11) ≠ materialized Final Send Plan (0) ≠ BroadReady (95) ≠ visible first-party emails (338).**
Report all five. Never summarize production readiness with a single "SAFE = X".
