# PHASE 4A.5J — WORKBUDDY_DISCOVERY_MAX_PAGES=2 ACCEPTANCE (4-run)

**Reported at:** 2026-09-29 04:07 +08 (Asia/Shanghai) — dynamic, generated this run
**Change point:** 2026-09-27 17:40 UTC = 2026-09-28 01:40 +08 (max_pages 1 → 2)
**Evidence (read-only, authoritative):** `output/4a5g_last_snapshot.json` (AT 2026-09-29 04:07:14) + `output/_4a5j_ckpt_20260929_0407.log`
**Measurement path:** one command only — `output/_4a5g_checkpoint.py` (`bd_leads.db` opened `mode=ro`).
No Inventory launch, no manual run, no SMTP, no DB write, no code edit, no knob change, no scheduler created.
Production knob `WORKBUDDY_DISCOVERY_MAX_PAGES=2` left exactly as-is. No git commit.

## Verdict

**ACCEPTANCE = PASS.** Average provider pages per Inventory run exceeded the 1-page baseline (1.75 vs 1.0, +75%), 4/4 runs since the change point are clean, and every forbidden-signal invariant is zero.

## The 4 Inventory runs since the change point

| # | run_id | started (UTC) | finished (UTC) | runtime | status | stop_reason | provider pages | requests | HTTP 429 | provider non-OK | family |
|---|--------|---------------|----------------|---------|--------|-------------|----------------|----------|----------|-----------------|--------|
| 1 | `inventory:2026-09-28:6ab888b1` | 2026-09-27 22:59:43 | 2026-09-27 23:06:18 | 6m35s | partial | safe_inventory_gap | **2** | 2 | 0 | 0 | game store |
| 2 | `inventory:2026-09-28:02e28542` | 2026-09-28 05:09:27 | 2026-09-28 05:18:30 | 9m03s | partial | safe_inventory_gap | **2** | 2 | 0 | 0 | tabletop game store |
| 3 | `inventory:2026-09-28:ca070d84` | 2026-09-28 08:56:09 | 2026-09-28 09:01:47 | 5m38s | partial | safe_inventory_gap | 1 | 1 | 0 | 0 | tabletop game store |
| 4 | `inventory:2026-09-28:1797b39c` | 2026-09-28 14:21:25 | 2026-09-28 14:45:09 | 23m44s | partial | safe_inventory_gap | **2** | 2 | 0 | 0 | gift shop |

`status=partial` + `stop_reason=safe_inventory_gap` = healthy terminal state (SAFE below the 50 target), **not** a failure.

## Invariants (all pass)

| Invariant | Value | Result |
|---|---|---|
| FAILED_INVENTORY_RUNS (since change point) | 0 | PASS |
| STALE_CLEANUP (24h) | 0 | PASS |
| LOCK_CONFLICT_STORM | none (`MAX_PAGES2_LOCK_CONFLICTS=0`) | PASS |
| CONCURRENT_INVENTORY | none — `RUNNING_INVENTORY_JOBS=0`; all 4 run windows disjoint | PASS |
| HTTP 429 count | 0 (also `PROVIDER_429_TOTAL_ALL_TIME=0`) | PASS |
| Provider error count | 0 (`MAX_PAGES2_PROVIDER_NON_OK_TOTAL=0`) | PASS |
| Zero-SAFE-gain not applicable (SAFE moved 18 → 19) | — | n/a |
| DB integrity / V2+MX policy | SAFE recomputed only through frozen `campaign_eligible_v2.select_candidates_for_plan_v2`; no guessed_email / V1-only / BROAD_READY substitution | PASS |

## Throughput verdict

- Pages per run: `[2, 2, 1, 2]` → **avg 1.75** vs baseline `[1, 1, 1, 1]` → **avg 1.0**.
- **Yes — average provider pages per run exceeded the 1-page baseline** (`MAX_PAGES2_THROUGHPUT_IMPROVED=true`).
- 1 of 4 runs still consumed a single page: expected structural behaviour of the browser provider (repeat-page + "2 consecutive pages with no new results" family-close rule), not a regression.

## Accumulation state at this checkpoint

- `READ_ONLY_V2_SAFE_UNIQUE_ORGS` = **19** (before change point = 18 at 2026-09-28 01:40 +08 → **+1**, new org `org:domain:saratogateaandhoney.com`).
- ACTIVE_CITY = **Saratoga Springs, NY**; LAST_COMPLETED_CITY = Ithaca; NEXT = Cooperstown.
- Active-city query families: 4/20 completed, 1 running, 15 pending; active family = `gift shop`.
- SAFE40_REACHED = **false** → `NEXT_ACTION=CONTINUE_UNATTENDED_ACCUMULATION`.
- BLOCKERS = **none**; WARNINGS = none.

## Send-freeze state (unchanged)

`SMTP_ENABLED=0` · `MATERIALIZED_FSP_PLANNED=0` · `SEND_LOG_TODAY=0` · last send 2026-09-16T01:09:52+08:00 · `send_log` total 517.
No PreSend / Preflight / Outreach / send activity was triggered or observed.

## Scope notes

- Canonical Inventory automation `1784775229336` (4×/day, 6h interval, anchor :58 +08) **left running, untouched**. The observed 4 runs/UTC-day are the authorised cadence, not a duplicate authority.
- Next Inventory run expected ≈ 2026-09-29 04:21 +08; the next 6-hourly checkpoint measures the settled state after it.
- Handoff repo (`workbuddy-task-window`) was **not** touched by this read-only automation — backfill/CHANGELOG is left to a supervised phase.
</content>
