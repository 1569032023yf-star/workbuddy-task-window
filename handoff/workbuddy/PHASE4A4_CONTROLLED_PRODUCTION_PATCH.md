# PHASE 4A.4 — CONTROLLED PRODUCTION LEAD-FACTORY PATCH

> **Mandate (user-authorized):** Deploy the approved Lead-Factory patch set (Codex commits `54a7fb65…` → `05c0a4191…`, consolidated at `05c0a41919167f0beed531ed7e6b1d40d89a36f1`) into the 4 authorized production files. Controlled: maintenance-hold + no-active-run + backup + baseline gate + apply-only-accepted-hunks + static/regression validation + ONE canonical live Inventory + acceptance + scheduler resume (Inventory+Recovery only) + GitHub handoff.
> **Source acceptance:** Phase 4A.3T acceptance report `2c1b69c36384a7958148037aa4b146acd4bcf676` → `LEAD_FACTORY_THROUGHPUT_PROVEN=true`, `READY_FOR_CONTROLLED_PRODUCTION_PATCH=true`.
> **Deploy date:** 2026-09-20 (Asia/Shanghai).
> **Outcome:** DEPLOYED + VALIDATED + ACCEPTED. 4 production files patched (production = dev pre-fix base `d96b004997aa9903459c6afa424f8c265c1750b8`, so whole-file copy from `05c0a419` = byte-identical accepted hunks, **zero unrelated drift**). One canonical live Inventory ran clean (3m26s, exit 0). No SMTP / IMAP / Outreach / PreSend / FSP / Authorization. SAFE stayed 0 (Ithaca NY exhausted; legitimate safe-exhaustion per runbook G). Scheduler resumed: Inventory + Recovery ACTIVE; PreSend/Preflight/Outreach held PAUSED (SAFE<40).

---

## A. Production pre-audit (before patch)

- Production app root = `C:/Users/15690/WorkBuddy/2026-06-05-15-31-42/roktandrazo-outreach` (git repo, branch `master`, remote `workbuddy-task-window`).
- 4 authorized files present + byte-identical to dev pre-fix base `d96b004997aa9903459c6afa424f8c265c1750b8` → copying dev-`05c0a419` versions applies ONLY the accepted hunks with **zero drift**.
- No active BD Python process (Get-CimInstance) → no concurrent run.
- Forbidden files (V2/MX/preflight/sender/final_send_plan/template/daily_session) confirmed present; their SHAs recorded as pre-patch baseline.
- SQLite online backup + byte-for-byte source backups captured → `C:/Users/15690/AppData/Local/Temp/rollback_4a4_20260920_153457/` (integrity ok; `bd_leads.db.before` SHA `38470fc5…`; no `.env`/secrets copied).

| Pre-patch SHA256 | File |
|---|---|
| `45db60d94017c3cc7b68ffdaa6044bf6af5392f790568b8766fc4236bad0c356` | discovery/discovery_service.py |
| `c9b06668a33e002473b215442b5fed7446ec927be3dca35e6f8d7203e7762293` | outreach_control.py |
| `ffbcacdf68992217b6680b19e69713ced045684d2a48f7375db1e092f667b33f` | discovery/website_resolver.py |
| `b4408fbbed69ab645dd178a74268e3f10eb6fa75e7065c2106be3040a13c9c2d` | discovery/providers/browser_maps_scraper.py |

`BASELINE_DRIFT_DETECTED=false` (all 4 match dev pre-fix base).

---

## B. Accepted patch set (5 Codex commits → 4 files)

Built from dev commits `54a7fb65…`, `040408c64…`, `adfe8a938…`, `c0061917…`, `05c0a4191…`; applied only accepted hunks, no unrelated drift; no other source file authorized.

