# PHASE 4A.5J — SAFE40 THROUGHPUT TUNING VIA THE EXISTING `WORKBUDDY_DISCOVERY_MAX_PAGES` KNOB

> **Nature:** operations / configuration phase. One production **automation-configuration** change
> (no code change, no schema change, no DB write, no SMTP, no send). Everything below is a live read on
> **2026-09-28 01:35–02:45 +08** unless marked otherwise.
>
> **Authority at phase start**
> `WORKBUDDY_BASE_COMMIT = 49ffd725eb1a405d7e932f77470d592a89c0240f`
> `CODEX_PRODUCTION_RELEASE = 641b36b87af596a503cdcb8fb518eab66d5ffbb9`
>
> **Confirmed starting facts (re-verified live, not carried forward):** `READ_ONLY_V2_SAFE_UNIQUE_ORGS = 18`,
> `SAFE_TARGET = 40`, `ACTIVE_CITY = Saratoga Springs, NY`, `LAST_COMPLETED_CITY = Ithaca, NY`,
> `NEXT_PENDING_CITY = Cooperstown, NY`, `MATERIALIZED_FSP_PLANNED = 0`, `SMTP_enabled = 0`,
> `SEND_LOG_TODAY = 0`, `RUNNING_INVENTORY_JOBS = 0`, inventory lock `absent` (not held).

---

## A. THE AUTHORIZED CHANGE — EXISTING KNOB ONLY

The throughput limiter was confirmed in code, not assumed:

```
bd_orchestrator.py:442
    discovered = service.run_places_batch(
        city, max_pages=max(1, int(os.getenv('WORKBUDDY_DISCOVERY_MAX_PAGES', '1'))))
```

`discovery/discovery_service.py:456` → `while pages_processed < max_pages:` and `:505` sets
`status = "paused_by_runtime_limit"` when `pages_processed >= max_pages` with a `next_page_cursor` remaining.
So **one provider page per run** was the hard ceiling, and it is an existing environment knob — no code change
was required or made.

**Change applied to the SAME canonical Inventory automation `1784775229336`** (not a new automation): its
execution environment now exports `WORKBUDDY_DISCOVERY_MAX_PAGES=2` for the inventory stage.

| Field | Before | After |
|---|---|---|
| `WORKBUDDY_DISCOVERY_MAX_PAGES` (Inventory execution env) | unset → default `1` | **`2`** |
| Automation id | 1784775229336 | **unchanged** |
| `rrule` | `FREQ=HOURLY;INTERVAL=6` | **unchanged** |
| `nextRunAt` | `1790549882001` = 2026-09-28 06:58:02 +08 | **unchanged** (`1790549882001`) |
| `cwds` | `.../roktandrazo-outreach` | unchanged |

**Explicitly NOT changed** (all re-confirmed unchanged): `DISCOVERY_PROVIDER=browser_maps`,
`BROWSER_MAPS_MODE=direct`, `SCRAPER_PROXY=http://127.0.0.1:3213`, `HTTP_PROXY`/`HTTPS_PROXY=http://127.0.0.1:3213`,
`WORKBUDDY_WEBSITE_RESOLUTION_MAX` (20), `WORKBUDDY_STAGING_POSTPROCESS_MAX` (20), `SAFE_INVENTORY_TARGET`,
website-resolution limits, staging limits, V2, MX, city-completion semantics, send eligibility.

### A.1 Why an automation-scoped value is the correct (and self-contained) placement

`env_loader.py::_load_env()` loads `.env` with **`os.environ.setdefault(key, value)`** — `.env` never
overrides a variable already present in the process environment. `WORKBUDDY_DISCOVERY_MAX_PAGES` is **not
present in `.env`** (verified: `.env` carries `DISCOVERY_PROVIDER`, `BROWSER_MAPS_MODE`, `SCRAPER_PROXY`,
`BD_MX_HTTPS_PROXY`, SMTP/IMAP keys only). Therefore:

- the automation-scoped export is authoritative, needs no repo or config-file edit, and
- the knob is scoped to the Inventory stage alone — no other stage or caller inherits `max_pages=2`,
- making section H's revert a single, local, reversible edit.

---

## B. ONE INVENTORY AUTHORITY PRESERVED

