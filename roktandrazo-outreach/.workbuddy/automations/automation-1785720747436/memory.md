# BD Weekend Inventory — Execution History

## 2026-08-09 (Sun) 16:00 Asia/Shanghai
- **Command**: `python bd_orchestrator.py --stage inventory --live`
- **Duration**: 44 min (15:56 → 16:40)
- **Pre-run lock**: Released (prior run 14:56-15:41) — no skipping needed
- **Cursors**: TN / Nashville / page 1 (stale since Aug 3)
- **5 inventory loops**: Website Recovery scanned 34 candidates × 5 iterations
  - 3 emails found per loop (jeff@midtngaming.com, customercare@easternnational.org × 2) — all hygiene=previously_sent
  - 20 no-email, 11 persistent network errors, 3 skip_platform
  - A0 = 0/30 throughout — zero new sendable leads collected
- **Lane A (Google Places)**: configuration_blocked
- **Lane B/C/D**: staging_postprocess_empty (no lead_staging table)
- **Post-run state**: 738 total, 34 new, 373 sent, 95 broad_outreach_ready — unchanged
- **Key issues**: Website Recovery pool exhausted, no staging table, Google Places blocked, cursors stale 6 days