| Commit | File(s) | Accepted hunk |
|---|---|---|
| `54a7fb65` | discovery_service.py, outreach_control.py | Zero-yield progression: `_query_consecutive_empty_pages` + `terminalized` summary + `_linked_backlog_terminal_outcome`/`_terminalize_linked_backlog`; outreach_control `_configured_inventory_target`→`INVENTORY_TARGET` default 50; `inventory_target_for_date` uses `max(60,target)` (weekend buffer) |
| `040408c64` | website_resolver.py | `_bounded_search` (multiprocessing `spawn`, `timeout_seconds`) — bounds website-resolution wall-clock |
| `adfe8a93` | website_resolver.py | Windows Job Object `_attach_kill_on_close_job`/`_close_kill_job` — kills Chromium descendant tree on close |
| `c0061917` | discovery_service.py, browser_maps_scraper.py | `_is_google_owned_host`/`_browser_maps_place_source`/`_safe_browser_maps_website` backfill + `browser_maps_scraper._is_external_link` google-owned rejection (wrong-domain guard) |
| `05c0a4191` | discovery_service.py | `extract_direct_place_data` — direct-place panel handling (new Google Maps result shape) |

---

## C. Production source scope (4 authorized files only)

Changed: `discovery/discovery_service.py`, `outreach_control.py`, `discovery/website_resolver.py`, `discovery/providers/browser_maps_scraper.py`.
**Explicitly NOT modified** (forbidden, verified unchanged post-patch): `bd_sender.py`, `daily_session.py`, `preflight_gate.py`, `campaign_eligible_v2.py`, `final_send_plan.py`, `bd_template.py`, DB schema.

---

## D. Backup / rollback

- Bundle: `C:/Users/15690/AppData/Local/Temp/rollback_4a4_20260920_153457/`
  - `bd_leads.db.before` (SQLite online `con.backup()`, integrity_check=ok, SHA `38470fc5…`)
  - `src_discovery__discovery_service.py`, `src_outreach_control.py`, `src_discovery__website_resolver.py`, `src_discovery__providers__browser_maps_scraper.py` (byte-for-byte source copies)
  - `rollback_manifest.json`, `ROLLBACK_INSTRUCTIONS.txt`
- `ROLLBACK_READY=true`. To roll back: restore the 4 `.before` source copies + `bd_leads.db.before` over the production files/DB.

---

## E. Static / regression validation

- **Targeted logic tests** (`validate_targeted.py`, 22 cases on patched functions: google-owned host rejection, place source, safe website, inventory-target config, bounded resolver happy/raise paths, direct-place guard): **22 PASS / 0 FAIL**, `TARGETED_FAILED=0`, `TARGETED_ERRORS=0`.
- **Full regression suite** (`test_discovery_service` + `test_campaign_eligible`, unittest): 32 tests, 4 failures. `regression_compare.py` swapped pre-patch `discovery_service.py` in and re-ran → `POST_PATCH_FAILURES == PRE_PATCH_FAILURES` (both 4) → `NEW_FAILURES_INTRODUCED_BY_PATCH=[]`. The 4 failures are pre-existing (1 env artifact `_retired\p3d_20260909\output\p2_3i_replay.py` in static-scan test; 3 staging-status tests). Production correctly restored to patched state after compare.
- **Policy unchanged gates:** `V2_POLICY_CHANGED=false`, `MX_POLICY_CHANGED=false`, `TEMPLATE_CHANGED=false`, `DB_SCHEMA_CHANGED=false` (forbidden SHAs identical; `consecutive_pages_without_new_place` column already exists → no migration).
- **Forbidden-file SHAs post-patch (== pre-patch):** preflight_gate `2cd286f2…`, campaign_eligible_v2 `1143bedf…`, bd_sender `002d68a1…`, daily_session `f4559a34…`, final_send_plan `26de2f01…`, bd_template `0c900d518…`.

---

## F. One canonical production Inventory (live, controlled)

- Launched via `launch_inventory.py` (background task, completed exit 0, 3m26s): env `SAFE_INVENTORY_TARGET=50`, `DISCOVERY_PROVIDER=browser_maps`, `BROWSER_MAPS_MODE=direct`, `SCRAPER_PROXY=http://127.0.0.1:3213`, `python bd_orchestrator.py --stage inventory --live`.
- `--live` runs the Inventory STAGE only (NOT Outreach; no SMTP).

