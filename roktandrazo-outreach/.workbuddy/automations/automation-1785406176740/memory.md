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

## 2026-08-04 08:52 CST
- **Batch analyzed**: 2026-08-03 (Monday)
- **Planned**: 9 | **SMTP Accepted**: 0 | **Delivery rate**: 0%
- **⚠️ CRITICAL**: 9 plans created at 21:32 CST (batch 3939af2047) but NONE sent — all stuck in `planned` status
- **Root cause**: `execution_mode = inventory_recovery` (not `daily_outreach`) — orchestrator ran in recovery/recon mode, didn't execute send phase. `daily_run_status = underfilled`
- **Open Signals**: 0 | **Replies**: 0 | **Bounces**: 0 | **Unsubs**: 0
- **Inventory**: 718 total (+4), 99 Broad Outreach Ready (+3), 1 Strict A0, 710 manual review pending
- **Primary states**: TN (170/31 cities, 9 sendable), AR (62/17 cities, 4 sendable), KY (58/19 cities, 1 sendable)
- **Dashboard**: regenerated (336 manual pending, 2 A0 sendable, 187 follow-up sendable). Fixed GBK encoding bug in bd_dashboard_v3.2.py line 189
- **4 consecutive days without sends** (Jul 31 → Aug 3) — orchestrator needs `execution_mode` reset to `daily_outreach`
- **Planned stores for 08-03**: Purple Butterfly Kids (TN/A0), Next Level Games (TN/broad), Storehouse no 9 (MS/broad), Vintage to Modern Toys (TN/broad), The Game Piece (TN/broad), Karz&Dollz Toy Shop (TN/broad), Geeks Etc Video Games (TN/broad), The Toy Store Gifts and More (AR/broad), Steadfast Hobbies (AR/broad)

## 2026-08-05 08:52 CST
- **Batch analyzed**: 2026-08-04 (Tuesday)
- **Planned**: 0 | **SMTP Accepted**: 0 | **Delivery rate**: N/A
- **⚠️ 5 consecutive days without sends** (Jul 31 → Aug 4) — today will be day 6 if no action
- **Open Signals**: 0 | **Replies**: 0 | **Bounces**: 0 | **Unsubs**: 0
- **Inventory**: 718 total, 100 Broad Outreach Ready (+1), 2 Strict A0 (+1), 709 manual review pending
- **Ops API**: planned_new=0, sent_new=0, replies=0, hard_bounces=0; inventory status=critical
- **Dashboard**: regenerated (335 manual pending, 3 A0 sendable, 187 follow-up sendable)
- **Primary states**: TN (170/31 cities, 9 sendable), AR (62/17 cities, 5 sendable), KY (58/19 cities, 1 sendable)
- **Root cause persists**: `execution_mode = inventory_recovery` — orchestrator won't send until reset to `daily_outreach`
- **Aug 3 planned batch (9 stores) still unexecuted** — batch 3939af2047 stuck in `planned` status
- **Files**: auto_report_2026-08-04.md, auto_report_2026-08-04.json, bd_operations_dashboard.html

## 2026-08-06 08:50 CST
- **Batch analyzed**: 2026-08-05 (Wednesday)
- **Planned**: 40 | **SMTP Accepted**: 40 | **Delivery rate**: 100%
- **✅ RESOLVED**: 6-day send drought broken! 2 batches executed:
  - `new_outreach_20260805_et1000` (18:47 CST): 20 emails — broad multi-state (TN/AR/WI/NY/OR/CA/WA/MA/MN/NC/PA/GA)
  - `new_outreach_20260805_2300cs_tnarky` (22:59 CST): 20 emails — TN/AR/KY focused
- **Open Signals**: 0 (no tracking data — poller cache missing, email_tracking_messages not linked to these sends; tracking_message_id linkage gap persists)
- **Replies**: 0 human, 0 auto | **Bounces**: 0 hard | **Unsubs**: 0
- **Inventory**: 738 total leads | 78 Broad Outreach Ready (from broad_outreach_gate) | 0 Strict A0 | 254 manual review pending (bd_ops_api)
  - Broad Ready dropped from 100→78 after 40 sends consumed inventory; 22 new leads added
  - Broad Ready by state: CA(13), FL(9), UT(7), AZ(5), WA(5), MO(4), WI(4), NY(4), OR(4), TX(3)
  - Strict A0 dropped from 2→0 — the 2 A0 leads were consumed in this batch
- **Primary states**: TN (170/31 cities, 7 sendable), AR (62/17 cities, 5 sendable → 2 after sends), KY (58/19 cities, 1→3 sendable)
- **Ops API today (08-06)**: planned=0, sent=0 — normal, send window starts at 09:00
- **Dashboard**: regenerated via bd_operations_dashboard.py (output/bd_operations_dashboard.html)
- **Note**: outreach_batch_date stored as batch ID strings (e.g. `new_outreach_20260805_et1000`), NOT as YYYY-MM-DD; sent_at LIKE fallback works for daily queries

## 2026-08-07 08:50 CST
- **Batch analyzed**: 2026-08-06 (Thursday)
- **Planned**: 0 | **SMTP Accepted**: 0 | **Delivery rate**: N/A
- **⚠️ No sends on Aug 6** — day after the 40-email batch. Either orchestrator didn't run or no inventory left.
- **Open Signals**: 0 | **Replies**: 0 human, 0 auto | **Bounces**: 0 hard | **Unsubs**: 0
- **Inventory**: 738 total | 78 Broad Outreach Ready | 1 Strict A0 (recovered from 0) | 729 manual review pending
  - Strict A0 back to 1 — new A0 lead collected or recovered since Aug 6
- **Primary states**: TN (177/35 cities, 5 sendable), AR (67/17 cities, 4 sendable), KY (66/20 cities, 1 sendable)
- **Dashboard**: regenerated successfully (318 manual pending via dashboard, 1 A0 sendable, 191 follow-up sendable)
- **Data Freshness**: FRESH (bounce scan 08:35 CST, 15 min ago)
- **Delivery Outcome**: SMTP 448 total, 269 in 30d; domain_invalid=22, hard_bounce=6, unmatched_dsn=21, unresolved=392
