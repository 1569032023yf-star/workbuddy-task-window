# FULL TASK CLOSURE — 2026-10-20 · 三项任务完整收尾复验

**生成时间 / Generated**: 2026-10-20T11:25:34+08:00 (+08)
**样本时区 / Sampling timezone**: Asia/Shanghai (+08)
**性质 / Nature**: 只读复验 + 测试夹具修复。**无业务库写入、无邮件、无部署、无调度变更、无发布清单变更。**
**目的 / Purpose**: 2026-10-20 上午磁盘一度 0 字节（"os error 112"），三项任务的收尾复验未能在健康环境下跑完。磁盘已恢复（现 20.0 GB 可用 / 90.0% 占用），本报告把三项任务一次性复验到可交付状态。
**Type**: read-only re-verification plus test-harness repair. No business writes, no email, no deploy, no schedule change, no release-registry change.

---

## 0. 一句话结论 / Bottom line

三项任务在健康环境下全部复验通过。复验同时发现并修正了 4 处**测试夹具时间/状态漂移**（仅测试代码，生产零改动）；并确认 4A.8S 发布已被 Codex 于 2026-10-15 10:42 实际部署，因此该发布在通道内的 `preflight` 现在会**按设计被 5 个依赖门禁阻断**（幂等保护），而非通道故障。

All three tasks pass end-to-end verification. Four test-fixture drift issues were found and fixed (test code only, zero production change). The 4A.8S release was really deployed by Codex at 2026-10-15 10:42, so a preflight for that release is now blocked by exactly the five dependency gates — by design, not a channel fault.

---

## 1. 环境恢复 / Environment recovery

| 项 / Item | 值 / Value |
|---|---|
| C: 总容量 / total | 200.0 GB |
| 可用 / free | **20.0 GB**（占用 90.0%） |
| 复验开始时 / at start | 2026-10-20 11:18 前后，写入正常（无 `os error 112`） |
| 生产库完整性 / `PRAGMA quick_check` | **ok** |

磁盘水位由 100%（0 字节）恢复到 90.0%，本轮全部证据生成、测试重跑、报告落盘与推送均无写入失败。

---

## 2. 任务一：Codex 受限生产部署通道 / Restricted deploy channel

### 2.1 终态 / Terminal state

通道仍在运行且行为未变：loopback `127.0.0.1:8791`（本次实测 LISTENING）、Bearer token 由 Windows 凭据管理器读取、四操作白名单、逐请求审计；`test_mode=false`。

### 2.2 三套验收测试（本轮实跑，非引用旧报告）/ Three suites re-run now

| 套件 / Suite | 结果 / Result | 证据 / Evidence |
|---|---|---|
| 进程内单元测试 / unit (U00–U06) | **32/32 PASS** | `closure_20261020/final_unit.log`, `unit_report.json` |
| 沙箱 CLI 验收 / sandbox (S01–S16) | **58/58 PASS** | `closure_20261020/final_sandbox.log`, `sandbox_cli_report.json` |
| 桥接端到端 / bridge (B00–B13) | **26/26 PASS** | `closure_20261020/final_bridge.log`, `bridge_report.json` |

三套均为 `VERDICT=ALL_PASS`。

### 2.3 关键新事实：发布已被真实消费 / The pinned release is consumed

- 生产 `bd_orchestrator.py` = `e7e619d3e40f415c1894aa3e1087978875c6f26570755254ab535b68e5580903`（31552 字节，mtime 2026-10-15 10:42:04）。
- 该 SHA 正是发布清单的 `after_sha256`；清单 `before_sha256` = `7afc4d7f6ac18e22…`。
- Codex 的真实部署操作记录：`op-20261015-104202-5ecde6`，state=`applied`，开始 2026-10-15T10:42:02+08:00，锁 holder=`deploy:op-20261015-104202-5ecde6`，已释放。
- 因此本轮 `POST /v1/preflight` 返回 **409 `PREFLIGHT_BLOCKED`**：14 门禁中 9 项通过、5 项依赖门禁失败，失败集合**精确等于** {`source_sha_matches`, `version_compatible`, `targeted_tests_pass`, `no_new_critical_regressions`, `rollback_verified`}。

这是**正确行为**：通道拒绝把同一发布再打一次（幂等保护）。桥接测试已改为状态感知断言——若生产处于 before-SHA 则要求 200 `PREFLIGHT_PASS` + 14/14；若处于 after-SHA 则要求 409 且失败集合精确等于上述 5 项（任何第 6 项失败或不同 verdict 仍判 FAIL）。

