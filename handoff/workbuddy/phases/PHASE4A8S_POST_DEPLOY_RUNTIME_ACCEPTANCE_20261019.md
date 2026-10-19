# PHASE 4A.8S 部署后运行验收（第二次只读，延长窗口）/ Post-Deployment Runtime Acceptance (2nd read-only pass, extended window)

- 验收请求 / Acceptance request: `handoff/phases/WORKBUDDY_READONLY_ACCEPTANCE_REQUEST_20261016.md`
  (repo `1569032023yf-star/roktandrazo-outreach-codex`, branch `codex/engineering-deployment-charter`)
- 验收窗口 / Acceptance window: 2026-10-15T15:41:00+08:00 → 采样时间 / sampling time 2026-10-19T10:23:03+08:00 (Asia/Shanghai, +08)
- 发布操作 / Release operation: `op-20261015-104202-5ecde6` (apply, 14/14 gates, caller=bridge, test_mode=false),
  finished 2026-10-15T10:42:04+08:00；生产 SHA `e7e619d3…`
- 与上一份报告的关系 / Relation to the earlier pass: 首份（`PHASE4A8S_POST_DEPLOY_RUNTIME_ACCEPTANCE_20261016`）采样于
  2026-10-16T18:29+08。本份以同一请求、同一窗口起点重跑，采样点延长至 2026-10-19T10:23:03+08:00，覆盖其后 10 个新增 6h 节拍。
  The earlier pass sampled on 2026-10-16T18:29+08; this pass re-runs the same request with the same window start and covers
  the subsequent ten 6-hour cycles.
- 执行性质 / Nature: read-only only. 未手动触发 Inventory、未 apply/rollback、未写业务数据、未发送邮件。
- 报告生成 / Generated: 2026-10-19T10:35:00+08:00

## 1. 运行事实与调度关联 / Run facts and scheduler linkage

窗口内唯一 Inventory 调度器 `automation-1784775229336`（ACTIVE，`FREQ=HOURLY;INTERVAL=6`，下次运行 2026-10-19T13:18:31+08:00，
执行 `python bd_orchestrator.py --stage inventory --live`）共执行 **15 次**计划运行：7 次
`completed/target_met` + 8 次 `partial/safe_inventory_gap`，**0 次 failed**。
两种终态均为设计内正常态（周末 target=60 而供给 56 → gap 4）。Both terminal states are healthy by design.

