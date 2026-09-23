# PHASE 4A.5F — Final discovery-liveness release deployed + Ithaca → Saratoga proven

- **Phase:** 4A.5F
- **Generated:** 2026-09-23 (Asia/Shanghai)
- **Outcome:** **BOTH ACCEPTANCE RUNS PASSED.** Ithaca reached `search_matrix_exhausted` in Run 1; Run 2 activated and proved real discovery work in Saratoga Springs, NY. Inventory automation restored to ACTIVE.
- **Codex release:** `641b36b87af596a503cdcb8fb518eab66d5ffbb9` ("Finalize Phase 4A.8H automation exhaustion")
- **Previous production baseline:** `dc493825cdf8d57342ca90cc582807d5d9623f67`
- **Deployed file:** `discovery/discovery_service.py` — exactly one file; nothing else touched.

---

## A. Release input and gate check

The release gate was verified before anything was written:

| Gate field (from the Codex 4A.8H report) | Required | Observed |
|---|---|---|
| `READY_FOR_PRODUCTION_REVIEW` | true | **true** |
| `LINKED_RETRY_ROWS_BEFORE` | — | 11 |
| `LINKED_RETRY_ROWS_AFTER` | — | 0 |
| `CITY_COMPLETION_ALL_MET` | true | **true** |
| `ITHACA_STATUS` | `search_matrix_exhausted` | **search_matrix_exhausted** |
| `NEXT_CITY` | Saratoga Springs | Saratoga Springs |
| `CITY_QUEUE_ADVANCEMENT_VERIFIED` | true | **true** |
| `TARGETED` / `FULL` | clean | 52 / 0 / 0 and 423 / 0 / 0 |

The commit exists on the authoritative remote (`git ls-remote … refs/heads/main` = `641b36b8`).
Note: the preceding phase (4A.5E) had correctly refused to start because that commit did not yet exist.

**What the release changes (and what it does not).** The 4A.8H delta to `discovery_service.py` is 8 lines and is
strictly an *operational-exhaustion* predicate correction. The recovery-exhausted flag previously excluded a
failed HTTPS-compatibility probe; it now reads:

```
last_site_automation_recovery_exhausted = (
    (self._site_static_access_failure or self._site_https_compatibility_probe)
    and self._site_browser_attempted
    and not self._site_qualifying_page
)
```

It only drives `automation_terminal_outcome='access_unreachable'`. In-source comments state it *"never asserts
that no public email exists"* and that the HTTPS probe *"contributes to operational exhaustion only after this
bounded browser attempt has actually run"*. There is no merchant, domain, or email special case. No V2 / MX /
send-eligibility policy was touched.

The deployed file is the **complete cumulative** payload relative to `dc493825` (83 insertions / 10 deletions over
that file), i.e. it carries 4A.8E fetcher-state wiring, 4A.8F HTTPS-first probe, 4A.8G bounded `www`/apex alias
probe, and this 4A.8H exhaustion finalization.

## B. Pre-deploy safety — all gates held before the write

```
Inventory automation            = PAUSED
RUNNING_INVENTORY_JOBS          = 0
INVENTORY_LOCK                  = released   (98 lock keys inspected; 0 held)
LIVE_INVENTORY_PROCESSES        = 0
SMTP_enabled                    = 0
MATERIALIZED_FSP_PLANNED        = 0
SEND_LOG_TODAY                  = 0          (LAST_SEND_AT = 2026-09-16T01:09:52.031266+08:00)
PreSend / Preflight / Outreach  = PAUSED
Recovery Sync                   = ACTIVE
ZERO_CONCURRENCY_EVIDENCE       = true       (job_runs 7139 → 7139 over 70 s; 0 running)
```

Backup taken before the write: `output/backup_pre_4a5f/discovery_service.py`, SHA256 verified equal to the
pre-deploy hash.

## C. Deploy + verification

```
PRE_DEPLOY_SHA256  = 30b2487b10753e62f1ec35f68adea4fe1d8e4126c1c64b1c4d1e865aaf3151af  (98,283 bytes)
CODEX_BLOB_SHA256  = d23c760aea14c995d859e709acf898ce8e691dd70b129df2f4b920d9e9617d07  (102,579 bytes)
POST_DEPLOY_SHA256 = d23c760aea14c995d859e709acf898ce8e691dd70b129df2f4b920d9e9617d07  (102,579 bytes)
DISCOVERY_SERVICE_BYTE_IDENTICAL = true
```

`py_compile` and `ast.parse` both clean (2,038 lines). No database migration. No other production file was
written — `browser_maps.py`, `retail_city_queue.py`, `bd_orchestrator.py`, V2/MX files, sender, templates and the
DB schema were untouched.

## D. Regression validation — controlled A/B

Method: the release's own test files were staged (held **constant** across both arms); only
`discovery/discovery_service.py` was swapped. Arm BASE = `30b2487b` (pre-deploy), Arm NEW = `d23c760a` (deployed).

