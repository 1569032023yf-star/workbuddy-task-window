# PHASE 4A.5D — DEPLOY CODEX 4A.8–4A.8D + PROVE ITHACA → SARATOGA

- **Date:** 2026-09-22 (Asia/Shanghai)
- **Codex release:** `dc493825cdf8d57342ca90cc582807d5d9623f67`
- **Cumulative range deployed:** `07784044` → `dc493825` (4A.8 / 4A.8B / 4A.8C / 4A.8D)
- **Production working tree:** `C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach`
- **Live DB:** `roktandrazo-outreach\data\bd_leads.db`
- **Production handoff HEAD before this phase:** `eaed05e`
- **Verdict:** deployment + validation PASSED (`NEW_FAILURES_INTRODUCED=0`); **city advancement NOT achieved — STOPPED at section D per instruction; Run 2 NOT started.**

---

## A. Pre-flight gates

| Gate | Required | Observed | Result |
|---|---|---|---|
| Scheduled Inventory paused | yes | `automation-1784775229336` = PAUSED | PASS |
| `RUNNING_INVENTORY_JOBS` | 0 | 0 | PASS |
| Held inventory lock | none | `run_lock:daily_outreach:inventory:2026-09-22` = `released` | PASS |
| Live inventory processes | 0 | 0 | PASS |
| SMTP connections | 0 | `SMTP_enabled` = `0` | PASS |
| `MATERIALIZED_FSP_PLANNED` | 0 | 0 | PASS |
| Zero-concurrency evidence | 0 new `job_runs` in 60–70 s | rows 7136 → 7136 over 70 s, `running=0` | PASS |

Sibling automations held PAUSED throughout: Pre-Send `1785804406748`, Preflight `1785804413719`, Outreach `1785804421539`. Recovery Sync `1786002601925` left ACTIVE (never launches inventory).

---

## B. Deployment — exactly 3 files, byte-identical

Scope was frozen to the three files below. `bd_orchestrator.py`, `campaign_eligible_v2.py`, `preflight_gate.py`, `bd_sender.py`, `daily_session.py`, `final_send_plan.py`, `bd_template.py` and the DB schema were **not** touched.

| File | PRE SHA256 (4A.7 `07784044`) | POST SHA256 (`dc493825`) | Byte-identical |
|---|---|---|---|
| `discovery/discovery_service.py` | `09f400b6a6b165d73a4d9dda6efa1b0ab05fa6d0e507badf7e325e06848a9e01` | `30b2487b10753e62f1ec35f68adea4fe1d8e4126c1c64b1c4d1e865aaf3151af` | true |
| `discovery/providers/browser_maps.py` | `245ed26c92a1624cb8f1bc1754f1df1efc887d4343b86ba0ceef769dc040d31a` | `88e53fa9afb3142186f1708f140cc0588810e34fd0c1a6ebc48d9dbef2e061c4` | true |
| `retail_city_queue.py` | `46d6f4521892785eccf4435bea0e4120ebf97f8862306b10d259805f7d06d1ad` | `03b4c6302dba271b5b0bed34567db5048086d4b1d0e9b2aee9a878023f349432` | true |

- Backups: `output/backup_pre_dc493825/` (manifest `_deploy_manifest.txt`), deployed snapshot: `output/deploy_dc493825/`.
- Verification: remote re-fetch vs. on-disk SHA256 compared twice (write-time and post-A/B restore) — byte-identical both times.
- Tests carried by the same cumulative range were copied into `tests/`: `test_phase4a8_website_liveness_cache_hygiene.py`, `test_phase4a8c_browser_fallback.py`, `test_phase4a8d_access_unreachable_city_liveness.py`, `test_phase4a1b_linked_backlog.py`, `test_phase2b_safe_replenishment.py`, `test_phase3d_existing_linkage.py`.

---

## C. Test validation — `NEW_FAILURES_INTRODUCED = 0`

### C.1 Per-file isolation (hard per-file timeout, production-supported runner)

