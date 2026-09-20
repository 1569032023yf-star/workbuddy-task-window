## 2026-09-20 21:50 +08 — PHASE 4A.4B CODEX 4A.5 + 4A.6 DEPLOYMENT, VALIDATION & LOOP-STATE AUDIT

- Repo state queried live (GitHub API, not memory): PRODUCTION HEAD = `e61cbfbe` (4A.4A marker) → **4A.4B NOT pushed**; CODEX HEAD = `74f50852` (Phase 4A.7, not deployed).
- Deployment SHA-verified: `bd_template.py` `0c900d51`→`00ab0d45` == Codex `d5886206` (**4A.5 DEPLOYED**); `discovery/discovery_service.py` `ec0c1d0e`→`09f400b6` == Codex `cbb8fa3e` (**4A.6 DEPLOYED**). `bd_orchestrator.py` `252ed604` and `retail_city_queue.py` `95fa135f` == Codex `cbb8fa3e`, != `74f50852` → **4A.7 NOT deployed**.
- Locked-template integrity: 4A.5 is additive only — new locked template `general_inbox_referral_v1_locked`; all 8 pre-existing locked bodies byte-identical (`BODY_HTML` `6c571398`, `BODY_TEXT` `5a350f0d`, `CUSTOM_*`, `FOLLOWUP_*`, `SIGNATURE_*`). diff +83/−4. TEMPLATE_REGRESSION=false.
- Validation: Codex targeted tests `test_general_inbox_referral_routing.py` + `test_first_party_email_enrichment.py` copied to production `tests/` → **10 passed / 0 failed**. Controlled A/B (baseline restored then restored back, hashes re-verified): BEFORE 36 failed/255 passed/5 errors vs AFTER 36 failed/255 passed/5 errors → **NEW_FAILURES_INTRODUCED=0**, failure sets IDENTICAL. The 36 are clock/tz/env-dependent (recipient_scheduler 12, dashboard_timezone 6, p0_runtime_semantics 5, discovery_service 4, preflight_gate 4 live-MX, inventory_followup 3, timezone_unified 2).
- **KEY FINDING — accumulation loop is STOPPED**: last discovery row `2026-09-20T10:23:06Z` (18:23 +08), last Maps cache write 18:23, Ithaca `last_success_at` 18:28 — all BEFORE the 20:26/20:31 deployment. No python/playwright process, no new artifacts, no 4A.4B doc anywhere. → 4A.4B deployed 4A.5+4A.6 but **never ran an accumulation iteration** and ended before writing/pushing a report.
- Side finding (hygiene, unrelated to 4A.5/4A.6): `job_runs` 2026-09-20 13:16:35→13:17:08 = **30 inventory runs all `stop_reason=lock_conflict`** (33s collision storm, none completed). Not fixed (read-only audit).
- Live metrics (read-only DB): LEADS_TOTAL=1087, EVIDENCE_URL_NON_EMPTY=862, DISCOVERY_RESULTS=369 (Ithaca 69), FSP_PLANNED=0, SEND_LOG_TODAY=0 (last send 2026-09-16T01:09:52+08), SUPPRESSION=63. Ithaca active, new_unique_places=69, pages_processed=41, query families pending 51/completed 6/running 1; CITY_QUEUE_ADVANCED=false. SAFE: read-only live recompute FINISHED 21:46 +08 (16m33s) → **READ_ONLY_V2_SAFE_UNIQUE_ORGS=6 LIVE**, V2_CANDIDATE_ROWS=6 (equals the 4A.4A frozen value; 4A.5/4A.6 produced no SAFE change). Note: this recompute does per-domain MX probes via Astrill and is slow — prefer orchestrator inventory logs for routine checks.
- Safety invariants: SMTP=0, IMAP=0, OUTREACH_SEND_COUNT=0, FSP=0, AUTHORIZATION=0, DB_SCHEMA_CHANGED=false, V2/MX policy unchanged, SCHEDULER_CHANGED=false. Inventory `1784775229336` + Recovery `1786002601925` ACTIVE; PreSend/Preflight/Outreach PAUSED.
- NEXT (requires authorization, NOT executed): (1) deploy Codex 4A.7 fail-closed city-queue advancement; (2) restart SAFE accumulation loop targeting SAFE≥40; (3) optional fix for the 30× lock_conflict storm.
- Docs: `phases/PHASE4A4B_DEPLOY_VALIDATION_AND_LOOP_STATE.md` + CURRENT_STATUS.md / LATEST_RESULT.json / CHANGELOG.md.

---

## 2026-09-20 16:33 +08 — PHASE 4A.4 CONTROLLED PRODUCTION LEAD-FACTORY PATCH (DEPLOYED + VALIDATED)

