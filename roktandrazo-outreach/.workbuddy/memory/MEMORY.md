# Roktandrazo BD Outreach — Project Memory

## System Architecture
- **DB**: SQLite at data/leads.db (bd_db.py)
- **Orchestrator**: bd_orchestrator.py (v3.1) — single production entry point
- **Sender**: bd_sender.py (SMTP via Tencent Exmail)
- **Hygiene Gate**: lead_hygiene_gate.py (Strict A0 eligibility filter)
- **Broad Outreach Gate**: broad_outreach_gate.py (Broad Outreach Ready tier, added 2026-07-29) — dual-tier eligibility
- **Template**: bd_template.py (V5)

## Key Configurations
- **ALLOWED_STATES**: TN, AR, KY, OH, IN, MN, NE, NC, OR, CO (expanded 2026-07-20)
- **Send window**: 09:00-13:00 Asia/Shanghai
- **Daily target**: 20 emails (expandable to 60 with Broad Outreach)
- **Risk gate cooldown**: 20h (temporary_block)
- **Primary state pool**: TN, AR, KY (for Lead Factory collection)

## Dual-Tier Eligibility (2026-07-29)
1. **Strict A0** — high-confidence verified leads (3 orgs): status='new', confidence='A', auto_sendable=1, email_verified=1, full evidence chain
2. **Broad Outreach Ready** — broad-match sendable (161 orgs, 162 locations): business category + service opportunity match, valid email, no hard blocks. Soft blocks (generic email, missing contact, incomplete evidence) no longer prevent sending.
- **Send priority**: Strict A0 → Broad High → Broad Normal, max 1 per organization, capped at 60/night
- **Hard blocks preserved**: previously_sent, suppressed, bounced, unsubscribed, negative reply, rejected, invalid email, system email, contact_form_only
- **organization_key**: auto-generated fallback from domain/name/city+state (632 patched)
- **Module**: broad_outreach_gate.py — evaluate_broad_outreach(), analyze_all_leads()

## Known Issues (as of 2026-07-20)
1. **recovery_send bypasses hygiene gate** — post_a0_upgrade_recovery_check sends via SQL-only filter
2. **Old bounces trigger risk stop** — IMAP scan picks up stale PostMaster notifications
3. **SCAN ERROR** — agent_bounce_auditor.py missing scan_bounces function
4. **Lead Factory vs Hygiene Gate** — leads collected from all states but gate was restrictive (now fixed)
5. **Evidence snippets** — Lead Factory doesn't populate evidence_snippet during collection
6. **send_log duplicate bug** (2026-07-23) — `log_send()` called twice per lead in orchestrator, producing 2 rows per email. `get_today_sent_asia_shanghai()` counts rows not unique leads → orchestrator miscalculates gap
7. **follow_up_queue_builder** — `workbuddy_candidate_modules.follow_up_queue_builder` module missing, follow-up phase skipped

## Recovery Patterns
- Stale run lock: release via `release_run_lock(today)` in bd_db
- Risk gate auto-clear: at 08:30 inbox stage if cooldown expired + no new risks
- Pool replenishment: 3-stage (existing pool → B2 browser verify → new city Lead Factory)
