# BD Tonight Send — 2026-08-03 22:00 CST

## Status: BLOCKED

**preflight_status: failed** → SMTP = 0, per user instruction.

## Preflight Results (10 PASS / 1 FAIL)

| Step | Check | Result |
|------|-------|--------|
| 1 | Plan entries exist | PASS (9) |
| 2 | Send authorization active | PASS |
| 3 | Auth entries = Plan entries | PASS (9=9) |
| 4 | Organization duplicate = 0 | PASS |
| 5 | Email duplicate = 0 | PASS |
| 6 | Template SHA matches | PASS |
| 7 | Ops Center HTTP 200 | PASS |
| 8 | Poller heartbeat fresh | **FAIL** (682.8 min stale, threshold 15 min) |
| 9 | Tracking Worker HTTP 200 | PASS |
| 10 | No stale plans/auths | PASS |

## Blocker

- **Poller heartbeat stale**: Last heartbeat 2026-08-03T10:39:12+08:00 (~682 min ago). Threshold: 15 min.

## Batch Details

- Batch: `new_outreach_20260803_et1000`
- Plan ID: `2026-08-03:new_outreach:3939af2047`
- Auth ID: `auth_2026-08-03_ab777bd5`
- 9 planned entries, all TN/AR retail/game/toy stores
- 0 emails sent (SMTP blocked)

## System State After Run

- standing_authorization: true
- manual_pause: false
- risk_gate_status: clear
- send_pause: false
- send_authorizations.preflight_status: failed

## Resolution

Restart the Ops Center poller (`bd_delivery_guard.py` or `bd_execution_host_service.py`) to refresh the heartbeat, then re-run `_preflight_tonight.py`. Once preflight passes, the send can proceed.
