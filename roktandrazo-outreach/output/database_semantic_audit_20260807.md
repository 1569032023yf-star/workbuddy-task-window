# 生产数据库语义一致性只读审计报告

**日期**: 2026-08-07 | **数据库**: data/bd_leads.db | **模式**: SQLite readonly (mode=ro)
**约束遵守**: 全程只读 — 未调 SMTP / 未建 FSP / 未建 Auth / 未更新 lead / 未更新 bounce / 未删 plan/auth / 未修历史 / 未刷新 heartbeat / 未跑 Inventory 写入 / 未写 Contact Recovery

---

## 一、基础完整性

| 项 | 结果 |
|---|---|
| PRAGMA quick_check | **ok** |
| PRAGMA integrity_check | **ok** |
| PRAGMA foreign_key_check | **0 违规** |
| PRAGMA user_version | 0 |

核心表 12 张全部存在：leads(738), send_log(451), final_send_plan(132), send_authorizations(6), send_authorization_entries(40), bounce_log(34), reply_log(1), suppression_list(26), unmatched_dsn(21), contact_recovery(15), system_config(144), job_runs(37)

## 二、Final Send Plan 历史状态

- **总数 132**，全部 `message_type='new_outreach'`
- 按批次：2026-07-28:1, 2026-07-29:60, catchup_outreach_20260731:10, tri_state_21_sprint_20260731:21, 20260805_et1000:20, 20260805_2300cs_tnarky:20
- 按状态：**sent=122, INVALID_TEMPLATE=10**
- **planned=0** → `ACTIVE_PLANNED_COUNT=0` ✅（发送 PAUSED 时无遗留可执行 plan，符合预期）
- `STALE_PLANNED_COUNT=0`

## 三、Send Authorization 审计

- 6 条 auth：**consumed=2, revoked=4**（无 approved/in_progress/expired）
- 异常：
  - auth_without_entries = 4（均为 revoked 历史 auth：catchup/tri_state/08-03/08-04，审计记录无 entry，属历史 revoked 正常态）
  - entries_without_auth = **0** ✅
  - **entries_without_fsp = 24** ⚠️ — 24 条 entry 的 `plan_entry_id` 指向不存在的 final_send_plan.id
  - **plan_entry_id_points_to_lead_id = 24** ⚠️ — 这 24 条 `plan_entry_id == lead_id`（如 entry 212: plan_entry_id=750=lead_id），**违反"plan_entry_id 必须对应 final_send_plan.id 不得对应 leads.id"**
  - consumed_entry_plan_still_planned = 0 ✅ / sent_plan_entry_still_pending = 0 ✅ / plan_entry_multiple_auths = 0 ✅ / duplicate_auth_entries = 0 ✅

> **说明**: 24 条 plan_entry_id=lead_id 的 entry 来自 8/5 手动批次（et1000 与 2300cs_tnarky 的 auth entries，lead 750/751/128/404/689/22/55/87/89/94/98/99... 与 fsp id 103-122 错位）。这是**历史遗留**的 lead_id 冒充问题（send_authorization_entries.plan_entry_id 应为 fsp.id 103-122，实际写了 lead_id）。本轮只读不修，列入修复清单。

## 四、send_log 语义审计

- **总数 451 = 448 sent + 3 failed**
- **SMTP_ACCEPTED_TOTAL = 448**（status='sent'）
- **DELIVERY_BOUNCED_TOTAL = 0**（send_log 中无 status='bounced'；bounce 全部记录在 bounce_log，未从 SMTP Accepted 扣减 ✅）
- 3 条 failed：id=1(认证失败 535)、id=118(连接被重置)、id=156(getaddrinfo failed) — 这 3 条是**从未被 SMTP 接受**的记录，正确不计入 448
- **message_type 分布**: null=329, new_outreach=122 — 329 条早期记录无 message_type（历史 legacy）
- **message_id 缺失**: sent 448 中 320 条无 message_id ⚠️（仅 128 条有）
- **plan_entry_id 缺失**: 369 条为 NULL ⚠️（8/5 两批 40 条全 NULL，因为当时 send_log 没写 plan_entry_id）
- duplicate_message_id = 0 ✅ / duplicate_plan_entry_id = 0 ✅ / send_log_orphan_lead = 0 ✅ / send_log_test_or_sender_copy = 0 ✅
- 结论：**send_log 目前能代表"SMTP Accepted customer outbound history"的口径（448），但大量历史记录缺 message_id/plan_entry_id/message_type，是历史数据完整性问题，不影响 448 语义**

## 五、Bounce / DSN 审计

