# PHASE 4A.1C — CONTROLLED PRODUCTION PATCH + INVENTORY VALIDATION

**Date:** 2026-09-11 (Asia/Shanghai)
**Authorization:** explicit user authorization (PHASE 4A.1C controlled patch)
**Codex source commit:** `7013b335ad4b1eec33cd559825ece7d5aaead70c` (approved production code)
**Note:** `ad1111b60e2dab7231ce8326547332defddea78d` = handoff/report-only commit on top of 7013b33; NOT a separate production version.

---

## A. PATCH SCOPE (exactly two files)

| File | Target SHA256 | Result |
|---|---|---|
| `bd_orchestrator.py` | `252ed6042b04837f6d429936771fa261889b5f556aa80140162b098894da4d05` | ✅ MATCH |
| `discovery/discovery_service.py` | `45db60d94017c3cc7b68ffdaa6044bf6af5392f790568b8766fc4236bad0c356` | ✅ MATCH |

Files fetched from Codex repo via GitHub API (stored credential, in-memory only) and SHA256-verified
against the TARGET values before deployment. No third production source file deployed.

## B. BASELINE RULE

- Read current production file SHA (bd_orchestrator=49e38bb…, discovery_service=735d70fe…).
- Backed up current files to rollback bundle.
- Deployed complete approved two-file target (full-file replace, not incremental diff).
- Verified exact target SHA after deploy.
- **BASELINE_DRIFT_DETECTED = false** — current production was the known pre-patch baseline, fully backed up;
  only the expected forward-patch delta exists. No unidentified production changes overwritten.

## C. TEMPORARY MAINTENANCE HOLD

- PRE-DEPLOYMENT states captured: Inventory / Pre-Send / Preflight / Outreach = **ACTIVE** (Recovery Sync ACTIVE).
- Held (PAUSED) the 4 canonical WorkBuddy automations for the patch window.
- Windows: PreSend = Disabled (kept), Outreach = Disabled (kept), PostSend = Ready/Enabled (UNIQUE_REQUIRED, kept).
- **DUPLICATE_ACTIVE_TRIGGER_COUNT = 0**.

## D. NO ACTIVE JOB

- ACTIVE_INVENTORY_JOB_COUNT = 0, ACTIVE_PRESEND_JOB_COUNT = 0, ACTIVE_OUTREACH_JOB_COUNT = 0.
- No Python process executing either patched file as an active production stage at deploy time.

## E. ROLLBACK

- Bundle: `C:/Users/15690/rollback_p4a1c_20260911_142132` (outside production root).
- Backed up: current `bd_orchestrator.py`, current `discovery/discovery_service.py`.
- SQLite online backup of `bd_leads.db` via `connection.backup()`; source + backup `PRAGMA integrity_check = ok`.
- Recorded: production baseline SHA256, target SHA256, DB SHA256, frozen-file SHA256, `.env` SHA256 (no content copied).
- **ROLLBACK_READY = true**.

## F. APPLY PATCH

- BD_ORCHESTRATOR_TARGET_HASH_MATCH = true
- DISCOVERY_SERVICE_TARGET_HASH_MATCH = true
- **TARGET_HASH_MATCH = 2/2**
- Frozen files verified unchanged: bd_sender / daily_session / preflight_gate / campaign_eligible_v2 / final_send_plan
  → **FROZEN_FILES_CHANGED = 0**
- **DB_SCHEMA_CHANGED = false** (only a WAL checkpoint occurred when the backup connection closed —
  db_size identical 6721536, schema_version=162, 27 tables intact, integrity_check=ok; the inventory later
  added job_runs + system_state rows, schema unchanged).
- **ENV_CHANGED = false**.

## G. PRODUCTION UTF-8 PRECHECK

- PYTHON_EXECUTABLE = `C:/Users/15690/.workbuddy/binaries/python/versions/3.13.12/python.exe` (managed production Python)
- SYS_UTF8_MODE = 1
- STDOUT_ENCODING = utf-8
- PYTHONUTF8=1, PYTHONIOENCODING=utf-8, LC_ALL=C.UTF-8, LANG=C.UTF-8
- Production Python is fully UTF-8; the dev GBK issue was environment-specific and does NOT apply.
- **UTF8_ENCODING_ERROR = false** (inventory ran without encoding error).

## H. ONE LIVE PRODUCTION INVENTORY

- Command: `bd_orchestrator.py --stage inventory --live` (exactly ONE run).
- Authorized; ran through the actual production Python execution environment.
- Expected canonical path (SAFE < target): run_places_batch → run_website_resolution → run_staging_postprocess
  → run_linked_backlog → frozen V2 SAFE measurement.
- **Legacy `inventory_monitor_executor.http_scan_website` was NOT used as SAFE authority.**

## I. REQUIRED BEHAVIOR VALIDATION

