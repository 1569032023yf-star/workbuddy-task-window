# AUTOMATION CLEANUP - 2026-10-20 · 自动任务去重与安全精简

**生成时间 / Generated**: 2026-10-20 11:05:32 +08
**执行范围 / Scope**: 仅 WorkBuddy 自动化（经正式自动化管理入口）。Windows 计划任务与生产数据库全程**只读**核查；无生产写入、无邮件、无调度权威变更。
**性质 / Nature**: 一次性清理，**未创建**任何周期性清理任务 / one-off cleanup, no recurring cleanup automation created.

---

## 1. 摘要 / Summary

| 项 / Item | 清理前 / Before | 清理后 / After |
|---|---|---|
| 可见自动化（`deleted_at IS NULL`）/ live automations | 4 | 4 |
| 其中 ACTIVE | 4 | 3 |
| 其中 PAUSED | 0 | 1 |
| 软删除历史行（惰性、不参与调度）/ soft-deleted rows | 25 | 25 |
| 正式采集调度器数量 / canonical Inventory schedulers | 1 | 1 |

- **改动总计 = 1 个字段**，覆盖全部 4 个可见自动化；其余 3 个的任务名、正文、rrule、cwd、next_run 逐字段零变化（见第 2 节）。
- Exactly 1 field-level change; every other field byte-identical.
- 未新增、未删除、未重命名任何自动化；软删除行数不变（25 → 25）。
- 历史执行记录全部保留：4 个可见任务累计 295 条 `automation_runs`。

---

## 2. 清理前后任务一览 / Per-task before & after

| ID | Name | Schedule | Before | After | Change |
|---|---|---|---|---|---|
| `automation-1784775229336` | RoktRazo BD Inventory — 4x/day (6h interval) Asia/Shangh | FREQ=HOURLY;INTERVAL=6 | ACTIVE | ACTIVE | unchanged |
| `automation-1786002601925` | BD Result Recovery Sync — 08:45 Asia/Shanghai | FREQ=DAILY;BYHOUR=8;BYMINUTE=45 | ACTIVE | ACTIVE | unchanged |
| `75fbacd1-fa43-46ea-8388-1d47647c3f4d` | BD SAFE40 Milestone Checkpoint — 4x/day (6h interval) As | FREQ=HOURLY;INTERVAL=6 | ACTIVE | ACTIVE | unchanged |
| `488f4c21-a70b-4611-a388-9a3f61c02db9` | BD checkpoint phase fix (one-off, 07:38) — restore +40 m | once @ 2026-09-28T07:38 | ACTIVE | PAUSED | **CHANGED** |

字段级变更明细 / Field-level diff (full):

| ID | Field | Before | After |
|---|---|---|---|
| `488f4c21-a70b-4611-a388-9a3f61c02db9` | status | ACTIVE | PAUSED |

---

## 3. SAFE40 Checkpoint 冗余验证 / Redundancy verification (5 conditions)

自动化 `75fbacd1-fa43-46ea-8388-1d47647c3f4d`（`BD SAFE40 Milestone Checkpoint — 4x/day (6h interval)`）是本次唯一待暂停候选，逐项验证：

| # | 条件 / Condition | 证据 / Evidence | 结论 / Verdict |
|---|---|---|---|
| 1 | 历史 SAFE40 只读检查任务 | 正文标注 `PHASE 4A.5J ... STRICTLY READ-ONLY`；仅执行 `_4a5g_checkpoint.py`（sqlite `mode=ro`）；SAFE40 里程碑 2026-10-09 首达、验收已完结 | PASS |
| 2 | 不负责正式客户采集 | 正文 FORBIDDEN 明确禁止启动 `bd_orchestrator.py` / 手动 Inventory / 手动累积；91 次历史运行均无采集行为 | PASS |
| 3 | 不负责回复 / 退订 / 退信 | 该职责属 `automation-1786002601925`（`result_recovery_sync.py`：tracking / bounce / reply / unsubscribe 扫描，73 次运行）；checkpoint 正文禁止 SMTP 与任何邮件动作 | PASS |
| 4 | 不负责唯一生产恢复流程 | 生产恢复 / 结果回流唯一入口为 `automation-1786002601925`（每日 08:45）；checkpoint 从不写业务库 | PASS |
| 5 | 不承担其他保留任务无法替代的关键告警或 SAFE 统计职责 | **不成立** — 见下 | **FAIL** |

### 条件 5 的实测证据 / Evidence for condition 5 (why it was NOT paused)

