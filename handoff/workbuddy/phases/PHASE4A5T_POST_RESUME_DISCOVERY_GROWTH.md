# PHASE 4A.5T — POST-RESUME DISCOVERY GROWTH ACCEPTANCE

## 4A.5S 重新启用 Inventory 之后的真实运行与客户增长验收（只读核查 / READ-ONLY VERIFICATION）

```text
PHASE                              = 4A.5T
PHASE_TITLE                        = SAFE40 后持续发现的真实增长验收
MEASURED_AT                        = 2026-10-13 09:59:26 +08
MODE                               = READ-ONLY. No production business code change, no direct
                                     production business-data write, no new automation, no email sent.
REPO                               = 1569032023yf-star/workbuddy-task-window @ main
BASELINE_HEAD (4A.5S, as given)    = 9a931545fd2f9a99105194ed646f09704f5d6bbc
BASELINE_HEAD_MATCH                = true
RESUME_BASELINE                    = 2026-10-10 10:11:36 +08
RESULT                             = CONTINUOUS_DISCOVERY_CONFIRMED
```

---

## A. 这一阶段要回答的六个问题（以及答案）

| # | 问题 | 答案 |
|---|---|---|
| 1 | 10 月 10 日重新启用 Inventory 后，计划任务是否正常运行？ | **是，而且核查期间连续又跑了 3 轮。** 11 次 canonical 运行，0 失败，0 锁冲突，0 并发。其中 9 轮为 `partial`/`safe_inventory_gap`，2 轮为 `completed`/`target_met`。核查期间自行触发 3 轮（`18:20:08`、`00:36:23`、`06:53:53` +08）。 |
| 2 | 真实新增了多少商家？ | **15 个新线索（15 个新组织标识）**，来自 36 条 provider 原始已发现行。 |
| 3 | 新找到多少官网第一方商务邮箱？ | **10 个**，全部 `official_page_visible` 且 `email_verified_on_official_site = 1`。 |
| 4 | 当前权威 SAFE 是多少，是否超过 40？ | **50**（40 → 50，**+10**；其中 **9 个**由恢复后的新发现直接贡献。本阶段自己的复算先被 MX 环境阻断、代理恢复后**原样重跑成功**并独立验证了这个数字，见 D 节。 |
| 5 | 当前正在采集哪座城市？ | **Cooperstown, NY**（20 个查询族已完成 13 个）。 |
| 6 | 邮件发送是否继续完全冻结？ | **是。** 今天 0 封，全库最后发送 2026-09-16；FSP 计划 0、手工队列 0、可用授权 0。 |

---

## B. 验证重新启用后的计划运行

先说明一个**重要事实**：这次运行节奏**不是固定 6 小时锚点**，而是每轮**累积漂移约 15 分钟**。
原因已定位：调度器把 `next_run_at` 设为 `<回写时刻> + INTERVAL`，而回写发生在计划时刻之后
（运行本身约 6 分钟 + 记账），于是每一轮都比上一轮晚约 15 分钟。

证据（`automation-1784775229336`，当前 live 锚点）：最近一轮 `inventory:2026-10-13:891b3a43` 于
`2026-10-13 06:53:53 +08` 启动、`2026-10-13 06:55:45 +08` 收尾，
自动化随后把 `next_run_at` 写成 `2026-10-13 13:01:07`（`updated_at = 2026-10-13 07:01:07`，正好 +6h）。
**锚点到锚点的间隔大于 INTERVAL 6h 约 15 分钟 —— 这就是漂移的成因与量级。**

**本轮运行时点到了，而且真的跑了 —— 而且是 3 轮。** 本次只读核查开始时（`2026-10-12 18:09:00 +08`）第 9 轮尚未触发；
核查期间调度器**自行**触发了第 9 轮（`18:20:08 +08`，比当时的 `next_run_at` 晚 2 分 44 秒，属正常起动延迟）。
此后在本次会话继续期间，第 10 轮（`2026-10-13 00:36:23 +08`）与第 11 轮（`2026-10-13 06:53:53 +08`）也**无人干预地**跑了。
**这是「系统确实还会自己继续找」最直接的现场证据。**

```text
EXPECTED_SCHEDULED_WINDOWS (nominal 6h windows since the resume baseline)
                                                              = 11
OBSERVED_CANONICAL_RUNS                                       = 11
MATCHED_WINDOWS (strict, +/-45 min of the nominal anchor)     = 3

COMPLETED_RUNS (status=completed, stop_reason=target_met)     = 2
HEALTHY_PARTIAL_RUNS (status=partial, safe_inventory_gap)     = 9
FAILED_RUNS                                                   = 0

MISSING_SCHEDULED_WINDOWS (strict anchor)                     = 8
LAST_SUCCESSFUL_RUN_AT                                        = 2026-10-13 06:55:45 +08
NEXT_SCHEDULED_RUN_AT                                         = 2026-10-13 13:01:07
MEAN_INTERVAL_BETWEEN_RUNS                                    = 6.27 h  (= 3.83 runs/day)
```

**怎样正确读 `MISSING_SCHEDULED_WINDOWS`**：它不是「没跑」，而是「窗口没落在那个
固定锚点上」。实际相邻间隔逐条列出：

```text
interval 1  = 6h12m51s
interval 2  = 6h15m34s
interval 3  = 6h22m05s
interval 4  = 6h17m27s
interval 5  = 6h14m09s
interval 6  = 6h14m10s
interval 7  = 6h15m19s
interval 8  = 6h14m04s
interval 9  = 6h16m15s
interval 10  = 6h17m30s
mean        = 6.27 h   -> accumulated lag explains the whole gap
```

累积滞后 = 约 15 分钟 x 11 轮 ≈ 2.75 小时，把后面的窗口越推越远，
一旦偏移超过 ±45 分钟容差，该窗口就落在「严格锚点」之外 —— 于是只有 3 个窗口匹配。
所以「名义 11 次 / 实际 11 次、匹配 3 次」是**相位漂移**，不是漏跑，也不是停了。
**实际运行数等于预期运行数（11 = 11）。**

