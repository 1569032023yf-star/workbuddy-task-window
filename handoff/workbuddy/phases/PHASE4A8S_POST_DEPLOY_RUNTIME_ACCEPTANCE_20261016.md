# PHASE 4A.8S 部署后运行验收（一次性只读）/ Post-Deployment Runtime Acceptance (One-time, Read-Only)

- 验收请求 / Acceptance request: `handoff/phases/WORKBUDDY_READONLY_ACCEPTANCE_REQUEST_20261016.md`
  (repo `1569032023yf-star/roktandrazo-outreach-codex`, branch `codex/engineering-deployment-charter`)
- 验收窗口 / Acceptance window: 2026-10-15T15:41:00+08:00 → 采样时间 / sampling time 2026-10-16T18:29:47.589964+08:00 (Asia/Shanghai, +08)
- 发布操作 / Release operation: `op-20261015-104202-5ecde6` (apply, verdict APPLIED, 14/14 gates, caller=bridge, test_mode=false),
  finished 2026-10-15T10:42:04+08:00; channel-confirmed production SHA `e7e619d3e40f415c1894aa3e1087978875c6f26570755254ab535b68e5580903`
- 执行性质 / Nature: read-only evidence collection only. 未手动触发 Inventory、未 apply/rollback、未写数据库业务数据、未发送邮件。
  No Inventory trigger, no apply/rollback, no DB business writes, no emails.
- 报告生成 / Generated: 2026-10-16T18:40:38+08:00

## 1. 运行事实与调度关联 / Run facts and scheduler linkage

验收窗口内唯一 Inventory 调度器 `automation-1784775229336`（ACTIVE，`FREQ=HOURLY;INTERVAL=6`，下次运行 2026-10-16 23:10:38 +08）
共执行 5 次计划运行，全部 `completed / target_met`：

| run_id | business_date | 开始 +08（原字段 UTC） | 结束 +08 | 状态 | target | 入口→出口 SAFE | gap |
|---|---|---|---|---|---|---|---|
| `inventory:2026-10-15:76940963` | 2026-10-15 | 2026-10-15 15:43:26 +08 (orig UTC 2026-10-15 07:43:26) | 2026-10-15 15:52:56 +08 | completed / target_met | 50 | entry≥50 → exit 52 | 0 |
| `inventory:2026-10-15:69235b78` | 2026-10-15 | 2026-10-15 21:59:50 +08 (orig UTC 2026-10-15 13:59:50) | 2026-10-15 22:08:38 +08 | completed / target_met | 50 | entry≥52 → exit 52 | 0 |
| `inventory:2026-10-16:fbcc7295` | 2026-10-16 | 2026-10-16 04:11:39 +08 (orig UTC 2026-10-15 20:11:39) | 2026-10-16 04:21:05 +08 | completed / target_met | 50 | entry≥50 → exit 54 | 0 |
| `inventory:2026-10-16:cdf0ebd2` | 2026-10-16 | 2026-10-16 10:36:42 +08 (orig UTC 2026-10-16 02:36:42) | 2026-10-16 10:43:39 +08 | completed / target_met | 50 | entry≥54 → exit 54 | 0 |
| `inventory:2026-10-16:b76e3cab` | 2026-10-16 | 2026-10-16 16:55:05 +08 (orig UTC 2026-10-16 08:55:05) | 2026-10-16 17:03:43 +08 | completed / target_met | 50 | entry≥54 → exit 56 | 0 |

- 原字段时区 / Original field timezones: `job_runs.started_at/finished_at` = UTC naive（表内已 +8h 归一）；`leads.collected_at` = +08 naive；`provider_request_audit.requested_at` = ISO `+00:00`。
- 无重复调度器 / No duplicate scheduler: WorkBuddy `automations` 表全量扫描——其余一切含 Inventory 语义的自动化均为 PAUSED 或已删除；
  Windows 计划任务面无任何 Inventory 任务（`RoktRazo-BD-PreSend`/`RoktRazo-BD-Outreach` = Disabled）。
- 说明 / Note: 10-15 上午 6h 节拍槽位无 `job_runs` 记录（在验收窗口之前）；本地证据无法归因（与发布时调度器重锚一致），无业务影响，单列不计入本次发布异常。
  One pre-window cadence slot on 10-15 morning has no run record; cause UNKNOWN from local evidence; no business impact; listed separately.