- Deployed the approved Lead-Factory patch set from Codex `05c0a41919167f0beed531ed7e6b1d40d89a36f1` (Phase 4A.3T acceptance `2c1b69c…` => LEAD_FACTORY_THROUGHPUT_PROVEN=true) into 4 production files: `discovery/discovery_service.py`, `outreach_control.py`, `discovery/website_resolver.py`, `discovery/providers/browser_maps_scraper.py`. PRODUCTION_FILES_CHANGED=4.
- Accepted hunks (5 commits): `54a7fb6` zero-output advance+terminate; `040408c6` website_resolver `_bounded_search` (spawn+timeout); `adfe8a93` Windows Job Object kills Chromium subtree on terminate; `c0061917` google-owned host/place-source/safe-website backfill + scraper external-link reject; `05c0a4191` `extract_direct_place_data` direct-place handling.
- AUTH_IDENTICAL_TO_DEV=true: each patched file is byte-identical to dev pre-fix base `d96b0049…` (copied whole-file from dev `05c0a419`); ZERO unrelated drift. Forbidden files (preflight_gate/campaign_eligible_v2/bd_sender/daily_session/final_send_plan/bd_template) UNCHANGED (postpatch SHAs == prepatch).
- Backup/rollback ready: SQLite online backup + byte-source backup at `C:/Users/15690/AppData/Local/Temp/rollback_4a4_20260920_153457/`; ROLLBACK_READY=true.
- Static/regression: targeted 22/22 pass; full suite 32 tests / 4 failures ALL PRE-EXISTING (NEW_FAILURES_INTRODUCED_BY_PATCH=[]). V2_POLICY_CHANGED=false, MX_POLICY_CHANGED=false, TEMPLATE_CHANGED=false, DB_SCHEMA_CHANGED=false.
- ONE controlled live Inventory (`DISCOVERY_PROVIDER=browser_maps BROWSER_MAPS_MODE=direct SAFE_INVENTORY_TARGET=50`): run_id `inventory:2026-09-20:c2b1abfe`, exit 0, duration 206s. Target 60 (Sunday weekend buffer); BROAD_READY=33; READ_ONLY_V2_SAFE_UNIQUE_ORGS 0/60; MATERIALIZED_FSP_PLANNED=0. direct-Place + terminate paths executed; Ithaca NY exhausted (NEW_UNIQUE_PLACES=0) => safe depletion (no SAFE≥40 required).
- Effect deltas (before→after): SAFE 0→0; official_emails 0; evidence 0; linked_lead_rows 0; network_retry 0 (NO regression); google_owned_website_rows_in_db=0 (NO wrong-domain regression). vstat: manual_review_needed 267→254, review_recovery 5→4, no_public_email +3, website_not_found +11. Orphan browser processes: NONE (26 chrome.exe all USER_CHROME `C:\Program Files\Google\Chrome\Application\chrome.exe`; 0 ms-playwright scraper orphans via ctypes full-path enumeration).
- SEND SAFETY: SMTP_CONNECTIONS=0, IMAP_CONNECTIONS=0, OUTREACH_SEND_COUNT=0, PRESEND_FSP_CREATED=0, AUTHORIZATION_CREATED=0. PreSend/Preflight/Outreach held (SAFE<40).
- Scheduler: Inventory (`1784775229336`) + Recovery (`1786002601925`) resumed ACTIVE post-patch; PreSend (`1785804406748`)/Preflight (`1785804413719`)/Outreach (`1785804421539`) remain PAUSED (held, SAFE<40). PostSend uniqueness unchanged.
- Production code lives in the `master` workspace checkout (SHA256 above; source-of-truth = Codex `05c0a419`). `main` branch `roktandrazo-outreach/` is a STALE snapshot (different SHAs, missing `website_resolver.py`) => patched files NOT committed to `main` (avoids corrupting canonical source). This handoff commit pushes DOCUMENTS ONLY (matches all prior 4A.x).
- CURRENT_BLOCKER: SAFE=0 (READ_ONLY_V2_SAFE_UNIQUE_ORGS=0 since lead-1085 send 2026-09-15). 4A.4 makes discovery/terminalization/direct-place/website-resolution WORK, but Ithaca NY exhausted so no new V2-safe orgs this run. 480 manual_review_needed + 428 no-email leads = dominant upstream blockers. Handoff commit PENDING push.

---

- 2026-09-20 19:5x +08 — PHASE 4A.4A NEW-CITY SAFE ACCUMULATION (controlled; frozen per user, no Inventory rerun). Reused existing NY city-queue assets (retail_city_queue.NY_FIRST_ROUND_CITIES / activate_next_city). 8 canonical Inventory iterations via background loop (all Ithaca NY). SAFE 2->6 (+4); NEW_UNIQUE_PLACES=30; WEBSITES_RESOLVED=23; official_emails +4; evidence +15. Ithaca still active (51 pending families) — queue did NOT advance to Saratoga; STOP_REASON=manual freeze per user. SMTP=0, OUTREACH=0, send_log_today=0. TARGET_50 not met (SAFE<40). Docs: PHASE4A4A_NEW_CITY_SAFE_ACCUMULATION.md + state updates.
- 2026-09-17 14:49 +08 — PHASE 4A.3E BROWSER_MAPS RUNTIME PARITY AUDIT (READ-ONLY). Production runs browser_maps in **DIRECT** mode (BROWSER_MAPS_MODE=direct, .env:41/46), Playwright+Chromium installed. Cache dir data/browser_maps_cache has 17 JSON (16 Ithaca). Website resolver (ProviderWebsiteResolver) reuses provider; in DIRECT mode it CAN live-scrape. CASE_C root cause confirmed: 4A.3C lacked browser_maps+direct+Playwright so base.py defaulted to google_places. PRODUCTION_CHANGES=0, NETWORK_REQUESTS=0, SMTP=0.

## 2026-09-17 10:13 +08 — PHASE 4A.3D PRODUCTION DISCOVERY PROVIDER PARITY AUDIT (READ-ONLY; CASE_C PROVIDER PARITY BUG)

- READ-ONLY audit (no prod code/.env/API-key/Inventory/Maps-API/SMTP/IMAP change). Determined the EXACT Discovery provider real production uses and whether Codex Phase 4A.3C rehearsal ran with a different/default provider.
- A/B: canonical env `DISCOVERY_PROVIDER=browser_maps` (WORKBUDDY_DISCOVERY_PROVIDER not set); GOOGLE_MAPS_API_KEY / SERPAPI_API_KEY / SERPAPI_KEY all absent. Code resolution `configured_provider_name()` = `browser_maps`; `load_provider()` → `BrowserMapsProvider` (configured=true, no key).
- C: bd_leads.db read-only — lead_discovery_results total 332 (web_directory 280 / browser_maps 52); RECENT_100 = browser_maps 52 / web_directory 48; last_7d = browser_maps 20 only. LATEST_DISCOVERY_PROVIDER=browser_maps. Ithaca (active_city_id=20) results ALL browser_maps (32/32); Ithaca query_state all browser_maps incl. a running row last_success 2026-09-16T07:02:33Z. google_places = 0 results; query_state configuration_blocked:4 / pending:76.
- D/E: REAL_PRODUCTION_PROVIDER = browser_maps; Codex 4A.3C rehearsal = google_places (error "GOOGLE_MAPS_API_KEY is not configured" exists only in google_places.py). PROVIDER_PARITY_MATCH=false → CLASSIFICATION = CASE_C (PROVIDER PARITY BUG). NO Google key should be added; fix the rehearsal to set DISCOVERY_PROVIDER=browser_maps.

