# BD Daily Collection Report — Automation Memory

## 2026-08-05 20:30 Asia/Shanghai

**Status**: Report generated successfully. Read-only, no writes.

**Key metrics**:
- Final Sendable Unsent: 79 (Strict A0: 1, Broad Outreach Ready: 78)
- Gap to 30: 0 | Gap to 60: 0
- New orgs today: 0 | Website emails: 0 | Facebook emails: 0 | Manual verified: 0
- Inventory: 718 total leads (170 TN, 62 AR, 58 KY)
- send_log total sent: 428 (+20 from overnight batch), send_plan today: 0
- Website recovery: 71 pending, 0 recheck_pending
- Network errors: 0
- Nashville queries: 22/22 complete, 33 orgs discovered

**Safety**: Read-only confirmed — send_plan=0, no new writes. 20 SMTP sends predate report (overnight batch). Inventory running.

**Deliverables**:
- output/daily_collection_reports/2026-08-05.json
- output/daily_collection_reports/2026-08-05.md
- Ops Center Dashboard regenerated (bd_dashboard_v3.2.py)

**Changes from 08-04**: Strict A0 dropped from 2→1, Broad Ready dropped from 11→78? No — previous report counted differently (95 broad ready on 08-03, 11+2=13 on 08-04). send_log grew from 408→428.

## 2026-08-04 20:30 Asia/Shanghai

**Status**: Report generated successfully. Read-only, no writes.

**Key metrics**:
- Final Sendable Unsent: 13 (Strict A0: 2, Broad Outreach Ready: 11)
- Gap to 30: 17 | Gap to 60: 47
- New orgs today: 0 | Website emails: 0 | Facebook emails: 0 | Manual verified: 1
- Inventory: 718 total leads (170 TN, 62 AR, 58 KY)
- send_eligibility: 95 broad_outreach_ready, 1 blocked
- Website recovery: 71 no-email-with-website, 0 recheck_pending
- Network errors: 2 other, 1 dns, 1 connection
- send_log total sent: 408

**Safety**: All checks passed — SMTP=0, send_plan=0, send_log entries today=0, inventory running.

**Deliverables**:
- output/daily_collection_reports/2026-08-04.json
- output/daily_collection_reports/2026-08-04.md
- Ops Center Dashboard regenerated

## 2026-08-03 20:30 Asia/Shanghai

**Status**: Report generated successfully. Read-only, no writes.

**Key metrics**:
- Final Sendable Unsent: 95 (↑87 from noon), all broad_outreach_ready
- Gap to 30: 0 | Gap to 60: 0
- New orgs today: 0 | Emails found: 0 | Manual verified: 0
- Inventory: 718 total leads, 622 unclassified for send_eligibility
- ALLOWED state sendable: 11 (OR:6, NC:3, MN:2)
- Website recovery: 0 recheck_pending, 72 no-email-with-website
- send_log: 411 (unchanged, 0 today)

**Safety**: All checks passed — SMTP=0, send_plan=0, send_log unchanged, inventory not stopped.

**Deliverables**:
- output/daily_collection_reports/2026-08-03.json
- output/daily_collection_reports/2026-08-03.md
- Ops Center Dashboard regenerated (bd_dashboard_v3.2.py)
