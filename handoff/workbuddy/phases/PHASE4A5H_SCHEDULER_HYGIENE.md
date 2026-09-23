# PHASE 4A.5H — SCHEDULER HYGIENE + CONTINUE UNATTENDED SAFE40

> **Nature:** operations phase. Exactly **one** production-state mutation (disable one legacy Windows
> scheduled task). Everything else is read-only measurement.
> **Authoritative inputs:**
> - Production handoff repo `1569032023yf-star/workbuddy-task-window` @ `232c28fd6f1026fec19c7ad4e07944d6abcab878`
> - Codex release `641b36b87af596a503cdcb8fb518eab66d5ffbb9` (unchanged; not re-deployed)
>
> **Executed:** 2026-09-23 16:52–17:05 +08 (Asia/Shanghai) · clock cross-checked against
> `SELECT datetime('now')` = `2026-09-23 09:01:15` UTC.
>
> **Not performed, at any point:** no Codex work · no production code change · no DB write · no schema change ·
> no manual Inventory run · no manual accumulation loop · no new scheduler or automation · no second checkpoint
> mechanism · no SMTP contact · no FSP materialisation · no authorization created · no send · no manual
> recipient · no guessed email · no third-party evidence · no V2/MX relaxation.

---

## A. DISABLE EXACTLY ONE LEGACY WINDOWS TASK

**Target:** `\RoktRazo-BD-Outreach` — the sole duplicate send-side trigger.

| Evidence | Before | After |
|---|---|---|
| `ScheduledTaskState` | **已启用** (Enabled) | **已禁用** (Disabled) |
| `NextRunTime` | 2026-09-23 23:00:00 | **N/A** |
| `LastRunTime` | 2026-09-22 23:00:01 | 2026-09-22 23:00:01 (preserved) |
| `LastResult` | 0 | 0 |
| `TaskToRun` | `python.exe …\bd_orchestrator.py --stage outreach --live` | **unchanged** |
| `ScheduleType` / `StartTime` | 每天 / 23:00:00 | 每天 / 23:00:00 (unchanged) |
| `RunAsUser` | 15690 | 15690 (unchanged) |

- `TASK_DELETED = false` — the task object still exists; only the enable flag was flipped.
- `TASK_ACTION_MODIFIED = false` — command, schedule, principal and triggers are byte-for-byte as before.
- The disable was completed **before** its 23:00 +08 run time, so tonight's duplicate trigger cannot fire.

### A.1 Why elevation was unavoidable (diagnosed, not guessed)

The first attempt failed closed with a real Windows error:

```
schtasks /change /tn "\RoktRazo-BD-Outreach" /disable
  -> rc = 1   stderr = 错误: 拒绝访问。   (Access denied)
```

Root cause, established by two independent facts:

| Fact | Evidence |
|---|---|
| The agent token is **not elevated** | `whoami /groups` → `Mandatory Label\Medium Mandatory Level`; `BUILTIN\Administrators` listed **只用于拒绝的组** (deny-only, i.e. filtered UAC token); `shell32.IsUserAnAdmin = False` |
| The task file denies the user write | `icacls C:\Windows\System32\Tasks\RoktRazo-BD-Outreach` → `RAKTROZO\15690:(R)` only, while `BUILTIN\Administrators:(I)(R,W,D,WDAC,WO)` holds the write ACE. A `CreateFileW(..., GENERIC_WRITE, ...)` probe was **DENIED** |
| UAC requires human consent | `EnableLUA=1`, `ConsentPromptBehaviorAdmin=0x5`, `PromptOnSecureDesktop=1` |

There is no non-elevated path: modifying a schedule requires write access to the task definition, which the
current token does not have. The disable was therefore performed **once**, through an elevated `schtasks`
invocation with explicit operator UAC consent:

```
Start-Process -FilePath "$env:SystemRoot\System32\schtasks.exe" `
  -ArgumentList '/change','/tn','\RoktRazo-BD-Outreach','/disable' -Verb RunAs -Wait -PassThru
  -> ELEVATED_EXITCODE=0