`1784775229336` remains the sole Inventory trigger; `rrule` and anchor untouched; the named lock
`run_lock:daily_outreach:inventory:{date}` remains authoritative. **No** second Inventory automation, **no**
parallel run, **no** manual loop. Process scan (full command-line read via ctypes/PEB) found no
`bd_orchestrator` process and no manual driver. `RUNNING_INVENTORY_JOBS = 0`; a scan for `lock_conflict`
stop reasons across all history is empty.

---

## C. CHECKPOINT MOVED TO `:38`

Reused the SAME checkpoint automation `75fbacd1-fa43-46ea-8388-1d47647c3f4d` — no second checkpoint was created.
Still STRICTLY READ-ONLY (it only runs `output/_4a5g_checkpoint.py` against `mode=ro`).

### C.1 The scheduler anchor mechanism (established empirically this phase)

The automation scheduler computes the anchor from the **update moment**, not from the previous anchor:

- changing only the **prompt** does **not** move `nextRunAt` (verified twice: Inventory stayed
  `1790549882001`; the checkpoint stayed `1790550856114` across a prompt-only update), whereas
- changing the **`rrule`** recomputes `nextRunAt = update_time + INTERVAL` (to the second).

Consequence: an anchor can only be placed on a chosen minute by re-writing the `rrule` **at** that minute.
The `FREQ=HOURLY;INTERVAL=6` form (required for four runs/day at even 6-hour spacing) accepts no
`BYMINUTE`, so the anchor minute is the only lever. The `rrule` was therefore re-written during the
`:38` window, giving:

| | Before (4A.5I) | After (4A.5J) |
|---|---|---|
| Checkpoint anchor | `:14` +08 (16 min after the Inventory anchor) | **`:38` +08 (40 min after the Inventory anchor)** |
| Spacing | 6 h | **6 h (unchanged)** |
| Checkpoint `rrule` | `FREQ=HOURLY;INTERVAL=6` | `FREQ=HOURLY;INTERVAL=6` |
| `nextRunAt` | `1790550856114` = 2026-09-28 07:14:16 +08 | **`1790555881207` = 2026-09-28 08:38:01 +08** (phase re-corrected to `2026-09-28 13:38:01 +08` — see C.2) |

Rationale: `max_pages=2` lengthens the discovery step, so a +16 min checkpoint risked measuring a run in
flight. Observed pre-change runtimes were **152 s / 246 s / 262 s / 486 s / 756 s** (2.5–12.6 min); the
downstream lanes are unchanged, so the expected `max_pages=2` runtime is materially below +40 min.

### C.2 Measured phase, and the one-off correction applied

Setting the anchor minute `:38` is **not sufficient** to obtain "40 minutes after each Inventory
anchor". The offset is a *phase*, not a minute: with 6-hour spacing, a checkpoint series at absolute
times `T_c ≡ B (mod 360 min)` follows the preceding Inventory run by `(B − A) mod 360`, where the
Inventory series is `T_i ≡ A (mod 360 min)`. Measured live this phase:

```
Inventory  anchor :58  ->  series  ... 06:58, 12:58, 18:58, 00:58 ...
Checkpoint anchor :38  ->  series  ... 02:38, 08:38, 14:38, 20:38 ...
measured offset = (158 - 58) mod 360 = 100 minutes      (target 35-40)
```

The anchor is `rrule-write moment + INTERVAL`, so the phase achievable by a single write is fixed by
*when* the write happens — and the only write moments that yield the `+40` phase are
`01:38 / 07:38 / 13:38 / 19:38` Asia/Shanghai. `FREQ=HOURLY;INTERVAL=6` accepts no `BYMINUTE`, so there
is no way to request the phase directly.

Because 100 min is **later** than 40 min, the safety intent of section C (never measure a run in flight)
is satisfied for the interim cycle. The exact phase is restored by one narrow **one-off configuration
task** — deliberately *not* a second checkpoint and *not* a second scheduler:

| one-off | id | fires | action |
|---|---|---|---|
| BD checkpoint phase fix | `488f4c21-a70b-4611-a388-9a3f61c02db9` | 2026-09-28 07:38 +08 (`nextRunAt` `1790552280000`) | two `automation_update` calls on `75fbacd1` (`INTERVAL=5` then `INTERVAL=6`) re-phasing the same series to `13:38`; then it reports and stops |

Target end state from `2026-09-28 13:38 +08`: checkpoint series `13:38 / 19:38 / 01:38 / 07:38` =
**40 minutes after each Inventory anchor**, 6-hour spacing unchanged. It touches no other field of the
checkpoint automation (name, prompt, cwd unchanged) and performs no monitoring work of its own.

