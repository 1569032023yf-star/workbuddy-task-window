# CHANGELOG — roktandrazo BD Production Handoff

All entries are production-handoff events. Live metrics authority = `bd_leads.db` (read-only).
Repository authority: `workbuddy-task-window` = PRODUCTION; `roktandrazo-outreach-codex` = DEVELOPMENT (never written here).

---

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
