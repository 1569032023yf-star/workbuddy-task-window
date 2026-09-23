# PHASE 4A.5G — UNATTENDED NY QUEUE SAFE40 ACCUMULATION (OPERATIONS PHASE, READ-ONLY VERIFICATION)

> Repository authority:
> - `1569032023yf-star/workbuddy-task-window` (branch `main`) = **PRODUCTION SOURCE / PRODUCTION HANDOFF** ← this repo
> - `1569032023yf-star/roktandrazo-outreach-codex` = **DEVELOPMENT SOURCE / CODEX HANDOFF** (none written to in this phase)
>
> Phase executed: 2026-09-23 14:17 – 14:35 +08 (Asia/Shanghai)
> Nature: **OPERATIONS PHASE.** No development, no Codex work, no code change, no DB write, no send.
> The only artefact written to production is this handoff record. All measurements are live reads.

---

## A. SCOPE

Goal: let the **existing canonical Inventory scheduler** continue the NY city queue unattended until
`READ_ONLY_V2_SAFE_UNIQUE_ORGS >= 40`, which is the trigger for the later EXACT40 NO-SMTP ACCEPTANCE.

In scope: verify the operating state, verify the send freeze, measure SAFE live, confirm there is no
duplicate Inventory authority / manual loop, and install a milestone-checkpoint mechanism.

Out of scope (and NOT performed): redesigning discovery, adding providers or schemas, manual Inventory
loops, SMTP, FSP materialization, V2/MX relaxation, manual recipients, Codex work, any production code edit.

---

## B. AUTHORITY ANCHORS (read-only, verified this phase)

| Item | Value | Method |
|---|---|---|
| Production handoff HEAD (entry) | `a8625051f35397f2671d2ba4c4d6e9504cfabe9e` | `git rev-parse HEAD` @ `C:/Users/15690/workbuddy-task-window` |
| Codex release HEAD | `641b36b87af596a503cdcb8fb518eab66d5ffbb9` | `git rev-parse HEAD` @ Codex dev tree — **read only, no Codex work** |
| Deployed liveness file | `discovery/discovery_service.py` SHA256 `d23c760aea14c995d859e709acf898ce8e691dd70b129df2f4b920d9e9617d07` | SHA256 of live file == 4A.5F POST_DEPLOY_SHA256 |
| Live production DB | `roktandrazo-outreach/data/bd_leads.db` (read via `sqlite3 ... mode=ro`) | root `bd_leads.db` is the 0-byte non-authoritative file |

---

## C. OPERATING STATE — LIVE VERIFICATION (2026-09-23 14:18 +08)

### C1. City queue (authority: `retail_city_queue`, state='NY', order by priority,id)

| id | city | status |
|---|---|---|
| 20 | Ithaca | `search_matrix_exhausted` |
| 21 | **Saratoga Springs** | **active** |
| 22 | Cooperstown | pending |
| 23 | Lake Placid | pending |
| 24 | Oneonta | pending |
| 25 | New Paltz | pending |
| 26 | Corning | pending |
| 27 | Glens Falls | pending |
| 28 | Plattsburgh | pending |
| 29 | Watertown | pending |
| 30 | Utica | pending |
| 31 | Binghamton | pending |
| 32 | Poughkeepsie | pending |
| 33 | Syracuse | pending |
| 34 | Albany | pending |
| 35 | Rochester | pending |
| 36 | Buffalo | pending |

- `ACTIVE_CITY_COUNT = 1`, `ACTIVE_CITY = Saratoga Springs, NY`
- `LAST_COMPLETED_CITY = Ithaca, NY` (`search_matrix_exhausted`)
- `NEXT_PENDING_CITY = Cooperstown, NY`; `PENDING_CITY_COUNT_NY = 15`
- `CITY_QUEUE_ADVANCEMENT_VERIFIED = true`
- The pending order matches the operator-specified queue order **exactly** (Cooperstown → … → Buffalo).

### C2. Inventory authority / lock health