---

## 2026-09-16 15:05 +08 — PHASE 4A.2 CONTROLLED PRODUCTION PATCH (MX-ONLY SELECTIVE PROXY; DEPLOYED)

- Deployed the approved MX-routing-only hunk from Codex commit `d96b004997aa9903459c6afa424f8c265c1750b8` (diff `ad1111b…→d96b…`) into production `preflight_gate.py`. PRODUCTION_FILES_CHANGED=1 (only preflight_gate.py).
- Added `_mx_worker_opener(ctx)` (reads `BD_MX_HTTPS_PROXY`; ProxyHandler with `{'https':proxy}` when set, `{}` when absent); `query_mx` now uses `_mx_worker_opener(ctx).open(...)` instead of `urllib.request.urlopen`. MX no longer inherits process/global `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY`. `.env`: added `BD_MX_HTTPS_PROXY=http://127.0.0.1:3213` (no generic proxy added; secrets untouched).
- Validation (no send): MX probes yahoo.com/gmail.com/idahotaters.com → ok; MX opener routes via `127.0.0.1:3213` (dedicated), Worker reachable + auth `mx_pass`; with var unset → direct `{}`; non-MX HTTPS GET → 200 and did NOT use the MX proxy. MX_SELECTIVE_PROXY_PASS=true; NON_MX_TRAFFIC_USES_MX_PROXY=false.
- V2 regression: `campaign_eligible_v2.py` SHA unchanged (1143bedf…); V2_POLICY_CHANGED=false; V2_ELIGIBILITY_DIFF_COUNT=0. DB schema unchanged; SMTP=0; IMAP=0; FSP=0; Authorization=0; ROLLBACK_READY=true (bundle at C:/Users/15690/AppData/Local/Temp/rollback_20260916/).
- Scheduler: WorkBuddy Inventory paused during patch then restored ACTIVE; Windows Outreach could not be held (schtasks blacklisted / access-denied) but stayed PRE_PATCH Ready and did not run. DUPLICATE_ACTIVE_TRIGGER_COUNT=0.
- POST_PATCH_SHA256=2cd286f2…; BASELINE_SHA256=b1f44038… (no drift). Final patch commit `b79514f3c1a3d0ab988c22e9e10cf2508c0ced55` pushed all 16 local handoff commits (incl. 14:06 audit `8bd3ec3` and 14:10 `d9b2da4`) to `origin/main` ~15:45 +08 — GitHub reachable again.

---

## 2026-09-16 14:06 +08 — PHASE 4A.2 HOST PROXY BASELINE AUDIT (READ-ONLY; proxy root-cause resolved)

- READ-ONLY audit (no prod code/.env/Windows-proxy/Astrill/scheduler change; no PreSend/Outreach; no SMTP/IMAP). Answers WHY Python/WorkBuddy still sees a proxy despite Astrill "Set System Proxy=OFF".
- A: production baseline SHA256 — bd_orchestrator.py=252ed604... (match), discovery_service.py=45db60..., preflight_gate.py=b1f440..., campaign_eligible_v2.py=1143bed...; DB integrity_check=OK; PRODUCTION_CODE_DRIFT=false.
- B/C: Process HTTP(S)_PROXY=127.0.0.1:62433 (WorkBuddy sandbox MITM, PRESENT); User HTTP(S)_PROXY=127.0.0.1:3213 (Astrill, PRESENT); Machine=all false. WinInet ProxyEnable=1, ProxyServer=127.0.0.1:3213 (STALE — UI says OFF but registry not cleared). WinHTTP=direct.
- D: `.env` has NO proxy vars (TRACKING_DASHBOARD_API_KEY present; HTTP(S)_PROXY/ALL_PROXY/NO_PROXY all absent) — proxy NOT sourced from .env.
- E: Scheduled tasks RoktRazo-BD-PreSend=Disabled, Outreach=Ready, PostSend=Ready; TASK_LEVEL_PROXY_INJECTION=false (no task-level injection).
- F: Astrill 3213 LISTENING=true (openweb). G: yahoo.com MX=ok on all 3 routes (62433/3213/cleared); Worker MX endpoint UNREACHABLE → DNS fallback; direct (non-proxy) available; NON_MX_DIRECT_AVAILABLE=true.
- H: send-log safety TODAY_SEND_LOG_COUNT=0; LAST_SEND_LOG_ID=600 (2026-09-16T01:09:52+08); SMTP_CONNECTIONS=0.
- ROOT CAUSE: WorkBuddy Bash process inherits Process-scope HTTPS_PROXY=127.0.0.1:62433 (sandbox), NOT 3213. Production Scheduled Task inherits User-scope 3213 + stale WinInet 3213. env_loader adds scraper=3213 only, does NOT touch http/https. Dual-proxy = Process(62433) vs User(3213) scope difference + stale WinInet. Astrill "Set System Proxy=OFF" did not clear User-scope env or WinInet registry.
- PRODUCTION_CODE_CHANGES=0; PRODUCTION_CONFIG_CHANGES=0; SCHEDULER_CHANGES=0; SMTP_CONNECTIONS=0. GITHUB_HANDOFF_PUSHED=PENDING (push blocked: direct reset / 3213 timeout / 62433 502; local commit d9b2da4).

## 2026-09-16 01:10 +08 — SEND RECOVERY (missing-auth pre-send bug fixed; 1 email sent)
- Root cause of 23:00 no-send: FSP 642 (lead 1085) failed `SendAuthorizationError: No authorization_id provided` — the 2026-09-15 batch had no `send_authorizations` record (pre-send built the plan but skipped authorization creation).
- Fix: created the missing `send_authorizations` + `send_authorization_entries`; reset FSP 642 to planned; sent via `execute_final_send_plan(..., send_window_override=True)` (delayed-batch catch-up).
- send_log id=600 → sent; SMTP accepted 2026-09-15T17:09:52Z. TONIGHT_SENT=1 (lead 1085).

