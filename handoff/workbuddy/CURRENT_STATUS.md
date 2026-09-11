# CURRENT_STATUS — roktandrazo BD Production Handoff

> Repository authority:
> - `1569032023yf-star/workbuddy-task-window` (branch `main`) = **PRODUCTION SOURCE / PRODUCTION HANDOFF** ← this repo
> - `1569032023yf-star/roktandrazo-outreach-codex` = **DEVELOPMENT SOURCE / CODEX HANDOFF** (do NOT write production handoff here)
>
> Generated: 2026-09-11T14:35:00+08:00 (Asia/Shanghai)
> Source of truth for live metrics: `bd_leads.db` (read-only query), automations, Windows Task Scheduler.

---

## C. REQUIRED CURRENT STATUS FIELDS

```
CURRENT_PHASE              = PHASE_4A_1C (Controlled Production Patch + Inventory Validation) — COMPLETE
PRODUCTION_STATUS          = PATCHED (2 files deployed from Codex 7013b33); FROZEN send chain intact;
                             canonical scheduler ACTIVE; no sends (SAFE_FSP materialized=0, by-design fail-closed)
CURRENT_BLOCKER            = SAFE_FSP materialized pool = 0. Authoritative READ_ONLY_V2_SAFE_UNIQUE_ORGS = 1
                             (MX-enforced, from live inventory 2026-09-11 14:28); NOT materialized into
                             Final Send Plan (review gate fail-closed). 428 no-email leads need
                             OFFICIAL_EMAIL_ENRICHMENT (separate authorization, not auto).
PRODUCTION_SCHEDULER_AUTHORITY = WorkBuddy Automation (workbuddy_automation) — SOLE scheduler authority.
                             BDExecutionHost Windows Service = Stopped (not scheduler).
                             No second/parallel scheduler. PostSend runs as UNIQUE_REQUIRED Windows task.
WORKBUDDY_AUTOMATIONS      = see section below (4 canonical ACTIVE + Recovery Sync ACTIVE)
WINDOWS_TASKS              = see section below
DUPLICATE_ACTIVE_TRIGGER_COUNT = 0   (PreSend/Outreach Disabled; PostSend is UNIQUE_REQUIRED, not duplicate)
PRODUCTION_CODE_SHA        = patched files @ Codex 7013b33:
                             bd_orchestrator.py = 252ed6042b04837f6d429936771fa261889b5f556aa80140162b098894da4d05
                             discovery/discovery_service.py = 45db60d94017c3cc7b68ffdaa6044bf6af5392f790568b8766fc4236bad0c356
                             (ad1111b = handoff/report-only commit on top of 7013b33; NOT a separate production version)
DATABASE_SCHEMA_CHANGED    = false  (no migrations; only job_runs + system_state rows added by the live inventory;
                                     schema_version=162, 27 tables intact, integrity_check=ok)
FROZEN_FILES_CHANGED       = false  (V2 / MX / Preflight / Sender / final_send_plan / campaign_eligible_v2 untouched)
SAFE_METRIC_DEFINITION     = see section D (5 distinct metrics, each with authority)
SAFE_CURRENT               = canonical SAFE_FSP (materialized final_send_plan.status='planned') = 0
                             (authoritative READ_ONLY_V2_SAFE_UNIQUE_ORGS = 1 — MX-enforced, corrected from earlier MX-less proxy of 11)
LAST_INVENTORY_RUN         = 2026-09-11 14:25:15–14:28:39 (one-off authorized live run; run_id inventory:2026-09-11:f5895b2a;
                             status=partial, stop_reason=safe_inventory_gap). Daily 15:00 automation ACTIVE.
LAST_PRESEND_RUN           = Scheduled Mon-Fri 21:30 (automation-1785804406748, ACTIVE). Last actual run not persisted in DB.
LAST_PREFLIGHT_RUN         = Scheduled Mon-Fri 21:50 (automation-1785804413719, ACTIVE). Last actual run not persisted in DB.
LAST_OUTREACH_RUN          = Scheduled Mon-Fri 22:00 (automation-1785804421539, ACTIVE). Last actual send = 2026-09-03 01:10 (+08:00).
LAST_POSTSEND_RUN          = 2026-09-10 00:10:01 (Windows task RoktRazo-BD-PostSend, result 0).
NEXT_ACTION                = (1) Resolve SAFE=0/1: authorize OFFICIAL_EMAIL_ENRICHMENT for 428 no-email leads OR
                             relax review gate for V2-eligible manual_review_needed leads (user authorization required, not auto).
                             (2) Continue permanent handoff: every future production audit/result synced here.
                             (3) RECOMMENDED: purge already-tracked *.db files from repo history per safe-git rule E
                             (separate destructive authorization — history rewrite).
```

### WORKBUDDY_AUTOMATIONS (canonical, sole scheduler)
| Automation ID | Name | Schedule | State |
|---|---|---|---|
| 1784775229336 | BD Inventory | daily 15:00 | ACTIVE |
| 1785804406748 | BD Production Pre-Send | Mon–Fri 21:30 | ACTIVE |
| 1785804413719 | BD Production Preflight | Mon–Fri 21:50 | ACTIVE |
| 1785804421539 | BD Production Outreach | Mon–Fri 22:00 | ACTIVE |
| 1786002601925 | Result Recovery Sync | daily 08:45 | ACTIVE (support job, not a stage trigger) |

