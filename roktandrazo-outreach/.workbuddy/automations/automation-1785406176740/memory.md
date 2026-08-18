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


## 2026-08-11 09:00 CST (automated run)
- **Batch analyzed**: 2026-08-10 (Monday)
- **Planned**: 0 | **SMTP Accepted**: 0 | **Delivery rate**: N/A
- **⚠️ 6 consecutive days without sends** (Aug 5-10) — last send was Aug 5 40-email batch
- **Open Signals**: 0 | **Replies**: 0 human, 0 auto | **Bounces**: 0 hard | **Unsubs**: 0
- **Tracking**: poller cache stale (Jul 30); 2 all-time open signals in D1; tracking_message_id linkage gap persists
- **Inventory**: 738 total | 48 Broad Outreach Ready orgs (48 locations) | 0 Strict A0 ⚠️ CRITICAL (7th day at 0)
  - Broad Ready stable at 48 — no consumption, no replenishment
  - Previously sent: 427 (up from earlier counts, more leads marked sent)
  - Manual review pending: 267 (review_status=pending) / 290 (dashboard) / 254 (bd_ops_api)
  - Suppressed: 17
- **Primary states**: TN (177/35 cities, 5 sendable), AR (67/17 cities, 4), KY (66/20 cities, 1), OR (25/4, 8)
- **Dashboard**: regenerated via bd_dashboard_v3.2.py (290 manual pending, 0 A0 sendable, 191 follow-up sendable)
- **Data Freshness**: FRESH (bounce scan 23:40 CST, 16 min ago)
- **Delivery Outcome**: SMTP 448 total, 234 in 30d; domain_invalid=22, hard=6, policy=3, unmatched_dsn=21, unresolved=392; auto_reply=1
- **Output**: auto_report_2026-08-11.md, auto_report_2026-08-11.json, bd_ops_dashboard.html
- **Key issues**: 1) 6-day send drought — orchestrator not running; 2) Strict A0=0 for 7 days; 3) No new lead collection in progress

## 2026-08-11 08:54 CST
- **Batch analyzed**: 2026-08-10 (Monday)
- **Planned**: 0 | **SMTP Accepted**: 0 | **Delivery rate**: N/A
- **⚠️ 5 consecutive days without sends** (Aug 6-10) since Aug 5 40-email batch
- **Open Signals**: 0 (tracking cache stale since Jul 30; 2 total open signals all-time)
- **Replies**: 0 human, 0 auto | **Bounces**: 0 new on Aug 10 | **Unsubs**: 0
- **Inventory**: 738 total | 48 Broad Outreach Ready orgs (48 locations) | 0 Strict A0 ⚠️ CRITICAL
  - Broad Ready stable at 48 orgs — inventory not being consumed (no sends), not being replenished
  - Strict A0 = 0 for 4th consecutive day (since Aug 7)
  - 29 leads have auto_sendable=1 but most already sent; 18 A-confidence unsent leads all have auto_sendable=0
  - Manual review pending: 254 (bd_ops_api) / 267 (report query) / 290 (dashboard)
- **Primary states**: TN (177/35 cities, 5 sendable), AR (67/17 cities, 4), KY (66/20 cities, 1), OR (25/4, 8), NC (20/7, 2)
- **Dashboard**: regenerated via bd_dashboard_v3.2.py (290 manual pending, 0 A0 sendable, 191 follow-up sendable)
- **Data Freshness**: FRESH (bounce scan Aug 10 17:35 MST, ~19 min ago)
- **Delivery Outcome**: SMTP 448 total, 234 in 30d; domain_invalid=22, hard=6, policy=3, unmatched_dsn=21, unresolved=392
- **Script fix**: broad_outreach_gate analyze_all_leads expects connection object, not path string (fixed in _daily_readonly_report.py); corrected key names from broad_outreach_ready→broad_org_opportunities
- **Output**: auto_report_2026-08-11.md, auto_report_2026-08-11.json, bd_operations_dashboard.html