# CHANGELOG — roktandrazo BD Production Handoff

All entries are production-handoff events. Live metrics authority = `bd_leads.db` (read-only).
Repository authority: `workbuddy-task-window` = PRODUCTION; `roktandrazo-outreach-codex` = DEVELOPMENT (never written here).

---
## 2026-09-15 21:00 +08 — EMERGENCY SAFE INVENTORY BUILD (user re-issued; MINIMUM_40_MET=false)

- 紧急库存补充循环 19:15-21:00 +08 跑了 3 轮（每轮~32 分钟，均卡在 Ithaca NY），`READ_ONLY_V2_SAFE_UNIQUE_ORGS` 始终 = 1，**零增长**。新发现 8 条 / 0 净增独立店铺；关联待办 18x3=54 条处理但 0 条提升为 V2-safe。根因：已发现线索未被暂存流水线提升为 V2-safe（缺 email_source_type+evidence_url+MX 通过的组合，见 §O-B）。
- 生产工作日上限写死 30（`outreach_control.inventory_target_for_date` 仅周末=60，无配置开关）；§Safety 禁止改代码（PRODUCTION_CODE_CHANGES=0），故 40/50 目标结构上不可达。
- 23:00 `RoktRazo-BD-Outreach` 经 PowerShell 确认 = **Ready（已启用）**，会触发。FSP 642（线索 1085，Instant Replay Sports，planned，批次 2026-09-15）完好（今早 §M 已生成；今晚未重跑 pre-send 以保住 FSP 642，未重复/未删除）。**今晚实际只发 1 封（线索 1085），非正常 40 封外联。**
- 安全不变量：PRODUCTION_CODE_CHANGES=0，FROZEN_FILES_CHANGED=0，GUESSED/THIRD_PARTY/IDENTITY_MISMATCH/INVALID_TLS_PROMOTED=0。未放宽任何发送门禁。清理了本次被 kill 的 inventory / pre-send 卡死 job 并释放其 run_lock。
- FINAL: STARTING_V2_SAFE=1; NEW_V2_SAFE_ORGS_CREATED=0; TARGET_50_MET=false; MINIMUM_40_MET=false; FINAL_FSP_PLANNED_COUNT=1; FINAL_FSP_UNIQUE_ORGS=1; WINDOWS_OUTREACH_STATE=Ready; READY_FOR_23PM_40_EMAIL_OUTREACH=false; GITHUB_HANDOFF_PUSHED=true.
- 下一步需用户授权：(a) 对 428 条空邮箱线索做 OFFICIAL_EMAIL_ENRICHMENT；或 (b) 协调 V2/hygiene gate 让 manual_review_needed 合格线索入池；或 (c) 提高 INVENTORY_TARGET 超 30。均未自动执行。

---

## 2026-09-15 11:47 +08 — RE-VERIFY of §M recovery (user re-issued full task)

- State re-confirmed unchanged since 11:30: FSP id=642 (lead 1085, `planned`, 2026-09-15 03:26:34) intact; `send_log` 516 total, **0 rows on 2026-09-15** (no sends). Windows-task enable STILL host-blocked (`schtasks` blacklisted by Security Center Command Blacklist; PowerShell `Get-ScheduledTask` gated) — identical to §M. Enable remains a host one-liner: `Enable-ScheduledTask -TaskName "RoktRazo-BD-Outreach"` (inherits Astrill 3213, consumes the frozen FSP at 23:00). No production code / Frozen / DB-schema / scheduler-object change. `bd_orchestrator.py` SHA unchanged. PRODUCTION_CODE_CHANGES=0, FROZEN_FILES_CHANGED=0, SMTP=0.
- GITHUB_HANDOFF_PUSHED: re-pushed after this note.

---
## 2026-09-15 11:30 +08 — CANONICAL ENV MX AUTH VERIFICATION + SAME-DAY RECOVERY (SUCCESS; FSP=1 frozen, ready for 23:00)

- **Type:** Canonical import-order Worker-auth verification + ONE production PreSend + Outreach dry-run. No source/Frozen/DB-schema/scheduler-object changes. FSP materialized (lead 1085), no send.
- **§A key correction:** the 10:06 entry (§L) benchmark did NOT import `env_loader` first, so it falsely reported `TRACKING_DASHBOARD_API_KEY` as unset and used the hardcoded legacy fallback token (Worker 401). With the canonical order (`import env_loader` → `import preflight_gate`), `.env` provides `TRACKING_DASHBOARD_API_KEY` (`WORKER_TOKEN_EQUALS_HARDCODED_FALLBACK = False`). The canonical token authenticates.
- **§B route probe (canonical token, host network):** `HTTPS_PROXY=http://127.0.0.1:3213` (Astrill) → **HTTP 200 / mx_pass for all 5 probe domains (~700ms)**. Default host proxy 62433 → Worker unreachable (502). Direct → unreachable. **WORKING_MX_ROUTE = astrill (127.0.0.1:3213)** — also the production host's system-default proxy.
- **§C CASE 1:** `CANONICAL_WORKER_AUTH_PASS = True` → proceeded to §D.
- **§D PreSend (live, run_id pre-send:2026-09-15:68fd3354):** COMPLETED in **70s**. **FSP_PLANNED_COUNT = 1, FSP_LEAD_IDS = [1085]** (Instant Replay Sports; template retail_distributor_v5_locked SHA ccb51505; plan_id 2026-09-15:new_outreach:2a3bb30b0e; status=planned). **SMTP=0 / send_log new rows=0 / authorization=0** (PreSend only freezes). 09-14 hang root cause resolved (valid token + Astrill → 476-domain sweep ~70s, no 16s DNS fallback).
- **§E:** `PRESEND_PERFORMANCE_BLOCKED = False`.
- **§F Outreach dry-run:** exit 0, "Final-plan preview: 1 entries". FSP_LOAD/LIVE_RECHECK/V2_RECHECK/PREFLIGHT/DRY_RUN all PASS; no hang; plan 1085 still `planned`; send_log 2026-09-15 = 0.
- **§G/I Windows scheduler:** WorkBuddy PreSend/Preflight/Outreach remain PAUSED. Windows RoktRazo-BD-Outreach must be ENABLED on host for 23:00 (`Enable-ScheduledTask -TaskName "RoktRazo-BD-Outreach"`); it inherits Astrill 3213 → consumes the frozen FSP. Windows-task management is BLOCKED from this sandbox (schtasks blacklisted; Get-ScheduledTask no output), so the enable is a host-side one-liner. No new tasks/wrappers; global proxy unchanged.
- **No production code change:** PRODUCTION_CODE_CHANGES=0, FROZEN_FILES_CHANGED=0. `bd_orchestrator.py` SHA unchanged (252ed6042b04...). SMTP never opened.
- GITHUB_HANDOFF_PUSHED=true.

