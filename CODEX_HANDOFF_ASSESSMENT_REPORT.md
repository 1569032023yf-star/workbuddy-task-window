# Codex 交接包评估报告 / Codex Handoff Assessment Report

Generated: 2026-07-13 11:51 Asia/Shanghai
Assessor: WorkBuddy (production system owner)
Handoff Package: `D:\CODEX\workbuddy_handoff_from_codex_20260713_1105\`

---

## 1. 已在生产的成果 / Assets Already in Production

### ✅ Patch 1 — Legacy Live Disable (ALL ACTIVE)

| File | Status | Evidence |
|---|---|---|
| `sender.py` | ACTIVE | `_send_email_smtp()` returns immediately; `send_email_to_lead()` fail-closed on non-dry_run |
| `main.py` | ACTIVE | `send`, `send-now`, `pipeline-live` commands → `sys.exit(2)` before `init_db()` |
| `pipeline.py` | ACTIVE | `run_full_pipeline(dry_run=False)` and `run_send_emails(dry_run=False)` → fail-closed |
| `send_phase2.py` | ACTIVE | `sys.exit(fail_closed_legacy_live())` at entry |
| `send_phase3.py` | ACTIVE | `sys.exit(fail_closed_legacy_live())` at entry |

**Verification**: All5 fail-closed paths tested. Backup at `backups/p0_patch1_legacy_live_disable_20260710_1053`.
**No re-overwrite needed.** Production sending chain is `daily_operator_auto.py → daily_session.py → bd_sender.py` only.

### ✅ Message-ID Fix (ACTIVE)

- `bd_sender.py`: Adds `Date`, `Message-ID` (via `make_msgid(domain="roktandrazo.com")`), `MIME-Version`, `Reply-To`
- `agent_bounce_auditor.py`: Classifies Message-ID bounces as `message_id_missing` (not `hard`)
- `daily_session.py`: Does not suppress `message_id_missing` bounces
- Backup at `backups/message_id_fix_20260707_1155`

### ✅ Evidence Snippet Backfill (DONE)

- Schema migration: `evidence_snippet`, `evidence_checked_at`, `evidence_method` columns added
- 26 leads have non-empty `evidence_snippet` values
- Backup at `backups/evidence_snippet_schema_20260707_125936`

### Current Production DB State

| Metric | Value |
|---|---|
| Total leads | 475 |
| Sent | 203 |
| A0 sendable | 0 (pool empty) |
| Suppression entries | 26 |
| Send log entries | 237 (234 sent, 3 failed) |
| Latest send | 2026-07-13 02:21:40 |

---

## 2. 候选模块理解评估 / Candidate Module Comprehension

### 2A. `lead_hygiene_gate.py` — ✅ 可理解，⚠️ 需适配

**概念**: 纯函数 A0 资格判定门，无副作用、无网络、无 DB 依赖。
**逻辑**: 检查14个风险条件（email缺失/无效、官网缺失、证据缺失、非官方来源、非目标州、suppressed、bounced、delivery_issue、already_sent、duplicate_domain、guessed_email、目录域、角色前缀、未验证免费邮箱）。

**字段映射分析（11个缺失字段）**:

| Gate expects | Production equivalent | Derivation method |
|---|---|---|
| `official_match` | **NOT IN DB** | Derive from `email_verified_on_official_site=1 AND email_source_type IN OFFICIAL_SOURCE_TYPES` |
| `social_only` | **NOT IN DB** | Derive from `email_source_type LIKE '%social%'` or `status='B1_social_verified'` |
| `contact_form_only` | **NOT IN DB** | Derive from `email_source_type='contact_form_only'` or `contact_form_url IS NOT NULL` |
| `suppressed` | **NOT IN DB** | JOIN `suppression_list` on email |
| `bounced` | **NOT IN DB** | JOIN `bounce_log` WHERE `bounce_type='hard'` or check `bounced_at IS NOT NULL` |
| `delivery_issue` | **NOT IN DB** | Check `status='delivery_issue'` |
| `already_sent` | **NOT IN DB** | JOIN `send_log` WHERE `status='sent'` |
| `duplicate_domain` | **NOT IN DB** | Compute via `domain_hash` GROUP BY HAVING COUNT > 1 |
| `guessed_email` | **NOT IN DB** | Derive from `email_source_type='guessed_email'` |
| `third_party_directory` | **NOT IN DB** | Derive from domain matching (yelp.com, yellowpages.com, etc.) |
| `supplier_email` | **NOT IN DB** | Derive from email pattern or notes |

**额外发现**: Gate 的 `OFFICIAL_SOURCE_TYPES` 不含 `manual_lookup`，但生产 sendable 查询已接受 `manual_lookup`。8 条 `manual_lookup` 有效线索会被 gate 拒绝。

### 2B. `b_pool_enrichment.py` — ⚠️ 部分可理解，❌ 不可直接运行

**概念**: HTTP-first B 池增强引擎，顺序：已有官网 → Maps → Facebook → 联系表单 → 官网验证。
**逻辑质量**: 结构清晰，关注点分离好，metrics 统计完整，安全设计（注入 fetcher、无 DB 写入、无 SMTP）。

**关键阻塞问题**:
1. **Import 路径**: `from app.lead_hygiene.lead_hygiene_gate import ...` — 生产目录结构无 `app/` 包
2. **Maps/Facebook URL 字段**: `maps_url`、`facebook_url` 不在生产 DB schema 中
3. **phone 字段**: 不在生产 DB schema 中
4. **website vs official_website**: Gate 使用 `website`，生产使用 `official_website`
5. **Fetcher 未实现**: 真实 HTTP 抓取需要 adapter 层，搜索实验证明外部通道阻塞
6. **Synthetic fixture 结果不可外推**: `26/50 A0` 是合成数据结果，不代表生产转化

---

## 3. 测试结果 / Test Results

### 3A. Codex 原始测试

- `test_lead_hygiene_gate.py`: ❌ Import 失败（`app.lead_hygiene` 不存在于生产目录结构）
- `test_b_pool_enrichment.py`: ❌ 同上（`app.lead_factory` 不存在）

### 3B. 生产兼容测试（WorkBuddy 新编写）

测试文件: `workbuddy_candidate_modules/test_hygiene_gate_production.py`

| Category | Tests | Passed | Failed |
|---|---|---|---|
| Pure Logic (normalize_state, email_domain) | 7 | 6 | 1 |
| HygieneDecision (all risk gates) | 22 | 22 | 0 |
| Schema Compatibility (DB read-only) | 15 | 15 | 0 |
| Production Risk Scenarios (DB read-only) | 6 | 3 | 3 |
| **Total** | **50** | **46** | **4** |

### Test Failure Analysis

| Test | Root Cause | Severity |
|---|---|---|
| `test_out_of_scope` | Test assertion bug: expects `"California"`, gate returns `"CALIFORNIA"` (correct uppercasing) | Low (test bug, not gate bug) |
| `test_no_leads_in_suppression_list_are_sendable` | **5 suppressed leads** still `status=new/A0` in DB | Medium (data hygiene, not logic bug — production sendable query correctly filters) |
| `test_only_tn_ar_ky_in_sendable` | **4 non-target leads** (CA, ME, MI, MD) still `status=new/A0` | Medium (legacy Phase 0/1 data, correctly filtered at send time) |
| `test_no_leads_in_suppression_list_are_sendable` | **`manual_lookup` source type** — gate rejects but production accepts | Medium (gate too strict for this source type) |

### Production Data Issues Found

| Issue | Count | Impact |
|---|---|---|
| Suppressed leads still status=new/A0 | 5 | No actual risk (filtered by sendable query) |
| Non-TN/AR/KY leads still status=new/A0 | 4 | No actual risk (filtered by sendable query) |
| `guessed_email` leads in DB | 173 | Correctly blocked — these are B-pool candidates |
| `manual_lookup` leads rejected by gate | 8 | Gate would incorrectly reject valid manually-verified leads |

---

## 4. 可合并建议 / Merge Recommendations

### `lead_hygiene_gate.py` — **建议有条件合并（Conditional Merge）**

**理由**: 核心逻辑正确且有价值（14个风险检查全覆盖），但需要以下适配才能用于生产：

**Required Adaptations**:
1. 写一个 `build_candidate_from_db_row(row)` 映射函数，将生产 DB 行转换为 gate 期望的 candidate dict
2. 将 `official_match` 映射为 `email_verified_on_official_site=1 AND email_source_type IN OFFICIAL_SOURCE_TYPES`
3. 将 `suppressed` 映射为 `email IN suppression_list`
4. 将 `bounced` 映射为 `email IN bounce_log WHERE bounce_type='hard'`
5. 将 `already_sent` 映射为 `email IN send_log WHERE status='sent'`
6. 将 `duplicate_domain` 映射为 `domain_hash` 重复检查
7. 将 `guessed_email` 映射为 `email_source_type='guessed_email'`
8. 将 `manual_lookup` 加入 `OFFICIAL_SOURCE_TYPES`（或创建独立白名单）
9. 将 `delivery_issue` 映射为 `status='delivery_issue'`
10. 将 `mx_provider LIKE '%Exchange%'` 检查加入 gate

**合并后价值**: 替代当前散落在 `bd_db.py`、`daily_session.py`、`daily_operator_auto.py` 中的重复过滤逻辑，统一为一个可测试的门控模块。

### `b_pool_enrichment.py` — **建议不合并（Do Not Merge）**

**理由**:
1. 核心概念（Maps → Facebook → 官网 → 验证的漏斗）有参考价值，但所有外部通道已被证明阻塞
2. Import 路径、schema、fetcher 接口均需全面改写
3. 合成 fixture 测试结果不可外推到生产
4. 当前生产 A0 瓶颈在**采集速度**而非**增强逻辑**

**建议**: 保留概念参考，不投入适配工作。

---

## 5. 必须废弃 / Must Discard

| Item | Reason |
|---|---|
| `test_b_pool_enrichment.py` (Codex) | 依赖 `app.lead_factory` import 和 synthetic fixture |
| Synthetic 50-record fixture | 不是生产数据，`26/50 A0` 不可外推 |
| Codex `test_lead_hygiene_gate.py` | 依赖 `app.lead_hygiene` import |
| Codex automations YAML | 不可注册为 WorkBuddy scheduled tasks |
| Search channel experiments | 最终 provider 成功数 0，证明通道阻塞 |
| Patch 2 (proposed) | 未合并，未通过生产验收 |
| `b_pool_enrichment.py` 的 `build_synthetic_fixture()` | 合成数据 |

---

## 6. 下一步优先级 / Next Priority

### 推荐：线索清洗优先（Lead Hygiene First）

**理由**:

| Dimension | Lead Hygiene | Search Speed |
|---|---|---|
| **Current bottleneck** | 5 suppressed + 4 non-target still in A0 pool; `manual_lookup` not accepted by gate; no unified hygiene layer | A0 pool is 0 — need new leads |
| **Effort** | Low — map 11 fields, write adapter function | High — external channels blocked, need new discovery approach |
| **Risk** | Low — pure logic, no network | High — network adapters unproven |
| **Impact** | Cleaner A0 pool, unified testable gate, prevent future data hygiene issues | Potentially faster lead discovery (unproven) |
| **Blocked by** | Nothing — can start immediately | Network access, adapter development, search provider selection |

**具体行动**:
1. 为 `lead_hygiene_gate.py` 写 `build_candidate_from_db_row()` 映射函数（~50行）
2. 将 `manual_lookup` 加入白名单
3. 写入生产兼容版到 `roktandrazo-outreach/lead_hygiene_gate.py`
4. 修改 `daily_operator_auto.py` 的 sendable 查询使用统一 gate
5. 批量修复 5 条 suppressed + 4 条 non-target 的 status
6. 然后专注 A0 池补满（采集 > 增强 > 搜索速度）

---

## 7. 生产运行状态 / Production Status

### ✅ 保持现有生产正常运行

| Check | Status |
|---|---|
| Patch 1 legacy disable | ACTIVE — all 5 files fail-closed |
| Message-ID fix | ACTIVE — bd_sender.py generates proper headers |
| Production send chain | ACTIVE — `daily_operator_auto → daily_session → bd_sender` |
| Daily automation | ACTIVE — "Roktandrazo BD Daily Orchestrator - 09:00 China Time" |
| Suppression filtering | WORKING — 26 entries correctly filtered |
| Bounce protection | WORKING — 11 bounced leads tracked |
| A0 pool status | EMPTY (0 sendable) — needs replenishment |
| `bd_sender.py` | UNMODIFIED by Patch 1 — fully functional |
| `bd_db.py` | UNMODIFIED — schema intact |
| DB integrity | 475 leads, 237 send_log, 26 suppression — consistent |

**结论**: 生产系统稳定，不需要回滚，不需要重启。当前瓶颈是 A0 池耗尽（需要新线索采集），不是代码问题。

---

## 8. WorkBuddy 编写的测试文件

| File | Purpose |
|---|---|
| `workbuddy_candidate_modules/lead_hygiene_gate.py` | Codex 原版（隔离副本） |
| `workbuddy_candidate_modules/test_hygiene_gate_production.py` | 50 个生产兼容测试 |
| `workbuddy_candidate_modules/b_pool_enrichment.py` | Codex 原版（隔离副本） |
| `workbuddy_candidate_modules/test_b_pool_enrichment.py` | Codex 原版（仅参考） |

**所有测试均在只读模式运行，未修改生产 DB。**