| Test file | Exit | Time | Passed | Failed |
|---|---|---|---|---|
| `test_phase4a8_website_liveness_cache_hygiene.py` | 0 | 2.6 s | 5 | 0 |
| `test_phase4a8c_browser_fallback.py` | 0 | 1.5 s | 8 | 0 |
| `test_phase4a8d_access_unreachable_city_liveness.py` | 1 | 68.8 s | 34 | 4 |
| `test_phase4a7_city_queue_advancement.py` | 0 | 5.5 s | 10 | 0 |
| `test_phase4a1b_linked_backlog.py` | 124 | 240 s | — | TIMEOUT |
| `test_phase2b_safe_replenishment.py` | 1 | 5.4 s | 3 | 1 |

A whole-batch `pytest` run hangs; isolation is mandatory (a single test issues a live-site attempt).

### C.2 Controlled A/B — code swapped, tests held constant

`output/_4a5d_ab.py` (3 problematic files) and `output/_4a5d_ab_nodes.py` (5 explicit node ids). BASE = `backup_pre_dc493825` (4A.7), NEW = deployed `dc493825`. Deployed code restored and hash-verified in a `finally` block.

| Experiment | BASE failed | NEW failed | NEW_FAILURES_INTRODUCED | PREEXISTING | FIXED_BY_DEPLOY |
|---|---|---|---|---|---|
| 3 problematic files | 2 | 1 | **0** | 1 | 1 |
| 5 explicit node ids | 4 | 4 | **0** | 4 | 0 |

- `NEW_ERRORS_INTRODUCED = 0` in both experiments.
- `test_phase4a1b_linked_backlog.py` times out in **both** arms → pre-existing hang, not introduced.
- `test_phase2b_safe_replenishment.py::…test_directory_or_social_url_is_not_promoted_to_official_site` failed on BASE and passes on NEW → the deploy **fixed** one pre-existing failure.
- `test_phase4a8d` could not be measured on BASE (exit 2, collection error: the new test imports symbols that only exist in the new code) — expected for a new test file, and covered instead by the node-level A/B above.

### C.3 Root cause of the residual failures (harness, not production runtime)

The residual failures are a **stale shared test fixture**, not a runtime regression:

- `tests/test_discovery_service.py::DiscoveryDb` does not create `leads.organization_key`.
- The deployed code reads it: `discovery_service.py:621` (`lead.get('organization_key') != _gen_organization_key(...)`) and `:629-630` (`SELECT id FROM leads WHERE organization_key=?`).
- The live production `leads` table **does** have `organization_key` (verified via `PRAGMA table_info`) — so production behaviour is unaffected.
- Tests that `UPDATE leads SET organization_key=…` therefore raise `sqlite3.OperationalError: no such column: organization_key`.

Corroborating: the release's own `test_proven_no_public_email_is_terminal_from_current_staging_provenance` asserts a terminalisation transition that does not occur — it fails on **both** arms. That is a pre-existing behavioural gap in the linked-backlog lane and is the same gap that blocks section D (see below). Flagged as release-hygiene debt, not a deploy blocker.

---

## D. Run 1 — exactly one canonical Inventory (`bd_orchestrator.py --stage inventory --live`)

- `run_id` = `inventory:2026-09-22:1f8a22c4`
- `status` = `partial`, `stop_reason` = `safe_inventory_gap` (healthy terminal state), exit 0, 610.0 s
- `ACTUAL` = 16, `GAP` = 34

| Metric | Before Run 1 | After Run 1 | Δ |
|---|---|---|---|
| `ACTIVE_CITY` | Ithaca, NY (id 20) | Ithaca, NY (id 20) | — |
| Ithaca browser_maps families | 20/20 completed | 20/20 completed | — |
| `WEBSITE_LOOKUP_PENDING` (active city) | 8 | **0** | −8 |
| `OPEN_STAGED_PENDING_ACTIVE_CITY` | 8 | **0** | −8 |
| `OPEN_RETRYABLE_NETWORK_ACTIVE_CITY` | 1 | **0** | −1 |
| `WEBSITE_NOT_FOUND_STATUS` | 11 | **19** | +8 |
| `NO_PUBLIC_EMAIL_TERMINALIZED_STATUS` | 19 | **20** | +1 |
| `LINKED_AUTOMATIC_RETRY_ACTIVE_CITY` | 12 | 11 | −1 (id 336 terminalised) |
| `ACCESS_UNREACHABLE_DEFERRED_TOTAL` | 0 | 0 | — |
| `READ_ONLY_V2_SAFE_UNIQUE_ORGS` | 16 | 16 | 0 |
| `city_completion_checks(20,"browser_maps")` | 5/9 | 5/9 | — |
| `CITY_ADVANCED` | — | **false** | — |

