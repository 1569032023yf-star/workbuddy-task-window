# PHASE 4A — METRIC PROVENANCE AUDIT (read-only)

**Date:** 2026-09-10 (audit) · recorded 2026-09-11
**Scope:** Verify real authority of lead 1085 + 4 production metrics. Read-only; no code/DB/scheduler changes.
**Conclusion:** `METRIC_DEFINITION_MISMATCH_FOUND = true`

---

## 1. Key schema facts (read-only introspection)
- `leads` table has **NO `campaign_eligible_v2` column** → V2 is pure live computation `review_campaign_eligible_v2()`.
- `final_send_plan` table has **NO `organization_key` column** → SAFE unique-org must JOIN `leads.organization_key`.
- No `email_evidence` / `lead_evidence` / `staging_leads` / `raw_places` tables. "evidence" = `leads.evidence_url` text column.
- `leads.email_verified_on_official_site` (INTEGER) is the real "verified" flag (not a `verified` column).

## 2. lead 1085 (live)
- email = `ithacainstantreplaysports@yahoo.com` · source = `official_page_visible`
- `email_verified_on_official_site` = 1 · evidence_url = `https://ithacainstantreplaysports.com/` · method = official_homepage
- evidence_checked_at = 2026-09-10 (fresh) · organization_key = `org:domain:ithacainstantreplaysports.com` · tz = America/New_York
- **status = `manual_review_needed` · auto_sendable = 0** · MX(yahoo.com) = ok (live DNS)
- V2-eligible (read-only) but blocked by review gate → **not materialized into FSP** → canonical SAFE_FSP = 0. This is by-design fail-closed, not a bug.

## 3. The four metrics — conflicting authorities found in code
| Metric | Value (this audit, live) | Authority / definition conflict |
|---|---|---|
| VISIBLE_FIRST_PARTY_EMAILS | canonical **338** | `email IS NOT NULL AND email_verified_on_official_site=1 AND status NOT IN terminal`. ⚠️ Code also defines D1≈914 (excl manual_lookup, all non-null non-terminal) and D2≈983 (incl manual_lookup) — these inflate via `email_source_type='unknown'`(387)/`'guessed_email'`(167). No single canonical. |
| FULL_EVIDENCE_RECORDS | **897** | `leads.evidence_url NOT NULL`. (Ad-hoc Inventory snapshot earlier reported 441 — different filter; that was a diagnostic-script口径偏差, not production path.) |
| V2_ELIGIBLE_UNSENT | **12** (proxy) | No stored column. Live = `review_campaign_eligible_v2()` (V1 + MX ok + source tier≠E4 + evidence≤90d). Proxy omits live MX → true canonical ≤12. |
| SAFE_FSP_ELIGIBLE_UNIQUE_ORGS | materialized **0** / read-only **11** | canonical = `final_send_plan.status='planned'` (0 rows). read-only V2-eligible distinct org = 11. |

## 4. Phase 4A SAFE=1 vs early SAFE=0 — root cause
- Phase 4A "SAFE=1" = user-accepted **read-only V2-eligible unique-org inventory** count (lead 1085 entered 1 new org on 2026-09-10).
- Early / tonight "SAFE=0" = canonical production SAFE_FSP = **materialized** `final_send_plan` = 0.
- Both correct; the 1-vs-0 confusion is purely a **metric-definition mismatch**, not a state change.

## 5. Standing rule (enforced going forward)
Never write bare `SAFE = X`. Always report the 5 metrics with authority:
V2_ELIGIBLE_UNSENT / READ_ONLY_SAFE_UNIQUE_ORGS / MATERIALIZED_FSP_PLANNED / BROAD_READY / VISIBLE_FIRST_PARTY_EMAILS.
`read-only V2 eligibility ≠ materialized Final Send Plan ≠ BroadReady ≠ visible first-party emails.`
