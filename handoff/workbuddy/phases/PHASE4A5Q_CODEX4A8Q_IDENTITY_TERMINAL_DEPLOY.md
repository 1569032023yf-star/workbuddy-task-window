# PHASE 4A.5Q — DEPLOY CODEX 4A.8Q UNLINKED IDENTITY-REVIEW TERMINAL HOTFIX

> Generated: 2026-10-08T15:34:06+08:00 (Asia/Shanghai)
> Refresh type: **AUTHORIZED PRODUCTION DEPLOYMENT** (single-file hotfix) + simulated recovery proof.
> Production-code payload: `discovery/discovery_service.py` — **1 file only**.
> Deployment scope authorization: PHASE 4A.5Q instruction (§A–§V). NOT a blanket Codex deployment,
> NOT an email-sending authorization.
> Codex counterpart: **PHASE 4A.8Q** — `codex/phase4a8q-identity-terminal-hotfix`.

---

## 1. Outcome / 结论

Codex commit `d34a337f09eea8d165f0f00c0d4935653b822f47` was verified and deployed to production as `discovery/discovery_service.py` **only**, byte-exact.

- PRODUCTION_HASH_BEFORE: `D23C760AEA14C995D859E709ACF898CE8E691DD70B129DF2F4B920D9E9617D07`
- PRODUCTION_HASH_AFTER: `96DCC751DFF7FF9174B556120BDF440211328CCF52B32559509164CB0169AE14`
- Baseline Git blob `2165988a494d1a82ea1a6d5bf1087a132a416679` re-derived independently and hashed to the baseline SHA-256, confirming
  the delivered patch was built against the exact bytes running in production (Gate E **case 1**).
- Isolated validation ran **outside the production directory** against a full copy of the production
  tree; the module under test was proven to be the isolated artifact, not any Codex development tree.
- Whole-file diff = **1 hunk / 1 line replaced by 5 lines**, confined to the `run_website_resolution` else-branch.
  Nothing else in the file changed; no other production module was touched.

**Recovery is NOT yet claimed.** The city/queue/discovery recovery is **scheduled-run dependent**.
The next canonical Inventory run is **`2026-10-08 20:41:04 +08`**, therefore
`POST_DEPLOY_SCHEDULED_VALIDATION_PENDING = true` is reported and
`RESULT = DEPLOYED_AWAITING_SCHEDULED_VALIDATION` is the honest terminal state of this phase.

---

## 2. Root cause being fixed (unchanged from the 4A.5P audit)

`lead_discovery_results.id=433` (Wow! Arcade, Saratoga Springs NY) sat in `website_lookup_pending` with an empty website and `linked_lead_id = NULL`.
The resolver had correctly returned `identity_review` (candidate `https://ohwownickelarcade.com` scored 20 vs the required 80 and was
**not** proven to belong to the merchant), but the else-branch of `run_website_resolution` wrote the row's ORIGINAL
status back, producing **no state transition** — so the row was re-armed every run and 4 of the 9
city-completion predicates stayed false (`staged_pending` stayed true).

Checklist:

```
validation_status = website_lookup_pending
rejection_reason  = website_resolution:identity_review:
website           = empty
linked_lead_id    = NULL
```

Deployment of this hotfix does **not** and must **not** itself change row 433 — the migration must
be produced by the next canonical scheduled run through the fixed code.

---

## 3. Gate E — production file hash hard gate (PASS, case 1)

| item | value |
|---|---|
| expected baseline SHA-256 | `D23C760AEA14C995D859E709ACF898CE8E691DD70B129DF2F4B920D9E9617D07` |
| expected patched SHA-256 | `96DCC751DFF7FF9174B556120BDF440211328CCF52B32559509164CB0169AE14` |
| **actual production SHA-256 at Gate E** | **`D23C760AEA14C995D859E709ACF898CE8E691DD70B129DF2F4B920D9E9617D07`** |
| verdict | **matches OLD/baseline -> case 1, patch preparation allowed** |
| PRE-EXISTING PATCHED? | no — hash did not equal the new value |

