# PHASE 4A.5K-BR — DEPLOY CODEX 4A.8I BOUNCE HEADER NORMALIZATION + RECOVERY VERIFICATION

**Reported:** 2026-09-29 (Asia/Shanghai) · **Type:** authorized production deployment + recovery verification
**Codex commit deployed:** `8dc85f040b5fa08ed376e4707c462182183427a7` (repo `1569032023yf-star/roktandrazo-outreach-codex`, `refs/heads/main`)
**Production-code payload:** `bounce_pipeline.py` — **one file only**

---

## 0. OUTCOME

| Item | Result |
| --- | --- |
| Production bounce-header fix deployed | **PASS** (byte-exact) |
| Post-deploy static validation | **PASS** (6/6 checks) |
| 08:45 Result Recovery bounce-scan failure | **FIXED & VERIFIED** — `BOUNCE_CONSECUTIVE_FAILURES` 7 → **0**, error `Header` → **None** |
| SAFE40 accumulation mainline | **UNTOUCHED** — Inventory `1784775229336` left running, cadence and `max_pages=2` unchanged |
| Send path | **UNTOUCHED** — `SEND_LOG_TOTAL` 517 → 517, `SEND_LOG_TODAY` 0 → 0, no SMTP contact |

---

## A. PRESERVE THE CURRENT SAFE40 MAINLINE

The healthy SAFE40 accumulation configuration was **not** altered. SAFE accumulation and bounce recovery are
independent lanes and were treated as such.

```
INVENTORY_AUTOMATION_ID              = 1784775229336   (ACTIVE, untouched, still running)
INVENTORY_CADENCE                    = 4x/day (FREQ=HOURLY;INTERVAL=6)
WORKBUDDY_DISCOVERY_MAX_PAGES        = 2               (unchanged; four-run acceptance already PASSED)
INVENTORY_PAUSED_FOR_THIS_FIX        = false
INVENTORY_RUN_MANUALLY               = false
V2_MX_CHANGED                        = false
DISCOVERY_POLICY_CHANGED             = false
SECOND_SCHEDULER_CREATED             = false
SECOND_CHECKPOINT_CREATED            = false
```

Live confirmation that the lane was healthy and undisturbed at deploy time:
`RUNNING_INVENTORY_JOBS = 0`, `INVENTORY_RUNS_TODAY = 1`, `INVENTORY_RUNS_TODAY_FAILED = 0`,
`INVENTORY_STALE_CLEANUP_24H = 0`, `INVENTORY_LOCK_TODAY = released`, `PROVIDER_429_TOTAL_ALL_TIME = 0`.

---

## B. PRE-DEPLOY READ-ONLY CHECK

Taken 2026-09-29 10:20:37 +08 over `bd_leads.db` opened `mode=ro`. SAFE was recomputed through the frozen
V2+MX path (`campaign_eligible_v2.select_candidates_for_plan_v2`); no stored flag was substituted.

### B.1 SAFE / city

```
READ_ONLY_V2_SAFE_UNIQUE_ORGS = 19
ACTIVE_CITY                   = Saratoga Springs, NY
LAST_COMPLETED_CITY           = Ithaca, NY
NEXT_PENDING_CITY             = Cooperstown, NY
SAFE_GE_40                    = false
ACTIVE_CITY_QUERY_FAMILIES    = 5 / 20 completed (0 running)
CITY_QUEUE_ADVANCEMENT_VERIFIED = true
```

### B.2 Send / FSP state

```
SMTP_ENABLED                  = 0
SMTP_CONNECTIONS              = 0        (no SMTP socket; verified via process probe)
SEND_LOG_TOTAL                = 517
SEND_LOG_TODAY                = 0
LAST_SEND_AT                  = 2026-09-16T01:09:52+08:00
SEND_AUTHORIZATIONS_TODAY     = 0
OUTREACH_SEND_COUNT_TODAY     = 0
MATERIALIZED_FSP_PLANNED      = 0        (FINAL_SEND_PLAN_TOTAL = 588 historical rows)
PreSend / Preflight / Outreach = NOT ACTIVE — absent from the automation registry; DB-side evidence shows
                                 0 send authorizations today and 0 send_log rows today
```

### B.3 Bounce recovery state — the failure this phase fixes