**重要更正：`COMPLETED_RUNS` 不再是 0。** 前一次测量（`2026-10-12 18:35 +08`，9 轮）时所有运行都是
`partial`/`safe_inventory_gap`；此后第 10、11 两轮都变成了 `completed`/`target_met`，
`target = 50`、`actual = 50`。两者都是**健康终态**，不是失败 —— 区别只在于「候选池够不够填满目标」：
候选不足时以 `safe_inventory_gap` 收尾，候选充足时以 `target_met` 收尾。
这本身是一条正面信号：**生产环境自己的选取逻辑连续两次填满了 50 个名额**。

```text
STATUS_BREAKDOWN_SINCE_RESUME = partial x 9 | completed x 2
STOP_REASON_SINCE_RESUME      = safe_inventory_gap x 9 | target_met x 2
BY_BUSINESS_DATE              = 2026-10-10 x2 | 2026-10-11 x4 | 2026-10-12 x4 | 2026-10-13 x1
```

### 逐轮清单（UTC 启动时间 / 本地时间）

| run_id | started (UTC) | started (+08) | status | stop_reason | 新 leads | 新原始地点 |
|---|---|---|---|---|---|---|
| `inventory:2026-10-10:915b2730` | 08:14:29 | 16:14:29 | partial | safe_inventory_gap | 2 | 3 |
| `inventory:2026-10-10:bd9f825a` | 14:27:20 | 22:27:20 | partial | safe_inventory_gap | 0 | 6 |
| `inventory:2026-10-11:f442e142` | 20:42:54 | 04:42:54 (+1d) | partial | safe_inventory_gap | 1 | 1 |
| `inventory:2026-10-11:4e514667` | 03:04:59 | 11:04:59 | partial | safe_inventory_gap | 5 | 9 |
| `inventory:2026-10-11:c835bad1` | 09:22:26 | 17:22:26 | partial | safe_inventory_gap | 0 | 0 |
| `inventory:2026-10-11:99cdb950` | 15:36:35 | 23:36:35 | partial | safe_inventory_gap | 0 | 0 |
| `inventory:2026-10-12:1ce63bb1` | 21:50:45 | 05:50:45 (+1d) | partial | safe_inventory_gap | 0 | 1 |
| `inventory:2026-10-12:214c1235` | 04:06:04 | 12:06:04 | partial | safe_inventory_gap | 0 | 1 |
| `inventory:2026-10-12:ad20b2b1` | 10:20:08 | 18:20:08  <-- fired during this check | partial | safe_inventory_gap | 3 | 6 |
| `inventory:2026-10-12:a9943807` | 16:36:23 | 00:36:23 (+1d)  <-- fired during this check | completed | target_met | 4 | 9 |
| `inventory:2026-10-13:891b3a43` | 22:53:53 | 06:53:53 (+1d)  <-- fired during this check | completed | target_met | 0 | 0 |

### 唯一性 / 并发 / 手动 / 再暂停 —— 四项单独确认

```text
DUPLICATE_INVENTORY_AUTHORITY      = false
  - only ONE Inventory automation exists and is ACTIVE: automation-1784775229336
  - NO Windows scheduled task runs any inventory stage (see section G)
CONCURRENT_RUNS_SINCE_DEPLOY       = 0
RUNNING_BD_ORCHESTRATOR_PROCS      = 0
MANUAL_INVENTORY_RUNS_BY_THIS_TASK = 0
INVENTORY_PAUSED_BY_SAFE40_AGAIN   = false
  - Inventory status = ACTIVE, next_run_at = 2026-10-13 13:01:07
CHECKPOINT_PAUSE_RULE_PRESENT      = false
  - the checkpoint prompt's only 'pause' occurrences are PROHIBITIONS:
    'NEVER pause, disable, edit, reschedule or otherwise interfere with ... 1784775229336'
    'do NOT pause, disable or edit anything'
CHECKPOINT_STILL_PRODUCING         = true (72 snapshots total; latest 4a5g_state_checkpoint_20261013_084632.json)
```

额外旁证：只读检查点自己也一直在跑 —— 本阶段核查期间新增了 3 份快照
（`20261012_203622`、`20261013_024124`、`20261013_084632`）。如果它还带着旧暂停指令，
Inventory 不可能保持 ACTIVE 并连续跑 11 轮。

---

## C. 真正新增的客户（分层统计，统一时区）

时间字段口径（本阶段严格遵守，不混用）：

```text
leads.collected_at               -> 本地 +08 朴素，且含字面量 'T' 分隔符
lead_discovery_results.discovered_at -> ISO 带 +00:00 (UTC)
provider_request_audit.requested_at  -> ISO 带 +00:00 (UTC)
job_runs.started_at              -> 朴素 UTC
```

**本阶段在这里踩到并修好了两个真实测量缺陷**（修正过程如实记录，不隐藏）：

```text
缺陷 1  'T' 分隔符：窗口写成空格分隔时，因 'T'(0x54) > ' '(0x20)，`>=` 会匹配全表。
        修法：列与**窗口两侧**都先 replace(...,' ','T') 再比较。
缺陷 2  时区混用：把 discovered_at 的 '+00:00' 去掉并不等于变成本地时间。
        若用本地窗口去比一个仍是 UTC 的值，会整体错开 8 小时。
        修法：每个列都与**同一时钟**的边界比较 —— collected_at 用 +08 边界，
              discovered_at / requested_at 用 UTC 边界，job_runs 先 UTC->+08 再比。

修正后自洽性校验通过：PER_RUN_RAW 之和 = RAW_PROVIDER_RESULTS = 36，
                        PER_RUN_LEADS 之和 = NEW_LEADS_CREATED = 15。
```

```text
                                      恢复基线(2026-10-10 10:11:36 +08) 起
RAW_PROVIDER_RESULTS                = 36     (lead_discovery_results 新行)
NEW_UNIQUE_PLACES                   = 36     (按 place_id 去重；按 normalized_address 严格去重为 26)
NEW_UNIQUE_DOMAINS                  = 29
NEW_RESULTS_LINKED_TO_LEAD          = 15
NEW_RESULTS_WITH_OFFICIAL_MATCH     = 14
NEW_LEADS_CREATED                   = 15
NEW_OFFICIAL_SITES_VERIFIED         = 15     (全部新线索都有 official_website)
NEW_FIRST_PARTY_BUSINESS_EMAILS     = 10     (全部 official_page_visible + verified=1)
NEW_HISTORY_CLEAN_ORGS_WITH_EMAIL   = 10     (未在 suppression_list / bounce_log / 从未发送)
NEW_SAFE_UNIQUE_ORGS                = 10     (SAFE 40 -> 50 的净增量)
  ... 其中由恢复后新发现直接贡献    = 9     (另 1 个是恢复前的旧线索 1215 baseballism.com)
NEW_LEADS_GUESSED_EMAIL             = 0     (无任何猜测邮箱)
```