Independent cross-check: the baseline commit `641b36b87af596a503cdcb8fb518eab66d5ffbb9` Git blob for `discovery/discovery_service.py` resolves to
`2165988a494d1a82ea1a6d5bf1087a132a416679`, and hashing that blob's bytes gives exactly `D23C760AEA14C995D859E709ACF898CE8E691DD70B129DF2F4B920D9E9617D07` — i.e. the pinned baseline commit
and the running production file are the same content.

---

## 4. Gate F — isolated validation (outside production directory)

Isolation layout: `output/_4a5q_isolated/roktandrazo-outreach`.

575 files copied from the production tree (excluding `data/`, .git, __pycache__ and other
non-runtime dirs). Proof that the reloaded dependencies were the **isolated production** modules
and not the Codex development working copy:

```
DISCOVERY_MODULE = ...\_4a5q_isolated\roktandrazo-outreach\discovery\discovery_service.py
BD_DB            = ...\_4a5q_isolated\roktandrazo-outreach\bd_db.py
HISTORY_XCHECK   = ...\_4a5q_isolated\roktandrazo-outreach\history_crosscheck.py
CITY_QUEUE       = ...\_4a5q_isolated\roktandrazo-outreach\retail_city_queue.py
CAMPAIGN_V2      = ...\_4a5q_isolated\roktandrazo-outreach\campaign_eligible_v2.py
```

### 4.1 CRITICAL FINDING — `core.autocrlf` would have produced the WRONG artifact

The first `git apply` of the delivered patch applied **cleanly** and produced a diff that was
**content-correct**, yet the resulting file hashed to `4132F29760396AB817F73D910B7730E0F4E2E43D68C0315061C13F87A971348C` — not the expected
`96DCC751DFF7FF9174B556120BDF440211328CCF52B32559509164CB0169AE14`.

Byte forensics: baseline **102,579 B / CRLF 0 / bare-LF 2,037** -> patched **104,803 B / CRLF 2,042
/ bare-LF 0**. The +2,224 B delta is exactly one byte per line rewritten to CRLF. Root cause: the
host Git config has `core.autocrlf` set to true at **system** scope (Windows default).

Per §E (no CRLF/LF conversion, no overwrite, no ignoring the hash) this was **not** papered over.
Re-applying with `core.autocrlf`=false / `core.eol`=lf produced **102,761 B / CRLF 0 / bare-LF 2,042** and
hash **`96DCC751DFF7FF9174B556120BDF440211328CCF52B32559509164CB0169AE14`** = **exact match**. The deployed artifact is therefore LF, matching production's
native format. **Deploying the naive `git apply` output would have silently rewritten every line
ending in a production source file while still passing a content diff review.**

### 4.2 Validation results

| check | result |
|---|---|
| `git apply` --check | clean |
| patched SHA-256 vs expected | **exact match** |
| `python -m py_compile discovery/discovery_service.py` | PASS |
| `patches/production/phase4a8q/verify_production_patch.py` | **PASS** — "production baseline-copy transitions: PASS (identity_review, no reselect, not_found, network_retry, linked resolved)" |
| Codex `tests/test_phase4a8q_identity_terminal_hotfix.py` | **4 passed** (see note) |
| existing `tests/test_discovery_service.py` | **17 passed, 3 failed — PRE-EXISTING, not a regression** |
| existing city/business tests | **45 passed** |
| logic changes in patch | **1 hunk, 1 -> 5 lines, single file** |

Note on the Codex test file: it imports `tests/test_phase2b_safe_replenishment.py`, which imports `dev_fsp.py` and
`safe_replenishment.py`. Those helpers are present in the pinned baseline commit but were trimmed from the
production working tree, so the test module could not collect as-shipped. They were restored
**into the isolated tree only, from the pinned baseline commit**, for test execution. Nothing was
added to production.

### 4.3 Regression triage — proving the 3 failures were NOT caused by the patch

A second tree (`output/_4a5q_isolated_base/roktandrazo-outreach`) was built containing the **pristine unpatched** production file
(SHA-256 `D23C760AEA14C995D859E709ACF898CE8E691DD70B129DF2F4B920D9E9617D07`) with otherwise identical contents.

| tree | same 3 tests | whole `tests/test_discovery_service.py` |
|---|---|---|
| pristine baseline (unpatched) | 3 failed | 3 failed, 17 passed, 9 subtests passed |
| patched | **3 failed (identical)** | - |

