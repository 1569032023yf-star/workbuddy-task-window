# 生产运维状态 / Production Operations Status

- **updated_at**: 2026-10-29 11:55 +08
- **authority**: WorkBuddy（生产运维方）
- **mode**: Phase 0 只读刷新（线下总路线.md §Phase 0）。本轮**未**启动采集、**未**重启桥接、**未**改配置、**未**改动任何自动化状态。
- **supersedes**: 2026-10-22 16:12 版（该版 SAFE=56、活动城市=Cooperstown，均已过时）

---

## 1. 一句话状态 / One-line status

生产采集链路健康且在真实推进：48 小时内 7 次触发全部成功、0 次漏跑，最新运行真实打出 3 页 Provider 请求；SAFE 从 62 升到 **63**（双读一致）；Cooperstown 已于 **10-23 正式关闭**（旧摘要的判断是错的）；Lake Placid 推进到 **14/20** 查询族。唯一仍未闭环的仍是**无人登录时的持久化**——桥接和采集都绑定在用户会话上。

---

## 2. 生产水位 / Watermarks

| 指标 | 值 | 观测时间 | 来源 |
|---|---|---|---|
| SAFE（distinct `organization_key`） | **63**（读数 63/63） | 11:48:26 +08 | `_count_safe_ready_pool`（与 10-28 同一入口，可比） |
| SAFE 变化 | 较 10-28 22:52 快照 **+1**；较 7 天前 +7 | — | 严格 24h 差值为 `UNKNOWN`（无对应时点快照） |
| SAFE 盘中轨迹 | 62 → **63**(00:14) → **64**(06:41) → **63**(11:48) | — | ⚠️ 非单调：今晨曾到 64 后回落 1，勿按持续增长解读 |
| MX 正控 / 负控 | `ok` / `nxdomain` | 11:49 +08 | `preflight_gate.query_mx` |
| leads 总数 | 1242 | 11:49 +08 | `bd_leads.db` |
| send_log 历史 / 今日 | 517 / **0**（末次 2026-09-16） | 同上 | `send_log` |
| 客户 SMTP | 关闭 | 同上 | 全库未见启用键；发送权 23 条最后建于 2026-09-15 |
| 当前活动城市 | Lake Placid (NY)，`active` | 同上 | `retail_city_queue` |
| 查询族进度 | **14/20**（剩 6 个） | 同上 | `lead_discovery_query_state` |
| 最近 Inventory run | `inventory:2026-10-29:8f789080`，completed / target_met，62/50 | 10:30:16–10:46:42 | `job_runs` |
| 该 run 的 Provider | **3 页 / 24 结果，全部 ok** | 10:37:20 | `provider_request_audit` |
| 下一次 Inventory firing | **2026-10-29 16:58:50** | — | `automations.next_run_at` |
| 库完整性 | `quick_check=ok`，sha256 `7f2ab53b…5e65` | 11:49 +08 | 只读 |

24h 新客户漏斗：发现 17 家商户 / 16 个独立组织 / 新增 13 条 lead / **2 个第一方官方邮箱**（上一版是 10 / 9 / 8 / 1）。

---

## 3. 城市 / Cities

| 城市 | 队列状态 | 正式完成判据 | 说明 |
|---|---|---|---|
| Cooperstown (22) | `search_matrix_exhausted` | **9/9 通过** | 实际完成于 **2026-10-23 00:49 +08**。10-28 摘要说它「无法自行关闭」——该判断在发布时already 过时 |
| Saratoga Springs (21) | `search_matrix_exhausted` | 9/9 通过 | 2026-10-08 完成 |
| Lake Placid (23) | `active` | **4/9 通过** | 14/20 族；未过项：`all_query_families`、`all_sources_or_reasons`、`pagination_complete`、`two_empty_pages`、`last_three_batches_empty` |
| Ithaca (20) | `search_matrix_exhausted` | **5/9 通过** | ⚠️ 队列状态与完成契约不一致：4 项未过。**仅报告，未修**——改城市状态属生产写入 |

Lake Placid 的 `last_error` 是 `Page.inner_text` 超时（累计 2 次），属单页级抖动，不是链路故障：同一时点 Provider 审计全为 `ok`。

