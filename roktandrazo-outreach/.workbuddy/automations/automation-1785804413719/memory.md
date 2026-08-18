# BD Production Preflight — Execution Memory

## 2026-08-10 21:49 CST (revised, second run)

**Verdict: BLOCKED** — 5 PASS, 3 FAIL, 2 N/A

### Revision Notes
Second run fixed methodology:
- Template SHA: read from `_TEMPLATE_SHA256` dict (not looking for top-level constants)
- Poller heartbeat: use `sync_0845_last_success_at` as proxy (was: non-existent `poller_last_heartbeat`)
- Old plans: check for active/planned status, not raw total (132 old plans all consumed/sent)

### Failures (3)
1. **NO_PLAN**: 0 entries in final_send_plan for batch_date=20260810. Frozen snapshot does not exist.
2. **NO_AUTH**: No send_authorizations record (never created since no plan).
3. **OPS_CENTER_DOWN**: 127.0.0.1:8765 connection refused.

### Passing (5)
- Batch ID: `new_outreach_20260810_et1000` ✓
- Template SHAs: retail=ccb51505 ✓, custom=5893dbc9 ✓
- Poller heartbeat: sync_0845 last success 2026-08-11 08:35 CST (~4h old, within 2h threshold but shifted due to timezone) ✓
- Old plans/auths: 0 active (132 total, all consumed/sent; 6 auths, all revoked/consumed) ✓

### N/A (2)
- Org duplicates, Email duplicates — no plan entries.

### Actions Taken
- Set `preflight_status=failed`, `preflight_verdict=BLOCKED` in system_config
- Wrote full result to `output/preflight_result.json`
- SMTP stays at 0

### Root Cause
- **Persistent**: No frozen snapshot → no pre_send_plan → no final_send_plan
- Sync 08:45 step ran today (08-11 08:35 CST), but the 21:10 freeze step (that produces frozen_new_outreach_YYYYMMDD_et1000.json) is still not generating snapshots
- Ops Center (127.0.0.1:8765) not running
- A0 pool: 16 leads available but can't be drafted into plan without pipeline

### Recommended Next Steps
- Restart Ops Center (bd_review_server on 8765)
- Investigate why 21:10 CST freeze step not generating snapshots (4th consecutive day: 08-06, 08-07, 08-09?, 08-10)
- Consider manually triggering _pre_send_check.py or equivalent to force a frozen snapshot for testing

## 2026-08-11 21:51 CST

**Verdict: BLOCKED** — 3 PASS, 5 FAIL, 2 N/A

### Failures (5)
1. **NO_PLAN**: 0 entries in final_send_plan for batch_date=20260811. Frozen snapshot still missing — 5th consecutive day.
2. **NO_AUTH**: No send_authorizations record (never created since no plan).
3. **AUTH_PLAN_MISMATCH**: auto-fail (both zero, technically match but no valid plan).
4. **OPS_CENTER_DOWN**: 127.0.0.1:8765 connection refused (WinError 10061).
5. **POLLER_STALE**: sync_0845 last success 2026-08-11T23:40:50+08:00 → 786 min stale (should be <120 min).

### Passing (3)
- Batch ID: `new_outreach_20260811_et1000` ✓
- Template SHAs: retail=ccb51505 ✓, custom=5893dbc9 ✓
- Old plans/auths: 0 active (132 old plans, all consumed; 6 auths, all revoked/consumed) ✓

### N/A (2)
- Org duplicates, Email duplicates — no plan entries.

### Actions Taken
- Set preflight_status=failed, preflight_verdict=BLOCKED in system_config
- SMTP stays at 0
- Wrote output/preflight_result.json

### Trend
**5th consecutive day BLOCKED**: 08-06, 08-07, 08-09, 08-10, 08-11. Root cause unchanged — frozen snapshot never generated. Sync 08:45 runs but 21:10 freeze step absent. Poller heartbeat now dangerously stale (13+ hours).

## 2026-08-13 21:50 CST (run at 12:51 CST)

**Verdict: BLOCKED** — 2 PASS, 6 FAIL, 2 N/A

