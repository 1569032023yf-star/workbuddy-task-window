# CURRENT_STATUS — roktandrazo BD Production Handoff

> Repository authority:
> - `1569032023yf-star/workbuddy-task-window` (branch `main`) = **PRODUCTION SOURCE / PRODUCTION HANDOFF** ← this repo
> - `1569032023yf-star/roktandrazo-outreach-codex` = **DEVELOPMENT SOURCE / CODEX HANDOFF** (do NOT write production handoff here)
>
> Generated: 2026-09-14T14:37:00+08:00 (Asia/Shanghai)
> REFRESH TYPE: **READ-ONLY status refresh** — no code/DB/scheduler/FSP/Authorization/send changes. Live metrics authority = `data/bd_leads.db` (read-only query), WorkBuddy automations, Windows Task Scheduler.
> NOTE: the live production DB is `roktandrazo-outreach/data/bd_leads.db`; the root `roktandrazo-outreach/bd_leads.db` is a 0-byte stale file and is NOT authoritative.

---

## C. REQUIRED CURRENT STATUS FIELDS

```
CURRENT_PHASE              = PHASE_4A_1C (Controlled Production Patch + Inventory Validation) — COMPLETE; stable, no sends
PRODUCTION_STATUS          = PATCHED (2 files @ Codex 7013b33); FROZEN send chain intact; canonical scheduler ACTIVE;
                             NO sends since 2026-09-03 (fail-closed by design; SAFE_FSP materialized=0)
CURRENT_BLOCKER            = SAFE_FSP materialized pool = 0. Authoritative READ_ONLY_V2_SAFE_UNIQUE_ORGS = 1
                             (MX-enforced, unchanged from 2026-09-11), NOT materialized into Final Send Plan:
                             the single safe lead (id 1085, org=ithacainstantreplaysports.com) is
                             status=manual_review_needed + auto_sendable=0 + manual_sendable=0 (review gate fail-closed).
                             480 manual_review_needed leads + 428 no-email leads = dominant upstream blockers.
PRODUCTION_SCHEDULER_AUTHORITY = WorkBuddy Automation (workbuddy_automation) — SOLE scheduler authority.
                             BDExecutionHost Windows Service = Stopped. Windows PostSend = UNIQUE_REQUIRED (Ready).
                             No second/parallel scheduler. PostSend runs as UNIQUE_REQUIRED Windows task only.
WORKBUDDY_AUTOMATIONS      = see section below (5 canonical ACTIVE + Recovery Sync ACTIVE)
WINDOWS_TASKS              = see section below
DUPLICATE_ACTIVE_TRIGGER_COUNT = 0   (PreSend/Outreach Disabled; PostSend UNIQUE_REQUIRED, not duplicate)
PRODUCTION_CODE_SHA        = patched files @ Codex 7013b33 (UNCHANGED since 2026-09-11; drift=false):
                             bd_orchestrator.py = 252ed6042b04837f6d429936771fa261889b5f556aa80140162b098894da4d05
                             discovery/discovery_service.py = 45db60d94017c3cc7b68ffdaa6044bf6af5392f790568b8766fc4236bad0c356
DATABASE_SCHEMA_CHANGED    = false  (schema_version=162, 27 tables, integrity_check=ok; only routine job_runs + system_state
                                     rows added by scheduled runs since patch)
FROZEN_FILES_CHANGED       = false  (V2 / MX / Preflight / Sender / final_send_plan / campaign_eligible_v2 untouched)
SAFE_METRIC_DEFINITION     = see section D (5 distinct metrics, each with authority)
SAFE_CURRENT               = canonical SAFE_FSP (materialized final_send_plan.status='planned') = 0
                             (authoritative READ_ONLY_V2_SAFE_UNIQUE_ORGS = 1 — MX-enforced, unchanged)
LAST_INVENTORY_RUN         = 2026-09-13 15:01 +08 (automation-1784775229336; run_id inventory:2026-09-13:6031059e;
                             status=partial, stop_reason=safe_inventory_gap; actual=1, gap=59). Validation run
                             2026-09-11 14:25 +08 (f5895b2a) same stop_reason. Daily 15:00 automation ACTIVE.
LAST_PRESEND_RUN           = automation-1785804406748 ACTIVE (Mon-Fri 21:30 +08); last actual run NOT persisted in DB (no job_run rows)
LAST_PREFLIGHT_RUN         = automation-1785804413719 ACTIVE (Mon-Fri 21:50 +08); last actual run NOT persisted in DB
LAST_OUTREACH_RUN          = automation-1785804421539 ACTIVE (Mon-Fri 22:00 +08); last actual send = 2026-09-03 01:10 +08
LAST_POSTSEND_RUN          = 2026-09-14 00:10 +08 (Windows task RoktRazo-BD-PostSend, Ready; result=0, no sends)
NEXT_ACTION                = (1) Resolve SAFE=0/1: authorize OFFICIAL_EMAIL_ENRICHMENT for 428 no-email leads OR
                             relax review gate for V2-eligible manual_review_needed leads (user authorization required, NOT auto).
                             (2) Continue permanent handoff: every future production audit/result synced here.
                             (3) RECOMMENDED: purge already-tracked *.db files from repo history per safe-git rule E
                             (separate destructive authorization — history rewrite).
```