## 2. SAFE≥50 入口证据与 Provider 执行 / Entry SAFE≥50 evidence and Provider execution

每轮入口 SAFE 的精确值只进入自动化 stdout（本地不可得），以「出口 SAFE − 本轮新增组织数」给出下界；五轮下界全部 ≥ 50
（50 / 52 / 50 / 54 / 54），出口 SAFE 52→52→54→54→56，target=50，gap=0，`stop_reason=target_met`。
Exact per-run entry SAFE is logged only to automation stdout (UNKNOWN locally); derived lower bounds all ≥ 50; exit SAFE 52→56.

- 真实 Provider 请求 / Actual Provider requests: `provider_request_audit` id 264–275，provider `browser_maps`，Cooperstown（city_id=22），
  5 个查询族、13 次请求、状态全部 `ok`、0 错误；每族 `pages_processed` 2–3 页（≤3 页预算，`WORKBUDDY_DISCOVERY_MAX_PAGES=3`）。
- 代码路径 / Code path (deployed): `bd_orchestrator.py` :429-431「Inventory sufficiency is an outcome, never permission to skip the bounded discovery path」
  → `DISCOVERY_PATH_EXECUTED=true` 无条件执行；:448-451 仅在 Provider 真实错误时停止。
- 对照 / Contrast: 部署前 4A.5U 审计记录为「SAFE≥50 时 0 个 Provider 请求」；部署后窗口内每轮均有真实请求且 SAFE 持续增长。
- **PROVIDER_REQUESTS_EXECUTED = true**

## 3. Cooperstown 推进 / Cooperstown progression

Cooperstown（city_id=22，status=active）共 20 个查询族；部署前已完成 13 个（最后完成于 2026-10-13 00:39:39 +08）。
20 query families; 13 completed before the release. 部署后新增完成 / completed after the release:

| 查询族 / query family | 完成时间 +08 | run_id | 页数 / pages | 新唯一地点 / new unique places |
|---|---|---|---|---|
| children's store | 2026-10-15 15:46:59 +08 | inventory:2026-10-15:76940963 | 3 | 5 |
| family game store | 2026-10-15 22:03:29 +08 | inventory:2026-10-15:69235b78 | 2 | 0 |
| visitor center gift shop | 2026-10-16 04:14:42 +08 | inventory:2026-10-16:fbcc7295 | 3 | 5 |
| tourist gift shop | 2026-10-16 10:36:39 +08 | inventory:2026-10-16:cdf0ebd2 | 2 | 0 |
| specialty retailer | 2026-10-16 16:58:44 +08 | inventory:2026-10-16:b76e3cab | 3 | 3 |

当前进度 / Current: **18/20 completed，2 个 pending**（puzzle store、card game store 两个族）。
即 13/20 →（请求参照点 / request reference）17/20 → **当前 18/20**。推进与上述 5 次计划运行一一对应。

## 4. 新增独立组织 / leads / 官网第一方邮箱 / New organizations, leads, first-party emails

区间 / Interval: 2026-10-15T10:42:04+08:00（发布完成）→ 采样时间 / sampling time。

| 指标 / metric | 值 / value |
|---|---|
| 新 lead 行数 / new lead rows | 8 |
| 独立新组织 / new independent organizations | **8** |
| 新行内重复 organization_key / duplicate org keys within new rows | 0 |
| 部署前已存在的 organization_key / pre-existing org keys | 0 |
| 官网第一方邮箱 / first-party official-site emails | 7（其中 verified 标记 6） |
| 无邮箱 lead / leads without email | 1 |
| 全部 manual_review_needed（无可发送） / all manual_review_needed (none sendable) | true |
| 城市分布 / cities | Cooperstown 8 |
| 按运行归因 / per-run attribution | 76940963:2，69235b78:0，fbcc7295:4，cdf0ebd2:0，b76e3cab:2 |

去重口径 / Dedup definition: distinct `organization_key`，且首次出现时间落在区间内；行数从不当作独立组织数。
Distinct organization_key with first appearance inside the interval; row counts are never used as organization counts.
第一方证据 / First-party evidence: `email_source_type=official_page_visible`（官网页面可见），`evidence_url` 留档于本地详细证据（不推送）。
历史门禁 / History gates: 资格字段未放宽（`send_eligibility` 为空、无自动发送资格）。

## 5. MX 控制探针与最新 SAFE / MX control probe and latest SAFE

