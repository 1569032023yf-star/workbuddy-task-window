# WorkBuddy 生产只读观测接口合同 / Production Read-Only Observability Contract

- **channel_id**: `rokt-deploy-channel`
- **endpoint**: `http://127.0.0.1:8791` (loopback only, never 0.0.0.0)
- **bridge_version**: `2.1` (operations = 13)
- **auth**: `Authorization: Bearer <token>`; token 存 Windows 凭据管理器 `rokt-deploy-channel:bridge-token`，只能本机 `CredReadW` 取，不入库、不入 Git、不入聊天。
- **transport**: 一律 `POST`（`/healthz` 为 `GET`），body 为 JSON 对象，最大 64 KiB。
- **生效时间**: 2026-10-22 15:58 +08（bridge 重启后实测 41/41 通过）
- **合同版本**: 1.0

---

## 1. 端点总表

| 端点 | 语义 | 写？ | 参数 | 返回 schema |
|---|---|---|---|---|
| `GET /healthz` | 存活与能力清单 | 否 | 无 | `{ok, bridge_version, operations, test_mode}` |
| `POST /v1/preflight` | 发布前 14 门禁 | 否 | `release_id` | 既有 |
| `POST /v1/apply` | 受控部署 | **是** | `release_id`, `confirm` | 既有 |
| `POST /v1/status` | 操作状态 | 否 | `operation_id` | 既有 |
| `POST /v1/rollback` | 字节级回滚 | **是** | `operation_id` | 既有 |
| `POST /v1/register` | 受限登记发布 | **是** | `release_id` | 既有 |
| `POST /v1/releases` | 已登记清单 | 否 | 无 | `rokt.releases.*` |
| `POST /v1/telemetry` | 汇总遥测 | 否 | 无 | `rokt.telemetry.v1` |
| `POST /v1/runtime` | Inventory 运行明细 | 否 | `run_id?`, `limit?` | `rokt.runtime.v1` |
| `POST /v1/city` | 城市阶段与完成条件 | 否 | `city?` | `rokt.city.v1` |
| `POST /v1/provider-audit` | 来源请求审计 | 否 | `hours?`, `city?` | `rokt.provider_audit.v1` |
| `POST /v1/scheduler` | 调度对账与唯一性 | 否 | `hours?` | `rokt.scheduler.v1` |
| `POST /v1/safe` | SAFE 权威快照 | 否（`refresh=1` 只触发只读测量） | `refresh?` | `rokt.safe_authority.v1` |
| `POST /v1/health` | 通道自检（不用 body） | 否 | 无 | 既有 |

不存在任意 PowerShell / Python / 文件 / SQL 执行面。未登记路径返回 `404 NOT_FOUND`。

---

## 2. 参数白名单（硬边界）

| 参数 | 类型 | 允许范围 | 越界行为 |
|---|---|---|---|
| `run_id` | string | `^[A-Za-z0-9:_\-]{1,80}$` | `400 BAD_PARAM` |
| `limit` | int | 1–50 | `400 BAD_PARAM` |
| `hours` | int | 1–168 | `400 BAD_PARAM` |
| `city` | int 或名称 | 1–9999，或 `^[A-Za-z .'\-]{1,64}$` 且必须命中队列行 | `400 BAD_PARAM` |
| `refresh` | bool-ish | `1/true/yes` | 忽略 |

参数全部走 SQL 绑定，不存在字符串拼接；`city` 名称先做字符白名单再等值匹配，不做模糊查询。

---

## 3. 各端点字段合同

### 3.1 `/v1/runtime`（A1）

必给：`run_id, stage, business_date, status, stop_reason, current_step, target, actual, gap, error_class, process_id, process_started_at, process_finished_at, process_duration_seconds, trigger_id, entrypoint, entrypoint_fingerprint.sha256`。

- **三种时间明确分开**：`planned_at`（派生自上次完成时刻 + rrule 间隔）≠ `triggered_at`（调度器回执 `automation_runs.created_at`）≠ `process_started_at`（`job_runs.started_at`，UTC→+08）。
- `planned_basis` 只有两种取值：`DERIVED_PREVIOUS_COMPLETION_PLUS_INTERVAL` 或 `NOT_RECORDED`。原始历史 `next_run_at` 每次运行被覆盖，**不伪造**。
- `trigger_receipts.firings[].executed`：该 firing 窗口内是否出现 `job_runs` 行。`false` 不等于漏跑，只表示 agent 层 fail-closed 未执行。
- `current_step` 只写首次入口值，**不代表阶段进度**。
- 阶段级事件（`activate_next_city` / `run_places_batch` / `run_staging_postprocess` / 城市完成判定）**当前未持久化**，一律 `NOT_RECORDED`，不做事后源码反推。
- `lock.state` ∈ `RELEASED / ACQUIRED / NO_LOCK_KEY_TODAY`。

### 3.2 `/v1/city`（A2/A3）

- `query_families`：总数（取生产 `RETAIL_QUERY_FAMILIES`，当前 20）、已完成数、剩余数、逐族状态。
- `records`：按 `validation_status` 的计数、待处理合计、`website_lookup_pending`、网络重试待办、已耗尽重试、下次到期时间。
- `pending_items[]`：**仅** `ref: ldr:<id>`、状态、错误类别、发现时间、`retry{attempts, failure_events, next_retry_at, last_failure_at, terminal_outcome}`。不含商家名/邮箱/域名/地址。
- `completion_checks`：9 项，直接调用生产 `retail_city_queue.city_completion_checks`，**不另立标准**；同时给出该模块与 `discovery_service.py` 的 SHA-256。
- `blocking_attribution`：用生产 `_manual_review_retryable / _linked_backlog_retryable / automatic_recovery_deferred` 归因，指出哪些行让 `no_open_work` 为 false。
- `stage_events.available=false` + `observable_proxies`：说明历史阶段轨迹不可得，仅给可持久化代理指标。

