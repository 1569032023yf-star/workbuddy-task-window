# LEGACY_TO_CURRENT_DIFF.md

> **Legacy vs Current System Comparison**
> Generated: 2026-07-07T14:13+08:00
> Scope: WorkBuddy legacy artifacts vs Codex current state

---

## 1. Rules Consistency

### 1.1 Rules That Are Consistent

| Rule | Legacy (WorkBuddy) | Current (Codex) | Status |
|------|-------------------|-----------------|--------|
| Daily target = 20 | ✅ MEMORY.md | ✅ Codex reports | ✅ CONSISTENT |
| Inventory floor = 60 | ✅ MEMORY.md | ✅ Codex reports | ✅ CONSISTENT |
| Send window 09:00-13:00 Asia/Shanghai | ✅ MEMORY.md | ✅ Codex reports | ✅ CONSISTENT |
| TN/AR/KY primary states | ✅ MEMORY.md | ✅ Codex reports | ✅ CONSISTENT |
| A0 = verified official email | ✅ MEMORY.md | ✅ Codex reports | ✅ CONSISTENT |
| B = guessed email, no auto-send | ✅ MEMORY.md | ✅ Codex reports | ✅ CONSISTENT |
| C = contact form only | ✅ MEMORY.md | ✅ Codex reports | ✅ CONSISTENT |
| B2 = manual_review_needed | ✅ MEMORY.md | ✅ Codex reports | ✅ CONSISTENT |
| Suppression = never re-send | ✅ MEMORY.md | ✅ Codex reports | ✅ CONSISTENT |
| Google Maps = candidate discovery only | ✅ MEMORY.md | ✅ Codex reports | ✅ CONSISTENT |
| Website verification required for A0 | ✅ MEMORY.md | ✅ Codex reports | ✅ CONSISTENT |
| evidence_url required for A0 | ✅ MEMORY.md | ✅ Codex reports | ✅ CONSISTENT |
| Reports must be bilingual | ✅ MEMORY.md | ✅ Codex reports | ✅ CONSISTENT |

### 1.2 Rules That Changed

| Rule | Legacy (WorkBuddy) | Current (Codex) | Change |
|------|-------------------|-----------------|--------|
| Template version | V4 (Jul 6) | V5 (Jul 6) | V5 removes Zoom, adds supply chain |
| evidence_snippet | Not present | New field | Codex added evidence_snippet |
| Message-ID header | Missing | Required | Codex fixed Message-ID |
| bounce_type 'message_id_missing' | Not present | New type | Codex added message_id_missing |

---

## 2. Field Changes

### 2.1 New Fields Added by Codex

| Field | Table | Purpose | Legacy Equivalent |
|-------|-------|---------|-------------------|
| `evidence_snippet` | leads | Text snippet proving email location | `notes` (legacy, unstructured) |

### 2.2 Legacy Fields Still Present

| Field | Table | Purpose | Status |
|-------|-------|---------|--------|
| `evidence_url` | leads | URL where email was found | ✅ Still used |
| `notes` | leads | General notes | ✅ Still used (legacy evidence stored here) |
| `email_verified_on_official_site` | leads | 0/1 flag | ✅ Still used |
| `email_source_type` | leads | Source type | ✅ Still used |
| `confidence_score` | leads | A/B/C | ✅ Still used |
| `manual_*` (7 fields) | leads | Human approval | ✅ Still used |

---

## 3. Evidence Handling

### 3.1 Legacy System (WorkBuddy)

- **evidence_url**: URL where email was found ✅
- **evidence_snippet**: NOT present ❌
- **notes**: Used for unstructured evidence (e.g., "Found in footer of website") ⚠️

### 3.2 Current System (Codex)

- **evidence_url**: URL where email was found ✅
- **evidence_snippet**: NEW field for structured evidence ✅
- **notes**: Still used for general notes ✅

### 3.3 Migration Path

- Legacy leads with evidence in `notes` field should be migrated to `evidence_snippet`
- New leads should use `evidence_snippet` for structured evidence
- `notes` should be reserved for general notes only

---

## 4. Pool Management Tools

### 4.1 Legacy System (WorkBuddy)

| Tool | Purpose | Status |
|------|---------|--------|
| `pool_analysis.py` | Pool statistics + CSV | ✅ Available |
| `b_pool_import.py` | B pool CSV → approved_manual_send | ✅ Available |
| `b_pool_audit_v2.py` | B pool website audit | ✅ Available |
| `fast_lead_discovery.py` | HTTP-first + browser fallback | ✅ Available |
| `browser_verifier.py` | Playwright verification | ✅ Available |

### 4.2 Current System (Codex)

| Tool | Purpose | Status |
|------|---------|--------|
| `daily_runner.py` | Daily automation (simplified) | ✅ Available |
| `lead_collector.py` | Lead collection | ✅ Available |
| `bd_db.py` | Database layer | ✅ Available |
| `bd_sender.py` | SMTP sender | ✅ Available |

### 4.3 Gap Analysis

| Capability | Legacy | Current | Gap |
|------------|--------|---------|-----|
| Pool statistics | ✅ pool_analysis.py | ❌ Not present | MISSING |
| B pool import | ✅ b_pool_import.py | ❌ Not present | MISSING |
| B pool audit | ✅ b_pool_audit_v2.py | ❌ Not present | MISSING |
| Fast lead discovery | ✅ fast_lead_discovery.py | ❌ Not present | MISSING |
| Browser verification | ✅ browser_verifier.py | ❌ Not present | MISSING |
| Daily orchestrator | ✅ daily_operator_auto.py | ⚠️ daily_runner.py (simplified) | SIMPLIFIED |
| Batch send | ✅ daily_session.py | ⚠️ batch_send() in daily_runner | SIMPLIFIED |
| Bounce auditor | ✅ agent_bounce_auditor.py | ❌ Not present | MISSING |
| Reply monitor | ✅ agent_reply_monitor.py | ❌ Not present | MISSING |
| Daily report | ✅ agent_daily_report.py | ⚠️ step_report() in daily_runner | SIMPLIFIED |

