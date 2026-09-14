# CURRENT_STATUS — roktandrazo BD Production Handoff

> Repository authority:
> - `1569032023yf-star/workbuddy-task-window` (branch `main`) = **PRODUCTION SOURCE / PRODUCTION HANDOFF** ← this repo
> - `1569032023yf-star/roktandrazo-outreach-codex` = **DEVELOPMENT SOURCE / CODEX HANDOFF** (do NOT write production handoff here)
>
> Generated: 2026-09-14T15:46:00+08:00 (Asia/Shanghai)
> REFRESH TYPE: **READ-ONLY status refresh + Inventory closeout + Lead 1085 state-transition audit** — no code/DB/scheduler/FSP/Authorization/send changes. Live metrics authority = `data/bd_leads.db` (read-only query), WorkBuddy automations, Windows Task Scheduler.
> TIMESTAMP NOTE: previous handoff stamped `Generated: 2026-09-14T14:37:00+08:00` while also recording the 2026-09-14 inventory start as `15:01 +08` and calling it "still running as of 14:37". 14:37 < 15:01 is impossible → the 14:37 timestamp was wrong (see section I / FINAL HANDOFF_TIMESTAMP_ERROR). Correct inventory start = 15:01:10 +08 (= 07:01:10 UTC); correct audit time = 15:46 +08 (this refresh).
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
LAST_INVENTORY_RUN         = 2026-09-14 15:01 +08 (automation-1784775229336; run_id inventory:2026-09-14:eba7c883;
                             status=partial, stop_reason=safe_inventory_gap; started 15:01:10 +08 / 07:01:10 UTC,
                             finished 15:04:36 +08 / 07:04:36 UTC; actual=1, gap=29) — NOW COMPLETED (was "running"
                             in prior handoff; prior timestamp 14:37 +08 predated the 15:01 start, see FINAL HANDOFF_TIMESTAMP_ERROR).
                             Prior completed: 2026-09-13 15:01 +08 (6031059e; partial, actual=1, gap=59). Validation run
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

### WORKBUDDY_AUTOMATIONS (canonical, sole scheduler) — verified 2026-09-14 15:46 +08
| Automation ID | Name | Schedule | State |
|---|---|---|---|
| 1784775229336 | RoktRazo BD Inventory | daily 15:00 +08 | ACTIVE |
| 1785804406748 | BD Production Pre-Send | Mon–Fri 21:30 +08 | ACTIVE |
| 1785804413719 | BD Production Preflight | Mon–Fri 21:50 +08 | ACTIVE |
| 1785804421539 | BD Production Outreach | Mon–Fri 22:00 +08 | ACTIVE (display name still carries stale suffix `[PAUSED: ExecutionHost未验证]`; actual status = ACTIVE) |
| 1786002601925 | BD Result Recovery Sync | daily 08:45 +08 | ACTIVE (support job, not a stage trigger) |

### WINDOWS_TASKS — verified 2026-09-14 15:46 +08 (via Get-ScheduledTask)
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
| **V2_ELIGIBLE_UNSENT** | **1** lead / **1** org — AUTHORITATIVE (Frozen V2 + MX, `CAMPAIGN_ELIGIBLE_V2` pool, recomputed 2026-09-14 read-only) | Replicated `review_campaign_eligible_v2` over 96 non-terminal email-present candidates with `system_config.mx_cache_*` injected as `mx_lookup` (no live MX, no DB write). Only **1** lead (id 1085, org `ithacainstantreplaysports.com`) lands in `CAMPAIGN_ELIGIBLE_V2`. Context (do NOT conflate): V1-eligible `review_campaign_eligible` (no MX) = **27** leads / 27 orgs; `VISIBLE_FIRST_PARTY_EMAILS` strict (verified+email+not-terminal) = **16**. The earlier "16" figure was the VISIBLE-strict count, not true V2+MX. |
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
| 2026-09-14 15:01 | inventory:2026-09-14:eba7c883 | inventory | 2026-09-14 07:01:10 | 2026-09-14 07:04:36 | partial | 1 | 29 | safe_inventory_gap | (empty) |

¹ post-send started_at is stored as previous-day UTC (00:10 +08 = previous day 16:10 UTC). PreSend / Preflight / Outreach / Recovery Sync stages have **NO job_runs rows** in this window — consistent with the 2026-09-11 note that they do not persist runs to `job_runs` (their last actual execution is not captured in the DB). Recovery Sync (automation-1786002601925, daily 08:45 +08) is confirmed active via scheduler but also does not write job_runs; its 2026-09-14 08:45 run accounts for the live DB file mtime of 2026-09-14 08:45.

**Note (re-verified 2026-09-14 15:46 +08):** the 5th inventory run (`inventory:2026-09-14:eba7c883`) has **COMPLETED** (finished 2026-09-14 07:04:36 UTC = 15:04:36 +08; status=partial, actual=1, gap=29, stop_reason=safe_inventory_gap). `LAST_SUCCESSFUL_INVENTORY` (last *completed*) = **2026-09-14 15:01 +08** (eba7c883), which is now also the latest inventory. No new V2-safe orgs materialized; READ_ONLY_V2_SAFE_UNIQUE_ORGS unchanged at 1 (lead 1085; see section I for why it still cannot enter FSP).

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