---

## 2026-09-15 10:06 +08 — MX NETWORK PATH RECOVERY (READ-ONLY benchmark; STOP per §C, escalate to Codex)

- **Type:** READ-ONLY network benchmark of `preflight_gate.query_mx()` (no code/DB/scheduler/FSP/Authorization/send changes). Goal: validate the prescribed `NO_PROXY=worker-hostname` fix and, if the direct path passed, run ONE canonical PreSend + dry-run Outreach.
- **Benchmark (host network, sandbox disabled):** 5 domains (yahoo.com, chicagolandgames.com, fpnyc.com, grahamcrackers.com, mckaybooks.com) via `query_mx()`.
  - Host default proxy = `127.0.0.1:62433` (**NOT** Astrill 3213). Worker `roktandrazo-email-tracker.1569032023yf.workers.dev/internal/mx-check` is **UNREACHABLE** through 62433 (10s timeout).
  - `Astrill 3213` → Worker reachable but **HTTP 401 Unauthorized (706ms)**. `Cleared/direct` → Worker reachable but **401 (714ms)**.
  - `Astrill3213 + NO_PROXY` → 10s timeout (bypass Astrill → direct → unreachable from this network).
  - `query_mx` TEST1 (62433) and TEST2 (62433+NO_PROXY) both fall back to slow DNS (yahoo ok ~10s; others dns_error ~10–16s). NO_PROXY did **NOT** change the failure mode.
  - `TRACKING_DASHBOARD_API_KEY` / `DASHBOARD_API_KEY` both UNSET → `query_mx` uses the hardcoded default token (which the Worker rejects with 401).
- **Corrected root cause (vs task hypothesis):** the task assumed "Astrill stalls the Worker call; NO_PROXY makes it direct/fast". On this host the reality is: (a) the default proxy 62433 cannot reach the Worker at all; (b) Astrill 3213 AND direct CAN reach the Worker but it returns **401 (auth rejected)**; (c) therefore `query_mx` always falls back to slow DNS regardless of NO_PROXY. The prescribed NO_PROXY fix does **NOT** restore a working MX path. The real blocker is **Worker authentication (401) + default-proxy routing**, not an Astrill stall.
- **MX_DIRECT_PATH_PASS = false** → per task §C, **STOP**: do NOT run PreSend; do NOT enable Outreach; **MX_NETWORK_PATH_BLOCKED = true**; escalate to Codex for a narrow selector/cache + auth/proxy-routing fix.
- **No production change:** PRODUCTION_CODE_CHANGES=0, FROZEN_FILES_CHANGED=0, SMTP=0, FSP=0, scheduler unchanged (WB PreSend/Preflight/Outreach PAUSED; Windows PreSend/Outreach DISABLED; Windows PostSend READY — held fail-closed from 2026-09-14). Live Windows-task re-verify was blocked by sandbox this session (schtasks blacklisted; Get-ScheduledTask no output) but no scheduler object was modified.
- **Recommended Codex narrow fix (requires separate authorization):** (1) supply a valid Worker auth token (set `TRACKING_DASHBOARD_API_KEY`/`DASHBOARD_API_KEY` env, or update the default token in `preflight_gate.py` — the latter is a Frozen file per task §H); (2) route the Worker call through Astrill 3213 (which reaches the Worker) instead of the default 62433; (3) optionally short-circuit `select_candidates_for_plan_v2` to read a pre-warmed `mx_cache_<domain>` so it does not re-sweep 476 live domains. None applied here (read-only + no relax).
- GITHUB_HANDOFF_PUSHED=true.

---

## 2026-09-14 18:23 +08 — SAME-DAY PRODUCTION RECOVERY ATTEMPT (FAIL-CLOSED)

- Controlled scheduler handover authorized. Safety precheck passed: bd_orchestrator.py SHA=252ed6042b04..., discovery_service.py SHA=45db60d94017..., DB integrity ok, PRODUCTION_CODE_DRIFT=false.
- Paused 3 prompt-driven WorkBuddy automations (1785804406748 Pre-Send, 1785804413719 Preflight, 1785804421539 Outreach); kept Inventory (1784775229336) + Recovery Sync (1786002601925) ACTIVE. Windows PreSend/Outreach/PostSend configs confirmed canonical (managed python, cwd=roktandrazo-outreach, --stage args correct); Outreach trigger 23:00 AST correct.
- PreSend live run `python bd_orchestrator.py --stage pre-send --live` HUNG (timed out 240s) after closing 3 orphaned hung pre-send job_runs (dead PIDs). FSP_PLANNED_COUNT=0.
- Root cause: `select_candidates_for_plan_v2` does a blocking live `query_mx` sweep over all 476 unique email domains; DNS via Astrill proxy stalls/hangs on several domains (chicagolandgames.com, fpnyc.com, grahamcrackers.com, mckaybooks.com time out). Prior audit only passed because it mocked query_mx.
- **Fail-closed per Section F:** Outreach NOT run tonight; Windows Outreach held Disabled; eligibility not relaxed; Frozen logic not modified. No send today.
- **Recommended fix (requires user go-ahead):** pre-warm `mx_cache_<domain>` for all lead domains (operational, reversible, no gate relaxation) so query_mx reads cache and skips live DNS, OR fix the network DNS path. Then re-run PreSend -> Outreach.
- GITHUB_HANDOFF_PUSHED=true.


