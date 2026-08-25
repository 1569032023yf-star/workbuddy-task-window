# BD Pre-Send Report — 2026-08-20 (ET 09:30 / CST 21:30)

**Batch ID:** `new_outreach_20260820_et1000`
**Generated:** 2026-08-20 21:31:13 Asia/Shanghai
**Status:** ❌ NO_BATCH_TODAY

---

## Diagnosis

| Check | Result |
|-------|--------|
| Frozen snapshot | `frozen_new_outreach_20260820_et1000.json` — NOT FOUND |
| Last known snapshot | `frozen_new_outreach_20260804_et1000.json` (Aug 4) |
| Freeze gap | no snapshot produced since Aug 4 |

## DB Context (FYI only — no action taken)

| Metric | Value |
|--------|-------|
| Raw eligible unsent (ALLOWED_STATES) | 38 |
| Today sent | 0 |
| Today plan entries | 0 |
| preflight_status | `no_batch` |
| Follow-up | 0 |
| SMTP | 0 (no SMTP) |

## Actions Taken

- [x] Confirmed no `frozen_new_outreach_20260820_et1000.json` exists (checked output/ and data/)
- [x] Set `preflight_status = no_batch` in system_config
- [x] No SMTP — clean exit
- [x] Follow-up = 0

## Root Cause

The pre-send pipeline requires a frozen candidate inventory snapshot created by the
21:10 CST freeze step. Without it there is no authoritative candidate list to plan from.
The freeze step has not produced a snapshot since Aug 4.

## Recommendation

Investigate why the 21:10 CST freeze step is not generating
`frozen_new_outreach_YYYYMMDD_et1000.json`:
1. Is the 5-phase schedule (daily_operator_auto.py / BD Execution Host Service) running?
2. Is the freeze/log collection step erroring out?
3. Is the Nashville A0 pool replenished (known gap of ~37)?
