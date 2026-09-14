# CHANGELOG — roktandrazo BD Production Handoff

All entries are production-handoff events. Live metrics authority = `bd_leads.db` (read-only).
Repository authority: `workbuddy-task-window` = PRODUCTION; `roktandrazo-outreach-codex` = DEVELOPMENT (never written here).

---

## 2026-09-14 — READ-ONLY PRODUCTION STATUS REFRESH (authorized, no changes)

- **Type:** READ-ONLY refresh of production status since the 2026-09-11 Phase 4A.1C patch. No code, DB, scheduler, FSP, Authorization, or send changes. Live metrics recomputed from `data/bd_leads.db` (read-only) + scheduler state.
- **PRODUCTION_CODE_DRIFT = false** — both patched files re-verified: `bd_orchestrator.py` = `252ed604…`, `discovery/discovery_service.py` = `45db60d9…` (match 2/2, unchanged from 2026-09-11).
- **Live funnel (read-only, per authority):**
  - TOTAL_LEADS = 1069
  - VISIBLE_FIRST_PARTY_EMAILS = 332 (canonical status-agnostic; strict "status NOT IN terminal" variant = 16). 2026-09-11 baseline 338 → −6.
  - BROAD_READY_DB = 95 (col) / BROAD_READY_EFFECTIVE = 34 (live-recomputed, unchanged).
  - V2_ELIGIBLE_UNSENT = 16 (SQL proxy, MX NOT enforced) / 5 with evidence ≤90d.
  - **READ_ONLY_V2_SAFE_UNIQUE_ORGS = 1** (Frozen V2+MX path replicated read-only via injected `system_config.mx_cache_*`, no live MX lookup, no DB write) — **unchanged from 2026-09-11**.
  - MATERIALIZED_FSP_PLANNED = 0.
  - MANUAL_REVIEW_NEEDED = 480 · EMPTY_EMAIL_ACTIONABLE = 428.