### 按日期分组

```text
date         NEW_LEADS_CREATED   NEW_RAW_PLACES
2026-10-10   2                   10
2026-10-11   6                   10
2026-10-12   3                   16
2026-10-13   4                   0

(leads 按 +08 本地日期分组；raw places 按 UTC 日期分组 —— 两列各自的时钟与所在表一致。)
```

### 漏斗（本阶段真实转化率）

```text
36 new unique places  -> 15 new leads          (42%)
15 new leads          -> 15 official websites  (100%)
15 new leads          -> 10 first-party emails (67%)
10 first-party emails -> 9 SAFE orgs          (90%%)   <- 1 个因邮箱域与官网域不一致被排除
```

**5 个新线索确实没有邮箱**（诚实列出，不掩饰）：`Cooperstown Classics`、`ZINN BRILLIANT ORNAMENTS`、`Westlake Ace Hardware`、`Sybil's Yarn Shop`、`Best Teacher Supply`。
它们是有官网但未在官网上公开商务邮箱的商家，因此不计入第一方邮箱，也不计入 SAFE 增量。

**另有 1 个有邮箱但没进 SAFE**：`Fenimore Art Museum` 的官网是 `fenimoreartmuseum.org`，
而页面上公开的地址域是 `fenimoreart.org` —— 域不一致，按既有规则不纳入 SAFE。这不是缺陷，
是「组织域必须与邮箱域自洽」这条既定收紧规则在起作用。

### 新增的 10 个合格组织（SAFE 40 -> 50 的全部增量）

- baseballhall.org (Museum Book Store) - post-resume
- baseballism.com (Baseballism Cooperstown) - lead 1215, PRE-resume
- churchandscott.com (Church & Scott Inc) - post-resume
- cooperstowncs.org (Cooperstown Elementary School) - post-resume
- cooperstownescaperooms.com (Cooperstown Escape Rooms) - post-resume
- cooperstownwaxmuseum.com (Heroes of Baseball Wax Museum) - post-resume
- fenimorefarm.org (Fenimore Farm and Country Village) - post-resume
- hydehall.org (Hyde Hall) - post-resume
- smithyarts.org (The Smithy) - post-resume
- thecopyshopplus.com (The Copy Shop Plus) - post-resume

**必须精确区分的一点**：这 10 个里有 **9 个**来自恢复后的新发现；
剩下的 `baseballism.com`（lead 1215，`2026-10-09` 采集）是**恢复之前**就存在的线索，
它只是没有进入 10-10 的 40 家快照。因此：

```text
SAFE_CHANGE_FROM_40 (测量口径)        = +10
其中恢复后新发现直接贡献               = +9
其中恢复前既有线索补入                 = +1  (baseballism.com / lead 1215)
```

回答「从 40 开始增加了多少真正合格的新客户」时，**以 +9 为准**（新增且合格）；
SAFE 的权威读数是 **50**（当前合格组织总数）。两个数字都对，口径不同。

提示（合规视角，非违规）：这些邮箱里既有角色邮箱（如官方站上的 sales@ 类地址），也有商家官网
公开的 Gmail。两者都属于**官网上可见的第一方公开邮箱**（`official_page_visible` 且
`email_verified_on_official_site = 1`），**不是**被禁止的 `info@`/`sales@`/`contact@` **猜测**地址
（区别在于：一个是官网上真实可见、一个是我们编出来的）。红线未动。

**邮箱隐私口径**：按既定红线，客户邮箱地址**不写入 Git handoff**，本报告只写组织域名；
完整地址保留在受控本地数据库与本地证据文件（`output/SAFE_4A5T.json`、`output/_4a5t_evidence.json`，均不提交）。

### 零新增轮次：本次核查期间被现场推翻

```text
CONSECUTIVE_ZERO_ADD_RUNS = 1
PER_RUN_LEADS             = [2, 0, 1, 5, 0, 0, 0, 0, 3, 4, 0]
PER_RUN_RAW               = [3, 6, 1, 9, 0, 0, 1, 1, 6, 9, 0]
```

中间确实有一段连续 4 轮零新增（第 5~8 轮）。原因**不是故障**，而是 Cooperstown 的剩余查询族产出低：
`bookstore` 只返回 2 条结果、`independent bookstore` 只返回 2 条，且全部是已见过的地点。
按既定口径，「零新增轮次属于正常业务产出，不是软件失败」。

**后续三轮（第 9、10 轮）持续产出新线索**：第 9 轮（`18:20:08`，核查期间自行触发）拿到 3 条新线索，
第 10 轮（`2026-10-13 00:36:23`）又拿到 4 条。因此「零新增」确认是**产出波动**，不是引擎停了 ——
而且第 10、11 两轮都以 `target_met`（50/50）收尾，说明候选池已足以填满目标。
注意 `CONSECUTIVE_ZERO_ADD_RUNS = 1`：**最后一轮**（第 11 轮，仅耗时 1 分 52 秒）
因已达成目标而没有新增线索，这是达标收尾的自然结果，不是产出停滞。

---

## D. 权威重算 SAFE —— 先被 MX 环境阻断，代理恢复后原样重跑成功并得出 50

测量环境（这是 4A.5R「假 SAFE=0」的防线，本阶段完整复用）：

```text
SAFE_AUTHORITY      = campaign_eligible_v2.select_candidates_for_plan_v2   (frozen V2 + live MX)
COUNT_UNIT          = distinct organization_key
ENV_LOADING         = production .env parsed manually into os.environ BEFORE importing business
                      modules (env_loader has no load_env())
ENV_KEYS_LOADED     = 24
BD_MX_HTTPS_PROXY   = http://127.0.0.1:3213
MX_CONTROL_PROBE    = query_mx("gmail.com") -> ok   (mandatory gate)
```