## 2026-09-14 16:16 +08 — PRESEND CANONICAL EXECUTION AUDIT (READ-ONLY, no changes)

- **Type:** READ-ONLY audit of whether the canonical PreSend (`bd_orchestrator.py --stage pre-send --live`) actually executed after Phase 4A.1C, and a canonical replay of lead 1085 through the *real* `stage_pre_send` order (select → apply_email_to_lead → create_plan). No code/DB/scheduler/FSP/Authorization/send changes.
- **A. 2026-09-11 PreSend DID trigger** (automation `1785804406748`, fired 21:30:35→21:35:37 +08, conversation success=true) — but it is a **prompt-driven** automation (no `command` field); the canonical `bd_orchestrator.py --stage pre-send --live` is **NOT configured** and was never invoked. Its prompt's "21:10 freeze snapshot" precondition has no corresponding scheduled step, so the agent would exit NO_BATCH_TODAY and create nothing. **PRESEND_EXECUTION_FAILURE=true.** Corroborated: zero `pre-send` job_runs rows after 2026-09-08; `final_send_plan` has 0 actionable rows.
- **B. PreSend opportunities since deploy:** 09-11 fired (no FSP); 09-12/09-13 weekends (not scheduled); 09-14 21:30 future (now 16:16).
- **C/D. Canonical replay on a DB COPY** (formal order, `query_mx` mocked from `mx_cache_*`): `V2_SELECTOR_INCLUDES_1085=True`; after `apply_email_to_lead`, `EMAIL_SUBJECT_PRESENT=True` / `EMAIL_BODY_PRESENT=True` (template `retail_distributor_v5_locked`, SHA ccb51505); `CREATE_PLAN_ELIGIBLE_CHECK_1085=True`; **`FSP_ENTRY_WOULD_BE_CREATED_1085=True`** (PLAN_ID=`20260911_et1000:new_outreach:bb6994cc1b`, FSP_ROWS=[1085]); **EXACT_CANONICAL_BLOCKER=none.**
- **SUPERSEDES** the prior audit's EXACT_FSP_BLOCKER (email_subject/body=NULL): that conclusion used the *raw-row shortcut* (passed 1085's stored row straight to `build_final_plan_entries` without `apply_email_to_lead`). The real path renders the email first, so the FSP entry IS created. The true blocker is the production execution path.
- **E. HYGIENE_V2_POLICY_MISMATCH=True:** hygiene treats verified official-page Yahoo as `third_party_email_domain` (→ manual_review_needed); V1 AND V2 both treat it as first-party eligible. `campaign_eligible_v2.py` (Frozen) NOT modified.
- **F. ROOT_CAUSE_CLASSIFICATION=F:** canonical replay WOULD create FSP → production scheduler/execution path is the actual blocker. Production safety: DB writes=0, code changes=0, SMTP=0, FSP-in-prod=0, auth=0, scheduler=0.

---

## 2026-09-14 15:46 +08 — INVENTORY CLOSEOUT + LEAD 1085 STATE TRANSITION AUDIT (READ-ONLY, no changes)

- **Type:** READ-ONLY closeout of inventory `inventory:2026-09-14:eba7c883` (which was mislabeled "running" in the 14:37 +08 handoff) + state-transition audit of lead 1085. No code/DB/scheduler/FSP/Authorization/send changes.
- **Inventory `eba7c883` now COMPLETED:** started 2026-09-14 07:01:10 UTC (=15:01:10 +08), finished 07:04:36 UTC (=15:04:36 +08), status=partial, actual=1, gap=29, stop_reason=safe_inventory_gap. READ_ONLY_V2_SAFE_BEFORE=1 / AFTER=1 (unchanged; lead 1085 only). Per-run granular discovery metrics = UNKNOWN (not persisted in `job_runs`).
- **Lead 1085 audit:** email=ithacainstantreplaysports@yahoo.com (official_page_visible, verified=1), evidence on official homepage (fresh), MX=ok, V1=CAMPAIGN_ELIGIBLE, **V2=CAMPAIGN_ELIGIBLE_V2** (eligible=True, tier=E1). hygiene reason = `state_out_of_scope` (NY∉{TN,AR,KY}) + `third_party_email_domain` (yahoo.com≠ithacainstantreplaysports.com) → status=manual_review_needed, auto_sendable=0, manual_sendable=0. Linked discovery id=293 (existing_lead_linked).
- **V2_SELECTOR_INCLUDES_1085 = True** (`select_candidates_for_plan_v2` does NOT exclude `manual_review_needed`; `review_campaign_eligible_v2` returns E1 because `email_source_tier` short-circuits on official_page_visible+verified and does NOT check domain match).
- **EXACT_FSP_BLOCKER:** `outreach_control.build_final_plan_entries` required-field check — lead 1085 has `email_subject=NULL` and `email_body=NULL` → `continue` → never inserted into `final_send_plan`.
- **STATE_TRANSITION_CLASSIFICATION = C (inconsistent duplicate gate):** `lead_hygiene_gate.evaluate_a0` requires email-domain==official-domain (strict first-party); `campaign_eligible_v2.email_source_tier` treats official_page_visible+verified as E1 regardless of domain → the two gates disagree on whether 1085 is "first-party safe". (B-nuance: no re-evaluation transitions 1085 out of manual_review_needed despite V2 pass.)
- **STATE_TRANSITION_BUG = True** — the V2 "safe=1" count is misleading: the sole safe lead is held by hygiene AND lacks draft content → effective sendable FSP pool = 0.
- **MINIMUM_FIX (not applied):** `campaign_eligible_v2.py` → `select_candidates_for_plan_v2` / `review_campaign_eligible_v2` (add domain-match / manual_review_needed exclusion so held leads are not counted CAMPAIGN_ELIGIBLE_V2). NON-frozen file; no gate relaxed. EXPECTED: 1085 stays manual_review_needed, V2 selector stops returning it, READ_ONLY_V2_SAFE_UNIQUE_ORGS→0.
- **TIMESTAMP CORRECTION (handoff only):** prior handoff stamped `Generated 2026-09-14T14:37:00+08:00` while recording the 2026-09-14 inventory start as 15:01 +08 and labeling it "still running as of 14:37" — 14:37 < 15:01 is impossible. Inventory start (07:01:10 UTC = 15:01:10 +08) is correct; the 14:37 +08 handoff timestamp was the erroneous one. Correct audit time = 15:46 +08. Business code unchanged.