Both trees fail identically, so the failures are **pre-existing environment/data conditions**, not
introduced by 4A.8Q. No §S rollback trigger.

---

## 5. Gate G — regression checklist + city simulation

### 5.1 Required items (all PASS)

```
UNLINKED_IDENTITY_REVIEW_TERMINAL          = PASS   (identity_review persists)
SECOND_SCAN_DOES_NOT_RESELECT              = PASS   (results_seen = 0 on re-scan)
NOT_FOUND_SEMANTICS_PRESERVED              = PASS   (website_not_found only on explicit not_found)
NETWORK_RETRY_SEMANTICS_PRESERVED          = PASS   (stays website_lookup_pending, retryable)
LINKED_LEAD_RECOVERY_PRESERVED             = PASS   (resolved -> email_extraction_pending + lead website written)
NO_FALSE_OFFICIAL_SITE_VERIFICATION        = PASS   (website stays empty)
NO_NEW_LEAD_CREATED_BY_FIX                 = PASS   (leads count 0)
NO_EMAIL_CREATED_BY_FIX                    = PASS
NO_SAFE_AUTO_PROMOTION                     = PASS
AUDIT_REASON_PRESERVED                     = PASS   (website_resolution:identity_review: retained)
```

### 5.2 City simulation on a CONTROLLED production DB copy (not production)

The simulation drove the **patched production code path** (`run_website_resolution` with an `identity_review` resolver) —
it did **not** hand-write the row with SQL.

```
[BEFORE]  row433 = website_lookup_pending / website '' / linked NULL
[BEFORE]  city_completion_checks(21,'browser_maps') = 5/9
          failing: all_candidates_classified, no_unprocessed_candidates,
                   official_site_recheck, review_recovery
[PATCHED CODE PATH] results_seen = 1, statuses = {'identity_review': 1}
[AFTER ]  row433 = identity_review / website '' / linked NULL
[AFTER ]  city_completion_checks = 9/9
complete_active_city_if_exhausted -> True
activate_next_city -> {id: 22, city: Cooperstown, state: NY, status: active}
city21 -> search_matrix_exhausted (completed_at recorded on the COPY)
```

```
SARATOGA_COMPLETION_CHECKS_EXPECTED = 9/9   (simulated)
CITY_ADVANCEMENT_SIMULATION         = PASS  (simulated)
```

**These are pre-deployment simulations and are explicitly NOT production recovery.** The
simulation copy was deleted; production `bd_leads.db sha256 4e9c308e...283545` was verified unchanged before and after
(identical sha256), so production was never opened for writing during Gate G.

---

## 6. Gate H — backups and pre-deploy snapshot

| artifact | value |
|---|---|
| source-file backup | output/backups/discovery_service_4a5q_pre_20261008_150455.py.bak |
| source sha256 (pre) | `D23C760AEA14C995D859E709ACF898CE8E691DD70B129DF2F4B920D9E9617D07` |
| backup byte-identical | **true**, sha256 re-verified |
| SQLite consistent backup | output/backups/bd_leads_4a5q_pre_20261008_150455.db (9,232,384 B, taken via the sqlite3 backup API — not a raw file copy) |
| backup readability | quick_check ok, integrity_check ok, FK violations 0, 27 tables |
| row 433 inside backup | website_lookup_pending / '' / NULL |
| pre-deploy active city | id 21 Saratoga Springs, NY (`status='active'`) |
| live DB health | quick_check ok, integrity_check ok, FK violations 0 |
| live DB sha256 / mtime | `bd_leads.db sha256 4e9c308e...283545` / 2026-10-08 08:46:08 |
| SAFE authority (pre) | READ_ONLY_V2_SAFE_UNIQUE_ORGS = 35 |

Send-freeze snapshot taken at the same moment: SEND_LOG_TOTAL 517, SEND_LOG_TODAY 0,
MANUAL_SEND_QUEUE 0, FINAL_SEND_PLAN total 588 (historical), bounce_log 63.

---

## 7. Gate I — safe deploy window

```
RUNNING_INVENTORY_JOBS    = 0        (no stage='inventory' row in status='running')
CONCURRENT_INVENTORY      = 0        (process-level command-line scan: no orchestrator,
                                      no browser_maps, no provider child, no manual driver)
INVENTORY_LOCK            = released (run_lock:daily_outreach:inventory:2026-10-08, updated 06:36:59)
DEPLOY_WINDOW_SAFE        = true
```