### WORKBUDDY_AUTOMATIONS (canonical, sole scheduler) — verified 2026-09-14 14:37 +08
| Automation ID | Name | Schedule | State |
|---|---|---|---|
| 1784775229336 | RoktRazo BD Inventory | daily 15:00 +08 | ACTIVE |
| 1785804406748 | BD Production Pre-Send | Mon–Fri 21:30 +08 | ACTIVE |
| 1785804413719 | BD Production Preflight | Mon–Fri 21:50 +08 | ACTIVE |
| 1785804421539 | BD Production Outreach | Mon–Fri 22:00 +08 | ACTIVE (display name still carries stale suffix `[PAUSED: ExecutionHost未验证]`; actual status = ACTIVE) |
| 1786002601925 | BD Result Recovery Sync | daily 08:45 +08 | ACTIVE (support job, not a stage trigger) |

### WINDOWS_TASKS — verified 2026-09-14 14:37 +08 (via Get-ScheduledTask)
| Task Name | State | Classification |
|---|---|---|
| RoktRazo-BD-PreSend | Disabled | DUPLICATE of canonical Pre-Send (suppressed) |
| RoktRazo-BD-Outreach | Disabled | DUPLICATE of canonical Outreach (suppressed) |
| RoktRazo-BD-PostSend | Ready / Enabled | UNIQUE_REQUIRED — runs `bd_orchestrator.py --stage post-send` 00:10 daily; no WorkBuddy equivalent exists |

---

## D. SAFE / POOL METRICS — EXPLICIT DEFINITIONS (no bare "SAFE = X")

> ⚠️ METRIC_DEFINITION_MISMATCH_FOUND = true (carried forward from 2026-09-11). Three distinct things were historically
> called "SAFE": read-only V2 eligibility ≠ materialized Final Send Plan ≠ BroadReady ≠ evidence count. All reported separately.
> **Refreshed 2026-09-14 (read-only):** the authoritative READ_ONLY_V2_SAFE_UNIQUE_ORGS remains **1** (MX-enforced), unchanged
> from 2026-09-11. The METRIC_DEFINITION_MISMATCH on VISIBLE_FIRST_PARTY_EMAILS was re-confirmed live (status-agnostic
> verified-email count = 332 vs strict "status NOT IN terminal" variant = 16; the 2026-09-11 handoff's reported 338
> equals the status-agnostic count, not the strict formula).

| Metric | Value (live 2026-09-14) | Authority |
|---|---|---|
| **V2_ELIGIBLE_UNSENT** | **16** leads (SQL proxy, MX **NOT** enforced) / **5** with evidence freshness ≤90d | `leads`: email NOT NULL + `email_verified_on_official_site=1` + non-terminal + `email_source_type` NOT IN ('guessed_email') [+ `evidence_checked_at` ≤90d → 5]. Canonical authority = `campaign_eligible_v2.review_campaign_eligible_v2()` which requires live MX=ok — **true canonical V2 ≤ 16**, and the live frozen-path measurement of the MX-enforced unique-org count = **1**. |
| **READ_ONLY_SAFE_UNIQUE_ORGS** | **1** org (AUTHORITATIVE, MX-enforced) | Recomputed 2026-09-14 read-only by replicating the Frozen V2 + MX path (`select_candidates_for_plan_v2` → `review_campaign_eligible_v2`) with the existing `system_config.mx_cache_*` injected (no live MX lookup, no DB write). Distinct `organization_key` among `CAMPAIGN_ELIGIBLE_V2` leads = 1. Unchanged from 2026-09-11. |
| **MATERIALIZED_FSP_PLANNED** | **0** (0 orgs) | `final_send_plan.status='planned'` (canonical production SAFE_FSP). The real "SAFE" the frozen send chain consumes. |
| **BROAD_READY** | **95** (DB column) / **34** (inventory effective, live-recomputed 2026-09-14) | `leads.send_eligibility='broad_outreach_ready'` = 95. Inventory-effective recomputed live via `broad_ready.is_broad_outreach_ready` = 34 (stricter; excludes leads failing additional gates). Both unchanged from 2026-09-11. |
| **VISIBLE_FIRST_PARTY_EMAILS** | **332** (canonical, status-agnostic) / **16** (strict "status NOT IN terminal" variant) | Canonical (matches 2026-09-11 reported 338) = `leads.email NOT NULL AND email_verified_on_official_site=1` = 332. The looser code defs D1≈914 / D2≈983 (incl `email_source_type='unknown'`/`'guessed_email'`) still exist — do not mix. |

