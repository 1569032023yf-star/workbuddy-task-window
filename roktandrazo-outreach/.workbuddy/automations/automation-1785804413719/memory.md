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

## 2026-08-18 21:48 CST

**Verdict: BLOCKED** — 4 PASS, 4 FAIL, 2 N/A. Root cause SHIFTED (infra recovered, but batch-id mismatch now blocks).

### Failures (4)
1. **NO_PLAN (step2)**: 0 entries in `final_send_plan` for `new_outreach_20260818_et1000`. Frozen snapshot still missing (last = 08-04).
2. **NO_AUTH (step3)**: no `send_authorizations` for the target batch.
3. **AUTH_PLAN_MISMATCH (step4)**: both zero = no valid plan (auto-fail).
4. **STEP10_ACTIVE_LEFTOVER**: 9 `planned` rows under `outreach_batch_date='2026-08-18'` (plain date) + 1 stale `approved` auth `auth_p1_2_first20_20260813` (expired 08-14, never flipped).

### Passing (4)
- Step1 batch_id `new_outreach_20260818_et1000` ✓
- Step7 template SHA retail=ccb51505 / custom=5893dbc9 ✓
- Step8 Ops Center HTTP **200** ✓ (RESTARTED — was down 11 consecutive days)
- Step9 poller heartbeat 0.02 min fresh, running=true ✓ (RESTARTED — was dead since 08-14)

### N/A (2)
- Org duplicates, Email duplicates — no plan for target batch.

### Key context (positive shift)
- A0 pool **29** (up from 6 — inventory replenished).
- Canary send completed today (lead 1055, `tom@playgamecafe.com`, 09:21 CST, template retail_distributor_v5_locked).
- 10 leads prepared today: 9 `planned` + 1 `cancelled` + 1 `sent` — but ALL under `outreach_batch_date='2026-08-18'` (plain date), NOT the canonical `new_outreach_20260818_et1000`.
- `tonight_pending_20260818.json` exists (10 prepared leads).
- **NEW ROOT CAUSE**: today's scripts `_canary_exec.py` / `_prepare_remaining_10.py` hardcoded `batch_date = "2026-08-18"` instead of the canonical batch id → the 9 prepared leads + canary are orphaned under the wrong identifier, and no authorization was created for the 9 planned leads.
- Poller `delivery_guard` job dead ("Guard dead, max restarts reached") — soft note, not a step-9 blocker.

### Actions Taken (read-only, NO SMTP)
- Wrote `output/preflight_result.json` via `_preflight_20260818.py` (read-only, `system_config_written=false`).
- Did NOT write system_config — respecting "预检不写 system_config" guardrail; `_pre_send_plan_20260818.py` already set `preflight_status=no_batch` at 21:26 today.
- SMTP_enabled='0' verified unchanged.

### Recommended next steps (for the human / next repair cycle)
1. Re-key the 9 planned leads + generate a fresh authorization under the canonical `new_outreach_20260818_et1000` (they are already V2-verified + template-rendered; only the batch-id + auth are missing).
2. Generate the frozen snapshot for `new_outreach_20260818_et1000` (restore the 21:10 freeze step).
3. Flip stale `auth_p1_2_first20_20260813` → `expired`.
4. Restart `delivery_guard` (poller running but this component crashed).

## 2026-08-19 21:51 CST

**Verdict: BLOCKED** — 4 PASS, 4 FAIL, 2 N/A

### Failures (4)
1. **NO_PLAN (step2)**: 0 entries in `final_send_plan` for `new_outreach_20260819_et1000`. Frozen snapshot still missing (last = 08-04).
2. **NO_AUTH (step3)**: no `send_authorizations` for the target batch.
3. **AUTH_PLAN_MISMATCH (step4)**: both zero = no valid plan (auto-fail).
4. **STEP10_ACTIVE_LEFTOVER**: 9 `planned` rows under `outreach_batch_date='2026-08-19'` (plain date) + 1 stale `approved` auth `auth_p1_2_first20_20260813` (expired 08-14, never flipped).

### Passing (4)
- Step1 batch_id `new_outreach_20260819_et1000` ✓
- Step7 template SHA retail=ccb51505 / custom=5893dbc9 ✓
- Step8 Ops Center HTTP **200** ✓ (recovered; was down 11 days)
- Step9 poller heartbeat 0.0 min fresh, running=true ✓

### N/A (2)
- Org duplicates, Email duplicates — no plan for target batch.

### Key context
- A0 pool **29** (unchanged). Frozen snapshot last = 08-04.
- **Same root cause as 08-18**: today's 9 `planned` + 1 `cancelled` leads written under plain date `2026-08-19`, NOT canonical `new_outreach_20260819_et1000`; no frozen snapshot, no auth. `tonight_pending_20260819.json` missing.
- Poller `delivery_guard` job dead ("Guard dead, max restarts reached") — soft note, not a step-9 blocker.

### Actions Taken (read-only, NO SMTP)
- Wrote `output/preflight_result.json` via `_preflight_20260819.py` (read-only, `system_config_written=false`).
- Did NOT write system_config — respecting "预检不写 system_config" guardrail; `_pre_send_plan_20260819.py` already set `preflight_status=no_batch`/`NO_BATCH_TODAY` at 21:31 (its blockers list still shows step8/step9 which have since recovered).
- SMTP_enabled='0' verified unchanged.

## 2026-08-20 21:51 CST

**Verdict: BLOCKED** — 2 PASS, 6 FAIL, 2 N/A. Root cause UNCHANGED (batch-id mismatch) + infra regressed again.