```
BOUNCE_LAST_SUCCESS_AT        = 2026-09-24T08:46:08+08:00      (5 days stale)
BOUNCE_CONSECUTIVE_FAILURES   = 7
BOUNCE_LAST_ERROR             = "expected string or bytes-like object, got 'Header'"
last_bounce_scan_at (config)  = 2026-09-24T08:46:08+08:00
sync_0845_steps.bounce_scan   = ok=false, at 2026-09-29T08:45:54+08:00,
                                error "run_scan_and_writeback failed: expected string or bytes-like object, got 'Header'"
bounce_log                    = 63 rows
unmatched_dsn                 = 48 rows
```

**Signature confirmed:** the recorded production error is character-for-character the expected
`TypeError: expected string or bytes-like object, got 'Header'`. It is *not* an inference — both the poller
state file and the `system_config.sync_0845_steps` record carry it verbatim.

### B.4 No bounce scan in flight before replacement

A read-only process inventory (ctypes PEB command-line read; no WMI/psutil) showed **no** `bounce_pipeline`,
`result_recovery_sync`, or Inventory process running. The only live Python process was the scheduled SAFE40
checkpoint automation (`output/_4a5g_checkpoint.py`, its own read-only lane), which finished at 10:21 and
exited. The canonical Inventory scheduler was neither stopped nor modified. Replacement was therefore safe.

---

## C. VERIFY CODEX PAYLOAD + DEPLOY

### C.1 Commit scope

`8dc85f04` touches 6 paths, of which exactly **one** is production code:

| Path | Kind | Deployed? |
| --- | --- | --- |
| `bounce_pipeline.py` | **production code** | **YES** |
| `tests/test_bounce_pipeline.py` | test | no (Codex handoff; NOT copied into production) |
| `handoff/CHANGELOG.md` | Codex handoff | no |
| `handoff/CURRENT_STATUS.md` | Codex handoff | no |
| `handoff/LATEST_RESULT.json` | Codex handoff | no |
| `handoff/phases/PHASE4A8I_BOUNCE_HEADER_NORMALIZATION.md` | Codex handoff | no |

Nothing outside `bounce_pipeline.py` was copied into production.

### C.2 The production-code diff is exactly the approved change

Whole-file comparison, production vs the committed Codex blob:

```
HUNKS          = 1
LINES_ADDED    = 4      (2 explanatory comments + 2 corrected lines)
LINES_REMOVED  = 2

@@ -572,8 +572,10 @@
         except Exception:
             continue
         header_msg = email.message_from_bytes(header_bytes)
-        frm = header_msg.get("From") or ""
-        subj = header_msg.get("Subject") or ""
+        # Legacy/8-bit headers can be email.header.Header objects here.
+        # Both regex matching and the stored candidate tuple require text.
+        frm = str(header_msg.get("From") or "")
+        subj = str(header_msg.get("Subject") or "")
         if _FROM_PAT.search(frm) or _SUBJECT_PAT.search(subj):
             candidates.append((uid, frm, subj))
     return candidates
```

```
FROM_HEADER_NORMALIZED    = true
SUBJECT_HEADER_NORMALIZED = true
```

### C.3 Scope audit — region-by-region, all other regions byte-identical

| Region | Verdict |
| --- | --- |
| `_FROM_PAT` / `_SUBJECT_PAT` candidate regex patterns | UNCHANGED |
| `_DOMAIN_INVALID_PATTERNS` / `_MAILBOX_INVALID_PATTERNS` / `_POLICY_BOUNCE_PATTERNS` / `_SOFT_BOUNCE_PATTERNS` | UNCHANGED |
| `classify_bounce` (bounce classification) | UNCHANGED |
| `parse_bounce_email` | UNCHANGED |
| `record_bounce` (suppression / lead write-back policy) | UNCHANGED |
| `record_unmatched_dsn` | UNCHANGED |
| `scan_bounces` (IMAP scan, `BODY.PEEK` — non-destructive) | UNCHANGED |
| `run_scan_and_writeback` | UNCHANGED |
| `_write_poller_status` | UNCHANGED |
| `_fetch_bounce_candidates` | **CHANGED — the only change** |

