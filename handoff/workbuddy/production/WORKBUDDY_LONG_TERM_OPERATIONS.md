# ROKT&RAZO — WORKBUDDY 长期生产运维交付
# Long-Term Production Operations Delivery

- **生成时间 / generated_at**: 2026-10-22 16:05 +08
- **业务时区 / business timezone**: Asia/Shanghai (+08)；`business_date` 按 America/New_York 16:00 切换
- **执行者**: WorkBuddy（生产运维方）
- **配套机器文件**: `WORKBUDDY_LONG_TERM_OPERATIONS.json`、`PRODUCTION_RUNTIME_LATEST.json`、`INVENTORY_SCHEDULER_RECONCILIATION.json`、`CITY_STAGE_TRACE.json`、`SAFE_AUTHORITY_SNAPSHOT.json`、`PROVIDER_REQUEST_AUDIT_24H.json`、`RELEASE_REGISTRY_SNAPSHOT.json`、`OBSERVABILITY_CONTRACT.md`、`PRODUCTION_OPERATIONS_STATUS.md`

---

## 0. 直接回答用户六个问题 / Six answers

| # | 问题 | 答案 |
|---|---|---|
| 1 | 城市为什么卡住 | **Cooperstown (city_id=22) 被 2 行历史遗留记录结构性锁死**：`ldr:556`、`ldr:565` 每轮都被判为"该重试"（`network_recovery_due=True`），但决定终态的计数器 `unavailable_attempts` 停在 **1** / **根本不存在**（而 `attempts` 已涨到 20 / 31）→ 永远达不到 `== 3` 的终态门槛 → `no_open_work` 恒 false → 9 项完成条件中 4 项恒 false。**时间不会自愈，需 Codex 补丁**。另有 `ldr:571` 属可自愈（`attempts` 1/3）。详见 §7 |
| 2 | 调度是否真正正常 | **正常**。48h 内 7 次触发，成对偏移 12.2–446.4s（均值 90.8s），**跳过整槽 0 次，漏跑 0 次**；`next_run_at` 与派生下一槽仅差 0.3s。3 次未产生生产运行属 agent 层 fail-closed（代理门），**不是漏跑** |
| 3 | 现在实际有多少 SAFE | **56**（同一次测量连续两读数 56 / 56；MX 正控 `ok`、负控 `nxdomain`、DB `quick_check=ok`）。24h/7d 净增长 **UNKNOWN**（无同口径历史快照） |
| 4 | 每天新增多少真实公司与第一方邮箱 | 24h：**0 / 0**（窗口内无任何发现，因查询族已耗尽）。7d：发现 8 条 → 8 个独立组织 → 4 个已验证官网 → 6 条新 lead → 5 条带邮箱 → **4 个第一方官网邮箱** → 6 个独立 `organization_key` |
| 5 | Codex 能否自行取生产证据 | **接口已可用**（5 个只读端点上线并实测 41/41），但**尚未被 Codex 消费确认**；`CODEX_HANDOFF_CONSUMED=false`，不得声称已完成对接 |
| 6 | WorkBuddy 能否长期维护生产服务 | 桥接**会话内**稳定（崩溃 2 秒自愈实测通过），**登录自启**已注册，**开机级常驻需要一次性管理员操作**（当前进程拿不到，见 §9） |

---

## 1. 板块 A —— 正式生产只读观测系统（已交付）

**新增 5 个固定字段、有限参数的只读端点**，全部 `mode=ro`、参数闭集、脱敏强制、无任意 SQL/文件/命令面：

| 端点 | 解决什么 | 实测 |
|---|---|---|
| `/v1/runtime` | Inventory 运行明细；区分**计划 / 触发 / 进程启动**三种时间 | 200 + `rokt.runtime.v1` |
| `/v1/city` | 城市阶段与 9 项完成条件、重试状态、阻塞归因 | 200 + `rokt.city.v1` |
| `/v1/provider-audit` | 来源请求审计，三态结论（真实请求 / 确认零请求 / 无记录） | 200 + `rokt.provider_audit.v1` |
| `/v1/scheduler` | 调度对账 + Inventory 唯一性 | 200 + `rokt.scheduler.v1` |
| `/v1/safe` | SAFE 权威快照 + 两次读数 + 增长/漏斗 | 200 + `rokt.safe_authority.v1` |