| Test file | BASE | NEW |
|---|---|---|
| `test_phase4a8_website_liveness_cache_hygiene.py` | 5 passed | 5 passed |
| `test_phase4a8c_browser_fallback.py` | 8 passed | 8 passed |
| `test_phase4a8d_access_unreachable_city_liveness.py` | TIMEOUT 240 s | TIMEOUT 240 s |
| `test_phase4a8f_https_upgrade.py` | **8 FAILED** | **13 passed / 0 failed** |
| `test_phase4a1b_linked_backlog.py` | TIMEOUT 240 s | TIMEOUT 240 s |
| `test_phase4a1c_discovery_coexistence.py` | 4 passed / 2 failed | 4 passed / 2 failed |
| `test_phase4a7_city_queue_advancement.py` | 10 passed | 10 passed |

```
NEW_FAILURES_INTRODUCED = 0
NEW_ERRORS_INTRODUCED   = 0
FIXED_BY_DEPLOY         = 8
BASE_TIMEOUTS == NEW_TIMEOUTS == [4a8d, 4a1b]   (identical sets)
```

- The 8 failures on BASE are the 4A.8F/G/H behaviours that did not exist before this deploy; the release **fixes**
  them (13 passed).
- The two 240 s timeouts reproduce **identically on both arms** (their own real-network hang) and are therefore
  pre-existing, not regressions.
- `test_phase4a1c` could not be collected on **either** arm because the production tree lacked the helper
  `tests/schema_fixture.py` (present in the release tree). That helper was restored from `641b36b8` — **only the
  missing helper, no test logic touched** — after which the file runs and shows the same 2 failures on both arms.
  Those 2 failures are environment-dependent fixtures, not caused by this deploy.
- `PER_FILE_TIMEOUT` isolation was used to locate hangs; the harness was not redesigned.

## E. Live before-snapshot (Run 1)

```
ACTIVE_CITY                    = Ithaca, NY   (id 20)
ITHACA_STATUS                  = active
ITHACA_BROWSERMAPS_FAMILIES    = 20   (20 completed / 0 pending / 0 running)
LINKED_AUTOMATIC_RETRY_BEFORE  = 11   ids [291,292,294,356,362,369,392,393,395,404,407]
WEBSITE_LOOKUP_PENDING_BEFORE  = 0
OPEN_STAGED_PENDING_BEFORE     = 0
OPEN_RETRYABLE_NETWORK_BEFORE  = 0
READ_ONLY_V2_SAFE_UNIQUE_ORGS_BEFORE = 16
MATERIALIZED_FSP_PLANNED_BEFORE      = 0
NEXT_PENDING_CITY              = Saratoga Springs, NY (id 21)
```

The retry count was **measured live** (11), not assumed — and it matched the Codex replay's 11.

## F. Acceptance — Run 1 (exactly one canonical Inventory)

`run_id = inventory:2026-09-23:3e75c913`, `status = partial`, `stop_reason = safe_inventory_gap`,
`04:17:47 → 04:26:48 UTC` (541 s). Settings unchanged from production defaults (`DISCOVERY_PROVIDER=browser_maps`,
`BROWSER_MAPS_MODE=direct`, proxy `127.0.0.1:3213`, `SAFE_INVENTORY_TARGET=50`, `WORKBUDDY_DISCOVERY_MAX_PAGES=2`).
No SMTP.

Orchestrator linked-backlog line:

```
{'eligible': 11, 'processed': 11, 'website_processed': 0, 'postprocess_processed': 11,
 'existing_leads_linked': 0, 'terminalized': 1, 'automation_deferred': 9}
```

| Metric | Before | After |
|---|---|---|
| `LINKED_AUTOMATIC_RETRY` | 11 | **0** |
| `ACCESS_UNREACHABLE_DEFERRED_TOTAL` | 0 | **9** |
| `WEBSITE_LOOKUP_PENDING` (active city) | 0 | 0 |
| `OPEN_STAGED_PENDING` (active city) | 0 | 0 |
| `OPEN_RETRYABLE_NETWORK` (active city) | 0 | 0 |
| `NO_PUBLIC_EMAIL` (status) | 20 | 21 |
| `WEBSITE_NOT_FOUND` (status) | 19 | 19 |
| `READ_ONLY_V2_SAFE_UNIQUE_ORGS` | 16 | 16 |

```
AUTOMATION_DEFERRED_THIS_RUN        = 9
TERMINALIZED_EXISTING_OUTCOMES      = 1        (row 369 → existing no_public_email semantics)
LINKED_AUTOMATIC_RETRY_AFTER        = 0        ← acceptance authority
```

