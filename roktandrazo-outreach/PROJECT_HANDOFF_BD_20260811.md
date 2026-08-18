# Rokt&Razo BD 自动化项目 — 完整交接文档（Handoff）

> **交接日期**：2026-08-11（中国时间 15:53，Asia/Shanghai）
> **项目目录**：`C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach`
> **本文件用途**：让一个新的 AI Agent 无需查看原聊天记录即可接手本项目的技术系统与业务状态。
> **重要声明**：本文档中的事实均来自历史执行记录与数据库只读核实；标有【假设】【推断】【未知】的内容未经验证。

---

## 1. 【项目背景】

### 为什么要做线下 BD
项目名为 **rokt&razo**（自称品牌），目标是通过**自动化冷邮件（outreach email）**向美国实体零售店进行批发分销（wholesale）和定制生产（custom/private-label manufacturing）业务的拓展。本质是「线上自动化 BD」：用代码替代人工去搜索潜在零售客户、验证联系方式、发送触达邮件、并跟踪结果（退信/打开/回复）。

> 说明：用户习惯称其为"线下 BD 业务项目"，但实际执行链路是**数字化的 BD 外呼**（冷邮件 + 数据管线），并非物理地推/到店拜访。接手时以此为准。

### 业务模式是什么
- 面向美国各州（重点是 TN/AR/KY 三州 lane，历史也曾跨 12 州）的实体零售店，提供两种合作：
  1. **零售分销（Retail Distributor）**：采购 rokt&razo 的成品桌游/拼图（ready-to-stock games and puzzles）放到店里卖。
  2. **定制印刷生产（Custom Printing Production）**：为礼品店等提供定制/自有品牌（private-label）产品开发、印刷、包装、生产支持。
- 邮件由品牌方"**Ian, Business Development Specialist**"名义发出，官网 `roktandrazo.com`。

### 面向什么客户 / 商户 / 合作方
- **游戏店 / 桌游店（Game Store / Puzzle Store）** → 用零售分销模板。
- **礼品店（Gift Shop）** → 用定制生产模板。
- 数据池中还有玩具店、漫画店、书店、收藏品店等（store_type 维度）。

### 解决什么核心问题
- 解决"BD 需要人工大海捞针 + 一对一发邮件"的低效问题：用**代码化采集 + 数据清洗 + 自动发送 + 退信追踪 + 时区优化**完成规模化的冷触达。

### 当前商业逻辑
- 采集大量潜在零售客户线索 → 清洗/验证邮箱 → 分类（零售/定制）→ 定时按收件人当地时间发送模板化触达 → 追踪打开/回复/退信 → 退信自动处理 → 人工跟进有回复的商家。目标是让收到邮件的商店主动联系 rokt&razo 下单或问价。

---

## 2. 【最终业务目标】

### 长期目标
建立 rokt&razo 面向美国零售渠道的**规模化、可自动化、低退信率**的 BD 触达体系，形成稳定的批发/定制订单来源。

### 当前阶段目标
1. 打通并验证"唯一生产发送链"（Execution Host → Orchestrator → Final Send Plan → Authorization → bd_sender → SMTP）。
2. 通过 **Production Release Gate**（8 项门禁），恢复"受监督的自动发送"。
3. 降低退信率（当前 8/5 批次 35%，其中 et1000 批次高达 60%）。
4. 解决 Inventory（线索采集执行器）连续多天 **0 产出** 的问题。

### 成功标准 / 核心 KPI
- **Release Gate 8 项全过**：POLLER_RESULT_SYNC_VERIFIED / LEAD_HISTORY_STATE_CLEAN / AUTH_HISTORY_CLEAN / BOUNCE_EVENT_DEDUP_CLEAN / FINAL_PLAN_HISTORY_CLEAN / BROAD_READY_COUNT / DRY_RUN_30_PASS / POST_SEND_RECONCILIATION_PASS，且 CUSTOMER_SMTP_CONNECTIONS=0。
- **SUPERVISED_SEND_RELEASE_READY=true** 才允许受监督发送；**UNATTENDED_SEND_RELEASE_READY=true** 才允许无人值守自动发送（需 Windows Service 冷启动/未登录验收）。
- 发送质量指标：退信率、打开率（tracking hit rate 当前 44.85%）、回复数。
- **新 SMTP 必须为 0**（在任何验收/测试轮次中不得真实向客户发信）。