The 14:29-dispatched run `inventory:2026-10-08:e2e57c0e` was observed in flight at the start of this phase and was
**allowed to finish normally** (14:33:50 -> 14:36:59 +08, `status=partial`/`stop_reason=safe_inventory_gap`). It was neither killed
nor throttled. Code was replaced only after it completed and released the lock.

Pre-existing hygiene artifacts noted but unrelated and untouched: 4 status-stage rows stuck at
`status='running'` from 2026-07-21..24, and 6 inventory rows with `finished_at` NULL all in `status='failed'` state
(2026-07-23..2026-09-02).

---

## 8. Gate J — deployment action

Replace was performed with a same-volume staging file plus `os.replace` (atomic replace), so a
partially written production source file was never observable.

```
staged bytes           = 102,761   hash = `96DCC751DFF7FF9174B556120BDF440211328CCF52B32559509164CB0169AE14`
PRODUCTION_HASH_AFTER  = `96DCC751DFF7FF9174B556120BDF440211328CCF52B32559509164CB0169AE14`
expected               = `96DCC751DFF7FF9174B556120BDF440211328CCF52B32559509164CB0169AE14`
MATCH                  = true
CRLF in deployed file  = 0
stray temp file left   = no
ROLLBACK_PERFORMED     = false     (hash matched on first write)
```

---

## 9. Gate K — post-deploy static verification

```
py_compile (production file)                     = PASS
module import from production path               = PASS (file identity verified)
module-on-disk hash == deployed hash             = true
behavior identity_review  -> identity_review      PASS
behavior not_found        -> website_not_found    PASS
behavior network_retry    -> website_lookup_pending PASS
RUNNING_INVENTORY_JOBS                           = 0
INVENTORY_LOCK                                   = released
row 433 status/website/linked                    = website_lookup_pending / '' / NULL  (UNTOUCHED)
DB quick_check / integrity_check / FK            = ok / ok / 0
```

Library-module integrity (must be byte-unchanged): `retail_city_queue.py` still `03b4c6302dba271b5b0bed34...`; also re-hashed
`campaign_eligible_v2.py`, `broad_ready.py`, `history_crosscheck.py`, `bounce_pipeline.py` — no change to V1/V2 eligibility, MX, suppression,
send history, dedup, schema, city search matrix, `max_pages=3`, cadence, automation IDs,
checkpoints or `.env`.

No manual Inventory was run. Row 433 was not updated by SQL. No database was re-initialized.

---

## 10. Gates L / M / N — SCHEDULED-RUN VALIDATION PENDING

```
NEXT_CANONICAL_INVENTORY_RUN = `2026-10-08 20:41:04 +08`
MANUAL_INVENTORY_RUNS        = 0
SECOND_INVENTORY_SCHEDULER   = false
```

At the time of writing, no canonical run has yet executed the fixed code, therefore:

```
ROW_433_TERMINALIZED_BY_CANONICAL_RUN = NOT YET OBSERVED
SARATOGA_COMPLETION_CHECKS_AFTER      = still 5/9 (production)
SARATOGA_COMPLETED                    = false
COOPERSTOWN_ACTIVATED                 = false (city 22 still pending)
FIRST_COOPERSTOWN_RUN_ID              = null
DISCOVERY_FLOW_RESTORED               = false (recent runs report 0 new provider pages)
POST_DEPLOY_SCHEDULED_VALIDATION_PENDING = true
```

Expected observations on the next run (from the Gate G simulation, **not** a claim of success):
row 433 -> `identity_review` with website empty and `linked_lead_id = NULL` retained and
`website_resolution:identity_review:` retained; city checks 9/9; city 21 `search_matrix_exhausted`; city 22 `active`.
Per §M, if the row migrates in one run and the city switch lands in the following run, that remains
valid and no manual city-advance function may be invoked.

---

## 11. Gates O / Q / R

**SAFE (authoritative recompute, `campaign_eligible_v2.py` + current MX, read-only):**

