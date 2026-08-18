# BD Daily Collection Report — Automation Memory

## 2026-08-12 11:29 Asia/Shanghai

**Status**: Report generated successfully. Read-only, no writes.

**Key metrics**:
- Final Sendable Unsent: 50 (Strict A0: 0, Broad Outreach Ready: 50) — ↑2 from 08-11 (48→50)
- Gap to 30: 0 | Gap to 60: 10
- New orgs today: 0 | Website emails: 0 | Facebook emails: 0 | Manual verified: 0
- Total leads: 738 (unchanged)
- Primary states: TN 177, AR 67, KY 66 (all unchanged)
- send_log total: 451 (unchanged), send_plan today: 0
- Website recovery: 74 pending (+3), contact_recovery: 15 pending
- Network errors: 4 (hard bounce 2, DNS 1, connection reset 1)
- Manual Review: 217 (unchanged)
- Broad unsent breakdown: 48 manual_review_needed + 2 bounced
- Inventory health: LOW (Sendable=50 < 60 threshold, gap to healthy = 10)
- No active discovery queries

**Key change**: Broad Outreach Ready unsent ↑2 (48→50). Two leads re-evaluated into broad_outreach_ready tier. Website recovery +3 (71→74). All other metrics frozen — no collection activity today.

**Safety**: Read-only confirmed — SMTP sends=0, send_plan=0, send_log unchanged. Inventory running.

**Bug fix**: Network errors now correctly sourced from leads.error_message (network_errors table missing). Previous reports showed 0 due to empty fallback.

**Deliverables**:
- output/daily_collection_reports/2026-08-12.json
- output/daily_collection_reports/2026-08-12.md
- Ops Center Dashboard regenerated (bd_dashboard_v3.2.py → output/bd_operations_dashboard.html)
- Ops Center (127.0.0.1:8765) unreachable — port not listening

## 2026-08-13 11:28 Asia/Shanghai

**Status**: Report generated successfully. Read-only, no writes.

**Key metrics**:
- Final Sendable Unsent: 50 (Strict A0: 0, Broad Outreach Ready: 50) — unchanged
- Gap to 30: 0 | Gap to 60: 10
- Total leads: 761 (+23 vs 08-12) — TN +5, AR +9, KY +9 (08-12 afternoon inventory ingestion)
- New orgs today (08-13): 0 | Website: 0 | Facebook: 0 | Manual verified: 0
- manual_review_needed: 236 (+19) | website_recovery: 88 (+14) | email_missing: 220 (+28)
- send_log total: 451 (unchanged) | send_plan today: 0 | final_send_plan today: 0 (table total 132)
- SMTP_enabled = 0
- Inventory health: LOW (Sendable=50 < 60)
- Discovery: Lexington KY queued front (retail_city_queue priority 21); lead_discovery_query_state 188 pending / 3 configuration_blocked / 0 in_progress — provider still blocked, no active execution

**Safety**: Read-only confirmed — SMTP=0, send_plan=0, final_send_plan=0, send_log unchanged (451). Inventory running (23 new leads since last report).

**Note**: Ops Center 8765 still not listening; dashboard refreshed via bd_dashboard_v3.2.py → output/bd_operations_dashboard.html.

**Deliverables**:
- output/daily_collection_reports/2026-08-13.json
- output/daily_collection_reports/2026-08-13.md
- output/bd_operations_dashboard.html (regenerated)

## 2026-08-13 20:28 Asia/Shanghai (evening run)

**Status**: Report generated. Read-only, no writes.

