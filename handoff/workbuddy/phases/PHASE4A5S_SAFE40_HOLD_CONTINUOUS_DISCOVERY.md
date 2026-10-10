# PHASE 4A.5S — SAFE40 BATCH HELD + CONTINUOUS DISCOVERY RE-AUTHORISED

**Phase type:** OPERATIONS / SCHEDULING-CONTROL ONLY (authorised operational-rule change).
**Generated:** 2026-10-10T10:15:11+08:00 (Asia/Shanghai)
**Canonical Inventory ID:** `automation-1784775229336` — the SAME automation, not a new one.
**Production business code changed:** NO · **Direct production DB writes:** NO · **Emails sent:** NO

---

## A. WHY THIS PHASE EXISTS

The owner has changed the operating decision. Previously, reaching SAFE40 was treated as the
finish line: the pre-existing SAFE40 checkpoint was written to **pause the canonical Inventory**
once `READ_ONLY_V2_SAFE_UNIQUE_ORGS >= 40`. That rule has now been **superseded**:

* The first 40 qualified organisations are **kept** as a sealed batch for a future outreach
  campaign, but
* **discovery must keep running** to find *more* new organisations, and
* **all email sending stays frozen** until the owner separately and explicitly authorises it.

SAFE40 is therefore re-classified from *stop condition* to *historical milestone*.

## B. WHAT WAS ACTUALLY WRONG (ROOT CAUSE)

The block was **not** in production code. It lived in a WorkBuddy automation prompt:

| Layer | Finding |
|---|---|
| `output/_4a5g_checkpoint.py` (the script) | **READ-ONLY.** It measures, diffs against the previous snapshot, and prints `NEXT_ACTION=PAUSE_INVENTORY_THEN_EXACT40_ACCEPTANCE`. It never writes the DB, never touches an automation. |
| Automation `75fbacd1` (the checkpoint) | Its **prompt**, reporting rule 2, instructed the agent to *"then PAUSE the automation ... (id 1784775229336)"*. **This is where the stop condition was hard-coded.** |
| Automation `1784775229336` (Inventory) | Was left `PAUSED` with `next_run_at = NULL` by that instruction. |

So the stop rule was an **operational instruction in an automation prompt**, i.e. it sits in the
supported, first-class automation control plane — **not** in `bd_orchestrator.py`, not in
`campaign_eligible_v2.py`, not in the city queue, and not in any V1/V2/MX gate.

**Consequence:** `DISCOVERY_CONTINUATION_REQUIRES_CODEX_FIX = false`. No production code had to
be touched, no schema change, no gate weakened.

## C. TIMELINE OF THE BLOCK

| When (+08) | Event |
|---|---|
| 2026-10-09 15:12:41 → 15:19:09 | Run `inventory:2026-10-09:d25355ad` finishes `partial`/`safe_inventory_gap` with `actual = 40`, `gap = 10` — **SAFE reaches 40**. |
| 2026-10-09 15:16:27 | Last lead ever collected (`LEAD_LAST_COLLECTED_AT`). |
| 2026-10-09 19:47:52 | Checkpoint run records `SAFE_CHANGED: 37 -> 40` and `SAFE40_REACHED -> PAUSE scheduled Inventory`. |
| 2026-10-09 19:49:44 | Checkpoint agent executes the pause: Inventory `status -> PAUSED`, `next_run_at -> NULL`. |
| 2026-10-09 21:xx, 2026-10-10 03:xx, 09:xx | **Three scheduled discovery runs never happened.** ≈19 h with no discovery. |
| 2026-10-10 10:11:31 | **PHASE 4A.5S** rewrites the checkpoint prompt (pause rule removed). |
| 2026-10-10 10:11:36 | **PHASE 4A.5S** re-activates the SAME Inventory automation. |

## D. THE CHANGE MADE (MINIMAL, IN THE SUPPORTED CONTROL PLANE)

Exactly **two** automation control-plane edits. No production file, no database row, no schema.

### D.1 Checkpoint `75fbacd1-fa43-46ea-8388-1d47647c3f4d` — prompt only