### 目标演进（最初 → 调整 → 当前）
- **最初**（7 月）：建立 lead 采集与自动发送的基础脚本（曾有 901 Games 试点、Inventory 30 家计划）。
- **后来调整**（8/3-8/6）：发现多套发信入口、临时脚本、fake heartbeat、时区混乱等问题 → 转向"代码库生产收敛 + 唯一发送链 + 数据语义一致"。
- **当前**（8/7 起）：停止大重构，进入 **Release Gate 收口**——只修门禁项，真实 SMTP 保持 PAUSED，直到 8 项门禁全绿且 Execution Host 验证通过。

---

## 3. 【业务模型】

- **获客方式**：代码化线索采集（WebSearch / Google Places（可选）/ 官网 / 目录 / Facebook 发现），数据落地 SQLite `leads` 表。
- **BD 拓展方式**：冷邮件自动外呼，按 TN→AR→KY 城市 lane 推进；历史也曾跨州快采（8/5 et1000 批次）。
- **合作模式**：批发采购（ready-to-stock）+ 定制/自有品牌生产（custom & private-label development, printing, packaging, production support）。
- **收益模式**：B2B 批发订单 + 定制生产订单（单价/毛利率数据在历史记录中**未量化**，见第 9 节）。
- **成本结构**：成本项**未量化**。可推断的成本包括：云 Worker（Cloudflare）、SMTP 邮箱（腾讯 Exmail）、可能的线索采集 API（Google Places 可选）、人力（运营/BD 审核）。
- **激励机制**：**未讨论**。
- **商户/合作方为什么愿意参与**：【假设】店里多一个可售的产品品类 + 可定制自有品牌产品；邮件中承诺免费样品（"complimentary sample so you can evaluate the product firsthand"）。
- **用户为什么愿意使用**：【推断】商户不需要先付款即可了解产品、可索取样品、可定制贴牌。此假设**尚未经真实回复验证**（reply_log 目前仅 1 条历史 OOO 自动回复，无真实业务回复）。
- **公司最终如何赚钱**：【假设】通过批发订单与定制生产订单赚取产品毛利。**无成交/收入数据**。

---

## 4. 【线下 BD SOP】

> 本项目的"线下 BD"实际是**线上自动化链路**，SOP 如下（按实际执行流程）：

1. **线索来源**：Inventory 执行器（`inventory_monitor_executor.py`）按城市 lane 采集 → 写入 `leads`。⚠️ **当前 Inventory 连续多天 0 产出**（08-08/09/10 均 `partial`，target=30 actual=0，stop_reason=max_loops_reached，停在 `inventory_start`）。
2. **筛选**：`email_hygiene.py`（唯一权威：语法/图片伪邮箱/系统地址/泛邮箱放行）+ `mx_status.py`（8 态）+ `history_crosscheck`（组织去重）+ `broad_ready.py`（Broad Outreach Ready 主池判定，Strict A0 仅优先层）。
3. **联系**：模板由唯一 canonical `bd_template.py` 生成（两套锁定模板，见第 9 节 SHA）；渲染器 `email_html_compact_v1`。
4. **到店/拜访**：本项目**无物理到店拜访**。对应的是"官网证据验证 / 官方站点邮箱确认"（manual_email_workflow）。
5. **沟通**：冷邮件正文 + 跟进（Follow-up 模板已统一，Subject=`Re: <original>`，In-Reply-To/References 用原始 Message-ID，新 tracking token；当前 `FOLLOW_UP_ENABLED` 由环境变量/系统配置控制，未启用）。
6. **提案**：邮件内含定制/批发价值点 + 免费样品邀约。
7. **签约/合作**：**未建立**（无合同/订单流程，无成交记录）。
8. **上线**：**未开始**（无订单）。
9. **跟进**：Reply 扫描（`bd_ops_poller` reply job + 08:45 同步）；人工在 Ops Center 审核回复。当前 reply_log=1（auto OOO）。
10. **复购/转介绍**：**未开始**。

