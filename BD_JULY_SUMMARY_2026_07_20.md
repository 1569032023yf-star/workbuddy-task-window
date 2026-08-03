# Roktandrazo 美国零售外联 — 七月总结（截至 2026-07-20）

> 数据来源：`roktandrazo-outreach/data/bd_leads.db`（send_log / bounce_log / reply_log / leads）
> 覆盖范围：2026-07-01 ~ 2026-07-20，14 个发送日

---

## 一、执行总览

| 指标 | 数值 |
|------|------|
| 发信总数 | **198 封** |
| 成功送达 | 196 封（成功率 99.0%） |
| 发送失败 | 2 封 |
| 回信 | **0 封** |
| 退信 | **2 封**（均为 hard bounce，退信率 ~1.0%） |
| 覆盖州数 | 36 个（含 1 个州字段为空） |
| 主州（TN/AR/KY）占比 | 94 / 198 = **47.5%** |

---

## 二、每日 / 周度发信节奏

**按周**

| 周 | 日期区间 | 发信量 |
|----|---------|--------|
| W1 | 7/01–7/07 | 65 |
| W2 | 7/08–7/14 | 75 |
| W3 | 7/16–7/20 | 77（58 + 7/20 当日 19） |

**按日**

| 日期 | 发送 | 日期 | 发送 |
|------|------|------|------|
| 07-01 | 21 | 07-13 | 20 |
| 07-02 | 10 | 07-14 | 20 |
| 07-03 | 15 | 07-16 | 18 |
| 07-06 | 17 | 07-17 | 16 |
| 07-07 | 2  | 07-19 | 5  |
| 07-08 | 5  | 07-20 | 19 |
| 07-09 | 18 |      |    |
| 07-10 | 12 |      |    |

> 每日目标 20 封，多数日期达标；7/16、7/17、7/20 因 A0 库存不足出现 underfilled（缺口 1–14 封）。

---

## 三、地区分布

| 地区 | 发信量 | 占比 |
|------|--------|------|
| **主州 TN** | 53 | 26.8% |
| **主州 KY** | 22 | 11.1% |
| **主州 AR** | 19 | 9.6% |
| 主州小计 | **94** | **47.5%** |
| 州字段为空 | 13 | 6.6% |
| 其余 35 州（分散） | 91 | 45.9% |

**其余州 Top（均 ≤8 封，长尾分散）**：NC 8、FL 7、MI 5、OH/CO/AZ 各 4、WI/VA/SC/OR/NM/NE/IN/IL/AL 各 3、其余各 1–2。

> 说明：主州策略（TN/AR/KY）为 7/7 落地，但 7/9 之前已有部分跨州/紧急补池线索发出，故其余 35 州占比较高。后续主州占比应持续提升。

---

## 四、店铺种类分布（已归并）

| 店铺大类 | 发信量 |
|----------|--------|
| 游戏 / 桌游 / 卡牌 / 漫画店 | 86 |
| 玩具店 | 57 |
| 礼品 / 博物馆 / 综合 / 特色店 | 22 |
| 线上品牌 / DTC | 20 |
| 未分类 | 11 |
| 拼图专营店 | 2 |

> 游戏/桌游类 + 玩具店合计 **143 封（72%）**，是核心目标客群；与拼图产品的渠道匹配度高。

---

## 五、回信与退信

### 回信：0 封
- 七月 reply_log 无新增；全量历史仅 1 条且非本月。
- 收件箱轮询模块（7/14 上线）已能识别 hot_reply / 自动回复 / 退订，目前扫描结果为 0 高意向回复。
- **判断**：处于冷启动外联早期，尚无正向反馈，需跟进序列 + 样品/目录策略激活。

### 退信：2 封（hard bounce）
| 邮箱 | 门店 | 地区 | 原因 |
|------|------|------|------|
| thetoyllc@gmail.com | Toy Lab | FL | Gmail Message-ID header 问题 |
| comics@borderlands.us | Borderlands Comics | SC | 投递失败（postmaster） |