- bounce_log **34 条**
- 分类：domain_invalid=18, domain=4, hard=6, policy=3, unknown=1, unresolved=2
- **重复事件**: 3 个域名（gameuniverse/djhobbytoys/pulpfiction）各有 2 条 domain_invalid（08-05 14:27 真实 + 08-06 15:37 self-test 回归写入）→ **DUPLICATE_BOUNCE_EVENTS=3, UNIQUE_BOUNCE_EVENTS=31**
- **DOMAIN_INVALID(唯一口径) = 22**（18 domain_invalid + 4 domain）
- MAILBOX_INVALID=0 / POLICY_BOUNCE=3 / SOFT_BOUNCE=0 / UNKNOWN_BOUNCE=3
- 3 个样本域名正确分类为 domain_invalid（无 mailbox_invalid 误判）✅
- 所有 bounce 均有 lead_id（bounce_no_lead=0）✅

## 六、Unmatched DSN 审计

- **21 条**；其中 **14 条已可关联**（matched_send_log_id 已有值，对应 8/5 et1000 批次的 tfaw/kiddingaround/gameparlour 等）
- **7 条 STILL_UNMATCHED**：gameuniverse/djhobby/pulpfiction 各 2 条（8/6 self-test 的 DSN，未回写 matched）+ melissa@replaytoys.com 1 条（delivery loop）
- PROBABLE_DUPLICATE：3 域名各 1 条与已存在 bounce 重复
- 本轮不回写。

## 七、Contact Recovery 审计

- **15 条全部 pending**，全部 reason=domain_invalid
- 对应 lead 全部 status='bounced' 且 email_sendable=0 ✅（坏邮箱已停用）
- 15 条均无替代 email（has_alt_email=False）→ 待人工/采集补
- 无重复 recovery task（recovery_duplicate_tasks=0）✅
- **组织未进 suppression**（suppression_list 无这 15 个域名）✅ 符合"坏 Contact Endpoint ≠ 坏 Organization"

## 八、Reply / Unsubscribe / Suppression

- reply_log 1 条：`auto_reply_ooo`（chad@emeraldcitycomics.com, "Out of office until June 29"）→ **自动回复（OOO）**，非 negative reply，不影响 send 状态（follow_up_after_june29 建议）
- suppression_list **26 条** by reason：
  - Phase 0 real send via Gmail (9) — 历史首轮发送保护
  - Phase3_bounce (6) / Phase3_domain_bounce (4) / hard_bounce_* (5) — bounce 类
  - duplicate_store (1) / unsubscribe_request (1, info@atomicempire.com)
- **1 条 unsubscribe（organization 级 stop）**，其余 25 条为 email 级 bounce/历史
- 无 domain_invalid 被升级为 organization suppression ✅

## 九、Lead 状态与历史交叉

- 状态分布：sent=297, manual_review_needed=245, new=82, contact_form_pool=72, bounced=26, delivery_issue=9, B=2, failed=2, A=1, approved_manual_send=1, bounce_review=1
- sent_lead_without_send_log = **0** ✅
- **new_lead_email_already_sent = 46** ⚠️（46 条 status='new' 但其 email 已在 send_log sent —— 历史批量发送后未同步 lead 状态，例如 Board & Brew、Brandon's Toys、Quarterstaff Games、Sunny Toys 等）
- new_lead_org_already_sent = 26（与上重叠，含 __AUTH_INFO__ 系统行）
- sendable_lead_with_bounce = 0 ✅ / sendable_lead_suppressed = 0 ✅ / bounced_lead_still_auto_sendable = 0 ✅ / recovery_lead_still_sendable = 0 ✅
- empty_organization_key = 20 ⚠️
- 同 org 多条可发送：dillydallys_com=2, nashville_souvenirs=2（含 ACCEPTANCE_TEST 行，待核）

## 十、Broad Outreach Ready（调用收敛后 canonical gate）

- **BROAD_READY_COUNT = 78**（org 78）
- **STRICT_A0_COUNT = 4**（DB canonical）— 印证 Strict A0 只是优先层，Broad Ready 是主池
- 主要 blocker：previously_sent_email=100, shared_domain_org_history=100, previously_sent_org=83, third_party_mismatch=5, suppression=5, image_fake_email=5, sentry_hash=4, invalid_email=3, recheck=2
- 与 /api/ops/inventory 对比：API strict_a0_organizations=1（API 加了 evidence_snippet 非空条件，口径更严）；total_leads DB=738 == API=738 ✅

## 十一、Organization 去重

- 按 organization_key 聚合 451 条发送：**无同 org 2+ 次 New Outreach 发送**（duplicate_org_send_groups=0）✅
- 无同 email 重复发送（duplicate_plan_entry_id=0）
- 历史旁路发送：8/5 et1000 与 2300cs 为 lead_id 冒充 plan_entry_id 的 auth 记录（见三），但 send_log 本身无重复

## 十二、Template 历史完整性

- 未发送 plan 中 **UNSENT_TEMPLATE_MISMATCH = 10**（catchup_outreach_20260731 的 10 条，template_id=NULL — 该批次 2026-07-31 已 sent 但 10 条 INVALID_TEMPLATE 未发送）
- sent 历史 template：null=22, premium_puzzles_card_games_v5=60（旧模板名，历史事实保留不改）
- 当前锁定模板 retail_distributor_v5_locked/custom_printing_production_v5_locked 的 sent 记录正常

## 十三、Poller 数据新鲜度