```

Verification was then repeated with a **separate, non-elevated read-only query** (not the mutating process's
own output), and the neighbouring tasks were re-read to prove they were untouched.

### A.2 Scope discipline

| Task | State before | State after | Touched? |
|---|---|---|---|
| `\RoktRazo-BD-Outreach` | Enabled | **Disabled** | **Yes — the only change** |
| `\RoktRazo-BD-PreSend` | Disabled | Disabled | No |
| `\RoktRazo-BD-PostSend` | Enabled (UNIQUE_REQUIRED) | Enabled | No |
| WorkBuddy Inventory `1784775229336` | ACTIVE | ACTIVE | No |
| Checkpoint `75fbacd1` | ACTIVE | ACTIVE | No |

`WINDOWS_TASK_MUTATED = 1` (the authorized one) · `WINDOWS_TASK_DELETED = 0` ·
`OTHER_WINDOWS_TASKS_MUTATED = 0` · `NEW_SCHEDULER_CREATED = false`.

---

## B. SCHEDULER AUTHORITY AFTER THE CHANGE

All values are live reads taken **after** the disable (2026-09-23 16:53–17:01 +08).

| Required invariant | Live value | Verdict |
|---|---|---|
| Windows `\RoktRazo-BD-Outreach` = Disabled | 已禁用 | **PASS** |
| WorkBuddy Outreach = PAUSED | PAUSED | **PASS** |
| WorkBuddy PreSend = PAUSED | PAUSED | **PASS** |
| WorkBuddy Preflight = PAUSED | PAUSED | **PASS** |
| Inventory `1784775229336` = ACTIVE | ACTIVE | **PASS** |
| Recovery Sync `1786002601925` = ACTIVE | ACTIVE | **PASS** |
| Checkpoint `75fbacd1` = ACTIVE | ACTIVE | **PASS** |
| `BDExecutionHost` = STOPPED | `STATE 1 STOPPED` (DEMAND_START) | **PASS** |
| `DUPLICATE_INVENTORY_AUTHORITY` = false | no Windows Inventory task exists; no Inventory-capable service running | **PASS** |
| `DUPLICATE_ACTIVE_SEND_TRIGGER_COUNT` = 0 | the only duplicate was the task just disabled; PostSend is UNIQUE_REQUIRED, not a duplicate | **PASS** |

No new scheduler or automation was created. WorkBuddy remains the **sole** Outreach/Inventory scheduling
authority.

### B.1 Process-level proof of single-operator discipline

A full command-line scan of all live processes (ctypes PEB read; no WMI/psutil dependency) found:

```
SCANNED_PIDS 435 · UNREADABLE_CMDLINES 160 (system/elevated processes)
PID_MATCHING_bd_orchestrator          = 0
PID_MATCHING_bd_browser/playwright    = 0
PID_MATCHING_manual_accumulation      = 0
```

The only path matches were this session's own WorkBuddy / bash / python processes (they contain the workspace
path in their argv). **No manual Inventory driver and no stray orchestrator was running.**

---

## C. THE 4A.5G CHECKPOINT IS KEPT — AND PROVEN

Existing read-only checkpoint automation **`75fbacd1-fa43-46ea-8388-1d47647c3f4d`** was retained unchanged.

It is admissible because it never launches Inventory, never writes the production DB, never creates an FSP,
never sends, and only measures milestones/blockers/warnings.

**Independently proven to be working in production:** its own scheduled firing at **2026-09-23 15:40:52 +08**
appended a real history record with no human involvement:

| Checkpoint (snapshot time) | SAFE | ACTIVE_CITY | BLOCKERS | WARNINGS |
|---|---|---|---|---|
| 2026-09-23 14:23:36 (4A.5G baseline) | 16 | Saratoga Springs, NY | none | none |
| 2026-09-23 15:40:52 (**automation, unattended**) | 16 | Saratoga Springs, NY | none | zero_progress (business yield) |
| 2026-09-23 16:59:07 (this phase) | 16 | Saratoga Springs, NY | none | zero_progress (business yield) |
| 2026-09-23 17:00:43 (**post-disable, this phase**) | 16 | Saratoga Springs, NY | none | zero_progress (business yield) |

`CHECKPOINT_AUTOMATION_ACTIVE = true` · `NEW_CHECKPOINT_MECHANISM_CREATED = false`.

---

## D. OPERATING-POLICY WORDING CORRECTED

**Defect found:** earlier handoff text implied that ordinary SAFE growth needs fresh user authorization
(e.g. *"Raising SAFE above 16 still requires user authorization … NOT auto"*). That was misleading: the
canonical Inventory automation already **owns** the deployed automatic lanes, and those lanes **are**
authorized for unattended operation.

**Corrected wording now states explicitly** that these EXISTING, already-deployed lanes remain authorized and
require no further authorization:

Places / BrowserMaps discovery · official website resolution · existing first-party enrichment · visible
official email extraction · generic inbox routing · evidence creation · V2/MX SAFE recomputation · city
completion / advancement.

Separate explicit user authorization is required **only** for:

1. a genuinely new enrichment/recovery lane that is not already deployed
2. changing V2 policy
3. changing MX policy
4. changing hygiene / send-eligibility rules
5. manual recipient creation
6. sending

No policy was weakened. No gate, threshold, or eligibility rule was altered.

**Files changed for this correction (documentation only):** `handoff/workbuddy/CURRENT_STATUS.md`
(header, `CURRENT_BLOCKER`, new `SAFE_GROWTH_AUTHORIZATION` field, `NEXT_ACTION`);
`handoff/workbuddy/LATEST_RESULT.json` (`current_blocker`, `NEXT_ACTION`, `REMAINING_BLOCKER`).

---

## E. FRESH READ-ONLY CHECKPOINT (AFTER THE CHANGE)

Source: `bd_leads.db` opened `mode=ro`; plus `schtasks` for the Windows-task fact. Nothing carried forward.

```
ACTIVE_CITY                        = Saratoga Springs, NY          (id 21, status active, provider browser_maps)
LAST_COMPLETED_CITY                = Ithaca, NY                    (id 20, search_matrix_exhausted)
NEXT_PENDING_CITY                  = Cooperstown, NY               (id 22)