| run_id | business_date | 开始 +08 | 结束 +08 | 状态 | target | 出口 SAFE | gap | Provider 页 | 新增组织 |
|---|---|---|---|---|---|---|---|---|---|
| `inventory:2026-10-15:76940963` | 2026-10-15 | 2026-10-15 15:43:26 +08 (UTC 2026-10-15 07:43:26) | 2026-10-15 15:52:56 +08 | completed | 50 | 52 | 0 | 3 | 2 |
| `inventory:2026-10-15:69235b78` | 2026-10-15 | 2026-10-15 21:59:50 +08 (UTC 2026-10-15 13:59:50) | 2026-10-15 22:08:38 +08 | completed | 50 | 52 | 0 | 2 | 0 |
| `inventory:2026-10-16:fbcc7295` | 2026-10-16 | 2026-10-16 04:11:39 +08 (UTC 2026-10-15 20:11:39) | 2026-10-16 04:21:05 +08 | completed | 50 | 54 | 0 | 3 | 4 |
| `inventory:2026-10-16:cdf0ebd2` | 2026-10-16 | 2026-10-16 10:36:42 +08 (UTC 2026-10-16 02:36:42) | 2026-10-16 10:43:39 +08 | completed | 50 | 54 | 0 | 2 | 0 |
| `inventory:2026-10-16:b76e3cab` | 2026-10-16 | 2026-10-16 16:55:05 +08 (UTC 2026-10-16 08:55:05) | 2026-10-16 17:03:43 +08 | completed | 50 | 56 | 0 | 3 | 2 |
| `inventory:2026-10-16:36ad0975` | 2026-10-16 | 2026-10-16 23:12:20 +08 (UTC 2026-10-16 15:12:20) | 2026-10-16 23:19:36 +08 | completed | 50 | 56 | 0 | 2 | 0 |
| `inventory:2026-10-17:889fc103` | 2026-10-17 | 2026-10-17 05:27:05 +08 (UTC 2026-10-16 21:27:05) | 2026-10-17 05:33:06 +08 | partial | 60 | 56 | 4 | 2 | 0 |
| `inventory:2026-10-17:faa6e08c` | 2026-10-17 | 2026-10-17 11:42:31 +08 (UTC 2026-10-17 03:42:31) | 2026-10-17 11:48:01 +08 | partial | 60 | 56 | 4 | 0 | 0 |
| `inventory:2026-10-17:ca6b9ae3` | 2026-10-17 | 2026-10-17 17:54:51 +08 (UTC 2026-10-17 09:54:51) | 2026-10-17 17:59:46 +08 | partial | 60 | 56 | 4 | 0 | 0 |
| `inventory:2026-10-17:71d2aaac` | 2026-10-17 | 2026-10-18 00:07:39 +08 (UTC 2026-10-17 16:07:39) | 2026-10-18 00:12:36 +08 | partial | 60 | 56 | 4 | 0 | 0 |
| `inventory:2026-10-18:28ac37fb` | 2026-10-18 | 2026-10-18 06:19:58 +08 (UTC 2026-10-17 22:19:58) | 2026-10-18 06:24:37 +08 | partial | 60 | 56 | 4 | 0 | 0 |
| `inventory:2026-10-18:d3c426b2` | 2026-10-18 | 2026-10-18 12:29:47 +08 (UTC 2026-10-18 04:29:47) | 2026-10-18 12:34:40 +08 | partial | 60 | 56 | 4 | 0 | 0 |
| `inventory:2026-10-18:ad0eb4ba` | 2026-10-18 | 2026-10-18 18:42:30 +08 (UTC 2026-10-18 10:42:30) | 2026-10-18 18:47:05 +08 | partial | 60 | 56 | 4 | 0 | 0 |
| `inventory:2026-10-18:5a37054b` | 2026-10-18 | 2026-10-19 00:54:23 +08 (UTC 2026-10-18 16:54:23) | 2026-10-19 00:59:06 +08 | partial | 60 | 56 | 4 | 0 | 0 |
| `inventory:2026-10-19:00dcf741` | 2026-10-19 | 2026-10-19 07:09:23 +08 (UTC 2026-10-18 23:09:23) | 2026-10-19 07:13:54 +08 | completed | 50 | 56 | 0 | 0 | 0 |

- 原字段时区 / Original field timezones: `job_runs.started_at/finished_at` = UTC naive（表内已 +8h 归一）；
  `provider_request_audit.requested_at` / `lead_discovery_results.discovered_at` = ISO `+00:00`；`leads.collected_at` = +08 naive。
- 节拍 / Cadence: 相邻运行间隔 6.05–6.26 h，与 `INTERVAL=6` 一致，无重复或补跑簇。
- 无重复调度器 / No duplicate scheduler: `automations` 表全量只读扫描——ACTIVE 且未删除的 Inventory 自动化仅 1 个；
  发送类三个自动化均 PAUSED + 已删除；Windows 计划任务面无 Inventory 任务。
  One dormant ACTIVE one-off automation `488f4c21…`（`scheduled_at=2026-09-28T07:38`，`next_run_at=null`，从未触发）
  为历史配置任务，不启动 Inventory，单列不计入调度器重复。

## 2. SAFE≥50 入口证据与 Provider 执行 / Entry SAFE≥50 evidence and Provider execution

入口 SAFE 的**精确值只写自动化 stdout**（`bd_orchestrator.py:425` 计算、:428 打印，未落库）；下表第 2 列为
「出口 SAFE − 本轮新增独立组织」的**推导下界**，第 3 列为实际落库的出口 SAFE（`:471-476` 写入 `job_runs.actual`）。
Exact entry SAFE is log-only; column 2 is a derived lower bound, column 3 is the persisted post-run SAFE.

