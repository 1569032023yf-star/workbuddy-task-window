# PHASE 4A.5A — DEPLOY CODEX `07784044` + SERIAL MANUAL SAFE ACCUMULATION

- **Authority repo:** `1569032023yf-star/workbuddy-task-window` @ `main`
- **Production HEAD before this phase:** `62f5f04`
- **Codex dev HEAD deployed:** `07784044` ("Finalize city exhaustion semantics", 2026-09-20T17:24:52Z)
- **Window:** 2026-09-21 08:44–09:35 Asia/Shanghai (2026-09-21 00:44–01:35 UTC)
- **Operator instruction executed:** deploy `07784044` → pause scheduled Inventory → run Inventory serially →
  stop when SAFE reaches 40 → restore scheduled Inventory → keep the three send stages paused.

---

## A. DEPLOYMENT OF CODEX `07784044`

`07784044` is **3 commits ahead** of the code that was live in production (`cbb8fa3e` = 4A.6):
`74f50852` (4A.7 fail-closed city queue advancement) → `4a63d1a4` (completion-semantics audit) →
`07784044` (finalize city exhaustion semantics).

Only **two production code files** differ (plus one new test file):

| File | Change | Before (SHA256 / bytes) | After (SHA256 / bytes) |
|---|---|---|---|
| `bd_orchestrator.py` | +8 / −2 | `252ed6042b04837f` / 30,139 | **`7afc4d7f6ac18e22`** / 30,645 |
| `retail_city_queue.py` | +157 / −3 | `95fa135feac19e39` / 7,466 | **`46d6f4521892785e`** / 15,039 |
| `tests/test_phase4a7_city_queue_advancement.py` | new | — | 9,000 bytes |

Both files were re-fetched after writing and re-hashed: **local == remote, byte-identical**.
Pre-deployment copies were backed up to `output/backup_pre_07784044/`.

### A.1 What the patch changes (verified by reading the diff, not assumed)

- `bd_orchestrator.py` — inside `stage_inventory` only:
  - imports and calls `complete_active_city_if_exhausted(...)` **before** activating a city, and again
    **after** the linked-backlog pass (so a city can be closed in the same run that drains its last item).
  - **No change to any send path.** No SMTP, FSP, authorization, template, V2 or MX code touched.
- `retail_city_queue.py` — adds `city_completion_checks()` plus two conservative helpers:
  - `places_matrix_completed_web_pending` is treated as a **holding state, not proof of remaining work**;
  - a city becomes terminal only when every fail-closed check passes (queries complete + cursors empty,
    web-directory reason terminal, and **no** staged-pending / retryable-network / retryable-manual /
    linked-backlog-retry rows);
  - `complete_if_exhausted()` now returns `cursor.rowcount == 1` instead of `total_changes > 0`.
  - The helpers perform **no lead or evidence mutation** and no network calls.

### A.2 Validation

| Check | Result |
|---|---|
| Targeted test `tests/test_phase4a7_city_queue_advancement.py` (copied from Codex) | **10 passed / 0 failed** |
| Full suite after deploy | **36 failed / 275 passed / 5 errors** |
| Full-suite failure set vs. pre-deploy baseline | **IDENTICAL — NEW REGRESSIONS = 0** (passed rose 255 → 275 from the two new test files) |
| Comparison method | FAILED-line set diff against `full_suite_after.txt` (the 4A.5+4A.6 baseline) |

The 36 pre-existing failures are the known clock/timezone/network-dependent ones
(recipient_scheduler, dashboard_timezone, p0_runtime, discovery_service, preflight_gate live-MX, …).

---

## B. SCHEDULER HANDLING

| Step | Action | Verified |
|---|---|---|
| 1 | Paused `automation-1784775229336` (RoktRazo BD Inventory, daily 15:00 +08) | status = **PAUSED** |
| 2 | Ran Inventory **serially** (one subprocess at a time, 20s gap, overlap check before every round) | 6 rounds, no overlap |
| 3 | Restored `automation-1784775229336` | status = **ACTIVE**, next run 15:00 +08 |