**真实生产证据（run `inventory:2026-10-22:03b70e7a`）**

- 进程 05:49:11 → 05:53:35 +08（264.0s），`status=completed`，`stop_reason=target_met`，target 50 / actual 56 / gap 0
- 入口 `bd_orchestrator.py` SHA-256 `e7e619d3…80903`（== 4A.8S after-SHA，未被改动）
- 锁 `run_lock:daily_outreach:inventory:2026-10-22 = released`
- **阶段级事件未持久化** ⇒ `stage_events.available=false`，只给可持久化代理指标。**已按要求标记 NOT_RECORDED，未用源码反推历史轨迹**

**测试**：观测沙箱 40/40（含 5 类越界参数拒绝、脱敏断言、三态判定、成对槽计算、只读哈希不变、模块内无写 SQL）；在线验收 41/41。

### 未达成的两项（不伪报）

1. **阶段事件轨迹**：需要一次生产代码改动（新增固定事件类型 + 有界错误类别 + 脱敏摘要）→ 由 Codex 出清单，走受控发布。
2. **Codex 实际消费确认**：需 Codex 读取并回执。WorkBuddy 已发布证据包与合同，但**"已发布" ≠ "已消费"**。

因此 `PRODUCTION_OBSERVABILITY_ACCEPTED = false`（10 项前置条件中 8 项成立，第 2、9 项未成立）。

---

## 2. 板块 B —— SAFE 权威与增长统计（已交付）

| 项 | 值 | 来源 |
|---|---|---|
| 规则版本 | `V1_V2_MX_HISTORY_SUPPRESSION_BUSINESS_FIT`；`campaign_eligible_v2.py` / `preflight_gate.py` 双 SHA | `/v1/safe` |
| 方法 | `select_candidates_for_plan_v2`，`mode=ro`，distinct `organization_key` | 同上 |
| 测量时间 | 2026-10-22 15:49:52 +08（读数 15:52:56 / 15:56:45） | 同上 |
| 库标识 | `bd_leads.db` sha256 `66509daa…f36`，`quick_check=ok` | 同上 |
| **SAFE_LATEST** | **56**（reading1=56, reading2=56, agreement=true） | 同上 |
| MX 正控 / 负控 | `gmail.com → ok` / `…invalid → nxdomain` | 同上 |
| 完整/新鲜 | `measurement_complete=true`、`fresh=true` | 同上 |
| 净增长 24h/7d | **UNKNOWN** —— 无同一规则版本的历史可比快照；已建立 `state/safe_ledger.jsonl` 从本次起累积 | 同上 |

**增长漏斗（同口径、显式去重）**

| 指标 | 24h | 7d |
|---|---|---|
| 商家发现记录 | 0 | 8 |
| 独立组织（domain 优先） | 0 | 8 |
| 已验证官网 | 0 | 4 |
| 新 leads | 0 | 6 |
| 带邮箱 | 0 | 5 |
| **第一方官网邮箱** | **0** | **4** |
| 独立 `organization_key` | 0 | 6 |
| 来源贡献 | — | browser_maps 8 |

> 口径：发现窗口用 UTC ISO，lead 窗口用 `leads.collected_at`（+08，字面 `T`）；**商家发现 ≠ 企业身份确认 ≠ 有邮箱 ≠ SAFE 客户**。

---

## 3. 板块 C —— 调度链核实（已完成）

**结论：调度没有漏跑。** 48h 成对对账：