**已讨论但尚不完整的板块**：话术（=锁定模板正文）、物料（未讨论）、报价（未讨论）、合同（未讨论）、CRM（=SQLite + Ops Center）、BD 人员管理（未讨论，仅"人工审核"角色）、KPI（见第 2 节 Release Gate 口径）、提成（未讨论）、区域管理（TN/AR/KY lane + 城市队列，见 CITY_EXPANSION_RULES.md）。

---

## 5. 【目前已经完成的事情】

| 时间 | 动作 | 结果 / 数据 | 结论 |
|------|------|------------|------|
| 7 月（7/17~7/31） | 前期线索采集与多批发送 | 累计发送：7/17=16、7/19=5、7/20=19、7/22=3、7/23=11、7/29=61、7/31=21 | 验证了可批量发信，但退信/邮箱质量问题开始暴露 |
| 8/3-8/4 | 初期门禁/计划 | 8/4 的 30 家计划 0 发出 | 发现 PENDING_REVIEW 阻塞，改选 8/5 批次 |
| **8/5** | **两批共 40 封真实发送** | ① `et1000` 18:47 发 20 封（跨 12 州，❌ 未遵循三州限定）；② `2300cs_tnarky` 22:59 发 20 封（TN/AR/KY，✅） | **40 封中 14 封退信（35%）**：et1000 12/20（60%）、2300cs 2/20（10%）——快采邮箱质量差是主因 |
| 8/5 晚 | 快速采集 20 条线索 | TN=7 / AR=5 / KY=8（全部 web_search 来源） | 已全部进入 2300cs 批次并发送 |
| 8/6 | P0「退信自动回流 + 发信自检闭环」 | 新建 `bounce_pipeline.py`（Exmail 多 MIME 解析）、`preflight_gate.py`、`post_send_reconciliation.py`、`result_recovery_sync.py`、`daily_results_0900.py`；62 项单测全绿 | 退信自动分类 domain_invalid 等、UNMATCHED_DSN 兜底（21 条）、坏邮箱不回池 |
| 8/6 | P0「邮件排版恢复 + 收件人当地时间发送」 | compact 渲染器 + 时区解析（225 resolved / 3 unresolved，TN/KY 跨时区城市级解析）+ 当地 10:00 分批 + dry-run eml | content SHA 不变（ccb51505 / 5893dbc9），大空白根因=模板 `{pixel}` 占位符残留空行 + SIGNATURE 尾部 2 空行 |
| **8/7** | **代码库生产级收敛** | 190 文件分类（A=38/B=45/C=26/D=30/E=49）；归档 22 个危险脚本（`_send_*`/`_preflight_*` 等 → `_archived_scripts/2026-08-07/`）并硬禁用 fail-closed；唯一 SMTP 权威 `bd_sender.py`；Asia/Shanghai 统一调度；secret 全部环境化 | 测试 269 passed / 1 historical failure（discovery identity_review） |
| 8/7 | 数据库语义只读审计 | 全程 mode=ro；发现 40 条 auth entry plan_entry_id=lead_id、46 条 lead 状态不同步、3 条 duplicate bounce、10 条 INVALID_TEMPLATE | 出具修复清单（未执行） |
| 8/7 | **Release Gate 收口** | ①Poller health/reply/bounce 三轮连续成功，**tracking job 失败**（线上 Worker 旧版无 dashboard-summary 路由，Cloudflare 403 code 1010）；②G2 迁移 46 条 lead new→sent；③G3 修复 40 条 auth entry plan_entry_id→真实 fsp.id（两阶段更新绕过 UNIQUE）；④G4 标记 3 条 duplicate_event；⑤G5 10 条 INVALID_TEMPLATE→cancelled；⑥G6 重算 BROAD_READY=48、Strict A0=0；⑦G7 30 条影子链 mock 全 sent + 10 项 BLOCK 全绿 | **SUPERVISED_SEND_RELEASE_READY=false**（仅 Poller tracking 未验证）；UNATTENDED=false（Service 未装） |
| 8/8-8/10 | Inventory 执行器每日运行 | **每日 target=30 actual=0，全部 `partial`/`stopped`（max_loops_reached / process_killed）** | ⚠️ 采集管线未产出——重大待解决问题 |
| **8/11** | **08:45 Result Recovery Sync 实际成功**（system_config 核实） | `sync_0845_last_success_at=2026-08-11T08:35:35+08:00`；steps：tracking_sync ok（total=136, matched=61, **hit_rate=44.85%**）、bounce_scan ok（scanned=15, matched=14, domain_invalid=12, unmatched=1）、reply_scan ok、unsubscribe_scan ok | 结果回流同步链路已通（本地对比，不依赖 Worker dashboard-summary） |

