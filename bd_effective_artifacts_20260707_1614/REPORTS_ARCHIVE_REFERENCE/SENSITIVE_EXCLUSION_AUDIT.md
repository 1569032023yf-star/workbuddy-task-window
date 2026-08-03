# SENSITIVE_EXCLUSION_AUDIT.md

> **Codex Handoff — Sensitive File Exclusion Audit**
> 确认交接包和 lab 中不包含任何敏感信息

---

## Exclusion Checklist

### ✅ Excluded from Handoff Package

| Item | Location | Status | Risk if Included |
|------|----------|--------|-----------------|
| SMTP password | `.env` → `BD_SMTP_PASS` | ❌ EXCLUDED | Account takeover |
| IMAP password | `.env` → `BD_IMAP_PASS` | ❌ EXCLUDED | Email access |
| SMTP user | `.env` → `BD_SMTP_USER` | ❌ EXCLUDED | Credential leak |
| Test email | `.env` → `BD_TEST_EMAIL` | ❌ EXCLUDED | Personal email |
| Real customer DB | `data/bd_leads.db` | ❌ EXCLUDED | PII / business data |
| Legacy DB | `data/leads.db` | ❌ EXCLUDED | PII / business data |
| Phase 1 DB | `data/phase1_leads.db` | ❌ EXCLUDED | PII / business data |
| Search history | `data/searched_cities.json` | ❌ EXCLUDED | Strategy leak |
| Browser cookies | (none present) | ✅ N/A | — |
| Browser profile | (none present) | ✅ N/A | — |
| Git credentials | (none present) | ✅ N/A | — |
| SSH keys | (none present) | ✅ N/A | — |

### ✅ Included in Handoff Package (Safe)

| Item | Contents | Why Safe |
|------|----------|----------|
| `CURRENT_STATUS.md` | System overview, no credentials | Business context only |
| `ARCHITECTURE_MAP.md` | Code structure, no data | Technical reference |
| `RUNBOOK.md` | Fix instructions, no credentials | Implementation guide |
| `GUARDRAILS.md` | Safety rules | Defensive documentation |
| `FILE_MANIFEST.md` | File list with descriptions | Inventory only |
| `SENSITIVE_EXCLUSION_AUDIT.md` | This file | Audit trail |

---

## Credential Scan Results

### .env File Keys (DO NOT INCLUDE)

```
BD_SMTP_HOST=smtp.exmail.qq.com     ← infrastructure (low risk but excluded)
BD_SMTP_PORT=465                     ← infrastructure (low risk but excluded)
BD_SMTP_SSL=true                     ← config (low risk but excluded)
BD_SMTP_USER=***@roktandrazo.com     ← SENSITIVE — excluded
BD_SMTP_PASS=***                     ← CRITICAL — excluded
BD_IMAP_HOST=imap.exmail.qq.com      ← infrastructure (low risk but excluded)
BD_IMAP_PORT=993                     ← infrastructure (low risk but excluded)
BD_IMAP_SSL=true                     ← config (low risk but excluded)
BD_IMAP_USER=***@roktandrazo.com     ← SENSITIVE — excluded
BD_IMAP_PASS=***                     ← CRITICAL — excluded
BD_FROM_NAME=Ian                     ← low risk
BD_FROM_EMAIL=***@roktandrazo.com    ← SENSITIVE — excluded
BD_TEST_MODE=true                    ← config (low risk)
BD_TEST_EMAIL=***                    ← SENSITIVE — excluded
```

### Database Tables with PII

| Table | PII Fields | Included? |
|-------|-----------|-----------|
| `leads` | email, store_name, city, state | ❌ NO |
| `send_log` | email, subject | ❌ NO |
| `bounce_log` | email | ❌ NO |
| `suppression_list` | email | ❌ NO |
| `system_config` | (no PII) | ❌ NO (still excluded — real DB) |
| `reply_log` | email, summary | ❌ NO |

---

## Lab Directory Audit

### `roktandrazo-outreach_codex_lab_20260707/`

This directory is **intentionally empty** at handoff time.
Codex will populate it with:

- Test scripts (using mock data only)
- Mock lead data (fake emails, fake store names)
- Documentation artifacts

**Rules for lab contents**:
- No real customer emails
- No real store names from the database
- No .env or credential files
- Mock data must use obviously fake values (e.g., `test@example.com`)

---

## Backup File Audit

### `backup/` directory contents

| File | Sensitive? | Notes |
|------|-----------|-------|
| `a_grade_sendable_*.csv` | YES — contains real emails | Excluded |
| `all_leads_*.csv` | YES — contains real emails | Excluded |
| `b_grade_*.csv` | YES — contains real emails | Excluded |
| `bounce_log_*.csv` | YES — contains real emails | Excluded |
| `suppression_list_*.csv` | YES — contains real emails | Excluded |
| `bd_template_v3_backup_*.py` | No | Code only |
| `bd_template_v4_backup_*.py` | No | Code only |

**All backup CSVs are excluded** from the handoff package.

---

## Verification Steps

Before finalizing the handoff package:

1. `grep -r "password\|secret\|credential" codex_handoff_bd_automation_20260707_1129/` → No results
2. `grep -r "@.*\.com" codex_handoff_bd_automation_20260707_1129/` → Only references to `roktandrazo.com` (brand name, not credentials)
3. No `.db` files in handoff package
4. No `.env` files in handoff package
5. No `cookies` or `profile` directories in handoff package

---

## Post-Fix Security

After Codex completes the fix:

1. **Do NOT commit .env** to any version control
2. **Do NOT include real DB** in any PR or branch
3. **Test with mock data** in the lab directory
4. **Verify fix with test email** (BD_TEST_MODE=true)
5. **Rotate SMTP password** if any credentials were accidentally exposed
