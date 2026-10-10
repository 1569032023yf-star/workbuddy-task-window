# PHASE 4A.5R — SAFE40 客户库存封存与发送持续冻结
# SAFE40 BATCH HOLD — CLIENT INVENTORY SEALED, SEND FREEZE CONTINUED

> FOR THE PROJECT OWNER (Ian / ianyf@roktandrazo.com). This report uses plain language first and
> machine-readable facts second.
>
> - Repository: `1569032023yf-star/workbuddy-task-window` (branch `main`).
> - Generated: 2026-10-10T09:49:04+08:00 (Asia/Shanghai).
> - This phase is **OPERATIONS + HANDOFF ONLY**. It changed **no** production business code, made
>   **no** direct production business-data write, created **no** automation, and sent **no** email.

---

## A. BUSINESS DECISION RECORDED (the point of this phase)

The owner has decided:

**Do NOT send any outreach email to the current SAFE40 batch now.** The 2026 Christmas buying and
product-development window is likely already too late, and the batch should not be rushed out with a
Christmas-themed message just to mark the SAFE40 target as "done".

This is **not** a deletion and **not** a reversal of the discovery work. The batch is fully preserved
for a future outreach plan.

```
CAMPAIGN_BUSINESS_DECISION = HOLD_NO_SEND
CURRENT_BATCH_DISPOSITION  = PRESERVE_FOR_FUTURE_OUTREACH
```

`HOLD_NO_SEND` is a handoff business marker only. It created no database field and changed no
lead-eligibility status.

---

## B. THE HEADLINE NUMBERS

```
READ_ONLY_V2_SAFE_UNIQUE_ORGS = 40
SAFE40_REACHED                = true
SAFE40_CHECKPOINT_STATUS      = ACTIVE (read-only) — it detected SAFE40 and paused Inventory
INVENTORY_STATUS              = PAUSED (paused 2026-10-09 19:49:44 +08; nextRunAt = None)
CLIENT_DATA_PRESERVED         = true
DATABASE_BACKUP_VERIFIED      = true
SMTP_ENABLED                  = 0
SMTP_CONNECTIONS              = 0
SEND_LOG_TODAY                = 0
MATERIALIZED_FSP_PLANNED      = 0
LIVE_SEND_AUTHORIZATIONS      = 0 (new since the freeze; 23 historical rows, last 2026-09-16)
CLIENTS_DELETED               = 0
EMAILS_SENT_BY_THIS_TASK      = 0
PRODUCTION_BUSINESS_CODE_CHANGED = false
NEW_AUTOMATIONS_CREATED       = false
```

---

## C. WHY SAFE = 40 IS TRUSTWORTHY (and why a "SAFE = 0" reading was REJECTED)

The owner's instruction explicitly required avoiding a false SAFE = 0 caused by a broken DNS/proxy
environment. This actually happened during the measurement round and was caught, diagnosed, and
corrected. It is recorded here because it is the single most important methodological fact.

**The false reading.** A first read-only run returned `READ_ONLY_V2_SAFE_UNIQUE_ORGS = 0` with
`V2_ELIGIBLE_CANDIDATE_ROWS = 0`. Taken at face value this looks like the whole eligible pool
collapsed.

**The diagnosis (proved, not guessed).**
1. `query_mx("gmail.com")` returned `dns_error` after ~10 s — i.e. even Google's own domain failed.
   A genuine pool collapse cannot cause that.
2. `curl` to the Worker MX endpoint `https://roktandrazo-email-tracker.1569032023yf.workers.dev/`
   returned **HTTP 000 after 20 s with `--noproxy '*'`** (direct), but **HTTP 200 in 1.2 s via the
   Astrill proxy `http://127.0.0.1:3213`**.
3. `preflight_gate.query_mx()` documents that it deliberately does **not** inherit process-level
   `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY`; it uses only the explicitly configured
   `BD_MX_HTTPS_PROXY`.