**Send stages untouched and still paused throughout:** Pre-Send `1785804406748`, Preflight `1785804413719`,
Outreach `1785804421539` — all **PAUSED**. Recovery Sync `1786002601925` remains ACTIVE (support job, it does
not launch inventory).

---

## C. SERIAL ACCUMULATION — 6 ROUNDS

Driver: `_4a5a_accumulate.py` — strictly sequential, refuses to start if any inventory row is `running`,
20s inter-round gap, fail-closed on `lock_conflict`, on an unexpected `stop_reason`, or on a non-zero exit.

| # | run_id | status | SAFE (target 50) | stop_reason | exit | duration |
|---|---|---|---|---|---|---|
| 1 | `inventory:2026-09-21:c3260be1` | partial | 11 | `safe_inventory_gap` | 0 | 6m29s |
| 2 | `inventory:2026-09-21:5de10633` | partial | 11 | `safe_inventory_gap` | 0 | 6m05s |
| 3 | `inventory:2026-09-21:64a414e8` | partial | 11 | `safe_inventory_gap` | 0 | 7m33s |
| 4 | `inventory:2026-09-21:e8ae46db` | partial | 11 | `safe_inventory_gap` | 0 | 5m57s |
| 5 | `inventory:2026-09-21:57b95d10` | partial | 11 | `safe_inventory_gap` | 0 | 5m53s |
| 6 | `inventory:2026-09-21:f76835e9` | partial | **13** | `safe_inventory_gap` | 0 | 8m06s |

**Result: SAFE 10 → 13. The target of 40 was NOT reached.**

### C.1 Yield of the 6 rounds

| Metric | Before | After |
|---|---|---|
| `READ_ONLY_V2_SAFE_UNIQUE_ORGS` | 10 | **13** |
| `LEADS` | 1,096 | **1,104** |
| `EVIDENCE_URL` non-empty | 871 | **879** |
| `lead_discovery_results` | 385 | **395** |
| `BROAD_READY` (live) | 43 | 44+ |
| `MATERIALIZED_FSP_PLANNED` | 0 | **0** |
| sends in last 24h | 0 | **0** (last `send_log` row still 2026-09-16T01:09:52+08) |

### C.2 Why it stopped at 13 (and not at 40)

After rounds 2–5 produced **four consecutive zero-growth rounds**, the driver was stopped during the
inter-round sleep window (no subprocess was killed mid-run; `RUNNING_INVENTORY_JOBS = 0`,
`HELD_INVENTORY_LOCKS = 0` verified afterwards). Round 6 landed **+2** just before the stop landed, so the
final measured value is **13**.

Measured economics: **~0.5 SAFE per round, ~6.5 min per round** ⇒ reaching 40 from 13 needs roughly
**another 54 rounds ≈ 6 hours** of continuous serial Inventory. That exceeds the window that was available
for this run, so the loop was halted at a clean checkpoint and the canonical scheduler was restored so that
the 15:00 automation continues the work.

---

## D. WHY SAFE CANNOT GROW FASTER — READ-ONLY DIAGNOSIS

**Active city is Ithaca, NY (`retail_city_queue.id = 20`, status `active`).**

| Signal | Value |
|---|---|
| `lead_discovery_query_state` for city 20 | **12 completed / 45 pending / 1 running / 1 configuration_blocked / 1 provider_not_configured** |
| 4A.7 `city_completion_checks(city=20, provider=browser_maps)` | **ALL_MET = False** — all 9 checks unmet |
| Active-city discovery results | manual_review_needed 15, rejected 20, no_public_email 12, website_not_found 11, review_recovery 7, history_blocked 5, website_lookup_pending 5, contact_form_pool 2, identity_review 2 |
| Global `manual_review_needed` | **263** |
| Leads with an email / officially verified | 598 / 356 |

Interpretation:

1. **The new fail-closed logic is behaving correctly.** Ithaca still has 45 un-run query families and open
   staged work, so `complete_active_city_if_exhausted` correctly refuses to mark it exhausted and the queue
   does **not** advance. This is the intended 4A.7 semantics — it is not a regression.
2. **Most of what Ithaca produces is not convertible.** 15 `manual_review_needed` rows are already linked to
   leads (ids 1079–1130) with an empty rejection reason; 12 are `no_public_email`, 11 `website_not_found`.
   Each Inventory round converts very few of these into a V2-safe organization, which is why the SAFE pool
   moved only +3 in six rounds.
3. **The binding constraint is upstream of Inventory**: email discovery / review-gate throughput, not
   discovery volume. Adding more Inventory rounds adds volume that mostly lands in `manual_review_needed`.

---

## E. ACCEPTANCE

| Criterion | Target | Result | Status |
|---|---|---|---|
| Codex `07784044` deployed byte-identically | yes | `bd_orchestrator.py` + `retail_city_queue.py` match remote SHA256 | **PASS** |
| Zero new test regressions | yes | FAILED set identical to baseline; 4A.7 test 10/10 | **PASS** |
| Scheduled Inventory paused during manual work | yes | PAUSED for the whole window | **PASS** |
| Manual Inventory strictly serial | yes | 6 rounds, one subprocess at a time, overlap guard active | **PASS** |
| Stop at SAFE = 40 | 40 | **stopped at 13** after 4 zero-growth rounds; ~6h more needed | **NOT MET** |
| Scheduled Inventory restored | ACTIVE | ACTIVE, next 15:00 +08 | **PASS** |
| Send stages remain paused | paused | PreSend / Preflight / Outreach all PAUSED | **PASS** |
| `SMTP_CONNECTIONS` / sends | 0 | 0; last send 2026-09-16 | **PASS** |
| Business logic changed | no | no V2 / MX / template / sender / city-policy change | **PASS** |

---

## F. OPTIONS TO REACH 40 (all require explicit authorization)

1. **Continue serial accumulation for ~6 more hours** (≈54 rounds). No policy change, but slow; the 15:00
   automation will keep chipping away at it in the meantime.
2. **Increase per-round throughput** (process more query families / backlog items per Inventory invocation).
   This is a Lead-Factory throughput change — out of scope without authorization.
3. **Work the upstream blocker**: the 263 `manual_review_needed` records and the no-email cohort
   (email enrichment / review-gate reconciliation). This changes the conversion rate rather than the volume
   and is the only option that plausibly makes 40 reachable in hours rather than days.
4. **Lower the target** to a reachable watermark (for example 20) and release the send stages against it.

Nothing in this phase changed V2 eligibility, MX gating, templates, sender identity, or city policy.
---

## G. STATE AFTER 4A.5A

```
PRODUCTION HEAD (handoff docs)  = see commit after this file
CODEX DEPLOYED                  = 07784044  (4A.7 + 4A.7A + 4A.7B)
PRODUCTION CODE SHA             = bd_orchestrator.py 7afc4d7f6ac18e22; retail_city_queue.py 46d6f4521892785e
BACKUP OF PRE-DEPLOY FILES      = output/backup_pre_07784044/
READ_ONLY_V2_SAFE_UNIQUE_ORGS   = 13   AUTHORITY = LIVE, printed by inventory:2026-09-21:f76835e9 (01:30 +08)
                                        (read-only V2+MX pool — NOT materialized FSP)
MATERIALIZED_FSP_PLANNED        = 0    AUTHORITY = final_send_plan.status='planned'
LEADS / EVIDENCE / DISCOVERY    = 1104 / 879 / 395   AUTHORITY = live counts
ACTIVE CITY                     = Ithaca, NY (queue id 20); 45 query families still pending
INVENTORY AUTOMATION            = ACTIVE (restored; daily 15:00 +08)
SEND STAGES                     = PreSend / Preflight / Outreach PAUSED (unchanged)
SMTP / SENDS                    = 0 (last send_log 2026-09-16T01:09:52+08)
```
