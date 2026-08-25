# RoktRazo BD Inventory — 15:00 Automation History

## 2026-08-19 15:00 (actual run 15:05–16:42 CST, completed clean 1h36m30s)
- **Status**: partial (max_loops_reached), BroadReady = 11/30 (A0=0), gap 19 — 12th consecutive zero-intake day (weekday target 30).
- **Active city**: Ithaca NY (state scope=NY). ⚠️ Discovery state has ADVANCED to NY (was TN/AR/KY through 08-18); retail_city_queue now has 17 Upstate NY cities (Ithaca active, 16 pending), seeded via `retail_city_queue.NY_FIRST_ROUND_CITIES` + `seed_state_cities`.
- **Lane A discovery BLOCKED (new root cause)**: `provider_not_configured` — web_directory `_DIRECTORY_PAGES` has NO "New York" entry, so `search_places` returns "no directory page for state NY" (0 leads). Google Places (default) also unconfigured. NY is not in allowed states (TN/AR/KY/OH/IN/MN/NE/NC/OR/CO) nor primary/backup pools. Lane B/C/D staging: empty.
- **Website Recovery**: 5 loops × 35 candidates → 0 emails. Per-loop: no_email≈24-25, network_err=10-11 (8 network_retry_pending + 2 skip_platform). Two NEW slow-timeout sites appeared (Aerobellum Games, Board Royale ~5min each) → stretched each loop to ~19min, total runtime ~96min (vs prior ~45min).
- **No SMTP**: 0 send_log writes during inventory window (verified). Today's 10 sends were all morning-outreach (09:15–09:25 CST). Lock released.
- **Review Center auto-classify (read-only)**: 14 manual_review_needed leads WITH email in allowed states → 0 A0 pass (all B2_manual_review). Top: business_identity_not_matched=14, official_site_email_not_verified=14, email_source_not_official=11, evidence_snippet_missing=11, state_out_of_scope=8.
- **FB queue**: 20 rows all terminal (no_facebook_link=7, failed_final=6, mismatch=5, no_facebook_final=2), 0 fb_email → 0 actionable (fb_worker.py browser worker not wired into inventory stage).
- **Dashboard refreshed**: Manual Review 536, Inventory 0 A0 (strict) / 11 BroadReady (main pool). Reconciliation any_failed=True.
- **🔴 LIMIT-31 counting bug (confirmed)**: `_count_broad_ready_pool(31)` = 11, but `_count_broad_ready_pool(1000)` = 64. The `LIMIT ?` applies to the CANDIDATE query (leads w/ email, non-excluded), so it only samples the first 31 by rowid → undercounts. TRUE BroadReady = 64 orgs (already ≥30 target). Distribution: 14 in allowed states (TN1/AR1/KY3/OR3/NC2/IN2/MN1/CO1) + 50 outside (WI7/WA7/UT6/CA4/TX4/PA4/AZ3/NV3/IL2/MO2/MI1/NY1/FL1/RI1/VT1/AL1/NJ1/Various1). The "gap 19"/"pool depleted" narrative is partly a counting artifact; real blocker = STATE SCOPE (whether non-allowed-state broad-ready orgs are sendable).
- **Action needed (unchanged, blocking — human decision)**: (1) fix `_count_broad_ready_pool` LIMIT-31 undercount; (2) decide whether broad-ready orgs outside allowed states are sendable (50/64); (3) NY discovery is un-serviceable — web_directory has no NY page, google_places unconfigured → either add NY directory page, revert active_discovery_state to a serviceable allowed state, or configure serpapi_maps/browser_maps + key.