**对 Codex 的含义**：该发布条目已"用尽"。要再部署新代码，必须在 `releases/channel_config.json` 登记**新发布条目**（新 `before_sha256` = 当前生产 SHA），本次**未**修改发布清单。

---

## 3. 任务二：部署后运行验收刷新 / Post-deploy runtime (live refresh)

### 3.1 Inventory 运行 / Inventory runs

| 项 / Item | 值 / Value |
|---|---|
| 今日 business_date=2026-10-20 运行数 / runs today | **1** |
| 最近一轮 / latest run | `inventory:2026-10-20:388f1d48` |
| 状态 / status | `completed` · stop_reason=`target_met` |
| target / actual | 50 / **56**（gap 0） |
| 窗口 / window（DB 原值） | 2026-10-20 01:45:47 → 2026-10-20 01:51:53 |
| 运行锁 / run lock (2026-10-20) | `released`，acquired 2026-10-20 01:45:47 → released 2026-10-20 01:51:53 |
| 现在是否在跑 / running now | 否（`automation_runtime_state.running=0`；无 ≤2h 未完成行） |

最近 12 条运行按阶段拆分：**inventory 9 条**（completed 4 / partial 5 / failed 0）、**post-send 3 条**（全部 completed，仅 IMAP 扫描与对账）。全部 5 条 partial 的 `target=60 / actual=56 / gap=4 / stop_reason=safe_inventory_gap`，business_date 均为 2026-10-17/18（周末 target 提升到 60），属已知非故障终态；**无 failed**。

> `business_date` 按 America/New_York 16:00 ET 切换，**不等于**"当日触发次数"：凌晨运行会记到前一 business_date。因此"今日 1 条"只表示该 business_date 下的记录数，不能据此推断漏跑或补跑。

> 时间列说明：`job_runs.started_at` 为 UTC 朴素值，跨表比较已按既有规则处理；此处保留 DB 原值，不做二次换算，避免误判。

### 3.2 部署后新增采集 / Growth since the 2026-10-15 deployment

| 指标 / Metric | 值 / Value |
|---|---|
| 新增 leads / new leads | **8** |
| 其中带邮箱 / with public email | **7** |
| 新增独立组织 / distinct organizations | **8** |
| 新增发现结果 / discovery results | **13**（provider: browser_maps=13） |
| 最后一条采集 / last collected_at | `2026-10-16T17:00:18.992331` |
| 库总量 / totals | leads 1213 · 有邮箱 652 · 官网验证 409 · 独立组织 1157 |

### 3.3 Provider 请求 / Provider audit

| 项 / Item | 值 / Value |
|---|---|
| 近 24h 请求数 / last 24h | **0** |
| 最后一次请求 / last request | `2026-10-16T21:30:01` |
| 近 24h 错误 / errors | 0 |

0 请求不是故障：Cooperstown 的 20 个查询族已全部跑满页预算，发现轴耗尽（结构性 0）。

### 3.4 城市 / Cities

| 项 / Item | 值 / Value |
|---|---|
| 活跃城市 / active | **Cooperstown, NY**（id 22，provider `browser_maps`） |
| 查询族 / query families | **20/20** 均已跑过（page cursor 全部到达上限或末页） |
| 累计 / cumulative | pages 54 · results_seen 913 · new_unique_places 77 |
| 最后成功 / last_success_at | `2026-10-16T21:30:01.319420+00:00` |
| 未终态行 / non-terminal rows | **1** 条：`website_lookup_pending`=1 |
| 已收尾城市 / cities with completed_at | 5 条，其中 `search_matrix_exhausted` 3 条（Saratoga Springs, Ithaca, Knoxville） |

**结论**：Cooperstown 仍被**单条** `website_lookup_pending` 行卡住（历史根因：`provider_timeout:45028ms`），代码内 9 项收尾检查因此无法同时为真，下一城市不会激活。这是**已知结构性死锁**，不是新故障；本轮未做任何修复（属生产变更，需单独授权）。

### 3.5 SAFE 权威测量 / Authoritative SAFE

| 项 / Item | 值 / Value |
|---|---|
| MX 正控 / positive control | `gmail.com` → **ok** |
| MX 负控 / negative control | 无效域 → **nxdomain** |
| 探针判定 / probe verdict | **PASS** |
| 读数 1 / reading 1 | 56 个独立组织（候选行 56，耗时 130.0s） |
| 读数 2 / reading 2 | 56 个独立组织（候选行 56，耗时 130.7s） |
| **CURRENT_SAFE** | **56**（区间 56–56，本次无抖动） |