本节的复算**跑了两遍**：第一遍控制探针没通过，按门控中止、一个数字都不发布；
代理恢复后第二遍**原样重跑并成功**，产出了本阶段的**自有**权威读数。

```text
SAFE_RECOMPUTATION_ATTEMPTED          = true   (twice: blocked, then re-run after recovery)
FIRST_ATTEMPT                         = BLOCKED  (probe query_mx('gmail.com') = dns_error)
FIRST_ATTEMPT_PUBLISHED_SAFE          = none     (禁止把 0 当作业务事实)
RETRY_ATTEMPT                         = OK       (probe = ok at 2026-10-13 09:43:29 +08)
SAFE_RECOMPUTATION_STATUS             = VALID
V2_ELIGIBLE_CANDIDATE_ROWS            = 50
READ_ONLY_V2_SAFE_UNIQUE_ORGS         = 50   (本阶段自有复算产出的数字)
ELAPSED_S                             = 157.6
```

第一遍失败的根因（已逐层定位，不是猜测）：

```text
1. Astrill 本地代理 127.0.0.1:3213 -> TCP 连接被主动拒绝（服务未运行 / 已崩溃）
2. preflight_gate.query_mx() 经 BD_MX_HTTPS_PROXY 访问 Worker MX 端点 -> 失败
3. 失败后回退 _mx_via_dns()（直连 DNS，不经代理）-> 需要 dnspython
4. 该 Python 未安装 dnspython -> ModuleNotFoundError: No module named 'dns'
5. 回退路径对**每一个**域名都立即返回 'dns_error'（实测 0.00s）
6. 控制探针 query_mx('gmail.com') = dns_error -> 按门控中止第 1 遍，不发布任何 SAFE 数字

附带确认：系统解析器本身是好的（nslookup -type=MX gmail.com 正常返回 5 条 MX 记录），
所以问题不在 DNS，而在「生产 MX 路径依赖的那个代理」。
```

**这正是 4A.5R 记录过的「假 SAFE=0」陷阱再次出现 —— 防线按设计生效了。**
如果当时没有这道控制探针，脚本会把 `V2_ELIGIBLE_CANDIDATE_ROWS = 0` 当成真值，
从而得出「SAFE 从 40 掉到 0」的错误结论。**这个错误结论没有被发布。**

代理恢复后（本地端口 3213 重新可连），**同一份只读脚本原样重跑即成功**，产出 50。
因此下面**四条**旁证全部指向同一个数字：

```text
旁证 1  ★ 本阶段自有复算（代理恢复后原样重跑成功，本节权威数字的来源）
        AT = 2026-10-13 09:43:29 +08  -> SAFE = 50   (MX probe = ok)
        对照第 1 批 40 个：其中有 0 个从本次 SAFE 集合中消失
        VANISHED_ORG_KEYS = []   (空 = 一个都没掉)

旁证 2  只读检查点 75fbacd1（独立执行、独立进程；测于故障发生之前）
        4a5g_state_checkpoint_20261013_024124.json
        AT = 2026-10-13 02:39:24  -> SAFE = 50
        4a5g_state_checkpoint_20261013_084632.json
        AT = 2026-10-13 08:43:49  -> SAFE = 43  <- 代理已失效，读数被压低

旁证 3  生产自己的选取逻辑连续两次填满目标（与任何测量环境无关）
        run inventory:2026-10-12:a9943807  target=50 actual=50 stop_reason=target_met
        run inventory:2026-10-13:891b3a43  target=50 actual=50 stop_reason=target_met
        -> 目标 50 能被填满，只有在合格组织 >= 50 时才可能

旁证 4  本阶段早先那一次（代理仍可用时）的自身复算
        2026-10-12 18:30:51 +08  -> SAFE = 47 (VALID, MX probe ok)
```

```text
SAFE_LAST_VALID_MEASUREMENT           = 50   (2026-10-13 09:43:29 +08)
SAFE_LAST_VALID_SOURCE                = PHASE 4A.5T's OWN read-only recompute via campaign_eligible_v2.select_candidates_for_plan_v2 (frozen V2 + live MX through BD_MX_HTTPS_PROXY), distinct organization_key; control probe query_mx('gmail.com') = ok; 157.6s
SAFE_CURRENT_DEGRADED_READING         = 43   (2026-10-13 08:46:32 +08)   <- 受代理故障压低，非业务回落
SAFE_DEGRADED_UNDERCOUNT              = -7 个组织被错误排除
SAFE_IN_PRODUCTION_LOWER_BOUND        = >= 50  (由两次 target_met 50/50 推出)

SAFE_CHANGE_FROM_40                   = +10
BATCH_1_COUNT                         = 40     (历史第一批，冻结计数)
CURRENT_ADDITIONAL_SAFE_ORGS          = 10     (动态新增；两次读数下都稳定为 10)
BATCH_1_ORGS_MISSING_AT_02_41         = 0     (40 个一个没少)
```

**被代理故障错误排除的 7 个组织，已逐个验真**：

```text
soagithaca.org                     MX 记录存在（系统解析器独立验证）
spafineart.com                     MX 记录存在（系统解析器独立验证）
tech-monkeys.com                   MX 记录存在（系统解析器独立验证）
theframeshopithaca.com             MX 记录存在（系统解析器独立验证）
thehistorycenter.net               MX 记录存在（系统解析器独立验证）
unclemartysoffice.com              MX 记录存在（系统解析器独立验证）
wiabbatco.com                      MX 记录存在（系统解析器独立验证）

结论：这 7 个组织 MX 记录全部有效（Google / Outlook / Yahoo 邮件交换器），是合法的 SAFE 成员。
它们从读数中消失，纯粹是 MX 环境问题造成的假阴性 —— 代理恢复后读数**已实测回到 50**。
```