| Metric | Value |
|---|---|
| run_id | `inventory:2026-09-20:c2b1abfe` |
| Business date | 2026-09-20 (Sunday → weekend buffer) |
| Target | 60 (orchestrator `max(60,50)`) |
| send_enabled | false |
| Duration | ~3m26s (15:55:55 → 15:59:21 +08) |
| Active city | Ithaca, NY |
| NEW_DISCOVERY_PATH_EXECUTED | true |
| DISCOVERY_RESULTS_SEEN | 8 |
| NEW_UNIQUE_PLACES | 0 |
| WEBSITE_RESOLUTION_PROCESSED | 0 |
| NORMAL_STAGING_POSTPROCESS_PROCESSED | 0 |
| LINKED_BACKLOG_PATH_EXECUTED | true |
| Linked backlog (eligible/processed/website_processed/postprocess_processed/existing_leads_linked/terminalized) | 18 / 18 / 11 / 7 / 0 / 14 |
| BROAD_READY | 33 |
| READ_ONLY_V2_SAFE_UNIQUE_ORGS | 0 / 60 |
| MATERIALIZED_FSP_PLANNED | 0 |

**Before/after deltas** (snapshot_before vs snapshot_after): SAFE 0→0; official_emails 346→346 (Δ0); evidence 844→844 (Δ0); linked_lead_rows 273→273 (Δ0); total_leads 1069→1069 (Δ0); network_retry_total 0→0 (Δ0); vstat: `manual_review_needed −13`, `no_public_email +3`, `website_not_found +11`, `review_recovery −1`.

