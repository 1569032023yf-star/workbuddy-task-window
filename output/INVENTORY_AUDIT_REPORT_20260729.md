# Production Inventory Audit Report / 生产库存审计报告

**Date / 日期**: 2026-07-29 09:45 CST  
**Scope / 范围**: Full production database audit + Automation verification + 60-send readiness  
**Authority / 权威**: Read-only, no SMTP, no Final Send Plan created  

---

## 1. Strict A0 Locations / 严格 A0 地点

| Metric | Count | SQL Logic |
|--------|-------|-----------|
| Strict A0 Locations | **1** | `WHERE status='new' AND confidence_score='A' AND auto_sendable=1` |
| Strict A0 Organizations | **1** | `COUNT(DISTINCT COALESCE(NULLIF(organization_key,''), 'org_'||id))` from above |

Only lead: id=316, B Side Games, Spokane WA, `bsideboardgamesandpuzzles_com`.

> 仅 1 个严格 A0 地点（1 个组织）。

---

## 2. Strict A0 Organizations / 严格 A0 组织

**1 organization**: `bsideboardgamesandpuzzles_com` (B Side Games)

> 1 个严格 A0 组织。

---

## 3. Organization Outreach Opportunities / 组织级发送机会

**Count: 1** (with full gate logic)

| # | lead_id | Organization | City | State | Email | Source |
|---|---------|-------------|------|-------|-------|--------|
| 1 | 316 | bsideboardgamesandpuzzles_com | Spokane | WA | bsidegames.info@gmail.com | official_page_visible |

**Full gate applied**:
- ✅ status='new', score='A', auto_sendable=1
- ✅ organization_key not null
- ✅ website present, evidence_url present, evidence_snippet present
- ✅ email_source_type in valid whitelist (includes official_page_visible, official_mailto)
- ✅ Not sent (email, lead, org all not in send_log)
- ✅ Not suppressed, not bounced, not replied
- ✅ Valid email format, not test/example

**Corrected whitelist**: added `official_page_visible` and `official_mailto` — these are legitimate source types (email visible on official page, email from mailto link on official page).

> 完整门禁计算后的组织发送机会：**1 个**。白名单已修正，包含 `official_page_visible` 和 `official_mailto`。

---

## 4. 60-Send Target Assessment / 60 条发送就绪判定

| Metric | Value |
|--------|-------|
| Target / 目标 | **60** |
| Actual qualified / 实际合格 | **1** |
| **Gap / 缺口** | **59** |

**❌ CANNOT meet 60. Tonight's maximum = 1.**

> **无法达到 60。今晚实际最大 = 1 条。**

---

## 5. Real Gap / 真实缺口

**59 organizations short.** Cannot fill from:
- Manual Review (41 leads)
- Website Lookup (18 leads)  
- Contact Form Only (0 leads)
- Low Priority (22 leads)
- Staging (0 results — pipeline empty)

> 真实缺口 59 个组织。不能从 Manual Review、Website Lookup、Contact Form、Low Priority 或 Staging 补齐。

---

## 6. Manual Review / 人工审核

**41 leads** (`status='new'` but `auto_sendable != 1`)

19 of these have `score='A'` but are blocked by:
- 11: `organization_key` is NULL/empty — never populated
- 4: invalid/garbage emails (image filenames: `tbs_rev_hz_type_110x@2x.png`, `certificate1_235x235@2x.jpg`, etc.)
- 3: `inventory_recovery` source with valid-looking data but suspicious emails:
  - id=320: `diane@sevendaysvt.com` — community newspaper contact, not the store
  - id=417: `www.kll@toystoreandgifts.com` — email starts with "www"
  - id=432: `13e49d785...@sentry.io` — error tracking service, not business contact

> 41 条人工审核。19 条 A 分但被 `auto_sendable=0`、缺失 organization_key 或垃圾邮箱卡住。

---

## 7. Website Lookup / 官网查找

**18 leads** (`status='new'` with missing email or evidence_url)

> 18 条缺少邮箱或证据 URL。

---

## 8. Contact Form Only / 仅联系表��

**0 leads** with `email_source_type='contact_form'` and `status='new'`

> 0 条仅联系表单。

---

## 9. Staging / 待处理

| Table | Rows |
|-------|------|
| lead_discovery_results | **0** |
| lead_discovery_hits | **0** |
| lead_discovery_query_state | **0** |
| city_discovery_reports | **0** |
| fb_enrichment_queue | **20** (pending, no consumption) |

**Staging pipeline is completely empty. Discovery cursor was never persisted.**

> Staging 管线完全为空。检索游标从未持久化。

---

## 10. Inventory Automation Last Real Run / 最近真实运行

| Field | Value |
|-------|-------|
| Automation ID | automation-1784775229336 |
| Status | ACTIVE |
| Schedule | DAILY 15:00 Asia/Shanghai |
| Prompt | `python bd_orchestrator.py --stage inventory --live` |
| Last confirmed output | **Unknown — no job_runs records, no staging data** |
| Run lock | STUCK: `inventory:2026-07-23:4af31342` held since July 23 |

