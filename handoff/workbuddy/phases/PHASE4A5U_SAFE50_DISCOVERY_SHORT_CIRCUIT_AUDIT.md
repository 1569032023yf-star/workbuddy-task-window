# PHASE 4A.5U — SAFE50 后持续发现阻塞诊断 / SAFE50 DISCOVERY SHORT-CIRCUIT AUDIT

- PHASE = 4A.5U
- 生成时间 = 2026-10-13T18:00:20+08:00（Asia/Shanghai，动态取时）
- 模式 = STRICTLY READ-ONLY。无生产业务代码改动、无生产数据库直接写入、无自动化改动、无新自动化、无邮件发送、无手动 Inventory 运行。本阶段唯一写入的是 handoff 文本文件。
- RESULT = **SAFE50_EARLY_EXIT_CONFIRMED**

---

## 1. 结论（一句话）

**SAFE50 提前退出已在生产中被真实触发并确认。** 生产 `bd_orchestrator.py` 的 `stage_inventory()` 在测量 SAFE 之后、执行任何发现工作之前，存在一道 `if safe >= target: ... return True` 门；SAFE 于 2026-10-13 00:45:23 +08 达到 50（工作日目标）后，随后 2 次计划运行全部在这道门提前结束（`stop_reason=target_met`，0 次 provider 请求，0 个新地点，0 条新 lead，0 个新第一方邮箱，查询族与 cursor 冻结在 13/20）。这不是情况 B/C/D——是情况 A。

## 2. 生产代码路径核实（任务第三节）

| 项 | 值 |
|---|---|
| 真实运行加载的文件 | `C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\bd_orchestrator.py`（canonical Inventory 自动化 cwd 即该目录） |
| 文件 SHA-256 | `7afc4d7f6ac18e22bba7cc6a9ea2250dc6d6bafe92128c00c08252731bb2e969` |
| handoff 仓库快照内同名文件 SHA-256 | `fb2b18f19c7cef8d56b3828bed554d199d6ce8de480a990ac97ee4b3b5f4c739`（`5bf9df9f` 提交；该 blob 最后修改于 `da36acf`，即 P2.3I 时代——**快照漂移为既有状态，非本阶段造成**；`discovery/discovery_service.py` 同理：生产 `96dcc751…0169ae14` vs 快照 `2bba7955…`） |
| wrapper `run_inventory_canary3.py` | 存在于生产树（SHA-256 `97183deefa6f18e6a5bf555153019dfd03fa683d0934b9ae4f7da4853d74c59d`，30 行）。自动化 prompt 直接调用 `python bd_orchestrator.py --stage inventory --live` 并先 `export WORKBUDDY_DISCOVERY_MAX_PAGES=3`；4A.5T 亦实测到执行体曾以 wrapper 入口运行（pid 47328）。**wrapper 是透明 env 守卫**：断言 knob==3 后 `runpy` 以相同 argv 委托 orchestrator，失败 exit 9——**不改变调用路径**，`stage_inventory` 代码路径唯一 |
| `inventory_target_for_date()` 真实目标 | `outreach_control.py`：`INVENTORY_TARGET = NEW_OUTREACH_TARGET(40) + 10 = 50`；`SAFE_INVENTORY_TARGET` 在 `.env` 与进程 env 中**均未设置**（`env_loader` 用 setdefault，进程 env 优先）→ 工作日 **50**，周末 `max(60, 50) = 60`。2026-10-13（周二）→ **50**，与 `job_runs.target=50` 实测一致 |
| 进入 `stage_inventory` 时的 SAFE | 两轮 post-SAFE50 运行进入时 SAFE=50（证据链见第 4 节） |
| 实际进入的分支 | `bd_orchestrator.py:429-431` 的 `if safe >= target:` 提前退出分支（`finish_job_run(..., 'completed', stop_reason='target_met')` + `return True`） |
| 是否执行 `run_places_batch` | **否**。该调用在 `:442`，位于提前退出之后 |
| 是否运行官网解析 / staging / backlog | **否**（分别在 `:445` / `:449` / `:455`，均在门后） |
| 是否推进城市查询族与 cursor | **否**。Cooperstown 仍 13/20，7 个 pending 族 `pages_processed=0`；`activate_next_city`（`:436`）与 `complete_active_city_if_exhausted`（`:435`/`:461`）均在门后，未执行 |

