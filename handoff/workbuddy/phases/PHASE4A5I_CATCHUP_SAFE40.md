# PHASE 4A.5I — CATCH-UP AUDIT + ACCELERATED UNATTENDED SAFE40

> Repo: `1569032023yf-star/workbuddy-task-window` (branch `main`) = PRODUCTION SOURCE / PRODUCTION HANDOFF
> Date: 2026-09-28 (Asia/Shanghai) · Author: WorkBuddy operator session
> Last remote handoff before this phase: **`60fe964eb75dca34456471a173737a360ae46c07`** (PHASE 4A.5H, 2026-09-23T17:06 +08)
> Codex production release: **`641b36b87af596a503cdcb8fb518eab66d5ffbb9`** (unchanged — no Codex work this phase)

**Nature:** operations / catch-up audit. Everything below is a **live read** on 2026-09-28 00:49–01:20 +08.
No metric was carried forward from a previous report or from memory.

**One authorized production-state change:** the cadence of the **existing sole** Inventory automation was raised
from one run/day to four runs/day (section D of the instruction). No new scheduler, no second Inventory
authority, no production code change, no DB write, no schema change, no SMTP, no send, no Codex work.

---

## A. CATCH-UP AUDIT SINCE 2026-09-23 17:06 +08

**CATCHUP_PERIOD = 2026-09-23T17:06 +08 → 2026-09-28T01:20 +08** (approx. 4.3 days).

### A.1 Every canonical Inventory run since the 4A.5H checkpoint

| RUN_ID | STARTED (UTC) | STARTED (+08) | ENDED (UTC) | DURATION | STATUS | STOP_REASON | TARGET | ACTUAL (=SAFE after) |
|---|---|---|---|---|---|---|---|---|
| `inventory:2026-09-24:45057361` | 2026-09-24 07:01:21 | 2026-09-24 15:01:21 | 2026-09-24 07:09:27 | 8 m 06 s | partial | `safe_inventory_gap` | 50 | **17** |
| `inventory:2026-09-25:39e3b75d` | 2026-09-25 07:01:11 | 2026-09-25 15:01:11 | 2026-09-25 07:05:17 | 4 m 06 s | partial | `safe_inventory_gap` | 50 | **17** |
| `inventory:2026-09-26:df4e7755` | 2026-09-26 07:00:56 | 2026-09-26 15:00:56 | 2026-09-26 07:05:18 | 4 m 22 s | partial | `safe_inventory_gap` | 60 | **17** |
| `inventory:2026-09-27:6e8574bd` | 2026-09-27 07:01:07 | 2026-09-27 15:01:07 | 2026-09-27 07:13:43 | 12 m 36 s | partial | `safe_inventory_gap` | 60 | **18** |

**INVENTORY_RUNS_SINCE_LAST_REPORT = 4 · FAILED_INVENTORY_RUNS = 0 · STALE_CLEANUP_24H = 0.**
All four fired at 15:00–15:01 +08 from the canonical automation, unattended. `status=partial` +
`stop_reason=safe_inventory_gap` is the **healthy** terminal state (target not met because the V2-safe pool is
below target) — **not** a failure. No `failed` run, no lock storm, no `stale_cleanup` in the period.

Per-run ACTIVE_CITY / QUERY_FAMILY / DISCOVERY_RESULTS_SEEN / NEW_UNIQUE_PLACES / OFFICIAL_EMAILS_FOUND /
FULL_EVIDENCE_CREATED — the per-run discovery deltas are computed from the **provider request audit**, which is
the authoritative per-run record (one row per provider page request):

| RUN (business_date) | ACTIVE_CITY | QUERY_FAMILY | PROVIDER PAGE | CURSOR USED → RETURNED | RESULTS SEEN | NEW_UNIQUE_PLACES | OFFICIAL_EMAILS_FOUND | FULL_EVIDENCE_CREATED | SAFE_AFTER |
|---|---|---|---|---|---|---|---|---|---|
| 2026-09-24 | Saratoga Springs, NY | board game store | 1 | `""` → `16` | 16 | 15 | 1 (`info@saratogacasino.com`) | 4 leads w/ evidence | 17 |
| 2026-09-25 | Saratoga Springs, NY | board game store | 1 (repeat) | `""` → `16` | 16 | 0 (all duplicates) | 0 | 0 | 17 |
| 2026-09-26 | Saratoga Springs, NY | board game store | 1 (repeat) | `""` → `16` | 16 | 0 (all duplicates) | 0 | 0 | 17 |
| 2026-09-27 | Saratoga Springs, NY | game store | 1 | `""` → `20` | 20 | 8 | 1 (`support@tech-monkeys.com`) | 2 leads w/ evidence | 18 |