**Wrong-domain regression check:** `google_owned_website_rows_in_db = 0` → no wrong-domain regression.
**Orphan browser-process check:** all 26 `chrome.exe` processes = `C:\Program Files\Google\Chrome\Application\chrome.exe` (user's normal Chrome); **0** from `ms-playwright` (scraper orphans) → no orphan browser processes.

---

## G. Production acceptance (PASS)

| Criterion | Result |
|---|---|
| Inventory completes normally (no stall) | PASS — exit 0, 3m26s, clean terminalization of 14 linked backlog |
| direct Place handling works | PASS — `extract_direct_place_data` path executed; staging ran |
| network_retry regression absent | PASS — before=0, after=0 (no return of regression) |
| legitimate progress OR safe exhaustion | PASS — safe exhaustion: Ithaca NY exhausted for discovered set (8 dup places, 0 new); terminalized 14 |
| no wrong-domain regression | PASS — `google_owned_website_rows_in_db=0` |
| V2/MX/template/DB-schema unchanged | PASS — forbidden SHAs identical |
| no orphan browser processes | PASS — 0 ms-playwright processes |
| SAFE≥40 required? | NO — runbook G explicitly does NOT require SAFE≥40 |

**ACCEPTANCE = PASS.** Controlled production Lead-Factory patch deployed + validated.

---

## H. Scheduler after patch

- **Resumed ACTIVE:** Inventory `automation-1784775229336` (daily 15:00 +08), Recovery Sync `automation-1786002601925` (daily 08:45 +08).
- **Held PAUSED (until SAFE≥40):** Pre-Send `1785804406748` (Mon–Fri 21:30), Preflight `1785804413719` (Mon–Fri 21:50), Outreach `1785804421539` (Mon–Fri 22:00).
- Windows tasks: PostSend UNIQUE_REQUIRED (Ready) — unchanged.
- `DUPLICATE_ACTIVE_TRIGGER_COUNT=0`.
- SAFE=0 < 40 → sending chain remains held fail-closed by design.

---

## I. GitHub handoff

- Created this doc (`handoff/workbuddy/PHASE4A4_CONTROLLED_PRODUCTION_PATCH.md`).
- Updated `CURRENT_STATUS.md`, `LATEST_RESULT.json`, `CHANGELOG.md` (handoff-only; **no production code committed to `main`** — see note below).
- Safe-git precheck: staged ONLY the 4 handoff doc files; no `.env` / credentials / `*.db` / PII / production code.
- **NOTE on production-code persistence:** the live production code is deployed in the `master` workspace checkout (verified by SHA256 below; source-of-truth = Codex commit `05c0a419`). The `main` branch's `roktandrazo-outreach/` is a **stale snapshot** (different SHAs, even missing `website_resolver.py`) — committing the 4 patched files there would corrupt the canonical source, so they were deliberately NOT committed to `main`. This matches all prior Phase 4A.x handoffs (handoff docs only). A separate, authorized sync of `main`'s `roktandrazo-outreach/` is recommended but out of scope.

---

## FINAL (deployment answers)

```
DEPLOYMENT_EXECUTED              = true
CODEX_SOURCE_COMMIT             = 05c0a41919167f0beed531ed7e6b1d40d89a36f1
PHASE4A3T_ACCEPTANCE_COMMIT     = 2c1b69c36384a7958148037aa4b146acd4bcf676
PRODUCTION_FILES_CHANGED        = 4
CHANGED_FILES                   = discovery/discovery_service.py, outreach_control.py, discovery/website_resolver.py, discovery/providers/browser_maps_scraper.py
PREPATCH_SHA256                 = discovery_service 45db60d9...; outreach_control c9b06668...; website_resolver ffbcacdf...; browser_maps_scraper b4408fbb...
POSTPATCH_SHA256                = discovery_service ec0c1d0e...; outreach_control b23c1359...; website_resolver 8945d439...; browser_maps_scraper 18d1c79d...
AUTH_IDENTICAL_TO_DEV           = true (zero unrelated drift)
BASELINE_DRIFT_DETECTED         = false
ROLLBACK_READY                  = true
ROLLBACK_BUNDLE                = C:/Users/15690/AppData/Local/Temp/rollback_4a4_20260920_153457/
TARGETED_TESTS                 = 22 PASS / 0 FAIL
FULL_SUITE                      = 32 tests; 4 failures (ALL pre-existing); NEW_FAILURES_INTRODUCED_BY_PATCH=[]
FAILED                          = 0 (new)
ERRORS                         = 0 (new)
V2_POLICY_CHANGED               = false
MX_POLICY_CHANGED               = false
TEMPLATE_CHANGED                = false
DB_SCHEMA_CHANGED               = false
INVENTORY_COMPLETED             = true (run_id inventory:2026-09-20:c2b1abfe; exit 0; 3m26s)
INVENTORY_RUN_ID                = inventory:2026-09-20:c2b1abfe
SAFE_BEFORE                     = 0
SAFE_AFTER                      = 0
WEBSITES_RESOLVED               = 0 (no new unique places; Ithaca NY exhausted)
NETWORK_RETRY                   = 0 (no regression; was already 0)
OFFICIAL_EMAILS_FOUND           = 0
FULL_EVIDENCE_CREATED           = 0
EXISTING_LEADS_LINKED           = 0
WRONG_DOMAIN_REGRESSION         = false (google_owned_website_rows_in_db=0)
ORPHAN_BROWSER_PROCESSES        = false (0 ms-playwright; 26 user-Chrome)
INVENTORY_AUTOMATION_RESTORED   = true (automation-1784775229336 ACTIVE)
RECOVERY_AUTOMATION_RESTORED    = true (automation-1786002601925 ACTIVE)
SEND_AUTOMATION_HELD            = true (PreSend/Preflight/Outreach PAUSED; SAFE<40)
READY_TO_BUILD_SAFE_POOL        = false (SAFE=0; needs new cities/leads + user authorization for enrichment)
READY_FOR_40_RECIPIENT_ACCEPTANCE = false (SAFE=0<40; sending chain held)
SMTP_CONNECTIONS                = 0
IMAP_CONNECTIONS                = 0
OUTREACH_SEND_COUNT             = 0
PRESEND_FSP_CREATED             = 0
AUTHORIZATION_CREATED           = 0
COMMIT_SHA                      = (see GITHUB_HANDOFF_PUSHED)
PUSH_SUCCESS                    = true
```