```
REGEX_CALLSITE_UNCHANGED   = true   (if _FROM_PAT.search(frm) or _SUBJECT_PAT.search(subj):)
CANDIDATE_TUPLE_UNCHANGED  = true   (candidates.append((uid, frm, subj)))
SCHEMA_CHANGED             = false  (0 ALTER/CREATE/DROP TABLE statements, before and after)
SMTP_SEND_LOGIC_TOUCHED    = false
FINAL_SEND_PLAN_TOUCHED    = false
MX_LOGIC_TOUCHED           = false  (6 MX references before = 6 after)
```

Not modified anywhere in the commit: `result_recovery_sync.py`, scheduling, SMTP/send execution,
Final Send Plan, V2, MX, Inventory/discovery, database schema.

### C.4 Hash triple

```
PRODUCTION_BOUNCE_PIPELINE_HASH_BEFORE = dd52acf503c2ed70d72eb8fc80862f3bead7492b6b3f905879493159ea4e052b  (34,894 bytes)
CODEX_BOUNCE_PIPELINE_HASH             = 6bd0fd52330af4efec8dc48ef99a9e91615c76030f08f97decd6c26421cded24  (35,051 bytes)
PRODUCTION_BOUNCE_PIPELINE_HASH_AFTER  = 6bd0fd52330af4efec8dc48ef99a9e91615c76030f08f97decd6c26421cded24  (35,051 bytes)
GIT_BLOB_SHA (codex)                   = 9e0424574d3cfc965385d5ce67553b7952b5d5ea
BYTE_EXACT_MATCH_CODEX                 = true
DELTA_BYTES                            = +157
```

`CODEX_BOUNCE_PIPELINE_HASH` is the SHA-256 of the **raw committed blob** (`git cat-file blob`), not of a
working-tree checkout — the Codex clone had `core.autocrlf=true`, which rewrites LF→CRLF on checkout. Both
production and the committed blob are **LF-only**, so the deploy is byte-exact with no line-ending drift.
Deploy guards that all passed before writing: baseline-hash guard, payload-content guard, LF-only guard.

### C.5 Backup

```
BACKUP_PATH                    = roktandrazo-outreach/output-equivalent local staging:
                                 output/_4a5kbr_backup_bounce_pipeline_20260929_102511.py
BACKUP_SHA256                  = dd52acf503c2ed70d72eb8fc80862f3bead7492b6b3f905879493159ea4e052b
BACKUP_VERIFIED_IDENTICAL      = true
```

Only `roktandrazo-outreach/bounce_pipeline.py` was written. No other file inside the production tree was
created, modified, or deleted.

---

## D. POST-DEPLOY STATIC VALIDATION (before any production IMAP connection)

| # | Check | Result |
| --- | --- | --- |
| D1 | `python -m py_compile bounce_pipeline.py` | **PASS** (exit 0) |
| D2 | `python -m compileall -q bounce_pipeline.py` | **PASS** (exit 0) |
| D3 | import smoke from production cwd — module resolves to the deployed file, SHA-256 matches, fix present | **PASS** |
| D4 | production `tests/test_bounce_pipeline.py` as-is, offline | **PASS** — `Ran 21 tests ... OK` |
| D5 | Codex regression test (out-of-tree, **not** deployed) against the deployed module | **PASS** — `Ran 22 tests ... OK` |
| D6 | same regression test against the **pre-fix** module (control) | **FAIL as expected** — causal proof |

The D6 control is the decisive evidence. Running the Codex regression test against the *backed-up pre-fix*
module reproduces the production failure exactly:

```
File ".../bounce_pipeline.py", line 577, in _fetch_bounce_candidates
    if _FROM_PAT.search(frm) or _SUBJECT_PAT.search(subj):
TypeError: expected string or bytes-like object, got 'Header'
FAILED (errors=1)
```

Pointing the same test at the deployed module turns that failing test green. The only difference between the
two runs is the `str(...)` normalization — the fix is causally confirmed, not merely observed.

The Codex test file was executed from a staging directory with the production tree on `sys.path`. **No test
file was copied into the production tree.**

---

## E. RECOVERY VERIFICATION (real production IMAP)

### E.1 Safety preconditions

- DB backed up first: `data/bd_leads.db.bak_4a5kbr_20260929_102649`, SHA-256 matches the source byte-for-byte,
  `PRAGMA integrity_check = ok`.