4. The measurement shell had `HTTP_PROXY=127.0.0.1:51990` (a dead local port) and — critically — the
   `.env` file had **not** been loaded into that process, so `BD_MX_HTTPS_PROXY` was unset.
   Production `.env` line 50 sets `BD_MX_HTTPS_PROXY=http://127.0.0.1:3213`.

**The correction.** The measurement was re-run after loading the production `.env` the same way
production does. Result: `query_mx("gmail.com") -> ok (0.6 s)`, and
`READ_ONLY_V2_SAFE_UNIQUE_ORGS = 40`.

**Conclusion.** `SAFE = 0` was a **local measurement-environment artifact**, not a production
regression. No production file, config, or DB value was changed to "fix" it — there was nothing to
fix in production. The false value was never written into any handoff file.

**Authority and confirmation.** Two independent sources agree on 40:

| Source | When | Value |
|---|---|---|
| `campaign_eligible_v2.select_candidates_for_plan_v2` (V2 + current MX, read-only, distinct `organization_key`) | 2026-10-09 18:37:14 +08 | **40** |
| Same authority, re-measured | 2026-10-10 09:47:08 +08 | **40** |
| Existing SAFE40 checkpoint (`output/_4a5g_checkpoint.py`, frozen V2+MX path) | 2026-10-09 19:47:52 +08 | **40** |
| Canonical Inventory run `inventory:2026-10-09:d25355ad` (its own `actual`) | 2026-10-09 07:19:09 +08 (finish) | **40** |

`V2_ELIGIBLE_CANDIDATE_ROWS = 40` and distinct-org count = 40 agree, i.e. 40 candidates across 40
distinct organizations.

---

## D. SAFE ACCUMULATION PATH (35 -> 40)

The checkpoint history (`output/4a5g_checkpoints.jsonl`) records the stepwise accumulation:

```
2026-10-09 01:37:34  safe=35
2026-10-09 07:41:20  safe=35
2026-10-09 13:44:46  safe=37   SAFE_CHANGED: 35 -> 37
2026-10-09 19:47:52  safe=40   SAFE_CHANGED: 37 -> 40   SAFE40_REACHED
```

New organizations credited (from the checkpoint milestones):

- 35 -> 37: `org:domain:christenespringlemountainmagic.com`, `org:domain:wiabbatco.com`
- 37 -> 40: `org:domain:allstararcade.com`, `org:domain:baseballmotel.com`,
  `org:domain:cooperstowndreamspark.com`

```
SAFE_CHANGE_FROM_35 = +5 (35 -> 40)
```

---

## E. WHAT CAUSED THE RECOVERY — THE 4A.8Q HOTFIX FIRED EXACTLY AS DESIGNED

The 4A.8Q hotfix (deployed in PHASE 4A.5Q, commit `ef46bd9`) changed the `run_website_resolution`
else-branch so an `identity_review` outcome becomes a **terminal** state for **unlinked** rows,
instead of being written back as the row's own original status (which re-armed it forever).

Production first execution of the fixed code path:

```
POST-DEPLOY RUN #1  inventory:2026-10-08:9f263936
  started   2026-10-08 12:42:25 UTC = 2026-10-08 20:42:25 +08
  finished  2026-10-08 12:46:28 UTC = 2026-10-08 20:46:28 +08
  status    partial / stop_reason=safe_inventory_gap  (healthy terminal state, NOT a failure)
  actual    35
```

This is the run that had been scheduled as `NEXT_CANONICAL_INVENTORY_RUN = 2026-10-08 20:41:04 +08`
in the 4A.5Q report. It ran unattended, on schedule, with no manual trigger.

**Row 433 terminalized inside this run.**

```
ROW_433_VALIDATION_STATUS  = identity_review
ROW_433_REJECTION_REASON   = website_resolution:identity_review:
ROW_433_WEBSITE            = (empty)
ROW_433_LINKED_LEAD_ID     = NULL
ROW_433_LAST_SEEN_AT       = 2026-10-08T12:44:19.685562+00:00  (= 2026-10-08 20:44:19 +08)
ROW_433_RECOVERY_VERIFIED  = true
```

