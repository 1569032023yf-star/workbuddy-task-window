# PHASE 4A.5C — FINISH ITHACA + ADVANCE CITY + BUILD SAFE40

**Status: STOPPED on a genuine software regression (Section F condition 3).**
City queue advancement is **structurally blocked**, not merely slow.

- Production authority (local = remote): `2ebc05f318d55a635e961339b2df6c9e8c716198`
- Codex `07784044` already deployed (bd_orchestrator `7afc4d7f…`, retail_city_queue `46d6f452…`)
- SAFE before: **15** → SAFE after: **16**
- **No SMTP. No send. No FSP. No authorization. No V2/MX/template/sender/city-policy change. No code change.**

---

## A. SINGLE INVENTORY AUTHORITY

| Requirement | Value |
|---|---|
| `RUNNING_INVENTORY_JOBS` before launch | **0** |
| Held inventory lock before launch | **released** |
| Live inventory processes before launch | **0** |
| New scheduler created | **No** |
| Scheduled Inventory `automation-1784775229336` | **PAUSED** during the manual window (restored ACTIVE at hand-off — see §G) |
| Recovery Sync `automation-1786002601925` | ACTIVE (untouched) |
| Pre-Send `1785804406748` / Preflight `1785804413719` / Outreach `1785804421539` | **PAUSED** (unchanged, verified live) |
| Duplicate active inventory triggers | 0 (single canonical entry point `bd_orchestrator.py --stage inventory --live`) |

Note: one **read-only** python process (an in-flight SAFE recount importing
`campaign_eligible_v2.select_candidates_for_plan_v2`) was observed at preflight. It is not an
inventory run, holds no run-lock, and writes nothing. It was left alone.

## B. THROUGHPUT KNOB (existing production configuration only)

All four knobs were verified to exist in production code before use; no code was modified.

| Env | Production default | Used here | Source |
|---|---|---|---|
| `DISCOVERY_PROVIDER` | — | `browser_maps` | task spec |
| `BROWSER_MAPS_MODE` | `file` | `direct` | `discovery/providers/browser_maps.py:224` |
| `SCRAPER_PROXY` / `HTTP_PROXY` / `HTTPS_PROXY` | — | `http://127.0.0.1:3213` | task spec |
| `SAFE_INVENTORY_TARGET` | `30` | `50` | `outreach_control.py:30` |
| `WORKBUDDY_DISCOVERY_MAX_PAGES` | `1` | **`2`** | `bd_orchestrator.py:442` |
| `WORKBUDDY_WEBSITE_RESOLUTION_MAX` | `20` | `20` (unchanged) | `bd_orchestrator.py:446` |
| `WORKBUDDY_STAGING_POSTPROCESS_MAX` | `20` | `20` (unchanged) | `bd_orchestrator.py:450` |

Semantics verified in code: `max_pages` advances **the single active query family** by up to N
result pages per canonical run (`run_places_batch`, `discovery_service.py:243-276`). It is not a
multi-city or multi-family knob.

## C. FINISH ITHACA — ACHIEVED

Strictly serial canonical runs (never concurrent), each preceded by an `ACTIVE_CITY` /
`BROWSERMAPS_*` / `SAFE` status print.

### C.1 Query-family completion

`Ithaca (active_city_id=20, provider=browser_maps)`:

| Metric | Start | End |
|---|---|---|
| TOTAL | 20 | 20 |
| COMPLETED | 15 | **20** |
| PENDING | 4 | **0** |
| RUNNING | 1 | **0** |
| FAILED / BLOCKED | 0 | 0 |

The two highest-product-fit families both completed durably during the window:
`puzzle store` (id 479) and `card game store` (id 480), together with
`tourist gift shop` (477), `specialty retailer` (478) and the resumed
`visitor center gift shop` (476). **No query row was manually marked complete.**

### C.2 Per-round measurements