| run_id | 入口 SAFE（推导下界） | 出口 SAFE（落库） | Provider 页请求 | 查询族数 | 单族最大页数 | 审计 id |
|---|---|---|---|---|---|---|
| `76940963` | 50 | 52 | 3 | 1 | 3 | 263, 264, 265 |
| `69235b78` | 52 | 52 | 2 | 1 | 2 | 266, 267 |
| `fbcc7295` | 50 | 54 | 3 | 1 | 3 | 268, 269, 270 |
| `cdf0ebd2` | 54 | 54 | 2 | 1 | 2 | 271, 272 |
| `b76e3cab` | 54 | 56 | 3 | 1 | 3 | 273, 274, 275 |
| `36ad0975` | 56 | 56 | 2 | 1 | 2 | 276, 277 |
| `889fc103` | 56 | 56 | 2 | 1 | 2 | 278, 279 |
| `faa6e08c` | 56 | 56 | 0 | 0 | 0 | — |
| `ca6b9ae3` | 56 | 56 | 0 | 0 | 0 | — |
| `71d2aaac` | 56 | 56 | 0 | 0 | 0 | — |
| `28ac37fb` | 56 | 56 | 0 | 0 | 0 | — |
| `d3c426b2` | 56 | 56 | 0 | 0 | 0 | — |
| `ad0eb4ba` | 56 | 56 | 0 | 0 | 0 | — |
| `5a37054b` | 56 | 56 | 0 | 0 | 0 | — |
| `00dcf741` | 56 | 56 | 0 | 0 | 0 | — |

- **SAFE≥50 且仍执行 Provider**：7 轮有查询族可推进的运行，入口下界为 50, 52, 50, 54, 54, 56, 56，全部 ≥ 50，
  同时真实发起 **17 次**页面请求（`provider_request_audit` id 263–279，provider `browser_maps`，
  Cooperstown city_id=22），状态全部 `ok`、`error` 全空、`request_count` 合计 17。
- **页预算 / Page budget**：单族单轮最大 **3 页**（≤3，`bd_orchestrator.py:441` `min(3, max(1, WORKBUDDY_DISCOVERY_MAX_PAGES))`）。
- **代码路径 / Deployed code path**：`:429-431`「Inventory sufficiency is an outcome, never permission to skip the bounded discovery path」
  → `:443 DISCOVERY_PATH_EXECUTED=true` 无条件进入；`:448-451` 仅在 Provider 真实报错时 `stopped`。窗口内 0 次触发该分支。
- **后续 8 轮 Provider 请求为 0 的原因 / Why the last 8 runs show zero requests**：`faa6e08c`, `ca6b9ae3`, `71d2aaac`, `28ac37fb`, `d3c426b2`, `ad0eb4ba`, `5a37054b`, `00dcf741`。
  Cooperstown 的 **20/20 查询族已于 2026-10-17 05:30:01 +08 全部 completed**（末族 card game store），
  `page_cursor` 全为空、`completed_at` 齐全、`consecutive_pages_without_new_place=6` ⇒ 发现轴耗尽（结构性），
  不是 4A.8S 修复前的「SAFE 达标即跳过」。这 8 轮运行仍完整执行了 website resolution / staging postprocess / linked backlog
  （`job_runs` 正常 `completed/partial`，无 `discovery_provider_error`）。Exhaustion, not short-circuit.
- **PROVIDER_REQUESTS_EXECUTED = true**（在仍有族的每一轮）

## 3. Cooperstown 推进 / Cooperstown progression

`retail_city_queue.id=22`（Cooperstown, NY；`status=active`；`active_provider=browser_maps`；`pages_processed=54`，
`results_seen=913`，`new_unique_places=77`，`duplicate_places=836`，`provider_errors=0`）。共 20 个查询族。