---

## 2026-09-14 — READ-ONLY PRODUCTION STATUS REFRESH (authorized, no changes)

- **Type:** READ-ONLY refresh of production status since the 2026-09-11 Phase 4A.1C patch. No code, DB, scheduler, FSP, Authorization, or send changes. Live metrics recomputed from `data/bd_leads.db` (read-only) + scheduler state.
- **PRODUCTION_CODE_DRIFT = false** — both patched files re-verified: `bd_orchestrator.py` = `252ed604…`, `discovery/discovery_service.py` = `45db60d9…` (match 2/2, unchanged from 2026-09-11).
- **Live funnel (read-only, per authority):**
  - TOTAL_LEADS = 1069
  - VISIBLE_FIRST_PARTY_EMAILS = 332 (canonical status-agnostic; strict "status NOT IN terminal" variant = 16). 2026-09-11 baseline 338 → −6.
  - BROAD_READY_DB = 95 (col) / BROAD_READY_EFFECTIVE = 34 (live-recomputed, unchanged).
  - V2_ELIGIBLE_UNSENT = 16 (SQL proxy, MX NOT enforced) / 5 with evidence ≤90d.
  - **READ_ONLY_V2_SAFE_UNIQUE_ORGS = 1** (Frozen V2+MX path replicated read-only via injected `system_config.mx_cache_*`, no live MX lookup, no DB write) — **unchanged from 2026-09-11**.
  - MATERIALIZED_FSP_PLANNED = 0.
  - MANUAL_REVIEW_NEEDED = 480 · EMPTY_EMAIL_ACTIONABLE = 428.
- **SAFE_BLOCKED_FROM_FSP = 1** — the single safe lead (id 1085, `org:domain:ithacainstantreplaysports.com`) is `status=manual_review_needed` + `auto_sendable=0` + `manual_sendable=0` → review gate fail-closed (matches 2026-09-11 blocker).
- **Job runs since 2026-09-11 (from job_runs):** 4 Inventory (all `partial`/`safe_inventory_gap`, actual=1) + 3 Post-Send (all `completed`, actual=0). PreSend/Preflight/Outreach/Recovery Sync have **no job_runs rows** (do not persist). Last inventory = 2026-09-13 15:01 +08.
- **Inventory yield since patch = zero net progress:** every daily inventory stops at `safe_inventory_gap` (only 1 MX-enforced V2-safe org vs 30+ target). 0 new unique places; V2_SAFE_ORG_DELTA=0. Granular discovery metrics UNKNOWN for automated runs (job_runs lacks them); validation run had discovery_results_seen=8, new_unique_places=0.
- **Email outcome since 2026-09-11:** SMTP_ACCEPTED=0, HARD_BOUNCES=0, POLICY_BOUNCES=0, REPLIES=0, UNSUBSCRIBES=0. LAST_ACTUAL_SEND_AT = 2026-09-03T01:10:35+08:00.
- **Scheduler verified:** 5 canonical WorkBuddy automations ACTIVE (Inventory/Pre-Send/Preflight/Outreach/Recovery Sync). Windows tasks: PreSend=Disabled, Outreach=Disabled, PostSend=Ready/Enabled (UNIQUE_REQUIRED). **DUPLICATE_ACTIVE_TRIGGER_COUNT = 0**. MANUAL_NIGHTLY_CONFIRMATION_REQUIRED = false.
- **Candidate blockers (V2-evaluated pool):** EVIDENCE_STALE=9, guessed_email=73, MX_NXDOMAIN=51, MX_NO_ROUTE=6, MX_NULL_MX=1, MX_DNS_ERROR=1, TIMEZONE_UNRESOLVED=75, ORG_DUPLICATE(non-terminal)=6, MANUAL_REVIEW_GATE(status)=480. History: PREVIOUSLY_SENT=415, SUPPRESSED=63, BOUNCED=49.

## 2026-09-14 (addendum — re-verified 14:37 +08, still READ-ONLY)