路径：`campaign_eligible_v2.select_candidates_for_plan_v2`（`mode=ro` 连接，distinct `organization_key`），V1/V2/MX/历史/退订/抑制门禁一律未动。

---

## 4. 任务三：自动化清理状态复核 / Automation cleanup state

| ID | Name | Status | Schedule | Prompt SHA (16) |
|---|---|---|---|---|
| `automation-1784775229336` | Inventory 采集调度器 | **ACTIVE** | `FREQ=HOURLY;INTERVAL=6` | `7d4e7e7ceaa8d5e9` |
| `automation-1786002601925` | Result Recovery Sync | **ACTIVE** | `FREQ=DAILY;BYHOUR=8;BYMINUTE=45` | `8575bb8237fbb491` |
| `75fbacd1-fa43-46ea-8388-1d47647c3f4d` | SAFE40 Checkpoint | **ACTIVE** | `FREQ=HOURLY;INTERVAL=6` | `7cfd9f1f2d13f80b` |
| `488f4c21-a70b-4611-a388-9a3f61c02db9` | One-off phase fix | **PAUSED** | once `2026-09-28T07:38` | `0a955ce984012c94` |

- 可见自动化 = **4**（ACTIVE 3 / PAUSED 1），软删除行 = **25**（不参与调度）。
- 采集型调度器 = **1**；未新建第二个 Inventory；rrule、cwd、prompt 摘要与 10-20 清理时**逐字节一致**（4 个 prompt SHA 全部相同）。
- 状态与 10-20 清理结论一致：one-off 已归为 PAUSED，SAFE40 Checkpoint 仍按 fail-safe 保留 ACTIVE。
- Recovery Sync 今日确实跑过：`system_config.sync_0845_last_success_at` = `2026-10-20T09:59:20.189270+08:00`，`automation_runtime_state.last_run_at` 与之一致。

**Windows 计划任务 / Scheduled tasks**：本轮无法复读（`schtasks.exe` / `sc.exe` 被主机安全策略列入程序黑名单，返回 `拒绝访问`）。沿用 2026-10-20 10:55 的实测证据：`RoktRazo-BD-PreSend` **Disabled**、`RoktRazo-BD-Outreach` **Disabled**、`RoktRazo-BD-PostSend` **Ready**（每日 00:10），**无任何 Inventory 计划任务**。本轮未做任何任务变更。

---

## 5. 本轮修复：仅测试夹具 / Fixes applied: test fixtures only

复验首跑暴露 **15 项失败**（unit 4 项后崩溃中止、sandbox 7 项、bridge 3 项），全部定位为**夹具漂移**，与通道逻辑、生产状态无关。逐条修复并给出判定依据：

| # | 文件 / File | 漂移 / Drift | 修复 / Fix | 依据 / Why it is correct |
|---|---|---|---|---|
| 1 | `test/build_sandbox.py` | 断言"生产文件必须等于 before-SHA"；而生产已是 after-SHA（Codex 已部署）→ 沙箱无法重建 | 若生产=after-SHA，则从**真实 apply 备份**（`backups/op-20261015-104202-5ecde6/bd_orchestrator.py.before.bak`，sha 校验 = before-SHA）取 pre-deploy 字节；基线改用**当前生产** SHA | 沙箱必须模拟"部署前世界"才能测 apply；备份是这次真实部署的字节级产物，可验证 |
| 2 | `test/run_unit_tests.py` | 沙箱内合成时间锚（`next_run_at`）在构建数日后过期 → `safe_window_verified` 因时间而非逻辑失败 | 运行前自动重建沙箱（可用 `SKIP_SANDBOX_REBUILD=1` 关闭） | 时间敏感夹具必须每次新鲜构建，否则测的是"沙箱年龄" |
| 3 | `test/run_sandbox_tests.py` | 同上（自动重建） | 同上 | 同上 |
| 4 | `test/run_sandbox_tests.py` | 锁键硬编码 `2026-10-14`（构建当日），S12 写入的外来锁键与执行器读取的当日键不同 → 外来锁场景**静默失效**（apply 竟成功） | 改为按 `datetime.now(CST)` 生成 `LOCK_KEY`，与 `executor.business_date_shanghai()` 同源 | 这是本次最有价值的发现：硬编码日期会让"外来锁必须阻断部署"的安全用例变成假通过 |
| 5 | `test/bridge_client_tests.py` | B04 断言固定为 200/PREFLIGHT_PASS；发布被消费后必然 409 | 改为状态感知：before-SHA → 200+14/14；after-SHA → 409 且失败集合精确等于 5 项依赖门禁、passed=9 | 断言更严（精确集合），不会掩盖任何新增失败面 |