| | Before | After |
|---|---|---|
| Rule 2 | `... then PAUSE the automation "RoktRazo BD Inventory — 4x/day (6h interval) Asia/Shanghai" (id 1784775229336) and STOP ...` | `... then treat SAFE40 as the preserved historical milestone (BATCH_1_HOLD_FOR_FUTURE_OUTREACH, first reached 2026-10-09) and CONTINUE — do NOT pause, disable or edit anything.` |
| FORBIDDEN list | did not mention automations | adds `pausing / disabling / editing / creating ANY WorkBuddy automation — in particular the canonical Inventory 1784775229336 — or any Windows scheduled task` |
| New block | — | `STANDING OPERATING RULE (PHASE 4A.5S ...)`: SAFE40 is a milestone, not a ceiling; `CONTINUOUS_DISCOVERY_AUTHORIZED=true` |
| Stale fact corrected | `WORKBUDDY_DISCOVERY_MAX_PAGES=2` | `=3` (the true 4A.5L/4A.5Q value) |

Evidence: `CHECKPOINT_PROMPT_HAS_PAUSE_RULE = false`, `CHECKPOINT_PROMPT_HAS_NEVER_PAUSE = true`,
prompt length 4,937 chars. `next_run_at` **unchanged** at `2026-10-10 13:57:40 +08` (`1791611860804`),
proving a prompt-only update does not re-anchor an HOURLY rule.

### D.2 Inventory `automation-1784775229336` — status only

| Field | Before | After |
|---|---|---|
| `status` | `PAUSED` | **`ACTIVE`** |
| `next_run_at` | `NULL` | `2026-10-10 16:11:36 +08` |
| `rrule` | `FREQ=HOURLY;INTERVAL=6` | `FREQ=HOURLY;INTERVAL=6` (**unchanged**) |
| `valid_from` | `2026-07-22T16:00:00Z` | unchanged |
| `cwds` | repo `roktandrazo-outreach` | unchanged |
| `prompt` | 1,986 chars, `WORKBUDDY_DISCOVERY_MAX_PAGES=3` | **unchanged** |

**Honest note on the anchor:** re-activating re-anchored the phase to `10:11:36 + 6 h`. The
interval (6 h), the cadence (4×/day) and the rrule are preserved, but the wall-clock phase moved
from ≈`20:4x / 02:4x / 08:4x / 15:1x` to **`16:11 / 22:11 / 04:11 / 10:11` (+08)**. This is the
automation framework's anchoring semantics (any write re-anchors an HOURLY rule), not a cadence
change. It also means the checkpoint now fires at `13:57` — *before* the first resumed run at
`16:11` — so its next report will legitimately say "no new Inventory run yet". The checkpoint is
read-only and no longer pauses anything, so this ordering is harmless and was deliberately **not**
re-phased (that would have been an unnecessary second write).

## E. WHAT WAS DELIBERATELY *NOT* TOUCHED

`bd_orchestrator.py` · `campaign_eligible.py` · `campaign_eligible_v2.py` · `broad_ready.py` ·
`history_crosscheck.py` · `bounce_pipeline.py` · `retail_city_queue.py` · `preflight_gate.py` ·
`discovery/discovery_service.py` · `.env` · database schema · V1/V2 policy · MX policy ·
city search matrix · `max_pages=3` · 4×/day cadence · run lock · city queue & cursors ·
checkpoints · PreSend/Preflight/Outreach · Windows scheduled tasks · `run_inventory_canary3.py`.

Production hotfix integrity re-confirmed: `discovery/discovery_service.py`
SHA-256 `96DCC751DFF7FF9174B556120BDF440211328CCF52B32559509164CB0169AE14`,
102,761 B, CRLF 0, mtime `2026-10-08 15:09:01`, `HOTFIX_HASH_MATCH = true` — not re-deployed,
not overwritten, not rolled back.

## F. BATCH 1 IS PRESERVED