The inventory run_lock from July 23 has never been released. All discovery tables are empty. The automation shows ACTIVE but has produced no verifiable output.

> Inventory Automation 最近一次真实运行未知。`run_lock` 自 7 月 23 日以来一直卡住。所有发现表为空。Automation 显示 ACTIVE 但无可验证输出。

---

## 11. Cursor Advancement / Cursor 是否前进

**Cursor: NOT ADVANCED.** `lead_discovery_query_state` = 0 rows. No cursor was ever saved.

> Cursor 未前进。从未保存过游标状态。

---

## 12. New Candidate Count / 新增候选数

**0** — all discovery staging tables are empty.

> 新增候选 0。

---

## 13. New A0 Organization Count / 新增 A0 组织数

**0** — no new organizations promoted to A0 since pipeline is stalled.

> ���增 A0 组织 0。

---

## 14. Current Active City / 当前活跃城市

| Field | Value |
|-------|-------|
| Nashville, TN | `pending` in retail_city_queue (priority=1) |
| All 7 queue entries | `pending` — NONE started |

City queue: Nashville → Memphis → Knoxville → Little Rock → Fayetteville → Louisville → Lexington (all TN/AR/KY primary states)

**Nashville has not been started.** The query was planned as 22/22 with `partial_first_page_collected` WebFetch status — but no discovery results were imported.

> Nashville 尚未启动。队列中 7 个城市全部为 `pending`。

---

## 15. Next Inventory Action / 下一库存动作

**Required**: 
1. Release the stuck `run_lock:daily_outreach:inventory:2026-07-23`
2. Initialize Nashville discovery with `browser_maps` provider
3. Persist cursor state after each batch
4. Import staging results → validate websites → extract emails → score → promote to A0
5. Process `fb_enrichment_queue` (20 items pending)

> 需要：释放卡住的 run_lock、启动 Nashville 发现、持久化游标、处理 fb_enrichment_queue。

---

## 16. send_log Unchanged / send_log 是否不变

**send_log = 330** (unchanged since 901 Games pilot send at 09:07).  
No SMTP was called during this audit.

> send_log 保持 330，本次审计未调用 SMTP。

---

## 17. Final Send Plan Not Created / 是否未创建

**Confirmed: planned=0, sent=1** (only the 901 Games pilot entry).  
No new Final Send Plan was created.

> 确认未创建新计划。planned=0, sent=1。

---

## 18. SMTP Not Called / SMTP 是否未调用

**Confirmed.** All scripts used `conn` for read-only queries. No `send_one()`, no `bd_sender`, no SMTP connections.

> 确认 SMTP 未调用。

---

## 19. Tonight's Maximum Planned / 今晚最终允许计划数量

```
Maximum allowed tonight: 1 (B Side Games, Spokane WA)
Target: 60
Shortfall: 59
```

**Cannot operate at 60/day without inventory pipeline recovery.**

> 今晚最多允许 1 条。在库存管线恢复之前无法按 60 条/天运行。

---

## 20. Auto Pre-Send/Outreach Still Paused / 自动任务仍暂停

| Automation | Status |
|------------|--------|
| Pre-Send 22:30 | PAUSED |
| Outreach 23:00 | PAUSED |
| Post-Send 00:10 | PAUSED |
| End-of-Day 00:25 | PAUSED |
| Inventory 15:00 | ACTIVE (but stuck) |

> Pre-Send、Outreach、Post-Send 均保持 PAUSED。Inventory ACTIVE 但卡住。

---

## 21. Proposed Inventory Thresholds (60/day mode) / 建议库存阈值

| Level | Current | Proposed (60/day) |
|-------|---------|-------------------|
| Critical | 60 | 60 |
| Warning | 80 | 120 |
| Target | 120 | 180 |

*Not applied — report only, pending approval.*

> 仅建议，未修改，等待批准。

---

## Summary / 总结

```
╔══════════════════════════════════════════════════════════════╗
║  PRODUCTION INVENTORY STATUS: CRITICAL                      ║
║                                                              ║
║  Total Leads:              621                               ║
║  Strict A0 Locations:        1                               ║
║  Strict A0 Organizations:     1                               ║
║  Organization Outreach Opps:  1  (B Side Games, Spokane WA)  ║
║  60-Send Target:            60                               ║
║  60-Send GAP:               59  ❌                            ║
║                                                              ║
║  Staging:                   EMPTY (pipeline stalled)         ║
║  Inventory Run Lock:        STUCK since July 23              ║
║  Nashville:                 PENDING (not started)            ║
║  Discovery Cursor:          NEVER PERSISTED                  ║
║  send_log:                  330 (unchanged)                  ║
║  SMTP:                      NOT CALLED                       ║
║  Final Send Plan:           NOT CREATED                      ║
║  Automations:               Pre-Send/Outreach PAUSED         ║
║                                                              ║
║  BOTTOM LINE: Cannot send 60 tonight.                        ║
║  Pipeline recovery required before scaling to 60/day.        ║
║  今晚无法发送 60 条。管线恢复后方可扩容至 60 条/天。           ║
╚══════════════════════════════════════════════════════════════╝
```