代码位置（生产工作区文件，行号为当前实测）：

```python
425            safe = _count_safe_ready_pool(conn)          # SAFE 测量（V2+MX，~80-150s）
...
429            if safe >= target:
430                finish_job_run(run_id, 'completed', actual=safe, gap=0, stop_reason='target_met')
431                return True                              # ← 发现尚未开始即结束
432            with conn:
433                seed_default_queue(conn)
434                service = DiscoveryService(conn)
435                complete_active_city_if_exhausted(...)
436                city = activate_next_city(...)
...
442                discovered = service.run_places_batch(city, max_pages=...)   # ← 永远到不了
```

`target` 在 `:395` 由 `inventory_target_for_date(business_date)` 计算；全文件仅此一处提前退出门（`discovery_service.py` 内无其它 target 门）。

## 3. 运行记录：SAFE50 时刻的界定

SAFE 在 run `inventory:2026-10-12:a9943807`（2026-10-13 00:36:23 → 00:45:23 +08）内由 47 升至 50：该轮 SAFE_BEFORE=47（上一轮 `ad20b2b1` 的 actual），执行了 3 次 provider 请求（`teacher supply store`，全部 ok，每页 20 条原始结果），结束时 SAFE_AFTER=50、`completed/target_met`。**该轮属于情况 B**（先发现后达标，不是提前退出）。

**SAFE50 时刻 = 2026-10-13 00:45:23 +08（= 2026-10-12 16:45:23 UTC）**，此后为 post-SAFE50 窗口。

## 4. Post-SAFE50 逐轮报告（任务第四节）

窗口切分用单一 `CHANGE_POINT_UTC = 2026-10-12T16:45:23`；`job_runs.started_at` 为 UTC 朴素时间，`provider_request_audit.requested_at` / `lead_discovery_results.discovered_at` 为 ISO `+00:00`，`leads.collected_at` 为本地 (+08) 朴素且用字面 `T` 分隔符（窗口比较前已 `replace(collected_at,' ','T')` 归一化——分隔符陷阱本轮再次规避）。

| 字段 | Run 1 | Run 2 |
|---|---|---|
| RUN_ID | `inventory:2026-10-13:891b3a43` | `inventory:2026-10-13:25df11b6` |
| STARTED_AT | 2026-10-12 22:53:53 UTC = 2026-10-13 06:53:53 +08 | 2026-10-13 05:04:24 UTC = 2026-10-13 13:04:24 +08（计划档 13:01:07） |
| FINISHED_AT | 2026-10-12 22:55:45 UTC = 06:55:45 +08 | 2026-10-13 05:06:05 UTC = 13:06:05 +08 |
| RUN_STATUS | completed | completed |
| STOP_REASON | target_met | target_met |
| TARGET | 50 | 50 |
| SAFE_BEFORE | 50（上一轮 post 测量；无其他写入方，见下） | 50（同上） |
| SAFE_AFTER | 50 | 50 |
| PROVIDER_PAGES | 0 | 0 |
| PROVIDER_REQUESTS | 0 | 0 |
| NEW_UNIQUE_PLACES | 0 | 0 |
| NEW_LEADS | 0 | 0 |
| NEW_FIRST_PARTY_EMAILS | 0 | 0 |
| ACTIVE_CITY | Cooperstown, NY（未激活/未收尾调用） | Cooperstown, NY（同上） |
| QUERY_FAMILY_PROGRESS | 13/20（未动） | 13/20（未动） |
| 运行时长 | 1m52s | 1m41s |

