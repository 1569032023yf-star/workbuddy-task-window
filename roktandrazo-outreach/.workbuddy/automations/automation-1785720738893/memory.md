# BD Weekend Inventory AM — Automation Memory

## 2026-08-08 Sat 10:00 Asia/Shanghai
- Run: `bd_orchestrator.py --stage inventory --live` (no SMTP)
- Result: **partial — A0=0/30**, gap=30, max_loops_reached (~40 min)
- Google Places: `configuration_blocked` → 0 discovery leads
- Website Recovery: 5 loops × 34 sites, 3 emails found (all previously_sent), 20 no-email, 11 network errors
- Pool: 34 new / 0 auto-sendable / 738 total
- Lock: acquired 09:52, released cleanly

## 2026-08-09 Sun 10:00 Asia/Shanghai
- Run: `bd_orchestrator.py --stage inventory --live` (no SMTP)
- Result: **partial — A0=0/30**, gap=30, max_loops_reached (~42 min)
- Google Places: `configuration_blocked` → 0 discovery
- Website Recovery: 5 loops × 34 sites, 3 emails found (all previously_sent), 20 no-email, 11 network errors
- Pool: 34 new / 29 auto_sendable (0 strict A0) / 738 total (unchanged)
- TN: 7 new/15 auto · AR: 10 new/9 auto · KY: 1 new/4 auto
- Lock: acquired 09:51, released cleanly
- ⚠️ 29 auto_sendable leads exist but strict A0 gate returns 0 — gate mismatch (get_sendable_leads stricter than auto_sendable flag)
- ⚠️ Website pool exhausted — same 34 candidates retried 5× with identical results
- 🔑 Critical gap: inventory stage has no new lead intake path while Google Places is blocked