### Supporting live facts (read-only, 2026-09-14)
- TOTAL_LEADS = 1069 · TOTAL_SENT (send_log) = 516 · FULL_EVIDENCE_RECORDS (evidence_url NOT NULL) = 844
- EMAIL_PRESENT = 587 · VERIFIED_EMAIL_PRESENT = 332 · VERIFIED_EVIDENCE_FRESH_90d = 61 · OFFICIAL_WEBSITE_PRESENT = 653
- LAST_SEND_LOG_TS = 2026-09-03T01:10:35+08:00 · LAST_FSP_CREATED_TS = 2026-09-02 14:32:08
- Manual review backlog: `status='manual_review_needed'` = 480 (dominant blocker to materialization)
- No-email actionable leads (empty email, non-terminal) = 428 (need OFFICIAL_EMAIL_ENRICHMENT)
- The 1 safe lead: id=1085, org=`org:domain:ithacainstantreplaysports.com`, status=`manual_review_needed`, blocked from FSP by `auto_sendable=0` + `manual_sendable=0` → SAFE_BLOCKED_FROM_FSP = 1.

### One-line rule
**read-only V2 eligibility (authoritative 1 org, MX-enforced) ≠ materialized Final Send Plan (0) ≠ BroadReady (95 col / 34 effective) ≠ visible first-party emails (332).**
Report all five. Never summarize production readiness with a single "SAFE = X".

---

## B. JOB RUNS SINCE 2026-09-11 14:28 +08 (read-only from job_runs; times stored UTC)

| date (+08) | run_id | stage | started_at (UTC) | finished_at (UTC) | status | actual | gap | stop_reason | error |
|---|---|---|---|---|---|---|---|---|---|
| 2026-09-11 15:01 | inventory:2026-09-11:e7e143b7 | inventory | 2026-09-11 07:01:11 | 2026-09-11 07:04:24 | partial | 1 | 29 | safe_inventory_gap | (empty) |
| 2026-09-11 00:10¹ | post-send:2026-09-11:a7e289e5 | post-send | 2026-09-11 16:10:02 | 2026-09-11 16:10:04 | completed | 0 | 40 | (none) | (empty) |
| 2026-09-12 15:03 | inventory:2026-09-12:0d0bb0d5 | inventory | 2026-09-12 07:03:28 | 2026-09-12 07:06:59 | partial | 1 | 59 | safe_inventory_gap | (empty) |
| 2026-09-12 00:10¹ | post-send:2026-09-12:1a6fe52d | post-send | 2026-09-12 16:10:02 | 2026-09-12 16:10:04 | completed | 0 | 40 | (none) | (empty) |
| 2026-09-13 15:01 | inventory:2026-09-13:6031059e | inventory | 2026-09-13 07:01:06 | 2026-09-13 07:05:10 | partial | 1 | 59 | safe_inventory_gap | (empty) |
| 2026-09-13 00:10¹ | post-send:2026-09-13:ad59b6a2 | post-send | 2026-09-13 16:10:02 | 2026-09-13 16:10:04 | completed | 0 | 40 | (none) | (empty) |

¹ post-send started_at is stored as previous-day UTC (00:10 +08 = previous day 16:10 UTC). PreSend / Preflight / Outreach / Recovery Sync stages have **NO job_runs rows** in this window — consistent with the 2026-09-11 note that they do not persist runs to `job_runs` (their last actual execution is not captured in the DB). Recovery Sync (automation-1786002601925, daily 08:45 +08) is confirmed active via scheduler but also does not write job_runs; its 2026-09-14 08:45 run accounts for the live DB file mtime of 2026-09-14 08:45.

---