`last_seen_at` (20:44:19 +08) sits **inside** run `9f263936` (20:42:25–20:46:28 +08), i.e. the
transition was produced by the scheduled run, not by any manual SQL. `official_match = 0`,
`evidence_url = NULL`, `website` empty, no lead created, no email created — so the row was **not**
mis-labeled as a verified site / found email / eligible merchant.

Re-arm probe: the resolver's pending selector
(`validation_status IN ('website_lookup_pending','manual_review_needed')`) now matches row 433
**0 times**. The permanent re-loop is closed.

**Asymmetry confirmation.** Row 462 (`Children's Museum at Saratoga`) is at terminal
`identity_review` **because it is linked**. Row 433 was unlinked and could not reach that state
before the fix. That is precisely the asymmetry 4A.8Q addressed.

---

## F. SARATOGA SPRINGS — COMPLETED BY THE EXISTING QUEUE MECHANISM

```
SARATOGA_QUERY_FAMILIES   = 20/20 completed (query_state rows 20, completed 20, provider browser_maps)
SARATOGA_COMPLETION_CHECKS = 9/9 (all nine predicates true)
SARATOGA_FINAL_STATUS     = search_matrix_exhausted
SARATOGA_COMPLETED_AT     = 2026-10-08T12:44:19.697812+00:00  (= 2026-10-08 20:44:19 +08)
SARATOGA_RECOVERY_VERIFIED = true
```

All nine completion predicates:

| # | Predicate | Result |
|---|---|---|
| 1 | `all_query_families` | true |
| 2 | `all_sources_or_reasons` | true |
| 3 | `pagination_complete` | true |
| 4 | `two_empty_pages` | true |
| 5 | `all_candidates_classified` | true |
| 6 | `no_unprocessed_candidates` | true |
| 7 | `official_site_recheck` | true |
| 8 | `review_recovery` | true |
| 9 | `last_three_batches_empty` | true |

`SARATOGA_STAGED_PENDING = []` (empty) — the 4 predicates that previously failed
(`all_candidates_classified`, `no_unprocessed_candidates`, `official_site_recheck`,
`review_recovery`) all share one driver, `no_open_work`; with row 433 terminal they flipped to true.

Completion note: the queue's "finished" state is `search_matrix_exhausted`, **not** `completed`.
`SELECT COUNT(*) FROM retail_city_queue WHERE status='completed'` = 0 by design; the completed set is
read via `search_matrix_exhausted` + `completed_at`.

---

## G. COOPERSTOWN, NY — ACTIVATED AND GENUINELY DISCOVERING

```
ACTIVE_CITY        = Cooperstown, NY
ACTIVE_CITY_ID     = 22
COOPERSTOWN_ACTIVATED_AT = 2026-10-08T18:50:05.751144+00:00 (= 2026-10-09 02:50:05 +08)
```

Activation happened in the **next** scheduled run after Saratoga was exhausted
(`inventory:2026-10-09:44c4d491`, started 2026-10-08 18:48:30 UTC = 2026-10-09 02:48:30 +08) — the
queue's normal "no active city at start -> activate next" path. No human advanced the city.

**Real provider requests (the discovery-flow proof):**

```
FIRST_COOPERSTOWN_RUN_ID            = inventory:2026-10-09:44c4d491
FIRST_COOPERSTOWN_STARTED_AT        = 2026-10-08 18:48:30 UTC  = 2026-10-09 02:48:30 +08
FIRST_COOPERSTOWN_FINISHED_AT       = 2026-10-08 18:53:04 UTC  = 2026-10-09 02:53:04 +08
FIRST_COOPERSTOWN_PROVIDER_REQUEST_AT = 2026-10-08T18:50:53.549505+00:00 = 2026-10-09 02:50:53 +08
```

`provider_request_audit` rows for `active_city_id = 22` (all `status = ok`):

