# RoktRazo BD Inventory — 15:00 Automation History

## 2026-07-23 15:00
- **Status**: partial (all_lanes_exhausted)
- **A0**: 12 → 15 (+3), target 60, gap 45
- **Review Recovery**: 27 known brands already in DB, no new inserts
- **Lanes executed**: Retail (3 leads, +1), Institutions (4, +0), Online Brands (35, +1), HTTP-first (24, +1)
- **SSL errors**: 121, timeouts: 33 — severe connectivity issues
- **Custom C pool**: 55 leads moved to contact_form_pool
- **Warning**: 3 A0 additions have questionable emails (bot/anthropic, sentry/wix, image filename) — hygiene gate needs strengthening
- **Recovery replay**: ran before main pipeline, confirmed all 27 known brands already in DB
- **Facebook enrichment**: skipped (browser not available in automation)

## 2026-07-29 15:00
- **Status**: complete (all_lanes_exhausted, discovery_blocked)
- **A0**: 1 → 3 (+2), target 120, gap 117
- **Orchestrator run**: Lane A discovery blocked (configuration_blocked), staging empty, 5 loops exhausted on Nashville contact_form_pool (2 leads, no emails found)
- **Manual inventory**: Near-A0 fixes (+1 B Side Games evidence_method repair), Memphis Sunny Toys upgrade (+1), Nashville 3 B-grade leads failed SSL (VPN proxy broken)
- **City advancement**: Nashville → search_matrix_exhausted (discovery blocked, lanes exhausted), Memphis now active
- **Review Center**: 213 manual_review_needed + 72 contact_form_pool = 285 pending
- **Organization Outreach Opportunities**: 195 total (13 in TN allowed states)
- **Blocker**: Astrill VPN HTTPS proxy SSL EOF errors prevent all website verification; Google Places API not configured; no staging imports