### 关键结论沉淀
- **退信率高发 = 快采邮箱质量差**（60% vs 10% 对比明确）。
- **send_log 451 = 448 sent + 3 failed**（failed 为从未被 SMTP 接受的记录，正确不计入 SMTP Accepted）。
- **bounced 邮件不得从 SMTP Accepted 中扣除**（Delivery Outcome 单独呈现）。
- **数据必须先备份再迁移**（`backup/repository_consolidation_20260807_093756`、`backup/release_gate_20260807_141244`）。
- **shadow 链测试教训**：mock 只拦 SMTP 不拦 DB 副作用 → 曾污染 60 条 send_log + 54 条假 reply，已清理恢复。**影子链必须用事务回滚或独立测试库**。

---

## 6. 【当前项目进度】

| 模块 | 状态 | 说明 |
|------|------|------|
| 战略 | 🟡 进行中 | 从"能发"转向"可靠地发 + 低退信率"，Release Gate 是当前战略闸门 |
| 商业模式 | 🟡 进行中 | 批发+定制双模板已定，但收益/成本未量化，无成交验证 |
| BD SOP（采集→发送→追踪） | 🟡 进行中 | 链路代码完备，但 **Inventory 采集 0 产出** 阻塞新线索 |
| 销售话术 | ✅ 已完成 | 两套锁定模板（V5 locked），禁止修改 |
| 商户方案 | 🟡 进行中 | 邮件方案已定；报价/合同/样品流程未建立 |
| BD 团队 | ⚠️ 存在问题 | 无真实团队；仅"人工审核/Ops Center 操作"角色；BD 人员管理/提成未讨论 |
| 数据系统 | ✅ 已完成 | SQLite 单库 + Ops Center 8765 + Dashboard + 08:45/09:00 自动化 |
| KPI | 🟡 进行中 | Release Gate 8 项已定义；业务侧 KPI（退信率/打开率/回复数）有雏形 |
| 激励机制 | 🔴 未开始 | 未讨论 |
| 实际市场验证 | ⚠️ 存在问题 | **零成交、零真实业务回复**（reply_log=1 是 OOO 自动回复）；唯一"验证"是技术链路与 mock |

---

## 7. 【已经做出的关键决策】

