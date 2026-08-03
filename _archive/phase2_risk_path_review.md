# Phase 2 Risk Path Review

**Date**: 2026-06-29 17:50  
**Staging Directory**: `/c/Users/15690/WorkBuddy/2026-06-05-15-31-42/roktandrazo-outreach_phase2_staging_20260629_1732/roktandrazo-outreach`

## Risk Questions & Answers

### 1. Under dry‑run, is there still a risk of real sending?
**No.** The dry‑run flag is consistently checked in all sending paths (`bd_sender.py`, `daily_session.py`, `daily_operator_auto.py`). When `dry_run=True`, the code prints `[DRY RUN]` and skips the actual SMTP call. The orchestrator also prints `[DRY RUN] Would run...` for subprocess calls.

### 2. Can `guessed_email` be sent?
**No.** The system only sends to leads with `pool='A0'` or `status='approved_manual_send'`. `guessed_email` leads reside in pool `B` and require explicit human approval (`approved_manual_send`) before they become sendable. The `b_pool_import.py` does not automatically promote guessed emails.

### 3. Can B/C pool leads be sent?
**No.** B‑pool leads are not selected for sending unless upgraded to A0 (via browser verification) or manually approved. C‑pool leads (contact‑form‑only) are never sent via email; they are marked for manual outreach.

### 4. Can `suppression`, `bounced`, or `delivery_issue` leads be sent?
**No.** The `select_leads_for_send()` function filters out leads with `status IN ('suppression', 'bounced', 'delivery_issue')`. The `send_pause` flag can also block all sending.

### 5. Can sending occur outside the 08:30–12:00 window?
**In dry‑run mode, no.** The `is_in_send_window()` check is bypassed only when `dry_run=True` for testing. In live mode, the orchestrator aborts if outside the window (line 828: `elif not dry_run and not is_in_send_window():`). The `--window` argument allows customizing the window.

### 6. Can `underfilled` be marked `completed`?
**No.** The status logic sets `completed` only when `sent >= target`. If `sent < target`, status remains `underfilled` (line 860‑866). The report also flags the gap.

### 7. After Browser Verifier upgrades A0, does it trigger a recovery check?
**Yes.** The `post_a0_upgrade_recovery_check()` function is called after the lead factory step (line 800). It checks if new A0 leads were added and, if still within the sending window, attempts to fill the gap.

### 8. If the window has passed, does it queue for the next window instead of sending immediately?
**Yes.** The `post_a0_upgrade_recovery_check()` function uses `is_in_send_window()`. If outside the window, it sets `next_window_queued = gap` and does not send (line 477‑480). The report then shows `next_window_needed_count`.

## Additional Risk Path Findings

- **SMTP layer (`bd_sender.py`)**: Unchanged in Phase 2. The `send_one()` function respects `dry_run` and `send_pause`.
- **Database writes (`bd_db.py`, `db.py`)**: Unchanged. No new write paths.
- **Automated tasks**: `daily_operator_auto.py` modified, but changes are in orchestration logic, not core safety guards.
- **New bypass paths**: None found. All new code paths (lead factory, browser verifier, recovery check) are gated by `dry_run` and `send_pause`.

## Conclusion
**No high‑risk paths detected.** The Phase 2 patch preserves the existing safety guards and adds new automation steps that are correctly gated by dry‑run and pause flags.