Run counters: `DISCOVERY_RESULTS_SEEN=0`, `NEW_UNIQUE_PLACES=0`, `WEBSITE_RESOLUTION_PROCESSED=8`, `STAGING_POSTPROCESS_PROCESSED=0`.

**The 4A.5C regression class is fixed.** In 4A.5C the same 8 rows were re-selected every round with `WEBSITES_RESOLVED=8 / STAGING_PROCESSED=8` and **zero** migration (rounds 4–8). In Run 1 those 8 rows were processed **once** and all 8 reached a terminal status (`website_not_found`), leaving `OPEN_STAGED_PENDING = 0` and `OPEN_RETRYABLE_NETWORK = 0`. Both 4A.5C defects (liveness at `discovery_service.py:412-416`; cache-hygiene `OSError [Errno 22]`) are closed.

### D.1 Remaining blocking rows (why Ithaca is still `active`)

`ITHACA_STATUS` = `active`, **not** `search_matrix_exhausted`. `no_open_work` is false, which is the sole input to the four failing checks (`all_candidates_classified`, `no_unprocessed_candidates`, `official_site_recheck`, `review_recovery`). They will all flip together.

There are **11 distinct blocking rows** — every one of them in `validation_status='review_recovery'` with an empty `rejection_reason`:

| discovery id | business | `official_match` | linked lead | lead `review_reason_code` | `attempts` |
|---|---|---|---|---|---|
| 291 | Michaels | 1 | 1097 | `no_public_email_or_form` | 65 |
| 292 | Barnes & Noble | 0 | 1098 | `review_recovery` | 65 |
| 294 | Odyssey Bookstore | 0 | 1099 | `review_recovery` | 65 |
| 356 | Odyssey Bookstore | 0 | 1113 | `review_recovery` | 7 |
| 362 | Sciencenter | 0 | 1116 | `review_recovery` | 13 |
| 369 | Tompkins Center for History & Culture | 0 | 1122 | `review_recovery` | 11 |
| 392 | Cops, Kids and Toys, Inc. | 0 | 1136 | `review_recovery` | 16 |
| 393 | T.J. Maxx | 0 | 1137 | `review_recovery` | 16 |
| 395 | Kohl's | 0 | 1139 | `review_recovery` | 16 |
| 404 | Nevin Welcome Center | 0 | 1145 | `review_recovery` | 11 |
| 407 | Petrune | 0 | 1147 | `review_recovery` | 8 |

Counters: `CANDIDATE_ROWS=48`, `MANUAL_REVIEW_RETRYABLE=0`, `LINKED_BACKLOG_RETRYABLE=11`, `STAGED_PENDING=0`, `RETRYABLE_NETWORK=0`.
All 11 have `last_attempt_at` inside the Run 1 window (2026-09-22 09:16–09:22 UTC) — the lane **did** run; it just never terminates them.

### D.2 Root cause — the retry lane admits a state its terminaliser does not cover

The deployed selector and the deployed terminaliser disagree on `review_recovery`:

- **Admitted:** `discovery_service.py:607` allows `row.validation_status in {…, 'manual_review_needed', 'review_recovery'}`; `:610` passes because `rejection_reason` is empty; `:605`/`:625` accept lead `review_reason_code='review_recovery'` with detail `review_recovery=official_site_unavailable`.
- **Never terminated:** `_linked_backlog_terminal_outcome` (`:698-723`) has branches only for `website_resolution:not_found:*`, `manual_review_needed + official_match=1 + rejection_reason='no_public_email_or_form'`, `identity_review`, and `manual_review_needed + review_reason_code='no_public_email_or_form'`. With `validation_status='review_recovery'` and an empty `rejection_reason`, it falls through and returns `''`.
- **Never deferred either:** `_defer_access_unreachable` is only called at `:682` when `fetcher.last_site_automation_recovery_exhausted` is true, which is set in `end_site()` (`:299-303`) only if *static access failed AND the browser was attempted AND no qualifying page was found*. All 11 rows still have `automation_terminal_outcome = null`, so this path never fired.

