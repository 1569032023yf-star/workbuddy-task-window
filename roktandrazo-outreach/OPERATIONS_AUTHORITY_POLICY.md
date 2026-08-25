# BD Outreach — Production Decision Authority Policy

**Document type:** Operations Policy (authority matrix)
**Established by:** P2.3C — Production Decision Authority Governance
**Scope:** roktandrazo-outreach production send chain (Windows Task Scheduler + Local Python + WorkBuddy Agent + Ian/HUMAN OWNER)
**Status:** Active. This document is the authoritative source for *who may decide what* in the production system. It does not modify code, DB, schema, or Automation.

---

## 1. Three Execution Authorities

| # | Authority | Nature | Role |
|---|-----------|--------|------|
| 1 | **LOCAL PRODUCTION SYSTEM** | Windows Task Scheduler + Local Python | Deterministic rule engine. Executes the send chain when all hard gates PASS. |
| 2 | **WORKBUDDY AGENT** | Intelligent Enrichment + Exception Analysis | Investigates, enriches, analyzes. Never a production scheduler or send authority. |
| 3 | **IAN / HUMAN OWNER** | Business & Risk Decision | Final authority for incidents, scale, architecture, and policy changes. |

---

## 2. A. Local Production System — What It May Auto-Decide

All items below are **deterministic rules**. Once the standing hard gates PASS, the local system
executes automatically **without re-asking Ian every day**:

- OSM / already-configured Discovery normal operation
- normalization
- dedup
- timezone enrichment
- organization_key
- MX
- Campaign Eligible V2
- FSP
- **real preflight** (P2.3B — traceable, no hardcoded pass)
- Fresh Authorization
- recipient local send window
- SMTP send
- bounce / reply recovery
- suppression
- daily report

**Normal production preconditions (all required):**
`manual_pause=false` AND `standing_authorization=true` AND `risk_gate=clear`
AND V2 PASS AND Preflight PASS AND normal send window.

> **DAILY_MANUAL_SEND_CONFIRMATION_REQUIRED = false**
> The local system must NOT re-prompt each day with "是否发送？" / "是否继续？" / "是否授权今晚发送？"
> when all gates are green.

---

## 3. B. WorkBuddy — What It May Self-Decide (no send trigger)

WorkBuddy is positioned as **INTELLIGENT ENRICHMENT + EXCEPTION ANALYSIS**, not a production scheduler.

Allowed without triggering send:
- Process B/B2/manual_review priority queues
- Search official websites
- Judge which site is the merchant's first-party official site
- Find public email on the official site
- Supplement `evidence_url` / `evidence_snippet`
- Analyze JS-heavy websites
- Analyze anomalous DSN
- Analyze bounce root cause
- Analyze production bugs
- Propose fix recommendations
- Generate management summaries

**Hard rule:** Any WorkBuddy enrichment result must be re-fed through the gates:
`V2 → MX → FSP → Preflight` — it does **NOT** become a send permission on its own.

---

## 4. C. WorkBuddy — What It May NOT Self-Decide

Unless Ian's current message explicitly authorizes it, WorkBuddy must NOT on its own:
- Send real emails
- Use send-window override
- Clear `manual_pause`
- Modify `standing_authorization`
- Clear `risk_gate`
- Increase send volume
- Lower V2 standards
- Allow `guessed_email`
- Modify locked template
- Switch SMTP provider
- Modify production Scheduler authority
- Delete production Tasks
- Modify database schema
- Create new sender
- Create new pipeline
- Mass-delete / mass-clean data
- Auto-switch to the next State experiment

---

## 5. D. Ian — What Requires Explicit Approval

**IAN_APPROVAL_REQUIRED = true** for:
1. Whether to resume sending after a production incident
2. Send-scale escalation: 5 → 10 → 20 → 30+
3. Modify ICP
4. Modify state / market experiment direction
5. Modify template core commercial content
6. Modify SMTP / provider
7. Modify security-gate thresholds
8. Delete production assets
9. Add paid external services
10. Major architecture changes

---

## 6. E. Production Bug Rule

If a clear production bug is found, WorkBuddy may:
- Investigate
- Reproduce
- Locate root cause
- Output a minimal fix proposal

But by default:
**CODE_CHANGE_AUTHORITY = limited**

Direct narrow fixes allowed only when:
1. Ian has explicitly authorized the fix; **OR**
2. The current task is itself an explicitly authorized production bug fix.

Forbidden: discover a problem → refactor other modules on the side.

---

## 7. F. Risk Escalation

On the following, the local system **auto fail-closed / pause**:
- bounce rate over threshold
- DNSBL / sender reputation
- SMTP / IMAP failure
- V2 / MX anomaly
- duplicate-send risk
- stale FSP / auth
- Preflight FAIL
- unexpected production state

WorkBuddy may auto-analyze, but:
**RESUME_SEND_DECISION = IAN**

WorkBuddy must NOT self-resume sending just because it judges "the issue should be fine."

---

## 8. G. Human Review Permission

In `/review`, Ian may:
- Reject
- Defer
- Confirm target merchant
- Provide / confirm official-email evidence

But human approval itself does **NOT** bypass V2:
`Human Verified → V2 → MX → FSP → Preflight → Send`

**HUMAN_REVIEW_CAN_BYPASS_V2 = false**

---

## 9. Final Authority Matrix (machine-readable)

```
PRODUCTION_SCHEDULER_AUTHORITY = Windows Task Scheduler (+ Local Python)
WORKBUDDY_ROLE = Intelligent Enrichment + Exception Analysis (NOT scheduler/send authority)
IAN_ROLE = Business & Risk Decision Owner (final authority)

DAILY_MANUAL_SEND_CONFIRMATION_REQUIRED = false
LOCAL_SYSTEM_CAN_AUTO_SEND_WHEN_ALL_GATES_PASS = true
WORKBUDDY_CAN_DIRECTLY_SEND = false
WORKBUDDY_CAN_RELEASE_MANUAL_PAUSE = false
WORKBUDDY_CAN_CHANGE_V2 = false
WORKBUDDY_CAN_CHANGE_SEND_SCALE = false

IAN_APPROVAL_REQUIRED_FOR_RESUME_AFTER_INCIDENT = true
IAN_APPROVAL_REQUIRED_FOR_SCALE_UP = true
IAN_APPROVAL_REQUIRED_FOR_ARCHITECTURE_CHANGE = true

HUMAN_REVIEW_CAN_BYPASS_V2 = false
```

---

*This policy is documentation only. It does not alter code, database, schema, or Automation
configuration. Code-level safety gates (V2, explicit MX, suppression, bounce history,
previously_sent, duplicate org, manual_pause, standing_authorization, risk_gate, locked V5,
timezone) remain enforced independently of this document.*
