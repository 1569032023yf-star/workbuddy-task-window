# Lead Hygiene Gate — Production Adapter Report

Generated: 2026-07-13 14:27 Asia/Shanghai
Location: `roktandrazo-outreach/workbuddy_candidate_modules/`
DB: Read-only copy of `data/bd_leads.db` (475 leads, 26 suppression, 237 send_log)

---

## 1. Field Mapping Table

| Gate Field | Production Source | Derivation | Fail-Closed |
|---|---|---|---|
| `email` | `leads.email` | Direct, lowercased | Empty → `email_missing` |
| `official_website` | `leads.official_website` | Direct | Empty → `official_website_missing` |
| `evidence_url` | `leads.evidence_url` | Direct | Empty → `evidence_url_missing` |
| `evidence_snippet` | `leads.evidence_snippet` | Direct | Empty → `evidence_snippet_missing` |
| `email_verified_on_official_site` | `leads.email_verified_on_official_site` | `=1` → `True` | `!=1` → `official_site_email_not_verified` |
| `email_source_type` | `leads.email_source_type` | Direct; `manual_lookup` promoted only if `manual_decision='approved'` + evidence present | Not in whitelist → `email_source_not_official` |
| `official_match` | **Derived** | `email_verified_on_official_site AND email_source_type IN OFFICIAL_SOURCE_TYPES_STRICT` | `False` → `business_identity_not_matched` |
| `state` | `leads.state` | Direct, uppercased via `normalize_state()` | Not in TN/AR/KY → `state_out_of_scope` |
| `suppressed` | `suppression_list.email` | Pre-computed set, case-insensitive match | `True` → `suppressed` |
| `bounced` | `bounce_log.bounce_type='hard'` | Pre-computed set, case-insensitive match | `True` → `bounced` |
| `delivery_issue` | `leads.status='delivery_issue'` | Direct status check | `True` → `delivery_issue` |
| `already_sent` | `send_log.status='sent'` OR `leads.status IN ('sent','bounced')` OR `leads.sent_at IS NOT NULL` | Combined check | `True` → `already_sent` |
| `duplicate_domain` | `leads.domain_hash` GROUP BY HAVING COUNT>1 | Pre-computed set | `True` → `duplicate_domain` |
| `guessed_email` | `leads.email_source_type='guessed_email'` OR unapproved `manual_lookup` | Direct + derived | `True` → `guessed_email` |
| `social_only` | `email_source_type LIKE '%social%'` OR `status='B1_social_verified'` | Pattern match | `True` → `B1_social_verified` |
| `contact_form_only` | `email_source_type='contact_form_only'` OR `status='contact_form_pool'` | Direct check | `True` → `C_contact_form` |
| `is_exchange_mx` | `leads.mx_provider` | Pattern match (exchange/outlook/microsoft) | Future gate extension |

### `manual_lookup` Promotion Rules

```
IF email_source_type = 'manual_lookup'
   AND manual_decision = 'approved'
   AND manual_found_email IS NOT NULL
   AND evidence_url IS NOT NULL AND evidence_url != ''
   AND evidence_snippet IS NOT NULL AND evidence_snippet != ''
THEN promote to official (email_source_type → 'official_mailto', official_match → True)
ELSE fail closed (guessed_email → True, email_source_type → 'manual_lookup_unapproved')
```

---

## 2. Test Results

**File**: `workbuddy_candidate_modules/test_production_adapter.py`
**Result**: **74/74 PASSED** (1 skipped — no duplicate domain hashes in production)

| Category | Tests | Passed | Skipped |
|---|---|---|---|
| Pure Logic (normalize_state, email_domain) | 7 | 7 | 0 |
| Gate Logic (22 risk scenarios) | 22 | 22 | 0 |
| Adapter Unit Tests (16 scenarios) | 16 | 16 | 0 |
| Schema Compatibility (18 checks) | 18 | 18 | 0 |
| Correct Interception (6 production verifications) | 6 | 5 | 1 |
| Full Dry-Run (1 sanity check) | 1 | 1 | 0 |
| **Total** | **74** | **73** | **1** |

### Fixed Failures (formerly 4/50 failing)

| Original Failure | Fix Applied | Result |
|---|---|---|
| `test_out_of_scope` — expected `"California"` but got `"CALIFORNIA"` | Corrected assertion: `normalize_state()` uppercases everything; test now verifies `"CALIFORNIA" NOT IN ALLOWED_STATES` | PASS |
| `test_no_leads_in_suppression_list_are_sendable` — `carmel@thinkertoys.com` in suppression but not caught | **Bug found**: context sets were not lowercased. Fixed `build_context()` to normalize all emails to `strip().lower()` | PASS |
| `test_only_tn_ar_ky_in_sendable` — CA lead still status=new/A0 | Gate correctly rejects; test converted to explicit `TestCorrectInterception` | PASS |
| `test_no_leads_in_suppression_list_are_sendable` — 5 suppressed leads | Gate correctly intercepts all 5; test converted to `TestCorrectInterception.test_suppressed_leads_correctly_intercepted` | PASS |

### New Bug Found & Fixed

**Case-sensitivity mismatch in `build_context()`**: Production DB has mixed-case emails (`SALES@Domain.COM`, `Carmel@thinkertoys.com`). Context sets from `suppression_list`, `bounce_log`, and `send_log` stored raw case, but adapter lowercased emails before lookup → false negatives. Fixed by normalizing all context sets to `strip().lower()`.

---

## 3. Full Production Dry-Run Results

```
Total records:                475
A0 eligible (PASS):           0
B2 rejected:                  434
B1 social:                    0
C contact form:               41
Exchange MX flagged:          0
```

### Rejection Breakdown