## 2026-08-18 15:00 (actual run 14:58–15:46 CST, completed clean 47m14s)
- **Status**: partial (max_loops_reached), A0 = 0/30, BroadReady = 7/30, gap 23 — 11th consecutive zero-intake day (weekday target 30).
- **Active city**: Nashville TN (from system_config cursor, no hardcode, no state jump).
- **Provider**: `WORKBUDDY_DISCOVERY_PROVIDER=web_directory` (matches retail_city_queue.active_provider). Lane A: `provider_timeout` (query 'gift shop', seen=0, new_unique=0, leads=0) — web_directory now timing out rather than returning the exhausted state directory. Lane B/C/D staging: empty.
- **Website Recovery**: 5 loops × 35 candidates → 0 emails. Per-loop: no_email=26, network_err=9 (7 network_retry_pending + 2 skip_platform). Persistent network errors unchanged (Turtles Nest Toys, Old Black Mountain Games, Dewaynes World Comics, Extreme Toys, Puzzles Plus, Treasure Chest Games, Go Toys Games Calendars).
- **No SMTP** (today_sent_count=4 from morning only, unchanged). No Final Send Plan. No Send Authorization. Lock released, job_run=partial/f808c232.
- **Review Center auto-classify (read-only)**: 6 manual_review_needed leads with email in TN/AR/KY → 0 A0 pass (all B2_manual_review). Top reasons: third_party_email_domain=4, already_sent=4, business_identity_not_matched=3, email_source_not_official=3, official_site_email_not_verified=3.
- **FB queue**: 20 rows all terminal (no_facebook_link=7, failed_final=6, mismatch=5, no_facebook_final=2) → 0 actionable; needs browser worker (fb_worker.py) not wired into inventory stage.
- **Dashboard refreshed**: Manual Review 540 pending, Inventory 1 A0 (strict) / 7 BroadReady (main pool). Reconciliation any_failed=True (historical tracking_token_missing debt).
- **Root cause (unchanged, 11th day)**: TN/AR/KY pool structurally depleted; web_directory only yields whole-state directories (wargames.com) already exhausted + now timing out. BroadReady stuck at 7 (was 5 on 08-14, 6 on 08-13).
- **Action needed**: (a) discovery provider with real coverage (serpapi_maps/browser_maps + key — human credential decision), OR (b) authorize sendable-pool expansion to non-primary allowed states. Neither automatable without user decision.

## 2026-08-14 15:00 (actual run 15:02–15:46 CST, completed clean 43m44s)
- **Status**: partial (max_loops_reached), A0 = 0/30, BroadReady = 5/30, gap 25 — 10th consecutive zero-intake day.
- **Active city**: Nashville TN (from system_config cursor, no hardcode, no state jump).
- **Provider**: ran with `WORKBUDDY_DISCOVERY_PROVIDER=web_directory` (DB retail_city_queue.active_provider already = web_directory; google_places has no API key). Lane A: 1 query family ('tabletop game store') → 15 seen, 0 new_unique, 0 leads (TN directory already exhausted). Lane B/C/D staging: empty.
- **Website Recovery**: 5 loops × 35 candidates → 0 emails. Per-loop: no_email≈25-26, network_err≈9-10 (7 persistent network_retry_pending + 2 skip_platform). Persistent network errors unchanged (Turtles Nest Toys, Old Black Mountain Games, Dewaynes World Comics, Extreme Toys, Puzzles Plus, Treasure Chest Games, Go Toys Games Calendars).
- **No SMTP** (send_log untouched, today_sent_count=4 from morning outreach only). No Final Send Plan. No Send Authorization. Lock released.
- **Review Center auto-classify**: 88 manual_review leads with email via evaluate_a0 → 0 pass (all verdict B2_manual_review). FB queue: 20 rows all terminal (failed_final/mismatch/no_facebook_*) → 0 actionable.
- **Dashboard refreshed**: Manual Review 546 pending, Inventory 0 A0.
- **Root cause (unchanged, 10th day)**: TN/AR/KY pool structurally depleted. analyze_all_leads: 42 broad_ready_orgs but ~30 in non-primary states (GA/NV/AZ/TX/UT etc. from 08-13 web_directory mass run); TN/AR/KY broad-ready only 5. Blocked: email_missing 471, previously_sent 474. web_directory provider works but only yields whole-state directories (wargames.com), already exhausted for TN/AR/KY.
- **Action needed**: (a) discovery provider with real coverage (serpapi_maps/browser_maps + key — human credential decision), OR (b) authorize sendable-pool expansion to non-primary allowed states already discovered (OH/NC/FL/GA etc.). Neither is automatable without user decision.