SAFE_BEFORE=50 的依据（非猜测）：(a) 上一轮 post 测量 actual=50；(b) 发送冻结下无任何其他组件写 `leads`（`SEND_LOG` 自 2026-09-16 起为 0，无手动运行，`MANUAL_INVENTORY_RUNS=0`）；(c) 提前退出分支以 `:425` 的门前测量值直接记 `actual`；(d) 时长签名佐证——发现轮 6-9 分钟，而这两轮仅 ~1.7-2.0 分钟，与本阶段实测的单纯 SAFE 测量耗时（142.3s）量级一致；(e) 只读 checkpoint 快照（14:50:27 +08）独立记录两轮 `pages=0, requests=0, families=null`，而达标轮 `pages=3, requests=3, families="teacher supply store"`。

窗口内 DB 实测（自 `2026-10-12T16:45:23Z` 起）：
- `provider_request_audit`：**COUNT=0**（对比：达标轮窗口内有 3 行，16:39:36 UTC）
- `lead_discovery_results`：**COUNT=0**（最后一条 discovered_at = 2026-10-12T16:39:36.749889+00:00）
- `leads`（`collected_at >= 2026-10-13T00:45:23` 本地）：**COUNT=0**；NEW_FIRST_PARTY_EMAILS=0（最后一条 lead collected_at = 2026-10-13T00:41:36，属达标轮）
- SAFE 全程保持 50（见第 5 节）

**分类结论：两轮均为情况 A（真正的 SAFE50 提前退出）**——SAFE_BEFORE >= TARGET，`target_met` 发生在发现之前，无 provider 请求，查询族与 cursor 不变。达标轮 `a9943807` 为情况 B（不算提前退出）。**不属于情况 C**（provider 有执行但无新增）也**不属于情况 D**（环境错误，见第 5 节探针）。

## 5. SAFE 测量环境（任务第五节）

- 测量脚本先手写解析生产 `.env` 注入 `os.environ`（24 个变量），**之后**才 import 业务模块；`BD_MX_HTTPS_PROXY = http://127.0.0.1:3213` 已生效（`.env` 第 50 行）。
- 控制探针：`preflight_gate.query_mx('gmail.com')` = **ok**（1.3s）。
- 权威测量：`campaign_eligible_v2.select_candidates_for_plan_v2`（frozen V2 + live MX + 历史/抑制/组织去重）→ `V2_ELIGIBLE_CANDIDATE_ROWS = 50`，`READ_ONLY_V2_SAFE_UNIQUE_ORGS = 50`（142.3s，测量时点 2026-10-13 约 17:57 +08）。
- `SAFE_RECOMPUTATION_STATUS = VALID`。与 4A.5T 历史基线（50 @ 09:43:29 +08）及 checkpoint 快照（50 @ 14:50:27 +08）三方一致；**未出现虚假下降，不构成情况 D**。

## 6. 城市推进验证（任务第六节）

- `ACTIVE_CITY = Cooperstown, NY`（`retail_city_queue` id=22，status=active，provider=browser_maps）；下一城市 `Lake Placid, NY`（id=23，pending）。
- 查询族：**13/20 completed**（7 个 pending：children's store / family game store / visitor center gift shop / tourist gift shop / specialty retailer / puzzle store / card game store；均 `pages_processed=0`，cursor 未推进）。与 4A.5T（13/20）完全一致——SAFE50 后零推进。
- 新增 Provider 页面（窗口内）= 0；新发现独立地点 = 0。
- 未终态官网解析记录：`website_lookup_pending` ×1（id=571 Museum Store）+ `review_recovery` ×4（id=556/565/578/588）——与 4A.5T 记录的存量完全一致，未增加、未清空。`manual_review_needed` ×16（评审池，非收尾阻塞项）。
- `city_completion_checks(Cooperstown, browser_maps)` 只读实算：**9 项全 false**（`all_query_families` / `all_sources_or_reasons` / `pagination_complete` / `two_empty_pages` / `all_candidates_classified` / `no_unprocessed_candidates` / `official_site_recheck` / `review_recovery` / `last_three_batches_empty`）。城市远未到收尾点，**未出现新的城市死锁**；按规则（只有 20/20 后仍被阻塞才升级），本阶段**不升级**为工程缺陷，未做任何手动清空或终态化。

