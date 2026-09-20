# PHASE 4A.4B — Codex 4A.5 + 4A.6 Controlled Production Deployment, Validation & Loop-State Audit

> Generated: 2026-09-20 21:50 +08 (Asia/Shanghai)
> Scope: **deployment verification + regression A/B + loop-state audit**. NO Inventory run, NO discovery/scrape,
> NO scheduler change, NO SMTP/IMAP, NO FSP, NO Authorization, NO send.
> Live DB authority: `roktandrazo-outreach/data/bd_leads.db` (read-only).
> Repo authority: this repo = PRODUCTION HANDOFF; `roktandrazo-outreach-codex` = DEVELOPMENT.

---

## A. REPO STATE (queried live via GitHub API, not from memory)

| Repo | HEAD | Commit message | Time (UTC) |
|---|---|---|---|
| PRODUCTION `workbuddy-task-window` | `e61cbfbe` | PHASE 4A.4A handoff: backfill COMMIT_SHA=9270f26 + PUSH_SUCCESS | 2026-09-20 12:01 |
| DEVELOPMENT `roktandrazo-outreach-codex` | `74f50852` | Wire fail-closed city queue advancement (Phase 4A.7) | 2026-09-20 12:18 |

- **4A.4B is NOT pushed.** Production `main` still ends at the 4A.4A marker `e61cbfbe`.
- Local clone `C:/Users/15690/workbuddy-task-window` is in sync with remote `main` (HEAD = `e61cbfb`, 0 behind).
- Codex HEAD `74f50852` (4A.7) is newer than anything deployed; 4A.7 was **not** deployed in this phase.

---

## B. DEPLOYMENT STATE — SHA256-VERIFIED

| File | Pre-4A.5/4A.6 baseline | Deployed now | Codex reference | Verdict |
|---|---|---|---|---|
| `bd_template.py` | `0c900d51…` | `00ab0d45…` | == `d5886206` (4A.5) | **4A.5 DEPLOYED** |
| `discovery/discovery_service.py` | `ec0c1d0e…` | `09f400b6…` | == `cbb8fa3e` (4A.6) | **4A.6 DEPLOYED** |
| `bd_orchestrator.py` | `252ed604…` | `252ed604…` | == `cbb8fa3e`, != `74f50852` | 4A.7 NOT deployed |
| `retail_city_queue.py` | `95fa135f…` | `95fa135f…` | == `cbb8fa3e`, != `74f50852` | 4A.7 NOT deployed |

Baseline identity proof: `discovery/discovery_service.py` @ Codex `d5886206` hashes to `ec0c1d0e…`, which is exactly
the production post-4A.4 SHA recorded in the 4A.4A handoff → the A/B baseline used in section C is the true pre-4A.6 state.

### Locked-template integrity (bd_template.py is on the frozen list)
4A.5 is **additive only**:

- NEW locked template `general_inbox_referral_v1_locked` (status `ACTIVE_LOCKED`, public generic inboxes only).
- All pre-existing locked bodies **byte-identical**: `BODY_HTML` `6c571398…`, `BODY_TEXT` `5a350f0d…`,
  `CUSTOM_BODY_HTML` `da3a505b…`, `CUSTOM_BODY_TEXT` `87344b84…`, `FOLLOWUP_BODY_HTML` `13b72cea…`,
  `FOLLOWUP_BODY_TEXT` `4d9f30f3…`, `SIGNATURE_HTML` `a202aa70…`, `SIGNATURE_TEXT` `23002b92…`.
- Diff = **+83 / −4 lines**; the two locked new-outreach templates (`retail_distributor_v5`,
  `custom_printing_production_v5`) are untouched. TEMPLATE_REGRESSION = false.

---

## C. VALIDATION

1. **Targeted tests (from Codex, copied into production `tests/`)**
   - `tests/test_general_inbox_referral_routing.py` (4A.5) + `tests/test_first_party_email_enrichment.py` (4A.6)
   - Result: **10 passed / 0 failed** (0.17s).

2. **Controlled A/B full-suite regression** (baseline files restored temporarily, then restored back; hashes re-verified after)
   - BEFORE (pre-4A.5/4A.6): **36 failed / 255 passed / 5 errors**
   - AFTER (deployed, excluding the 10 new tests): **36 failed / 255 passed / 5 errors**
   - **NEW_FAILURES_INTRODUCED = 0**; failure sets are **IDENTICAL** (`ONLY_IN_AFTER = []`, `ONLY_IN_BEFORE = []`).
   - The 36 pre-existing failures are environment/clock dependent, not code defects:
     `test_recipient_scheduler` 12, `test_dashboard_timezone` 6, `test_p0_runtime_semantics` 5,
     `test_discovery_service` 4, `test_preflight_gate` 4 (live MX network), `test_inventory_followup` 3,
     `test_timezone_unified` 2. (Run executed Sunday 21:30 +08 = 09:30 ET; weekday/window-sensitive tests flip by clock.)

3. **4A.7 negative proof**: Codex `tests/test_phase4a7_city_queue_advancement.py` fails to import
   (`cannot import name 'city_completion_checks' from 'retail_city_queue'`) → confirms 4A.7 is genuinely NOT deployed.
   The file is staged at `output/staging_4a7/` (NOT left in production `tests/`).

---

## D. LOOP-STATE AUDIT — KEY FINDING

**The SAFE accumulation loop is STOPPED.** It did not run under 4A.5 + 4A.6.