READ_ONLY_V2_SAFE_UNIQUE_ORGS      = 16      (fresh V2+MX recompute; SAFE_GE_40 = false)
MATERIALIZED_FSP_PLANNED           = 0

SMTP_ENABLED                       = 0       (system_config SMTP_enabled)
SEND_LOG_TODAY                     = 0       (SEND_LOG_TOTAL = 517; LAST_SEND_AT = 2026-09-16T01:09:52+08:00)

RUNNING_INVENTORY_JOBS             = 0
INVENTORY_LOCK                     = released  (run_lock:daily_outreach:inventory:2026-09-23,
                                                updated 2026-09-23 07:04:00 UTC)

DUPLICATE_ACTIVE_SEND_TRIGGER_COUNT = 0      (was 1; the Windows duplicate is now Disabled)
```

Supporting state, same read:

```
INVENTORY_RUNS_TODAY = 3   INVENTORY_RUNS_FAILED_TODAY = 0   INVENTORY_STALE_CLEANUP_24H = 0
Today's runs: 04:17:47→04:26:48 (3e75c913, 4A.5F Run 1) · 04:30:28→04:33:16 (86d61cde, 4A.5F Run 2)
              07:01:28→07:04:00 (f857bc6b, the canonical 15:00 automation firing UNATTENDED — actual 16/50,
              stop_reason=safe_inventory_gap, status=partial)
manual_send_queue = 0 · final_send_plan(status=planned) = 0 · send_log total = 517 · suppression_list = 63
Saratoga Springs counter: pages_processed = 3, results_seen = 3, new_unique_places = 1,
              duplicate_places = 2, provider_errors = 0, resume_state = query_completed