**Key metrics**:
- Final Sendable Unsent: 50 (Broad 50, Strict A0 0) — unchanged; Gap to 30=0 / Gap to 60=10; Inventory LOW
- Total leads: 1017 (+256 vs 11:27 morning's 761) — large afternoon ingestion (~16:43-16:44 CST batch)
- New orgs today: 268 (morning run wrongly showed 0 — see bug fix)
- Website/Facebook/Manual emails today: 0
- manual_review_needed: 487 (+251) | email_missing: 471 (+251) | website_recovery: 94 (+6)
- send_log total: 451 (unchanged) | send_log today: 0 | send_plan today: 0
- **final_send_plan today: 30** (20 'planned' active + 10 'superseded') — ⚠️ deviation from =0 expectation

**Safety**: SMTP=0 ✓, send_plan=0 ✓, send_log unchanged ✓, but **final_send_plan today = 30 (NOT 0)** → safety `pass` = false. Not caused by this read-only run; a P1 supervised send plan (plan_p1_supervised_20260813) was created earlier today (09:15 CST) with 20 active 'planned' entries, none yet sent (SMTP=0).

**Key change**: Discovery expanded beyond ALLOWED_STATES — city queue front now Atlanta GA / Birmingham AL / Richmond VA (priority 30); 268 new leads span GA/FL/IL/VA/MO/OK/LA/AL/SC/MS + OH(+43)/NC(+25).

**Bug fix**: `new_orgs_today` returned 0 because `collected_at` uses ISO-8601 'T' format (2026-08-13T16:44:24+08:00) while the script's range used naive 'YYYY-MM-DD HH:MM:SS' (space). Switched the four "today" activity queries to `date(<col>) = ?`. Now correctly 268.

**Ops Center**: 8765 still not listening; dashboard refreshed via bd_dashboard_v3.2.py → output/bd_operations_dashboard.html.

**Deliverables**:
- output/daily_collection_reports/2026-08-13.json (overwritten with evening snapshot)
- output/daily_collection_reports/2026-08-13.md
- output/bd_operations_dashboard.html (regenerated)

## 2026-08-14 20:30 Asia/Shanghai (evening run)

**Status**: Report generated. Read-only — 0 DB writes (verified before/after: send_log 471, final_send_plan 162, leads 1017, bounce_log 49 all unchanged).

**Key metrics**:
- Final Sendable Unsent: 37 (Broad 37, Strict A0 0) — ↓13 from 08-13 (50→37); Gap to 30=0 / Gap to 60=23; Inventory LOW
- Total leads: 1017 (unchanged) | New orgs today: 0 | Website/Facebook/Manual: 0
- manual_review_needed: 473 (-14) | website_recovery: 94 | contact_recovery: 27
- send_log total: 471 (+20) | final_send_plan total: 162 (142 sent + 10 superseded + 10 cancelled)
- SMTP_enabled = 0

**⚠️ Major event — P1 supervised release executed today**:
- **20 emails sent today** (08-14 09:34–09:52 CST) via plan `p1_2_first20_20260813`, all strict_a0 segment, templates ccb51505 (19) + 5893dbc9 (1). post_send_reconciliation = PASSED (0 issues).
- **15 bounces within ~2h** (11:48–11:49 CST) — 75% bounce rate: 12 domain_invalid (MX: Host not found = nonexistent domains), 2 mailbox_invalid, 1 policy_bounce. **Red flag: strict_a0 emails were NOT MX-verified** — info@guessed domains.
- 13 of the 20 sent leads were previously broad_outreach_ready (explains Final Sendable ↓13).

**Bug fix (report generator)**: `send_log_today`/`send_plan_today`/`final_send_plan_today` used naive 'YYYY-MM-DD HH:MM:SS' range and silently missed ISO-8601 'T' timestamps → wrongly reported 0 sends today (same bug class as new_orgs_today, fixed 08-13). Now use `date(<col>)=?`. `send_plan` table does NOT exist — plan tracking lives in `final_send_plan`. Added "Bounces Today (classified)" section.

**Safety**: SMTP channel=0 ✓, no new final_send_plan today ✓, send_log NOT changed by this run ✓. The 20 sends / 15 bounces are production activity, not this automation.

**Ops Center**: 8765 still not listening; dashboard refreshed via bd_dashboard_v3.2.py → output/bd_operations_dashboard.html.

**Follow-up needed (bounce auditor)**: investigate why 12 strict_a0 leads passed hygiene with unverifiable domains; email_verified flag / MX check bypass suspected.

**Deliverables**:
- output/daily_collection_reports/2026-08-14.json
- output/daily_collection_reports/2026-08-14.md
- output/bd_operations_dashboard.html (regenerated)

## 2026-08-17 20:26 Asia/Shanghai (evening run)

**Status**: Report generated. Read-only — 0 DB writes (before/after identical: leads 1020, send_log 471, final_send_plan 162, bounce_log 49, suppression 53).

**Key metrics**:
- Final Sendable Unsent: 37 (Broad 37, Strict A0 0) — unchanged vs 08-14; Gap to 30=0 / Gap to 60=23; Inventory LOW
- Total leads: 1020 (+3 vs 08-14 1017) | New orgs today: 3 | Website/Facebook/Manual emails today: 0
- manual_review_needed: 465 (-8) | website_recovery: 94 | contact_recovery: 27 | email_missing: 463
- send_log total: 471 (unchanged) | send_log today: 0 | final_send_plan total: 162 | final_send_plan today: 0
- SMTP_enabled = 0
- Network errors: 4 (hard bounce 2, DNS 1, connection reset 1)
- Active state TN / city Nashville. Discovery city queue front: Atlanta GA / Birmingham AL / Richmond VA (priority 30). Query status: 408 pending / 29 completed / 3 configuration_blocked. Latest pending: "card game store Jackson MS". No in_progress query (provider blocked).

**Note**: No 08-15 / 08-16 reports exist → `_delta_vs` null, delta column shows raw values (no day-over-day comparison).

**Safety**: SMTP=0 ✓, send_plan today=0 ✓, final_send_plan today=0 ✓, send_log unchanged (471) ✓. Inventory running.

**Ops Center**: 8765 still not listening (curl 000); dashboard refreshed via bd_dashboard_v3.2.py → output/bd_operations_dashboard.html (+ manual_review_queue.json, followup_rotation_status.json). Dashboard flags DATA STALE (last_bounce_scan_at 08-14, age ~4831min).

**Deliverables**:
- output/daily_collection_reports/2026-08-17.json
- output/daily_collection_reports/2026-08-17.md
- output/bd_operations_dashboard.html (regenerated)