### 3.3 `/v1/provider-audit`（A4）

三态结论，禁止把"没日志"当成"0 次"：

| verdict | 含义 | 判据 |
|---|---|---|
| `REAL_REQUESTS` | 窗口内确有请求 | 窗口内有 `provider_request_audit` 行 |
| `ZERO_REQUESTS_CONFIRMED` | 确认零请求 | 无行 **且** 该城市/来源查询族已全部 completed（无可发请求） |
| `UNKNOWN_NO_RECORD` | 证据不足 | 无行但查询矩阵未耗尽 |

同时给 `per_provider{requests, success, failed, timeout, rate_limited, last_requested_at}`。

### 3.4 `/v1/scheduler`（C1/C2）

- 对账模型：`planned(next) = completed(previous) + interval`（**成对**计算）。原因：调度器把 HOURLY 规则锚在"上次完成时刻"，绝对时间网格必然假报漏跑。
- 输出：`receipts_paired`、`drift_seconds{min,max,avg}`、`skipped_slots_total`、`skipped_slot_detail`、`pending_slot`、`next_run_at_vs_pending_slot_seconds`。
- `missed_inventory_runs_confirmed` = 相邻回执间**被跳过的整槽总数**，不是"计划时间已过"。
- 唯一性：按角色表分类（`INVENTORY / READ_ONLY_SAFE_CHECKPOINT / RESULT_RECOVERY_SYNC / SEND_STAGE / UNCLASSIFIED`）。任一 ACTIVE 且 `UNCLASSIFIED` 即判 `NOT_PROVEN`（fail-closed）。
- `windows_service`：只读 `SCM QueryServiceStatusEx` + 注册表 `Start`，**不做启停/删除**。
- `scheduled_tasks`：`schtasks.exe` 被宿主策略禁用，保持 `UNKNOWN`，不猜。

### 3.5 `/v1/safe`（B1/B2）

- 权威路径：`campaign_eligible_v2.select_candidates_for_plan_v2` + `preflight_gate.query_mx`，`mode=ro` 连接，SAFE = distinct `organization_key`。
- 必给：`rule_version.code{sha256}`、`method`、`source`、`measured_at`、`db_identity{sha256, quick_check}`、`safe_unique_orgs`、`mx_positive_control`、`mx_negative_control`、`mx_probe_ok`、`measurement_complete`、`available`、`fresh`、`age_hours`、`failure_reason`。
- `readings[]`：连续两次读数 + `reading_agreement`（MX 实时解析存在抖动，单次读数不作为最终值）。
- `safe_net_growth{h24,d7}`：**只有在存在同一 `rule_version` + 同一去重口径的历史快照时才给数字**，否则 `UNKNOWN` + `reason`。增量账本 `state/safe_ledger.jsonl` 自本次起累积。
- `new_customer_funnel{h24,d7}`：发现记录数、独立组织、已验证官网、新 leads、带邮箱、**第一方官网邮箱**、独立 `organization_key`、来源贡献；显式声明"发现 ≠ 身份确认 ≠ 有邮箱 ≠ SAFE"。
- `refresh=1`：另起独立进程测量（需要 `dnspython`，用系统 Python 3.13），HTTP 立即返回 `refresh_result=MEASUREMENT_STARTED`，客户端轮询。测量**永不阻塞**服务。

---

## 4. 全局保证

1. **只读**：所有库以 `mode=ro` 打开；模块内不存在 `INSERT/UPDATE/DELETE/DDL/ATTACH`（有自动化断言，见 `test/run_obs_tests.py::no_write_sql_in_module`）。
2. **脱敏**：任一返回体只要出现 `business_name/email/website/domain/address/phone/payload/token` 等键，`assert_redacted` 直接抛错（fail-closed），不会返回半脱敏数据。
3. **不猜**：缺失即 `UNKNOWN / NOT_RECORDED` + `reason`；`0` 只在有正面证据时出现。
4. **有界**：参数闭集、行数上限、时间窗上限 168h、`pending_items` 上限 40、引用列表上限 20。
5. **可审计**：每次调用写入 `logs/audit.jsonl`（含 path / auth / code / ms）。

## 5. 错误码

| code | 含义 |
|---|---|
| 401 `UNAUTHORIZED` | 缺/错 Bearer token |
| 404 `NOT_FOUND` | 未登记端点 |
| 400 `BAD_PARAM*` / `*_RANGE` | 参数越界或不合法 |
| 400 `INVALID_JSON` / `BODY_NOT_OBJECT` / `EMPTY_OR_OVERSIZE_BODY` | 请求体不合法 |
| 500 `INTERNAL` | 未预期异常（细节只在审计日志） |

## 6. 测试与验收证据

| 套件 | 结果 | 文件 |
|---|---|---|
| 观测沙箱（合成库 + 生产规则模块副本） | **40/40** | `deploy-channel/test/obs_report.json` |
| 观测在线验收（真实生产只读） | **41/41** | `deploy-channel/test/live_obs_acceptance.json` |
| 通道单元 | 32/32 | `test/unit_report.json` |
| 通道沙箱部署 | 58/58 | `test/sandbox_cli_report.json` |
| 多文件发布 | 34/34 | `test/multi_report.json` |
| 桥接调用链 | 26/26 | `test/bridge_report.json` |