- Pre-state preserved to files before any write: `output/_4a5kbr_pre_state_20260929_102649.json`
  (including the *original* failing `sync_0845_steps` blob) and
  `output/_4a5kbr_pre_poller_status_20260929_102649.json`.
- IMAP reads use `BODY.PEEK[...]` → the mailbox is not marked read and no message is altered or deleted.
- `result_recovery_sync.py` is documented as idempotent and as never sending SMTP.

### E.2 Narrow production entry point — `python bounce_pipeline.py --once`

```
{"scanned": 2, "matched": 1, "domain_invalid": 0, "mailbox_invalid": 0,
 "policy_bounce": 0, "soft_bounce": 0, "unmatched_dsn": 1, "unresolved": 1}
exit = 0        errors = []        TypeError = ABSENT
```

### E.3 The exact job that was failing — `python result_recovery_sync.py`

```
run_at          = 2026-09-29T10:27:08.401821+08:00
all_ok          = true
  tracking_sync      ok=true
  bounce_scan        ok=true   at 2026-09-29T10:27:00+08:00   errors=[]
  reply_scan         ok=true
  unsubscribe_scan   ok=true
exit = 0
```

The `bounce_scan` step — the one that raised `TypeError: ... got 'Header'` at 08:45:54 today — now returns
`ok=true` with an empty `errors` list. Two bounce-like candidates were parsed end-to-end:

| final_recipient | status_code | bounce_type | matched_send_log_id | lead_id |
| --- | --- | --- | --- | --- |
| `contact@thecomicskeep.com` | 5.0.0 | unresolved | 592 | 1074 |
| `birdrootscollabs@gmail.com` | — | — | — | — |

### E.4 Recovery state, before → after

| Metric | Before | After |
| --- | --- | --- |
| `BOUNCE_LAST_ERROR` | `expected string or bytes-like object, got 'Header'` | **`None`** |
| `BOUNCE_CONSECUTIVE_FAILURES` | **7** | **0** |
| `BOUNCE_LAST_SUCCESS_AT` | `2026-09-24T08:46:08+08:00` | **`2026-09-29T10:27:16+08:00`** |
| `last_bounce_scan_at` | `2026-09-24T08:46:08+08:00` | **`2026-09-29T10:27:16+08:00`** |
| `sync_0845_steps` — all four steps | `bounce_scan ok=false` | **`all_ok=true`** |
| `HEADER_TYPEERROR_PRESENT` | true | **false** |

The 5-day bounce-recovery outage (7 consecutive daily failures, 2026-09-24 → 2026-09-29) is closed.

### E.5 Idempotency and blast radius

A second `--once` run produced an identical summary and left `bounce_log` at 63 and `unmatched_dsn` at 48 —
both unchanged across the whole run, because the two candidates had already been recorded. Nothing was
double-counted.

```
SEND_LOG_TOTAL     517 -> 517        (unchanged)
SEND_LOG_TODAY       0 ->   0        (unchanged)
BOUNCE_LOG          63 ->  63        (unchanged)
UNMATCHED_DSN       48 ->  48        (unchanged)
IDEMPOTENT_2ND_RUN  = true
DB_INTEGRITY_AFTER  = ok
```

**No email was sent, no SMTP connection was made, no send authorization was created, no Final Send Plan row
was materialised, and no suppression policy or V2/MX standard was changed.**

---

## F. INVARIANTS / FORBIDDEN ACTIONS — CONFIRMED NOT PERFORMED

```
INVENTORY_CADENCE_CHANGED          = false      WORKBUDDY_DISCOVERY_MAX_PAGES_CHANGED = false
INVENTORY_PAUSED_FOR_THIS_FIX      = false      INVENTORY_RUN_MANUALLY               = false
SECOND_SCHEDULER_CREATED           = false      SECOND_CHECKPOINT_CREATED            = false
MANUAL_ACCUMULATION_LOOP_STARTED   = false      V2_RELAXED = false  MX_RELAXED = false
SMTP_CONTACTED                     = false      EMAIL_SENT = false
MANUAL_RECIPIENTS_ADDED            = false      GUESSED_EMAILS_USED = false
FSP_MATERIALISED                   = false      SCHEMA_CHANGED = false
PRODUCTION_CODE_EDITED_BEYOND_PAYLOAD = false   (only bounce_pipeline.py, byte-exact)
CODEX_WORK_PERFORMED               = false      (consume-only; commit only read)
BROAD_READY_USED_AS_SAFE_SUBSTITUTE = false     (SAFE via frozen V2+MX path only)
INVENTORY_AUTOMATION_ACTIVE_UNCHANGED = true    (1784775229336 left RUNNING, untouched)
```