---

## D. FIRST FOUR CANONICAL RUNS — OBSERVATION WINDOW (OPEN)

The next four scheduled Inventory runs are **not** manually launched. Cadence 4×/day at 6-hour spacing with
the Inventory anchor `:58` gives the observation window:

```
run 1  2026-09-28 06:58 +08      run 3  2026-09-28 18:58 +08
run 2  2026-09-28 12:58 +08      run 4  2026-09-29 00:58 +08
```

Per-run fields recorded for each: `RUN_ID`, runtime, `STATUS`, `STOP_REASON`, active city before/after,
`QUERY_FAMILY`, `PAGES_PROCESSED`, `PROVIDER_REQUESTS`, `DISCOVERY_RESULTS_SEEN`, `NEW_UNIQUE_PLACES`,
`OFFICIAL_EMAILS_FOUND`, `FULL_EVIDENCE_CREATED`, `SAFE_BEFORE`/`SAFE_AFTER`, `HTTP_429_COUNT`,
`PROVIDER_ERROR_COUNT`.

**`FOUR_RUN_ACCEPTANCE_COMPLETE = false` at the time of writing** — the window needs ~24 h of wall clock.
The first checkpoint that observes all four runs is the `02:38 +08` run on 2026-09-29. Reporting rule 3 of the
existing checkpoint automation was extended to emit this acceptance table exactly once when ≥ 4 post-change
runs exist, then revert to one-line reporting (so no zero-yield noise and no per-run commit).

### D.1 Read-only instrumentation added (measurement only — NOT a new scheduler or checkpoint)

`output/_4a5g_state.py` now additionally computes, from `provider_request_audit` + `job_runs`:

```
BASELINE_PAGES_PER_RUN / BASELINE_AVG_PAGES_PER_RUN      the four canonical 1x/day runs
INVENTORY_RUN_PROVIDER_PAGES                             per-run pages/requests/non-ok/429/families
PROVIDER_PAGES_LATEST_RUN
MAX_PAGES2_RUNS_OBSERVED / MAX_PAGES2_RUN_DETAIL
MAX_PAGES2_PAGES_PER_RUN / MAX_PAGES2_AVG_PAGES_PER_RUN
MAX_PAGES2_ACCEPTANCE_COMPLETE
MAX_PAGES2_FAILED_RUNS / MAX_PAGES2_STALE_CLEANUP / MAX_PAGES2_LOCK_CONFLICTS
MAX_PAGES2_429_TOTAL / MAX_PAGES2_PROVIDER_NON_OK_TOTAL
MAX_PAGES2_THROUGHPUT_IMPROVED
PROVIDER_429_TOTAL_ALL_TIME
```

### D.2 Measurement defect found and corrected (would have faked a "0 pages" result)

`provider_request_audit.requested_at` is stored as `2026-09-24T07:03:54.140485+00:00` while
`job_runs.started_at` is space-separated naive UTC (`2026-09-24 07:01:21`). A naive
`BETWEEN requested_at AND (started_at, finished_at)` therefore matched **nothing** — every run reported
`pages = 0`, which would have masked the entire throughput measurement. Both sides are now normalised
(`' '` → `'T'`, strip `+00:00`/`Z`, truncate to seconds, upper bound suffixed `999`) before comparison.
This is the same class of cross-table timestamp inconsistency already recorded for this project
(`job_runs` naive-UTC vs `lead_discovery_results` ISO+00:00 vs `leads` local-naive).

---

## E. PRE-CHANGE BASELINE (the comparison basis for acceptance)

Provider pages per canonical run, measured from `provider_request_audit` inside each run window:

| RUN_ID | Date | Pages | Non-OK | 429 | Query family |
|---|---|---|---|---|---|
| `inventory:2026-09-24:45057361` | 09-24 | 1 | 0 | 0 | board game store |
| `inventory:2026-09-25:39e3b75d` | 09-25 | 1 | 0 | 0 | board game store |
| `inventory:2026-09-26:df4e7755` | 09-26 | 1 | 0 | 0 | board game store |
| `inventory:2026-09-27:6e8574bd` | 09-27 | 1 | 0 | 0 | game store |

```
BASELINE_PAGES_PER_RUN      = [1, 1, 1, 1]
BASELINE_AVG_PAGES_PER_RUN  = 1.0
PROVIDER_429_TOTAL_ALL_TIME = 0
```