- **SAFE_BLOCKED_FROM_FSP = 1** — the single safe lead (id 1085, `org:domain:ithacainstantreplaysports.com`) is `status=manual_review_needed` + `auto_sendable=0` + `manual_sendable=0` → review gate fail-closed (matches 2026-09-11 blocker).
- **Job runs since 2026-09-11 (from job_runs):** 4 Inventory (all `partial`/`safe_inventory_gap`, actual=1) + 3 Post-Send (all `completed`, actual=0). PreSend/Preflight/Outreach/Recovery Sync have **no job_runs rows** (do not persist). Last inventory = 2026-09-13 15:01 +08.
- **Inventory yield since patch = zero net progress:** every daily inventory stops at `safe_inventory_gap` (only 1 MX-enforced V2-safe org vs 30+ target). 0 new unique places; V2_SAFE_ORG_DELTA=0. Granular discovery metrics UNKNOWN for automated runs (job_runs lacks them); validation run had discovery_results_seen=8, new_unique_places=0.
- **Email outcome since 2026-09-11:** SMTP_ACCEPTED=0, HARD_BOUNCES=0, POLICY_BOUNCES=0, REPLIES=0, UNSUBSCRIBES=0. LAST_ACTUAL_SEND_AT = 2026-09-03T01:10:35+08:00.
- **Scheduler verified:** 5 canonical WorkBuddy automations ACTIVE (Inventory/Pre-Send/Preflight/Outreach/Recovery Sync). Windows tasks: PreSend=Disabled, Outreach=Disabled, PostSend=Ready/Enabled (UNIQUE_REQUIRED). **DUPLICATE_ACTIVE_TRIGGER_COUNT = 0**. MANUAL_NIGHTLY_CONFIRMATION_REQUIRED = false.
- **Candidate blockers (V2-evaluated pool):** EVIDENCE_STALE=9, guessed_email=73, MX_NXDOMAIN=51, MX_NO_ROUTE=6, MX_NULL_MX=1, MX_DNS_ERROR=1, TIMEZONE_UNRESOLVED=75, ORG_DUPLICATE(non-terminal)=6, MANUAL_REVIEW_GATE(status)=480. History: PREVIOUSLY_SENT=415, SUPPRESSED=63, BOUNCED=49.
- **Flag:** FULL_EVIDENCE_DELTA = 844 − 897 = −53 (unexpected given no Inventory writes; likely a 2026-09-11 baseline-definition difference — recommend reconfirming the 897 figure before treating as regression).
- Updated handoff: CURRENT_STATUS.md, LATEST_RESULT.json (this entry), CHANGELOG.md. Safe-git precheck: only handoff docs staged; no .env/secrets/*.db/PII. Committed + pushed to `main` (handoff/report-only, NOT a production version bump).

## 2026-09-11 — PHASE 4A.1C Controlled Production Patch + Inventory Validation (authorized)
- **Deployed exactly two production files from Codex `7013b335ad4b1eec33cd559825ece7d5aaead70c`** (verified SHA256 MATCH 2/2):
  - `bd_orchestrator.py` → `252ed604…`
  - `discovery/discovery_service.py` → `45db60d9…`
  - `ad1111b` noted as handoff/report-only (not a separate production version).
- Pre-deployment: paused 4 canonical automations (Inventory/Pre-Send/Preflight/Outreach); captured PRE-DEPLOYMENT=ACTIVE; Windows PreSend/Outreach Disabled, PostSend UNIQUE_REQUIRED. DUPLICATE_ACTIVE_TRIGGER_COUNT=0.
- Verified no active job; created rollback bundle `C:/Users/15690/rollback_p4a1c_20260911_142132` (current files + SQLite online DB backup, integrity_check=ok); ROLLBACK_READY=true.
- Frozen files (bd_sender/daily_session/preflight_gate/campaign_eligible_v2/final_send_plan) unchanged; DB schema unchanged (WAL checkpoint only); .env unchanged.
- Production UTF-8 precheck: SYS_UTF8_MODE=1, STDOUT_ENCODING=utf-8 (managed Python 3.13.12) — no GBK/encoding risk.
- Ran ONE authorized live Inventory (`--stage inventory --live`, exit 0, 204s): NEW_DISCOVERY_PATH_EXECUTED=true, LINKED_BACKLOG_PATH_EXECUTED=true, legacy scanner NOT used as SAFE authority.
  - status=partial, stop_reason=safe_inventory_gap; READ_ONLY_V2_SAFE=1/30 (authoritative, MX-enforced) — did NOT claim target_met despite BroadReady≥30 → **false-completion bug fixed**.
  - Safety: REAL_SMTP=0, REAL_IMAP=0, FINAL_SEND_PLAN_CREATED=0, AUTHORIZATION_CREATED=0, GUESSED_EMAIL_PROMOTED=0.
- Restored 4 automations to ACTIVE (PRE-DEPLOYMENT state); Recovery Sync ACTIVE. No schedule changes.
- **Corrected metric:** authoritative READ_ONLY_SAFE_UNIQUE_ORGS = 1 (MX-enforced), not the earlier MX-less proxy of 11.
- Updated handoff: CURRENT_STATUS.md, LATEST_RESULT.json, phases/PHASE4A1C_PRODUCTION_PATCH.md.

## 2026-09-11 — PERMANENT GITHUB HANDOFF MODE established
- Created `handoff/workbuddy/` structure:
  - `CURRENT_STATUS.md` (all C-section fields + D-section 5-metric definitions with authority)
  - `LATEST_RESULT.json` (no credentials/PII; safe summary)
  - `CHANGELOG.md` (this file)
  - `phases/PHASE4A_METRIC_PROVENANCE_AUDIT.md`
  - `phases/PHASE4A1_PRODUCTION_VALIDATION.md`
  - `phases/SCHEDULER_AUTHORITY_AUDIT.md`
- Repo authority documented: production source/handoff = `workbuddy-task-window` (main); dev/Codex = `roktandrazo-outreach-codex` (do not write).
- **No production code changed this session** (PRODUCTION_CODE_SHA unchanged = `da36acfdbd19c896f3fdc0dc1bc1e16ac2b42eb4`).
- **No database schema or frozen files changed.**
- Live metrics captured (read-only): V2_ELIGIBLE_UNSENT=12 / READ_ONLY_SAFE_UNIQUE_ORGS=11 / MATERIALIZED_FSP_PLANNED=0 / BROAD_READY=95 / VISIBLE_FIRST_PARTY_EMAILS=338 (canonical).
- Flagged: repo currently tracks `*.db` files from prior history (violates safe-git rule E); recommend purge via separate authorization.

## 2026-09-10 — Phase 4A Production Scheduler Resume (authorized)
- Restored 4 canonical WorkBuddy automations PAUSED→ACTIVE (Inventory/Pre-Send/Preflight/Outreach); no schedule change.
- Immediate one-off Inventory run (11:27): BroadReady=34/30 short-circuit → email-recovery lane skipped → all SAFE metrics delta=0. REAL_SMTP=0.
- Read-only Metric Provenance Audit: METRIC_DEFINITION_MISMATCH_FOUND=true (4 conflicting VISIBLE_FIRST_PARTY_EMAILS defs; campaign_eligible_v2 not a stored column; final_send_plan has no organization_key).
- PostSend reclassified UNIQUE_REQUIRED (not duplicate) — retains Windows task.

## 2026-09-09 — P3D Production Legacy Decommission & Cleanup (authorized)
- Enumerated all live execution surfaces (automations / Windows tasks / service / scripts / _retired).
- Removed 5 legacy automations; moved 57 files to `_retired/p3d_20260909/`.
- BDExecutionHost kept Stopped (audited, not deleted). DUPLICATE_ACTIVE_TRIGGER_COUNT validated = 0.
- Frozen send chain (V2/MX/Preflight/Sender/final_send_plan/Auth) untouched.
