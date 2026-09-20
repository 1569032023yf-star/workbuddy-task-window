# PHASE 4A.4C — INVENTORY LOCK-CONFLICT STABILIZATION

- **Authority repo:** `1569032023yf-star/workbuddy-task-window` @ `main`
- **Prior production commit:** `823d31a`
- **Codex dev HEAD (unchanged):** `74f50852` (4A.7, still NOT deployed)
- **Window:** 2026-09-21 00:31–01:05 Asia/Shanghai (2026-09-20 16:31–17:05 UTC)
- **Scope constraint honored:** no change to Lead Factory, V2 eligibility, MX gating, templates, sender, or city policy.

---

## A. READ-ONLY AUDIT — every launcher capable of starting Inventory

| # | Launcher | Type | State | Actually launches Inventory? |
|---|---|---|---|---|
| 1 | WorkBuddy automation `automation-1784775229336` "RoktRazo BD Inventory — 15:00 Asia/Shanghai" | recurring daily 15:00 CST | **ACTIVE** | **YES — CANONICAL** (`bd_orchestrator.py --stage inventory --live`) |
| 2 | Scheduled task `RoktRazo-BD-Outreach` | Task Scheduler, daily 23:00 CST | Ready | No — action is `--stage outreach` |
| 3 | Scheduled task `RoktRazo-BD-PostSend` | Task Scheduler, daily 00:10 CST | Ready | No — action is `--stage post-send` |
| 4 | Scheduled task `RoktRazo-BD-PreSend` | Task Scheduler, daily 22:30 CST | **Disabled** | No — action is `--stage pre-send` |
| 5 | Windows service `BDExecutionHost` | Service | Stopped / Manual | No (not running) |
| 6 | WorkBuddy automation `automation-1786002601925` "BD Result Recovery Sync 08:45" | recurring daily 08:45 CST | ACTIVE | No — runs `result_recovery_sync.py` |
| 7 | Manual driver `%TEMP%\run_4a4b_accumulate.py` | ad-hoc background loop | was running | **YES — the reentrant loop** |

**Result: `DUPLICATE_ACTIVE_INVENTORY_TRIGGERS = 0`.**
There is exactly one canonical Inventory scheduler. **No duplicate scheduler exists.**
The Outreach/PostSend scheduled tasks do not invoke the inventory stage; no Task Scheduler entry targets inventory.

---

## B. STORM MEASUREMENT

`job_runs`, `stage='inventory'`, `business_date='2026-09-20'`:

| Metric | Value |
|---|---|
| Total `lock_conflict` rows | **6,851** |
| Peak rate (single driver) | ~52–55 rows/min ≈ **1 launch/second** |
| Burst rate (13:23–13:46 UTC) | ~136–140 rows/min ⇒ **2–3 concurrent driver instances** |
| Sustained window | ~12:55 → 14:34 UTC (~1h40m) |
| Successful non-conflict iterations | 22 `safe_inventory_gap` (partial) |

> Note for future audits: the previously reported figure "30 inventory runs in ~33 seconds" was a
> **30-row sample of a 6,844-row** event. The real magnitude is ~230x larger.

---

## C. ROOT CAUSE (code-verified, not inferred)

Two independent locks govern one concurrent inventory run per business date:

1. **`job_runs` row** `stage='inventory' AND status='running'` — guard at `bd_orchestrator.py:615`
   (`start_job_run` returns False → prints `[DUPLICATE]` → **no row is inserted**).
2. **Named lock** `run_lock:daily_outreach:inventory:{date}` (holder = run_id) — acquired at
   `bd_orchestrator.py:412`.

The failure mode is the **second** guard:

```
bd_orchestrator.py:615  start_job_run(...)            -> SUCCEEDS (previous row is terminal, not 'running')
                                                         -> INSERT row status='running'
bd_orchestrator.py:412  acquire_run_lock(inventory:{date}, run_id)  -> FALSE (named lock held elsewhere)
bd_orchestrator.py:413  finish_job_run(run_id,'stopped', stop_reason='lock_conflict')
```

Consequences:

- Each invocation **inserts a permanent row** then marks it terminal, so the next invocation is free to
  insert again ⇒ **one polluted row per launch, unbounded**.