| 决策 | 为什么 | 是否仍有效 |
|------|--------|-----------|
| 唯一生产 SMTP 权威 = `bd_sender.py`；其他生产文件禁止 smtplib/sendmail | 消除多入口、保证事务/幂等可审计 | ✅ 有效（静态测试 `test_single_smtp_authority` 强制执行） |
| 生产调度权威时区 = **Asia/Shanghai**（inventory 15:00 / pre-send 22:30 / outreach 23:00 / post-send 00:10 / end-of-day 00:25） | 统一主时钟，杜绝 CST/EST/New_York 混用 | ✅ 有效 |
| 收件人**当地时间 10:00、Mon-Fri** 发送，按 ET/CT/MT/PT 分批 | 提升打开率 | ✅ 有效（`recipient_scheduler.py` + Preflight 时区检查） |
| 发送/Outreach **持续 PAUSED**，直到 Release Gate 8 项全绿 + Execution Host 验证 | 防止未验证链路真实发信造成伤害 | ✅ 有效（最硬约束，验收时新 SMTP 必须=0） |
| 两套模板锁定：`retail_distributor_v5_locked`（ccb51505）/ `custom_printing_production_v5_locked`（5893dbc9），**正文/Subject 不可改** | 用户明确要求锁定话术 | ✅ 有效 |
| 内容与渲染版本分离：`renderer_version=email_html_compact_v1` / `renderer_sha256=eb8b679d` | 排版调整不改 content SHA | ✅ 有效 |
| Broad Outreach Ready = 主发送池；**Strict A0 只是优先层**，不是唯一池 | 避免高门槛卡死发送量 | ✅ 有效 |
| 归档并硬禁用所有日期型/临时发信脚本（fail-closed raise） | 消除第二发信入口 | ✅ 有效 |
| secret 全环境化，缺失即 fail-closed | 去除硬编码默认密钥（含 config.py 明文 SMTP 密码） | ✅ 有效 |
| 禁止伪造 heartbeat：只有真实 Poller 可写 `bd_ops_poller_status.json` | 防止"发信前刷心跳骗过 Preflight" | ✅ 有效 |
| Dashboard 不硬编码 Nashville，动态读 system_config；失败显示 unknown 而非假数据 | 数据必须真实 | ✅ 有效 |
| Authorization 消费原子化：`status='pending'→'consumed'`，重复消费返回 False；`final_plan_entry_id` 必须是真实 fsp.id（禁止=lead_id） | 防重复发送/并发 | ✅ 有效 |
| 用 GitHub 仓库仅作快照，**不得用旧版本覆盖本地修复** | 本地 8/3-8/7 修复未 push，防止回滚 | ✅ 有效 |
| 本次阶段"停止大重构，只做 Release Gate 收口" | 收敛范围、避免打补丁循环 | ✅ 有效 |
| 验收必须"只汇报一次"+ 明确【事实/推断】区分 | 避免误导新接手者 | ✅ 有效（即本文档） |

---

## 8. 【还没有解决的问题】

### 未决策问题
- 是否/何时部署 Cloudflare Worker 新路由（含 `/internal/dashboard-summary`）——当前 tracking job 唯一 blocker，需在 Cloudflare 侧操作（wrangler npm 网络此前不可达）。
- 何时安装 Windows Service（`bd_execution_host_service.py`）——需要 UAC 提权，尚未执行。
- Follow-up 是否启用（代码就绪，开关由系统配置控制，未决策开启）。
- 报价/合同/样品寄送流程（未建立）。
- 是否扩大 CRM（历史明确"不扩大"——保持为 SQLite + Ops Center）。

### 风险
- **Inventory 连续 0 产出**（08-08/09/10 全部 partial，max_loops_reached）→ 无新线索，发送恢复后无米下锅。
- 8/5 退信率 35%，其中快采批次 60% → 发送信誉/邮箱被投诉风险。
- Poller tracking 依赖外部 Worker 路由未部署 → Release Gate 第 1 项卡住。
- **510 条 leads 时区 UNSET**（仅 8/5 那批 228 条有时区：225 RESOLVED + 3 UNRESOLVED）→ 历史线索无法当地 10:00 调度。
- `preflight_status=failed`（system_config）、`daily_run_status=underfilled` → 09:00 日报可能显示 DATA STALE。
- 影子链测试曾污染生产库（已清理，但教训需固化进测试流程）。

### 假设（未验证）
- 商户愿意回复/下单（无真实回复样本）。
- 打开率（44.85% hit rate 是"tracking 匹配率"，非严格打开率）能转化为商机。
- 免费样品话术有效。