| Check | Value |
|---|---|
| `RUNNING_INVENTORY_JOBS` | 0 |
| Inventory process (`bd_orchestrator.py`) present | **none** (full process-command-line scan, 391 PIDs) |
| Stray/manual accumulation driver present | **none** (only this phase's own two diagnostic scripts) |
| `run_lock:daily_outreach:inventory:2026-09-23` | `released` (acquired 04:30:29 UTC, released 04:33:16 UTC) |
| Inventory runs today | 2 — both are the **4A.5F acceptance runs** (`3e75c913` 12:17→12:26 +08, `86d61cde` 12:30→12:33 +08); both `partial` / `safe_inventory_gap`, `actual=16` |
| `INVENTORY_RUNS_TODAY_FAILED` | 0 |
| `INVENTORY_STALE_CLEANUP_24H` | 0 |
| `INVENTORY_JOB_RUNS_TOTAL` | 7 017 |

### C3. TRIGGER AUTHORITY MAP (this phase corrected two stale handoff claims — see section F)

| Trigger | Kind | State | Classification |
|---|---|---|---|
| `1784775229336` RoktRazo BD Inventory (daily 15:00 +08) | WorkBuddy automation | **ACTIVE** | **SOLE Inventory authority** — correct, left untouched |
| `1785804406748` BD Pre-Send | WorkBuddy automation | PAUSED | send path held |
| `1785804413719` BD Preflight | WorkBuddy automation | PAUSED | send path held |
| `1785804421539` BD Outreach | WorkBuddy automation | PAUSED | send path held |
| `1786002601925` BD Result Recovery Sync (daily 08:45 +08) | WorkBuddy automation | ACTIVE | support job; last success 2026-09-23T08:46:11+08; never starts Inventory |
| `75fbacd1-fa43-46ea-8388-1d47647c3f4d` 4A.5G SAFE40 Milestone Checkpoint (daily 15:40 +08) | WorkBuddy automation | **ACTIVE (created this phase)** | read-only milestone checkpoint; never launches Inventory |
| `\RoktRazo-BD-PreSend` | Windows task | **Disabled** | suppressed duplicate (last run 2026-09-08 22:30) |
| `\RoktRazo-BD-Outreach` | Windows task | **Enabled** ⚠️ | legacy duplicate of the canonical Outreach stage — see section F |
| `\RoktRazo-BD-PostSend` | Windows task | **Enabled** | UNIQUE_REQUIRED (no WorkBuddy equivalent); post-send only, non-sending |
| `BDExecutionHost` (RoktAndRazoBDExecutionHost) | Windows service | **STOPPED** (DEMAND_START, exit 1077) | not a live scheduler |

- There is **no Windows task for Inventory** ⇒ **no duplicate Inventory authority exists.**
- `DUPLICATE_INVENTORY_AUTHORITY = false`

### C4. Send freeze (live)

| Invariant | Value | Verdict |
|---|---|---|
| `system_config.SMTP_enabled` | `0` | PASS |
| `MATERIALIZED_FSP_PLANNED` (`final_send_plan.status='planned'`) | `0` | PASS |
| `send_log` rows today | `0` | PASS |
| `OUTREACH_SEND_COUNT_TODAY` | `0` | PASS |
| `send_log` total | 517 | context |
| `LAST_SEND_AT` | `2026-09-16T01:09:52.031266+08:00` | context (no send since 9/16) |
| `manual_send_queue` rows | 0 | PASS (no manual recipients) |

---

## D. SAFE MEASUREMENT (authority: frozen V2 + MX read-only path — NOT copied from any prior report)

Fresh recompute this phase by calling the deployed `campaign_eligible_v2.select_candidates_for_plan_v2`
against the live DB (read-only; in-process MX cache only, no live-policy change, no DB write):

```
READ_ONLY_V2_SAFE_UNIQUE_ORGS = 16
V2_SAFE_CANDIDATE_ROWS        = 16
SAFE_GE_40                    = false
MATERIALIZED_FSP_PLANNED      = 0        (reported separately, never conflated)
```

Distinct `organization_key` set (16 orgs):

```
org:domain:angry-mom-records.com        org:domain:booksale.org
org:domain:cornell.edu                  org:domain:fingerlakestoylibrary.org
org:domain:gmes.com                     org:domain:goretailgroup.com
org:domain:ithaca.edu                   org:domain:ithacachildrensgarden.org
org:domain:jilliansdrawers.com          org:domain:mamagooseithaca.com
org:domain:mimisatticithaca.com         org:domain:museum.cornell.edu
org:domain:soagithaca.org               org:domain:theframeshopithaca.com
org:domain:thehistorycenter.net         org:domain:unclemartysoffice.com
```

Context only — explicitly **NOT** SAFE substitutes:
`BROAD_READY_STORED_FLAG (leads.send_eligibility='broad_outreach_ready') = 95`,
`LEADS_TOTAL = 1115`, `EMAIL_POOL = 604`.
All 16 SAFE orgs are Ithaca-derived; Saratoga Springs has not yet contributed a new eligible org.

`SAFE40_REACHED = false` → per phase rule E, **no pause of Inventory, no EXACT40 acceptance** was run.

---

## E. PRODUCTION CODE INTEGRITY (byte level)

Method: exhaustive git-blob comparison of every `.py` file in Codex release `641b36b8` against the live
production runtime tree (excluding `handoff/`, `docs/`, release-package and candidate-module folders).

| Result | Count |
|---|---|
| Release `.py` files compared | 191 |
| **Byte-identical in production** | **143** |
| Absent in production (dev-only scripts/tests, e.g. `development_safety.py`, `bd_execution_host_service.py`, `main.py`, 12 test modules) | 38 |
| Content-different | 10 |

Content-different files and their nature:

| File | Nature | Runtime risk |
|---|---|---|
| `bd_db.py` | Codex copy carries `.development-copy` dev-safety guard block absent in production | none — guard is inert outside the dev copy |
| `env_loader.py` | same dev-safety scaffolding / credential-isolation block | none |
| `migrations/migrate_city_outreach_40.py` | one-off migration script copy | none |
| `tests/test_dashboard_timezone.py`, `test_discovery_service.py`, `test_inventory_followup.py`, `test_p0_runtime_semantics.py`, `test_preflight_gate.py`, `test_single_smtp_authority.py`, `test_timezone_unified.py` | production retains its own test copies | none (test harness only) |

**Every runtime file on the discovery → V2 → MX → plan → send blast radius is byte-identical**:
`bd_orchestrator.py`, `discovery/discovery_service.py`, `discovery/providers/browser_maps.py`,
`retail_city_queue.py`, `campaign_eligible_v2.py`, `final_send_plan.py`, `drafter.py`
(`preflight_gate.py` differs by line endings only).

```
V2_MX_POLICY_DRIFT = none
FROZEN_FILES_CHANGED_THIS_PHASE = false
DATABASE_SCHEMA_CHANGED = false
PRODUCTION_CODE_CHANGED_THIS_PHASE = false
```

> Note: a first comparison pass reported 155/161 files as different. That was a harness artefact —
> `git archive | tar -x` applied EOL conversion from `.gitattributes`. The authoritative raw-blob
> comparison (`git ls-tree` object id vs `git hash-object` of the live file) is reported above.

---

## F. FINDINGS CARRIED FORWARD (documentation corrections, no state mutation)

1. **`\RoktRazo-BD-Outreach` Windows task is ENABLED, not Disabled.**
   The previous handoff table (verified 2026-09-14) listed it as `Disabled`. Live `schtasks` on
   2026-09-23 shows `Scheduled Task State = 已启用 (Enabled)`, `Next Run Time = 2026-09-23 23:00:00`,
   `Last Run = 2026-09-22 23:00:01`, `Last Result = 0`, action
   `python.exe ...\roktandrazo-outreach\bd_orchestrator.py --stage outreach --live`.
   Corroborated in the DB: `outreach` job_runs fired at 2026-09-21 15:00:04 UTC and 2026-09-22 15:00:02 UTC
   (= 23:00 +08) with `status=stopped`, `stop_reason=final_send_plan_missing`, `actual=0`, and the
   matching `outreach` run-lock acquisitions.
   **Residual risk is structurally bounded, not zero:** the outreach stage stops on
   `final_send_plan_missing`; FSP can only be materialised by Pre-Send, which is PAUSED on the WorkBuddy
   side and Disabled on the Windows side. With `SMTP_enabled=0`, `FSP_PLANNED=0` and 0 sends since
   2026-09-16, no mail can leave through this path today.
   **Recommendation (operator decision, not executed):** set `\RoktRazo-BD-Outreach` to Disabled so the
   runtime trigger set matches the declared "Outreach = PAUSED" state, then re-verify.
   This phase deliberately did **not** mutate it: it is outside the phase's authorised actions, and the
   current dependency chain makes it inert.
2. **`DUPLICATE_ACTIVE_TRIGGER_COUNT`** in the previous handoff was stated as `0` on the basis that both
   PreSend and Outreach were Disabled. PreSend is indeed Disabled; Outreach is not. The duplicate-trigger
   statement is therefore corrected in `CURRENT_STATUS.md` section C.

---

## G. CHECKPOINT MECHANISM INSTALLED (read-only, no second scheduler)

To satisfy the requirement that only *meaningful* milestones are recorded during unattended accumulation —
and that nothing silently drifts — a deterministic read-only checkpoint was installed:

| Artefact | Path | Purpose |
|---|---|---|
| `_4a5g_state.py` | `WorkBuddy/2026-06-05-15-31-42/output/` | live read-only state measurement (`measure()`) |
| `_4a5g_checkpoint.py` | `WorkBuddy/2026-06-05-15-31-42/output/` | diffs against previous snapshot; classifies milestones / blockers / warnings; appends `4a5g_checkpoints.jsonl` |
| Automation `75fbacd1-fa43-46ea-8388-1d47647c3f4d` | WorkBuddy, daily **15:40 +08** | runs the checkpoint after the 15:00 canonical Inventory run and reports |

Checkpoint escalation rules (as installed):
- **BLOCKER** → report the failed invariant and stop fail-closed: `SMTP_enabled != 0`, `send_log today > 0`,
  `FSP_PLANNED > 0`, `concurrent_inventory_jobs > 1`, `inventory_job_failed_today > 0`,
  `stale_cleanup within 24h > 0` (lock storm), `SAFE metric unavailable`.
- **WARNING (not a blocker)** → `inventory_runs_today > 4` (possible duplicate authority),
  `zero_progress_no_state_transition` (business yield, explicitly **not** a software failure),
  SAFE orgs lost.
- **MILESTONE** → active city changed, completed city changed, SAFE count changed, new SAFE orgs,
  `SAFE40_REACHED` (→ pause Inventory, then EXACT40 acceptance, still no send).

Baseline checkpoint (2026-09-23 14:23:36 +08):

```
SAFE=16  ACTIVE_CITY=Saratoga Springs, NY  LAST_COMPLETED=Ithaca  NEXT=Cooperstown
INVENTORY_RUNS_TODAY=2  FAILED=0  STALE_CLEANUP_24H=0  LOCK=released
SMTP_ENABLED=0  FSP_PLANNED=0  SEND_TODAY=0
MILESTONES=['BASELINE_SNAPSHOT_CREATED']   BLOCKERS=none   WARNINGS=none
NEXT_ACTION=CONTINUE_UNATTENDED_ACCUMULATION
```

---

## H. FORBIDDEN ACTIONS — CONFIRMED NOT PERFORMED

```
MANUAL_INVENTORY_LOOP_STARTED      = false
INVENTORY_PARALLELISED             = false
SECOND_SCHEDULER_CREATED           = false   (checkpoint automation is READ-ONLY and never launches Inventory)
PRODUCTION_CODE_MODIFIED           = false
CODEX_WORK_PERFORMED               = false
DATABASE_WRITTEN                   = false   (all reads via sqlite mode=ro)
DISCOVERY_POLICY_REDESIGNED        = false
PROVIDERS_OR_SCHEMAS_ADDED         = false
SMTP_CONTACTED                     = false   (SMTP_CONNECTIONS = 0)
EMAIL_SENT                         = false
MANUAL_RECIPIENTS_ADDED            = false
GUESSED_EMAILS_USED                = false
V2_RELAXED / MX_RELAXED            = false / false
FSP_MATERIALISED                   = false
WINDOWS_TASK_MUTATED               = false   (finding reported only)
SCHEDULER_STATES_CHANGED           = false   (Inventory left ACTIVE; PreSend/Preflight/Outreach left PAUSED; Recovery left ACTIVE)
```

---

## I. PHASE RESULT

```
PHASE                              = 4A.5G (unattended NY queue SAFE40 accumulation — operating state confirmed)
OPERATING_STATE_CONFIRMED          = true
READ_ONLY_V2_SAFE_UNIQUE_ORGS      = 16          (fresh read-only V2+MX recompute, not carried forward)
SAFE_GE_40                         = false
MATERIALIZED_FSP_PLANNED           = 0
ACTIVE_CITY                        = Saratoga Springs, NY
LAST_COMPLETED_CITY                = Ithaca, NY (search_matrix_exhausted)
NEXT_PENDING_CITY                  = Cooperstown, NY
CITY_QUEUE_ADVANCEMENT_VERIFIED    = true
SOLE_INVENTORY_AUTHORITY           = WorkBuddy automation 1784775229336 (ACTIVE)
DUPLICATE_INVENTORY_AUTHORITY      = false
INVENTORY_AUTOMATION_RESTORED      = n/a (left ACTIVE, never changed this phase)
PRESEND_PREFLIGHT_OUTREACH_PAUSED  = true / true / true
RECOVERY_SYNC                      = ACTIVE
SMTP_CONNECTIONS                   = 0
OUTREACH_SEND_COUNT                = 0
BLOCKERS                           = none
NEXT_ACTION                        = CONTINUE_UNATTENDED_ACCUMULATION (canonical scheduler left running)
STOP                               = true (operations phase closed; no send activity initiated)
```

No engineering blocker was detected. Business yield is not a software failure: SAFE stayed at 16 with no
new eligible organization from Saratoga Springs yet, which is expected at this stage of the queue.