---

## I. INVENTORY CLOSEOUT + LEAD 1085 STATE TRANSITION AUDIT (2026-09-14 15:46 +08, READ-ONLY)

> Audit mandate: read-only. No code/DB/scheduler/FSP/Authorization/send changes. Only handoff docs updated.

### A. Inventory closeout — `inventory:2026-09-14:eba7c883` (NOW COMPLETED)
| Field | Value |
|---|---|
| RUN_ID | inventory:2026-09-14:eba7c883 |
| STARTED_AT | 2026-09-14 07:01:10 UTC (= 15:01:10 +08) |
| FINISHED_AT | 2026-09-14 07:04:36 UTC (= 15:04:36 +08) |
| STATUS | partial |
| ACTUAL | 1 |
| GAP | 29 |
| STOP_REASON | safe_inventory_gap |
| ERROR | (empty) |
| READ_ONLY_V2_SAFE_BEFORE | 1 (prior completed run 6031059e, 2026-09-13) |
| READ_ONLY_V2_SAFE_AFTER | 1 (unchanged; lead 1085 still the only V2-safe org) |

Granular per-run metrics (DISCOVERY_RESULTS_SEEN / NEW_UNIQUE_PLACES / WEBSITE_RESOLUTION_PROCESSED / STAGING_POSTPROCESS_PROCESSED / LINKED_BACKLOG_PROCESSED) = **UNKNOWN** — `job_runs` persists only target/actual/gap/stop_reason/error, not discovery sub-metrics (consistent with prior audit; do not speculate).

### B. Lead 1085 audit
| Field | Value |
|---|---|
| LEAD_ID | 1085 |
| email | ithacainstantreplaysports@yahoo.com |
| email_source_type | official_page_visible |
| email_verified_on_official_site | 1 |
| evidence_url | https://ithacainstantreplaysports.com/ |
| evidence_method | official_homepage |
| evidence_checked_at | 2026-09-10T02:17:28.952484+00:00 (fresh, <90d) |
| official_email_evidence | evidence_snippet (homepage shows `ithacainstantreplaysports@yahoo.com … IthacaInstantReplaySports@yahoo.com …`) |
| organization_key | org:domain:ithacainstantreplaysports.com |
| timezone | America/New_York (timezone_status=RESOLVED) |
| MX_RESULT | ok (yahoo.com valid MX) |
| V1_RESULT | CAMPAIGN_ELIGIBLE (v1_pool) |
| V2_RESULT | CAMPAIGN_ELIGIBLE_V2 (eligible=True; tier=E1; mx_status=ok; evidence_stale=False; blockers=[]) |
| linked discovery result id | 293 |
| linked discovery validation_status | existing_lead_linked |
| review_reason_code | hygiene_failed |
| review_reason_detail | state_out_of_scope,third_party_email_domain |
| status / auto_sendable / manual_sendable | manual_review_needed / 0 / 0 |

### C. State path trace (function-level, read-only)
1. **Discovery evidence found** — `lead_discovery_results.id=293` (provider=browser_maps, evidence_method=official_homepage, evidence_url=official site, snippet contains the yahoo email). `validation_status=existing_lead_linked` → `linked_lead_id=1085`.
2. **Existing lead linkage** — linked to lead 1085 (lead.notes: `discovery_result_id=293`).
3. **Evidence merge** — lead 1085 set: email=…@yahoo.com, email_source_type=official_page_visible, email_verified_on_official_site=1, evidence_url, evidence_method, evidence_snippet, evidence_checked_at=2026-09-10.
4. **Hygiene result** — `lead_hygiene_gate.evaluate_a0(1085)` (pure, side-effect-free):
   - `state='NY'` → `normalize_state('NY')='NY' ∉ {TN,AR,KY}` → reason **`state_out_of_scope`** (line 74-75)
   - `domain='yahoo.com'`, `official_domain='ithacainstantreplaysports.com'` → `domain != official_domain` → reason **`third_party_email_domain`** (line 90-92)
   - returns `HygieneDecision("B2_manual_review", False, (…,'state_out_of_scope','third_party_email_domain',…))`
5. **Lead status** — consuming code maps `B2_manual_review` → `status='manual_review_needed'`, `auto_sendable=0`, `manual_sendable=0`, `review_reason_code='hygiene_failed'`, `review_reason_detail='state_out_of_scope,third_party_email_domain'`.
6. **auto_sendable/manual_sendable** = 0/0 (set by the hygiene consumer, not by V2).
7. **select_candidates_for_plan_v2(1085)** — `status='manual_review_needed'` is **NOT** in the terminal exclusion list (`sent,bounced,do_not_contact,rejected,failed,delivery_issue,bounce_review,contact_form_pool`), so it passes the status filter. Then `review_campaign_eligible_v2(1085)`:
   - `email_source_tier`: `email_source_type='official_page_visible'` AND `verified=1` → returns **TIER_E1 immediately (line 188-189)**, does NOT check domain match.
   - MX ok + evidence fresh → `eligible=True`, `pool=CAMPAIGN_ELIGIBLE_V2`, `blockers=[]`.
   → **V2_SELECTOR_INCLUDES_1085 = True**.