- 部署完成时（2026-10-15T10:42:04+08）已完成 **13/20**（请求文档的 13/20 与此一致）。
- 上一份报告采样点（2026-10-16T18:29+08）为 18/20；**17/20 的参照点于 2026-10-16 10:39:55 +08 达成**（tourist gift shop 完成）。
- 当前 **20/20 completed，0 pending**，即 13 → 17 → 18 → **20/20**。

窗口内（部署后）完成的 7 个族与其归属运行 / families completed after the release, with run attribution:

| 查询族 / query family | 完成时间 +08 | run_id | 页数 | 新唯一地点 |
|---|---|---|---|---|
| children's store | 2026-10-15 15:46:59 +08 | `inventory:2026-10-15:76940963` | 3 | 5 |
| family game store | 2026-10-15 22:03:29 +08 | `inventory:2026-10-15:69235b78` | 2 | 0 |
| visitor center gift shop | 2026-10-16 04:14:42 +08 | `inventory:2026-10-16:fbcc7295` | 3 | 5 |
| tourist gift shop | 2026-10-16 10:39:55 +08 | `inventory:2026-10-16:cdf0ebd2` | 2 | 0 |
| specialty retailer | 2026-10-16 16:58:44 +08 | `inventory:2026-10-16:b76e3cab` | 3 | 3 |
| puzzle store | 2026-10-16 23:15:57 +08 | `inventory:2026-10-16:36ad0975` | 2 | 0 |
| card game store | 2026-10-17 05:30:01 +08 | `inventory:2026-10-17:889fc103` | 2 | 0 |

- 游标 / Cursors: 全部 20 族 `page_cursor=''` 且 `completed_at` 非空（收敛态）；族级分页计数 2–3，与 `provider_request_audit`
  逐条对应（17 条 = 17 次页请求）。
- **城市为何仍非终态 / Why the city is not terminal yet**：`city_completion_checks` 9 项中 5 项为真，
  4 项为假（all_candidates_classified, no_unprocessed_candidates, official_site_recheck, review_recovery），**全部由同一行**驱动：`lead_discovery_results` 中 1 行
  `validation_status=website_lookup_pending`，`rejection_reason=website_resolution:network_retry:provider_timeout:45028ms`。
  该行属可重试网络超时，不属发布回归（窗口内 `provider_errors=0`、无运行重叠）；结论供 Codex 工程侧判定，
  本次只读不动数据。A single retryable network-timeout staging row keeps four of nine completion checks false.
- 副作用 / Consequence: 该族已耗尽但城市未 `search_matrix_exhausted`，因此下一城市未激活、发现轴停在 Cooperstown，
  SAFE 自 2026-10-16 17:03:43 +08 起稳定在 56。尚未收尾的城市不改变 SAFE 口径。

## 4. 新增独立组织 / leads / 官网第一方邮箱 / New organizations, leads, first-party emails

区间 / Interval: 2026-10-15T15:41:00+08:00 → 2026-10-19T10:23:03+08:00。

| 指标 / metric | 值 / value |
|---|---|
| `lead_discovery_results` 新行 / new discovery rows | 13（distinct `place_id` 13，distinct 域名 10） |
| 新 lead 行数 / new lead rows | 8 |
| **新独立组织 / new independent organizations** | **8** |
| 同一 organization_key 多行 / multi-row orgs | 0 |
| 官网第一方邮箱 / first-party official-site emails | 7（`official_page_visible`） |
| 其中 verified 标记 / verified-on-site flag | 6 |
| 无邮箱 lead / leads without email | 1 |
| 城市分布 / cities | Cooperstown 100% |
| 全部 `manual_review_needed`（无可发送资格） | true |
| 按运行归因 / per-run attribution | 76940963:2, 69235b78:0, fbcc7295:4, cdf0ebd2:0, b76e3cab:2, 36ad0975:0, 889fc103:0 |
| 2026-10-17 05:30 +08 之后新增 / additions after family exhaustion | 0 |