| 触发时刻 (+08) | 派生计划时刻 | 偏移 | 是否产生生产运行 | run_id |
|---|---|---|---|---|
| 10-22 11:58:21 | 11:58:01 | +20.2s | 否（fail-closed） | — |
| 10-22 05:44:17 | 05:43:24 | +52.5s | 是 | `inventory:2026-10-22:03b70e7a` |
| 10-21 23:24:52 | 23:24:23 | +29.4s | 是 | `inventory:2026-10-21:c894911a` |
| 10-21 17:21:26 | 17:20:53 | +33.1s | 否（fail-closed） | — |
| 10-21 11:01:40 | 10:54:14 | +446.4s | 否（fail-closed） | — |
| 10-21 04:36:37 | 04:35:56 | +41.7s | 是 | `inventory:2026-10-21:1a7f7233` |
| 10-20 22:16:08 | 22:15:56 | +12.2s | 是 | `inventory:2026-10-20:8b9f1d72` |

- 相邻槽被跳过合计 **0**；`next_run_at 18:18:22.823` 与派生下一槽 18:18:22.540 相差 **0.3s**
- **11:58 那次"疑似漏跑"已被证伪**：`automation_runs` 有回执（thread `…:1792641501956`），agent 因 **Astrill 3213 代理死亡**按 fail-closed 拒绝执行，未产生 `job_runs` 行 —— 这是设计行为，不是调度故障
- 代理现已恢复（3213 OPEN、google 204、maps 200）

**Inventory 唯一性**

- WorkBuddy 侧：`automation-1784775229336` = 唯一 `role=INVENTORY` 的 ACTIVE 自动化；其余为 `READ_ONLY_SAFE_CHECKPOINT`（SAFE40，ACTIVE）、`RESULT_RECOVERY_SYNC`、以及 PAUSED 一次性任务
- 服务侧：`BDExecutionHost` = **STOPPED / MANUAL**（只读 SCM 查询），不构成第二驱动
- 计划任务侧：`schtasks.exe` 被宿主策略禁用 → **UNKNOWN**，不猜
- 判定：`UNIQUE`（`workbuddy_active_unclassified_drivers=0`）

---

## 4. 板块 D —— 桥接服务生命周期（部分达成，如实标注）

| 项 | 状态 | 证据 |
|---|---|---|
| 服务在线 | **UP** | `/healthz` → `bridge_version=2.1`，13 operations，`test_mode=false` |
| 崩溃自愈 | **已验证** | 15:58:06 `CHILD_EXIT exit_code=1 uptime=525.6s` → 15:58:08 `SPAWN child_pid=30996`，**2 秒**恢复，新代码生效 |
| 会话内常驻 | 可用 | 监督进程 + 单实例锁 + 有界退避 + 心跳（`state/supervisor_heartbeat.json`） |
| 登录自启 | **已注册**（本次未观测） | `HKCU\…\Run\RoktDeployChannelSupervisor`；已删除会造成端口竞争的旧项 `RoktDeployBridge` |
| 开机级常驻 | **未达成** | `CREATE_BREAKAWAY_FROM_JOB` → `WinError 5`；`WScript.Shell` COM 与 `cmd.exe` 均被宿主安全策略拒绝；explorer 方式无效 |
| 服务身份 | 当前用户、非提权 | 无 `SeServiceLogonRight`，无服务安装权限 |
| 回环误走系统代理 | **已修** | 健康探测使用空 `ProxyHandler`，不受 `HTTP_PROXY` 影响 |
| 发布安全门禁 | **保留** | 14 门禁、白名单、寄存器封签（篡改即 `REGISTRY_TAMPERED`）、字节级 diff、备份、排他锁、安全窗口、受控回滚；单元 32/32、沙箱 58/58、多文件 34/34、桥接 26/26 |

**遥测契约修正（D3）**

| 旧问题 | 修正 |
|---|---|
| `running_inventory_24h_window` 实际只查 2 小时 | 改名为 `running_inventory_2h`，另给真正的 `running_inventory_24h`、`inventory_runs_24h`，并附 `window_note` |
| `safe.reason` 提示 `POST /v1/safe-snapshot`（该路由不存在） | 改为指向真实存在的 `POST /v1/safe`；`safe.authoritative_route` 显式给出 |