> "SAFE_AFTER" is the SAFE value at the next read-only checkpoint following the run (the 15:40 +08 checkpoint);
> it is checkpoint-derived, not recomputed against a historical DB snapshot — this is stated explicitly rather
> than presented as a per-run recomputation.

**Leads created in the period (8 total, all Saratoga Springs):**

| lead_id | store_name | email | evidence | collected_at (+08) |
|---|---|---|---|---|
| 1150 | G. Willikers Toys | — | yes | 2026-09-23 12:32 |
| 1151 | Game Grid Saratoga Springs | — | yes | 2026-09-24 15:04 |
| 1153 | Insane Games Wilton Mall | — | yes | 2026-09-24 15:05 |
| **1154** | Saratoga Gaming & Racing | **info@saratogacasino.com** (`official_page_visible`) | yes | 2026-09-24 15:05 |
| 1155 | Northshire Bookstore | — | yes | 2026-09-24 15:06 |
| 1156 | Cooper's Cave Games | — | yes | 2026-09-27 15:06 |
| **1157** | Tech Monkeys | **support@tech-monkeys.com** (`official_page_visible`) | yes | 2026-09-27 15:07 |

Only **2** of 8 new leads carried a first-party visible email → the SAFE gain of **+2**.

### A.2 City movement since Saratoga Springs

**No city movement in the period.** Ithaca remains the last completed city; Saratoga Springs has been the
active city since 2026-09-23T04:31:45 UTC and is **still active**.

| City | Status | Started | Completed |
|---|---|---|---|
| Ithaca, NY (id 20) | `search_matrix_exhausted` | 2026-08-18 | 2026-09-23T04:25:32 UTC |
| **Saratoga Springs, NY (id 21)** | **`active`** | 2026-09-23T04:31:45 UTC | — |
| Cooperstown, NY (id 22) | `pending` | — | — |

Saratoga city-completion checks: **0/9 met**. Query families: **2 completed / 17 pending / 1 running**.

---

## B. FRESH CURRENT STATE (live read-only, 2026-09-28 00:53–01:00 +08)

```
ACTIVE_CITY                        = Saratoga Springs, NY          (id 21, status=active)
LAST_COMPLETED_CITY                = Ithaca, NY                    (search_matrix_exhausted)
NEXT_PENDING_CITY                  = Cooperstown, NY               (15 NY cities pending)

CITY_QUERY_FAMILIES_COMPLETED      = 2   (toy store, board game store)
CITY_QUERY_FAMILIES_PENDING        = 17
CITY_QUERY_FAMILIES_RUNNING        = 1   (game store; page cursor 20)
CITY_QUERY_FAMILIES_FAILED_BLOCKED = 0
CITY_COMPLETION_CHECKS             = 0/9
ACTIVE_CITY_RUNTIME                = 7 provider pages processed; results_seen 71;
                                     new_unique_places 24; duplicate_places 47; provider_errors 0
ACTIVE_CITY_STARTED_AT             = 2026-09-23T04:31:45 UTC
ACTIVE_CITY_LAST_SUCCESS_AT        = 2026-09-27T07:04:42 UTC

READ_ONLY_V2_SAFE_UNIQUE_ORGS      = 18      (fresh V2+MX read-only recompute; V2_SAFE_CANDIDATE_ROWS = 18)
MATERIALIZED_FSP_PLANNED           = 0       (final_send_plan.status='planned')
MATERIALIZED_FSP_ANY_PENDING       = 0
RUNNING_INVENTORY_JOBS             = 0
INVENTORY_LOCK                     = absent for business_date 2026-09-28 (no run yet);
                                     2026-09-27 lock = released @ 07:13:43 UTC
INVENTORY_RUNS_TODAY (UTC)         = 1

SMTP_ENABLED                       = 0
SEND_LOG_TODAY                     = 0
SEND_LOG_TOTAL                     = 517
LAST_SEND_AT                       = 2026-09-16T01:09:52+08:00
MANUAL_SEND_QUEUE                  = 0

Inventory automation (1784775229336) = ACTIVE      (cadence changed this phase — see section D)
Recovery  automation (1786002601925) = ACTIVE
PreSend   automation (1785804406748) = PAUSED
Preflight automation (1785804413719) = PAUSED
Outreach  automation (1785804421539) = PAUSED
Checkpoint automation (75fbacd1)     = ACTIVE      (cadence changed this phase — see section E)

Windows \RoktRazo-BD-PreSend         = Disabled   (untouched)
Windows \RoktRazo-BD-Outreach        = Disabled   (4A.5H disable HELD across 5 days — re-verified)
Windows \RoktRazo-BD-PostSend        = Enabled    (UNIQUE_REQUIRED; last run 2026-09-28 00:10:02, result 0)
BDExecutionHost service              = Stopped
DB integrity_check / quick_check     = ok / ok ; foreign_key_check = 0 issues ; journal_mode = wal
```