## 7. 自动化安全检查（任务第七节）

- 唯一 Inventory 自动化 `automation-1784775229336`：**ACTIVE**，`rrule=FREQ=HOURLY;INTERVAL=6`，cwd=生产目录，`next_run_at = 2026-10-13 19:10:57 +08`；prompt 内 `export WORKBUDDY_DISCOVERY_MAX_PAGES=3` 完整保留。**`WORKBUDDY_DISCOVERY_MAX_PAGES = 3` 保持原样。**
- 唯一性：全库扫描（name+prompt 含 inventory/orchestrator）仅此一个非删除态 Inventory 权威；其余 inventory 类自动化（Outreach/Pre-Send/Post-Send/Weekend Inventory 等）均为 PAUSED 且 `deleted_at` 非空。`DUPLICATE_INVENTORY = false`。
- 并发/锁：今日仅 1 次 inventory run（13:04 +08），无 running 中作业；`run_lock:daily_outreach:inventory:2026-10-13 = released`（10-12 亦 released）；无 lock_conflict。
- Checkpoint `75fbacd1`：ACTIVE 只读，其 4A.5S 版 prompt 明确授权持续发现并禁止暂停任何自动化——**本次发现停止与 checkpoint 无关**（停止发生在 orchestrator 代码门，而非控制面）。
- 间隔漂移：实测 (+08) 00:36:23 → 06:53:53 → 13:04:24，间隔 6h17m30s / 6h10m31s； scheduler 每轮重锚（`next_run_at = 写回时刻 + 6h`），相位漂移持续存在但为既有已知行为。**本阶段未改 cadence、锚点、页面预算或自动化状态。**
- 计划任务（Windows）：4A.5T 已核实无 Inventory 计划任务；本阶段未改动任何计划任务（只读诊断范围内无需重验，状态沿用 4A.5T 结论）。

## 8. 发送冻结验证（任务第八节）

| 检查项 | 实测值 | 结论 |
|---|---|---|
| SMTP_ENABLED | `system_config.SMTP_enabled = 0` | 保持 |
| SMTP_CONNECTIONS | 0（无发送路径活动；SEND_LOG 今日 0、无计划任务触发） | 保持 |
| SEND_LOG_TODAY | 0（2026-10-13 本地日；自 2026-10-13 亦为 0） | 保持 |
| MATERIALIZED_FSP_PLANNED | 0（final_send_plan 无 planned 行） | 保持 |
| LIVE_SEND_AUTHORIZATIONS | 0（send_authorizations 仅 consumed/revoked/superseded；43 条 pending 条目全部挂在已 revoked 的父授权下，属历史残留） | 保持 |
| PRESEND | `automation-1785804406748` PAUSED | 保持 |
| PREFLIGHT | `automation-1785804413719` PAUSED | 保持 |
| OUTREACH | `automation-1785804421539` PAUSED | 保持 |
| 末次实际发送 | 2026-09-16T01:09:52.031266+08:00（SEND_LOG_TOTAL=517 未变） | 保持 |

未创建或测试任何真实发送计划。第一批 40 个客户完整保留（`BATCH_1_HOLD_FOR_FUTURE_OUTREACH`）。

## 9. 交给 Codex 的最小修复需求（本阶段不热改）

**确认 SAFE50 提前退出的准确信息：**