1. **SAFE 数值本身可替代，告警面不可替代。** 每轮 SAFE 已由 Inventory 写入 `job_runs.actual`；但 checkpoint 额外提供**跨轮差分 + MX 通道健康门控 + 调度静默检测**，保留任务中无一项覆盖：
   - **2026-10-19 17:25**：MX 权威通道故障（Worker `401`、12/12 域名 `dns_error`、`mx_cache` 全部超龄）致 SAFE 假性下跌 **56 → 17**。checkpoint 判 FAIL-CLOSED，并用 `LEADS_TOTAL=1213 / EMAIL_POOL=652 / BROAD_READY=95` 未变证明「测量欠测、数据无丢失」。Inventory 自身无法区分「SAFE 真下跌」与「MX 通道故障」。
   - **2026-10-20 09:41**：检出 **01:52 / 07:52 两次 Inventory 触发未登记**，且当日 `run_lock` 键完全缺失（= orchestrator 从未启动），指向宿主机夜间离线。本次只读核查独立复核：`job_runs` 中 `business_date=2026-10-20` 仅 **1** 轮运行，与 checkpoint 判断一致。
   - 结论：Inventory 只能报告「自己跑过的那一轮」，**无法报告自己的缺席**；而该告警 48 小时内已真实命中两次。

**因此按任务书 fail-safe 条款保持 ACTIVE（KEEP），未做任何修改。这是有证据的主动不动，不是遗漏。**
> Kept ACTIVE per the fail-safe clause: it is the only retained task that detects missed Inventory firings and MX-induced SAFE undervaluation. Deliberate no-op, not an omission.

### 后续若仍要降载 / If load reduction is still wanted (each needs separate authorization)

1. **降频不暂停**：`FREQ=HOURLY;INTERVAL=6` → `INTERVAL=12`（4x → 2x/日），保留告警能力；
2. **职责迁移后再停**：把「Inventory 静默检测 + MX 通道探针」并入 `automation-1786002601925`（每日 08:45）；迁移前暂停会留下约 22 小时告警盲区；
3. **维持现状**（本次实际选择）。

---

## 4. 保留任务的理由 / Why the retained tasks stay

| ID | 保留理由 / Reason |
|---|---|
| `automation-1784775229336` | 唯一正式采集调度器：`FREQ=HOURLY;INTERVAL=6`，anchor :58 Asia/Shanghai。三页预算 `WORKBUDDY_DISCOVERY_MAX_PAGES=3` 与正文完整保留（prompt SHA-256 前缀 `7d4e7e7ceaa8d5e9` 前后一致）。未创建第二实例，未改频率。 |
| `automation-1786002601925` | 结果恢复 / 回流唯一入口（每日 08:45 Asia/Shanghai）：tracking 同步 + bounce / reply / unsubscribe 扫描并写 `system_config`；恢复检查点与历史日志未删除。 |
| `75fbacd1-fa43-46ea-8388-1d47647c3f4d` | 见第 3 节：唯一保留的跨轮 SAFE 差分 + MX 通道 + 调度静默告警面（fail-safe 保留）。 |
| `488f4c21-a70b-4611-a388-9a3f61c02db9` | 一次性任务（`2026-09-28 07:38`），已执行 1 次、无下次运行。本次把状态由 `ACTIVE` 归一为 `PAUSED` 以匹配要求的 DISABLED/PAUSED 终态：未重新启用、未再次执行、未删除，`next_run_at` 保持为空。 |

---

## 5. Inventory 最近一次运行状态 / Latest Inventory run

| 字段 / Field | 值 / Value |
|---|---|
| run_id | `inventory:2026-10-20:388f1d48` |
| 状态 / status | `completed` · stop_reason = `target_met` |
| 时间窗 / window | 2026-10-20 01:45:47 → 2026-10-20 01:51:53（UTC naive 落库） |
| target / actual SAFE | 50 / 56 |
| 运行中 / running now | 0 个（本次作业前 `running=0`，未打断任何运行） |
| 运行锁 / run lock | `released` |
| 近 24h Provider 请求 / provider audit | 0 次（发现轴已耗尽，结构性 0） |
| DB 完整性 / quick_check | `ok` |

本任务未执行任何 Inventory、未触发采集、未部署或回滚代码。

---

## 6. 重复调度核查 / Duplicate-scheduling audit

| 面 / Surface | 发现 / Finding |
|---|---|
| WorkBuddy 自动化 | 采集型调度器 = **1**。同频（`FREQ=HOURLY;INTERVAL=6`）的仅 Inventory 与只读 checkpoint，且相位错开：checkpoint 下次 15:45:38 vs Inventory 下次 15:58:05（相差 12.5 分钟，无重叠、无补跑簇） |
| 软删除但状态位仍为 ACTIVE 的行 | 9 行（`deleted_at` 非空）。逐行核对 `automation_runtime_state.last_run_at` 全部 ≤ `deleted_at`，**删除后 0 次运行** → 不参与调度（若计数不排除 `deleted_at` 会虚增为 12） |
| Windows 计划任务（共 213 个，BD 相关 3 个） | `RoktRazo-BD-PreSend` **Disabled**、`RoktRazo-BD-Outreach` **Disabled**、`RoktRazo-BD-PostSend` **Ready**（每日 00:10）。**无任何 Inventory 计划任务** → 不存在第二套采集调度 |
| Windows PostSend 是否会产生客户发送 | 代码核查 `bd_orchestrator.py:288-321` `stage_post_send`：仅 IMAP 收件箱增量扫描 + 发送结果对账 + dashboard 生成，**无 SMTP / send_one 路径** → 不产生客户发送；保持原状态未改 |
| Codex 自主工程调度 | Windows 计划任务无 Codex 项；WorkBuddy 自动化无 Codex 任务；无 cron 类调度。本次仅改 1 个 WorkBuddy 自动化状态位，Codex 开发总控与部署通道配置（`deploy-channel\releases\channel_config.json`）零改动 |