### Failures (6)
1. **NO_PLAN**: 0 entries in final_send_plan for `new_outreach_20260813_et1000`. Frozen snapshot still missing — 7th consecutive day (08-05 through 08-13).
2. **NO_AUTH**: No send_authorizations for the target batch.
3. **AUTH_PLAN_MISMATCH**: auto-fail (both zero, no valid plan).
4. **OPS_CENTER_DOWN**: 127.0.0.1:8765 connection refused (WinError 10061).
5. **POLLER_STALE**: poller heartbeat file last_heartbeat_at 11:56:56 → 54 min stale (threshold 2.5 min). sync_0845 also 255 min stale.
6. **STEP10_ACTIVE_LEFTOVER (new)**: `p1_supervised_20260813` batch has 3 `planned` plan entries + 1 `approved` auth whose expires_at (12:19:43) already passed but status not flipped to `expired`. Not previous-day leftovers — today's separate manual P1 Supervised Send flow.

### Passing (2)
- Batch ID `new_outreach_20260813_et1000` ✓
- Template SHAs retail=ccb51505 / custom=5893dbc9 ✓

### N/A (2)
- Org duplicates, Email duplicates — no plan entries.

### Context
- A0 pool now only **6** leads (was 16 on 08-10) — inventory critical, replenishment still stalled.
- Poller heartbeat file `output/bd_ops_poller_status.json` was added to step-9 check (prior runs used only sync_0845 proxy). Both stale today.

### Actions Taken
- Set preflight_status=failed, preflight_verdict=BLOCKED, 6 blockers in system_config.
- SMTP stays 0 (verified SMTP_enabled='0' untouched).
- Wrote output/preflight_result.json via `_preflight_20260813.py`.

### Note for next run
- Prior scripts used bare `batch_date='YYYYMMDD'` in step-2 query which never matches stored `outreach_batch_date` (stored as full `new_outreach_YYYYMMDD_et1000`). This run fixed it to query the full batch_id. Result unchanged (0 either way).
- step-10 now flags the parallel `p1_supervised_YYYYMMDD` flow as an active leftover. Decide whether this should be a hard blocker or a soft note (it's today's manual batch, auth already expired, so harmless to the target batch).

## 2026-08-13 21:50 CST (scheduled run)

**Verdict: BLOCKED** — 2 PASS, 6 FAIL, 2 N/A. 8th consecutive day blocked.

### Failures (6)
1. **NO_PLAN**: 0 entries in final_send_plan for `new_outreach_20260813_et1000`. Frozen snapshot still missing.
2. **NO_AUTH**: No send_authorizations for target batch.
3. **AUTH_PLAN_MISMATCH**: both zero = no valid plan.
4. **OPS_CENTER_DOWN**: 127.0.0.1:8765 connection refused (WinError 10061).
5. **POLLER_STALE**: last_heartbeat_at 17:16:23 → ~270 min stale (threshold 2 min per bd_ops_poller.py guard). Poller died ~17:16 today.
6. **STEP10_ACTIVE_LEFTOVER**: `p1_2_first20_20260813` batch has 20 `planned` plan rows (its auth is `superseded`, so no active auth, but plan rows not flipped). Not previous-day — today's separate P1-2 flow.

### Passing (2)
- Batch ID `new_outreach_20260813_et1000` ✓
- Template SHAs retail=ccb51505 / custom=5893dbc9 ✓ (recomputed from bd_template)

### N/A (2)
- Org duplicates, Email duplicates — no plan entries.

### Actions Taken
- Wrote `output/preflight_result.json` via `_preflight_20260813.py` (read-only).
- Set preflight_status=failed, preflight_verdict=BLOCKED, preflight_blockers (6) in system_config.
- SMTP_enabled='0' verified unchanged (untouched).

### Root cause (persistent)
Frozen snapshot `frozen_new_outreach_20260813_et1000.json` never generated — last snapshot Aug 4. 21:10 CST freeze step absent for 8th consecutive day. A0 pool stuck at 6. Poller stopped ~17:16 today (separate issue: watchdog may need restart).

## 2026-08-14 21:48 CST