| Item | Value |
|---|---|
| Batch id | `BATCH_1_HOLD_FOR_FUTURE_OUTREACH` |
| Business decision | `HOLD_ALL_OUTREACH` |
| Qualified organisations | **40** (`BATCH1_ORG_COUNT`) |
| Milestone evidence file | `output/SAFE40_BATCH1_MILESTONE.json` — 19783 B, sha256 `025403743c1e38c3c8f4093da570494a…`, 40 org records + lead ids + domain + city + MX + email-source |
| Consistent DB backup | `C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\output\backups\bd_leads_safe40_batch_hold_20261010_094548.db` — 9322496 B, sha256 `d8b6eec82071df85e8295187c0ce7f7b…` |
| Backup verification | `quick_check = ok`, `integrity_check = ok`, FK violations `0`, 27 tables |
| Clients deleted | **0** |
| Clients marked sent | **0** |
| Full email list committed to Git | **NO** (kept in the local controlled DB / local evidence file only) |

A content-level comparison of the live DB against this backup shows **0 differing tables**
(identical row counts *and* identical per-table content digests across all 26 data tables), so the
milestone snapshot is a faithful, current copy of the sealed batch.

## G. SAFE RECOMPUTED (AUTHORITATIVE PATH, CORRECT MX ENVIRONMENT)

| Field | Value |
|---|---|
| Authority | `campaign_eligible_v2.select_candidates_for_plan_v2` (frozen V2 + live MX via `BD_MX_HTTPS_PROXY`), distinct `organization_key` |
| `SAFE_RECOMPUTED_AT` | 2026-10-10 10:12:13 +08 |
| `MX_PROBE` | `ok` — control probe `query_mx("gmail.com")` succeeded in 0.7 s |
| `V2_ELIGIBLE_CANDIDATE_ROWS` | 40 |
| **`READ_ONLY_V2_SAFE_UNIQUE_ORGS`** | **40** |
| `SAFE40_REACHED` | `true` |
| `SAFE_CHANGE_FROM_35` | +5 |

**The `.env` was loaded before importing any business module.** This is the guard against the
4A.5R false-`SAFE = 0` incident: with a broken `HTTP_PROXY` and no `.env`, every MX lookup falls
through the Worker endpoint and returns `dns_error`, which masquerades as "the whole pool became
ineligible". The control probe (`gmail.com` must return `ok`) is what distinguishes a real reading
from a measurement-environment failure. **No false SAFE value was used anywhere in this phase.**

## H. DISCOVERY YIELD — MEASURED PROPERLY

This phase reports what the system actually *produced*, not how many times it ran.

| Metric | Since milestone (2026-10-09 19:47:52) | Since Cooperstown activation (2026-10-08 18:50:05) |
|---|---|---|
| `RAW_DISCOVERED_LEADS` | 0 | 28 |
| `NEW_UNIQUE_ORGS` | 0 | 13 |
| `NEW_LEADS` | 0 | 13 |
| `OFFICIAL_WEBSITES_VERIFIED` | 0 | 6 |
| `FIRST_PARTY_EMAILS_FOUND` | 0 | 6 |
| `NEW_HISTORY_CLEAN_ORGS_WITH_EMAIL` | 0 | 6 |

**The all-zero column is the point.** Since the milestone was recorded, the system produced
**nothing at all** — because the checkpoint paused discovery two minutes later. That is exactly
the failure this phase fixes, and it is reported rather than hidden.

> **Measurement trap caught during this phase:** `leads.collected_at` is stored with a literal
> `T` separator (`2026-10-09T15:16:27`), while the comparison window was first written with a
> space. Because `'T'` (0x54) sorts above `' '` (0x20), the raw `>=` comparison silently matched
> **every** row and reported a fake `13 new orgs since the milestone`. Normalising the column
> (`replace(collected_at,' ','T')`) corrected it to the true value **0**. The same class of
> timestamp-format bug has bitten this project before across `job_runs` / `provider_request_audit`.

## I. CITY QUEUE STATE

