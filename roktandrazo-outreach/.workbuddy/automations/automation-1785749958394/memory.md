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

## 2026-08-18 20:31 Asia/Shanghai (evening run — 20:30 scheduled)

**Status**: Report generated. Read-only — 0 DB writes (before/after identical: leads 1043, send_log 472, final_send_plan 173, bounce_log 52, suppression_list 54). Essentially a re-snapshot ~4min after the 20:27 run; no data change.

**Key metrics** (identical to 20:27 run):
- Final Sendable Unsent: 37 (Broad 37, Strict A0 0) | Gap to 30=0 / Gap to 60=23 | Inventory LOW
- Total leads: 1043 | New orgs today: 23 | Website/Facebook/Manual emails: 0
- manual_review_needed: 467 | website_recovery_pending: 92 | contact_recovery_pending: 27
- send_log total: 472 (today 1) | final_send_plan total: 173 (today 11) | SMTP_enabled=0
- Network errors: 4 (hard bounce 2, DNS 1, connection reset 1) | Bounces today: 3 (unresolved)
- Active: TN / Nashville. Discovery queue front: Atlanta GA / Birmingham AL / Richmond VA (priority 30). Query pending 407 / completed 29 / config_blocked 3 / provider_timeout 1. Latest pending: "card game store Jackson MS". No in_progress (provider blocked).

**Safety**: read-only ✓. Strict "Final Send Plan=0" → FAIL (11 production entries today at 01:51 CST, +1 send 09:21). SMTP channel=0 ✓. send_log unchanged by this run (472) ✓. Inventory running (DB mtime 20:28).