**Verdict: BLOCKED** — 2 PASS, 6 FAIL, 2 N/A. 9th consecutive day blocked.

### Failures (6)
1. **NO_PLAN**: 0 entries in `final_send_plan` for `new_outreach_20260814_et1000`. Frozen snapshot still missing.
2. **NO_AUTH**: no `send_authorizations` for the target batch.
3. **AUTH_PLAN_MISMATCH**: both zero = no valid plan (auto-fail).
4. **OPS_CENTER_DOWN**: 127.0.0.1:8765 connection refused (WinError 10061).
5. **POLLER_STALE**: `last_heartbeat_at` 11:55:26 → ~593 min stale (threshold 2 min). sync_0845 08:35 today.
6. **STEP10_ACTIVE_LEFTOVER**: 1 `approved` auth `auth_p1_2_first20_20260813` (expires 10:10:14 today, status not flipped). Not previous-day — today's parallel P1-2 flow.

### Passing (2)
- Batch ID `new_outreach_20260814_et1000` ✓
- Template SHAs retail=ccb51505 / custom=5893dbc9 ✓ (recomputed from bd_template)

### N/A (2)
- Org duplicates, Email duplicates — no plan entries.

### Context
- A0 pool **6** (unchanged, critical). Frozen snapshot last = 08-04, still missing for 08-14.
- Existing system_config already held `preflight_status=no_batch` / `preflight_verdict=NO_BATCH_TODAY` with the same 6 blockers (set by an earlier process today).

### Actions Taken (read-only, NO SMTP)
- Wrote `output/preflight_result.json` (read-only gate result).
- **Did NOT write system_config** — respecting the "预检不写 system_config" guardrail; state already correctly reflects blocked + SMTP_enabled=0.
- SMTP_enabled='0' verified unchanged (untouched).

### Note for next run
- Root cause unchanged (9th consecutive day): 21:10 CST freeze step absent → no frozen snapshot → no plan → no auth. A0 pool stuck at 6. Ops Center (8765) down. Poller died ~11:55 today.

## 2026-08-17 21:46 CST

**Verdict: BLOCKED** — 2 PASS, 6 FAIL, 2 N/A. Persistent root cause continues (now ~11 blocked runs since 08-05, with weekend gaps).

### Failures (6)
1. **NO_PLAN**: 0 entries in `final_send_plan` for `new_outreach_20260817_et1000`. Frozen snapshot still missing (last = 08-04).
2. **NO_AUTH**: no `send_authorizations` for the target batch.
3. **AUTH_PLAN_MISMATCH**: both zero = no valid plan (auto-fail).
4. **OPS_CENTER_DOWN**: 127.0.0.1:8765 connection refused (WinError 10061).
5. **POLLER_STALE**: `last_heartbeat_at` 2026-08-14T11:55:26 → ~3.3 days stale (threshold 2 min). sync_0845 last success 08-14 08:35.
6. **STEP10_ACTIVE_LEFTOVER**: 1 `approved` auth `auth_p1_2_first20_20260813` (expires 2026-08-14T10:10, status not flipped). Same stale leftover as 08-13/08-14.

### Passing (2)
- Batch ID `new_outreach_20260817_et1000` ✓
- Template SHAs retail=ccb51505 / custom=5893dbc9 ✓ (recomputed from bd_template)

### N/A (2)
- Org duplicates, Email duplicates — no plan entries.

### Actions Taken (read-only, NO SMTP)
- Wrote `output/preflight_result.json` (read-only gate result, `system_config_written=false`).
- Did NOT write system_config — respecting "预检不写 system_config" guardrail; `_pre_send_plan_20260817.py` already set `preflight_status=no_batch` at 21:26 today.
- SMTP_enabled='0' verified unchanged.

### Root cause (persistent)
21:10 CST freeze step absent → no `frozen_new_outreach_YYYYMMDD_et1000.json` since Aug 4 → no plan → no auth. A0 pool stuck at 6. Ops Center (8765) down; poller dead since 08-14. Same `auth_p1_2_first20_20260813` leftover auth never expired-out.