### 矛盾 / 数据不足
- `strict_a0` 在 DB canonical 与 Ops API 口径不一致（4 vs 1，G6 后 canonical 为 0，因 A0 lead 已标 sent）。
- Poller status json 中 tracking/health/reply 的 `last_success_at=None`，但 system_config 的 08:45 sync 已成功——**两条状态来源不一致**，需统一。
- reply_log=1 是 6/25 的历史 OOO 自动回复（chad@emeraldcitycomics.com），**不代表真实业务反馈**。
- 收益率/成本/ROI/客单价等财务数据全部缺失（历史未讨论）。

### 需继续验证的问题
- 部署 Worker 后 tracking job 是否转绿（Release Gate 第 1 项）。
- Inventory 为什么停在 `inventory_start`（max_loops_reached）——读执行器日志定位。
- 时区 UNSET 的 510 条如何批量回填（复用 `timezone_resolver.py --apply`，需注意仅对可解析城市）。
- discovery `identity_review` 历史失败测试（HEAD 即失败，discovery 模块零改动）是否修复。

---

## 9. 【重要数据】

### 数据库核心（2026-08-11 只读核实）
| 表 | 数量 |
|----|------|
| leads | **738**（TN=177 / AR=67 / KY=66 / CA=47 / TX=28 / OR=25 / WA=23 / FL=23 / NY=22 / NC=20） |
| send_log | **451**（sent=448 + failed=3） |
| final_send_plan | **132**（sent=122 + cancelled=10） |
| send_authorizations | **6**（consumed=2 + revoked=4） |
| send_authorization_entries | **40**（G3 修复后全部指向真实 fsp.id） |
| bounce_log | **34**（domain_invalid=18 / hard=6 / domain=4 / policy=3 / unresolved=2 / unknown=1） |
| unmatched_dsn | **21**（7 条仍无法关联 send_log） |
| contact_recovery | **15**（全 pending，无替代邮箱） |
| suppression_list | **26**（unsubscribe=1 + bounce 类 15 + Phase0 9 + duplicate 1） |
| reply_log | **1**（auto_reply_ooo，6/25，非真实业务回复） |
| job_runs | **45** |

### 发送历史（按天）
8/5=40、7/31=21、7/29=61、7/23=11、7/22=3、7/20=19、7/19=5、7/17=16（更早未列）。

### 退信与质量
- 8/5 两批 40 封 → **14 封退信（35%）**；et1000 12/20（60%）、2300cs 2/20（10%）。
- 退信类型（8/5-8/7 DSN）：domain_invalid 为主（MX Host not found）。
- tracking 匹配率：**44.85%**（136 条中 61 条匹配 send_log）。

### 时区
- RESOLVED=225、TIMEZONE_UNRESOLVED=3（city/state 缺失）、**UNSET=510**。

### 模板与渲染
- retail_distributor_v5_locked → content SHA `ccb51505`；custom_printing_production_v5_locked → `5893dbc9`。
- renderer：`email_html_compact_v1` / SHA `eb8b679d`。
- 渲染要求：HTML 恰 1 个 tracking pixel；text/plain 与 sender-copy 无 pixel；无 flex/绝对定位/大空白。

### 候选池（G6 重算）
- **Broad Outreach Ready = 48**；Strict A0 = 0（历史 4，因已发送已标 sent）。

### 财务数据
- 客单价 / CAC / 提成 / 毛利 / ROI / 收入目标 / 预算：**全部未知（历史未讨论）**。

---

## 10. 【我个人的偏好和已经明确否定的方案】

### 认可 / 重视
- **fail-closed（安全失败）**：任何不确定 → 不发送/标记/阻断，而不是猜。
- **真实数据优于好看数据**：Dashboard 宁显示 unknown/stale，也不显示假 Nashville/0。
- **先备份再迁移**；**只读审计不修数据**；验收要出**修复清单**而不是偷偷改。
- **幂等、原子事务、防重复发送**。
- **多 Agent 并行 + 每项自测全绿 + 只汇报一次**。
- **影子链/mock 绝不碰真实 SMTP**（真实客户 SMTP 连接数必须=0）。
- **明确区分**：SUPERVISED（人工监督可发送）与 UNATTENDED（无人值守已验证）不能混为一谈。
- 遇到需要 UAC/系统级操作时，如实报告"执行到需要管理员的一步"，不假装已安装。