| Field | Value |
|---|---|
| `LAST_COMPLETED_CITY` | **Saratoga Springs, NY** (id 21, `search_matrix_exhausted` at `2026-10-08T12:44:19.697812+00:00`) |
| `ACTIVE_CITY` | **Cooperstown, NY** (id 22, active since `2026-10-08T18:50:05.751144+00:00`) |
| `NEXT_PENDING_CITY` | **Lake Placid, NY** (id 23, priority 4) |
| Active-city query families | 3/20 completed |
| Active-city pages / results / unique places | 9 / 129 / 28 |
| Active-city provider errors | 0 |

* The queue was **not** reset, reordered, or hand-advanced. Cooperstown continues from its own
  cursor; Lake Placid is next in the pre-existing order.
* Cooperstown is only 3/20 families in, so it has **17 families of remaining discovery capacity** — resuming it is not a no-op.

## J. ROW 433 IS STILL CORRECT

```text
ROW_433_VALIDATION_STATUS = identity_review
ROW_433_WEBSITE           = (empty)
ROW_433_LINKED_LEAD_ID    = NONE
ROW_433_REJECTION_REASON  = website_resolution:identity_review:
ROW_433_OFFICIAL_MATCH    = 0
ROW_433_RESELECTOR_MATCH  = 0   (not re-armed; the 4A.8Q fix holds)
```

## K. SEND FREEZE — FULLY HELD

```text
SMTP_ENABLED                = 0
SMTP_CONNECTIONS            = 0
SEND_LOG_TODAY              = 0
SEND_LOG_TOTAL              = 517   (last send ever: 2026-09-16T01:09:52.031266+08:00)
MATERIALIZED_FSP_PLANNED    = 0
MANUAL_SEND_QUEUE           = 0
LIVE_SEND_AUTHORIZATIONS    = 0
AUTH_BY_STATUS              = {"consumed": 9, "revoked": 7, "superseded": 7}
PRESEND                     = PAUSED
PREFLIGHT                   = PAUSED
OUTREACH                    = PAUSED
NEW_SEND_AUTHORIZATION      = false
```

SAFE40 reaching 40 was treated as an **inventory milestone, not a send permit**. Nothing about
this phase changes the send posture: sending still requires a fresh, explicit owner authorisation.

## L. HEALTH

```text
POST_DEPLOY_INVENTORY_RUNS        = 4   (all partial / safe_inventory_gap = healthy terminal state)
FAILED_INVENTORY_RUNS             = 0  since deploy
INVENTORY_RUNS_TODAY (business)   = 0   (0 — discovery was paused all day)
STALE_CLEANUPS                    = 0  since deploy
LOCK_CONFLICTS                    = 0  since deploy
HTTP_429                          = 0   (all-time, still zero)
PROVIDER_ERRORS                   = 0  since deploy (60 all-time, historical)
CONCURRENT_INVENTORY              = 0
RUNNING_INVENTORY_JOBS            = 0
INVENTORY_LOCK_TODAY              = absent   (key absent = no lock was ever taken today)
DUPLICATE_INVENTORY_AUTHORITY     = false
DB_QUICK_CHECK                    = ok
DB_INTEGRITY_CHECK                = ok
FOREIGN_KEY_VIOLATIONS            = 0
```

*All-time totals are annotated deliberately: `LOCK_CONFLICTS_ALLTIME = 6890` and*
*`INVENTORY_RUNS_ALL = 7068` are dominated by thousands of junk rows written by a retired*
*2026-07 driver that spun on a missing `[DUPLICATE]` marker. Reporting them as a current health*
*signal would be misleading, so the scoped (since-deploy) figures are the ones that matter.*

### L.1 Why the DB file hash moved but nothing was written

`DB_SHA256` is `bce7bb0d5a1dc0ba6387dad53c17bbc354ad3cf2d515c781eeb0d5a22d1f47fe` while the 09:45 backup hashes to
`d8b6eec82071df85e8295187c0ce7f7b061007b21b07f861540014f48b9a75dc`. The byte difference is a **SQLite WAL/checkpoint artifact**, not a write:

* the live DB's `mtime` is `2026-10-10 08:45:41` — **before this session started** (first probe ~10:09);
* journal mode is `wal`; a `-wal` file (0 B) and `-shm` file are present;
* a **content-level diff of all 26 data tables shows 0 differing tables** — identical row counts
  *and* identical per-table content digests (`CONTENT_DIFF_TABLES = 0`).

Therefore `DIRECT_PRODUCTION_DB_WRITES_BY_THIS_TASK = 0` is asserted on evidence, not on intent.

## M. VERIFICATION STATUS — WHAT IS PROVEN AND WHAT IS NOT

| Claim | Status |
|---|---|
| Stop rule removed from the supported control plane | **PROVEN** (prompt re-read from the automation DB) |
| No production code needed changing | **PROVEN** (rule lived in an automation prompt) |
| Canonical Inventory is the same automation, ACTIVE, 6 h rrule, cadence intact | **PROVEN** |
| No duplicate Inventory authority | **PROVEN** (only `1784775229336` is ACTIVE and drives Inventory; no Windows Inventory task) |
| Batch 1 data + backup + milestone file preserved | **PROVEN** |
| Send freeze intact | **PROVEN** |
| **Discovery actually resumed (new leads appearing again)** | **NOT YET — PENDING.** `DISCOVERY_CONTINUATION_VERIFIED = PENDING`. No Inventory run has occurred since re-activation; the first is scheduled 2026-10-10 16:11:36 +08. Nothing is claimed about real new yield until that run is observed. |

This distinction is deliberate: a scheduling change is not the same as observed production
recovery, and this handoff does not conflate them.

## N. MACHINE-READABLE RESULT

```text
PHASE = 4A.5S

CURRENT_TIME                            = 2026-10-10T10:15:11+08:00
PRODUCTION_HOTFIX_HASH_MATCH            = true

CAMPAIGN_BUSINESS_DECISION              = HOLD_ALL_OUTREACH
FIRST_40_ORGS_PRESERVED                 = true   (40 orgs)
SAFE40_MILESTONE_RECORDED               = true
SAFE40_ACCEPTANCE_STATUS                = COMPLETE (first reached 2026-10-09; not re-run)
CONTINUOUS_DISCOVERY_AUTHORIZED         = true
SAFE40_AUTO_STOP_DISCOVERY_DISABLED     = true
DISCOVERY_CONTINUATION_REQUIRES_CODEX_FIX = false

INVENTORY_AUTOMATION_ID                 = automation-1784775229336
INVENTORY_ACTIVE                        = true
INVENTORY_STATUS_AFTER                  = ACTIVE
INVENTORY_RRULE_AFTER                   = FREQ=HOURLY;INTERVAL=6
INVENTORY_NEXT_RUN_AT                   = 2026-10-10 16:11:36 +08
CURRENT_MAX_PAGES                       = 3
CURRENT_CADENCE                         = 4x/day
FIRST_RESUMED_RUN                       = 2026-10-10 16:11:36 +08

CHECKPOINT_ID                           = 75fbacd1-fa43-46ea-8388-1d47647c3f4d
CHECKPOINT_STATUS                       = ACTIVE
CHECKPOINT_PAUSE_RULE_PRESENT           = false
DUPLICATE_INVENTORY_AUTHORITY           = false
MANUAL_INVENTORY_RUNS                   = 0
NEW_AUTOMATIONS_CREATED                 = false

ACTIVE_CITY                             = Cooperstown, NY
LAST_COMPLETED_CITY                     = Saratoga Springs, NY
NEXT_PENDING_CITY                       = Lake Placid, NY
CITY_QUEUE_RESET                        = false

SAFE_RECOMPUTED_AT                      = 2026-10-10 10:12:13 +08
READ_ONLY_V2_SAFE_UNIQUE_ORGS           = 40
SAFE40_REACHED                          = true
MX_PROBE_OK                             = true

RAW_DISCOVERED_LEADS_SINCE_MILESTONE    = 0
NEW_UNIQUE_ORGS_SINCE_MILESTONE         = 0
NEW_FIRST_PARTY_EMAILS_SINCE_MILESTONE  = 0
NEW_SAFE_ORGS_SINCE_MILESTONE           = 0
NEW_UNIQUE_ORGS_SINCE_COOPERSTOWN       = 13
NEW_FIRST_PARTY_EMAILS_SINCE_COOPERSTOWN = 6
DISCOVERY_CONTINUATION_VERIFIED         = PENDING

FAILED_INVENTORY_RUNS                   = 0
HTTP_429                                = 0
PROVIDER_ERRORS                         = 0
LOCK_CONFLICTS                          = 0
CONCURRENT_INVENTORY                    = 0
DB_QUICK_CHECK                          = ok
DB_INTEGRITY_CHECK                      = ok
FOREIGN_KEY_VIOLATIONS                  = 0

SMTP_ENABLED                            = 0
SMTP_CONNECTIONS                        = 0
SEND_LOG_TODAY                          = 0
MATERIALIZED_FSP_PLANNED                = 0
LIVE_SEND_AUTHORIZATIONS                = 0
NEW_SEND_AUTHORIZATION_CREATED          = false
EMAILS_SENT_BY_THIS_TASK                = 0

V1_CHANGED                              = false
V2_CHANGED                              = false
MX_POLICY_CHANGED                       = false
PRODUCTION_BUSINESS_CODE_CHANGED        = false
DIRECT_PRODUCTION_DB_WRITES_BY_THIS_TASK = 0
CLIENTS_DELETED                         = 0
DATABASE_BACKUP_VERIFIED                = true

RESULT                                  = CONTINUOUS_DISCOVERY_RE_AUTHORIZED_AWAITING_FIRST_RUN
```