auto_send_enabled = true (config) — but the effective gate SMTP_enabled = 0 keeps the send path closed
```

**Note on the third run:** the canonical 15:00 automation executed on its own, unattended, with no manual
intervention (15:01:28 +08 start). This is direct evidence that the unattended accumulation regime is live and
that the Operations Host is not dependent on a human driver. Saratoga Springs did **not** advance to
Cooperstown in this round — expected, because the city was only activated at 04:31 UTC today and its own search
matrix is not yet drained. City completion is decided by `retail_city_queue.city_completion_checks`, never by a
round counter.

---

## F. CONTINUATION DECISION

```
READ_ONLY_V2_SAFE_UNIQUE_ORGS = 16  <  40
REAL_ENGINEERING_BLOCKER      = none
=> leave Inventory ACTIVE and continue normal unattended NY-queue operation
```

- No manual accumulation loop was started.
- Zero SAFE gain in a round is **business yield, not a bug**; no code was touched because a city has a low yield.
- The checkpoint automation will surface any genuine runtime regression (repeated identical rows with no state
  transition, lock storm, duplicate Inventory authority, crash/uncaught exception, browser-process leak,
  V2/MX policy regression, DB integrity issue) the next time it runs.

## G. SAFE40 TRIGGER

`SAFE40_REACHED = false`. Scheduled Inventory was **not** paused. PreSend, Preflight and Outreach were **not**
run, and nothing was sent. EXACT40 NO-SMTP acceptance remains gated on
`READ_ONLY_V2_SAFE_UNIQUE_ORGS >= 40` and a separate authorization.

---

## H. SAFETY INVARIANTS

```
SMTP_CONNECTIONS        = 0        OUTREACH_SEND_COUNT      = 0
MATERIALIZED_FSP_PLANNED = 0       AUTHORIZATION_CREATED    = 0
CODE_CHANGES            = 0        DB_WRITES                = 0
DB_SCHEMA_CHANGED       = false    MANUAL_INVENTORY_RUNS    = 0
MANUAL_INVENTORY_LOOP   = false    INVENTORY_PARALLELISED   = false
SECOND_SCHEDULER_CREATED = false   NEW_CHECKPOINT_CREATED   = false
PRODUCTION_CODE_CHANGED = false    CODEX_WORK_PERFORMED     = false
V2_RELAXED = false                 MX_RELAXED               = false
HYGIENE_RULE_CHANGED = false       DISCOVERY_POLICY_REDESIGNED = false
PROVIDERS_OR_SCHEMAS_ADDED = false GUESSED_EMAILS_USED      = false
THIRD_PARTY_EVIDENCE_USED = false  MANUAL_RECIPIENTS_ADDED  = false
INVENTORY_AUTOMATION_RESTORED = n/a (never changed)   PRESEND/PREFLIGHT/OUTREACH = PAUSED/PAUSED/PAUSED
```

---

## I. NON-BLOCKING OBSERVATIONS (recorded, deliberately not acted on)

1. **Four stale `job_runs` rows with `status='running'`** from `stage='status'`, started 2026-07-21 → 2026-07-24.
   They are pre-existing orphans from July, are not Inventory runs, hold no lock, and have no live process.
   They do **not** meet the definition of a runtime regression (they are not "repeated identical rows with no
   state transition" from this phase's work) and were left untouched under the "no DB write" rule.
   Recommended follow-up (needs its own authorization): close them out.
2. **`auto_send_enabled = true`** in `system_config` while `SMTP_enabled = 0`. The effective send gate is
   `SMTP_enabled`, so the send path stays closed; recorded so the pair is not misread as an open channel.
3. **Repo hygiene (unchanged, needs separate authorization):** the handoff repo has 3 untracked scratch files
   (`_cleanup_final.txt`, `_schema.txt`, `_verify_handoff.py`) and has historically tracked `*.db` files
   (violates safe-git rule E; requires an explicitly authorized history rewrite).

---

## FINAL

```
WINDOWS_OUTREACH_DISABLED          = true          (ELEVATED_EXITCODE=0; independently re-verified 已禁用)
DUPLICATE_ACTIVE_SEND_TRIGGER_COUNT = 0

INVENTORY_ACTIVE                   = true          (1784775229336, untouched)
RECOVERY_ACTIVE                    = true          (1786002601925)
PRESEND_PAUSED                     = true
PREFLIGHT_PAUSED                   = true
OUTREACH_PAUSED                    = true

CHECKPOINT_AUTOMATION_ACTIVE       = true          (75fbacd1, proven firing 15:40:52 +08)

ACTIVE_CITY                        = Saratoga Springs, NY
LAST_COMPLETED_CITY                = Ithaca, NY
NEXT_PENDING_CITY                  = Cooperstown, NY

READ_ONLY_V2_SAFE_UNIQUE_ORGS      = 16
MATERIALIZED_FSP_PLANNED           = 0

SAFE40_REACHED                     = false

SMTP_CONNECTIONS                   = 0
OUTREACH_SEND_COUNT                = 0

CODE_CHANGES                       = 0
DB_WRITES                          = 0
INVENTORY_RUNS_MANUAL              = 0

NEXT_ACTION                        = CONTINUE_UNATTENDED_ACCUMULATION (canonical scheduler left running)
STOP                               = true
```