- 去重口径 / Dedup: `leads.organization_key` 去重（新行内 0 重复、无与部署前既有键冲突）；行数从不当作组织数。
- 发现侧分类 / Discovery-row outcomes: 5 `manual_review_needed`(new_candidate)、1 `identity_review`(new_candidate)、
  1 `review_recovery`、1 `existing_lead_linked`(same_identity_empty_email)、4 `website_not_found`、1 `outside_active_city`。
- 第一方证据 / First-party: `email_source_type=official_page_visible`（官网页面可见），`evidence_url`/`evidence_snippet` 留档本地不推送。
- 历史门禁 / History gates: 新行无 `history_blocked`；`send_eligibility` 为空、`auto_sendable` 未置位 ⇒ 未放宽任何资格。

## 5. MX 控制探针与最新 SAFE / MX control probe and latest SAFE

| 项 / item | 值 / value |
|---|---|
| 探针标识 / probe identity | `preflight_gate.query_mx`（既有正式只读探针） |
| 版本 / version | 模块 SHA-256 `2cd286f2…`（41251 B，mtime 2026-09-16 15:15:54） |
| 端点 / endpoint | Worker `/internal/mx-check`（Bearer；端点地址与凭据均不入报告 / endpoint and credentials withheld） |
| 超时 / timeout | 10 s |
| 解析环境 / resolver env | `BD_MX_HTTPS_PROXY` 显式配置，仅本次 HTTPS 请求使用，不继承 `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY`；Worker 失败回退直连 DNS |
| 通过判据 / pass criteria | 正控 gmail.com → `ok` 且 负控无效域 → 非 `ok` |
| 控制结果 / control results | gmail.com → **ok**；无效域 → **nxdomain** |
| 探针时间 / probe time | 2026-10-19T10:23:03+08:00（耗时 20.53 s） |
| 探针结论 / verdict | **PASS** |

- 首次尝试（10:21:37–10:21:39 +08）正控与负控均返回 `dns_error` ⇒ **探针未通过时不读 SAFE**（按验收规则），
  根因为本地转发代理（回环地址）瞬时不可连、且当时所用解释器缺 `dnspython` 致 DNS 回退不可用；
  10:22:52 以生产同构解释器复测即通过（代理 3/3 连通）。已如实保留两次尝试。
  First attempt failed closed (no SAFE read); transient local-proxy outage plus missing `dnspython` in that interpreter;
  re-run with the production-like interpreter passed.
- 通过后按既有完整门禁（V1/V2/MX/历史/退订/抑制不变）以 `mode=ro` 经
  `campaign_eligible_v2.select_candidates_for_plan_v2` 按 distinct `organization_key` 计数：

| 读数 / reading | 采样时间 +08 | 候选行 | 独立组织 |
|---|---|---|---|
| 1 | 2026-10-19T10:23:03+08:00 | 56 | 56 |
| 2 | 2026-10-19T10:27:19+08:00 | 56 | 56 |

**CURRENT_SAFE = 56**（两次独立读取一致 56, 56；库内 leads 总数 1213）。

## 6. 异常、并发、锁与冻结 / Exceptions, concurrency, locks, freeze

| 检查 / check | 结果 / result |
|---|---|
| 运行重叠 / run overlaps | 0 |
| 锁冲突 / 锁未释放 / lock conflicts | 0（5 个业务日锁键均 `released`；最近 2026-10-19 锁 released 于 2026-10-18 23:13:54 UTC） |
| `job_runs` 失败 / job failures in window | 0 |
| Provider 错误 / Provider errors in window | 0（17 条审计记录全 `ok`，error 字段全空） |
| 发现行重复 / duplicate discovery rows | 0（13 行 = 13 distinct place_id） |
| 重复组织 / duplicate organizations | 0（8 lead = 8 org；无多行同 org） |
| 新增 bounce / reply / unmatched DSN | 0 / 0 / 0 |
| 发送（窗口内）/ sends in window | **0**（最后发送 2026-09-16T01:09:52+08:00） |
| 新发送授权 / new send authorizations | 0（pending 条目 43，可执行 **0**） |
| `SMTP_enabled` 配置 / config flag | `0`（自 2026-08-11 未变） |
| PreSend / Preflight / Outreach 自动化 | 均 PAUSED + 已删除 |
| Windows 计划任务 / scheduled tasks | PreSend=Disabled、Outreach=Disabled、PostSend=Ready（仅退信/回复扫描，无发送面）；无 Inventory 任务 |