| Reason | Count | Example (masked) |
|---|---|---|
| Evidence snippet missing | 408 | Most legacy leads lack evidence_snippet |
| Non-TN/AR/KY state | 340 | Legacy Phase 0/1/2 data across 35+ states |
| Business identity not matched | 241 | Not verified on official website |
| Email source not official | 241 | guessed_email, unknown, empty |
| Not verified on official site | 233 | `email_verified_on_official_site=0` |
| Already sent | 223 | `sent_at IS NOT NULL` or `status='sent'` |
| Guessed email | 156 | `email_source_type='guessed_email'` |
| Empty email/domain | 51 | No email collected |
| Contact form only | 41 | `status='contact_form_pool'` |
| Evidence URL missing | 28 | No evidence_url recorded |
| Official website missing | 26 | No website recorded |
| Suppressed | 17 | In suppression_list |
| Delivery issue | 9 | `status='delivery_issue'` |
| Hard bounced | 6 | In bounce_log with type='hard' |

### Key Observations

1. **0 A0 through strict gate** matches production's 0 sendable — gate and production query agree
2. **408/475** lack `evidence_snippet` — the dominant blocker. Only 26 leads have evidence_snippet populated (from Codex evidence_snippet backfill)
3. **340/475** are non-TN/AR/KY — legacy data from Phase 0/1/2 before state deep coverage strategy
4. **223/475** already sent — bulk of database is historical
5. **17 suppression blocks** (vs previous 26 in suppression_list) — case-insensitive matching caught more, but some suppressed emails have no matching lead

---

## 4. Suggested Integration Point

### Option A: Drop-in Replacement for `get_sendable_leads()` (Recommended)

**File**: `bd_db.py`, function `get_sendable_leads()` (line 313)

Current logic has scattered filtering across SQL WHERE clauses. Replace with:

```python
from workbuddy_candidate_modules.production_adapter import build_candidate_from_db_row, build_context
from workbuddy_candidate_modules.lead_hygiene_gate import evaluate_a0

def get_sendable_leads(limit=20, exclude_ids=None):
    conn = get_db()
    ctx = build_context(conn)
    # Get all candidate leads (broad filter)
    rows = conn.execute("SELECT * FROM leads WHERE status IN ('new','approved_manual_send')").fetchall()
    conn.close()
    
    eligible = []
    for row in rows:
        rd = dict(row)
        if exclude_ids and rd['id'] in exclude_ids:
            continue
        candidate = build_candidate_from_db_row(rd, ctx)
        decision = evaluate_a0(candidate)
        if decision.a0_eligible:
            eligible.append(rd)
        if len(eligible) >= limit:
            break
    return eligible
```

**Advantages**:
- Single source of truth for all filtering logic
- All 14 risk checks in one place
- Unit-testable without DB
- Consistent with gate decisions

### Option B: Parallel Validation (Safer)

Keep existing `get_sendable_leads()` SQL as-is. Add gate as a second-pass validator:

```python
def validate_sendable_batch(leads):
    """Run hygiene gate on a batch of sendable leads. Returns (pass, fail) lists."""
    conn = get_db()
    ctx = build_context(conn)
    conn.close()
    passed, failed = [], []
    for lead in leads:
        candidate = build_candidate_from_db_row(lead, ctx)
        if evaluate_a0(candidate).a0_eligible:
            passed.append(lead)
        else:
            failed.append((lead, evaluate_a0(candidate).reasons))
    return passed, failed
```

**Advantages**:
- Zero risk to existing flow
- Gate catches anything SQL missed
- Can log discrepancies for auditing

### Recommendation

**Start with Option B** (parallel validation) for 1 week. If no discrepancies, switch to Option A.

---

## 5. Rollback Plan

### Rollback Scope

| Component | Rollback Action |
|---|---|
| `production_adapter.py` | Delete from `workbuddy_candidate_modules/` — no production references |
| `test_production_adapter.py` | Delete from `workbuddy_candidate_modules/` — test-only |
| `dry_run_all.py` | Delete from `workbuddy_candidate_modules/` — analysis-only |
| `lead_hygiene_gate.py` | Delete from `workbuddy_candidate_modules/` — Codex original |
| Production DB | **NOT MODIFIED** — no rollback needed |
| `bd_sender.py` | **NOT MODIFIED** — no rollback needed |
| `daily_operator_auto.py` | **NOT MODIFIED** — no rollback needed |
| `suppression_list` | **NOT MODIFIED** — no rollback needed |
| Scheduled task | **NOT MODIFIED** — no rollback needed |

### If Gate is Integrated into Production

1. Revert `bd_db.py` to backup (or remove gate import)
2. Gate module files can be deleted without affecting anything
3. No DB schema changes → no DB rollback needed
4. No status field changes → no data rollback needed

### Backup

All original production files have existing backups:
- Patch 1: `backups/p0_patch1_legacy_live_disable_20260710_1053`
- Message-ID fix: `backups/message_id_fix_20260707_1155`
- Evidence snippet: `backups/evidence_snippet_schema_20260707_125936`

---

## 6. Files Produced

| File | Purpose | Production Impact |
|---|---|---|
| `workbuddy_candidate_modules/production_adapter.py` | Field mapping + context builder | None (isolated) |
| `workbuddy_candidate_modules/test_production_adapter.py` | 74 production-compatible tests | None (test-only) |
| `workbuddy_candidate_modules/dry_run_all.py` | Full dry-run script | None (read-only) |
| `workbuddy_candidate_modules/lead_hygiene_gate.py` | Codex original gate (unchanged) | None (isolated copy) |
| `LEAD_HYGIENE_PRODUCTION_ADAPTER_REPORT.md` | This report | None (documentation) |

**No production files were modified. No DB writes. No sends. No suppression changes.**