---

## 7. 业务数据与发信影响 / Business data & sending impact

- **业务数据 / Business data**：`BUSINESS_DATA_MODIFIED = false`。所有生产查询以 `file:...?mode=ro` 打开；`PRAGMA quick_check = ok`；本任务 0 条 INSERT / UPDATE / DELETE 业务行。
- **发信 / Sending**：`EMAILS_SENT_BY_CLEANUP = 0`。`SMTP_enabled = 0`；`send_log` 末次发送 `2026-09-16T01:09:52.031266+08:00`（清理前既有）；`pending` 授权 43 条但**可执行 0**；PreSend / Preflight / Outreach 保持软删除 + PAUSED，未重新激活。
- **门禁 / Gates**：SAFE、MX、历史去重、发送门禁、`WORKBUDDY_DISCOVERY_MAX_PAGES=3`、调度间隔、锁语义均未改动。

---

## 8. 执行后验收 / Post-change acceptance

| # | 检查项 / Check | 结果 / Result | 证据 / Evidence |
|---|---|---|---|
| 1 | Inventory = ACTIVE | PASS | `automation-1784775229336` → `ACTIVE`，rrule `FREQ=HOURLY;INTERVAL=6` |
| 2 | Recovery Sync = ACTIVE | PASS | `automation-1786002601925` → `ACTIVE`，rrule `FREQ=DAILY;BYHOUR=8;BYMINUTE=45` |
| 3 | SAFE40 Checkpoint = PAUSED（若冗余验证通过） | **NOT APPLIED** | 第 5 项冗余条件 FAIL → 按 fail-safe 保持 `ACTIVE`（第 3 节） |
| 4 | One-off phase fix = DISABLED/PAUSED | PASS | `488f4c21-a70b-4611-a388-9a3f61c02db9` → `PAUSED`，`next_run_at` 空，历史记录保留 |
| 5 | ACTIVE 正式 Inventory 数量 = 1 | PASS | `active_inventory_count = 1` |
| 6 | Inventory 原频率与页面预算不变 | PASS | rrule 未变；prompt SHA-256 前缀 `7d4e7e7ceaa8d5e9` 前后一致（含三页预算） |
| 7 | 未误启动 PreSend / Preflight / Outreach | PASS | 三者仍在软删除集合且 PAUSED，无 `next_run_at` |
| 8 | 无新增 / 删除 / 意外修改其他任务 | PASS | 字段级差异仅 1 条（第 2 节）；可见任务 4 → 4；软删除 25 → 25 |
| 9 | Codex 开发总控不受影响 | PASS | 未改 Codex 相关调度 / 部署通道；仅 1 个 WorkBuddy 自动化状态位变更 |

---

## 9. 环境提示 / Environment advisory (本任务未做磁盘变更)

执行期间 `C:` 卷一度 **0 字节可用（占用 100%）**，导致两次写入失败（`os error 112`，报告生成与推送曾中断）。已定位最大占用者：`.workbuddy\logs` 下应用日志（`network-failover.jsonl` 327MB + 两个日期归档 234MB / 158MB）。随后宿主侧日志轮转自行释放约 2.3GB，报告得以完成。已尝试的日志清理操作被回收站通道拒绝并 fail-closed 放弃，**本任务实际未删除任何文件**。

风险：低余量下生产 SQLite 写入可能 `disk I/O error`，会影响 15:58 的 Inventory 节拍。**建议在下次生产节拍前清理磁盘**；个人目录清理需单独授权。

---

## 10. 结果字段 / Result fields

```
INVENTORY_ACTIVE = true
RECOVERY_SYNC_ACTIVE = true
SAFE40_CHECKPOINT_PAUSED = false
ONE_OFF_TASK_DISABLED = true
DUPLICATE_INVENTORY = false
SEND_TASKS_PAUSED = true
UNEXPECTED_CHANGES = false
BUSINESS_DATA_MODIFIED = false
EMAILS_SENT_BY_CLEANUP = 0
RESULT = PARTIAL_CLEANUP_APPLIED_SAFE40_CHECKPOINT_RETAINED_FAIL_SAFE
COMMIT_SHA = a3d5cf231f33af9fa552c9fe5c3dfc895ee38eb4
PUSH_SUCCESS = true
```

**说明 / Note**: `SAFE40_CHECKPOINT_PAUSED = false` 是**经验证的 fail-safe 决定**，非遗漏——该任务是 48 小时内两次真实事件（MX 通道故障致 SAFE 假性下跌、Inventory 调度静默）的唯一检出方；暂停会移除唯一告警面。降载替代方案见第 3 节，需单独授权。