| R | City | NEW_UNIQUE_PLACES | WEBSITES_RESOLVED | STAGING_PROCESSED | OFFICIAL_EMAILS_FOUND | FULL_EVIDENCE_CREATED | SAFE_AFTER | BM completed | sends | FSP |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Ithaca, NY | 0 | 5 | 5 | 0 | 0 | 16 | 16/20 | 0 | 0 |
| 2 | Ithaca, NY | 0 | 5 | 5 | 0 | 0 | 16 | 17/20 | 0 | 0 |
| 3 | Ithaca, NY | 8 | 8 | 12 | 0 | 4 | 16 | 17/20 | 0 | 0 |
| 4 | Ithaca, NY | 0 | 8 | 8 | 0 | 0 | 16 | 18/20 | 0 | 0 |
| 5 | Ithaca, NY | 0 | 8 | 8 | 0 | 0 | 16 | 19/20 | 0 | 0 |
| 6 | Ithaca, NY | 0 | 8 | 8 | 0 | 0 | 16 | 20/20 | 0 | 0 |
| 7 | Ithaca, NY | 0 | 8 | 8 | 0 | 0 | 16 | 20/20 | 0 | 0 |
| 8 | Ithaca, NY | 0 | 8 | 8 | 0 | 0 | 16 | 20/20 | 0 | 0 |

8 canonical rounds completed, total wall time 4682 s (~78 min). A 9th round was launched by the
serial driver and then abandoned when the driver was stopped; its job row was closed with the
**existing** `stale_cleanup` semantics and its run-lock released (see §F.1).

All runs: `exit=0`, `status=partial`, `stop_reason=safe_inventory_gap`.
**No round was aborted for a zero-SAFE round** (per instruction). `NEW_UNIQUE_PLACES` total = 8.

Two facts stand out:

1. Round 3 produced **8 new unique places and 4 new full-evidence records but zero SAFE gain** —
   the new merchants yielded no first-party email.
2. From round 4 onward `WEBSITES_RESOLVED=8` and `STAGING_PROCESSED=8` **every single round**
   with **zero** conversions — and rounds 7-8 still report 8/8 even after the query matrix had
   fully completed and discovery returned nothing (`DISCOVERY_RESULTS_SEEN=0`). The lanes are
   re-selecting the same rows and producing no state change. That is the signature of the defect
   proven in §D.

## D. CITY ADVANCEMENT — BLOCKED BY A SOFTWARE REGRESSION (root cause proven)

### D.1 The gate

Deployed `city_completion_checks(20, "browser_maps")` returns 9 booleans. Nine-of-nine is
required before `complete_if_exhausted` writes `status='search_matrix_exhausted'`.

| Check | Value |
|---|---|
| `all_query_families` | **True** |
| `all_sources_or_reasons` | **True** |
| `pagination_complete` | **True** |
| `two_empty_pages` | **True** |
| `last_three_batches_empty` | **True** |
| `all_candidates_classified` | **False** |
| `no_unprocessed_candidates` | **False** |
| `official_site_recheck` | **False** |
| `review_recovery` | **False** |
| `ALL_MET` | **False** |

The four failing keys are all the *same* predicate: `no_open_work`
(`retail_city_queue.py:186-196`), defined as
`not (staged_pending or retryable_network or retryable_manual or linked_retry)`.

Live composition of that predicate for Ithaca:

| Term | Count | Drainable by canonical lanes? |
|---|---|---|
| `staged_pending` (`website_lookup_pending` etc.) | **8** | **No — see D.2** |
| `retryable_network` (`website_resolution:network_retry:`) | **1** | **No — see D.3** |
| `retryable_manual` | 1 | No (same row as linked) |
| `linked_retry` | 12 | No — re-processed every round, 0 conversions |

`OPEN_WORK = True` ⇒ `no_open_work = False` ⇒ `complete_if_exhausted` never fires ⇒
`ITHACA_STATUS` never becomes `search_matrix_exhausted` ⇒ `activate_next_city` never reaches
Saratoga Springs.

