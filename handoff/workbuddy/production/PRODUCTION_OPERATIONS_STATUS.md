# 生产运维状态 / Production Operations Status

- **updated_at**: 2026-10-22 16:05 +08
- **authority**: WorkBuddy（生产运维方）
- **channel**: `rokt-deploy-channel` @ `127.0.0.1:8791`，bridge **2.1**，13 operations

---

## 1. 一句话状态 / One-line status

观测面已上线并被真实生产只读验收（沙箱 40/40 + 在线 41/41）；调度经证明**没有漏跑**；SAFE 权威值 **56**；城市仍卡在 **Cooperstown**，阻塞行已精确到 3 条，其中 2 条属**有界重试契约覆盖不到的历史超额 attempts**，需 Codex 出补丁。

---

## 2. 生产水位 / Watermarks

| 指标 | 值 | 观测时间 | 来源 |
|---|---|---|---|
| SAFE（distinct `organization_key`） | **56** | 15:49:52 +08 | `/v1/safe`（读数 56/56） |
| MX 正控 / 负控 | `ok` / `nxdomain` | 同上 | `preflight_gate.query_mx` |
| leads 总数 / 带邮箱 | 1213 / 652 | 15:40 +08 | `bd_leads.db` |
| send_log 今日 / 历史 | 0 / 517（末次 2026-09-16） | 同上 | `/v1/telemetry` |
| SMTP_enabled | 0（关闭） | 同上 | `system_config` |
| 当前活动城市 | Cooperstown (NY)，`active` | 15:41 +08 | `/v1/city` |
| 下一城市 | Lake Placid (NY)，`pending`，`activatable=true` | 同上 | `/v1/city` |
| 查询族进度 | 20 / 20 completed | 同上 | `lead_discovery_query_state` |
| Provider 请求 24h | **0**，判定 `ZERO_REQUESTS_CONFIRMED` | 同上 | `/v1/provider-audit` |
| 最近 Inventory run | `inventory:2026-10-22:03b70e7a`，completed / target_met，56/50 | 05:49–05:53 +08 | `job_runs` |
| 下一次 Inventory firing | 18:18:22.823 +08 | — | `automations.next_run_at` |
| 库完整性 | `quick_check=ok`，sha256 `66509daa…f36`（今日只读未变） | 16:00 +08 | 只读双读 |

---

## 3. 城市阻塞清单 / City blockers

| ref | 状态 | attempts | 失败事件数 | 下一次到期 | 能否自行终态化 |
|---|---|---|---|---|---|
| `ldr:571` | `website_lookup_pending` | 1 / 3 | 1 | 2026-10-22 06:21:27（已到期） | 能（再 2 次） |
| `ldr:556` | `review_recovery` | **20** | 1 | 2026-10-21 22:21:41 | **不能** |
| `ldr:565` | `review_recovery` | **31** | 1 | — | **不能** |

9 项完成条件：5 项 true / 4 项 false（同源 `no_open_work`）。

---

## 4. 调度 / Scheduler

- 48h：7 次触发，7 次成对匹配，**跳过整槽 0，漏跑 0**；偏移 12.2–446.4s（均值 90.8s）
- 3 次未产生生产运行 = agent 层 fail-closed（Astrill 3213 代理死亡），**不是漏跑**
- 唯一性：`automation-1784775229336` 是唯一 `role=INVENTORY` 的 ACTIVE 自动化；`BDExecutionHost` = STOPPED/MANUAL；计划任务层 `UNKNOWN`
- SAFE40 Checkpoint：`ACTIVE`（保留，仍承担漏跑告警职责）

---

## 5. 桥接 / Bridge

| 项 | 状态 |
|---|---|
| healthz | 200，`2.1`，`test_mode=false` |
| 崩溃自愈 | 15:58:06 CHILD_EXIT → 15:58:08 SPAWN（2s） |
| 会话外常驻 | **未达成**（需 §9 的一次性管理员操作） |
| 登录自启 | `HKCU\…\Run\RoktDeployChannelSupervisor`（旧重复项 `RoktDeployBridge` 已删除） |
| 发布门禁 | 14 门禁 + 封签 + 字节级回滚；32/58/34/26 全绿 |

---

## 6. 未授权动作计数 / Unauthorized action counters

```
PRODUCTION_DB_UNAUTHORIZED_WRITES = 0
UNAUTHORIZED_EMAILS_SENT          = 0
DUPLICATE_INVENTORY_CREATED       = false
CUSTOMER_SMTP_ENABLED             = false
FORCED_CITY_STATUS_CHANGE         = 0
MANUAL_LEAD_OR_EVIDENCE_WRITE     = 0
```

本次全部操作：只读查询、只读接口代码、测试、`phase4a8u` 已部署文件**未触碰**（`discovery_service.py` `415fbe0c…`、`retail_city_queue.py` `02d04313…` 与本轮开始时一致）。

---

## 7. 需要 Codex 接手的两个工程项

1. **`linked_backlog_retry` 超额 attempts 无法终态化**（阻塞 §3 的 `ldr:556/565`）——建议：当 `attempts >= NETWORK_RECOVERY_ATTEMPT_LIMIT` 且不存在 terminal outcome 时，按 `network_retry_exhausted` 终态化，或对历史行做一次性迁移；须出正式受控发布清单。
2. **阶段事件持久化**（让 `STAGE_TRACE_REAL_RUN_VERIFIED` 可为 true）——固定事件类型 + 有界错误类别 + 脱敏摘要，不做任意日志面。

## 8. 需要用户/管理员的一次性动作

见 `WORKBUDDY_LONG_TERM_OPERATIONS.md` §9：安装 Windows 服务或注册"计算机启动时"计划任务，使桥接在无人登录时存活。
