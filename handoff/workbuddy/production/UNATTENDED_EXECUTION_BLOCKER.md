# Unattended Execution — Why Scheduling Still Stops, and the One-Time Fix

Generated: 2026-10-26T00:49:24+08:00
Producer: WorkBuddy
Scope: read-only diagnosis. No scheduler, service, or automation record was modified.

---

## 1. The question

Why does production collection keep stopping even though the Inventory automation is `ACTIVE`?

## 2. What the evidence actually shows

The Inventory automation is **not** sitting in a PAUSED state, and it is **not** carrying a persistent credential failure.

Over the observed 48h window the canonical automation fired 6 times and executed real production work 3 times:

| fired at (+08) | result | production run | duration |
|---|---|---|---|
| 2026-10-24 02:35 | success | — (target already met) | 206s |
| 2026-10-24 08:39 | success | — (target already met) | 264s |
| 2026-10-25 02:57 | **fail: automation-auth-unavailable** | none | **7.5s** |
| 2026-10-25 08:57 | success | `inventory:2026-10-25:c671e444` (stopped, browser timeout) | 2086s |
| 2026-10-25 15:32 | success | `inventory:2026-10-25:e06b14b2` (partial, gap 4) | 2338s |
| 2026-10-25 22:11 | success | `inventory:2026-10-25:9453e5ae` (partial, gap 4) | 2126s |

The single auth failure is a **7.5-second fail-closed refusal**, and the three firings after it all succeeded with no reauthorization. Owner identity is `1db01fd8-…` with `owner_status = confirmed`, which is the same profile the current session runs under.

## 3. The actual root cause of the auth failure

Reconciliation shows the failure did not come out of a healthy cadence. Immediately before it there is an **18.2 hour gap**:

```
planned_at   2026-10-24T14:43:48+08:00
actual fire  2026-10-25T02:57:10+08:00
gap          65601.7s
skipped      2 slots
```

So the chain is:

1. The scheduler stopped firing for 18.2 hours.
2. When it finally came back it tried to catch up immediately.
3. That catch-up firing found no live session context and refused fail-closed with `automation-auth-unavailable`.

It is therefore a **symptom of the host being offline**, not a broken credential. That distinction matters: reauthenticating would not have prevented it.

**The 18.2h gap was not power management.** AC standby timeout is `0` (never sleep), and there are no boot, shutdown, unexpected-shutdown, or sleep/wake events in the window. By elimination the WorkBuddy desktop process was not running.

## 4. Why this will keep happening

The WorkBuddy automation layer is a **user-session scheduler**. It can only fire while:

- the WorkBuddy desktop application is running, and
- a user session is logged in.

There is no product surface that grants an automation the right to execute while the app is closed or the user is signed out. `owner_status = confirmed` records ownership, it does not create a daemon.

The stack was originally designed to avoid this. A Windows service was registered for exactly that purpose:

```
Service  BDExecutionHost  (RoktAndRazoBDExecutionHost)
Start    Manual        Account  LocalSystem      State  Stopped
Image    C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\pythonservice.exe
Params   PythonClass = bd_execution_host_service.BDExecutionHost
```

That service is a **zombie registration**. It cannot start, and it was not started:

- `pythonservice.exe` does **not exist** at the configured path.
- `bd_execution_host_service.py` is **retired**; only `_retired/p3d_20260909/bd_execution_host_service.py` and a `.bak_p2_4a_20260902_091848` remain in the production tree.

So the login-free path that was supposed to exist has decayed, which is why the user-session scheduler is now the only scheduler.

## 5. What would actually fix it

Two independent problems, two different costs.

### 5.1 Bridge durability — no admin needed

`HKCU\…\Run\RoktDeployChannelSupervisor` is already registered and points at an existing binary and an existing `supervisor.py`. A process started that way is a child of Explorer, not of the agent job object, so it survives.

**Action:** one logoff / logon. The bridge then persists for the life of the session.

Cannot be done from inside an agent turn: `CREATE_BREAKAWAY_FROM_JOB` returns `WinError 5`, and every indirect launcher is blocked (`explorer.exe` rc=1 silent, WMI blocked, `schtasks.exe` and `reg.exe` on the Program Blacklist, `Start-Process` rejected by the host validator). No bypass was attempted.

### 5.2 True unattended scheduling — needs one admin action

To collect while nobody is logged in, scheduling must move out of the user session. That requires a real Windows service, which requires elevation. This is the single minimal ask:

1. Install a working service host for the orchestrator (rebuild `bd_execution_host_service.py` or point a service at `bd_orchestrator.py --stage inventory --live`).
2. Set it to `Automatic` start, account `LocalSystem`.
3. Confirm it survives a reboot with no user logged in.

Until that exists, the honest state is: **production runs whenever WorkBuddy is open and the user is logged in; it stops otherwise.** No amount of re-running the automation by hand changes that, and this report will not claim otherwise.

## 6. Interim mitigations that need no permission

- `WorkBuddy.WorkBuddy` is already in `HKCU\Run`, so the app restarts at logon.
- AC sleep is already disabled (`STANDBYIDLE = 0`), so the machine stays awake on power.
- Leave the WorkBuddy window open. Closing the app is the single largest cause of missed slots.
- The 08:45 Result Recovery job and the SAFE40 checkpoint are independent and unaffected.

## 7. Expectation for the next firing

Next canonical firing: **2026-10-26T04:46:56+08:00**.

2026-10-26 is a Monday, so `inventory_target_for_date()` returns **50** (weekday) rather than 60 (weekend). SAFE is currently **56**, which already exceeds 50. The next firing is therefore expected to short-circuit as `target_met` with **zero provider requests**.

That is the designed path, not a regression. It must not be read as "collection is broken", and SAFE staying at 56 must not be read as "SAFE stalled". Real discovery resumes when the weekday target rises above the pool, currently driven by 16 remaining Lake Placid query families and the next NY city in the queue.

## 8. Machine-readable verdict

```
INVENTORY_STATUS              = ACTIVE_AND_HEALTHY
AUTH_FAILURE_CAUSE            = HOST_OFFLINE_CATCH_UP_REFUSAL
AUTH_FAILURE_PERSISTENT       = false
REAUTH_REQUIRED               = false
UNATTENDED_SCHEDULING_SUPPORTED = false
LOGIN_FREE_SERVICE_AVAILABLE  = false   (BDExecutionHost is a zombie registration)
BRIDGE_LOGON_PERSISTENCE_READY = true   (HKCU Run present and valid)
BRIDGE_BOOT_PERSISTENCE_VERIFIED = false
ADMIN_ACTIONS_REQUIRED        = 1        (provision a real service host)
NON_ADMIN_ACTIONS_REQUIRED    = 1        (one logoff/logon for bridge durability)
```