## O. PLAIN LANGUAGE

**Are the first 40 clients safe?** Yes. All 40 are intact, nothing was deleted, and there is a
verified consistent backup plus a milestone file that lists all 40 organisations and where each was
found. The complete email list stays local and was not pushed to GitHub.

**Is email still completely stopped?** Yes. Today: 0 sent; the last email ever went out on
2026-09-16. No send plan, no queue, no valid authorisation, all three send jobs PAUSED. Reaching 40
was treated as a stock milestone, not a green light to send.

**Why had finding new clients stopped?** Not a bug in the program. The "achievement" checker
(a scheduled task) had a written instruction that said: when you hit 40, switch the search engine
off. It did exactly that, two minutes after it saw 40 — so the system sat idle for about 19 hours.

**What did we change?** Two instructions in the scheduler, nothing in the actual business
program: (1) the checker no longer switches anything off — it treats 40 as a keepsake milestone;
(2) the search engine itself has been switched back on, same task as before.

**Does it need a programmer?** No. The off-switch was in a scheduler instruction, not in the
code, so this was fixed with the normal scheduler controls. Nothing in the matching rules, the
email checks, or the database was touched.

**Has it actually started finding people again?** Not yet — and I will not pretend otherwise. The
search engine comes back on at **2026-10-10 16:11** (about 6 hours from now); the first real run
should follow shortly after. Until that run is seen, this is a scheduling fix, not a proven
recovery. The next checkpoint is at 13:57 and will correctly report "no run yet".

**How many qualified organisations right now?** 40, re-measured live at 2026-10-10 10:12:13 +08.

**Which city is it working on?** Cooperstown, NY — only 3 of 20 search topics done, so there is
plenty left. Lake Placid is next in line. The queue was not reset.

**One caveat left over for the future:** lead 1221 (Silver Fox Gift Shop) records `info@mysite.com`
while marked "venue verified" — `mysite.com` is a website-builder placeholder, so that address is
almost certainly not the shop's real email. It was left untouched (read-only phase) and belongs on
the re-validation checklist before any future campaign.

---

**STOP.** No further action taken. Next verification point: the first resumed canonical Inventory
run, scheduled `2026-10-10 16:11:36 +08`. Sending remains frozen and requires separate explicit
authorisation.