**Required invariants: PASS** — `SMTP_ENABLED = 0`, `MATERIALIZED_FSP_PLANNED = 0`,
PreSend/Preflight/Outreach = PAUSED.

### B.1 Authority / no-duplicate evidence

- Full process command-line scan (467 PIDs scanned via ctypes PEB read): **no `bd_orchestrator.py`, no
  Playwright/Chromium BD browser, no manual accumulation driver.** Only this operator session's own processes.
- No Windows Inventory scheduled task exists → `DUPLICATE_INVENTORY_AUTHORITY = false`.
- `DUPLICATE_ACTIVE_SEND_TRIGGER_COUNT = 0` (re-verified: Windows Outreach still Disabled).

### B.2 Provider health — no 429 / no provider regression

`provider_request_audit`, all `browser_maps` requests in the period: **status `ok`, 0 non-ok, 0 zero-result,
0 errors.** No HTTP 429 or rate-limit regression; `ACTIVE_CITY_PROVIDER_ERRORS = 0`.
(Whole-DB distinct statuses: `ok` 114, `configuration_blocked` 34, `no_data_available` 4, `provider_timeout` 2,
`provider_not_configured` 2 — all historical, none in the catch-up period.)

### B.3 Authorization hygiene note (informational, not a send exposure)

`send_authorizations` = 23 rows: **9 consumed / 7 revoked / 7 superseded**. The 7 non-`consumed` rows are all
`superseded` (not "live pending"): every one is long past `expires_at` (2026-07-24 … 2026-09-01, 15-minute
windows), every one has `consumed_at` set, and **0 of their plans has any `planned` FSP** (verified per plan_id).
They are inert and cannot authorise a send. Reported precisely here so the raw count is not mistaken for 7 live
authorizations.

---

## C. IF SAFE ≥ 40 — NOT TRIGGERED

`READ_ONLY_V2_SAFE_UNIQUE_ORGS = 18 < 40` → **EXACT40 NO-SMTP ACCEPTANCE NOT RUN.**
Scheduled Inventory was **not** paused. `SAFE40_REACHED = false`.

---

## D. SAFE < 40 → CADENCE AUDIT AND ACCELERATION (authorized action taken)

### D.1 The six gate conditions of the instruction — all satisfied

| Condition | Live evidence | Verdict |
|---|---|---|
| no concurrent Inventory | `RUNNING_INVENTORY_JOBS = 0`; 467-PID command-line scan found no orchestrator/driver | PASS |
| run lock healthy | 09-24…09-27 locks all `released` at run end; `STALE_CLEANUP_24H = 0`; no lock storm | PASS |
| no stale_cleanup / lock storm | 0 in the period since 2026-09-23 (last storm was 2026-09-21, pre-4A.5G) | PASS |
| typical Inventory runtime < 30 min | 8.1 / 4.1 / 4.4 / 12.6 min — max 12 m 36 s | PASS |
| no HTTP 429 / rate-limit regression | 0 non-ok, 0 provider errors in the period | PASS |
| no BrowserMaps/provider regression | every request `status=ok`; `CITY_PROVIDER_ERRORS = 0` | PASS |
| DB integrity healthy | `integrity_check=ok`, `quick_check=ok`, `foreign_key_check` = 0 | PASS |