- 旧残留单列 / Pre-existing residue (separate, not attributable to this release):
  `job_runs` 中 6 行 2026-07 起未完成的 inventory 行（最早
  2026-07-23 02:54:03 UTC），超出 2h 陈旧窗口；窗口内 2h 内未完成行 = 0。
- 本次观测到的唯一写库动作 / Only DB write observed during this session: 10:20:49 +08 由**既有 08:45 Recovery Sync 自动化**写入
  6 个运维键（`sync_0845_*`、`last_bounce_scan_at`、`last_imap_scan_result`、`last_dsn_scan`、`last_reply_scan_at`）；
  与本次验收无关、不涉发现/发送；`send_log`/`leads`/`bounce_log`/`reply_log` 无新增。
- SMTP=0 判定依据 / Basis: `send_log` + 发送授权 + `SMTP_enabled=0` 为只读权威口径；直接 SMTP 遥测不在只读面内（推断值，已标注）。

## 结论 / Verdicts

- **DEPLOYED = CONFIRMED**：生产文件 `bd_orchestrator.py` SHA `e7e619d3e40f415c1894aa3e1087978875c6f26570755254ab535b68e5580903`、31552 B、
  mtime 2026-10-15 10:42:04 +08，与发布清单一致且自部署后未变；通道操作 `op-20261015-104202-5ecde6` 14/14 门禁。
- **PRODUCTION_EFFECTIVENESS_VERIFIED = CONFIRMED**：窗口内 7 轮「仍有查询族」的运行在入口 SAFE 下界 ≥50 时全部真实发起 Provider
  请求（17 次，0 错误，单族 ≤3 页）；Cooperstown 13/20 → **20/20**；SAFE 52 → **56**；
  新增 8 个独立组织 / 8 lead / 7 个官网一方邮箱；并发、锁、Provider 错误为零；发送面冻结保持
  （窗口内 0 发送、0 新授权、可执行授权 0）。
  发现轴于 2026-10-17 05:30 +08 耗尽后 Provider 请求为 0 属结构性结果，不构成「达标即停」。
- **UNKNOWN 项 / UNKNOWN items**: ①每轮入口 SAFE 精确值（仅 stdout，已给出推导下界）；②直接 SMTP 连接数（以 send_log/授权推断为 0）；
  ③首份报告中「10-15 上午缺失节拍槽」的归因仍未改变（本窗口不含该槽位）。

## 边界（本次未做）/ Boundaries (not performed by this task)

`BUSINESS_CODE_DEPLOYED_BY_THIS_TASK=false`、`PRODUCTION_DB_WRITES_BY_THIS_ACCEPTANCE=0`、`EMAILS_SENT_BY_THIS_TASK=0`、
`INVENTORY_MANUAL_TRIGGER=false`、`ROLLBACK_PERFORMED=false`、`SAFE_MX_HISTORY_GATES_UNCHANGED=true`、
`NO_SECOND_INVENTORY_SCHEDULER=true`、`SECOND_SCHEDULE_CREATED=false`。
生产完整性 / Integrity: DB `quick_check=ok`，WAL 0 字节，主库 mtime 2026-10-19 10:20:49 与上述 Recovery Sync 写入时刻一致。

## 证据来源 / Evidence provenance (no credentials)