**Ops Center**: 8765 listening (HTTP 200); live api/ops/summary generated_at 20:31, inventory.status=critical (Ops Center's own gap model to 40/80/120). Static dashboard regenerated via bd_dashboard_v3.2.py; Data Freshness FRESH (last_bounce_scan_at 20:28).

**Deliverables**:
- output/daily_collection_reports/2026-08-18.json
- output/daily_collection_reports/2026-08-18.md
- output/bd_operations_dashboard.html (regenerated) + manual_review_queue.json + followup_rotation_status.json

## 2026-08-18 20:27 Asia/Shanghai (evening run)

**Status**: Report generated. Read-only — 0 DB writes (before/after identical: leads 1043, send_log 472, final_send_plan 173, bounce_log 52, suppression 54).

**Key metrics**:
- Final Sendable Unsent: 37 (Broad 37, Strict A0 0) — unchanged vs 08-17; Gap to 30=0 / Gap to 60=23; Inventory LOW
- Total leads: 1043 (+23 vs 08-17 1020) | New orgs today: 23 | Website/Facebook/Manual emails today: 0
- New leads today span MO/NC/OR/PA/WA/AL/CO/IN (discovery still expanding beyond ALLOWED_STATES)
- manual_review_needed: 467 (+2) | website_recovery: 92 (-2) | contact_recovery: 27 | email_missing: 461 (-2)
- send_log total: 472 (+1) | send_log today: 1 | final_send_plan total: 173 (+11) | final_send_plan today: 11
- SMTP_enabled = 0 (channel off)
- Network errors: 4 (hard bounce 2, DNS 1, connection reset 1)
- Bounces today: 3 (all 'unresolved', null diagnostic) at 08:35 — morning IMAP scan stale notifications (gigabitescafe/deepcomics/gamedaymiami)

**⚠️ Production activity today (NOT caused by this run)**:
- 1 SMTP send at 09:21 CST: lead 1055 "Game Cafe" Independence MO → tom@playgamecafe.com (template_id='' empty, manual_verified_by=user). MO is outside ALLOWED_STATES. Flag for review.
- 11 final_send_plan entries today (01:51 CST, plan prefix `2026-08-18:new_outreach:`), all strict_a0: 9 planned + 1 sent + 1 cancelled. Suggests P17/P1.2 supervised batch active.

**Safety**: read-only integrity ✓ (0 writes). Strict "Final Send Plan=0" check → FAIL (11 production entries today). SMTP channel=0 ✓. send_log unchanged BY THIS RUN ✓ (before=after=472), but production +1 today.

**Ops Center**: 8765 NOW LISTENING (HTTP 200) — first time in recent runs. Live dashboard data confirmed current (api/ops/summary generated_at 20:27, today sent_new=1/planned_new=9). Static dashboard regenerated via bd_dashboard_v3.2.py. Data freshness now FRESH (last_bounce_scan_at 20:23, age 4min). Reconciliation: 1 legacy batch FAILED (new_outreach_20260805, 20 tracking_token_missing), 1 PASSED (p1_2_first20_20260813).

**Deliverables**:
- output/daily_collection_reports/2026-08-18.json
- output/daily_collection_reports/2026-08-18.md
- output/bd_operations_dashboard.html (regenerated) + manual_review_queue.json + followup_rotation_status.json

## 2026-08-20 20:31 Asia/Shanghai (evening run — 20:30 scheduled)

**Status**: Report generated. Read-only — 0 DB writes (before/after identical: leads 1066, send_log 482, final_send_plan 229, bounce_log 54, suppression_list 55).

**Key metrics**:
- Final Sendable Unsent: 37 (Broad 37, Strict A0 0) | Gap to 30=0 / Gap to 60=23 | Inventory LOW
- Total leads: 1066 (unchanged vs 08-19) | New orgs today: 0 | Website/Facebook/Manual emails: 0
- manual_review_needed: 488 | website_recovery_pending: 97 | contact_recovery_pending: 28 | email_missing: 480
- send_log total: 482 (today 0) | final_send_plan total: 229 (today 45) | SMTP_enabled=0
- Network errors: 4 (hard bounce 2, DNS 1, connection reset 1) | Bounces today: 0
- Active: TN / Nashville. Discovery queue front: Atlanta GA / Birmingham AL / Richmond VA (priority 30). Query pending 463 / completed 31 / config_blocked 4 / provider_not_configured 1 / provider_timeout 1. Latest pending: "card game store Ithaca NY". No in_progress.

**⚠️ Production activity today (NOT caused by this run)**: final_send_plan +45 entries today (was 184→229), all still `planned`/`cancelled`, SMTP=0 so nothing sent. Breakdown: `2026-08-20:new_outreach:199a9b0383` = 40 planned, `2026-08-20:follow_up:8354ac2a58` = 4 planned (follow-up re-enabled? flag), `canary_2026-08-20:new_outreach:81a9168fc8` = 1 cancelled.

**Safety**: read-only ✓. Strict "Final Send Plan=0" → FAIL (45 production entries today). SMTP channel=0 ✓. send_log unchanged by this run (482) ✓. Inventory running (DB mtime 15:11).

**Ops Center**: 8765 NOT listening (curl 000, no port in netstat). Static dashboard regenerated via bd_dashboard_v3.2.py; Data Freshness AGING (last_bounce_scan_at 15:11, age 320min). Reconciliation 2 batches any_failed=True. Schedule Preview 44 rows.

**Deliverables**:
- output/daily_collection_reports/2026-08-20.json
- output/daily_collection_reports/2026-08-20.md
- output/bd_operations_dashboard.html (regenerated) + manual_review_queue.json + followup_rotation_status.json

## 2026-08-19 20:32 Asia/Shanghai (evening run — 20:30 scheduled)

**Status**: Report generated. Read-only — 0 DB writes (before/after identical: leads 1066, send_log 482, final_send_plan 184, bounce_log 54, suppression_list 55).

**Key metrics**:
- Final Sendable Unsent: 37 (Broad 37, Strict A0 0) | Gap to 30=0 / Gap to 60=23 | Inventory LOW
- Total leads: 1066 (+23 vs 08-18 1043) | New orgs today: 23 | Website/Facebook/Manual emails: 0
- manual_review_needed: 488 (+21) | website_recovery: 97 (+5) | contact_recovery: 28 (+1) | email_missing: 480
- send_log total: 482 (today 10) | final_send_plan total: 184 (today 11) | SMTP_enabled=0
- Network errors: 4 (hard bounce 2, DNS 1, connection reset 1) | Bounces today: 2 (1 domain_invalid MX-not-found + 1 unresolved)
- Active: TN / Nashville. Discovery queue front: Atlanta GA / Birmingham AL / Richmond VA (priority 30). Query pending 444 / completed 31 / config_blocked 3 / provider_not_configured 1 / provider_timeout 1. Latest pending: "card game store Ithaca NY". No in_progress.

**Safety**: read-only ✓. Strict "Final Send Plan=0" → FAIL (11 production entries today, +10 sends). SMTP channel=0 ✓. send_log unchanged by this run (482) ✓. Inventory running (DB mtime 20:29).

**Ops Center**: 8765 listening (HTTP 200); live api/ops/summary generated_at 20:32, total_leads=1066 (matches snapshot). Static dashboard regenerated via bd_dashboard_v3.2.py; Data Freshness FRESH (last_bounce_scan_at 20:29, age 3min).

**Deliverables**:
- output/daily_collection_reports/2026-08-19.json
- output/daily_collection_reports/2026-08-19.md
- output/bd_operations_dashboard.html (regenerated) + manual_review_queue.json + followup_rotation_status.json

## 2026-08-21 20:31 Asia/Shanghai (evening run — 20:30 scheduled)

**Status**: Report generated. Read-only — 0 DB writes (before/after identical: leads 1066, send_log 496, final_send_plan 278, bounce_log 62, suppression_list 55).

**Key metrics**:
- Final Sendable Unsent: 29 (Broad 29, Strict A0 0) — ↓8 vs 08-20 (37→29); Gap to 30=1 / Gap to 60=31; Inventory LOW
- Total leads: 1066 (unchanged) | New orgs today: 0 | Website/Facebook/Manual emails: 0
- manual_review_needed: 480 (-8) | website_recovery_pending: 97 | contact_recovery_pending: 36 (+8) | email_missing: 480
- send_log total: 496 (+14) | send_log today: 5 | final_send_plan total: 278 (+49) | final_send_plan today: 5
- SMTP_enabled=0 | Network errors: 4 (hard bounce 2, DNS 1, connection reset 1) | Bounces today: 8
- Active: TN / Nashville. Discovery queue front: Atlanta GA / Birmingham AL / Richmond VA (priority 30). Query pending 463 / completed 31 / config_blocked 4 / provider_not_configured 1 / provider_timeout 1. Latest pending: "card game store Ithaca NY". No in_progress.

**⚠️ Production activity today (NOT caused by this run)**:
- 5 SMTP sends 11:59–12:04 CST, batch `2026-08-21:new_outreach:38419abaa0`, template retail_distributor_v5_locked, leads 1056–1060 (The Wyvern's Tale / Mage's Comics / Village Meeple / Meta-Games Unlimited / Ye Gamer's Guild). 5 final_send_plan entries status='sent'.
- 8 bounces today (08:51 CST IMAP scan), all `domain_invalid` / "type=MX: Host not found (html fallback)" — these are STALE PostMaster notifications for `info@` guessed domains (warhammermadison.com, collectiblecornermke.com, thirdplanet.com, crimsondragongames.com, beansandicecream.com, patinamn.com, gamegalaxysa.com, wondermenttoys.com), NOT today's 5 sends. Recurring stale-notification issue (same class flagged 08-14/08-18).

**Safety**: read-only ✓ (0 writes). Strict "Final Send Plan=0" → FAIL (5 production 'sent' entries today). SMTP channel=0 ✓. send_log unchanged by this run (496) ✓. Inventory running.

**Ops Center**: 8765 NOT listening (curl 000). Static dashboard regenerated via bd_dashboard_v3.2.py; Data Freshness AGING (last_bounce_scan_at 08-21 08:51, age ~700min). Reconciliation 2 batches any_failed=True. Schedule Preview 5 rows.

**Deliverables**:
- output/daily_collection_reports/2026-08-21.json
- output/daily_collection_reports/2026-08-21.md
- output/bd_operations_dashboard.html (regenerated) + manual_review_queue.json + followup_rotation_status.json