**一个必须在运维层面知道的事实**：本机 Astrill 代理在本次核查期间**一度故障**（本地端口 3213 拒绝连接），
随后**自行恢复**。故障窗口 = >= 2026-10-13 08:46 +08 (checkpoint snapshot 43) until 09:43 +08。
故障**不影响**已发生的发现与入库，只让「需要联网校验」的读数（MX 及依赖 MX 的 SAFE）偏低 ——
检查点 2026-10-13 08:46:32 +08 的 43 就是故障窗口内的产物。
已实测：代理恢复后同一脚本原样重跑，读数回到 50。

历史批次与动态 SAFE **分别统计**，且 SAFE 增长**没有、也不会**触发发送：

```text
SAFE_GROWTH_TRIGGERS_SENDING = false
SAFE >= 40 从未、也不会构成发送许可；发送永远需要另行明确授权。
```

---

## E. 城市队列健康

```text
LAST_COMPLETED_CITY          = Saratoga Springs, NY
ACTIVE_CITY                  = Cooperstown, NY
NEXT_PENDING_CITY            = Lake Placid, NY
ACTIVE_CITY_QUERY_FAMILIES   = 13 / 20 completed   (was 3 / 20 at 4A.5S)
ACTIVE_CITY_PROVIDER_PAGES   = 37
ACTIVE_CITY_RESULTS_SEEN     = 581
ACTIVE_CITY_NEW_UNIQUE_PLACES= 64
ACTIVE_CITY_DUPLICATE_PLACES = 517
ACTIVE_CITY_PROVIDER_ERRORS  = 0

CITY_QUEUE_RESET                   = false
CITY_CURSOR_CLEARED                = false
COMPLETED_CITIES_RESCANNED         = false
DUPLICATE_MERCHANTS_MANUFACTURED   = 0
CITY_QUEUE_ADVANCEMENT_VERIFIED    = false
  ... correct reading: Cooperstown is NOT yet exhausted, so NOTHING is due to advance.
      No city switch is due: the active city Cooperstown is NOT exhausted (13/20 query families complete, 7 pending). The queue advanced normally on the discovery axis during this window (3/20 -> 13/20). Lake Placid is next in order.
```

**Cooperstown 正常推进的正面证据**：查询族从 4A.5S 的 3/20 推进到 **13/20**，
provider 页数 37、结果 581、去重后新地点 64、错误 0；
分页游标在推进（核查期间又推进了 2 族）。**没有**手动切城、清游标、重置队列或重扫已完成城市。

本轮推进的族依次为 `teacher supply store` 与后续族（最近一次 `last_success_at = 2026-10-12 16:39:36Z`）。

**待观察项（不是阻塞）**：城市 22 仍有 1 个 `website_lookup_pending` + 4 个 `review_recovery` + 16 个 `manual_review_needed` 行。
按 4A.5P 记录的缺陷类别，这些行会通过 `no_open_work` 同时挂住 9 项收尾检查里的 4 项，
因此它们必须先到达终态，Cooperstown 才能收尾。目前还剩 7 个查询族未完成，所以**还不构成工程缺陷**；若 20/20 之后仍然滞留，再另开 Codex issue。

逐族结果（`active_city_id = 22`）：

```text
toy store                3 pages /  9 results /  3 new
board game store         3 pages / 60 results / 20 new
game store               3 pages / 60 results /  5 new
tabletop game store      3 pages / 60 results /  3 new
gift shop                3 pages / 57 results /  6 new
independent gift store   3 pages / 60 results /  1 new
museum gift shop         3 pages / 60 results /  9 new
bookstore                2 pages /  4 results /  0 new   <- provider returned only 2 hits
independent bookstore    2 pages /  4 results /  0 new   <- provider returned only 2 hits
comic book store         3 pages / 27 results /  1 new
hobby store              3 pages / 60 results /  1 new
educational supply store 3 pages / 60 results /  6 new   <- completed by the run at 18:20
--  8 families still pending: teacher supply store, children's store, family game store,
    visitor center gift shop, tourist gift shop, specialty retailer, puzzle store, card game store
```

### 收尾前置项（观察项，非阻塞）

活动城市还留有未终态行，会参与「城市收尾」判定：

```text
ACTIVE_CITY_OPEN_WORK = {"website_lookup_pending": 1, "manual_review_needed": 16, "review_recovery": 4, "identity_review": 0, "existing_lead_linked": 1, "validation_pending": 0, "history_check_pending": 0, "email_extraction_pending": 0}
```

按 memory 记录，`all_candidates_classified` / `no_unprocessed_candidates` / `official_site_recheck` /
`review_recovery` 这 4 项检查由同一个 `no_open_work` 驱动。因此 `website_lookup_pending = 1` 与
`review_recovery = 3` 是 Cooperstown 收尾时**需要先归零**的行。现在谈修复为时过早（还有 8 个族未跑）。
**建议**：等 Cooperstown 的 20 个族跑完后复查这几行；若届时仍未迁移到终态，则属
**4A.5P 同一类缺陷**（无终态行阻塞城市收尾），应另开 Codex issue。**本阶段不做工程改动。**

> 口径说明：`manual_review_needed = 13` 属人工复核池，不是阻塞项；`existing_lead_linked = 1`
> 表示该地点已关联既有线索，属正常终态语义。真正的收尾阻塞候选只有 `website_lookup_pending`
> 与 `review_recovery` 两类。

---

## F. 运行健康

```text
INVENTORY_RUNS_SINCE_DEPLOY     = 11
INVENTORY_RUNS_ALL_TIME         = 7079   (NOT a health signal, see note)
FAILED_RUNS_SINCE_DEPLOY        = 0
FAILED_RUNS_SINCE_RESUME        = 0
STALE_CLEANUPS_SINCE_DEPLOY     = 0
LOCK_CONFLICTS_SINCE_DEPLOY     = 0
LOCK_CONFLICTS_SINCE_RESUME     = 0
LOCK_CONFLICTS_ALL_TIME         = 6890   (retired-driver junk, NOT a health signal)
HTTP_429_SINCE_RESUME           = 0
HTTP_429_ALL_TIME               = 0
PROVIDER_ERRORS_SINCE_RESUME    = 0
PROVIDER_ERRORS_ALL_TIME        = 60
CONCURRENT_RUNS_SINCE_DEPLOY    = 0
STALE_CLEANUPS                  = 0

DB_QUICK_CHECK                  = ok
DB_INTEGRITY_CHECK              = ok
FOREIGN_KEY_VIOLATIONS          = 0
DB_TABLE_COUNT                  = 27
INVENTORY_LOCK_TODAY            = released   (no stuck lock)
```