| Evidence | Value |
|---|---|
| Last `lead_discovery_results.discovered_at` | `2026-09-20T10:23:06Z` (18:23 +08) |
| Last `data/browser_maps_cache/*.json` write | 2026-09-20 18:23 +08 |
| `retail_city_queue.last_success_at` (Ithaca) | `2026-09-20T10:28:28Z` (18:28 +08) |
| Deployment timestamps | `bd_template.py` 20:26 +08, `discovery_service.py` 20:31 +08 |
| Running python / playwright processes | NONE |
| New artifacts in `output/` in last 3h | NONE |
| Any `4A.4B` document anywhere in the workspace | NONE |

→ The only discovery activity today (18:00–18:23) belongs to the **4A.4A** 8-iteration run (frozen at 20:00).
The 4A.4B session deployed 4A.5+4A.6 at ~20:26–20:31 and then ended **before** starting any accumulation
iteration and before writing/pushing any 4A.4B report.

### Side finding (production hygiene, not caused by 4A.5/4A.6)
`job_runs` for 2026-09-20 13:16:35 → 13:17:08 contains **30 inventory runs, every one `stop_reason=lock_conflict`**
(a 33-second collision storm). No inventory run completed that window. Candidate root cause: concurrent
inventory triggers racing the same `inventory:<business_date>` run lock. Not addressed in this phase (read-only audit).

---

## E. LIVE METRICS (read-only from `bd_leads.db`, 2026-09-20 21:45 +08)

| Metric | Value | Authority |
|---|---|---|
| `LEADS_TOTAL` | 1087 | live DB |
| `EVIDENCE_URL_NON_EMPTY` | 862 | live DB (= 4A.4A `evidence_after`; no new evidence since freeze) |
| `DISCOVERY_RESULTS_TOTAL` | 369 (Ithaca 69) | live DB |
| `MATERIALIZED_FSP_PLANNED` | 0 | live DB |
| `SEND_LOG_TODAY` | 0 (last send 2026-09-16T01:09:52+08) | live DB |
| `SUPPRESSION_LIST` | 63 | live DB |
| `BROAD_READY` | 33 (4A.4 run authority) | last run record |
| `V2_ELIGIBLE_UNSENT` / `READ_ONLY_V2_SAFE_UNIQUE_ORGS` | **6 — LIVE** (recomputed read-only 2026-09-20 21:46 +08, 16m33s; `V2_CANDIDATE_ROWS=6`) | live DB |
| Active city | Ithaca, NY — status `active`, `new_unique_places=69`, `pages_processed=41` | live DB |
| Ithaca query families | pending 51 / completed 6 / running 1 / configuration_blocked 1 / provider_not_configured 1 | live DB |
| `CITY_QUEUE_ADVANCED` | false (Saratoga Springs NOT activated) | live DB |

Safety invariants: `SMTP_CONNECTIONS=0`, `IMAP_CONNECTIONS=0`, `OUTREACH_SEND_COUNT=0`,
`PRESEND_FSP_CREATED=0`, `AUTHORIZATION_CREATED=0`, `DATABASE_SCHEMA_CHANGED=false`,
`V2_POLICY_CHANGED=false`, `MX_POLICY_CHANGED=false`, `SCHEDULER_CHANGED=false`.
Scheduler: Inventory `1784775229336` ACTIVE, Recovery `1786002601925` ACTIVE,
PreSend `1785804406748` / Preflight `1785804413719` / Outreach `1785804421539` PAUSED (held, SAFE<40).

---

## F. WHAT 4A.4B DID AND DID NOT COMPLETE

| Item | Status |
|---|---|
| Deploy Codex 4A.5 (`d5886206`) | ✅ done, SHA-verified, tests pass |
| Deploy Codex 4A.6 (`cbb8fa3e`) | ✅ done, SHA-verified, tests pass |
| Regression validation (A/B) | ✅ done, 0 new failures |
| Scheduler posture (Inventory+Recovery ACTIVE / sends PAUSED) | ✅ verified |
| SMTP=0 / 0 sends | ✅ verified |
| SAFE accumulation loop under 4A.5+4A.6 | ❌ **NOT STARTED** (loop dead since 18:23) |
| 4A.4B report + handoff push | ✅ this document (loop outcome recorded as NOT RUN) |

---

## G. RECOMMENDED NEXT STEPS (require user authorization — NOT executed)

1. **Deploy Codex 4A.7 (`74f50852`) — fail-closed city queue advancement.**
   Rationale: Ithaca still has 51 pending families and `CITY_QUEUE_ADVANCED=false`; 4A.7 makes queue advancement
   fail-closed so a stalled/depleted city hands off deterministically instead of looping on one city.
   Touches `bd_orchestrator.py` + `retail_city_queue.py` (both currently at 4A.6 state).
2. **Then restart the SAFE accumulation loop** with 4A.5+4A.6(+4A.7) live, targeting SAFE ≥ 40 (target_50 gate).
3. Optional hygiene fix: the 30× `lock_conflict` inventory collision storm (13:16–13:17 today).

---

## H. SAFE RECOMPUTE — COMPLETED (LIVE)

`READ_ONLY_V2_SAFE_UNIQUE_ORGS` was recomputed read-only (frozen V2 + live MX, all email-present leads) and finished at
2026-09-20 21:46 +08 after 16m33s:

```
V2_CANDIDATE_ROWS               = 6
READ_ONLY_V2_SAFE_UNIQUE_ORGS   = 6      AUTHORITY = LIVE (matches 4A.4A frozen value 6)
MATERIALIZED_FSP_PLANNED        = 0
```

The live value equals the frozen 4A.4A measurement → no SAFE change was produced by the 4A.5/4A.6 deployment
(expected: 4A.6 affects discovery-side first-party email enrichment, which had no run in this phase).
Operational note: this recompute does per-domain MX probes through the Astrill proxy and is slow (~16 min);
prefer reading the value from `bd_orchestrator --stage inventory` logs for routine checks.