```
SAFE_BEFORE = 35
SAFE_AFTER  = 35     (a code hotfix does not itself create eligible organizations)
SAFE_GE_40  = false  -> canonical Inventory left RUNNING, not paused
```

**Send freeze held before, during and after deployment:**

```
SMTP_ENABLED               = 0
SMTP_CONNECTIONS           = 0
SEND_LOG_TODAY             = 0
SEND_LOG_TOTAL             = 517
MATERIALIZED_FSP_PLANNED   = 0
MANUAL_SEND_QUEUE          = 0
NEW_LIVE_SEND_AUTHORIZATIONS = 0   (send_authorizations total 23, all historical)
PRESEND / PREFLIGHT / OUTREACH = PAUSED
```

**DB health after deployment:** ok / ok / 0 FK violations. Deployment-attributable DB writes =
**0**. Any data written since is attributable to the pre-existing scheduled Inventory cadence only.

---

## 12. Gate S — rollback conditions (none triggered)

No rollback trigger fired: the post-write hash matched, the module imported, no regression was
introduced (the 3 failures reproduce identically on the unpatched baseline), no eligibility gate
moved, no send activity appeared, and no scheduling conflict was observed. `ROLLBACK_PERFORMED` was
therefore **not** performed and the original code backup was not restored.

---

## 13. Deviations, limitations and follow-ups

1. **Line-ending hazard (new, durable).** The Codex `patches/production/phase4a8q/README.md` instructs a plain `git apply` then a
   hash compare; on this host that step is **silently wrong** because of system-scope
   `core.autocrlf`=true. Any future patch deployment must apply with `core.autocrlf`=false / `core.eol`=lf and
   must verify the full-file hash. Recommended permanent fix: set `core.autocrlf`=false (system scope)
   or add a .gitattributes pin.
2. **Codex test file is not self-contained in production.** `tests/test_phase4a8q_identity_terminal_hotfix.py` depends on
   `tests/test_phase2b_safe_replenishment.py` -> `dev_fsp.py` / `safe_replenishment.py`, which are absent from the production working tree though
   present in the pinned baseline commit. The two helpers were restored into the **isolated tree
   only**. Follow-up for Codex: remove the dev-harness coupling or ship the helper.
3. **3 pre-existing failures** in `tests/test_discovery_service.py`
   (`test_closed_and_no_website_results_enter_manual_review`, `test_staged_places_contact_form_and_no_email_enter_review_pools`, `test_staged_places_without_email_extracts_official_email_to_a0`) — reproduce identically without the patch. Out of scope
   here; recorded so they are not mistaken for 4A.8Q fallout.
4. **Stale rows.** 4 status-stage rows stuck in `status='running'` (July) and 6 inventory rows with
   `finished_at` NULL in `status='failed'` state. Pre-existing; not cleaned in this phase.
5. **Cleanup deferred.** `run_inventory_canary3.py` deliberately left untouched per §P.

---

## 14. Compliance ledger

| requirement | status |
|---|---|
| only `discovery/discovery_service.py` modified | yes — 1 file, 1 hunk |
| 4A.8K/M/N/O/P and 4B.1A/1B NOT deployed | yes (`CODEX_OTHER_PHASES_DEPLOYED` = false) |
| `campaign_eligible_v2.py`/`broad_ready.py`/`history_crosscheck.py`/`bounce_pipeline.py`/`retail_city_queue.py` unmodified | yes (hashes unchanged) |
| V1/V2 rules, MX, send history, dedup, suppression unchanged | yes |
| DB schema / city matrix / `max_pages=3` / 4x-day / automation IDs unchanged | yes |
| second Inventory scheduler | none created |
| manual Inventory | 0 runs |
| direct SQL write to row 433 | none |
| email sending | none |
| new automations / checkpoints / send plans / authorizations | none created |
| DB rollback | not performed (row-level audit facts preserved) |

---

## 15. Machine-readable report