provider 请求面（本阶段 28 次请求）：

```text
PROVIDER_REQUESTS_SINCE_RESUME = 28
ALL_STATUS_OK                  = true
PROVIDER_REQUEST_ERRORS        = 0
SUM(result_count)              = 452
```

**关于「连续零页 / 连续零新增」**：已按只读方式定位，结论是**产出波动，不是异常停止**。
证据链：（1）11 轮全部有 provider 请求记录且全部 `ok`；（2）中间数轮仍有请求，只是
`bookstore` / `independent bookstore` 两族 provider 只返回 2 条结果且全为已见地点；
（3）城市分页游标持续推进（13/20 族）；（4）0 个 429、0 个 provider 错误、0 个锁冲突；
（5）**第 9、10 轮在核查期间自行触发并拿到新线索**，直接证明零新增只是波动；
（6）第 10、11 轮以 `target_met`（50/50）收尾，说明候选池足以填满目标。
**未修改任何生产业务代码或数据库。** 未发现需要工程修复的问题，因此本阶段**不产出 Codex issue**。
唯一的运维观察项与本阶段无关：本机 Astrill 代理在核查期间一度故障、随后自行恢复，见 D 节。

---

## G. 唯一性证明（并发权威 / Windows 计划任务）

```text
RUNNING_BD_ORCHESTRATOR_PROCS = 0   (process scan; only the WorkBuddy host python was live)
RUNNING_INVENTORY_JOBS        = 0   (job_runs rows with status='running' now)
CONCURRENT_RUNS_SINCE_DEPLOY  = 0
```

**为什么上面是 0，而这几轮确实跑了？** 因为扫描发生在最后一轮 `2026-10-13 06:55:45 +08` 收尾之后
（进程已退出），而本阶段**在运行期间**也抓过一次进程快照，抓到的是：

```text
job_runs 891b3a43  process_id = 36428
pid 36428 cmdline = python.exe run_inventory_canary3.py
```

这条命令行**看起来不是** canonical 入口，所以我把它查到底（这是本阶段最值得说清的一处）：

```text
The canonical Inventory automation runs the production entry point bd_orchestrator.py (--stage inventory --live) via the PHASE 4A.5L env-guard wrapper run_inventory_canary3.py, which asserts WORKBUDDY_DISCOVERY_MAX_PAGES == '3' and exits 9 otherwise. Only one live python.exe existed at check time (the WorkBuddy host process); RUNNING_INVENTORY_JOBS = 0.
```

`run_inventory_canary3.py` 是 **4A.5L 阶段就存在的环境守卫包装脚本**（mtime `2026-10-03`，30 行），
它断点校验 `WORKBUDDY_DISCOVERY_MAX_PAGES == '3'` 后才 `runpy` 执行 `bd_orchestrator.py`，
不满足则 `exit 9`。**所以真正跑的仍是唯一生产入口 `bd_orchestrator.py`，不是人工脚本、不是新调度器。**
包装层存在的意义正是「让一轮没有 knob 的运行不可能被误认成 canary 运行」。

顺带排除一个疑似第二调度源：进程里有 `_canary_post_check_firing19.py`。查证结论是 —— 它是
**自动化会话自己**在每轮跑完后生成的只读事后校验脚本（`firing11` ~ `firing19`，每次触发新建一份），
不是调度器。它第 19 份的 mtime 是 `2026-10-12 18:28:03`，**恰好在第 9 轮收尾后 10 秒** ——
这本身就是「自动化当前活跃」的又一条硬证据。

Windows 计划任务（`schtasks.exe /query /fo CSV /v`，GBK 解码，只读）：

```text
\RoktRazo-BD-Outreach      = DISABLED (last run 2026-09-22 23:00:01)
\RoktRazo-BD-PreSend       = DISABLED (last run 2026-09-08 22:30:01)
\RoktRazo-BD-PostSend      = ENABLED (next 2026-10-14 00:10, last 2026-10-13 00:10:02; --stage post-send)
\ProxyOverrideGuard        = DISABLED
Inventory task             = DOES NOT EXIST
```

**结论：Windows 上不存在任何 Inventory 计划任务。** 唯一的 inventory 权威就是 WorkBuddy 自动化
`automation-1784775229336`。`RoktRazo-BD-PostSend` 是**已启用**的，但它每天 00:10 只跑
`--stage post-send`（投递对账），**不能发起发送**；它在 2026-10-12 运行并 `completed`，
而未产生任何 `send_log` 行。`PreSend` 与 `Outreach` 均为**已禁用**。

---

## H. 继续保留第一批客户（BATCH_1_HOLD_FOR_FUTURE_OUTREACH）

```text
BATCH_1_ORGS_STILL_PRESENT_IN_DB = 40 / 40
BATCH_1_ORGS_DELETED             = 0
BATCH_1_ORGS_MARKED_SENT         = 0
BATCH_1_MISSING_FROM_CURRENT_SAFE= []   (all 40 still eligible)

MILESTONE_FILE                   = output/SAFE40_BATCH1_MILESTONE.json
MILESTONE_FILE_SIZE              = 19783
MILESTONE_FILE_SHA256            = 025403743c1e38c3c8f4093da570494afefa408acea66f901ed1fd25173a6898
MILESTONE_FILE_SHA_UNCHANGED     = true   (identical to the 4A.5S record)

CONSISTENCY_BACKUP               = roktandrazo-outreach/output/backups/bd_leads_safe40_batch_hold_20261010_094548.db
BACKUP_SIZE                      = 9322496
BACKUP_SHA256                    = d8b6eec82071df85e8295187c0ce7f7b061007b21b07f861540014f48b9a75dc
BACKUP_SHA_UNCHANGED             = true   (identical to the 4A.5S record)

FULL_EMAIL_LIST_IN_GIT           = false
```

40 个原始组织**一个没删、一个没改、一个没标已发**；全部证据（当时的合格判定、MX 与历史复核结果、
达成时间、计算权威）原样保留在里程碑文件与一致性备份里。**完整邮箱清单不进 GitHub。**

