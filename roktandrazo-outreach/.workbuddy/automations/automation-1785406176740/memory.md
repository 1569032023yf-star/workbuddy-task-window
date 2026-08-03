# BD Daily Results Automation Memory

## 2026-08-01 08:53 CST
- **Batch analyzed**: 2026-07-31
- **Planned**: 21 | **SMTP Accepted**: 21 | **Delivery rate**: 100%
- **Open Signals**: 0 (tracking worker poller cache stale from 07-30; 21 new sends may lack tracking_message_id linkage)
- **Replies**: 0 human, 0 auto | **Bounces**: 0 hard | **Unsubs**: 0
- **Inventory**: 714 total leads, 96 Broad Outreach Ready, 1 Strict A0 (CRITICAL), 707 manual review pending
  - Note: discrepancy vs dashboard (334) due to `review_status=pending` in bd_ops_api inventory counting all leads with review_reason_code
- **Active primary states**: TN (167 in 29 cities), AR (61 in 17 cities), KY (58 in 19 cities)
- **Issue**: July 31 sends all have `outreach_batch_date=NULL` — sender not populating the field; may affect daily counting
- **Dashboard**: regenerated via bd_dashboard_v3.2.py (334 manual pending, 2 A0 sendable, 171 follow-up sendable)

## 2026-08-02 08:54 CST
- **Batch analyzed**: 2026-08-01 (Sunday)
- **Planned**: 0 | **SMTP Accepted**: 0 | **Delivery rate**: N/A
- **Note**: Weekend — no send activity expected. Last active day: Jul 31 (21 sends, all missing outreach_batch_date=NULL)
- **Open Signals**: 0 | **Replies**: 0 | **Bounces**: 0 | **Unsubs**: 0
- **Inventory**: 714 total, 96 Broad Outreach Ready, 1 Strict A0 (CRITICAL), 707 manual review pending
- **Primary states**: TN (167/29 cities, 6 sendable), AR (61/17 cities, 4 sendable), KY (58/19 cities, 1 sendable)
- **Issue persists**: outreach_batch_date=NULL bug still affects Jul 31 send_log queries — sent_at LIKE fallback works but untracked under batch_date
- **Dashboard**: regenerated successfully (334 manual pending, 2 A0 sendable, 171 follow-up sendable)
- **Script fix**: Fixed _daily_readonly_report.py early-return missing `planned` key (0-send edge case); fixed bd_dashboard_v3.2 import (dot vs underscore mismatch)

## 2026-08-03 09:09 CST
- **Batch analyzed**: 2026-08-02 (Sunday)
- **Planned**: 0 | **SMTP Accepted**: 0 | **Delivery rate**: N/A
- **Note**: Weekend — no send activity. Last active day: Jul 31 (21 sends)
- **Open Signals**: 0 | **Replies**: 0 | **Bounces**: 0 | **Unsubs**: 0
- **Inventory**: 714 total, 96 Broad Outreach Ready, 1 Strict A0 (CRITICAL), 707 manual review pending
- **Primary states**: TN (167/29 cities, 6 sendable), AR (61/17 cities, 4 sendable), KY (58/19 cities, 1 sendable)
- **Dashboard**: regenerated via bd_dashboard_v3.2.main() (334 manual pending, 2 A0 sendable, 179 follow-up sendable)
- **Used**: _daily_readonly_report.py — all 4 sections completed cleanly
