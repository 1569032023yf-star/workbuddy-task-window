# PHASE 4A.5B — UPSTREAM SAFE CONVERSION AUDIT + RECOVERY

**Date:** 2026-09-21 (Asia/Shanghai)
**Production HEAD at start:** `2a53e2f` (4A.5A) — Codex `07784044` already deployed
**Scope:** increase SAFE conversion from EXISTING production leads before adding discovery volume
**Hard constraints honoured:** V2 not relaxed · MX not relaxed · no guessed emails · no third-party
email evidence · no sends · no template/sender/city-policy change · no business-logic change

---

## A. CITY QUERY METRIC — CORRECTED

Scope enforced strictly to `active_city_id = 20 (Ithaca, NY)` **AND** `provider = 'browser_maps'`.
Source table: `lead_discovery_query_state`. `google_places` / `web_directory` / legacy rows are
reported separately and are **excluded** from the headline numbers.

```
BROWSERMAPS_QUERY_TOTAL          = 20
BROWSERMAPS_COMPLETED            = 13
BROWSERMAPS_PENDING              = 6
BROWSERMAPS_RUNNING              = 1
BROWSERMAPS_FAILED_OR_BLOCKED    = 0
```

### A.1 Why the earlier "45 unrun families" was wrong

The previously circulated figure mixed every provider into one count. Actual per-provider rows for
city 20:

| provider | status | rows |
|---|---|---|
| browser_maps | completed / pending / running | 13 / 6 / 1 |
| google_places | pending | 19 |
| google_places | configuration_blocked | 1 |
| web_directory | pending | 19 |
| web_directory | provider_not_configured | 1 |

`19 + 19 + 1(running) + ...` is where "45" came from. `google_places` is not configured and
`web_directory` has no provider — **neither is the active provider**, so neither may gate the
browser_maps completion contract. Corrected unrun count for the active provider = **7** (6 pending
+ 1 running).

### A.2 Deployed completion contract — `city_completion_checks(20, "browser_maps")`

```
RETAIL_QUERY_FAMILIES                 = 20
all_query_families                    = False
all_sources_or_reasons                = False
pagination_complete                   = False
two_empty_pages                       = False
all_candidates_classified             = False
no_unprocessed_candidates             = False
official_site_recheck                 = False
review_recovery                       = False
last_three_batches_empty              = False
ALL_MET                               = False
```

`ALL_MET=False` is the **correct fail-closed result**: 7 query families are unrun and the city has
open staged work. 4A.7 is behaving as designed; this is not a regression.

Active city row: `id=20, Ithaca, NY, status=active, active_provider=browser_maps,
web_directory_status=NULL`.

---

## B. UPSTREAM BLOCKER CLASSIFICATION (READ-ONLY — NO ROW CHANGED)

Universe: nonterminal leads (`status NOT IN sent/bounced/do_not_contact/rejected/failed/
delivery_issue/bounce_review`) that are `manual_review_needed`, or have an empty email, or carry an
email-related `review_reason_code`.

```
CANDIDATE_UNIVERSE = 595
```

| # | bucket | count |
|---|---|---|
| 1 | HAS_OFFICIAL_WEBSITE_NO_EMAIL | 90 |
| 2 | HAS_OFFICIAL_WEBSITE_EMAIL_EXTRACTION_RETRYABLE | 14 |
| 3 | LINKED_BACKLOG_RETRYABLE | 252 |
| 4 | REVIEW_RECOVERY_RETRYABLE | 1 |
| 5 | TERMINAL_IDENTITY_OR_HYGIENE | 4 |
| 6 | WEBSITE_NOT_FOUND | 10 |
| 7 | NO_OFFICIAL_WEBSITE | 129 |
| 8 | HISTORY_OR_SUPPRESSION_BLOCKED | 1 |
| 9 | OTHER | 94 |
| | **TOTAL** | **595** |

Assignment priority (documented, deterministic): `8 → 5 → 3 → 4 → 2 → 1 → 6 → 7 → 9`. Terminal
buckets are resolved first so they can never be silently counted as recoverable.

```
MANUAL_REVIEW_TOTAL (leads.status='manual_review_needed') = 513
RECOVERABLE_EXISTING_COHORT (buckets 2+3+4)               = 267
TERMINAL_MANUAL_COHORT (buckets 5+8)                      = 5
```