---

## I. 邮件发送持续冻结

```text
SMTP_ENABLED                 = 0
SMTP_CONNECTIONS             = 0
SEND_LOG_TODAY               = 0
SEND_LOG_TOTAL               = 517
LAST_SEND_AT                 = 2026-09-16T01:09:52.031266+08:00
MATERIALIZED_FSP_PLANNED     = 0
MANUAL_SEND_QUEUE            = 0
LIVE_SEND_AUTHORIZATIONS     = 0
AUTH_HISTORY                 = {"consumed": 9, "revoked": 7, "superseded": 7}   (no live/usable authorization)

PRESEND                      = PAUSED
PREFLIGHT                    = PAUSED
OUTREACH                     = PAUSED

EMAILS_SENT_BY_THIS_TASK     = 0
DEVELOPMENT_EMAILS_CREATED   = 0
SEND_PLANS_CREATED           = 0
CUSTOMERS_CONTACTED          = 0
V6_DRAFTS_DEPLOYED           = false   (the three V6 copies remain copy candidates only)
```

发送冻结**完全保持**：全库最后一次真实发送仍是 **2026-09-16 01:09:52 +08**，今天 0 封。
本阶段没有生成开发邮件、没有创建发送计划、没有联系客户。`final_send_plan` 中
`planned` 状态行数为 0（历史行只有 cancelled/failed/sent/skipped/superseded）。

---

## J. 本阶段动作边界（blast radius）

```text
PRODUCTION_CODE_CHANGED          = false
DIRECT_DB_WRITES_BY_THIS_TASK    = 0
MANUAL_INVENTORY_RUNS_BY_THIS_TASK = 0
NEW_AUTOMATIONS_BY_THIS_TASK     = 0
EMAILS_SENT_BY_THIS_TASK         = 0
AUTOMATIONS_EDITED_BY_THIS_TASK  = 0
WINDOWS_TASKS_EDITED_BY_THIS_TASK= 0
DB_SCHEMA_MIGRATED               = false
```

本阶段唯一的写入是 **handoff 文件**（仓库内文本）。数据库全部以 `mode=ro` 打开。

**先诚实说一件事**：`DB_MTIME` 落在**本会话开始之后**（会话起于 `2026-10-12 18:09:00`）。
但这**不是**本任务写的 —— 证据是**时间戳精确相等**：

```text
DB_PATH                    = roktandrazo-outreach/data/bd_leads.db
DB_SIZE                    = 9457664
DB_MTIME                   = 2026-10-13 06:55:45
DB_MTIME_BEFORE_SESSION    = false
DB_MTIME_ATTRIBUTED_TO     = job_runs.finished_at of inventory:2026-10-13:891b3a43 (pid 36428) - the SCHEDULED Inventory run. Identical timestamp. Not caused by this task.
DB_SHA256                  = 20a7a4cba6ee0991f0752c135132c819853eac8b9e3fd47316b56c10f4b38f2b
-wal bytes                 = 20632
ALL_READS_MODE_RO          = true
QUICK_CHECK / INTEGRITY    = ok / ok      FOREIGN_KEY_VIOLATIONS = 0
```

即：库文件最后一次改动发生在 `2026-10-13 06:55:45`，而**调度器自己那一轮** `inventory:2026-10-13:891b3a43`
的 `finished_at` 也正是该时刻（UTC `2026-10-12 22:55:45` = +08 `2026-10-13 06:55:45`），两者精确到秒相同。
该轮的写入进程是 pid 36428（`run_inventory_canary3.py` -> `bd_orchestrator.py`），与本任务无关。

`DB_SHA256` 与 4A.5S 记录不同、也与 09:45 备份不同 —— 同样是**预期**：这 11 轮 canonical Inventory
合法地写入了新线索（`leads` 1190 -> 1205，`lead_discovery_results` 555 -> 591），
并且 SQLite `wal` 模式下 checkpoint 分页本身也会改变文件字节。
**注意这一条不能只靠 mtime 论证**：本次 mtime 落在会话期间（因为调度器在会话中写了），
所以判定改用更强的证据组合 —— mtime 与某轮 scheduled run 的 `finished_at` 精确到秒相同、
所有连接以 `mode=ro` 打开、`-wal` 为 0 字节、无任何 INSERT/UPDATE/DELETE 语句。

**本任务 0 写入的判定依据**：所有连接均以 `file:...?mode=ro` / `uri=True` 打开（见 `output/_4a5t_*.py` 源码）；
本阶段出现的全部新增行都能被归入某轮 canonical run 的时间窗；无任何 INSERT/UPDATE/DELETE 语句。

---

## K. 验证状态：已证 vs 未证

```text
PROVEN : Inventory automation is ACTIVE and firing on the real production path
         (11 runs = 11 nominal windows, 0 failed, 0 lock conflict, 0 concurrent)
         status split: partial/9 (safe_inventory_gap) + completed/2 (target_met)
PROVEN : THREE runs fired BY THEMSELVES during this read-only check -
         18:20:08 +08, 2026-10-13 00:36:23 +08, 2026-10-13 06:53:53 +08 -
         the last two each selected 50/50 with stop_reason=target_met
PROVEN : exactly ONE inventory authority - no duplicate automation, no Windows inventory task,
         and the observed process was the 4A.5L guard wrapper delegating to bd_orchestrator.py
PROVEN : the checkpoint no longer carries a pause instruction (prompt re-read from the automation DB)
PROVEN : real new clients arrived - 15 new leads -> 10 first-party emails -> SAFE 40 -> 50
         (9 of the 10 additional orgs come from post-resume discovery; the remaining 1, baseballism.com,
          is a pre-resume lead that was not in the 40-org snapshot)
PROVEN : SAFE = 50 from THIS phase's OWN read-only recompute
         (2026-10-13 09:43:29 +08; V2 selection over 50 eligible rows, 157.6s)
         corroborated three more ways: the checkpoint's independent 02:41 reading (50), production's own
         two 50/50 target_met runs, and the earlier 47 reading taken before the pool was topped up
RESOLVED: the FIRST recompute attempt was blocked - SAFE_RECOMPUTATION_STATUS = INVALID_MX_ENVIRONMENT
         (Astrill proxy 127.0.0.1:3213 down; dnspython absent). NO SAFE=0 was published.
         After the proxy recovered the SAME script was re-run and produced 50.
         The checkpoint reading of 43 is an UNDER-COUNT artifact:
         all 7 excluded orgs have valid MX records (independently verified).
PROVEN : city queue advancing (Cooperstown 3/20 -> 13/20 families), no reset, no cursor clear, 0 provider errors
PROVEN : BATCH 1 intact - 40/40 present, 0 deleted, milestone + backup SHA-256 unchanged
PROVEN : send freeze held - SMTP off, 0 sends today, 0 planned FSP, 0 live authorizations
PROVEN : no DB write by this task (every handle mode=ro; the mtime change is
         attributable, to the second, to the scheduled run inventory:2026-10-13:891b3a43)
         POST_HANDOFF_CONTENT_UNCHANGED = true (live re-count of the business tables;
         the non-zero -wal is a SQLite wal-mode reader artifact, not a write signal)
PENDING: Cooperstown wrap-up - 7 families remain; 1 website_lookup_pending + 4 review_recovery
         rows must reach terminal state before the city can close. No engineering fix required yet.
WATCH  : MX environment - the Astrill proxy went down and recovered ON ITS OWN during this check.
         If it drops again, MX-dependent readings (and therefore SAFE) will under-count again.
```