| id | query family | source query | result_count | requested_at (+08) |
|---|---|---|---|---|
| 226 | toy store | toy store Cooperstown NY | 3 | 2026-10-09 02:50:53 |
| 227 | toy store | toy store Cooperstown NY | 3 | 2026-10-09 02:50:53 |
| 228 | toy store | toy store Cooperstown NY | 3 | 2026-10-09 02:50:53 |
| 229 | board game store | board game store Cooperstown NY | 20 | 2026-10-09 09:00:44 |
| 230 | board game store | board game store Cooperstown NY | 20 | 2026-10-09 09:00:44 |
| 231 | board game store | board game store Cooperstown NY | 20 | 2026-10-09 09:00:44 |
| 232 | game store | game store Cooperstown NY | 20 | 2026-10-09 15:15:38 |
| 233 | game store | game store Cooperstown NY | 20 | 2026-10-09 15:15:39 |
| 234 | game store | game store Cooperstown NY | 20 | 2026-10-09 15:15:39 |

```
COOPERSTOWN_PROVIDER_PAGES    = 9
COOPERSTOWN_PROVIDER_REQUESTS = 9
COOPERSTOWN_RAW_RESULTS       = 129   (results_seen; PROVIDER RAW OUTPUT, not new merchants)
COOPERSTOWN_NEW_UNIQUE_PLACES = 28
COOPERSTOWN_DUPLICATE_PLACES  = 101
COOPERSTOWN_PROVIDER_ERRORS   = 0
```