- Line 413 emits **no stdout marker**. The driver only backs off when it sees `[DUPLICATE]` in stdout
  (which belongs to guard #1 and is never printed here) ⇒ **zero backoff ⇒ ~1 subprocess launch/second**.
- The wedge self-healed only when `acquire_run_lock`'s **2h stale TTL** (`bd_db.py:796–828`) expired at
  ~14:34 UTC — which is exactly when real work resumed (`safe_inventory_gap` iterations 14:34:38 onward).

**Classification:** not a duplicate scheduler, not an orphan process alone → **`reentrant accumulation loop
with no backoff on a silent early-exit path`, amplified by a `stale run-lock` held by an interrupted run.**

---

## D. STABILIZATION ACTIONS PERFORMED (existing semantics only)

1. **Stopped the reentrant driver.** Terminated `PID 66044` (`%TEMP%\run_4a4b_accumulate.py`) and its
   inventory child. Verified `python processes = 0`.
2. **Verified no respawn:** 0 new `job_runs` rows over 100s ⇒ **RESPAWN = NO**
   (proves the driver, not a scheduler, was generating the storm).
3. **Cleared the orphaned run** `inventory:2026-09-20:e9fe55d7` using the **same UPDATE statement**
   `start_job_run` itself uses for stale cleanup (`bd_db.py:982–985`), then released the named lock via
   the existing `bd_db.release_run_lock()` (holder-matched), and wrote an audit marker with the same key
   shape as the existing precedent
   (`audit:stale_lock_released:run_lock:daily_outreach:inventory:2026-07-23 / 2026-09-15`).

Verified: `STALE_RUNNING_INVENTORY_JOBS = 1 → 0`, `HELD_INVENTORY_LOCKS = 1 → 0`,
`LIVE_INVENTORY_PROCESSES = 0`.

---

## E. CANONICAL INVENTORY RUN — attempt executed, externally disrupted

Run executed exactly once with the required environment:

```
DISCOVERY_PROVIDER=browser_maps   BROWSER_MAPS_MODE=direct   SAFE_INVENTORY_TARGET=50
SCRAPER_PROXY / HTTP_PROXY / HTTPS_PROXY = http://127.0.0.1:3213
bd_orchestrator.py --stage inventory --live
```

| Field | Value |
|---|---|
| run_id | `inventory:2026-09-20:caa09c3e` |
| PID | 69236 |
| started / finished (UTC) | 16:46:09 / 16:51:13 — **4m54s** |
| Lock acquisition | **SUCCESS — status went `running`, did NOT early-exit** |
| `stop_reason` | `stale_cleanup_orphan_killed` — **≠ lock_conflict** ✅ |
| `status` | `failed` (terminated by an external actor, see §F) |
| Discovery evidence | wrote `data/browser_maps_cache/hobby_store_ithaca_ny_*.json`; browser_maps resolved 1 direct Maps place panel |
| Delta | `LEADS 1089 → 1092`, `EVIDENCE 864 → 867`, `DISCOVERY_RESULTS 374 → 380` |

**The lock-conflict failure mode itself did not recur** — the run acquired the inventory lock normally and
did real discovery work. It was cut short by something outside this task.

---

## F. BLOCKER — a second operator is driving the same production DB

Evidence collected during this run:

| Time (CST) | Fact |
|---|---|
| 00:50:01 | `%TEMP%\run_4a4b_accumulate.py` rewritten (13,573 → 18,951 bytes) *after* I killed its process |
| 00:52:58 → 00:54:31 | new `lock_conflict` rows every ~31s — storm restarted without me |
| 00:55:06 | driver rewritten again (19,410 bytes) |
| 00:56:22 | driver rewritten again (19,818 bytes) |
| 00:56:37 | driver **relaunched** `PID 50320` → inventory child `PID 21004` holding the lock now (`inventory:2026-09-20:15d27180`) |

The rewritten driver's own docstring states: *"Prior version spun 6,844x on the SILENT lock_conflict
early-exit (bd_orchestrator:413, no [DUPLICATE] text, no traceback)"* — independently confirming §C.

This violates the required authority model: **one canonical Inventory scheduler + an explicitly controlled
manual driver that never overlaps a canonical Inventory**. My canonical run was overlapped and killed by
this second operator, and the residual storm (`lock_conflict` 6,844 → 6,851) belongs to it, not to my run.

I deliberately did **not** launch a further inventory into the contested lock — doing so would itself have
produced more `lock_conflict` rows and deepened the overlap. No second-operator process was killed by me.

---

## G. ACCEPTANCE TABLE

| Criterion | Target | Result | Status |
|---|---|---|---|
| `DUPLICATE_ACTIVE_INVENTORY_TRIGGERS` | 0 | 0 (1 canonical scheduler; no inventory task/service) | **PASS** |
| `STALE_RUNNING_INVENTORY_JOBS` | 0 | 0 at stabilization checkpoint | **PASS** |
| `LIVE_INVENTORY_PROCESSES` before restart | 0 | 0 verified | **PASS** |
| `LOCK_CONFLICT_STORM_RESOLVED` | true | Root cause identified & verified; my instance stopped with RESPAWN=NO, but a second operator **resumed** the loop | **PARTIAL** |
| `INVENTORY_COMPLETED` | true | Run started, acquired lock, produced discovery; terminated externally before terminal success | **FAIL (blocked)** |
| `STOP_REASON != lock_conflict` | true | `stale_cleanup_orphan_killed` (external kill, not a lock conflict) | **PASS** |
| `SMTP_CONNECTIONS` | 0 | 0 — last `send_log` row 2026-09-16; 0 sends in last 24h | **PASS** |
| `OUTREACH_SEND_COUNT` | 0 | 0; `final_send_plan` planned = 0 | **PASS** |

No business logic was modified. Only existing semantics were used for cleanup.

---

## H. RECOMMENDED NEXT STEP (awaiting authorization)

1. **Reconcile to a single operator.** Close or acknowledge the second session/loop
   (`%TEMP%\run_4a4b_accumulate.py`, currently PID 50320 → 21004). Two operators cannot both hold canonical
   authority over one SQLite production DB; every concurrent attempt is guaranteed to either wedge on the
   named lock or kill the other's run.
2. Then re-run the single canonical Inventory under the same env — expected to complete cleanly now that the
   silent-exit root cause is understood.
3. Optional hygiene (out of scope here): make `bd_orchestrator.py:413` emit a machine-readable marker so any
   future driver can back off; and clean the 6,851 historical `lock_conflict` rows polluting `job_runs`.