| Field | Value |
|---|---|
| BROAD_READY_BEFORE | 34 (inventory effective; DB column = 95) |
| READ_ONLY_V2_SAFE_BEFORE | 1 |
| MATERIALIZED_FSP_PLANNED_BEFORE | 0 |
| NEW_DISCOVERY_PATH_EXECUTED | true |
| PROVIDER_STATUS | ok (8 results seen, no error) |
| PROVIDER_ERROR | none |
| DISCOVERY_RESULTS_SEEN | 8 |
| NEW_UNIQUE_PLACES | 0 |
| WEBSITE_RESOLUTION_PROCESSED | 0 |
| NORMAL_STAGING_POSTPROCESS_PROCESSED | 0 |
| LINKED_BACKLOG_PATH_EXECUTED | true |
| LINKED_BACKLOG_ELIGIBLE | 18 |
| LINKED_BACKLOG_PROCESSED | 18 |
| BROAD_READY_AFTER | 34 |
| READ_ONLY_V2_SAFE_AFTER | 1 |
| MATERIALIZED_FSP_PLANNED_AFTER | 0 |

- BroadReady is INFORMATIONAL ONLY. Inventory completion authority = READ_ONLY_V2_SAFE_UNIQUE_ORGS (= 1).

## J. ACCEPTANCE LOGIC

- BROAD_READY (34) ≥ target (30) BUT READ_ONLY_V2_SAFE (1) < target (30).
- Inventory did **NOT** report `target_met`; it reported `status=partial`, `stop_reason=safe_inventory_gap`.
- Yield need not be positive: NEW_UNIQUE_PLACES=0, SAFE delta=0 are acceptable because the pipeline ran
  correctly and safely. No rules weakened to manufacture yield.

## K. SAFETY

| Check | Result |
|---|---|
| LEGACY_SCANNER_USED_AS_SAFE_AUTHORITY | false |
| GUESSED_EMAIL_PROMOTED | 0 |
| THIRD_PARTY_EMAIL_PROMOTED | 0 |
| IDENTITY_MISMATCH_PROMOTED | 0 |
| INVALID_HTTP_TLS_PROMOTED | 0 |
| REAL_SMTP_CONNECTIONS | 0 |
| REAL_IMAP_CONNECTIONS | 0 |
| FINAL_SEND_PLAN_CREATED | 0 |
| AUTHORIZATION_CREATED | 0 |
| FROZEN_FILES_CHANGED | 0 |

## L. SCHEDULER AFTER VALIDATION

All restore conditions met (ROLLBACK_READY=true, TARGET_HASH_MATCH=2/2, INVENTORY_RUN_PASS=true,
BROADREADY_FALSE_COMPLETION_FIXED_IN_PRODUCTION=true, NEW_DISCOVERY_PATH_EXECUTED=true,
LINKED_BACKLOG_PATH_EXECUTED=true, no safety regression) → restored each WorkBuddy automation to its exact
PRE-DEPLOYMENT (ACTIVE) state. No new automations; no schedule changes. Windows PreSend/Outreach remain
Disabled; Windows PostSend remains Ready/Enabled (UNIQUE_REQUIRED).

## M. WORKBUDDY GITHUB HANDOFF

- Repo: `1569032023yf-star/workbuddy-task-window` (main).
- CODEX_SOURCE_COMMIT = `7013b335ad4b1eec33cd559825ece7d5aaead70c`.
- DEPLOYMENT_RUN_ID = `p4a1c-20260911` (inventory run_id `inventory:2026-09-11:f5895b2a`).
- Updated: CURRENT_STATUS.md, LATEST_RESULT.json, CHANGELOG.md, this phase report.
- No database / secrets / runtime artifacts pushed.

---

## FINAL OUTPUT

```
DEPLOYMENT_EXECUTED              = true
ROLLBACK_READY                  = true
BASELINE_DRIFT_DETECTED         = false
TARGET_HASH_MATCH               = 2/2
FROZEN_FILES_CHANGED            = 0
SYS_UTF8_MODE                   = 1
STDOUT_ENCODING                 = utf-8
UTF8_ENCODING_ERROR             = false
NEW_DISCOVERY_PATH_EXECUTED     = true
PROVIDER_STATUS                 = ok (8 results seen, no error)
PROVIDER_ERROR                  = none
DISCOVERY_RESULTS_SEEN          = 8
NEW_UNIQUE_PLACES               = 0
LINKED_BACKLOG_PATH_EXECUTED    = true
LINKED_BACKLOG_PROCESSED        = 18
BROAD_READY_BEFORE              = 34  (DB column = 95)
BROAD_READY_AFTER               = 34  (DB column = 95)
READ_ONLY_V2_SAFE_BEFORE        = 1
READ_ONLY_V2_SAFE_AFTER         = 1
MATERIALIZED_FSP_PLANNED_AFTER  = 0
BROADREADY_FALSE_COMPLETION_FIXED_IN_PRODUCTION = true
REAL_SMTP_CONNECTIONS           = 0
FINAL_SEND_PLAN_CREATED         = 0
AUTHORIZATION_CREATED           = 0
INVENTORY_RUN_PASS              = true
PRODUCTION_PATCH_VALIDATED      = true
DUPLICATE_ACTIVE_TRIGGER_COUNT  = 0
WORKBUDDY_HANDOFF_PUSHED        = true
```

STOP.