### 明确反对 / 已否定
- ❌ **日期型临时补丁脚本**（`_fix_20260807.py` 这类）——修复必须进正式模块。
- ❌ **多套发信入口 / Legacy Sender / 旧 pipeline**——只能有唯一 SMTP 权威 `bd_sender.py`。
- ❌ **SEND_LIVE=True** 之类"备用发信开关"。
- ❌ **发送脚本自己刷 Poller heartbeat** 来骗过 Preflight。
- ❌ **硬编码 secret**（含明文 SMTP 密码、默认 dashboard key、tracking pepper）。
- ❌ **GitHub 旧版本覆盖本地修复** / 旧项目整体复制回生产。
- ❌ **把 Strict A0 当作唯一发送池**。
- ❌ **用 CST/EST 等含糊缩写当主调度时钟**。
- ❌ **修改锁定模板正文 / Subject**；❌ **增加 Best regards**（除非模板原文有）。
- ❌ **Dashboard 硬编码 Nashville** 假数据。
- ❌ **DELIVERED / 已读 / Confirmed Read** 等不实投递表述（只允许 SMTP Accepted / Outcome Unresolved / Open Signal）。
- ❌ 把 bounced 邮件从 SMTP Accepted 中扣除。
- ❌ 真实客户 SMTP 验收（"只发一个看看"也不行）。

### 决策时最看重的
安全 > 一致性 > 可测试性 > 单一真相源 > 最少生产入口（用户在多轮任务中反复强调此优先级）。

---

## 11. 【目前最应该做的 5 件事】

| 排序 | 动作 | 为什么 | 依赖 | 完成标准 |
|------|------|--------|------|----------|
| 1 | **定位并修复 Inventory 0 产出**（读执行器日志，查 max_loops_reached 根因） | 无新线索则发送恢复后无米下锅 | 读 `output/` 下 inventory 相关日志、`inventory_monitor_executor.py` | 单日 dry-run 产出 >0 个候选并落库 |
| 2 | **部署 Cloudflare Worker 新路由 + 配置 DASHBOARD_API_KEY** | Release Gate 第 1 项（Poller tracking job）唯一 blocker | Cloudflare 侧权限/wrangler 网络；`.env` 加 `DASHBOARD_API_KEY` | `bd_ops_poller` tracking job `last_success_at` 非 null |
| 3 | **回填 510 条时区 UNSET**（复用 `timezone_resolver.py --apply`） | 历史线索需当地 10:00 调度 | 城市/州数据完整 | 可解析城市全部 RESOLVED，UNRESOLVED 列表可审计 |
| 4 | **统一 Poller 状态双来源**（system_config sync vs bd_ops_poller_status.json jobs） | 当前两处状态不一致，影响 Data Freshness 判定 | 读两处写入逻辑 | Dashboard 的 Data Freshness 单一可信 |
| 5 | **重跑 Release Gate 8 项**（Poller 四 job 连续两轮 + 影子链 dry-run + 对账） | 门禁放行受监督发送的前提 | 事项 1-4 | 8 项全绿 → `SUPERVISED_SEND_RELEASE_READY=true`；仍保持真实 SMTP=0 |

---

## 12. 【给新 Agent 的交接说明】

**现在项目处在哪**：rokt&razo BD 自动化外呼系统已从"能发信"走到"生产级收敛完成 + Release Gate 收口"阶段。技术底座（唯一发送链、退信闭环、时区调度、只读审计、影子链验证）已就绪；发送真实客户邮件被**硬性暂停**，直到 8 项 Release Gate 全绿。当前最大卡点是 **Inventory 采集 0 产出**（无新线索）和 **Poller tracking 依赖未部署的 Worker 路由**。

**最重要的上下文**：
1. 数据库是单一真相源（`data/bd_leads.db`），所有 Dashboard/Ops Center 数据来自它。
2. `bd_sender.py` 是唯一 SMTP 权威，事务/幂等已收敛，**不要再加第二条发送路径**。
3. 模板正文锁定（V5 locked + SHA），排版只动渲染层。
4. 任何写入数据库的迁移必须先备份，任何"验证"不得真发信。