### D.2 Defect 1 — `website_lookup_pending` rows have no terminal write (liveness bug)

Two canonical lanes touch these rows and **neither can ever close them**:

`discovery/discovery_service.py:412-416` — `run_website_resolution`, failure branch:

```sql
UPDATE lead_discovery_results SET rejection_reason=?, last_seen_at=? WHERE id=?
```

It writes only `rejection_reason` and **never changes `validation_status`**, so a failed row stays
`website_lookup_pending` forever.

`discovery/discovery_service.py:768-770` — `_postprocess_staged_result`, empty-website branch:

```python
website = str(row.get("website") or "").strip()
if not website:
    return "website_lookup_pending", None      # no write at all
```

It returns without writing anything.

Meanwhile both selectors re-select the same rows every run
(`run_website_resolution` selects `website='' AND validation_status IN
('website_lookup_pending','manual_review_needed') ORDER BY discovered_at,id LIMIT 20`;
`run_staging_postprocess` selects `validation_status IN STAGING_POSTPROCESS_STATUSES …
LIMIT 20`). With only 8 such rows and a limit of 20, **all 8 are re-selected on every run, fail the
same way, and stay pending.** Observed live: `STAGING_PROCESSED=8` / `WEBSITES_RESOLVED=8` in
rounds 4, 5, 6 and 7 with 0 status transitions.

Current pending set (all `last_seen_at ≈ 2026-09-21T08:21`, i.e. re-touched in round 6):

| id | rejection_reason |
|---|---|
| 337, 349, 360, 368, 406, 409, 412 | `website_resolution:not_found:` |
| 374 | `website_resolution:network_retry:OSError:[Errno 22] …` |

**Consequence:** the 4A.7 fail-closed contract is *fail-closed correct* but **not live**. A city
whose query matrix is fully exhausted can never satisfy `no_open_work`, so the queue deadlocks at
the first city that produces any unresolvable website lookup. This is a genuine software
regression, and it is the sole blocker for §D and §E.

### D.3 Defect 2 — scraped private-use glyphs + embedded newlines poison the cache filename

Row `id=374` ("Comics For Collectors", `comic book store Ithaca NY`) was stored with raw Google
Maps label glyphs in structured columns:

```
formatted_address = "\ue0c8\n124 W State St, Ithaca, NY 14850, United States"
phone             = "\ue0b0\n+1 607-272-3007"
```

`U+E0C8` / `U+E0B0` are Material-Icons private-use codepoints; `\n` is a literal newline. The
website resolver builds a `browser_maps_cache` **filename** from
`business_name + formatted_address + phone`, producing an illegal Windows path:

```
OSError: [Errno 22] Invalid argument:
'…\data\browser_maps_cache\comics_for_collectors_\ue0c8\n124_w_state_st,_ithaca,_ny_14850,_united_states_\ue0b0\n+1_607-272-3007_ithaca_ny_.json'
```

The cache directory holds 42 files, **none** with private-use/control characters — the write never
succeeds. The row is re-attempted every round and fails identically
(`rejection_reason` unchanged, `last_seen_at` advanced each round), so
`retryable_network` is permanently true. This is unsanitised scraper output, i.e. a data-hygiene
defect at the `browser_maps` ingestion boundary, and it independently guarantees that
`no_open_work` can never become true.

### D.4 Verdict

```
ITHACA_STATUS                     = active            (NOT search_matrix_exhausted)
CITY_QUEUE_ADVANCEMENT_VERIFIED   = false
NEXT_CITY_ACTIVATED               = none
CITIES_PROCESSED                  = 1 (Ithaca NY only)
CITY_QUEUE_ADVANCEMENT_BLOCKED_BY = software regression (D.2 liveness + D.3 hygiene)
```

Section D instructed: *"If all legitimate completion conditions pass but the city does not
advance: STOP and report a software regression."* Here the query-matrix conditions **do** pass
(5/9, all matrix-related) and the city does not advance. The four remaining conditions are not
merely unmet — they are **unsatisfiable by the deployed canonical lanes**.