## 2026-08-13 15:00 (actual run 15:01–15:30 CST, killed mid-run loop 3/5)
- **Status**: partial. A0 = 0/30, BroadReady = 6/30, gap 24 (weekday target 30).
- **Active city**: Nashville TN (from system_config cursor, no hardcode, no state jump).
- **Lane A discovery**: configuration_blocked (provider=google_places, no API key). Lane B/C/D staging: empty.
- **Website Recovery**: 3 loops × 35 candidates → 0 emails. Per loop: no_email=26, network_err=9 (7 real network_retry_pending + 2 skip_platform). Persistent network errors unchanged (Turtles Nest Toys, Old Black Mountain Games, Dewaynes World Comics, Extreme Toys, Puzzles Plus, Treasure Chest Games, Go Toys Games Calendars).
- **Process killed mid-run**: background task "failed" at ~50min while on loop 3 (candidate #26 Kindness & Joy Toys) — network hang, no traceback. Left stale lock + job_runs='running'. Cleaned up manually (release_run_lock + finish_job_run partial). Loops 4–5 would have been identical (same exhausted 35-candidate pool).
- **Review Center auto-classify**: 102 manual_review leads with email scanned via evaluate_a0 → 0 pass A0 → 0 auto-approved.
- **FB enrichment queue**: 20 rows assessed; only 3 actionable (2 NC + 1 OR, all CONTACT_FORM_ONLY); 0 emails found. Requires browser worker (fb_worker.py) not wired into inventory stage — remains unprocessed.
- **No SMTP, no Final Send Plan, no Send Authorization.** Dashboard refreshed (bd_dashboard_v3.2.py).
- **Root cause (9th consecutive zero-intake day)**: google_places provider unconfigured → zero new lead intake since Jul 29. TN/AR/KY pool structurally depleted: 147 sent, 139 manual_review (132 no-email), 20 contact_form, only 14 unsent-with-email (6 BroadReady + 8 hard-blocked: 7 previously_sent, 1 suppressed).
- **Action needed**: configure discovery provider credentials (set WORKBUDDY_DISCOVERY_PROVIDER, e.g. serpapi_maps/browser_maps with key) — this is a human credential decision; without it the pipeline cannot reach the 30 target.

## 2026-08-13 (actual run 05:59–06:43 CST, 44min)
- **Status**: partial (max_loops_reached), A0 = 0/30, gap 30 — 8th consecutive zero-intake day
- **Active city**: Nashville TN (from system_config cursor, no hardcode)
- **Lane A discovery**: configuration_blocked (provider=google_places, provider_not_configured). Lane B/C/D staging: empty
- **Website Recovery**: 35 candidates × 5 loops → 0 emails found. Final loop: no_email=26, network_err=9 (7 real network_retry_pending + 2 skip_platform mis-counted into the aggregate counter)
- **Persistent network errors (unchanged)**: Turtles Nest Toys, Old Black Mountain Games, Dewaynes World Comics & Games, Extreme Toys, Puzzles Plus, Treasure Chest Games, Go Toys Games Calendars
- **Platform skips**: 901 Toys, CM Games Morristown (others no longer in the 35-candidate query)
- **No SMTP** (send_log +0 today), no Final Send Plan, no Send Authorization. Lock released. Dashboard refreshed (A0=0, Manual Review=295).
- **Root cause (unchanged)**: Google Places provider unconfigured → zero intake since Jul 29. Website Recovery pool fully depleted (all no-email/network/platform). Previously_sent recurring emails now excluded by `NOT EXISTS manual_email_submission submitted_by='inventory_lane'`.
- **Action needed**: configure discovery provider (set `WORKBUDDY_DISCOVERY_PROVIDER` + credentials, e.g. serpapi_maps or browser_maps) or activate a new intake lane. FB enrichment queue (20 rows) is NOT wired into the inventory stage — remains unprocessed.

## 2026-08-11 15:00 (actual run: 05:56 UTC = 13:56 CST)
- **Status**: partial (discovery_blocked, pool_drained, max_loops_reached)
- **A0**: 0/30, gap 30 — 40min runtime, identical pattern to all prior runs since Aug 6
- **Active city**: Nashville TN (from system_config cursor — no hardcode)
- **Lane A discovery**: configuration_blocked (Google Places API). Lane B/C/D staging: empty
- **Website Recovery**: 34 candidates × 5 loops → 3 emails per loop (all previously_sent: jeff@midtngaming.com, customercare@easternnational.org ×2), 20 no email, 7 persistent network errors + 4 platform skips = 11 total errors per loop
- **Persistent network errors (7, unchanged)**: Turtles Nest Toys, Old Black Mountain Games, Dewaynes World Comics & Games, Extreme Toys, Puzzles Plus, Treasure Chest Games, Go Toys Games Calendars
- **Platform skips (4, unchanged)**: 901 Toys, CM Games Morristown, CM Games Lexington, Matts Games Collectibles
- **Pool**: 738 total, unchanged. A0=0, Broad=95, Manual=217. All lanes exhausted.
- **Sent today**: 0. No SMTP, no Final Send Plan.
- **Root cause**: Google Places API blocked (rate limit / credentials) → zero new lead intake since Aug 6 (6th consecutive day). Website Recovery pool fully depleted — all 34 candidates hit either no-email (20) or network error (7) or platform skip (4). 3 recurring emails found (jeff@midtngaming.com, customercare@easternnational.org) are all previously_sent and excluded by send_log gate.
- **Action needed**: Google Places API credentials must be refreshed or alternative discovery provider activated. Website Recovery pool cannot generate more leads without new intake.