- 生产源文件：`roktandrazo-outreach/bd_orchestrator.py`（生产运行树，SHA-256 `7afc4d7f6ac18e22bba7cc6a9ea2250dc6d6bafe92128c00c08252731bb2e969`）
- 分支路径：生产运行树即权威（handoff repo `1569032023yf-star/workbuddy-task-window@main` 内同名 blob 为陈旧快照 `fb2b18f1…`，勿以它为修改基准）
- 代码位置：`stage_inventory()` 第 429-431 行
- 触发条件：进入时 `safe(50) >= target(50)`；target 由 `inventory_target_for_date()` 给出（工作日 50 / 周末 60；`SAFE_INVENTORY_TARGET` 未配置时取默认）
- 日志证据：`job_runs` 两轮 `completed/target_met`（06:53:53、13:04:24 +08）+ `provider_request_audit` 窗口内 0 行 + 时长签名（~2min vs 发现轮 6-9min）+ 查询族/cursor 冻结

**最小修复方向（二选一，由 owner 与 Codex 决定）：**

1. **删除/中性化提前退出门**：`stage_inventory` 始终执行发现链路（seed queue → complete/activate city → `run_places_batch` → 官网解析 → staging → linked backlog → 收尾检查），`target` 仅保留用于结束时的 gap/status 报告（现有 `:464-466` 逻辑）；或
2. **显式硬顶门控**：仅当运营者显式配置了硬顶（如 `SAFE_INVENTORY_TARGET` 作为 cap 且另有显式开启标志）时才允许提前退出，默认无顶。

**必须保持不变的**：run lock、城市队列与 cursor 语义、V2/MX 门控、官网解析/staging/backlog 通道、发送冻结、无第二调度器。**修改属生产代码变更，需 owner 授权 + Codex 实施 + 部署验证；本阶段只读，未动一行代码。**

与 4A.5S 的区别（重要）：4A.5S 的停止规则在**自动化控制面**（checkpoint prompt），已通过改 prompt 修复；本规则在**生产代码**里，控制面修不掉，必须 Codex 改代码。

## 10. 最终 KEY=VALUE 摘要

```text
PHASE = 4A.5U
PRODUCTION_INVENTORY_CODE_SHA256 = 7afc4d7f6ac18e22bba7cc6a9ea2250dc6d6bafe92128c00c08252731bb2e969
  (file: roktandrazo-outreach/bd_orchestrator.py, production runtime tree;
   handoff-repo snapshot blob fb2b18f19c7cef8d56b3828bed554d199d6ce8de480a990ac97ee4b3b5f4c739 is stale, pre-existing)
SAFE_LAST_VALID = 50 (this phase's own recompute, control probe ok, SAFE_RECOMPUTATION_STATUS = VALID)
TARGET_FOR_OBSERVED_RUNS = 50 (weekday; weekend 60; SAFE_INVENTORY_TARGET unset)
POST_SAFE50_SCHEDULED_RUNS = 2
POST_SAFE50_PROVIDER_REQUESTS = 0
POST_SAFE50_NEW_LEADS = 0
POST_SAFE50_NEW_FIRST_PARTY_EMAILS = 0
POST_SAFE50_NEW_SAFE_ORGS = 0
TARGET_MET_EARLY_EXIT_OBSERVED = true
SAFE50_DISCOVERY_SHORT_CIRCUIT_CONFIRMED = true
DISCOVERY_CONTINUES_ABOVE_50 = false
ACTIVE_CITY = Cooperstown, NY (13/20 query families, unchanged; next = Lake Placid, NY)
INVENTORY_ACTIVE = true
DUPLICATE_INVENTORY = false
PRODUCTION_CODE_CHANGED = false
DIRECT_DB_WRITES_BY_THIS_TASK = 0
MANUAL_INVENTORY_RUNS = 0
SMTP_CONNECTIONS = 0
EMAILS_SENT = 0
COMMIT_SHA = (见 CHANGELOG / LATEST_RESULT 元数据 fixup)
PUSH_SUCCESS = (见 CHANGELOG / LATEST_RESULT 元数据 fixup)
RESULT = SAFE50_EARLY_EXIT_CONFIRMED
```

STOP.