### B.1 Critical scoping correction on the "267 recoverable" number

Production recovery lanes (`DiscoveryService.run_linked_backlog`, `run_staging_postprocess`,
`run_website_resolution`) are **hard-scoped to `active_city_id`**. Re-scoping bucket 3 by that rule:

| bucket | total | has discovery row | **discovery row in active city 20** |
|---|---|---|---|
| 2 HAS_WEBSITE_EMAIL_EXTRACTION_RETRYABLE | 14 | 14 | **14** |
| 3 LINKED_BACKLOG_RETRYABLE | 252 | 252 | **10** |
| 4 REVIEW_RECOVERY_RETRYABLE | 1 | 1 | **1** |

**252 → 10.** The other 242 sit in Cincinnati / Columbus / Orlando / Nashville / Asheville … and
are unreachable without a city-policy change, which is explicitly out of scope for this phase.

Real automatically-reachable cohort: **≈25 leads** (14 + 10 + 1) plus the 10 `website_not_found`
rows reachable through the website-resolution lane.

### B.2 Near-miss analysis — why the leads that already HAVE an email are not SAFE

```
EMAIL_POOL (has email, nonterminal) = 109
SAFE_UNIQUE_ORGS (live recompute)   = 13          <- confirms the baseline
POOL: BLOCKED 87 | NEEDS_EMAIL_VERIFICATION 8 | NEEDS_MANUAL_REVIEW 1 | CAMPAIGN_ELIGIBLE_V2 13
```

Blocker histogram (a lead can carry several):

| blocker | occurrences |
|---|---|
| broad_ready (previously_sent_email / previously_sent_org / shared_domain_org_history / suppression / recheck_pending) | 173 |
| guessed_email_without_enhanced_verification | 73 |
| mx (nxdomain / no_mail_route / null_mx / dns_error) | 60 |
| third_party_email | 10 |
| evidence_stale | 9 |
| public_mailbox_no_official_evidence | 4 |
| timezone | 1 |
| hygiene | 1 |

MX distribution over the 104 unique domains: `nxdomain 50, ok 44, no_mail_route 8, dns_error 1,
null_mx 1`.

**Interpretation:** the existing email-bearing pool is essentially exhausted. 87 of 96 non-eligible
leads are hard-BLOCKED by history/hygiene (already sent, suppressed, shared-domain org history) —
these are permanent and must not be overridden. 73 are `guessed_email`, which V2 forbids promoting.
Only 8 + 1 sit in recoverable pools, and those are dominated by guessed-email or stale-evidence
cases whose only lawful fix is fresh first-party evidence.

---

## C. RECOVERY OF EXISTING SAFE AUTOMATIC COHORTS

Only already-authorized production paths were used, in bounded serial batches:

1. `DiscoveryService.run_website_resolution(city, resolver, max_results=20, unlinked_only=True)`
2. `DiscoveryService.run_staging_postprocess(city, max_results=20, unlinked_only=True)`
3. `DiscoveryService.run_linked_backlog(city, resolver, max_results=20)`

No lead row was written directly. No manual promotion of terminal manual-review rows. No hygiene
outcome rewritten. No email invented. No new provider discovery (no `run_places_batch`).

| round | rows processed | website_resolution | staging_postprocess | linked backlog | official emails | full evidence | SAFE gain | SAFE total |
|---|---|---|---|---|---|---|---|---|
| 1 | 20 | 5 seen (4 not_found, 1 network_retry) | 5 seen | 10 eligible / 10 processed | 0 | 0 | 0 | 13 |
| 2 | 20 | 5 seen (4 not_found, 1 network_retry) | 5 seen | 10 eligible / 10 processed | 0 | 0 | 0 | 13 |
| 3 | 20 | 5 seen (4 not_found, 1 network_retry) | 5 seen | 10 eligible / 10 processed | 0 | 0 | 0 | 13 |

```
SAFE_BEFORE             = 13
SAFE_AFTER              = 13
ROWS_PROCESSED          = 60
OFFICIAL_EMAILS_FOUND   = 0
FULL_EVIDENCE_CREATED   = 0
NEW_SAFE_ORGS           = 0
STOP_REASON             = three_consecutive_zero_safe_batches
```