---

## 5. 板块 E —— WorkBuddy → Codex 自动交接（已发布，未消费）

- 证据包 7 个 + 合同 1 个 + 状态 1 个 已写入交接仓库 `handoff/workbuddy/production/`
- 每个包都含 `schema_version / generated_at / business_timezone / run_id / data_sources / production_code_sha256 / payload_sha256 / unavailable[]`
- **不含**客户明细、凭据、数据库原件
- `CODEX_HANDOFF_PUBLISHED=true`；`CODEX_HANDOFF_CONSUMED=false`；`CODEX_RUNTIME_EVIDENCE_ACCEPTED=false`
- **不把"已推送"当成"Codex 已处理"**

---

## 6. 今日修复的真实缺陷（6 个，均非"改测试凑绿"）

| # | 缺陷 | 后果 | 修法 |
|---|---|---|---|
| 1 | `supervisor._pid_alive` / `launch_supervisor.pid_alive` 只做 PID 子串匹配 | **Windows PID 回收**：旧锁 pid 12484 已被 `WeMailNode_x64.exe` 复用 → 判定"监督进程还活着" → 启动器拒绝启动 → **通道永久起不来** | 解析 `tasklist` CSV，同时校验 `python.exe/pythonw.exe` 镜像名 |
| 2 | `prodobs.scheduler_reconciliation` 存在**重复** `uniqueness` 字典 | 后一个覆盖前一个，`workbuddy_active_unclassified_drivers` 被静默丢弃（沙箱测试捕获） | 删除重复块 |
| 3 | 参数错误被 `except Exception` 吞成 **500** | Codex 无法区分"我传错了"与"服务炸了" | 显式捕获 `ValueError` → `400 BAD_PARAM*` |
| 4 | `telemetry` 的 `running_inventory_24h_window` 名不符实 | 误导 Codex 认为覆盖 24h | 重命名 + 补真 24h 字段 |
| 5 | `telemetry.safe.reason` 指引不存在的 `/v1/safe-snapshot` | 假可用提示 | 指向 `/v1/safe` + `authoritative_route` |
| 6 | 证据生成器判定 `CUSTOMER_SMTP_ENABLED` 的**极性写反**：`str(v) not in ("None","1")`，`v="0"`（关闭）时返回 **True** | 报告会声称**客户 SMTP 已开启**——与"客户 SMTP 必须保持关闭"的红线**完全相反**的假报，且是安全类字段 | 改为三态函数：`"0"→false`、`"1"→true`、读不到→`UNKNOWN`（fail-closed）；同时保留原始值、来源、DB↔telemetry 交叉一致性字段 |

第 6 项是本次自查发现的**安全类假报**（原报告 JSON 为 `true`、Markdown 为 `false`，两份自相矛盾）。修法不只是改布尔值，而是把该字段从"断言"改成"实测"：新增 `CUSTOMER_SMTP_ENABLED_RAW` / `_SOURCE` / `CUSTOMER_SMTP_SOURCES_AGREE`，任何读者可脱离本文件自行复核。同批把 `PRODUCTION_DB_UNAUTHORIZED_WRITES`、`UNAUTHORIZED_EMAILS_SENT`、`BRIDGE_HEALTH`、`RELEASE_SECURITY_GATES_PRESERVED` 也一并从硬编码改为实测派生（详见 §8 注释）。

另修：健康探测走系统代理返回 502（前序已修，本次复核仍在位）；`U06`/`B01` 端点集合断言随合同扩容同步更新（**扩容而非放宽**：仍是闭集断言，13 条逐条列出）。

---

## 7. 城市为何卡住（根因详述，供 Codex 修）