## 2026-07-30 15:00
- **Status**: partial (discovery_blocked, pool_drained, max_loops_reached)
- **A0**: 0/120, gap 120 — CRITICAL. Pool completely drained; all 3 A0 leads (#316, #531, #671) sent 2026-07-29, now excluded by send_log gate
- **Orchestrator run**: active city Memphis, Lane A discovery configuration_blocked, staging empty, 5 loops on 1 Memphis contact_form_pool candidate → 0 emails found
- **Broad Ready**: 99 locations, 99 orgs, 99 Organization Outreach Opportunities
- **Near-A0 candidates**: 18 leads have emails but auto_sendable=0 (8 with real emails upgradeable, 10 bad emails)
- **B-grade no email**: 11 leads in AR/TN — all missing both email AND website URL
- **City queue**: Nashville complete → Memphis active → Knoxville pending. No advance needed (Memphis still in progress)
- **Review Center**: 142 exception_review (no email) + 20 contact_form_only = 162 pending
- **Blockers unchanged**: Google Places API, VPN proxy SSL, no staging imports. No SMTP invoked.

## 2026-07-31 15:00
- **Status**: partial (discovery_blocked, pool_drained, all_lanes_exhausted)
- **A0**: 0/120, gap 120 — unchanged. All 3 strict A0 sent 07/29, excluded by send_log gate
- **Orchestrator run**: City queue bug — jumped to Louisville bypassing Memphis/Knoxville; Lane A configuration_blocked, staging empty, 0 candidates
- **City queue fix**: Louisville/Lexington reset to pending; Memphis retained at partial_collection_done
- **Broad Outreach**: 95 orgs / 95 locations (95 Organization Outreach Opportunities), 11 in allowed states (OR 6, NC 3, MN 2)
- **send_eligibility**: Written to 95 leads as 'broad_outreach_ready'
- **Organization keys**: 569 patched via _gen_organization_key
- **Memphis email extraction**: 5 B-grade leads scanned, 0 emails found (3 no email on page, 1 SSL EOF, 1 Facebook page)
- **Review Center**: 334 pending (261 manual_review_needed + 73 contact_form_pool)
- **Near-A0**: 342 leads with A-grade email but not strict A0 (only ~16 in allowed states)
- **No SMTP invoked, no Final Send Plan created**

## 2026-08-01 15:00
- **Status**: partial (discovery_blocked, pool_drained, all_lanes_exhausted)
- **A0**: 0/120, gap 120 — all 4 strict A0 (#316,#531,#671,#530) sent 07/29 or earlier
- **Orchestrator run 1**: City queue bug reoccurred — Louisville activated instead of Memphis. Root cause identified: `activate_next_city()` only selects `status='pending'` cities; Memphis was `partial_collection_done`
- **Fix applied**: Deactivated Louisville, activated Memphis (partial unique index `idx_retail_city_only_one_active` on `status='active'` requires at most 1 active city at a time)
- **Orchestrator run 2**: Memphis active, 3 B-grade candidates found, all failed — 3 sites no email extraction (comiccellaronline.com empty, 901comics.com is Chinese company, extremetoysmemphis.com SSL EOF), 1 contact_form_pool (memphistoyexchange.com SPA no static content)
- **City queue state**: Nashville→search_matrix_exhausted, Memphis→active, Knoxville→pending, Little Rock/Fayetteville→partial_collection_done, Louisville/Lexington→pending
- **Broad Outreach**: 95 orgs (95 Organization Outreach Opportunities), 11 in allowed states (OR 6, NC 3, MN 2)
- **Review Center**: 333 pending (259 manual_review_needed + 74 contact_form_pool)
- **Near-A0**: 343 candidates, 179 in allowed states — untapped pool for upgrades
- **Memphis A-grade**: #531 Sunny Toys (email micah@micahrich.com flagged as DOMAIN_MISMATCH/invalid — font attribution, already sent), #683 901 Comics Midtown (email_verified_on_official_site=0, new, not yet sendable)
- **Blockers**: Google Places API not configured, Astrill VPN SSL proxy breaks HTTPS, all Memphis sites dead ends
- **No SMTP invoked, no Final Send Plan created**

## 2026-08-02 15:00
- **Status**: partial (discovery_blocked, all_lanes_exhausted, city_advanced)
- **A0**: 0→4/120 (via send_log exclusion fix), gap 116 — 4 unsent A0 found (#691,#695,#735,#739) not in send_log
- **All A0 (raw)**: 24 (20 sent & excluded by send_log)
- **Orchestrator run**: Lane A configuration_blocked, staging empty, 5 loops on 3 Memphis B2 candidates — all SSL EOF (extreme_toys x5)
- **City advancement**: Memphis → search_matrix_exhausted (5 candidates SSL-blocked x5+ days), Knoxville activated (0 B+candidates with websites — all 5 B-grade lack website URLs)
- **Broad Outreach**: 95 orgs (11 in allowed states: OR 6, NC 3, MN 2)
- **Organization Outreach Opportunities**: 99 (4 A0 + 95 Broad, unique union)
- **Review Center**: 333 pending (260 manual_review_needed + 73 contact_form_pool)
- **Near-A0**: 10 in allowed states with email but auto_sendable=0 (6 bogus, 4 real)
- **B-grade w/ email**: 20 in allowed states (upgrade pool)
- **Next actionable city**: Lexington, KY (4 B+candidates w/ websites)
- **Blockers unchanged**: Google Places, Astrill VPN SSL, no staging
- **No SMTP invoked, no Final Send Plan created**

## 2026-08-03 15:00
- **Status**: partial (discovery_blocked, all_lanes_exhausted, city_advanced)
- **A0**: 0/30 (weekday target), gap 30. Dashboard shows 9 A-grade (7 retail+2 custom), sendable_leads gate=0
- **Website Recovery**: 35 candidates scanned (TN/AR/KY) → 4 emails found (3 previously_sent, 1 bogus sentry/wix), 20 no email, 7 network errors properly classified, 4 platform skips. 0 new emails added to sendable pool
- **Orchestrator**: Lane A discovery hung (Google Places 20min), killed. Ran manual inventory
- **City**: Knoxville→search_matrix_exhausted (0 websites), Little Rock AR activated. Remaining: Fayetteville AR, Louisville KY, Lexington KY
- **Broad Outreach**: 95 orgs
- **Review Center**: 333 pending (260 manual+73 contact_form). 23 have emails in allowed states
- **Near-A0**: 13 in TN/AR/KY w/ email but auto=0 (mostly bogus)
- **No SMTP, no Final Send Plan**

## 2026-08-05 15:00
- **Status**: partial (max_loops_reached, pool_drained)
- **A0**: 1/30 (weekday target), gap 29 — unchanged
- **Orchestrator run**: Active city Nashville TN, Lane A configuration_blocked, staging empty, 5 loops × 34 candidates
- **Emails found**: 3 — info@indiantypefoundry.com (Middle TN Gam), customercare@easternnational.org ×2 (Shiloh NMP + Cumberland Gap NHP) — all previously_sent
- **No email**: 20 consistently no-email across all 5 loops
- **Network errors (properly classified)**: 7 persistent — Turtles Nest Toys, Old Black Mountain Games, Dewaynes World Comics, Extreme Toys, Puzzles Plus, Treasure Chest Games, Go Toys Games Calendars. Loop 4: Fort Loudoun also flipped to network_retry_pending
- **Platform skips**: 4 — 901 Toys, CM Games Morristown, CM Games Lexington, Matts Games Collectibles
- **No SMTP, no Final Send Plan**
- **Blockers unchanged**: Google Places API, Astrill VPN, no staging. Pool completely drained — same 34 leads returning identical results across all loops

## 2026-08-04 15:00
- **Status**: partial (discovery_blocked, all_lanes_exhausted, max_loops_reached)
- **A0**: 1/30 (weekday target), gap 29. Raw DB shows 28 auto_sendable=1 leads but orchestrator gate filters most out (send_log exclusion, state filter, etc.)
- **New A0 promoted**: #689 The Crown Shop (shop@thecrownshop.com, Little Rock AR) — promoted to strict A0 via http_success on loop 1
- **Website Recovery**: 35 candidates × 5 loops → 4 unique emails found: jeff@midtngaming.com (previously_sent), customercare@easternnational.org ×2 (previously_sent, Shiloh NMP + Cumberland Gap), shop@thecrownshop.com (NEW A0). 20 consistently no-email, 11 persistent network errors, 4 platform skips
- **Network errors (persistent ×5 loops)**: Turtles Nest Toys, Old Black Mountain Games, Dewaynes World Comics & Games, Extreme Toys, Puzzles Plus, Treasure Chest Games, Go Toys Games Calendars (7 sites) — all properly classified as network_retry_pending, NOT "no email"
- **Platform skips**: 901 Toys, CM Games Morristown, CM Games Lexington, Matts Games Collectibles
- **Lane A discovery**: configuration_blocked (Google Places API not configured)
- **Lane B/C/D staging**: empty
- **City**: Nashville TN → CONTACT_ENRICHMENT_IN_PROGRESS (city cursor apparently reset from prior Little Rock by seed_default_queue)
- **Remaining cities**: Memphis (CONTACT_ENRICHMENT_IN_PROGRESS), Knoxville (search_matrix_exhausted), Little Rock/Fayetteville/Louisville/Lexington (QUEUED)
- **Broad Outreach**: 95 orgs
- **Review Center**: 334 pending (261 manual + 73 contact_form)
- **Dependency fix**: httpx was missing in venv — installed for this run
- **No SMTP, no Final Send Plan**