The three lanes re-selected the **same** rows every batch (5 `website_lookup_pending` + the same 10
linked rows) and produced the **same** no-op outcome. The recoverable existing cohort is therefore
exhausted in practice: it is not a throughput problem, the rows have genuinely no resolvable
official website / no publicly visible first-party email.

MX speed-up note: `preflight_gate.query_mx` was wrapped with an in-process cache for the repeated
SAFE recomputes. It is a pure `domain → status` function, so semantics are unchanged; only
redundant network calls were removed. No policy or threshold was touched.

**Verdict on C:** recovering existing stock yields **zero** under this city and these rules. The
three automatic lanes are not starved of throughput — the rows simply have no resolvable official
website or no publicly visible first-party email.

---

## D. NEW DISCOVERY RESUMED (recovery cohort exhausted, SAFE < 40)

Canonical entry point only: `bd_orchestrator.py --stage inventory --live`, strictly sequential,
never concurrent. Recovery and Inventory never overlapped (the scheduled Inventory automation was
PAUSED for the whole duration).

| round | exit | status | new unique places | website res. | staging post. | linked backlog | SAFE after |
|---|---|---|---|---|---|---|---|
| 1 | 0 | partial / safe_inventory_gap | **6** | 5 | 9 | 12 eligible / 12 processed | **15** |
| 2 | 0 | partial / safe_inventory_gap | 0 | 5 | 5 | 10 / 10 | 15 |
| 3 | 0 | partial / safe_inventory_gap | 0 | 5 | 5 | 10 / 10 | 15 |
| 4 | terminated externally | see §D.1 | — | — | — | — | 15 |

Round 1 advanced one new query family and produced **+2 SAFE (13 → 15)** and `BROAD_READY 47 → 49`.
Rounds 2–3 re-processed already-seen pages (`NEW_UNIQUE_PLACES=0`). Measured rate over 4 rounds:
**+2 SAFE per ~3 rounds (~35 min)**. Extrapolating to SAFE 40 would need roughly **35–40 more
rounds (~7–9 h)** — not finishable inside this session window, and every additional round depends on
`browser_maps` returning pages that contain genuinely new places for a small city.

### D.1 Clean stop and orphan clearing (full disclosure)

The outer serial driver was stopped by terminating only the wrapper process, letting the in-flight
`bd_orchestrator` child continue. The child did exit, but not through its normal
`finish_job_run` path, leaving job `inventory:2026-09-21:48e446a0` in `status='running'` and holding
`run_lock:daily_outreach:inventory:2026-09-21`. Verified no python process was alive, then cleared it
with the **existing** semantics — the same `status='failed', stop_reason='stale_cleanup'` UPDATE that
`bd_db.start_job_run` applies to stale rows, plus `release_run_lock`:

```
job_runs rows updated   = 1     (48e446a0 -> failed / stale_cleanup)
lock rows released      = 1     (run_lock:daily_outreach:inventory:2026-09-21 = released)
RUNNING_INVENTORY_JOBS  = 0
HELD_INVENTORY_LOCKS    = 0
```

`lead_discovery_query_state` row 476 (`visitor center gift shop`) is legitimately `status='running'`
with 1 page processed and 3 new unique places — it is a resume checkpoint consumed by
`_active_query` on the next run, **not** a stuck row.

### D.2 Scheduler state at hand-off

`RoktRazo BD Inventory — 15:00 Asia/Shanghai` (`automation-1784775229336`) restored to **ACTIVE** so
the remaining 5 Ithaca families continue on the canonical schedule.

Remaining unrun families (all for the active city):

```
visitor center gift shop   (resume checkpoint, 1 page done)
tourist gift shop
specialty retailer
puzzle store               <- highest product fit for Rokt&Razo
card game store            <- highest product fit for Rokt&Razo
```

---

## E. SAFETY INVARIANTS (verified live at hand-off)