- 两封均已进入 bounce_log 并加入 suppression（不再重发）。
- 退信根因与 7/7 的 **Message-ID header 修复** 直接相关（见下节）。

---

## 六、系统优化措施（七月）

### 1. Message-ID Header 修复（7/7 交接 → 7/9 生效）
- 问题：`bd_sender.py` 缺 `Message-ID` header，导致 M365/Outlook 侧 policy bounce。
- 修复：补全 3 个文件（bd_sender.py / agent_bounce_auditor.py / daily_session.py）约 10 行。
- 效果：7/9 扫描发现 14 条退信，其中仅 2 条属本系统（Toy Lab / Borderlands），修复后重发成功；明确规则——**Message-ID 类退信不得写入 suppression_list**。

### 2. Lead Hygiene Gate 生产合并（7/13）
- 用 14 字段预检门禁替代原 4 项人工校验，作为**只读预检第二道门**。
- 测试 **88/88 通过**，Shadow Mode 零误报、零误杀；杜绝「已发送 / 被抑制 / 非主州 / 证据缺失」线索混入发信池。

### 3. email_source_type 白名单修复（7/13）
- `get_sendable_leads()` 补 `manual_lookup`，让人工验证线索能进入可发池（此前被静默过滤）。
- 当日 A0 池补 12 条（TN/AR/KY）。

### 4. 主州策略落地（7/7）
- 写入 `system_config`：city_selector 锁定 **TN/AR/KY 主州 + FL/UT/SC 备份州**。
- 设定 `inventory_floor=60`、发送窗口 `09:00–13:00 Asia/Shanghai`、补池班次 `13:30–17:30`。
- 修正 B2 池定义（`manual_review_needed` = 167），消除「B2 空 vs 待审 167」矛盾。

### 5. Facebook 富化 + B 池回收管线（7/13）
- 新建 `fb_batch_runner` + `fb_rate_limiter` + `b_pool_recovery_runner` + `inventory_recovery_loop`。
- 4 阶段管线（官网扫描 → 提取 FB → FB 阅读取联 → 门禁校验），**write-safe 零误发**地持续补充 A0 库存。

### 6. Risk Circuit Breaker v3.0（7/16，关键修复）
- 致命缺陷：风险事件直接暂停整个调度器且无自动恢复——automation 自 7/9 因 hard bounce **PAUSED 卡死 7 天**。
- 改为 `temporary_risk_block`（20h 冷却）+ 08:30 自动恢复 + `run_lock` 防并发；`today_sent` 改读 send_log。
- 已恢复 ACTIVE，避免再次人为停摆。

### 7. 收件箱轮询 + 跟进队列（7/14）
- `inbox_polling_monitor`：IMAP 增量扫描，自动分类 bounce / reply / unsubscribe / hot / auto。
- `follow_up_queue_builder`：识别 14 天未回复线索（86 候选），为跟进序列打底。

### 8. 模板与数据清洗（7/14）
- 修复 `apply_email_to_lead()` 未调用；Mast General Store 邮箱截断（.co→.com）修正。
- 降权 3 家线索（占位符 / 第三方 Gmail / 非官网邮箱）。

---

## 七、当前瓶颈与下一步

1. **A0 可发库存持续吃紧**：7/16 剩 21 → 7/17 剩 6 → 7/20 剩 7，多次 underfilled。依赖 B 池回收管线补池，建议加大 FB/官网回收力度或人工验证批次。
2. **send_pause 仍未解除**：7/20 因累计 bounce≥2 触发 `send_pause=true`，需人工确认后解除。
3. **回信率 0**：需设计跟进序列（14 天触发）+ 样品/目录引流，把 143 封游戏/玩具类高匹配线索转化为对话。
4. **C 池 55 封仅 contact form**：无法自动发，需单独的表单提交/人工触达流程。

---

*生成于 2026-07-20 · 数据已与 leads / send_log / bounce_log / reply_log 交叉校验*