> Pre-deployment (hold) states were ACTIVE for all 4 canonical; they were PAUSED for the patch window and
> restored to ACTIVE after validation passed. No schedule changed. PostSend has no WorkBuddy equivalent (Windows task).

### WINDOWS_TASKS
| Task Name | State | Classification |
|---|---|---|
| RoktRazo-BD-PreSend | Disabled | DUPLICATE of canonical Pre-Send (suppressed) |
| RoktRazo-BD-Outreach | Disabled | DUPLICATE of canonical Outreach (suppressed) |
| RoktRazo-BD-PostSend | Ready / Enabled | UNIQUE_REQUIRED — runs `bd_orchestrator.py --stage post-send` 00:10 daily; no WorkBuddy equivalent exists |

---

## E. PHASE 4A.1C PATCH SUMMARY

- **CODEX_SOURCE_COMMIT** = `7013b335ad4b1eec33cd559825ece7d5aaead70c` (approved production code)
- **ad1111b60e2dab7231ce8326547332defddea78d** = handoff/report-only, NOT a separate production version (do not double-count)
- **Scope** = exactly two production files deployed:
  1. `bd_orchestrator.py` → target SHA256 `252ed604…` ✓ MATCH
  2. `discovery/discovery_service.py` → target SHA256 `45db60d9…` ✓ MATCH
- **TARGET_HASH_MATCH** = 2/2
- **Rollback bundle** = `C:/Users/15690/rollback_p4a1c_20260911_142132` (current files + SQLite online DB backup, integrity_check=ok)
- **Baseline drift** = false (current production = known pre-patch baseline, fully backed up; only the expected forward-patch delta)
- **Frozen files unchanged** = bd_sender / daily_session / preflight_gate / campaign_eligible_v2 / final_send_plan
- **DB schema changed** = false (WAL checkpoint only; schema_version=162, 27 tables, integrity_check=ok)
- **Live inventory (one, authorized)** = NEW_DISCOVERY_PATH_EXECUTED=true, LINKED_BACKLOG_PATH_EXECUTED=true,
  legacy scanner NOT used as SAFE authority; status=partial / stop_reason=safe_inventory_gap (did NOT claim target_met
  despite BroadReady≥30 → false-completion bug fixed).

---

## D. SAFE / POOL METRICS — EXPLICIT DEFINITIONS (no bare "SAFE = X")

> ⚠️ METRIC_DEFINITION_MISMATCH_FOUND = true (carried forward). Three distinct things were historically called "SAFE":
> read-only V2 eligibility ≠ materialized Final Send Plan ≠ BroadReady ≠ evidence count. All reported separately.
> **Correction this session:** the live inventory (which enforces MX) measured authoritative
> READ_ONLY_V2_SAFE_UNIQUE_ORGS = **1**, not the earlier MX-less SQL proxy of 11. The 11 was an over-count.

| Metric | Value (live 2026-09-11, post-patch) | Authority |
|---|---|---|
| **V2_ELIGIBLE_UNSENT** | **12** leads (SQL proxy, MX **NOT** enforced) | `leads`: email NOT NULL + `email_verified_on_official_site=1` + non-terminal + `email_source_type` NOT IN ('guessed') + `evidence_checked_at` ≤90d. Canonical authority = `campaign_eligible_v2.review_campaign_eligible_v2()` which requires live MX=ok — **true canonical V2 ≤ 12**, and the live inventory measured the MX-enforced unique-org count = 1. |
| **READ_ONLY_SAFE_UNIQUE_ORGS** | **1** org (AUTHORITATIVE, MX-enforced, from live inventory 2026-09-11 14:28) | distinct `leads.organization_key` among V2+MX-eligible. ⚠️ Earlier MX-less proxy reported 11 — that was an over-count; 1 is the corrected canonical value. |
| **MATERIALIZED_FSP_PLANNED** | **0** (0 orgs) | `final_send_plan.status='planned'` (canonical production SAFE_FSP). The real "SAFE" the frozen send chain consumes. |
| **BROAD_READY** | **95** (DB column) / **34** (inventory effective) | `leads.send_eligibility='broad_outreach_ready'` = 95. The inventory's internal effective BROAD_READY = 34 (stricter; excludes leads failing additional gates). Definition mismatch — report both. |
| **VISIBLE_FIRST_PARTY_EMAILS** | **338** (canonical) | Canonical = `leads.email NOT NULL AND email_verified_on_official_site=1 AND status NOT IN terminal`. ⚠️ Code contains looser defs D1≈914 / D2≈983 (incl `email_source_type='unknown'`/`'guessed_email'`) — do not mix with canonical 338. |

### Supporting live facts (read-only, post-patch)
- TOTAL_LEADS = 1069 · TOTAL_SENT = 516 · FULL_EVIDENCE_RECORDS (evidence_url NOT NULL) = 897
- LAST_SEND_LOG_TS = 2026-09-03T01:10:35+08:00 · LAST_FSP_CREATED_TS = 2026-09-02 14:32:08
- Manual review backlog: `status='manual_review_needed'` = 480 (dominant blocker to materialization)
- Inventory job_runs (2026-09-11): status=`partial`, actual=1, gap=29, stop_reason=`safe_inventory_gap`, error=empty

### One-line rule
**read-only V2 eligibility (authoritative 1 org, MX-enforced) ≠ materialized Final Send Plan (0) ≠ BroadReady (95 col / 34 effective) ≠ visible first-party emails (338).**
Report all five. Never summarize production readiness with a single "SAFE = X".