**Honest separation of the counting layers** (the owner's instruction required this):

| Layer | Value | Meaning |
|---|---|---|
| Provider raw results | 129 | pages returned by the provider, incl. duplicates |
| Deduplicated new places | 28 | genuinely new businesses for the city |
| Rows written to `lead_discovery_results` | 28 | ids 528–555 |
| Leads created (`linked_lead_id` set) | 13 | lead ids 1214–1226 |
| Of those, first-party official emails | 6 | `email_verified_on_official_site = 1` |
| New SAFE organisations from this city | 3 | `allstararcade.com`, `baseballmotel.com`, `cooperstowndreamspark.com` |

Note: `provider_request_audit.result_count` is raw provider output (it is **not** "new leads" and
**not** "SAFE organisations"). `result_count = 3` on the first toy-store page meant 3 search hits,
not 3 customers.

**DISCOVERY_FLOW_RESTORED = true** — real provider pages > 0 **and** real provider requests > 0, on a
new city, driven by the normal scheduled path.

---

## H. POST-DEPLOY INVENTORY HEALTH

Every canonical Inventory run after the hotfix deploy (deploy moment 2026-10-08 15:09:01 +08):

| run_id | started (+08) | finished (+08) | status | stop_reason | actual | gap |
|---|---|---|---|---|---|---|
| `inventory:2026-10-08:9f263936` | 2026-10-08 20:42:25 | 2026-10-08 20:46:28 | partial | safe_inventory_gap | 35 | 15 |
| `inventory:2026-10-09:44c4d491` | 2026-10-09 02:48:30 | 2026-10-09 02:53:04 | partial | safe_inventory_gap | 35 | 15 |
| `inventory:2026-10-09:abb4fc81` | 2026-10-09 08:57:53 | 2026-10-09 09:05:55 | partial | safe_inventory_gap | 37 | 13 |
| `inventory:2026-10-09:d25355ad` | 2026-10-09 15:12:41 | 2026-10-09 15:19:09 | partial | safe_inventory_gap | 40 | 10 |

```
POST_DEPLOY_INVENTORY_RUNS = 4
SUCCESSFUL_OR_HEALTHY_PARTIAL_RUNS = 4
FAILED_RUNS                = 0
HTTP_429                   = 0
PROVIDER_ERRORS            = 0
LOCK_CONFLICTS             = 0
CONCURRENT_RUNS            = 0
STALE_CLEANUPS             = 0
MANUAL_INVENTORY_RUNS      = 0
LAST_SUCCESSFUL_INVENTORY_AT = 2026-10-09 15:19:09 +08
```

`status=partial` + `stop_reason=safe_inventory_gap` is the **healthy** terminal state for this
system (SAFE below the internal 50 target). It is not a failure. Note the `actual` column walks
35 -> 35 -> 37 -> 40, independently reproducing the SAFE accumulation.

Lock discipline: `run_lock:daily_outreach:inventory:2026-10-09` = `released`, `_acquired_at` =
2026-10-09 07:12:41 (**naive UTC** = 15:12:41 +08, matching run `d25355ad`). No lock key exists for
2026-10-10, i.e. no run started on 2026-10-10 after the pause.

---

## I. INVENTORY PAUSED BY THE EXISTING SAFE40 RULE

```
INVENTORY_AUTOMATION_ID = automation-1784775229336
INVENTORY_STATUS        = PAUSED
INVENTORY_NEXT_RUN_AT   = None
INVENTORY_UPDATED_AT    = 2026-10-09 19:49:44 +08
INVENTORY_RRULE         = FREQ=HOURLY;INTERVAL=6   (cadence config itself unchanged; 4x/day)
MAX_PAGES               = 3 (prompt export unchanged)
DUPLICATE_INVENTORY_AUTHORITY = false (exactly 1 active Inventory automation)
```

The existing SAFE40 milestone checkpoint (`75fbacd1-fa43-46ea-8388-1d47647c3f4d`, read-only,
`nextRunAt = 2026-10-10 13:57:40 +08`, still ACTIVE) recorded at **2026-10-09 19:47:52 +08**:

```
SAFE40_REACHED -> PAUSE scheduled Inventory, then run EXACT40 NO-SMTP ACCEPTANCE
```

Inventory was paused **2 minutes later** at 19:49:44 +08. So the pause came from the pre-existing
rule, not from this phase. Per the owner's instruction ("if the existing mechanism has already
paused Inventory per the rules, keep it paused"), it is **left paused**.

Important nuance for the owner: this phase **did not** run the EXACT40 no-SMTP acceptance. That
acceptance was the checkpoint's next intended step; with the business decision now `HOLD_NO_SEND`
there is nothing to accept for sending, so no send-side acceptance was started. No new automation,
no second Inventory, no manual run, no cadence change was made.

---

## J. SEND FREEZE — FULLY VERIFIED

```
SMTP_ENABLED             = 0
SMTP_CONNECTIONS         = 0        (no send path active; SMTP_ENABLED=0 and SEND_LOG_TODAY=0)
SEND_LOG_TODAY           = 0        (2026-10-10)
SEND_LOG_TOTAL           = 517      (unchanged; last send 2026-09-16T01:09:52+08:00)
MATERIALIZED_FSP_PLANNED = 0        (final_send_plan.status='planned' = 0)
MANUAL_SEND_QUEUE        = 0
LIVE_SEND_AUTHORIZATIONS = 0 new    (23 historical rows; max approved_at 2026-09-16T01:08:44)
PRESEND                  = PAUSED   (automation-1785804406748)
PREFLIGHT                = PAUSED   (automation-1785804413719)
OUTREACH                 = PAUSED   (automation-1785804421539)
```

Authorization table by status: consumed 9, revoked 7, superseded 7 — **no active/approved
authorization exists**. `final_send_plan` by status: cancelled 229, failed 104, sent 188,
skipped 57, superseded 10 — **zero** `planned`.

`SAFE40_REACHED` was **not** treated as a send permission. No send plan, no authorization, no email.

---

## K. CLIENT DATA PRESERVATION

```
CLIENTS_DELETED = 0
```

Nothing was deleted, truncated, or re-initialised. Preserved as-is: discovered organisations,
brand/store basics, official websites, verified public business emails, email evidence + source URLs,
historical contact records, MX verification outcome, dedup/review results, and the existing DB audit
logs.

Inventory snapshot at 2026-10-10 09:47:42 +08 (read-only):

```
leads                       = 1190
leads with email            = 634
first-party official emails = 378   (email_verified_on_official_site = 1)
lead_discovery_results rows = 555
retail_city_queue rows      = 36
tables                      = 27
```

**Backup (local, controlled storage only — NOT pushed to GitHub):**

```
BACKUP_FILE            = roktandrazo-outreach\output\backups\bd_leads_safe40_batch_hold_20261010_094548.db
BACKUP_AT              = 2026-10-10 09:45:48 +08
BACKUP_SIZE            = 9,322,496 bytes
BACKUP_SHA256          = d8b6eec82071df85e8295187c0ce7f7b061007b21b07f861540014f48b9a75dc
BACKUP_QUICK_CHECK     = ok
BACKUP_INTEGRITY_CHECK = ok
BACKUP_FK_VIOLATIONS   = 0
BACKUP_TABLE_COUNT     = 27
BACKUP_CONTENT_MATCHES_LIVE = true   (leads / discovery / send_log / city_queue row-count parity)
SOURCE_SHA256_UNCHANGED = true
```

Made with the SQLite online backup API on a **read-only** source connection (a consistent backup, not
a raw copy of an active file). The source DB hash was identical before and after.

**No full client email list was committed to GitHub.** This handoff records counts and a handful of
already-public business addresses used as evidence; the owner's full contact data stays local.

---

## L. DATABASE HEALTH

```
DB_QUICK_CHECK       = ok
DB_INTEGRITY_CHECK   = ok
FOREIGN_KEY_VIOLATIONS = 0
```

Ownership split of writes, as required:

- `DIRECT_PRODUCTION_DB_WRITES_BY_THIS_TASK` = **0** (all reads used `mode=ro`).
- Legitimate writes by the **automation's own** scheduled runs (which are not this task's writes):
  4 Inventory runs + their normal audit/queue writes through 2026-10-09 15:19:09 +08.