```
PHASE = 4A.5Q
CODEX_PHASE = 4A.8Q
CODEX_FIX_COMMIT = d34a337f09eea8d165f0f00c0d4935653b822f47
CODEX_BRANCH = codex/phase4a8q-identity-terminal-hotfix
CODEX_BRANCH_TIP = a636a99893e19605a3a4e701dc7bf3b9235b6c40
CODEX_BASELINE_COMMIT = 641b36b87af596a503cdcb8fb518eab66d5ffbb9
PRODUCTION_BASELINE_MATCH = true
PRODUCTION_HASH_BEFORE = `D23C760AEA14C995D859E709ACF898CE8E691DD70B129DF2F4B920D9E9617D07`
PRODUCTION_HASH_AFTER = `96DCC751DFF7FF9174B556120BDF440211328CCF52B32559509164CB0169AE14`
PATCH_APPLIES_CLEANLY = true
ISOLATED_VALIDATION_PASS = true
PRODUCTION_PAYLOAD_FILES = 1
PRODUCTION_PAYLOAD = `discovery/discovery_service.py`
UNAPPROVED_FEATURES_INCLUDED = 0
DEPLOYMENT_COMPLETE = true
ROLLBACK_PERFORMED = false
ROW_433_STATUS_BEFORE = website_lookup_pending
ROW_433_STATUS_AFTER = website_lookup_pending
ROW_433_TERMINALIZED_BY_CANONICAL_RUN = false
SARATOGA_COMPLETION_CHECKS_BEFORE = 5/9
SARATOGA_COMPLETION_CHECKS_AFTER = 5/9
SARATOGA_COMPLETED = false
COOPERSTOWN_ACTIVATED = false
CITY_QUEUE_ADVANCEMENT_VERIFIED = false
FIRST_COOPERSTOWN_RUN_ID = null
FIRST_COOPERSTOWN_PROVIDER_PAGES = null
DISCOVERY_FLOW_RESTORED = false
SAFE_BEFORE = 35
SAFE_AFTER = 35
SAFE40_REACHED = false
MAX_PAGES = 3
CANONICAL_INVENTORY_CADENCE = 4x/day
MANUAL_INVENTORY_RUNS = 0
SECOND_INVENTORY_SCHEDULER_CREATED = false
DEPLOYMENT_DIRECT_DB_WRITES = 0
DB_QUICK_CHECK = ok
DB_INTEGRITY_CHECK = ok
FOREIGN_KEY_VIOLATIONS = 0
SMTP_ENABLED = 0
SMTP_CONNECTIONS = 0
SEND_LOG_TODAY = 0
MATERIALIZED_FSP_PLANNED = 0
LIVE_SEND_AUTHORIZATIONS = 0
CODEX_OTHER_PHASES_DEPLOYED = false
HANDOFF_UPDATED = true
POST_DEPLOY_SCHEDULED_VALIDATION_PENDING = true
RESULT = DEPLOYED_AWAITING_SCHEDULED_VALIDATION
```

COMMIT_SHA = ef46bd9f482e71937b7b2ba23dbd07ee0515d47c
PUSH_SUCCESS = true   (origin main e1122ea..ef46bd9)
Recorded in CURRENT_STATUS.md (AJ-M) and LATEST_RESULT.json. The follow-up commit that wrote
this SHA back into the handoff artifacts is a metadata fixup; the content commit above is the
authoritative phase commit.

---

## 16. Plain-language answers (§V)

1. **Was the 4A.8Q hotfix actually deployed?** Yes — one file, `discovery/discovery_service.py`, byte-exact, hash
   `96DCC751DFF7FF9174B556120BDF440211328CCF52B32559509164CB0169AE14`, verified immediately after the write.
2. **Was exactly one state-machine change made?** Yes — one hunk, one line replaced by five,
   only inside the `run_website_resolution` else-branch. Nothing else in the file or the repository changed.
3. **Has row 433 been processed by normal automation yet?** No. It is still
   `website_lookup_pending`, because the fixed code only takes effect on the next scheduled run. No SQL was used
   to force it.
4. **Has Saratoga finished and Cooperstown started?** Not yet in production. Both were proven
   to follow from the fix **in simulation** (9/9 and Cooperstown active), but production still
   shows 5/9 with Saratoga active and Cooperstown pending.
5. **Is discovery producing real requests again?** Not yet — recent runs still report 0 new
   provider pages, which is the expected consequence of the still-blocked city.
6. **SAFE?** 35, unchanged by the deployment, still below 40; Inventory therefore keeps running.

```
RESULT = DEPLOYED_AWAITING_SCHEDULED_VALIDATION
```
