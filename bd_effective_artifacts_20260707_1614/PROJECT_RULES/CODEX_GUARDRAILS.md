# GUARDRAILS.md

> **Codex Handoff — Execution Guardrails**
> Hard rules that MUST NOT be violated during this fix.

---

## Absolute Prohibitions (Zero Tolerance)

### 1. No Real Sends
```
❌ NEVER run: python daily_session.py --live
❌ NEVER run: python daily_operator_auto.py --live
❌ NEVER run: python bd_sender.py (any mode that triggers SMTP)
```
This handoff is **code-fix only**. No emails may leave the server.

### 2. No Database Modifications
```
❌ NEVER run: INSERT / UPDATE / DELETE on bd_leads.db
❌ NEVER run: python b_pool_import.py --live
❌ NEVER modify: data/bd_leads.db schema
```
The fix is purely in Python source files. No DB changes needed.

### 3. No Suppression List Changes
```
❌ NEVER: add_to_suppression() for Message-ID bounces
❌ NEVER: bulk-add any emails to suppression_list
❌ NEVER: remove existing suppression entries
```

**Critical**: Missing Message-ID bounces are a **sender-side defect**, not an invalid recipient.
Adding these emails to suppression would permanently lose valid customers.

### 4. No Credential Exposure
```
❌ NEVER: copy .env file
❌ NEVER: print SMTP_PASSWORD / IMAP_PASSWORD
❌ NEVER: commit .env to git
❌ NEVER: include real credentials in any handoff document
```

### 5. No Confidence Score Batch Updates
```
❌ NEVER: UPDATE leads SET confidence_score='A' WHERE ...
❌ NEVER: UPDATE leads SET email_verified_on_official_site=1 WHERE ...
```
Each lead must be individually browser-verified before promotion.

### 6. No Automation Registration
```
❌ NEVER: create cron jobs
❌ NEVER: register WorkBuddy automations
❌ NEVER: modify existing automation schedules
```

---

## Safe Operations (Allowed)

### ✅ Read-Only Operations
- Read any file in `roktandrazo-outreach/`
- Run `python daily_session.py --dry-run`
- Run `python pool_analysis.py`
- Run `python agent_reply_monitor.py --dry-run`
- Query DB with SELECT (read-only)

### ✅ Code Modifications (This Fix Only)
- Edit `bd_sender.py` — add Message-ID
- Edit `agent_bounce_auditor.py` — add message_id_missing subtype
- Edit `daily_session.py` — add message_id_missing handling
- Create test files in `roktandrazo-outreach_codex_lab_20260707/`

### ✅ Lab Operations
- Write test scripts in the lab directory
- Create mock data for testing
- Document findings

---

## Bounce Classification Rules

| Bounce Type | Suppression? | Rationale |
|-------------|-------------|-----------|
| `hard` (user unknown, mailbox not found) | ✅ YES | Recipient doesn't exist |
| `domain` (DNS failure) | ✅ YES | Domain doesn't exist |
| `policy` (SPF/DKIM/DMARC) | ❌ NO | May be fixable on sender side |
| `message_id_missing` | ❌ NO | **Sender-side defect, NOT recipient issue** |
| `soft` (temporary) | ❌ NO | May resolve on retry |
| `unknown` | ❌ NO | Needs manual review |

**Key rule**: Only suppress when the **recipient address itself** is definitively invalid.
Sender-side technical issues (missing headers, auth failures) are NEVER grounds for suppression.

---

## Testing Boundaries

### In Lab Directory (SAFE)
```
roktandrazo-outreach_codex_lab_20260707/
  ├── test_message_id.py          # Unit test for Message-ID
  ├── test_bounce_classification.py  # Test bounce types
  └── mock_data/                  # Mock leads for testing
```

### In Production Directory (CAUTION)
```
roktandrazo-outreach/
  ├── bd_sender.py                # ✅ Edit allowed (add Message-ID)
  ├── agent_bounce_auditor.py     # ✅ Edit allowed (add subtype)
  ├── daily_session.py            # ✅ Edit allowed (add handling)
  └── data/bd_leads.db            # ❌ READ ONLY — no modifications
```

---

## Git Safety

If git is initialized in `roktandrazo-outreach/`:
```bash
# Check git status before any changes
git status

# Create a branch for the fix
git checkout -b fix/message-id-header

# Commit with clear message
git commit -m "fix: add Message-ID header to prevent policy bounces"
```

If git is NOT initialized:
```bash
# Create backup before editing
cp bd_sender.py bd_sender_backup_20260707.py
cp agent_bounce_auditor.py agent_bounce_auditor_backup_20260707.py
cp daily_session.py daily_session_backup_20260707.py
```

---

## Escalation Rules

If any of these occur during testing, STOP and report:

1. **Any real email is sent** — immediately check send_log, report to user
2. **Database corruption** — restore from backup, report to user
3. **Suppression list modified** — revert, report to user
4. **Credentials leaked** — rotate SMTP password immediately
5. **bounce_log shows new hard bounces** — investigate before proceeding