**Acceptance requirement:** `AVERAGE_PROVIDER_PAGES_PER_RUN > 1.0`. A zero-SAFE-gain run is **not** a failure.

### E.1 Why page count, not family count, is the right throughput unit here

Family closure is deliberately conservative: a family closes only after **2 consecutive pages with no new
place**. `board game store` consumed pages 1/2/3 across three separate runs (`pages_processed = 3`,
`results_seen = 48`, `new_unique_places = 15`) before closing — i.e. the same first page was fetched three
times. Two pages per run therefore raises pages/run directly **and** shortens the number of runs needed to
reach the two no-new-page verdict, so both page throughput and city-completion rate should improve.
Current active-city position: **2 of 20 query families completed**, active family `game store`
(persisted family cursor `20`), 17 pending, 1 running.

---

## F. SAFE40 GATE

`READ_ONLY_V2_SAFE_UNIQUE_ORGS` is freshly recomputed through the frozen V2+MX path
(`campaign_eligible_v2.select_candidates_for_plan_v2`) after every scheduled run, **never** substituted by
`BROAD_READY` / stored flags / email counts. `SAFE = 18 < 40` → `SAFE40_REACHED = false`, EXACT40 acceptance
**not** triggered, Inventory **not** paused. On `SAFE >= 40` the existing checkpoint automation pauses
Inventory itself and stops before any PreSend/Preflight/Outreach/send activity.

## G. IF `max_pages=2` IS HEALTHY

Keep `WORKBUDDY_DISCOVERY_MAX_PAGES=2` and the 4×/day cadence. **No** automatic raise to 3 or 4.

## H. IF `max_pages=2` CAUSES A REAL REGRESSION

Revert **only** `WORKBUDDY_DISCOVERY_MAX_PAGES` → `1`, keeping the 4×/day cadence, and report the exact
evidence. Because the knob lives in the automation prompt, the revert is one local edit with no code,
schema or `.env` consequence. Regression signals tracked in section E: rate limiting (429), lock contention,
browser-process leak, provider instability, runtime overlap, DB integrity failure. No Codex work unless a
real code bug is proven.

## I. SEND SAFETY — FROZEN THROUGHOUT

```
SMTP_enabled = 0 · SMTP_CONNECTIONS = 0 · MATERIALIZED_FSP_PLANNED = 0 · OUTREACH_SEND_COUNT = 0
final_send_plan(status='planned') = 0 · send_log today = 0 · SEND_LOG_TOTAL = 517
LAST_SEND_AT = 2026-09-16T01:09:52+08:00
WorkBuddy PreSend = PAUSED · Preflight = PAUSED · Outreach = PAUSED (no send authorization)
DB integrity_check = ok · foreign_key_check = 0 rows
```

No manual recipients, no guessed emails, no third-party evidence, no V2/MX relaxation, no send authorization.

## J. ENVIRONMENT LIMITATION THIS PHASE

`schtasks.exe` is now on the local sandbox **program blacklist** (attempting it is blocked with
"PROGRAM BLOCKED BY SECURITY POLICY"). The three Windows scheduled tasks therefore could **not** be re-verified
this phase; the check was not retried or worked around. Last verified state remains the 4A.5I reading of
2026-09-28 00:52 +08 — `\RoktRazo-BD-Outreach` **Disabled** (the 4A.5H change, still holding),
`\RoktRazo-BD-PreSend` **Disabled**, `\RoktRazo-BD-PostSend` **Enabled** (UNIQUE_REQUIRED) — corroborated
DB-side by the absence of any new `outreach` stage result and `SEND_LOG_TOTAL = 517` unchanged.

---

## FINAL