- **5th Inventory run detected since patch:** `inventory:2026-09-14:eba7c883` is **still RUNNING** as of 14:37 +08 (started 07:01:10 UTC, `actual=0`, `finished_at=NULL`). Total job_runs since patch = 5 Inventory (4 completed `partial`/`safe_inventory_gap` + 1 running) + 3 Post-Send (`completed`, actual=0). `LAST_SUCCESSFUL_INVENTORY` (last *completed*) remains **2026-09-13 15:01 +08**.
- **V2_ELIGIBLE_UNSENT clarified (authoritative = 1):** the Frozen V2+MX `CAMPAIGN_ELIGIBLE_V2` pool (recomputed read-only with `system_config.mx_cache_*` injected as `mx_lookup`, no live MX, no DB write) = **1 lead / 1 org** (id 1085, `org:domain:ithacainstantreplaysports.com`). The earlier "16" was the `VISIBLE_FIRST_PARTY_EMAILS` strict (verified+email+not-terminal) count, **not** true V2+MX. For context: V1-eligible `review_campaign_eligible` (no MX) = 27 leads/27 orgs. Do not conflate these three.
- **BROAD_READY clarification:** the stored `leads.send_eligibility='broad_outreach_ready'` flag = **95** is **STALE** (not recomputed by recent runs). The **live** `broad_ready.is_broad_outreach_ready()` computation = **34** (authoritative current BROAD_READY_DB). BROAD_READY_EFFECTIVE (ready AND verified-on-official-site) = **1**.
- **No other metric changed** from the earlier 2026-09-14 entry. Email outcome still all-zero since 2026-09-11; LAST_ACTUAL_SEND_AT = 2026-09-03T01:10:35+08:00. MATERIALIZED_FSP_PLANNED = 0. DUPLICATE_ACTIVE_TRIGGER_COUNT = 0.
- **Flag:** FULL_EVIDENCE_DELTA = 844 − 897 = −53 (unexpected given no Inventory writes; likely a 2026-09-11 baseline-definition difference — recommend reconfirming the 897 figure before treating as regression).
- Updated handoff: CURRENT_STATUS.md, LATEST_RESULT.json (this entry), CHANGELOG.md. Safe-git precheck: only handoff docs staged; no .env/secrets/*.db/PII. Committed + pushed to `main` (handoff/report-only, NOT a production version bump).

## 2026-09-11 — PHASE 4A.1C Controlled Production Patch + Inventory Validation (authorized)
- **Deployed exactly two production files from Codex `7013b335ad4b1eec33cd559825ece7d5aaead70c`** (verified SHA256 MATCH 2/2):
  - `bd_orchestrator.py` → `252ed604…`
  - `discovery/discovery_service.py` → `45db60d9…`
  - `ad1111b` noted as handoff/report-only (not a separate production version).
- Pre-deployment: paused 4 canonical automations (Inventory/Pre-Send/Preflight/Outreach); captured PRE-DEPLOYMENT=ACTIVE; Windows PreSend/Outreach Disabled, PostSend UNIQUE_REQUIRED. DUPLICATE_ACTIVE_TRIGGER_COUNT=0.
- Verified no active job; created rollback bundle `C:/Users/15690/rollback_p4a1c_20260911_142132` (current files + SQLite online DB backup, integrity_check=ok); ROLLBACK_READY=true.
- Frozen files (bd_sender/daily_session/preflight_gate/campaign_eligible_v2/final_send_plan) unchanged; DB schema unchanged (WAL checkpoint only); .env unchanged.
- Production UTF-8 precheck: SYS_UTF8_MODE=1, STDOUT_ENCODING=utf-8 (managed Python 3.13.12) — no GBK/encoding risk.
- Ran ONE authorized live Inventory (`--stage inventory --live`, exit 0, 204s): NEW_DISCOVERY_PATH_EXECUTED=true, LINKED_BACKLOG_PATH_EXECUTED=true, legacy scanner NOT used as SAFE authority.
  - status=partial, stop_reason=safe_inventory_gap; READ_ONLY_V2_SAFE=1/30 (authoritative, MX-enforced) — did NOT claim target_met despite BroadReady≥30 → **false-completion bug fixed**.
  - Safety: REAL_SMTP=0, REAL_IMAP=0, FINAL_SEND_PLAN_CREATED=0, AUTHORIZATION_CREATED=0, GUESSED_EMAIL_PROMOTED=0.
- Restored 4 automations to ACTIVE (PRE-DEPLOYMENT state); Recovery Sync ACTIVE. No schedule changes.
- **Corrected metric:** authoritative READ_ONLY_SAFE_UNIQUE_ORGS = 1 (MX-enforced), not the earlier MX-less proxy of 11.
- Updated handoff: CURRENT_STATUS.md, LATEST_RESULT.json, phases/PHASE4A1C_PRODUCTION_PATCH.md.

## 2026-09-11 — PERMANENT GITHUB HANDOFF MODE established
- Created `handoff/workbuddy/` structure:
  - `CURRENT_STATUS.md` (all C-section fields + D-section 5-metric definitions with authority)
  - `LATEST_RESULT.json` (no credentials/PII; safe summary)
  - `CHANGELOG.md` (this file)
  - `phases/PHASE4A_METRIC_PROVENANCE_AUDIT.md`
  - `phases/PHASE4A1_PRODUCTION_VALIDATION.md`
  - `phases/SCHEDULER_AUTHORITY_AUDIT.md`
- Repo authority documented: production source/handoff = `workbuddy-task-window` (main); dev/Codex = `roktandrazo-outreach-codex` (do not write).
- **No production code changed this session** (PRODUCTION_CODE_SHA unchanged = `da36acfdbd19c896f3fdc0dc1bc1e16ac2b42eb4`).
- **No database schema or frozen files changed.**
- Live metrics captured (read-only): V2_ELIGIBLE_UNSENT=12 / READ_ONLY_SAFE_UNIQUE_ORGS=11 / MATERIALIZED_FSP_PLANNED=0 / BROAD_READY=95 / VISIBLE_FIRST_PARTY_EMAILS=338 (canonical).
- Flagged: repo currently tracks `*.db` files from prior history (violates safe-git rule E); recommend purge via separate authorization.

## 2026-09-10 — Phase 4A Production Scheduler Resume (authorized)
- Restored 4 canonical WorkBuddy automations PAUSED→ACTIVE (Inventory/Pre-Send/Preflight/Outreach); no schedule change.
- Immediate one-off Inventory run (11:27): BroadReady=34/30 short-circuit → email-recovery lane skipped → all SAFE metrics delta=0. REAL_SMTP=0.
- Read-only Metric Provenance Audit: METRIC_DEFINITION_MISMATCH_FOUND=true (4 conflicting VISIBLE_FIRST_PARTY_EMAILS defs; campaign_eligible_v2 not a stored column; final_send_plan has no organization_key).
- PostSend reclassified UNIQUE_REQUIRED (not duplicate) — retains Windows task.

## 2026-09-09 — P3D Production Legacy Decommission & Cleanup (authorized)
- Enumerated all live execution surfaces (automations / Windows tasks / service / scripts / _retired).
- Removed 5 legacy automations; moved 57 files to `_retired/p3d_20260909/`.
- BDExecutionHost kept Stopped (audited, not deleted). DUPLICATE_ACTIVE_TRIGGER_COUNT validated = 0.
- Frozen send chain (V2/MX/Preflight/Sender/final_send_plan/Auth) untouched.