## 2026-08-08 08:51 CST
- **Batch analyzed**: 2026-08-07 (Friday)
- **Planned**: 0 | **SMTP Accepted**: 0 | **Delivery rate**: N/A
- **⚠️ 2 consecutive days without sends** (Aug 6-7) after Aug 5 40-email batch
- **Open Signals**: 0 | **Replies**: 0 human, 0 auto | **Bounces**: 0 new | **Unsubs**: 0
- **⚠️ Aug 5 batch bounce scan (Aug 7)**: 14 bounces from 40 sends (35% bounce rate)
  - 12 domain_invalid + 2 unresolved — mostly guessed_email info@ addresses to invalid domains
  - Bounced stores: Things From Another World (OR), Kidding Around (NY), Game Parlour (CA), Game Cafe (CA), Phoenix Comics & Games (WA), JP Comics & Games (MA), Levels Up Games (MN), Phantom of the Attic (PA), Uncle Bob's Hobbies (NC), Dr. No's Comics & Games (GA), Gamezone (CA), Gamers Geek and Tavern (NC), Village Toymaker (TN), Comic Book World Florence (KY)
- **Inventory**: 738 total | 48 Broad Outreach Ready (orgs) | 0 Strict A0 ⚠️ | 254 manual review (bd_ops_api)
  - Strict A0 dropped 1→0 — either consumed or reclassified
  - Broad Ready dropped 78→48 — 30 consumed by sends/bounces since Aug 5 report; no new replenishment
  - 192 exception_review leads (no email) — biggest inventory blocker
- **Primary states**: TN (177/35 cities, 5 sendable), AR (67/17 cities, 4 sendable), KY (66/20 cities, 1 sendable)
- **Dashboard**: regenerated via bd_dashboard_v3.2.py (260 manual pending, 0 A0 sendable, 191 follow-up sendable)
- **Data Freshness**: FRESH (bounce scan 08:35 CST, 17 min ago)
- **Delivery Outcome**: SMTP 448 total, 264 in 30d; domain_invalid=22, hard=6, unmatched_dsn=21, unresolved=392
- **Key issues**:
  1. 35% bounce rate on Aug 5 batch — guessed_email strategy produces high invalid-domain rate
  2. Strict A0 = 0 — critical, no high-confidence auto-sendable inventory
  3. Tracking gap: only 4/40 Aug 5 sends have tracking_message_id; D1 returns 403
  4. Broad Ready at 48 orgs — sufficient for ~2 days of sending if orchestrator runs
  5. 192 exception_review leads = 192 leads with no email — cannot send without email discovery

## 2026-08-12 23:59 CST (automated run, late)
- **Batch analyzed**: 2026-08-11 (Tuesday)
- **Planned**: 0 | **SMTP Accepted**: 0 | **Delivery rate**: N/A
- **⚠️ 6 consecutive days without sends** (Aug 6-11) — last send was Aug 5 (40-email batch). Today is day 7.
- **Open Signals**: 0 (poller_cache stale since Jul 30 — only 2 test signals; tracking_message_id linkage gap persists)
- **Replies**: 0 human, 0 auto | **Bounces**: 0 hard | **Unsubs**: 0
- **Inventory**: 749 total (+11 from 738) | 55 Broad Outreach Ready orgs/55 locs (up from 48) | 0 Strict A0 ⚠️ CRITICAL (8th day at 0)
  - Manual review pending: 267 (review_status=pending) / 222 (status=manual_review_needed) / 254 (bd_ops_api)
  - Previously sent: 427 | Suppressed: 18