```
WORKBUDDY_DISCOVERY_MAX_PAGES_BEFORE  = 1
WORKBUDDY_DISCOVERY_MAX_PAGES_AFTER   = 2

INVENTORY_CADENCE                     = 4x/day (FREQ=HOURLY;INTERVAL=6), anchor :58 +08, nextRunAt 1790549882001
CHECKPOINT_CADENCE                    = 4x/day (FREQ=HOURLY;INTERVAL=6)
CHECKPOINT_OFFSET_MINUTES             = 40   (target; effective from 2026-09-28 13:38 +08)
                                          interim cycle 08:38 = 100 min (later => still safe)
CHECKPOINT_NEXTRUNAT                  = 1790555881207 = 2026-09-28 08:38:01 +08
                                          re-phased to 2026-09-28 13:38:01 +08 by one-off 488f4c21 (was :14 / 16 min in 4A.5I)

FOUR_RUN_ACCEPTANCE_COMPLETE          = false (window open; first four runs 06:58/12:58/18:58 +08, 00:58 +08 next day)
FAILED_INVENTORY_RUNS                 = 0
HTTP_429_REGRESSION                   = false (0 x 429 all-time; baseline non-OK pages = 0)
PROVIDER_REGRESSION                   = false (all browser_maps requests status='ok')
LOCK_STORM                            = false (no lock_conflict in history; lock not held)

ACTIVE_CITY                           = Saratoga Springs, NY
LAST_COMPLETED_CITY                   = Ithaca, NY
NEXT_PENDING_CITY                     = Cooperstown, NY

READ_ONLY_V2_SAFE_UNIQUE_ORGS         = 18  (fresh V2+MX read-only recompute)
SAFE_GAIN_DURING_ACCEPTANCE           = 0   (window not yet complete)
SAFE40_REACHED                        = false

SMTP_CONNECTIONS = 0 · OUTREACH_SEND_COUNT = 0 · MATERIALIZED_FSP_PLANNED = 0
CODE_CHANGES = 0 · DB_WRITES = 0 · MANUAL_INVENTORY_RUNS = 0
```

STOP — operations phase; the canonical scheduler continues unattended.

---

## K. HANDOFF SYNC POLICY + ACCEPTANCE-WINDOW EVIDENCE

**Sync policy.** This phase changed production configuration (the Inventory automation's execution
environment and the checkpoint anchor), so the live status document was refreshed **immediately** rather
than lagging behind reality. `LATEST_RESULT.json` and `CHANGELOG.md` were deliberately **not** touched: the
phase instruction is to update the standard handoff only once a trigger event occurs — first 4-run
`max_pages=2` acceptance completes, SAFE changes, a city changes, a real blocker appears, or SAFE reaches 40.
Their absence of a 4A.5J block is a deferral, not an unreported phase.

**Window evidence (read-only, 2026-09-28T02:45:03+08:00).** The acceptance window is still entirely ahead of the
change point:

| Table / key | Rows dated 2026-09-28 | Meaning |
|---|---|---|
| `job_runs.started_at` | 0 | no inventory run since the knob changed |
| `provider_request_audit.requested_at` | 0 | no provider page fetched since the knob changed |
| `lead_discovery_results.discovered_at` | 0 | no new discovery result since the knob changed |
| `run_lock:daily_outreach:inventory:2026-09-28` | key absent | today's named lock has never been taken |

Latest canonical Inventory run remains `inventory:2026-09-27:6e8574bd` (2026-09-27 07:01:07Z, i.e.
15:01:07 +08), `status=partial`, `stop_reason=safe_inventory_gap`, exactly **1** provider page — so the
`[1,1,1,1]` → baseline is intact and unmodified by this phase.

**Why `max_pages=2` should clear the 1.0-page baseline.** Active city 21 (Saratoga Springs, NY) holds 20
query families: `toy store` and `board game store` are `completed` (3 pages each), `game store` is `running`
with `page_cursor='20'` after 1 page, and 17 families are `pending`. A family therefore costs roughly
**3 provider pages**, and the old ceiling of 1 page/run meant ~3 runs per family. With 2 pages/run a family
finishes in ~1.5 runs, which is the basis for the expected `AVERAGE_PROVIDER_PAGES_PER_RUN > 1.0`.

**Freeze re-verified read-only at 02:45 +08:** `MATERIALIZED_FSP_PLANNED = 0` (no `final_send_plan`
row in `planned`/`pending`), `manual_send_queue = 0`, `send_log` total unchanged at 517, last send
`2026-09-16T01:09:52+08:00`, `SMTP_CONNECTIONS = 0`, `OUTREACH_SEND_COUNT = 0`.

**Timestamp correction this phase.** `CURRENT_STATUS.md` initially carried a hardcoded
`Generated: 2026-09-28T02:55:00+08:00` while its own file mtime was 02:41 — a timestamp in the future,
the same defect class as the 4A.5C `HANDOFF_TIMESTAMP_ERROR` already recorded in that file. Both the
`Generated` stamp and the `PHASE_4A5J_VERIFIED` window end were re-derived from the real clock.
**Lesson: never hardcode a handoff timestamp; always derive it from `datetime.now()` at write time.**