## E. INVENTORY YIELD SINCE PATCH (2026-09-11 validation → 2026-09-14)

Per-Inventory runs (automated, since patch). Granular discovery metrics are **UNKNOWN** for the automated runs
because `job_runs` stores only target/actual/gap/stop_reason/error — not discovery sub-metrics.

| run_id | date (+08) | actual | gap | stop_reason | DISCOVERY_RESULTS_SEEN | NEW_UNIQUE_PLACES | WEBSITE_VERIFIED_DELTA | VISIBLE_EMAIL_DELTA | FULL_EVIDENCE_DELTA | V2_SAFE_ORG_DELTA |
|---|---|---|---|---|---|---|---|---|---|---|
| inventory:2026-09-11:f5895b2a (validation) | 2026-09-11 14:25 | 1 | 29 | safe_inventory_gap | 8 | 0 | 0 | n/a | n/a | 0 |
| inventory:2026-09-11:e7e143b7 | 2026-09-11 15:01 | 1 | 29 | safe_inventory_gap | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| inventory:2026-09-12:0d0bb0d5 | 2026-09-12 15:03 | 1 | 59 | safe_inventory_gap | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| inventory:2026-09-13:6031059e | 2026-09-13 15:01 | 1 | 59 | safe_inventory_gap | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

Cumulative funnel deltas since patch (live 2026-09-14 vs 2026-09-11 baseline):
- DISCOVERY_RESULTS_SEEN (since patch, automated) = UNKNOWN (only validation run's 8 is recorded)
- NEW_UNIQUE_PLACES = 0
- WEBSITE_VERIFIED_DELTA = 0 (no new unique places; validation run website_resolution_processed=0)
- VISIBLE_FIRST_PARTY_EMAIL_DELTA = 332 − 338 = **−6**
- FULL_EVIDENCE_DELTA = 844 − 897 = **−53** (⚠ unexpected given no Inventory writes occurred; likely a baseline-definition difference in the 2026-09-11 figure — recommend reconfirming the 897 baseline definition before treating as a regression)
- V2_SAFE_ORG_DELTA = 1 − 1 = **0**

**Conclusion:** Inventory yield since patch = effectively zero net progress. Every daily inventory stops immediately at
`safe_inventory_gap` (only 1 org meets the MX-enforced V2 bar, far below the 30+ target). No new unique places, no new
V2-safe orgs.

---

## F. EMAIL OUTCOME SINCE 2026-09-11 (read-only)

| Metric | Since 2026-09-11 | Notes |
|---|---|---|
| SMTP_ACCEPTED | 0 | `send_log` has 0 rows with `sent_at >= 2026-09-11`. No sends. |
| HARD_BOUNCES | 0 | `bounce_log` has 0 rows since 2026-09-11. |
| POLICY_BOUNCES | 0 | none. |
| REPLIES | 0 | `reply_log` has 0 rows since 2026-09-11. |
| UNSUBSCRIBES | 0 | 0 leads with `unsubscribed_at >= 2026-09-11`. |
| LAST_ACTUAL_SEND_AT | 2026-09-03T01:10:35+08:00 | No send has occurred since; SMTP accepted ≠ inbox delivery (no accepts logged). |

---

## G. SCHEDULER (verified 2026-09-14)

- **WorkBuddy automations (sole scheduler):** Inventory / Pre-Send / Preflight / Outreach all ACTIVE (Mon–Fri windows); Recovery Sync ACTIVE (daily 08:45). Outreach automation display name still carries a stale `[PAUSED: ExecutionHost未验证]` suffix but actual status = ACTIVE.
- **Windows tasks:** PreSend = Disabled, Outreach = Disabled (both suppressed duplicates); PostSend = Ready/Enabled (UNIQUE_REQUIRED).
- **DUPLICATE_ACTIVE_TRIGGER_COUNT = 0** (no second/parallel scheduler; only PostSend is a live non-duplicate trigger).
- **MANUAL_NIGHTLY_CONFIRMATION_REQUIRED = false** (unchanged).

---

## H. NEXT ACTION (carried forward)

1. Resolve SAFE=0/1: authorize **OFFICIAL_EMAIL_ENRICHMENT** for the 428 no-email leads OR relax the review gate for
   V2-eligible `manual_review_needed` leads (user authorization required, NOT automatic).
2. Continue permanent handoff: sync every future production audit/result to `workbuddy-task-window` main.
3. RECOMMENDED: purge already-tracked `*.db` files from repo history per safe-git rule E (separate destructive authorization — history rewrite).