Net effect: a monotonic retry loop. `attempts` was already 7–65 before Run 1 and increments every round; `no_open_work` stays false forever and the city can never advance. This is a **liveness gap in the deployed 4A.8/4A.8D release itself**, distinct from the 4A.5C defects it did fix, and it is exactly the behaviour asserted by the release's own pre-existing failing test `test_proven_no_public_email_is_terminal_from_current_staging_provenance`.

Two candidate fixes for the next Codex batch (not applied here; no code was modified in this phase):
1. Extend `_linked_backlog_terminal_outcome` to cover the `review_recovery` replay state (e.g. terminalise to `no_public_email` when a verified same-party fetch found neither a visible public email nor a contact form, and to `website_not_found`/`identity_review` on the corresponding evidence).
2. Add a bounded attempt ceiling that routes to `_defer_access_unreachable` (keeping `email` empty and the row non-V2-eligible) rather than retrying indefinitely.

Note id 291 (Michaels) is the closest to resolvable: `official_match=1` and lead `review_reason_code='no_public_email_or_form'`, so it would terminalise as `no_public_email` if `rejection_reason`/`validation_status` reached the state the existing branch expects.

---

## E. Saratoga Springs verification — NOT EXECUTED

Section E is gated on Run 1 proving `ITHACA_STATUS=search_matrix_exhausted`. That gate was **not** met, therefore:

- Run 2 was **not** started (per the instruction's explicit STOP condition).
- `ACTIVE_CITY` remains Ithaca, NY; `CITY21_STATUS` = `pending`; `CITY_QUEUE_ADVANCEMENT_VERIFIED` = false.

---

## F. Scheduler state after the phase

Because the acceptance gate did not pass, the Inventory automation was left **PAUSED** (fail-closed) instead of being restored to ACTIVE, and no long accumulation loop was started. This is an operator decision point.

| Automation | State |
|---|---|
| Inventory `1784775229336` (15:00 +08) | **PAUSED** (failed acceptance → left paused) |
| Pre-Send `1785804406748` | PAUSED |
| Preflight `1785804413719` | PAUSED |
| Outreach `1785804421539` | PAUSED |
| Recovery Sync `1786002601925` | ACTIVE |

New SAFE checkpoint: `READ_ONLY_V2_SAFE_UNIQUE_ORGS = 16`.

---

## G. Safety

| Check | Value |
|---|---|
| `SMTP_ENABLED` | 0 |
| `SEND_LOG_TODAY` | 0 |
| `MATERIALIZED_FSP_PLANNED` | 0 |
| `LAST_SEND_AT` | 2026-09-16T01:09:52+08:00 |
| `RUNNING_INVENTORY_JOBS` / `INVENTORY_LOCK` | 0 / `released` |
| `ACCESS_UNREACHABLE_DEFERRED_TOTAL` | 0 |
| guessed / third-party emails added | none |
| manual recipients | none |
| MX / V2 standard relaxed | no |
| DB schema changed | no |
| rows relabelled `no_public_email` without factual proof | none (`no_public_email` +1 came from the lane's own evidence gate) |

`LEADS_TOTAL` 1114, `EMAIL_POOL` 604, `OFFICIAL_EMAIL_POOL` 340, `DISCOVERY_ROWS` 412, `BROAD_READY_STORED_FLAG` 95 — all unchanged before/after Run 1 (only staging statuses moved).

---

## FINAL

```
CODEX_RELEASE=dc493825cdf8d57342ca90cc582807d5d9623f67
DEPLOYED_FILES=3
DEPLOYED_FILES_LIST=discovery/discovery_service.py,discovery/providers/browser_maps.py,retail_city_queue.py
BYTE_IDENTICAL=true
BACKUP_PATH=output/backup_pre_dc493825/
TARGETED_TESTS_PASSED=47
TARGETED_TESTS_FAILED=5
TARGETED_TESTS_TIMEOUTS=1
NEW_FAILURES_INTRODUCED=0
NEW_ERRORS_INTRODUCED=0
FIXED_BY_DEPLOY=1
PREEXISTING_FAILURES=4
INVENTORY_RUNS_EXECUTED=1
RUN1_RUN_ID=inventory:2026-09-22:1f8a22c4
RUN1_STATUS=partial
RUN1_STOP_REASON=safe_inventory_gap
RUN1_SECONDS=610.0
WEB_LOOKUP_PENDING_BEFORE=8
WEB_LOOKUP_PENDING_AFTER=0
OPEN_STAGED_PENDING_BEFORE=8
OPEN_STAGED_PENDING_AFTER=0
OPEN_RETRYABLE_NETWORK_BEFORE=1
OPEN_RETRYABLE_NETWORK_AFTER=0
WEBSITE_NOT_FOUND_BEFORE=11
WEBSITE_NOT_FOUND_AFTER=19
NO_PUBLIC_EMAIL_BEFORE=19
NO_PUBLIC_EMAIL_AFTER=20
ACCESS_UNREACHABLE_DEFERRED=0
LINKED_AUTOMATIC_RETRY_BEFORE=12
LINKED_AUTOMATIC_RETRY_AFTER=11
ITHACA_QUERY_FAMILIES=20/20
ITHACA_STATUS=active
CITY_COMPLETION_CHECKS=5/9
CITY_COMPLETION_MET=false
BLOCKING_ROW_COUNT=11
BLOCKING_ROW_IDS=291,292,294,356,362,369,392,393,395,404,407
BLOCKING_ROW_STATE=validation_status=review_recovery,rejection_reason empty,attempts 7..65,automation_terminal_outcome null
ROOT_CAUSE_REMAINING=selector admits review_recovery (discovery_service.py:607,610,625) but _linked_backlog_terminal_outcome (:698-723) has no review_recovery branch and _defer_access_unreachable (:682-684) never fires
CITY_ADVANCED=false
ACTIVE_CITY=Ithaca, NY
ACTIVE_CITY_ID=20
NEXT_PENDING_CITY=Saratoga Springs, NY
CITY_QUEUE_ADVANCEMENT_VERIFIED=false
RUN2_EXECUTED=false
SARATOGA_ACTIVATED=false
SAFE_BEFORE=16
SAFE_AFTER=16
MATERIALIZED_FSP_PLANNED=0
SENDS_TODAY=0
SMTP_ENABLED=0
LAST_SEND_AT=2026-09-16T01:09:52.031266+08:00
INVENTORY_AUTOMATION=PAUSED
PRESEND_PREFLIGHT_OUTREACH=PAUSED
RECOVERY_SYNC=ACTIVE
STOP_REASON=city_advancement_not_proven:review_recovery_liveness_gap
```

## Next recommended action

One Codex batch limited to `discovery/discovery_service.py`: give the `review_recovery` replay state a bounded, evidence-backed exit (terminaliser branch and/or attempt ceiling → `access_unreachable` deferral). Then re-run a single canonical Inventory; the four failing checks share the single `no_open_work` input and should flip together, unblocking `search_matrix_exhausted` and the Saratoga advance.

## Handoff commit

- `COMMIT_SHA = 8029142f0fa577c4ac6ddf6e669ac218fa253573`
- `PUSH_SUCCESS = true` — verified authoritatively via `git ls-remote origin main` → `8029142f0fa577c4ac6ddf6e669ac218fa253573` (`refs/heads/main`).
- Files in the commit: this report, `CHANGELOG.md`, `CURRENT_STATUS.md`, `LATEST_RESULT.json`. No production code, no DB, no credentials.

## Provenance

Live reads only, all dated 2026-09-22 (Asia/Shanghai): `data/bd_leads.db` (`retail_city_queue`, `lead_discovery_results`, `leads`, `job_runs`, `system_config`), `job_runs.run_id=inventory:2026-09-22:1f8a22c4`, `output/4a5d_metrics_before_run1.json`, `output/4a5d_metrics_after_run1.json`, `output/4a5d_blockers.json`, `output/4a5d_ab_summary.json`, `output/4a5d_abnodes_summary.json`, `output/4a5d_run1_driver.log`, `output/backup_pre_dc493825/_deploy_manifest.txt`.