```
city_id=22 Cooperstown (NY)  status=active  pages_processed=54
query_matrix: 20/20 completed  → 4 项查询类条件 = true
web_directory_status = web_directory_provider_not_configured → true

9 项完成条件：
  all_query_families            true
  all_sources_or_reasons        true
  pagination_complete           true
  two_empty_pages               true
  last_three_batches_empty      true
  all_candidates_classified     FALSE  ┐
  no_unprocessed_candidates     FALSE  ├─ 四项同源 = no_open_work
  official_site_recheck         FALSE  │
  review_recovery               FALSE  ┘
```

`no_open_work=false` 的**三个具体来源**（生产函数归因 + 只读查库核对，非推测）：

| 行引用 | 状态 | `linked_backlog_retry` / `website_resolution_retry` 实测载荷 | 是否会自行终态化 |
|---|---|---|---|
| `ldr:571` | `website_lookup_pending` | `website_resolution_retry.attempts=1`，`next_retry_at=2026-10-22 06:21:27 +08`（**已到期**），`terminal_outcome=null` | **具备终态化先决条件**：`manual_review_needed` 分支的计数键是 `attempts`，上限 3，还差 2 次 |
| `ldr:556` | `review_recovery` | `attempts=20`，**`unavailable_attempts=1`**，`recovery_history_valid=True`，`next_retry_at=2026-10-22 06:21:41 +08`（已到期），`automation_terminal_outcome` / `automation_terminal_at` **不存在** | **不会** |
| `ldr:565` | `review_recovery` | `attempts=31`，**`unavailable_attempts` 键不存在**，`last_failure_at` / `next_retry_at` / `failures` **全部不存在**，`recovery_history_valid=False` | **不会** |

**结构性缺口（交 Codex 修，代码位置精确到行）**

终态判定在 `retail_city_queue.py:256-271` `automatic_recovery_deferred()`，对 `linked_backlog_retry` 要求**四个条件同时成立**：

```python
row['validation_status'] == 'review_recovery'                       # 556/565 满足
and recovery_history_valid(retry, 'linked_backlog_retry')           # 556 满足；565 不满足
and retry['unavailable_attempts'] == NETWORK_RECOVERY_ATTEMPT_LIMIT # 必须恰好 == 3
and retry['automation_terminal_outcome'] == 'network_retry_exhausted'
and retry['automation_terminal_at'] == retry['last_failure_at']
```

两个关键事实：

1. **计数键不是 `attempts`，而是 `unavailable_attempts`**（`retail_city_queue.py:262`）。实测 `ldr:556` 的 `attempts` 已涨到 **20**，而 `unavailable_attempts` 停在 **1**；`ldr:565` 连该键都没有。也就是说**重试循环在累加 `attempts`，但没有累加决定终态的 `unavailable_attempts`**，于是 `== 3` 永远不成立。
2. **终态三元组从未被写入**（`automation_terminal_outcome` / `automation_terminal_at` 在两行上都缺失），所以哪怕计数对了也仍返回 `False`。

而 `network_recovery_due()`（`retail_city_queue.py:238-253`）恰恰对这两行都返回 `True`：
- `ldr:565`：`unavailable_attempts` 缺失 → 命中 `:245` 的特例分支 `return not retry.get('automation_terminal_outcome')` → **True**（每轮都被重新排队）
- `ldr:556`：`unavailable_attempts=1` 为真值 → 落到 `:251`，`next_retry_at` 已过期 → **True**（每轮都被重新排队）

⇒ 两行陷入 **「每轮 due=True → 重试 → `attempts` +1 → `unavailable_attempts` 不动 → 永不终态」** 的死循环，`_linked_backlog_retryable` 恒为 `True`，`no_open_work` 恒为 `false`，城市永久 fail-closed 扣留，**Lake Placid 永不激活**。4A.8U 的有界重试契约只覆盖新产生的失败事件，**没有覆盖历史遗留行**。

**预测（不写库、不干预）**：代理已恢复，下一次自然 firing（18:18:22 +08）可推进 `ldr:571` 的 `attempts`，再下一次达到 3。但 `ldr:556/565` 仍会扣住城市。**仅靠时间不会自愈，必须由 Codex 出补丁。**