### D.2 ACTION TAKEN — same automation, cadence only

```
INVENTORY_CADENCE_BEFORE = 1×/day  at 15:00 +08   (FREQ=DAILY;BYHOUR=15;BYMINUTE=0)
INVENTORY_CADENCE_AFTER  = 4×/day  every 6 hours  (FREQ=HOURLY;INTERVAL=6)
                           next run 2026-09-28 06:58:02 +08; series anchor minute = :58
                           → effective 4 runs/day at 6-hour spacing
```

Automation `1784775229336` was **modified in place** (id unchanged, prompt unchanged, working directory
unchanged). Renamed `RoktRazo BD Inventory — 4x/day (6h interval) Asia/Shanghai` so the schedule label cannot
mislead. **No second Inventory scheduler was created; serial authority and the existing named lock
(`run_lock:daily_outreach:inventory:<business_date>`) are unchanged; nothing was parallelised.**

> **EXPLICIT DEVIATION NOTICE.** The instruction asked for the four runs at **03:00 / 09:00 / 15:00 / 21:00
> Asia/Shanghai**. The automation scheduler available in this environment **rejects multi-value `BYHOUR`**
> (`BYHOUR must be an integer between 0 and 23` on `BYHOUR=3,9,15,21`), and its hourly form explicitly does not
> accept `BYHOUR`/`BYMINUTE`. The faithful supported expression of "four runs per day, six hours apart" is
> `FREQ=HOURLY;INTERVAL=6`. The resulting wall-clock anchor is **:58**, i.e. runs at 00:58 / 06:58 / 12:58 /
> 18:58 +08, **not** the requested 03:00 / 09:00 / 15:00 / 21:00. The **operational intent (4×/day, 6 h apart,
> ≤1 concurrent, same lock) is met**; the exact clock alignment is **not** achievable through this scheduler
> grammar and would require the UI scheduler, which accepts explicit times. Recorded rather than silently
> approximated.

### D.3 Root-cause finding — the real throughput limiter (report only, NOT changed)

The catch-up audit identified why 4 days produced only 2 SAFE orgs. It is **not** run duration and **not** an
error: it is the **per-run discovery page budget**.

`bd_orchestrator.py:442` (deployed, unchanged) calls:

```python
service.run_places_batch(city, max_pages=max(1, int(os.getenv('WORKBUDDY_DISCOVERY_MAX_PAGES', '1'))))
```

`WORKBUDDY_DISCOVERY_MAX_PAGES` is **not set** in the automation environment → default **1 page per run**.
Confirmed empirically: `provider_request_audit` holds **exactly one row per run** for city 21 (7 requests over
7 runs), and `retail_city_queue.pages_processed = 7`.

A second, **by-design** factor compounds it: `discovery_service.py:491-500` documents that *browser-backed
providers can repeat a completed page while returning a non-empty cursor*, so a query family is only closed
after **two consecutive pages with no new place**. Observed rhythm: a family consumes ~3 provider requests
(1 productive + 2 duplicate repetitions) — e.g. `board game store` was requested 3× (09-24/25/26) with the
cursor reset to `""` each time, then completed. Ithaca shows the same pattern at larger scale
(`game store`: `pages_processed = 28`, `consecutive_pages_without_new_place = 27`).

**Quantified consequence:** Saratoga has 20 query families × ~3 requests ≈ **60 provider requests** for the
city. At the previous 1 run/day this was ≈ 60 days per city; at the new 4×/day it is ≈ **15 days per city**.
Period SAFE yield was 2 orgs from 7 requests ≈ **0.29 SAFE/request**, so +22 more SAFE (16→18→40) implies
≈ 76 more requests ≈ **~19 days at the accelerated cadence**, plus the remaining 15 NY cities afterwards.