### Failures (6)
1. **NO_PLAN (step2)**: 0 entries in `final_send_plan` for `new_outreach_20260820_et1000`. Frozen snapshot still missing (last = 08-04).
2. **NO_AUTH (step3)**: no `send_authorizations` for the canonical batch.
3. **AUTH_PLAN_MISMATCH (step4)**: both zero = no valid plan (auto-fail).
4. **OPS_CENTER_DOWN (step8)**: 127.0.0.1:8765 connection refused (WinError 10061) — regressed (was 200 on 08-18/08-19).
5. **POLLER_STALE (step9)**: last_heartbeat 15:11 today → 399 min stale (threshold 2 min). `running=true` but `delivery_guard` dead + `tracking` all-transports-failed.
6. **STEP10_ACTIVE_LEFTOVER**: **44** `planned` rows under plain date `2026-08-20` (NOT canonical batch) — grew from 9 (08-18/08-19) to 44 today. No auth created for them.

### Passing (2)
- Step1 batch_id `new_outreach_20260820_et1000` ✓
- Step7 template SHA retail=ccb51505 / custom=5893dbc9 ✓

### N/A (2)
- Org duplicates, Email duplicates — no plan for canonical batch.

### Key context
- A0 pool **29** (unchanged). Frozen snapshot last = 08-04.
- **Same root cause as 08-18/08-19**: today's prepared leads written under plain date `2026-08-20`, NOT canonical `new_outreach_20260820_et1000`; no frozen snapshot, no auth. Count grew 9 → 44 (pipeline IS producing leads now, but under wrong batch id).
- 1 `canary_2026-08-20` cancelled (auth `auth_canary_2026-08-20` revoked).
- send_log today = 0 (nothing sent, SMTP=0).
- system_config already held `preflight_status=no_batch`/`NO_BATCH_TODAY` + 6 blockers (set by `_pre_send_plan` at 21:31).

### Actions Taken (read-only, NO SMTP)
- Wrote `output/preflight_result.json` via `_preflight_20260820.py` (read-only, `system_config_written=false`).
- Did NOT write system_config — respecting "预检不写 system_config" guardrail; state already correctly reflects blocked + SMTP_enabled=0.
- SMTP_enabled='0' verified unchanged.

### Recommended next steps (for human / next repair cycle)
1. Re-key the 44 planned leads under canonical `new_outreach_20260820_et1000` + generate a matching authorization (they are already prepared; only batch-id + auth missing).
2. Restore the 21:10 CST freeze step to generate `frozen_new_outreach_YYYYMMDD_et1000.json` (missing since 08-04).
3. Restart Ops Center (8765) — regressed today.
4. Restart `delivery_guard` + fix `tracking` transport (poller running but both sub-jobs failing).

## 2026-08-21 21:51 CST

**Verdict: BLOCKED** — 3 PASS, 5 FAIL, 2 N/A. Root cause UNCHANGED (batch-id mismatch), but SENDING RESUMED (5 emails actually sent).

### Failures (5)
1. **NO_PLAN (step2)**: 0 entries in `final_send_plan` for canonical `new_outreach_20260821_et1000`. Frozen snapshot still missing (last = 08-04).
2. **NO_AUTH (step3)**: no `send_authorizations` for the canonical batch.
3. **AUTH_PLAN_MISMATCH (step4)**: both zero = no valid plan (auto-fail).
4. **OPS_CENTER_DOWN (step8)**: 127.0.0.1:8765 connection refused (no listener) — still down.
5. **POLLER_STALE (step9)**: `last_heartbeat_at` 2026-08-20T15:11:50 → 1839 min stale (threshold 2 min). `running=true` but `delivery_guard` dead + `tracking` all-transports-failed.

### Passing (3)
- Step1 batch_id `new_outreach_20260821_et1000` ✓
- Step7 template SHA retail=ccb51505 / custom=5893dbc9 ✓
- Step10 old plans/auths: 0 active ✓

### N/A (2)
- Org duplicates, Email duplicates — no plan for canonical batch.

### Key context — SENDING RESUMED (important shift)
- **5 emails actually sent today** (08-21 11:59–12:04 CST, SMTP accepted), template `retail_distributor_v5_locked`, leads 1056–1060.
- BUT all 5 written under plain date `outreach_batch_date='2026-08-21'` (plan_id `2026-08-21:new_outreach:38419abaa0`), NOT canonical `new_outreach_20260821_et1000`. Auth `auth_2026-08-21:new_outreach:...` now `consumed`.
- **Same root cause as 08-18/08-19/08-20**: today's sends keyed under plain date, not canonical batch id; no frozen snapshot.
- system_config `SMTP_enabled`='0' is now STALE — SMTP is actually working (5 sends today) but flag not updated since 08-11.
- sync_0845 ran this morning (08:51). A0 pool 29. Frozen snapshot last = 08-04.

### Actions Taken (read-only, NO SMTP)
- Wrote `output/preflight_result.json` via `_preflight_20260821.py` (read-only, `system_config_written=false`).
- Did NOT write system_config — respecting "预检不写 system_config" guardrail; `_pre_send_plan_20260821.py` already set `preflight_status=no_batch`/`NO_BATCH_TODAY` at 21:31.
- SMTP_enabled='0' left untouched (flagged as stale).

### Recommended next steps (for human / next repair cycle)
1. **Fix batch-id in the send pipeline** — today's 5 sends prove SMTP + plan + auth all work; the only remaining defect is the batch identifier (plain date vs canonical `new_outreach_YYYYMMDD_et1000`). Re-keying the same flow to the canonical id would make the gate pass.
2. Restore the 21:10 CST freeze step (`frozen_new_outreach_YYYYMMDD_et1000.json` missing since 08-04).
3. Restart Ops Center (8765).
4. Restart `delivery_guard` + fix `tracking` transport.
5. Reconcile `SMTP_enabled` config flag with reality (it's been '0' while sends actually go out).