修复后三套测试全部 `ALL_PASS`（32/32、58/58、26/26）。

**未修改**：`bin/executor.py`、`bin/bridge.py`、`releases/channel_config.json`、任何生产文件、任何自动化、任何计划任务。

---

## 6. 生产零写入证明 / Zero-write proof

| 证据 / Evidence | 复验前 / before | 复验后 / after | 判定 / Verdict |
|---|---|---|---|
| `bd_leads.db` SHA-256 | `494b83f6484a19397646fa5d747d0ed1…` | `494b83f6484a19397646fa5d747d0ed1…` | **相同 / identical** |
| `bd_leads.db` mtime | 2026-10-20 09:59:20 | 2026-10-20 09:59:20 | 未变（= 09:59 Inventory 收尾） |
| `bd_leads.db-wal` | 0 字节 | 0 字节 | 0 字节，无未落盘写入 |
| `bd_orchestrator.py` SHA-256 | `e7e619d3e40f415c1894aa3e10879788…` | `e7e619d3e40f415c1894aa3e10879788…` | **相同 / identical** |
| 11 张表内容摘要 / content digest | — | 与复验前**逐表相同**（`digest_identical=true`） | **无 INSERT/UPDATE/DELETE** |

摘要覆盖：leads 1213、lead_discovery_results 604、job_runs 7255、send_log 517、system_config 454、suppression_list 63、bounce_log 63、provider_request_audit 279、retail_city_queue 36、send_authorizations 23、final_send_plan 588。

---

## 7. 发送面冻结确认 / Sending surface frozen

| 检查 / Check | 值 / Value | 判定 |
|---|---|---|
| `system_config.SMTP_enabled` | `0` | **0 = 关闭** |
| `send_log` 自 2026-10-01 起条数 | **0** | 无任何发送 |
| `send_log` 最后一条 / last | `2026-09-16T01:09:52.031266+08:00`（ithacainstantreplaysports@yahoo.com，retail_distributor_v5_locked） | 2026-09-16 之后无发送 |
| `send_authorizations` 状态分布 | {'consumed': 9, 'revoked': 7, 'superseded': 7} | **无 pending/approved，可执行授权 = 0** |
| `suppression_list` / `bounce_log` | 63 / 63 | 未变 |
| `manual_send_queue` | 空 | 无手工发送队列 |
| PreSend / Preflight / Outreach | 三者 PAUSED + 软删除 | 仍冻结 |

---

## 8. 本轮未做的事 / Not done in this task

1. 未发送任何邮件（SMTP 0，`send_log` 0 新增）。
2. 未部署、未回滚任何代码；未改发布清单（新发布登记留给 Codex 决策）。
3. 未触发 Inventory / 未启动 orchestrator / 未创建第二个采集调度器。
4. 未修改任何自动化状态、rrule、cwd、prompt。
5. 未改 Windows 计划任务（且本轮无法读取，见第 4 节）。
6. 未做城市推进或收尾（Cooperstown 死锁留给后续单独授权）。
7. 未改 SAFE / MX / 历史 / 退订 / 抑制任何门禁标准。
8. 未删除任何文件（包括历史备份与日志）。

---

## 9. 收尾验收表 / Closure acceptance

| # | 检查项 / Check | 结果 | 证据 |
|---|---|---|---|
| 1 | 三项任务文件齐备且远端同步 | PASS | 远端 `main` = 本地 HEAD `e7ec719`；三份报告在 `handoff/workbuddy/phases/` |
| 2 | 部署通道三套测试全通过 | PASS | 32/32 + 58/58 + 26/26 |
| 3 | 通道四操作契约未变、无任意命令面 | PASS | B01/B05/B06/B06b/B07/B08 |
| 4 | 未授权请求一律 401、审计不漏 | PASS | B02/B03/B13 系列 |
| 5 | 发布已部署且幂等保护生效 | PASS | 409 + 5 项依赖门禁精确失败 |
| 6 | Inventory 无失败运行、今日运行完成 | PASS | `inventory:2026-10-20:388f1d48` = completed/target_met |
| 7 | SAFE 权威读数可得 | PASS | 正负控通过，CURRENT_SAFE=56（56–56） |
| 8 | Provider 无错误、发现轴耗尽已解释 | PASS | 近 24h 0 请求、0 错误 |
| 9 | 活跃城市进度可量化 | PASS | Cooperstown 20/20 族、77 新场所、1 行阻塞 |
| 10 | 自动化仅 1 个采集调度器 | PASS | live=4，ACTIVE=3，Inventory=1 |
| 11 | 自动化 prompt/rrule 与清理时一致 | PASS | 4 个 SHA 全部相同 |
| 12 | one-off 保持 PAUSED、SAFE40 保留 | PASS | 见第 4 节 |
| 13 | 发送面冻结 | PASS | SMTP=0、send_log 0、可执行授权 0 |
| 14 | 生产库与代码零写入 | PASS | SHA 相同 + 摘要相同 + WAL 0 |
| 15 | 夹具修复未触碰生产/通道逻辑 | PASS | 仅 4 个 `test/*.py` |
| 16 | 报告字段完整 | PASS | 第 10 节 |