| 项 / item | 值 / value |
|---|---|
| 探针标识 / probe identity | `preflight_gate.query_mx`（既有正式只读探针 / existing formal read-only probe） |
| 版本 / version | 模块 SHA-256 `2cd286f2…`（41251 B，mtime 2026-09-16 15:15:54） |
| 端点 / endpoint | Worker `/internal/mx-check`（Bearer；凭据不入报告 / credentials not in report） |
| 超时 / timeout | 10 s |
| 解析环境 / resolver env | `BD_MX_HTTPS_PROXY` 显式配置；仅本次 HTTPS 请求使用，不继承 `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY`；Worker 失败回退直连 DNS |
| 通过判据 / pass criteria | 正控 gmail.com → `ok` 且 负控无效域 → 非 `ok` |
| 控制结果 / control results | gmail.com → **ok**（2026-10-16T10:29:46.918Z）；无效域 → **nxdomain** |
| 探针时间 / probe time | 2026-10-16T18:29:47.589941+08:00（耗时 1.22s） |
| 探针结论 / probe verdict | **PASS** |

探针通过后按既有完整门禁（V1/V2/MX/历史/退订/抑制不变）以 `mode=ro` 连接测量：
After the probe passed, measured on a `mode=ro` connection via `campaign_eligible_v2.select_candidates_for_plan_v2`, distinct `organization_key`:

| 读数 / reading | 采样时间 +08 | 候选行 / candidate rows | 独立组织 / unique orgs |
|---|---|---|---|
| 1 | 2026-10-16T18:29:47.602614+08:00 | 56 | 56 |
| 2 | 2026-10-16T18:31:40.460697+08:00 | 56 | 56 |

**CURRENT_SAFE = 56**（两次独立读取一致；已知 MX 抖动区间内无分歧 / two consecutive readings agree）。

## 6. 异常、并发、锁与冻结 / Exceptions, concurrency, locks, freeze

| 检查 / check | 结果 / result |
|---|---|
| 运行重叠 / run overlaps | 0 |
| 锁冲突 stop_reason / lock-conflict stops | 0（窗口内 inventory 锁全部 released） |
| job_runs 错误 / job errors in window | 0 |
| Provider 错误（窗口内）/ Provider errors in window | 0 |
| 新增 bounce / reply / unmatched DSN（窗口内） | 0 / 0 / 0 |
| 发送（窗口内 / since deployment） | 0 / 0（最后发送 2026-09-16 01:09:52 +08） |
| 新发送授权 / new send authorizations | 0 |
| PreSend `1785804406748` / Preflight `1785804413719` / Outreach `1785804421539` | 均 PAUSED 且已删除 / all PAUSED + deleted |
| Windows 任务 / scheduled tasks | PreSend/Outreach Disabled；PostSend Ready（仅验证阶段，无发送面 / verification only） |

- 旧残留单列 / Pre-deployment residue (separate, not attributed to this release): Saratoga Springs（city_id=21）`browser_maps`
  代理连接失败 18 行，时间 2026-09-30 ~ 2026-10-02（发布前）。
- SMTP=0 判定依据 / Basis for SMTP=0: `send_log` 与发送授权为权威口径；直接 SMTP 遥测不在只读面内（推断值，已标注）。
  send_log + authorizations are the authoritative read-only surface; direct SMTP telemetry is out of read-only scope (inferred).

## 结论 / Verdicts

- **DEPLOYED = CONFIRMED**：生产文件 SHA `e7e619d3…`（31552 B）与发布清单一致；通道操作记录 `op-20261015-104202-5ecde6`
  applied @ 2026-10-15T10:42:04+08:00，14/14 门禁，caller=bridge，test_mode=false。
- **PRODUCTION_EFFECTIVENESS_VERIFIED = CONFIRMED**：发布后 5 次计划运行全部真实执行 Provider 请求；SAFE 52→56；
  Cooperstown 13/20→18/20；新增 8 个独立组织、7 个官网一方邮箱；并发/锁/Provider 错误为零；发送面冻结保持。
- UNKNOWN 项 / UNKNOWN items: 每轮入口 SAFE 精确值（仅自动化 stdout 有记录，本地不可得）；10-15 上午缺失节拍槽的归因；
  直接 SMTP 连接数（以 send_log/授权推断为 0）。

## 边界（本次未做）/ Boundaries (not performed by this task)