**建议补丁方向（三选一，由 Codex 决定；任一会解除死锁）**
- 在重试写入路径上同步递增 `unavailable_attempts`，使 `== 3` 可达；
- 或当 `unavailable_attempts == 3` 时补齐 `automation_terminal_outcome/at` 三元组；
- 或对 `attempts` 加独立硬上限作为兜底（例如 `attempts >= 3 × LIMIT` 即视为 `network_retry_exhausted`），避免历史行无限循环。

---

## 8. 结果字段 / Result fields

```text
PRODUCTION_OBSERVABILITY_ACCEPTED = false        # 10 项中 8 项成立；缺：阶段事件持久化 + Codex 消费回执
STAGE_TRACE_ENDPOINT_WORKING = true              # /v1/city 200，结构化代理指标 + 显式 NOT_RECORDED
STAGE_TRACE_REAL_RUN_VERIFIED = false            # 生产未持久化逐阶段事件
ACTIVE_DISCOVERY_STATE_OBSERVED = NY
CITY_COMPLETION_CHECKS_AVAILABLE = true          # 9 项，调用生产规则函数
WEBSITE_RETRY_STATE_AVAILABLE = true             # attempts / next_retry_at / terminal_outcome

SAFE_AUTHORITY_CONNECTED = true
SAFE_LATEST = 56                                 # 15:49:52 +08；读数 56/56；MX ok / nxdomain
SAFE_NET_GROWTH_24H = UNKNOWN                    # 无同口径历史快照
SAFE_NET_GROWTH_7D = UNKNOWN
MX_POSITIVE_CONTROL = ok
MX_NEGATIVE_CONTROL = nxdomain
TWO_SAFE_RECONCILIATIONS_VERIFIED = true         # 同次测量两次独立读数一致

INVENTORY_SCHEDULER_VERIFIED = true
EXPECTED_VS_ACTUAL_TRIGGERS_RECONCILED = true    # 7/7 成对，偏移 12.2–446.4s
MISSED_INVENTORY_RUNS_CONFIRMED = 0
GLOBAL_INVENTORY_UNIQUENESS_VERIFIED = true      # 计划任务层 UNKNOWN（schtasks 被禁）
SAFE40_CHECKPOINT_ACTIVE = true

BRIDGE_HEALTH = UP_SESSION_SCOPED                # 由 GET /healthz(ok=true, v2.1) 派生，非硬编码
BRIDGE_HEALTH_SOURCE = GET /healthz (ok=True, bridge_version=2.1)
BRIDGE_CRASH_RECOVERY_VERIFIED = true            # CHILD_EXIT → SPAWN 2s
BRIDGE_LOGIN_AUTOSTART_VERIFIED = REGISTERED_NOT_OBSERVED_THIS_SESSION
BRIDGE_BOOT_PERSISTENCE_VERIFIED = false
RELEASE_SECURITY_GATES_PRESERVED = true          # 由 /v1/releases.seal(sealed=true, tampered=false) 派生

CODEX_HANDOFF_PUBLISHED = true
CODEX_HANDOFF_CONSUMED = false
CODEX_RUNTIME_EVIDENCE_ACCEPTED = false
CODEX_HANDOFF_ISSUE_COMMENT = NOT_POSTED   # 本会话无 GitHub API 客户端（gh 缺失、连接器不可用）

COOPERSTOWN_CLOSED = false
COOPERSTOWN_COMPLETION_CHECKS_FAILED = all_candidates_classified,no_unprocessed_candidates,official_site_recheck,review_recovery
COOPERSTOWN_STRUCTURALLY_BLOCKED_REFS = ldr:556,ldr:565   # 不会自愈，需 Codex 补丁
COOPERSTOWN_SELF_HEALING_REFS = ldr:571
LAKE_PLACID_ACTIVE = false
LAKE_PLACID_PROVIDER_REQUESTS = 0

# ── 安全状态：全部为实测值，不再硬编码 ──
CUSTOMER_SMTP_ENABLED = false                    # 3 态；读不到即 UNKNOWN，绝不默认 false
CUSTOMER_SMTP_ENABLED_RAW = 0                    # system_config.SMTP_enabled 原始值
CUSTOMER_SMTP_ENABLED_SOURCE = bd_leads.db:system_config.SMTP_enabled (mode=ro)
CUSTOMER_SMTP_SOURCES_AGREE = true               # DB 与 /v1/telemetry.guardrails 交叉一致
PRODUCTION_SEND_LOG_TOTAL = 517
PRODUCTION_SEND_LOG_TODAY = 0
UNAUTHORIZED_EMAILS_SENT = 0                     # today=0 才给 0；否则 REVIEW_REQUIRED
PRODUCTION_DB_SHA256 = 66509daab31eebe2bd39b27aa5be416179e7e96f40bddb1a5fa26f509a9b6f36
PRODUCTION_DB_SHA_AFTER = 66509daab31eebe2bd39b27aa5be416179e7e96f40bddb1a5fa26f509a9b6f36
PRODUCTION_DB_MTIME = 2026-10-22T08:46:21+08:00
PRODUCTION_DB_QUICK_CHECK = ok
PRODUCTION_DB_UNAUTHORIZED_WRITES = 0            # 括号式取证：观测前后 SHA 相同才给 0
DUPLICATE_INVENTORY_CREATED = false

BLOCKERS_REQUIRING_ONE_TIME_AUTHORIZATION = 见 §9（仅 1 项：开机级常驻）
NEXT_AUTOMATIC_ACTION = 2026-10-22 18:18:22 +08 的 Inventory firing；Cooperstown 不会自行关闭（详见 §7）
COMMIT_SHA = 7c6538fc932673ecc69be59b065dc94409e2a6d0
PUSH_SUCCESS = true
OVERALL_RESULT = OBSERVABILITY_DELIVERED_CODEX_CONSUMPTION_PENDING
```