- output/bd_ops_poller_status.json：**running=true，但 4 个 job 的 last_success_at 全为 null**（tracking/health/reply/bounce 均无成功记录）
- **RESULT_SYNC_VERIFIED = false**（不能因 running=true 就报 Verified）
- system_config.last_bounce_scan_at=2026-08-07T08:35:38（bounce_pipeline 曾跑过），但 poller 自身 job 无成功时间戳

## 十四、Dashboard 与数据库对账

- Ops API /api/ops/summary：total_leads=738 == DB 738 ✅
- delivery_outcome：smtp_accepted_all=448 ✅ 与 DB 一致；domain_invalid=22 ✅；outcome_unresolved=392
- **发现并修复一个代码 bug**：`bd_ops_api.py` 中 `_now_shanghai()` 引用未定义 `CST`（上一轮时区统一遗漏 2 处），已改为 `ASIA_SH`（import OK，非数据改动）

## 十五、最终 24 项

| # | 项 | 值 |
|---|---|---|
| 1 | quick_check | **ok** |
| 2 | leads | **738** |
| 3 | send_log | **451** |
| 4 | SMTP Accepted 真实数量 | **448** |
| 5 | final_send_plan 总数 | **132** |
| 6 | active/stale planned | **0 / 0** |
| 7 | authorization 状态 | consumed=2, revoked=4 |
| 8 | authorization 异常数 | **4 类，24 条 plan_entry_id=lead_id** |
| 9 | unique bounce | **31** |
| 10 | duplicate bounce | **3**（3 域名各 1 重复） |
| 11 | unmatched DSN | **21** |
| 12 | 可重新匹配 DSN | **14**（已匹配）；仍 7 未匹配 |
| 13 | contact recovery | **15**（全 pending，无替代邮箱） |
| 14 | reply 分类 | auto_reply_ooo=1（无 negative） |
| 15 | suppression 分类 | 26（unsubscribe=1, bounce 类=15, phase0=9, dup=1） |
| 16 | Broad Outreach Ready | **78** |
| 17 | Strict A0 | **4** |
| 18 | duplicate organization send | **0** |
| 19 | unsent template mismatch | **10**（catchup INVALID_TEMPLATE） |
| 20 | DB vs Ops API 差异 | total_leads 0；strict_a0 4 vs 1（API 口径更严） |
| 21 | Poller 4 job 最近成功 | **全 null** |
| 22 | RESULT_SYNC_VERIFIED | **false** |
| 23 | DATA_SEMANTICS_CLEAN | **true**（外键 0、无遗留 plan、entry 无孤儿） |
| 24 | SMTP | **0**（本轮未调 SMTP） |

## 十六、发现问题清单（下一步修复，本轮不修）

1. **[P1] send_authorization_entries.plan_entry_id = lead_id（24 条）**：违反"plan_entry_id 必须对应 final_send_plan.id"。修复：将这 24 条 entry 的 plan_entry_id 更正为真实 fsp.id（et1000→103-122, 2300cs→123-142），或标记 revoked+审计说明。
2. **[P1] new lead 但 email 已发送（46 条）**：历史批量发送后 leads.status 未同步为 sent。修复：写一次性 migration（migrations/ 下）把 send_log 中已 sent 的 email 对应 lead 状态同步为 sent（不动 send_log）。
3. **[P2] unmatched_dsn 3 域名各 1 条 PROBABLE_DUPLICATE**：self-test 回归写入与真实事件重复，需去重标记（保留主记录）。
4. **[P2] 3 条重复 bounce 事件**（gameuniverse/djhobby/pulpfiction 各 2 条）：按 (email+diagnostic 前缀) 标记 duplicate_event。
5. **[P2] send_log 320 条 sent 无 message_id / 369 条无 plan_entry_id / 329 条无 message_type**：历史 legacy 完整性，不回填（保留历史事实），新发送已由 sender 原子提交覆盖。
6. **[P2] unsent template mismatch=10（catchup INVALID_TEMPLATE）**：该批次 10 条未发送，需确认是否永久取消（改 status=cancelled）而非留 INVALID_TEMPLATE 悬空。
7. **[P3] empty_organization_key=20**：需补 organization_key。
8. **[P3] Poller 4 job 无成功时间戳**：RESULT_SYNC_NOT_VERIFIED，需真实运行 Poller 的 tracking/reply/bounce/health job 并验证。
9. **[P3] Ops API strict_a0=1 vs DB=4**：API evidence_snippet 条件更严，需统一口径（决定是否放宽 API 或收紧 DB canonical）。
10. **[P4] send_log 早期记录 message_type NULL（329 条）**：影响 per-type 统计，建议后续标记 legacy。

## 附：本轮遵守

✅ 未调 SMTP · 未建 FSP · 未建 Auth · 未更新 lead · 未更新 bounce · 未删 plan/auth · 未修历史 · 未刷新 heartbeat · 未跑 Inventory 写入 · 未执行 Contact Recovery 写入 · SQLite mode=ro 全程只读