`BUSINESS_CODE_DEPLOYED_BY_THIS_TASK=false`（4A.8S 由 Codex 于 10-15 经通道部署，本次只读）、`PRODUCTION_DB_WRITES_BY_THIS_TASK=0`、
`EMAILS_SENT_BY_THIS_TASK=0`、`INVENTORY_MANUAL_TRIGGER=false`、`ROLLBACK_PERFORMED=false`、`SAFE_MX_HISTORY_GATES_UNCHANGED=true`、
`NO_SECOND_INVENTORY_SCHEDULER=true`。
生产完整性 / Production integrity: `bd_orchestrator.py` SHA 未变（`e7e619d3…`）；DB mtime 2026-10-16 17:03:43 早于本次会话读取（18:15+），WAL 0 字节。

## 证据来源 / Evidence provenance (no credentials)

生产库只读查询（`mode=ro`）：`job_runs`、`provider_request_audit`、`lead_discovery_query_state`、`retail_city_queue`、`leads`、
`send_log`、`send_authorizations`、`bounce_log`、`reply_log`、`unmatched_dsn`、`system_config`；
WorkBuddy 自动化库只读查询 `~/.workbuddy/workbuddy.db` 表 `automations`；Windows 计划任务只读枚举；
部署通道操作记录 `deploy-channel/state/operations.json`；MX 探针与 SAFE 测量脚本输出（本地留档）。
本地详细证据（含客户明细）仅保留于运行方本地，不推送 Git。Detailed evidence with customer records stays local; not pushed.

## KEY=VALUE 摘要 / Summary

```
ACCEPTANCE_REQUEST=WORKBUDDY_READONLY_ACCEPTANCE_REQUEST_20261016
RELEASE_OP=op-20261015-104202-5ecde6
RELEASE_FINISHED_AT=2026-10-15T10:42:04+08:00
PRODUCTION_SHA=e7e619d3e40f415c1894aa3e1087978875c6f26570755254ab535b68e5580903
ACCEPTANCE_WINDOW_START=2026-10-15T15:41:00+08:00
SAMPLING_TIME=2026-10-16T18:29:47.589964+08:00
INVENTORY_AUTOMATION=automation-1784775229336
DUPLICATE_INVENTORY_SCHEDULER=false
RUNS_IN_WINDOW=5
RUNS_ALL_COMPLETED_TARGET_MET=true
ENTRY_SAFE_LOWER_BOUNDS=50,52,50,54,54
EXIT_SAFE_SEQUENCE=52,52,54,54,56
PROVIDER_REQUESTS_EXECUTED=true
PROVIDER_REQUESTS_IN_WINDOW=13
PROVIDER_ERRORS_IN_WINDOW=0
PAGES_PER_FAMILY_MAX=3
COOPERSTOWN_CITY_ID=22
COOPERSTOWN_FAMILIES_BEFORE=13
COOPERSTOWN_FAMILIES_AFTER=18
COOPERSTOWN_FAMILIES_PENDING=2
NEW_LEAD_ROWS=8
NEW_INDEPENDENT_ORGANIZATIONS=8
FIRST_PARTY_OFFICIAL_SITE_EMAILS=7
FIRST_PARTY_EMAILS_VERIFIED_FLAG=6
LEADS_WITHOUT_EMAIL=1
NEW_LEADS_ALL_MANUAL_REVIEW=true
MX_CONTROL_PROBE=PASS
MX_POSITIVE_CONTROL=ok
MX_NEGATIVE_CONTROL=nxdomain
CURRENT_SAFE=56
SAFE_READINGS=56,56
RUN_OVERLAPS=0
LOCK_CONFLICTS=0
JOB_ERRORS_IN_WINDOW=0
BOUNCE_REPLY_DSN_NEW_IN_WINDOW=0,0,0
SENDS_IN_WINDOW=0
SENDS_SINCE_DEPLOYMENT=0
NEW_SEND_AUTHORIZATIONS=0
PRESEND_PREFLIGHT_OUTREACH_PAUSED=true
BUSINESS_CODE_DEPLOYED_BY_THIS_TASK=false
PRODUCTION_DB_WRITES_BY_THIS_TASK=0
EMAILS_SENT_BY_THIS_TASK=0
INVENTORY_MANUAL_TRIGGER=false
ROLLBACK_PERFORMED=false
DEPLOYED=CONFIRMED
PRODUCTION_EFFECTIVENESS_VERIFIED=CONFIRMED
```