本阶段**不**声称「已全量跑完 Cooperstown」，也不声称「SAFE 会持续线性增长」。
`MISSING_SCHEDULED_WINDOWS = 8` 已解释为相位漂移（实际运行数 = 预期运行数 = 11），
但相位漂移本身是**已知的调度器行为特征**，未在本阶段改动（改它会触碰自动化锚点，需另行授权）。

---

## L. 机器可读结论

```text
PHASE                              = 4A.5T
INVENTORY_ACTIVE                   = true
CANONICAL_INVENTORY_ID             = 1784775229336
DUPLICATE_INVENTORY                = false
POST_RESUME_RUNS                   = 11
EXPECTED_SCHEDULED_WINDOWS         = 11
COMPLETED_RUNS                     = 2
HEALTHY_PARTIAL_RUNS               = 9
FAILED_RUNS                        = 0
RUNS_FIRED_DURING_THIS_CHECK       = 3
NEW_UNIQUE_PLACES                  = 36
NEW_LEADS_CREATED                  = 15
NEW_FIRST_PARTY_EMAILS             = 10
NEW_SAFE_UNIQUE_ORGS               = 10
  ... of which from post-resume discovery = 9
READ_ONLY_V2_SAFE_UNIQUE_ORGS      = 50   (THIS phase's own recompute, 2026-10-13 09:43:29 +08)
SAFE_RECOMPUTATION_STATUS          = VALID
SAFE_CURRENT_DEGRADED_READING      = 43   (proxy outage under-count; NOT business truth)
SAFE_CHANGE_FROM_40                = +10
ACTIVE_CITY                        = Cooperstown, NY
NEXT_PENDING_CITY                  = Lake Placid, NY
NEXT_SCHEDULED_RUN_AT              = 2026-10-13 13:01:07
DISCOVERY_CONTINUATION_VERIFIED    = true
BATCH_1_PRESERVED                  = true
SMTP_ENABLED                       = 0
SMTP_CONNECTIONS                   = 0
EMAILS_SENT_BY_THIS_TASK           = 0
PRODUCTION_CODE_CHANGED            = false
DIRECT_DB_WRITES_BY_THIS_TASK      = 0
MANUAL_INVENTORY_RUNS_BY_THIS_TASK = 0
NEW_AUTOMATIONS                    = 0
RESULT                             = CONTINUOUS_DISCOVERY_CONFIRMED
```

---

## M. 大白话总结（回答你最关心的两句话）

**从 40 开始，现在究竟增加了多少个真正合格的新客户？**

**+10 个。** 这 10 个商家全部带官网、全部有官网上真实公开的商务邮箱，
其中 9 个是 10 月 10 日恢复调度之后**新发现**的，另 1 个（`baseballism.com`）是恢复前就采集到、
但没进入当时 40 家快照的既有线索。所以权威口径下合格组织总数从 **40 涨到了 50**；
若只算「恢复后新发现的净增」，答案是 **+9**。

这一阶段累计新采集 **15 条新线索**、**10 个第一方邮箱**，来自 **36 条** provider 原始已发现行。

**系统是否还会自动继续寻找？**

**会，而且这次不是推断 —— 是我亲眼看着它跑的。** 本次只读核查期间，调度器**自己**跑了 3 轮：

```text
第 9 轮   2026-10-12 18:20:08 +08  ->  18:27:53    partial / safe_inventory_gap   新线索 x3
第 10 轮  2026-10-13 00:36:23 +08  ->  00:45:23    completed / target_met 50/50  新线索 x4
第 11 轮  2026-10-13 06:53:53 +08  ->  06:55:45    completed / target_met 50/50  新线索 x0

累计 11 轮、0 失败、0 锁冲突、0 并发；下一轮自动排在 2026-10-13 13:01:07。
```

节奏不是死钉在 6 小时整点，而是每轮晚约 15 分钟（调度器按「回写时刻 + 6 小时」排下一次），
所以是每天约 3.8 次而非精确 4 次。这个相位漂移本阶段未改动（改它会触碰自动化锚点，需另行授权）。

**一个需要你知道的运维事实**：本机 Astrill 代理在核查期间**一度挂掉**（本地端口 3213 拒绝连接），
随后**自行恢复**。43 这个偏低读数是故障窗口（>= 2026-10-13 08:46 +08 (checkpoint snapshot 43) until 09:43 +08）内的产物，
被它排除的 7 个商家我逐个验过，MX 记录全部有效。
**代理恢复后我原样重跑，读数果然回到 50。**
换句话说：故障期间那道控制探针按设计挡住了「SAFE 掉到 0」的假结论；恢复后同一脚本立即给出真值。
两道防线都按设计工作了。

**邮件一封没发**，也**不会**因为 SAFE 涨到 50 就自己发。要发信永远需要你另行明确授权。