**This is NOT raised as an engineering blocker.** Per the instruction's blocker definition, none of the listed
conditions is present: rows do transition (families complete, cities advance, cursors persist for the running
family), there is no lock storm, no duplicate authority, no crash, no browser leak, no DB integrity failure,
no V2/MX drift, no provider/network regression. It is a **throughput/capacity observation**, recorded here with
evidence for a **Codex review decision** — because the two levers that would change it
(`WORKBUDDY_DISCOVERY_MAX_PAGES` and the provider repetition/pagination handling) are **discovery-policy
changes and are NOT authorized this phase**. Explicitly NOT changed.

---

## E. CHECKPOINT CADENCE

The **existing** read-only checkpoint automation `75fbacd1-fa43-46ea-8388-1d47647c3f4d` was reused — **no second
checkpoint mechanism was created**. It was moved onto the same 6-hourly interval so it still lands **after** each
inventory run — **anchor minute :14 +08, i.e. 16 minutes after the Inventory anchor** (next checkpoint run 2026-09-28 07:14:16 +08; the offset exceeds the observed 4–13 min Inventory runtime, so the checkpoint measures post-run state).

`CHECKPOINT_CADENCE_AFTER = 4×/day, FREQ=HOURLY;INTERVAL=6` — **anchor :14 +08 (+16 min after the Inventory anchor; next run 2026-09-28 07:14:16 +08)** (was 1×/day at 15:40 +08).
It remains **STRICTLY READ-ONLY**: never launches Inventory, never writes the DB, never creates FSP, never sends.

- Escalation triggers are unchanged: **SAFE changed · active city changed · completed city changed · SAFE ≥ 40 ·
  real engineering blocker · send-freeze violation.**
- Zero-yield runs remain **non-reporting** (one compact line only). No git commit is produced for a zero-yield
  run.
- One threshold was adjusted to match the authorised cadence: the duplicate-authority warning in
  `output/_4a5g_checkpoint.py` fired above **4** runs/UTC-day; with 4 runs/day now legitimate it was raised to
  **6** (tolerance band). Without this, a normal day would have falsely warned about a duplicate Inventory
  authority.
- The read-only measurement (`output/_4a5g_state.py`) was extended to record active-city query-family progress
  (families completed/pending/running, pages processed, provider requests last 24 h) so future checkpoints carry
  the throughput evidence needed to judge section D. Read-only; no new report trigger added.

Checkpoint proofs of unattended operation: it fired **by itself** on 2026-09-23 15:40:52, 09-24 15:40:55,
09-25 15:40:31, 09-26 15:41:00, 09-27 15:40:36 (+08) — 5 consecutive unattended firings.
Last checkpoint (2026-09-27 15:40:36 +08): `SAFE=18`, `MILESTONES=[SAFE_CHANGED: 17→18,
SAFE_NEW_ORGS(1): org:domain:tech-monkeys.com]`, `BLOCKERS=[]`, `WARNINGS=[]`.

---

## F. ENGINEERING BLOCKER DEFINITION — APPLIED

`REAL_ENGINEERING_BLOCKER = none.` Each condition checked explicitly against live evidence:

| Blocker condition | Result |
|---|---|
| identical rows repeatedly reselected with **no transition** | **No** — repetitions transition: families close (`toy store` 09-23, `board game store` 09-26) and the running family's cursor persists (`game store` → 20) |
| city cannot progress despite legitimate work being drained | **No** — Saratoga advanced 0→2 completed families; Ithaca already reached `search_matrix_exhausted` |
| Inventory lock storm | **No** — 0 stale_cleanup, locks released each run |
| duplicate Inventory authority | **No** — no Windows Inventory task; `BDExecutionHost` Stopped |
| uncaught crash / exception | **No** — 0 `failed` runs; latest error field empty |
| browser-process leak | **No** — 467-PID scan found no BD browser process |
| DB integrity failure | **No** — `integrity_check=ok`, `foreign_key_check`=0 |
| V2/MX policy drift | **No** — no production file written; core still byte-identical to Codex `641b36b8` |
| generalised provider/network regression | **No** — all requests `status=ok` |

**Zero SAFE gain by itself was not treated as a bug.** No redesign was performed.

---

## G. EXISTING AUTOMATIC LANES — AUTHORIZED AND CONTINUING