8. **create_plan eligibility** — `campaign_eligible_check_v2` (same `review_campaign_eligible_v2`) also returns True.
9. **EXACT_FSP_BLOCKER (final gate)** — `outreach_control.build_final_plan_entries` required-field check:
   `required = ("id","email","store_name","email_subject","email_body","evidence_url")`; lead 1085 has `email_subject=None` and `email_body=None` → `continue` → **NOT inserted** into `final_send_plan`. So 1085 never reaches a planned FSP row.

### D. Do NOT fix (read-only) — minimum fix location
- **MINIMUM_FIX_FILE** = `campaign_eligible_v2.py` (**NON-frozen**; the only Phase 4A.1C locked files are `bd_orchestrator.py` + `discovery/discovery_service.py`, untouched).
- **MINIMUM_FIX_FUNCTION** = `select_candidates_for_plan_v2` (or `review_campaign_eligible_v2`): add the hygiene gate's domain-match rule so a lead flagged `third_party_email_domain` / `status='manual_review_needed'` is **NOT** counted as `CAMPAIGN_ELIGIBLE_V2`. This reconciles the V2 safe pool with the hygiene hold. **No gate is relaxed** (per "目标不是放宽门禁").
- **EXPECTED_STATE_TRANSITION** = 1085 REMAINS `manual_review_needed` (gate not relaxed); V2 selector no longer returns it; `READ_ONLY_V2_SAFE_UNIQUE_ORGS` → 0; FSP build becomes internally consistent.
- Note: the missing `email_subject`/`email_body` is a **secondary drafting gap** (drafter.py never produced content for `manual_review_needed` leads). It only matters once a lead is approved; it is NOT the root inconsistency.
- No Frozen file needs modification → no STOP required. Per read-only mandate, **NOT applied here**.

### E. Timestamp consistency (handoff correction only)
- **HANDOFF_TIMESTAMP_ERROR = TRUE.** Prior handoff stamped `Generated: 2026-09-14T14:37:00+08:00` yet recorded the 2026-09-14 inventory start as `15:01 +08` and labeled it "still running as of 14:37". 14:37 < 15:01 is impossible. The inventory start (07:01:10 UTC = 15:01:10 +08) is correct; the **14:37 +08 handoff timestamp was the erroneous one** (predated the run).
- **CORRECT_INVENTORY_START_LOCAL** = 2026-09-14 15:01:10 +08 (= 07:01:10 UTC). Finished 15:04:36 +08.
- **CORRECT_AUDIT_TIME_LOCAL** = 2026-09-14 15:46 +08 (this refresh). Prior handoff's true as-of should have been ≥ 15:04:36 +08.
- Business code NOT changed; only handoff doc time口径 corrected.

### I. FINAL (audit answers)
```
INVENTORY_RUN_FINAL_STATUS      = completed (partial; actual=1, gap=29, safe_inventory_gap)
READ_ONLY_V2_SAFE_AFTER        = 1 (lead 1085; unchanged) — but NOT materializable (see blocker)
LEAD_1085_V2_PASS              = True (CAMPAIGN_ELIGIBLE_V2)
V2_SELECTOR_INCLUDES_1085      = True
EXACT_FSP_BLOCKER              = build_final_plan_entries required-field check: email_subject/email_body = NULL → skipped
STATE_TRANSITION_CLASSIFICATION = C (inconsistent duplicate gate): hygiene requires email-domain==official-domain;
                                  V2 email_source_tier treats official_page_visible+verified as E1 regardless of domain
                                  (B-nuance: no re-evaluation transitions 1085 out of manual_review_needed despite V2 pass)
STATE_TRANSITION_BUG           = True (V2 "safe=1" is misleading; sole safe lead is held by hygiene AND lacks draft content → effective sendable FSP pool = 0)
MINIMUM_FIX_FILE               = campaign_eligible_v2.py
MINIMUM_FIX_FUNCTION           = select_candidates_for_plan_v2 / review_campaign_eligible_v2 (add domain-match / manual_review_needed exclusion)
HANDOFF_TIMESTAMP_ERROR        = True (14:37 +08 stamp invalid vs 15:01 +08 inventory start)
NEXT_RECOMMENDED_ACTION       = (read-only, no change made) reconcile deliberately: (a) KEEP 1085 held + exclude
                                  manual_review_needed from V2 selector [recommended, no gate relaxed], OR
                                  (b) if third-party free-mailboxes w/ official-page evidence are acceptable, relax
                                  lead_hygiene_gate.evaluate_a0 third_party rule — but that IS a gate relaxation,
                                  contrary to stated goal, so requires explicit user authorization.
GITHUB_HANDOFF_PUSHED          = true (commit 5060ddb @ main; verified via ls-remote)
```