## E. CONTINUE SAFE BUILD IN NEW CITY — NOT REACHED

Saratoga Springs, NY (queue id 21) was never activated. No non-Ithaca discovery was performed; no
NY city beyond Ithaca was processed. Continuing was pointless: Ithaca's query matrix was exhausted
(`NEW_UNIQUE_PLACES=0` in rounds 2, 4-7), the city could not be closed, and the next city could
not be reached.

## F. STOP CONDITIONS

| # | Condition | Triggered |
|---|---|---|
| 1 | SAFE ≥ 40 | No (16) |
| 2 | six-hour manual runtime | No (~1h 12m) |
| 3 | **genuine software regression** | **YES — STOP** |
| 4 | 3 consecutive canonical crashes | No (0 crashes; all 7 runs exit 0) |
| 5 | provider unavailable persistently | No (provider returned results every round) |

`STOP_REASON = software_regression:city_queue_deadlock (D.2 no_terminal_write_for_website_lookup_pending + D.3 unsanitised_cache_filename)`

The SAFE acceptance watermark was **not** lowered.

### F.1 Clean-stop proof

| Item | Value |
|---|---|
| `RUNNING_INVENTORY_JOBS` after stop | **0** |
| `INVENTORY_LOCK` after stop | **released** |
| Abandoned run | `inventory:2026-09-21:7e871faa` → `status=failed`, `stop_reason=stale_cleanup` (existing semantics) |
| Send-log rows added | **0** |
| `MATERIALIZED_FSP_PLANNED` | **0** |
| Production code changed | **0 files** |

## G. WHEN SAFE ≥ 40 — N/A; STANDING STATE RESTORED

SAFE = 16 < 40, so no 40-recipient release was prepared: no FSP, no authorization, no SMTP.

Scheduled Inventory `automation-1784775229336` was **restored to ACTIVE** (its standing
configuration before this phase) because the manual window ended without reaching the target.
It will keep hitting the same deadlocked completion gate until Defect D.2 is fixed, at which point
the queue will advance to Saratoga Springs on the next canonical run.

Pre-Send / Preflight / Outreach remain **PAUSED**.

## H. SAFETY

| Invariant | Value |
|---|---|
| `SMTP_CONNECTIONS` | **0** |
| `OUTREACH_SEND_COUNT` (today) | **0** |
| `MATERIALIZED_FSP_PLANNED` | **0** |
| Guessed emails promoted | 0 |
| Third-party email evidence used | 0 |
| V2 relaxed | No |
| MX relaxed | No |
| Manual recipient creation | None |
| Production code changed | **0 files** |
| Frozen-chain files changed | **0** |
| DB schema changed | No |

## I. HAND-OFF

Deliverables: this report + `CURRENT_STATUS.md` / `LATEST_RESULT.json` / `CHANGELOG.md` updates,
committed to `1569032023yf-star/workbuddy-task-window@main`.

### I.1 Required Codex fix (narrow, two hunks, no policy change)

1. **Liveness (D.2)** — give the website-resolution lane a durable terminal outcome for the
   "no official website found" and "network" failures, so `website_lookup_pending` can actually
   drain. Minimum surface: `discovery/discovery_service.py::run_website_resolution` (failure
   branch) and/or `_postprocess_staged_result` (empty-website branch), plus whatever
   `STAGING_POSTPROCESS_STATUSES`/`validation_status` value the repo already uses for
   `website_not_found` (the value exists in the DB — 11 Ithaca rows carry it). Do **not** remove
   the fail-closed gate; make it satisfiable.
2. **Hygiene (D.3)** — sanitise scraped `business_name` / `formatted_address` / `phone`
   (strip C0/C1 control characters, private-use codepoints above U+E000, and collapse newlines)
   before they are used in `browser_maps_cache` filenames and before they are persisted.
   Existing row `id=374` in city 20 also carries the poisoned values.