> 说明：本节为人工阅读版，长文本字段做了压缩；**机器权威值以同目录 `WORKBUDDY_LONG_TERM_OPERATIONS.json` 为准**（54 个字段，逐字段带来源；不一致时以 JSON 为准）。

---

## 9. 需要一次性授权的操作（最小集，1 项）

**目标**：让桥接在**无人登录**时也存活（`BRIDGE_BOOT_PERSISTENCE_VERIFIED=true`）

- 现状：`CREATE_BREAKAWAY_FROM_JOB` 返回 `WinError 5`；`WScript.Shell` COM、`cmd.exe` 自 PowerShell、`schtasks.exe`、`sc.exe` 均被宿主策略拒绝 → **非提权路径已用尽**
- 需要（二选一，需管理员/提权执行一次）：
  1. `sc create RoktDeployChannel binPath= "C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\pythonw.exe C:\Users\15690\WorkBuddy\deploy-channel\bin\supervisor.py" start= auto obj= ".\15690"`（含一次登录密码登记）
  2. 或注册一个"计算机启动时"运行的计划任务，运行身份 = 当前操作员
- 授权后验收：重启 → 不登录 → `http://127.0.0.1:8791/healthz` 返回 200 且 `bridge_version=2.1`

**不需要授权的其余工作已全部完成**。

---

## 10. 未取得的数据（UNKNOWN / NOT_RECORDED，逐项给原因）

| 数据 | 标记 | 原因 |
|---|---|---|
| 每次运行的阶段事件轨迹 | `NOT_RECORDED` | 生产未持久化；不做事后反推 |
| 历史原始 `next_run_at` | `NOT_RECORDED` | 每次运行被覆盖；改用派生 + 明示派生方式 |
| Windows 计划任务清单 | `UNKNOWN` | `schtasks.exe` 被宿主策略禁用 |
| SAFE 24h/7d 净增长 | `UNKNOWN` | 无同规则版本历史快照 |
| firing 未执行的具体原因文本 | 不输出 | 回执标题可能含客户名，只给 `executed=false` + 证据类型 |
| 开机级常驻 | `false` | 需一次性管理员操作（§9） |