The 11-row cohort resolved as 9 × `access_unreachable` (291, 292, 294, 356, **362**, 392, 393, 395, 404) +
1 × terminal `no_public_email` via the pre-existing evidence path (369) + 1 × `identity_review` (407). Row 362
(Sciencenter, `http://www.sciencenter.org`) follows the operational-exhaustion path — **no email or evidence was
inserted for it**.

City completion after Run 1:

```
CITY_COMPLETION_CHECKS(20,'browser_maps') = 9/9   (was 5/9)
CITY_COMPLETION_ALL_MET                   = true
ITHACA_STATUS                             = search_matrix_exhausted
CITY20 completion_reason                  = search_matrix_exhausted   (completed_at 2026-09-23T04:25:32Z)
```

## G. Acceptance — Run 2 (exactly one second canonical Inventory)

Authorized only because Run 1 proved `search_matrix_exhausted` + all nine checks. At start there was **no active
city** (Ithaca closed, Saratoga pending), so the orchestrator's own activation lane ran.

`run_id = inventory:2026-09-23:86d61cde`, `status = partial`, `stop_reason = safe_inventory_gap`, 168.7 s.

```
CITY_BEFORE  = none
CITY_AFTER   = Saratoga Springs, NY        ← ACTIVE_CITY_AFTER_RUN2
CITY_ADVANCED = true                        ← CITY_QUEUE_ADVANCEMENT_VERIFIED = true
NEXT_CITY_AFTER = Cooperstown, NY
```

Orchestrator: `Active city: Saratoga Springs, NY; new discovery then linked backlog`, then
`Query: toy store Saratoga Springs NY` → `[+] G. Willikers Toys (Saratoga Springs, NY)`.

```
SARATOGA_DISCOVERY_RESULTS_SEEN      = 2
SARATOGA_NEW_UNIQUE_PLACES           = 1
SARATOGA_ACTIVE_QUERY_FAMILY         = toy store
SARATOGA_QUERY_STATUS                = 20 families seeded (0 completed / 19 pending / 1 running)
LINKED_BACKLOG_PROCESSED             = 0   (Ithaca's cohort fully drained — no carry-over)
ACCESS_UNREACHABLE_DEFERRED_TOTAL    = 9   (unchanged)
```

Saratoga's first new lead (id 1150, `organization_key = org:domain:gwillikerstoys.com`) was created through the
normal path: **email empty**, `email_source_type = contact_form`, evidence URL
`https://www.gwillikerstoys.com/contact-us`. No email or evidence was invented.

## H. After successful acceptance

```
INVENTORY_AUTOMATION_RESTORED = true   (automation-1784775229336 → ACTIVE)
PRESEND_PAUSED  = true
PREFLIGHT_PAUSED = true
OUTREACH_PAUSED  = true
RECOVERY_ACTIVE  = true
```

No manual accumulation loop was started and no additional Inventory round was run in this phase. Future NY queue
work is left to the canonical scheduler.

## I. Send safety — all invariants held

```
SMTP_CONNECTIONS = 0          OUTREACH_SEND_COUNT = 0        MATERIALIZED_FSP_PLANNED = 0
SEND_LOG_TOTAL   = 517 (unchanged)                            LAST_SEND_AT = 2026-09-16T01:09:52.031266+08:00
V2_POLICY_CHANGED = false     MX_POLICY_CHANGED = false       SEND_ELIGIBILITY_POLICY_CHANGED = false
No authorization created. No FSP generated. No send.
```

Deferred `access_unreachable` rows were re-verified against the red line:

```
DEFERRED_WITH_EMAIL               = 0    (all 9 keep an empty email)
DEFERRED_MISLABELED_AS_FACTUAL    = 0    (none re-classified as no_public_email or website_not_found)
```

## J. SAFE checkpoint — freshly recomputed, not carried forward

```
READ_ONLY_V2_SAFE_UNIQUE_ORGS = 16     (fresh read-only recompute via the deployed V2+MX path)
MATERIALIZED_FSP_PLANNED      = 0      (reported separately — never conflated with SAFE inventory)
```

SAFE remains 16 (< 40). Per the phase spec this is **not** a software failure: it means production should
continue normal city discovery. The SAFE ceiling is unchanged by this phase — the release unblocked *queue
advancement*, it did not manufacture new eligible organizations.

## K. Safety / operational state summary

```
CODE_CHANGES = 1 file (the authorized release)   DB_MIGRATION = none
SMTP = 0   IMAP = 0   FSP = 0
PreSend/Preflight/Outreach = PAUSED (unchanged)   Recovery = ACTIVE (unchanged)
Inventory = ACTIVE (restored only after both acceptance runs passed)
```

## Provenance

All live figures were read read-only from `roktandrazo-outreach/data/bd_leads.db` on 2026-09-23 (Asia/Shanghai)
during this phase. Codex artefacts were read at commit `641b36b887af596a503dcb8fb518eab66d5ffbb9`.
No number in this report was copied from a previous phase document.