- **Primary states**: TN (181/38 cities, 6 sendable), KY (72/23, 4), AR (68/18, 1) — KY now ahead of AR
- **Dashboard**: regenerated via bd_dashboard_v3.2.py (295 manual pending, 0 A0 sendable, 243 follow-up sendable)
- **Ops API**: today planned_new=0 sent_new=0 replies=0 hard_bounces=0; inventory status=critical (strict_a0_orgs=0)
- **Data Freshness**: FRESH (bounce scan 23:40 CST, 18 min ago)
- **Delivery Outcome**: SMTP 448 total, 234 in 30d; domain_invalid=22, hard=6, policy=3, unmatched_dsn=21, unresolved=392; auto_reply=1
- **Note**: review_server (port 8765) NOT running — /api/ops/* endpoints and dynamic bd_ops_dashboard.html not live; static dashboard regenerated instead
- **Script**: new _daily_results_readonly.py (clears bd_ops_api cache + get_today_stats/get_inventory + broad gate + dashboard regen)

## 2026-08-13 08:52 CST (automated run)
- **Batch analyzed**: 2026-08-12 (Wednesday)
- **Planned**: 0 | **SMTP Accepted**: 0 | **Delivery rate**: N/A
- **⚠️ 7 consecutive days without sends** (Aug 6-12) — last send Aug 5 (40-email batch). Confirmed last send_at = 2026-08-05T22:59:59+08:00.
- **Open Signals**: 0 (poller_cache stale Jul 30; total_open_signals=2 test-only) | **Replies**: 0 | **Bounces**: 0 | **Unsubs**: 0
- **Inventory**: 749 total (unchanged) | 55 Broad Outreach Ready orgs/55 locs | 0 Strict A0 ⚠️ CRITICAL (9th day at 0)
  - auto_sendable=1 not-yet-sent = 4 (all fail Strict A0 gate — not confidence A + verified)
  - Manual review pending: 267 (review_status=pending) / 222 (status=manual_review_needed) / 254 (bd_ops_api)
  - Previously sent: 427 | Suppressed: 18
- **Primary states**: TN (181/38 cities, 6 sendable), KY (72/23, 4), AR (68/18, 1), OR (25/4, 6), NC (20/7, 2)
- **Collection progress**: active_city=Nashville, active_state=Tennessee, city_status=CONTACT_ENRICHMENT_IN_PROGRESS, queries 1/20 executed, current="board game store" (google_places), raw_records=0
- **Ops API**: today(08-13) planned_new=0 sent_new=0 replies=0 hard_bounces=0; inventory status=critical (strict_a0_orgs=0)
- **Data Freshness**: FRESH (bounce scan 08:35 CST, 16min ago)
- **Dashboard**: static regen via bd_dashboard_v3.2.main() → output/bd_operations_dashboard.html (295 manual, 0 A0, 243 follow-up sendable)
- **Note**: review_server (port 8765) NOT running — /api/ops/today & /api/ops/inventory dynamic endpoints down; static dashboard used
- **Key issues**: 1) 7-day send drought; 2) Strict A0=0 for 9 days; 3) Nashville enrichment in progress but 0 raw records

## 2026-08-14 08:51 CST (automated run)
- **Batch analyzed**: 2026-08-13 (Thursday)
- **Planned**: 0 | **SMTP Accepted**: 0 | **Delivery rate**: N/A
- **⚠️ 8 consecutive days without sends** (Aug 6-13) — last send Aug 5 (40 emails). No sends yesterday.
- **Open Signals**: 0 (poller_cache stale Jul 30; total_open_signals=2 test-only) | **Bounces**: 0 | **Unsubs**: 0
- **🔴 NEW CRITICAL BUG — reply_log false positives**: "Human Replies=359" is bogus. All 359 `customer_reply` rows have `lead_id=0` + `email=ianyf@roktandrazo.com` + summary "From: Ian <ianyf@roktandrazo.com> | Subject: Premium puzzles" — the reply monitor is scanning Ian's OWN Sent mailbox and logging outbound mail as customer_reply. Real organic replies = 0 (only other reply_log row is lead_id=237 auto_reply_ooo dated 2026-06-25).
- **Leads jumped 749→1017 (+268)**: 268 leads collected on 08-13 (Nashville enrichment ran). total_leads=1017.
- **Inventory**: 60 Broad Outreach Ready orgs/60 locs (up from 55) | 0 Strict A0 ⚠️ CRITICAL (10th day at 0) | manual review: 515 (review_status=pending w/ reason) / 487 (status=manual_review_needed); raw review_status=pending=1005 | previously sent 427 | suppressed 18
- **Primary states**: TN (189/39 cities, 6 sendable), KY (80/24, 5), AR (79/20, 3), OR (25/4, 6), NC (45/26, 2)
- **Dashboard**: regenerated via bd_dashboard_v3.2.main() → output/bd_operations_dashboard.html (Manual Review 560, 1 A0 sendable, 243 follow-up sendable, SMTP 448/194 30d, Reconciliation any_failed=True)
- **Collection config**: active_city=Nashville, active_state=Tennessee (active_city_state=TN), city_selector_mode=primary_state_only, primary_state_pool=[TN,AR,KY], backup=[FL,UT,SC]
- **Output**: auto_report_2026-08-14.md, auto_report_2026-08-14.json, bd_operations_dashboard.html
- **Key issues**: 1) 8-day send drought; 2) Strict A0=0 (10 days); 3) reply monitor misclassifying own sent mail as customer_reply (needs fix); 4) Reconciliation any_failed=True

## 2026-08-18 08:52 CST (automated run)
- **Batch analyzed**: 2026-08-17 (Monday)
- **Planned**: 0 | **SMTP Accepted**: 0 | **Delivery rate**: N/A
- **⚠️ 3-day drought** (Aug 15-17) — last send was Aug 14 P1.2 batch (20 emails)
- **Open Signals**: 0 (poller_cache stale Jul 30; total=2 test-only) | **Replies**: 0 | **Bounces**: 0 new | **Unsubs**: 0
- **✅ reply_log false-positive FIXED**: reply_log now 1 row only (lead_id=237 auto_reply_ooo 2026-06-25); the 359 bogus self-mail rows (lead_id=0/ianyf@) are GONE — reply monitor cleaned
- **🔴 Aug 14 P1.2 batch (20 emails) bounce audit**: 18 bounce records = 12 domain_invalid + 3 unresolved + 2 mailbox_invalid + 1 policy_bounce (~90% bounce rate). Only 5 clean: Well Played (NC), Mystic Falls Cardboard (GA), Village Tinker (TN), The Game Store (AR), Stoney's Gift & Toy (KY). bounce scan continued finding new bounces through 08-18 08:35
- **Inventory**: 1020 total (+3 from 1017) | 53 Broad Outreach Ready orgs/53 locs (down from 60) | 0 Strict A0 ⚠️ CRITICAL (~14th day at 0) | manual: 515 (review_status=pending) / 465 (status) / 254 (bd_ops_api) | prev_sent=447 | suppressed=45
- **Primary states**: TN (189/39, 6 sendable), KY (80/24, 4), AR (80/20, 3), OR (25/4, 6), NC (45/26, 1)
- **Collection**: Nashville TN, CONTACT_ENRICHMENT_IN_PROGRESS, queries 5/40 executed (web_directory), current="board game store", raw_records=0 (enrichment stuck — same as 08-13/14)
- **Dashboard**: regenerated → output/bd_operations_dashboard.html (Manual Review 538, 0 A0 sendable, follow-up 251 sendable, SMTP 468/180 30d, domain_invalid=34 hard=6 unmatched_dsn=36 unresolved=379, Reconciliation 2 batches any_failed=True)
- **Data Freshness**: FRESH (bounce scan 08:35 CST, 16min ago)
- **Key issues**: 1) 3-day drought after P1.2; 2) Strict A0=0 ~14 days; 3) P1.2 bounce rate ~90% (guessed info@ emails to invalid domains) — bounce source must be governed before next batch; 4) Nashville enrichment producing 0 records