- The one file created by this task is the **backup copy**, which is a new file, not a write to the
  production DB.

---

## M. FORBIDDEN ACTIONS — NONE PERFORMED

Not done: no code deploy/rollback; no manual Inventory run; no direct `UPDATE`/`DELETE` on production
business data; no automation created, edited, unpaused, or rescheduled; no city-queue edit; no
eligibility-gate change; no send plan; no send authorization; no SMTP contact; no `.env` change; no
second scheduler. `run_inventory_canary3.py` untouched. `PRODUCTION_BUSINESS_CODE_CHANGED = false`.

---

## N. WHEN THE OWNER WANTS TO RE-START THIS BATCH (mandatory re-validation)

The SAFE40 snapshot **must not** be reused as a shortcut. Before any future outreach on this batch:

1. Re-check every email address and official website is still valid.
2. Re-check MX for every domain.
3. Re-check send history, unsubscribes, bounces and the suppression list.
4. Re-check organization dedup.
5. Re-write the outreach copy for that moment's theme/season.
6. Obtain a **new, explicit** send authorization from the owner.

Until all six are done, `CURRENT_BATCH_DISPOSITION = PRESERVE_FOR_FUTURE_OUTREACH` stands and
`CAMPAIGN_BUSINESS_DECISION = HOLD_NO_SEND` remains in force.

**Data-quality observation to carry into step (1):** lead 1221 (`Silver Fox Gift Shop`) carries
`info@mysite.com` with `email_verified_on_official_site = 1`. `mysite.com` is a website-builder
placeholder domain shared by many sites, so this address is very likely **not** a genuine
establishment-specific mailbox. It is flagged here for review during the re-validation step. Nothing
was changed in this phase (read-only; gate changes are out of scope).

---

## O. HANDOFF

- New: `handoff/workbuddy/phases/PHASE4A5R_SAFE40_BATCH_HOLD_NO_SEND.md` (this file).
- Updated: `handoff/workbuddy/CURRENT_STATUS.md`, `handoff/workbuddy/LATEST_RESULT.json`,
  `handoff/workbuddy/CHANGELOG.md`.
- Historical phase reports and JSON blocks are preserved; the 4A.5Q "awaiting scheduled run" record is
  **not** rewritten as if recovery had already happened at that time. 4A.5Q stays as the deployment
  record; 4A.5R is the separate recovery/acceptance record.