Unchanged and still authorized for unattended operation: BrowserMaps discovery · official website resolution ·
existing first-party enrichment · visible official email extraction · generic inbox routing · evidence creation ·
V2/MX recomputation · city completion · city advancement.
**No** new provider, **no** new schema, **no** new enrichment lane, **no** V2/MX relaxation.

---

## H. SAFETY

```
SMTP_CONNECTIONS          = 0
OUTREACH_SEND_COUNT       = 0
MATERIALIZED_FSP_PLANNED  = 0
PreSend / Preflight / Outreach = PAUSED / PAUSED / PAUSED
```
No guessed email. No third-party evidence. No manual recipient. No send. No 1-email canary.
No manual Inventory run (`INVENTORY_RUNS_MANUAL = 0`).

**Changes made this phase — complete list:**

| # | Change | Class |
|---|---|---|
| 1 | Inventory automation `1784775229336`: cadence 1×/day → 4×/day (`FREQ=HOURLY;INTERVAL=6`) + name updated | scheduler config (authorized) |
| 2 | Checkpoint automation `75fbacd1`: cadence 1×/day 15:40 → 4×/day same 6-hourly interval | scheduler config (authorized) |
| 3 | `output/_4a5g_checkpoint.py`: duplicate-authority warning threshold 4 → 6 runs/UTC-day | read-only local tool |
| 4 | `output/_4a5g_state.py`: added active-city query-family / provider-request metrics | read-only local tool |
| 5 | Handoff documents (this report + CURRENT_STATUS + LATEST_RESULT + CHANGELOG) | documentation |

**Not changed:** production code (`CODE_CHANGES = 0`) · database (`DB_WRITES = 0`) · schema
(`DATABASE_SCHEMA_CHANGED = false`) · V2/MX/hygiene policy · Windows scheduled tasks (all three untouched) ·
PreSend/Preflight/Outreach states · `WORKBUDDY_DISCOVERY_MAX_PAGES` · Codex `641b36b8`.

---

## I. FINAL

```
LAST_REMOTE_HANDOFF              = 60fe964eb75dca34456471a173737a360ae46c07
CATCHUP_PERIOD                   = 2026-09-23T17:06 +08 → 2026-09-28T01:20 +08

INVENTORY_RUNS_SINCE_LAST_REPORT = 4   (2026-09-24, 09-25, 09-26, 09-27 — all 15:00 +08, all unattended)
FAILED_INVENTORY_RUNS            = 0
REAL_ENGINEERING_BLOCKER         = none

ACTIVE_CITY                      = Saratoga Springs, NY
LAST_COMPLETED_CITY              = Ithaca, NY
NEXT_PENDING_CITY                = Cooperstown, NY

READ_ONLY_V2_SAFE_UNIQUE_ORGS    = 18      (fresh read-only V2+MX recompute)
SAFE_GAIN_SINCE_4A5H             = +2      (16 -> 17 on 2026-09-24; 17 -> 18 on 2026-09-27)

MATERIALIZED_FSP_PLANNED         = 0
SAFE40_REACHED                   = false

INVENTORY_CADENCE_BEFORE         = 1x/day at 15:00 +08
INVENTORY_CADENCE_AFTER          = 4x/day, FREQ=HOURLY;INTERVAL=6  (anchor :58 +08; see DEVIATION NOTICE)

CHECKPOINT_CADENCE_AFTER         = 4x/day, FREQ=HOURLY;INTERVAL=6  (anchor :14 +08 = +16 min after the
                                   Inventory anchor; next run 2026-09-28 07:14:16 +08)

EXACT40_ACCEPTANCE_RUN           = false
EXACT40_ACCEPTANCE_RESULT        = NOT_RUN  (SAFE < 40)

SMTP_CONNECTIONS                 = 0
OUTREACH_SEND_COUNT              = 0
CODE_CHANGES                     = 0
DB_WRITES                        = 0
INVENTORY_RUNS_MANUAL            = 0

NEXT_ACTION                      = CONTINUE_UNATTENDED_ACCUMULATION
                                   (sole Inventory automation now running 4x/day; leave it running; do NOT
                                   start a manual loop; do NOT send. Report on SAFE >= 40 for separate
                                   EXACT40 NO-SMTP acceptance authorisation.)
```