生产库 `mode=ro`：`job_runs`、`provider_request_audit`、`lead_discovery_query_state`、`retail_city_queue`、`leads`、
`lead_discovery_results`、`send_log`、`send_authorizations`、`send_authorization_entries`、`bounce_log`、`reply_log`、
`unmatched_dsn`、`system_config`；WorkBuddy 库 `~/.workbuddy/workbuddy.db` 表 `automations`；Windows 计划任务只读枚举；
部署通道 `deploy-channel/state/operations.json`；`preflight_gate.query_mx` 探针与 SAFE 测量脚本输出（本地留档）。
本地详细证据（含客户明细）仅保留在运行方本地，不推送 Git。Detailed evidence with customer records stays local.

## KEY=VALUE 摘要 / Summary

```
ACCEPTANCE_REQUEST=WORKBUDDY_READONLY_ACCEPTANCE_REQUEST_20261016
ACCEPTANCE_PASS=2_EXTENDED_WINDOW
RELEASE_OP=op-20261015-104202-5ecde6
PRODUCTION_SHA=e7e619d3e40f415c1894aa3e1087978875c6f26570755254ab535b68e5580903
ACCEPTANCE_WINDOW_START=2026-10-15T15:41:00+08:00
SAMPLING_TIME=2026-10-19T10:23:03+08:00
INVENTORY_AUTOMATION=automation-1784775229336
DUPLICATE_INVENTORY_SCHEDULER=false
RUNS_IN_WINDOW=15
RUNS_COMPLETED=7
RUNS_PARTIAL_SAFE_GAP=8
RUNS_FAILED=0
ENTRY_SAFE_DERIVED_LOWER_BOUNDS=50,52,50,54,54,56,56
EXIT_SAFE_SEQUENCE=52,52,54,54,56,56,56,56,56,56,56,56,56,56,56
PROVIDER_REQUESTS_EXECUTED=true
RUNS_WITH_PROVIDER_REQUESTS=7
PROVIDER_PAGE_REQUESTS_IN_WINDOW=17
PROVIDER_ERRORS_IN_WINDOW=0
PAGES_PER_FAMILY_MAX=3
RUNS_WITH_ZERO_PROVIDER_EXHAUSTION=8
COOPERSTOWN_CITY_ID=22
COOPERSTOWN_FAMILIES_BEFORE=13
COOPERSTOWN_FAMILIES_NOW=20
COOPERSTOWN_FAMILIES_PENDING=0
COOPERSTOWN_CITY_STATUS=browser_maps_active_city_completion_blocked_by_1_retryable_network_row
NEW_DISCOVERY_ROWS=13
NEW_LEAD_ROWS=8
NEW_INDEPENDENT_ORGANIZATIONS=8
FIRST_PARTY_OFFICIAL_SITE_EMAILS=7
FIRST_PARTY_EMAILS_VERIFIED_FLAG=6
LEADS_WITHOUT_EMAIL=1
NEW_LEADS_ALL_MANUAL_REVIEW=true
MX_CONTROL_PROBE=PASS
MX_POSITIVE_CONTROL=ok
MX_NEGATIVE_CONTROL=nxdomain
MX_PROBE_ATTEMPTS=2_first_failed_closed
CURRENT_SAFE=56
SAFE_READINGS=56,56
RUN_OVERLAPS=0
LOCK_CONFLICTS=0
JOB_ERRORS_IN_WINDOW=0
DUPLICATE_ORGANIZATIONS=0
BOUNCE_REPLY_DSN_NEW_IN_WINDOW=0,0,0
SENDS_IN_WINDOW=0
NEW_SEND_AUTHORIZATIONS=0
EXECUTABLE_SEND_AUTHORIZATIONS=0
SMTP_ENABLED_CONFIG=0
PRESEND_PREFLIGHT_OUTREACH_PAUSED=true
BUSINESS_CODE_DEPLOYED_BY_THIS_TASK=false
PRODUCTION_DB_WRITES_BY_THIS_ACCEPTANCE=0
EMAILS_SENT_BY_THIS_TASK=0
INVENTORY_MANUAL_TRIGGER=false
ROLLBACK_PERFORMED=false
DEPLOYED=CONFIRMED
PRODUCTION_EFFECTIVENESS_VERIFIED=CONFIRMED
```