**不要重新讨论**：唯一发送链、模板锁定、Asia/Shanghai 主时钟、当地 10:00 调度、Broad Ready 主池、禁止伪造 heartbeat、禁止日期型脚本、shadow 链须事务隔离。这些已决策且用户明确反对回头。

**必须重新梳理**：① Inventory 执行器为什么连续 0 产出（日志/代码）；② Poller 两条状态来源的统一；③ 时区 UNSET 510 条的批量回填方案；④ 财务/收益模型（从未量化）；⑤ 真实业务回复=0，任何"转化率"类结论都不可靠。

**接下来最值得推进**：先修 Inventory（有米下锅），再部署 Worker（放行 tracking），回填时区，重跑 Gate。全程真实 SMTP=0。

---

## 【事实 / 推断区分】

### A. 历史聊天中已明确确认的事实
- 业务为 rokt&razo 品牌，向美国零售店做批发 + 定制生产 BD，用冷邮件自动化执行。
- 两套锁定模板及 SHA：retail `ccb51505`、custom `5893dbc9`；渲染器 `email_html_compact_v1`/`eb8b679d`。
- 唯一 SMTP 权威 `bd_sender.py`；生产调度 Asia/Shanghai；当地 10:00 发送策略。
- 发送数据：send_log=451（448 sent+3 failed）；8/5 两批 40 封、退信 14 封（35%；et1000 60%/2300cs 10%）。
- 数据库计数（2026-08-11 只读核实）：leads=738、FSP=132、auth=6/entries=40、bounce=34、unmatched_dsn=21、contact_recovery=15、suppression=26、reply=1。
- Release Gate 结果（8/7）：LEAD_HISTORY_STATE_CLEAN/AUTH_HISTORY_CLEAN/BOUNCE_EVENT_DEDUP_CLEAN/FINAL_PLAN_HISTORY_CLEAN/DRY_RUN_30_PASS/POST_SEND_RECONCILIATION_PASS 全 true；POLLER_RESULT_SYNC_VERIFIED=false（tracking 依赖未部署的 Worker 路由）；CUSTOMER_SMTP_CONNECTIONS=0。
- Execution Host Windows Service 未安装；自动 Outreach 任务保持 PAUSED。
- 08:45 Result Recovery Sync 于 2026-08-11 08:35 实际成功（tracking 命中 61/136=44.85%）。
- Inventory job 08-08/09/10 连续 `partial`，target=30 actual=0，stop_reason=max_loops_reached。
- 时区：225 RESOLVED / 3 UNRESOLVED / 510 UNSET。

### B. 已形成但尚未验证的业务假设
- 商户愿意因为"多一个可售品类 + 可定制 + 免费样品"而回复/下单。
- 当地 10:00 发送能显著提升打开率。
- 打开率（tracking 匹配率）能转化为商机。
- 批发 + 定制双产品线能形成稳定收入。

### C. 根据聊天记录做出的推断
- 退信率高的主因是快采邮箱质量差（60% vs 10% 的对比支撑）。
- "线下 BD 项目"实际执行是线上自动化冷邮件，无物理拜访。
- Inventory 0 产出可能是采集循环条件（max_loops_reached）或网络/代理/Provider 配置问题——**未读日志证实，属推断**。
- Poller 状态双来源不一致（system_config sync 成功 vs status json jobs 部分 None）可能因两套写入路径未统一——**未读代码证实，属推断**。

### D. 历史记录中没有 → 标"未知"
- 客单价 / CAC / 提成 / 毛利 / ROI / 预算 / 收入目标：**未知**。
- 商户报价 / 合同条款 / 样品寄送成本：**未知**。
- BD 团队人数 / 提成结构 / 区域负责人：**未知**。
- 是否已有任何真实订单：**未知**（reply_log 无真实业务回复，但"无订单"是基于可查数据的推断，若订单记录在系统外则未知）。