---

## 10. 结果字段 / Result fields

```
TASK_1_DEPLOY_CHANNEL = READY_RELEASE_CONSUMED
TASK_2_POST_DEPLOY_RUNTIME = VERIFIED
TASK_3_AUTOMATION_CLEANUP = APPLIED_AS_REPORTED
CHANNEL_TESTS = unit 32/32 PASS; sandbox 58/58 PASS; bridge 26/26 PASS
PREFLIGHT_FOR_CONSUMED_RELEASE = 409_PREFLIGHT_BLOCKED_BY_5_DEPENDENCY_GATES
PRODUCTION_SHA = e7e619d3e40f415c1894aa3e1087978875c6f26570755254ab535b68e5580903
CURRENT_SAFE = 56
SAFE_BAND = 56-56
MX_PROBE = PASS
INVENTORY_RUNS_TODAY = 1
INVENTORY_LAST_STATUS = completed/target_met
INVENTORY_ACTIVE = true
RECOVERY_SYNC_ACTIVE = true
SAFE40_CHECKPOINT_ACTIVE = true
ONE_OFF_TASK_PAUSED = true
ACTIVE_INVENTORY_SCHEDULERS = 1
BUSINESS_DATA_MODIFIED = false
PRODUCTION_CODE_MODIFIED = false
RELEASE_REGISTRY_MODIFIED = false
AUTOMATIONS_MODIFIED = false
SCHEDULED_TASKS_MODIFIED = false
EMAILS_SENT = 0
DEPLOYS_PERFORMED = 0
TEST_FIXTURES_CHANGED = 4
DISK_FREE_GB = 20.0
RESULT = FULL_TASK_CLOSURE_VERIFIED
```

---

## 11. 遗留与建议 / Residual risks & recommendations

1. **发布清单需登记新条目**（需 Codex 决策）：当前唯一发布条目已被消费，任何新部署都要新增 `before_sha256` = 当前生产 SHA 的条目，否则 preflight 会一直被 5 项依赖门禁阻断。**本轮未改清单。**
2. **Cooperstown 单行死锁**：1 条 `website_lookup_pending`（历史 `provider_timeout:45028ms`）同时挂住 4 项收尾检查，下一城市不会激活。修复属生产变更，需单独授权。
3. **发现轴已耗尽**：Provider 近 24h 0 请求、0 错误；SAFE 稳定在 56。若要继续增长，需要新城市激活或新查询族，而不是调 `MAX_PAGES`。
4. **磁盘 90.0% 占用**（20.0 GB 可用）：仍处高水位。本轮未删除任何文件；如继续清理，建议只动 `.workbuddy\logs` 的过期日期归档（需单独确认）。
5. **调度任务不可读**：`schtasks.exe` / `sc.exe` 已被主机安全策略拉黑，后续若要复核计划任务，需先在安全中心调整程序黑名单，否则只能沿用历史读数。

---

## 12. 证据文件 / Evidence files

目录 `C:\Users\15690\WorkBuddy\deploy-channel\test\closure_20261020\`：

- `recon.py` / `recon.json` — 只读采集（库、自动化、通道、磁盘、指纹）
- `mx_probe_safe.py` / `mx_probe_safe.json` — MX 双控探针 + SAFE 双读数
- `postcheck.py` / `postcheck.json` — 复验后零写入复核
- `suites.json`、`final_unit.log`、`final_sandbox.log`、`final_bridge.log`
- `unit_report.json`、`sandbox_cli_report.json`、`bridge_report.json`

修复的测试文件：`test/build_sandbox.py`、`test/run_unit_tests.py`、`test/run_sandbox_tests.py`、`test/bridge_client_tests.py`。