### I.2 Final metrics

All values below are read **live** from `roktandrazo-outreach/data/bd_leads.db` at the end of this
phase. SAFE was recomputed through the deployed production selector
`campaign_eligible_v2.select_candidates_for_plan_v2` plus the deployed V2+MX gate, with
`preflight_gate.query_mx` wrapped in a pure in-process `domain → status` cache (semantics
unchanged; verified to reproduce the orchestrator's own live count exactly). MX domains swept: 105,
1m34s.

```
SAFE_BEFORE                       = 15
SAFE_AFTER                        = 16        (orchestrator live count and independent recount agree)

ITHACA_BROWSERMAPS_TOTAL          = 20
ITHACA_BROWSERMAPS_COMPLETED      = 20
ITHACA_BROWSERMAPS_PENDING        = 0
ITHACA_BROWSERMAPS_RUNNING        = 0

ITHACA_STATUS                     = active    (NOT search_matrix_exhausted)
CITY_COMPLETION_CHECKS_PASSED     = 5 / 9     (ALL_MET = false)
OPEN_STAGED_PENDING               = 8
OPEN_RETRYABLE_NETWORK            = 1
NEXT_CITY_ACTIVATED               = none      (Saratoga Springs NY, queue id 21, still pending)
CITY_QUEUE_ADVANCEMENT_VERIFIED   = false
CITIES_PROCESSED                  = 1 (Ithaca NY)

NEW_UNIQUE_PLACES                 = 8         (all in round 3)
OFFICIAL_EMAILS_FOUND             = 0
FULL_EVIDENCE_CREATED             = 4         (round 3)
EMAIL_PRESENT                     = 604       (unchanged)
FIRST_PARTY_OFFICIAL_EMAILS       = 340
FULL_EVIDENCE_RECORDS             = 461
LEADS_TOTAL                       = 1114
DISCOVERY_ROWS                    = 412

CANONICAL_ROUNDS_COMPLETED        = 8         (all exit=0, status=partial, safe_inventory_gap)
TOTAL_WALL_TIME                   = 4682 s (~78 min)
DISCOVERY_MAX_PAGES               = 2

INVENTORY_AUTOMATION_RESTORED     = true      (automation-1784775229336 ACTIVE)
PRESEND_PAUSED                    = true
PREFLIGHT_PAUSED                  = true
OUTREACH_PAUSED                   = true

SMTP_CONNECTIONS                  = 0
OUTREACH_SEND_COUNT               = 0         (today 0; last send 2026-09-16T01:09:52+08:00)
MATERIALIZED_FSP_PLANNED          = 0
RUNNING_INVENTORY_JOBS            = 0
INVENTORY_LOCK                    = released

READY_FOR_40_RECIPIENT_ACCEPTANCE = false

STOP_REASON = software_regression:city_queue_deadlock
              (D.2 website_lookup_pending has no terminal write
             + D.3 unsanitised scraped cache filename)
COMMIT_SHA  = bf8497ea113391601d57f75aeb09293041159fa6
PUSH_SUCCESS = true   (2ebc05f..bf8497e main -> main; remote re-verified via GitHub API)
```

### I.3 What the next phase must do

The SAFE watermark (40) must **not** be lowered and the fail-closed gate must **not** be removed.
The productive next actions, in order:

1. Codex fixes D.2 (make `no_open_work` satisfiable) — without this, **every** city in the queue
   will deadlock exactly like Ithaca, and no amount of discovery volume will ever move SAFE via a
   new city.
2. Codex fixes D.3 (sanitise scraped values) and cleans the poisoned row `id=374`.
3. Re-run one canonical Inventory to observe `ITHACA_STATUS = search_matrix_exhausted` and
   `ACTIVE_CITY = Saratoga Springs, NY`, i.e. `CITY_QUEUE_ADVANCEMENT_VERIFIED = true`.
4. Only then resume SAFE accumulation toward 40 in Saratoga Springs / the rest of the NY queue.