---

## 5. TN/AR/KY Filtering

### 5.1 Legacy System (WorkBuddy)

- **city_selector_v2.py**: Has state filtering capability
- **primary_state_pool**: ['TN', 'AR', 'KY'] in system_config
- **city_selector_mode**: 'primary_state_only'
- **44 cities**: Defined in primary_state_cities.json

### 5.2 Current System (Codex)

- **No state filtering**: Current system does not have state-specific filtering
- **No primary_state_pool**: Not configured in current system
- **No city_selector**: Not present in current system

### 5.3 Gap

**MISSING**: TN/AR/KY state filtering logic. Legacy system had sophisticated city selection with state priority. Current system lacks this capability.

---

## 6. Browser Verification

### 6.1 Legacy System (WorkBuddy)

- **browser_verifier.py**: Playwright-based verification
- **Capabilities**:
  - Check footer, contact, about, wholesale, vendor, buyer pages
  - Extract visible emails with evidence_url + evidence_snippet
  - Classify: A0 (email found) / B2 (no email) / C (contact form) / Invalid (dead)
- **Speed**: ~60s/lead (slow)
- **Alternative**: fast_lead_discovery.py (3.1s/lead, 19x faster)

### 6.2 Current System (Codex)

- **No browser verification**: Current system uses WebFetch only
- **WebFetch limitations**: Cannot handle JS-rendered sites (Shopify, Wix, Squarespace)

### 6.3 Gap

**MISSING**: Browser verification capability. Legacy system had Playwright-based verification that could handle JS-rendered sites. Current system relies on WebFetch which is inadequate.

---

## 7. Sendable Pool Calculation

### 7.1 Legacy System (WorkBuddy)

- **pool_analysis.py**: Comprehensive pool statistics
- **Queries**:
  - A0: `status='new' AND confidence_score='A' AND email_verified_on_official_site=1 AND email_source_type IN (...)`
  - B2: `status IN ('new', 'manual_review_needed') AND confidence_score='B'`
  - C: `confidence_score='C'`
  - AMS: `status='approved_manual_send'`
- **Filters**: suppression, sent_log, bounce_log, Exchange MX

### 7.2 Current System (Codex)

- **Strict sendable_pool**: Codex has implemented strict pool calculation
- **Current count**: 5 (very low)

### 7.3 Gap Analysis

| Pool | Legacy Count | Current Count | Gap |
|------|--------------|---------------|-----|
| A0 sendable | ~18 (Jul 7) | 5 | -13 |
| B2 manual_review_needed | 167 | ? | Unknown |
| C contact_form_pool | 30 | ? | Unknown |
| AMS approved_manual_send | 0 | 0 | 0 |

**Root cause**: Codex's strict verification may be excluding leads that legacy system included. Need to audit which leads are being excluded and why.

---

## 8. Template System

### 8.1 Legacy System (WorkBuddy)

- **V5 template** (current):
  - Subject: "Premium puzzles & card games for {store} (Low MOQ / DDP)"
  - Body: "puzzle and family card game brand", 4 bullets, catalogue mention
  - No Zoom, no "Play Learn Laugh"
- **Template file**: `bd_template.py`
- **Backup**: `backup/bd_template_v4_backup_20260706.py`

### 8.2 Current System (Codex)

- **Template**: Uses `bd_template.py` from legacy system
- **Apply function**: `apply_email_to_lead(lead)`

### 8.3 Status

**CONSISTENT**: Both systems use the same V5 template.

---

## 9. Bounce Handling

### 9.1 Legacy System (WorkBuddy)

- **agent_bounce_auditor.py**: Bounce classification
- **Types**: hard, policy, soft, unknown
- **Suppression**: Only hard bounces auto-suppress
- **Message-ID**: NOT handled (legacy issue)

### 9.2 Current System (Codex)

- **Message-ID fix**: Codex has added `message_id_missing` type
- **Suppression**: message_id_missing does NOT suppress
- **Status**: Lab-only fix, not deployed to production

### 9.3 Gap

**PARTIALLY FIXED**: Codex has identified and fixed the Message-ID bounce issue in the lab. Production code still needs to be patched.

---

## 10. Summary

### 10.1 What Legacy System Had That Current System Lacks

1. **Pool statistics tool** (pool_analysis.py)
2. **B pool import tool** (b_pool_import.py)
3. **B pool audit tool** (b_pool_audit_v2.py)
4. **Fast lead discovery** (fast_lead_discovery.py)
5. **Browser verification** (browser_verifier.py)
6. **Bounce auditor** (agent_bounce_auditor.py)
7. **Reply monitor** (agent_reply_monitor.py)
8. **Daily orchestrator** (daily_operator_auto.py)
9. **State filtering** (city_selector_v2.py)
10. **Comprehensive daily reports** (agent_daily_report.py)

### 10.2 What Current System Has That Legacy System Lacks

1. **evidence_snippet field** (structured evidence)
2. **Message-ID header fix** (lab-only, not deployed)
3. **message_id_missing bounce type** (lab-only, not deployed)

### 10.3 Recommendation

**Codex should read the legacy tools to understand the full system capabilities.** Many of the legacy tools are well-designed and could be adapted for the current system. The key missing capabilities are:

1. Browser verification (critical for A0 upgrades)
2. Pool statistics (critical for inventory management)
3. State filtering (critical for TN/AR/KY strategy)
4. Bounce/reply monitoring (critical for deliverability)
