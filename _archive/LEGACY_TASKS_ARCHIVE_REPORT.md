# Legacy Tasks Archive Report

**Date**: 2026-06-30

---

## Archived Tasks

| Field | Value |
|-------|-------|
| Task ID | automation-1782369770937 |
| Original Name | BD Daily Send — 08:30 Auto Operator |
| New Name | [ARCHIVED] BD Daily Send — 08:30 Auto Operator |
| Status | PAUSED |
| Schedule | FREQ=DAILY;BYHOUR=8;BYMINUTE=30 |
| Risk | Used --live directly (no dry-run gate) |
| Action Taken | Archived (PAUSED), will not execute |

### Why Archived
- Used old 08:30 schedule (new task uses 09:00)
- Did not include dry-run gate before live
- May have used old V3 template
- Superseded by new task with full safety chain

---

## New Active Task

| Field | Value |
|-------|-------|
| Task ID | automation-1782800192924 |
| Name | Roktandrazo BD Daily Send Live - 09:00 |
| Status | ACTIVE |
| Schedule | FREQ=DAILY;BYHOUR=9;BYMINUTE=0 |
| Command | daily_operator_auto.py --dry-run/--live --target-count 20 --allow-topup --stop-on-risk |
| Safety | dry-run gate + --stop-on-risk + send window check |

---

## Safety Confirmation

- [x] Old task archived (not deleted)
- [x] New task created with --stop-on-risk
- [x] New task includes dry-run gate
- [x] No duplicate sending tasks active
- [x] Database not modified
- [x] Source code not modified
- [x] Backup preserved

---

*Generated at 2026-06-30 14:15*