---

## 4. 调度 / Scheduler

- 48h：**7 次触发，7 次成功，0 次失败，0 漏槽**；每次都产生了对应生产 run
- 触发间隔**不是固定 6 小时**：调度器在运行完成时重新锚定，所以间隔 = 6h + 上次运行时长（残差 ≤ 12s）。用绝对 6h 网格对账会误报漏跑
- 行动层唯一性：`automation-1784775229336` 是唯一 `role=INVENTORY` 的 ACTIVE 自动化
- Windows 任务层（本轮首次核实）：`BD-Outreach`=DISABLED、`BD-PreSend`=DISABLED、`BD-PostSend`=**READY**
  - PostSend 每日 00:10 跑 `--stage post-send --live`，今天 00:10:01 跑过，结果 0。该阶段只做收件箱扫描 + 发送对账 + 看板，**函数体内零 SMTP 调用**，保持 READY 不产生客户发送
- `BDExecutionHost` 服务 = STOPPED（僵尸注册：`pythonservice.exe` 不存在、模块已退役）。**不得启动**

---

## 5. 桥接 / Bridge

| 项 | 状态 |
|---|---|
| 监听 | **无**（本轮未启动；上次健康 2026-10-28 22:40:59，最后心跳 22:53:10） |
| 实现完整性 | `channel_config.json` 与 `allowed_scope.json` **仍双双对上封印** |
| 已注册发布 | 4 个，本轮**无新增** |
| 会话内健康 | 是（历史：3 秒起监听、`/healthz` 200、bridge 2.1、`test_mode=false`） |
| 跨调用存活 | **否**（`CREATE_BREAKAWAY_FROM_JOB` = WinError 5；`schtasks`/`reg` 被宿主阻断） |
| 开机级持久化 | **未验证**（`HKCU\Run` 已注册、命令正确，但从未观测到它拉起进程） |

桥接不在不影响本轮证据：7 份状态文件全部直接取自 `bd_leads.db`（只读）与磁盘文件，不依赖 `/v1/*`。

---

## 6. 网络 / Network

- 生效代理 `http://127.0.0.1:7877`（Clash/Mihomo，mixed HTTP+SOCKS5），`.env` sha256 `ab350e09…`，**本轮未改动**
- 出口实测：经 7877 取 `generate_204` → **204 / 0.687s**
- `BD_MX_HTTPS_PROXY` 仍指向已死的 3213。`query_mx` 走直连 DNS 兜底，正负控均正确。**仍未迁移，属授权范围外**
- **非交互出口未验收**：会话内可用 ≠ 登出后可用

---

## 7. 未授权动作计数 / Unauthorized action counters

```
PRODUCTION_DB_UNAUTHORIZED_WRITES = 0
UNAUTHORIZED_EMAILS_SENT          = 0
DUPLICATE_INVENTORY_CREATED       = false
CUSTOMER_SMTP_ENABLED             = false
AUTOMATION_STATE_CHANGED          = false
FORCED_CITY_STATUS_CHANGE         = 0
MANUAL_INVENTORY_TRIGGER          = 0
BRIDGE_STARTED_THIS_CYCLE         = false
```

本轮全部操作：只读 SQL（`mode=ro`）、读取 `workbuddy.db` 的临时副本、读取磁盘上的封印/日志、写交接仓库文件。

---

## 8. 需要 Codex 接手 / For Codex

1. **Ithaca 状态不一致**：队列写 `search_matrix_exhausted`，但完成契约 4 项不过。需要判定是历史脏行还是契约需要兼容。
2. Provider 诊断候选 `8d63d2d` / 发布包 `30fccc9` 的三个文件**仍不在发布白名单**，不得自行扩容。
3. 远端 HEAD 已前进到 `9421c4f1`，最新两个提交都在取消日志（Phase 1 主题），未见开启生产派发。

## 9. 需要用户/管理员的一次性动作 / One-time action

把 `deploy-channel` supervisor 装成 Windows 服务或"计算机启动时"任务（最小权限、非 LocalSystem），使桥接与采集脱离登录会话存活。除此之外当前没有阻塞在用户侧的事项。