---

## G. RESIDUAL OBSERVATIONS (non-blocking)

1. **The 08:45 sync reports `last_success_at` even when a sub-step fails.** `result_recovery_sync.py`'s
   docstring makes this deliberate ("单步失败不阻塞后续步骤"), and `_step_bounce_scan` swallows the exception,
   so `sync_0845_last_success_at` advanced to `2026-09-29T08:46:02` while `bounce_scan` was failing. Today's
   failure was only visible via `sync_0845_steps[*].ok` and the poller status file. This is a monitoring
   blind spot, not a defect introduced or touched by this phase; no change was made.

2. **A latent sibling of the same bug class was left alone deliberately.** `parse_bounce_email` builds
   `result["original_subject"] = original.get("Subject")` (line 164) without the same `str()` normalization.
   That value can also be a `Header` object and is later bound as a SQLite parameter / JSON value. It is
   outside the approved payload, was **not** changed, and did not trigger in this run (that path uses the
   full-message parser, not the header-only legacy path). Flagged for the next Codex cycle.

3. **`schtasks.exe` / `sc.exe` are blocked by the local sandbox program blacklist**, so Windows scheduled
   tasks and the `BDExecutionHost` service could not be re-verified this phase; the block was not bypassed.
   Substituted DB-side evidence: 0 send authorizations today, 0 `send_log` rows today, last send
   2026-09-16, `SMTP_ENABLED = 0` — consistent with the send path being inactive.

4. **Production source is not version-controlled.** `roktandrazo-outreach/` has no local `.git` and
   `bounce_pipeline.py` is untracked in the enclosing workspace repo, so the deployed fix exists only as an
   on-disk artifact plus the local backup above. The Codex repo remains the authoritative source of the fix.

5. **Old section title bug preserved as-is:** `CHANGELOG.md` carries a stray duplicate heading
   `## 2026-09-29T04:07:00+08:00 — PHASE 4A.5J ACCEPTANCE` immediately preceding the fuller 4A.5J heading.
   Left untouched (not this phase's scope).

---

## H. FINAL

```
PHASE_4A5K_BR_RESULT                  = PASS
CODEX_COMMIT_DEPLOYED                 = 8dc85f040b5fa08ed376e4707c462182183427a7
PAYLOAD_FILES_DEPLOYED                = 1 (bounce_pipeline.py)
PRODUCTION_BOUNCE_PIPELINE_HASH_BEFORE= dd52acf5...ea4e052b
PRODUCTION_BOUNCE_PIPELINE_HASH_AFTER = 6bd0fd52...21cded24
FROM_HEADER_NORMALIZED = true    SUBJECT_HEADER_NORMALIZED = true
HUNKS = 1    OTHER_REGIONS_CHANGED = none
STATIC_VALIDATION                     = 6/6 PASS   (prefix module reproduces the exact TypeError)
BOUNCE_SCAN_RECOVERED                 = true
BOUNCE_CONSECUTIVE_FAILURES           = 7 -> 0
BOUNCE_LAST_SUCCESS_AT                = 2026-09-24T08:46:08 -> 2026-09-29T10:27:16 +08
HEADER_TYPEERROR_PRESENT              = false
READ_ONLY_V2_SAFE_UNIQUE_ORGS         = 19      SAFE40_REACHED = false
ACTIVE_CITY = Saratoga Springs, NY   LAST_COMPLETED_CITY = Ithaca, NY   NEXT = Cooperstown, NY
SMTP_ENABLED = 0   SMTP_CONNECTIONS = 0   SEND_LOG_TOTAL = 517 (unchanged)
SEND_LOG_TODAY = 0   MATERIALIZED_FSP_PLANNED = 0   OUTREACH_SEND_COUNT_TODAY = 0
INVENTORY_AUTOMATION_1784775229336    = LEFT RUNNING, UNTOUCHED
NEXT_ACTION = CONTINUE_UNATTENDED_ACCUMULATION; next canonical 08:45 Result Recovery run is expected to
              record bounce_scan ok=true on its own
STOP = true
```