```
PreSend    automation-1785804406748  = PAUSED
Preflight  automation-1785804413719  = PAUSED
Outreach   automation-1785804421539  = PAUSED
Recovery   automation-1786002601925  = ACTIVE
Inventory  automation-1784775229336  = ACTIVE (restored)

SMTP_enabled (system_config)         = 0
SMTP_CONNECTIONS / sends today       = 0
OUTREACH_SEND_COUNT                  = 0
last send_log row                    = 2026-09-16T01:09:52+08:00
MATERIALIZED_FSP_PLANNED             = 0
RUNNING_INVENTORY_JOBS               = 0
HELD_INVENTORY_LOCKS                 = 0

V2 changed = false | MX changed = false | template changed = false
sender changed = false | city policy changed = false | business logic changed = false
No terminal manual-review row promoted. No hygiene outcome rewritten. No email invented.
No third-party email evidence used.
```

---

## F. FINAL

```
SAFE_BEFORE                          = 13
SAFE_AFTER                           = 15          (+2, both from new discovery in D round 1)

BROWSERMAPS_QUERY_TOTAL              = 20
BROWSERMAPS_COMPLETED                = 15
BROWSERMAPS_PENDING                  = 4           (+1 resume checkpoint counted as running)
BROWSERMAPS_FAILED_OR_BLOCKED        = 0
city_completion_checks ALL_MET       = false       (correct fail-closed)

MANUAL_REVIEW_TOTAL                  = 519         (leads.status='manual_review_needed')
RECOVERABLE_EXISTING_COHORT          = 267 raw  ->  25 actually reachable (94% outside active city)
TERMINAL_MANUAL_COHORT               = 5

ROWS_PROCESSED      (recovery, C)    = 60
OFFICIAL_EMAILS_FOUND (recovery, C)  = 0
FULL_EVIDENCE_CREATED (recovery, C)  = 0
NEW_SAFE_ORGS       (recovery, C)    = 0
NEW_SAFE_ORGS       (discovery, D)   = 2

EMAIL_POOL exhausted check           = 109 leads with email -> 87 hard-BLOCKED by
                                       broad_ready history/hygiene, 73 guessed_email
                                       => existing email stock cannot carry the target

READY_FOR_40_RECIPIENT_ACCEPTANCE    = false
STOP_REASON                          = recovery_cohort_exhausted_zero_yield
                                       -> canonical serial Inventory resumed
                                       -> manual loop halted after 4 rounds (0 refining yield,
                                          +2/3 rounds rate); scheduled Inventory restored ACTIVE
```

### F.1 What this phase actually proved

1. The "45 unrun Ithaca families" figure was a **metric error** from mixing providers. Truth is 7 (now 5).
2. The "267 recoverable leads" figure was also **scope-inflated**: production lanes are active-city
   scoped, so only **25** are reachable without a city-policy change.
3. Those 25, plus every other automatic lane row, produce **zero** new first-party emails. Recovery
   of existing stock is exhausted, not slow.
4. The email-bearing pool is structurally capped: 87/96 non-eligible leads are blocked by
   already-sent / suppression / shared-domain-org history, and 73 are guessed emails. Neither can be
   lawfully overridden.
5. **New discovery is the only working lever** (+2 in one round), but at ~2 SAFE / 3 rounds it needs
   ~7–9 h of additional serial runs to reach 40.

### F.2 Options to reach 40 — all require authorization, none started

| option | effect | cost / risk |
|---|---|---|
| A. Let the canonical 15:00 scheduler run several days | +2 SAFE ≈ every 3 rounds | slowest, zero risk, no change |
| B. Keep serial manual rounds going this session | ~7–9 h | operator-bound, browser-scraper dependent |
| C. Raise per-round throughput (Lead-Factory change) | multiplies both discovery and email rate | **out of scope** for this phase; needs its own authorization + tests |
| D. Lower the acceptance watermark from 40 to a reachable value (e.g. 20) | unblocks send-stage acceptance | policy decision, not technical |

---

**Artifacts:** `handoff/workbuddy/phases/PHASE4A5B_UPSTREAM_SAFE_CONVERSION_AUDIT.md` (this file)
**Raw evidence:** `output/4a5b_buckets.json`, `output/4a5b_nearmiss.json`, `output/4a5b_recovery/rounds.csv`,
`output/4a5b_rounds/rounds.csv`, `output/4a5b_final.json`
**Production code:** unchanged (`bd_orchestrator.py` `7afc4d7f`, `retail_city_queue.py` `46d6f452`).