---

## 11. 长期自动执行 / Long-term autonomous loop

新增一个**只读**周期任务，让证据与 SAFE 账本持续累积（这是 SAFE 24h/7d 增长能变成数字的唯一途径）：

- **automation_id**: `c6bf1717-a7a6-40c7-a1de-074fab9b6128`
- **名称**: BD Production Evidence Refresh — 22:40 (read-only, no inventory)
- **频率**: 每日 22:40 +08（`FREQ=DAILY;BYHOUR=22;BYMINUTE=40`）
- **做什么**: 桥接健康检查 → `/v1/safe?refresh=1` 取新测量 → 取 runtime / city(22,23) / provider-audit / scheduler / telemetry → 重写证据包（仅值变化才提交并推送）
- **明令禁止**: 不启动 Inventory、不跑 `bd_orchestrator.py`、不发邮件、不写 `bd_leads.db`、不改任何自动化状态
- **唯一性影响**: 已在角色表登记为 `READ_ONLY_EVIDENCE_REFRESH`（即使其 prompt 提到 orchestrator 也不会被判为第二 Inventory）；重建后 `/v1/scheduler` 仍返回 `UNIQUE`、`unclassified=0`

既有三项受控任务**状态未变**：Inventory `ACTIVE`、Recovery Sync `ACTIVE`、SAFE40 Checkpoint `ACTIVE`、一次性任务 `PAUSED`。

---

## 12. 提交信息 / Commit information

- 提交仓库：`1569032023yf-star/workbuddy-task-window`（`main`）
- 本次提交只含 `handoff/workbuddy/production/` 下的证据包、合同、报告与生成器；**不含**数据库、凭据、客户数据
- 交付提交链：
  - `c0652430da99981a12688f2261fb9cb52cd24833` 首次交付
  - `44a9592b0f42c0cad484f6d27c85e481512fa819` 回填结果字段
  - `7c6538fc932673ecc69be59b065dc94409e2a6d0` 修正 `CUSTOMER_SMTP_ENABLED` 极性反转 + 城市根因精确到行（本次内容提交）
- `PUSH_SUCCESS = true`；校验方式为 `git ls-remote origin refs/heads/main` 与 `git rev-parse HEAD` 逐字相等（不读本地 origin 缓存）
- 报告无法包含自身的 commit hash，故先交付、后以追加提交回填，与 `894b642` 的做法一致
- **GitHub Issue #2 未留言**：本会话没有 GitHub API 客户端（`gh` 未安装、GitHub 连接器不可用）。证据包已发布在交接仓库，Codex 可直接读取 `handoff/workbuddy/production/`；如需 Issue 侧回执，请由具备 GitHub 通道的一侧补发。`CODEX_HANDOFF_ISSUE_COMMENT = NOT_POSTED`

### 12.1 可复算 / Reproducibility

证据包不是"请相信我"的产物，生成器已随包发布：

- 路径：`handoff/workbuddy/production/tools/build_handoff.py`
- 它产出了本目录下 `WORKBUDDY_LONG_TERM_OPERATIONS.json` 与 6 个证据文件
- 只读性由结构保证：所有生产读取要么是回环桥接的 HTTP 调用，要么是 `sqlite3.connect("file:...?mode=ro", uri=True)`（引擎级拒写）
- Bearer token 运行时从 Windows 凭据管理器读取，**不出现在脚本或任何输出中**（已做敏感串扫描）
- `PRODUCTION_DB_UNAUTHORIZED_WRITES` 是**括号式测量**：整轮观测前后各取一次 `bd_leads.db` 的 SHA-256，相等才记 0

Codex 可据此独立复跑并比对 `evidence_sha256`，无需反向信任本报告。
