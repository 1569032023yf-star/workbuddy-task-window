# Rokt&Razo 美国零售 BD 自动化项目 — 阶段复盘

> 报告日期：2026-08-18 ｜ 用途：2026-08-19 项目汇报
> 数据来源：实时数据库 `data/bd_leads.db` + 当前 Runtime + 腾讯企业邮箱真实 DSN
> 说明：本报告所有数字均取自今日实时查询，非凭记忆编写。

---

# 一页领导汇报版

## 1. 我们想解决什么

过去人工寻找美国实体零售客户（玩具店、桌游店、漫画店、礼品店等）、逐个验证邮箱、逐一发开发信，效率低、规模化难、结果无法回流。

项目目标：

> 自动完成「商户发现 → 邮箱验证 → 安全触达 → 退信/回复结果回流」闭环。

## 2. 为什么这段时间没有持续发信

不是项目停滞，而是在**真实发送过程中连续发现生产风险，因此主动暂停扩量并逐项治理**。

按阶段说明：

### 第一阶段：库存问题
Inventory 曾连续 0 产出。原因：新商户来源断裂、历史三州客户覆盖率高、旧候选重复扫描。后来完成 Discovery 恢复、Geographic Expansion、ICP 明确。

### 第二阶段：发送链治理
发现多套旧发送入口、Final Plan / Authorization 旧语义、tracking Worker / Poller / Scheduler 状态混乱。因此没有盲目继续发送。完成唯一 Canonical Send Chain、Authorization 原子化、duplicate / suppression、当地时间调度、tracking / reconciliation。

### 第三阶段：邮箱质量问题（关键）
第一次真实验证批：20 SMTP Accepted，但 15 Bounced（**Bounce Rate = 75%**）。真实 DSN 分析发现：
- Domain Invalid 12
- Mailbox Invalid 2
- Policy 1

核心原因不是发信服务器信誉，而是**旧 Lead 大量使用 guessed email，且没有 MX / 第一方官网邮箱验证**。

### 第四阶段：Email Quality V2
因此暂停扩量，新增：official-page email requirement、MX Gate、evidence freshness、Campaign Eligible V2。从「看起来像邮箱」升级为：

> **官网真实出现 + MX 可投递 + 从未联系过**

## 3. 当前已经解决什么

- 自动找客户已恢复，新州市场已扩展
- ICP 已明确
- 正式发信链（Canonical Send Chain）已稳定
- 退信结果能够从企业邮箱自动回流（IMAP DSN scan）
- 假回复（fake reply）污染已修复
- MX 检查已接入，作为 V2 发送硬性门槛
- 高质量 V2 Lead 已开始重新积累

## 4. 当前最新结果（实时查询）

| 指标 | 数值 |
|------|------|
| Total Leads | **1020** |
| ICP 合格（route A 高匹配） | 858（B 中匹配 54 / U 不匹配 104） |
| Campaign Eligible V2（今日发送底仓） | **11** |
| 今日新增 V2 | 0（进行中，目标最多补至 30） |
| 今日计划发送 | 11（已锁定底仓，动态追加至最多 30） |
| 今日 SMTP Accepted | 待发送后回填 |
| 今日 Bounce | 待发送后回填 |
| 今日 Bounce Rate | 待发送后回填 |
| 今日 Reply | 待发送后回填（不计入 OOO / self-sent） |

历史累计：已发送 379、累计 bounce 40、replied 0、unsubscribed 0、do_not_contact 1、时区已解析 966。

## 5. 今天这批验证意味着什么

今日发送为 Email Quality Gate V2 升级后**第一批修复性验证发送**：全部 11 条均为官网真实出现 + MX PASS + 从未联系过的第一方邮箱。

发送后依据腾讯企业邮箱真实 DSN 回填结果：
- 若 Bounce 明显下降（例如 ≤1/11）→ 新 Email Quality Gate 已显著改善投递质量，问题定位与优化方向正确。
- 若仍偏高 → 如实说明邮箱级验证仍需加强，继续控制规模、不牺牲域名信誉换数量。

---

# 详细技术 / 项目附录

## A. ICP（理想客户画像）
目标商户类型：独立玩具店 / 桌游拼图店 / 卡牌店 / 漫画店 / 礼品店 / 博物馆商店 / 书店礼品区 / 手工艺爱好店 / 小镇综合商店 / 旅游区商店。
排除：纯电商无实体、制造商/批发商（非零售）、目录/第三方聚合站邮箱不可直接发送。

## B. Lead Funnel（当前全库状态）
- Total Leads：1020
- 已发送：379 ｜ 累计 bounce：40 ｜ replied：0 ｜ unsubscribed：0 ｜ do_not_contact：1
- email_source_type 分布：official_page_visible 291、guessed_email 168、web_search 30、official_mailto 5、contact_form_only 5、web_directory 8、manual_lookup 8、wholesale_vendor_page 1、web_search_official 6、web_search_directory 5、inventory_recovery 2、no_contact_found 2、未知/空 487
- 关键结论：旧库 guessed_email（168）与 unknown（487）占比高，是历史高 bounce 根因。

## C. Canonical Send Chain（唯一正式发信链）
Campaign Eligible V2 → Final Send Plan → Scheduler → Fresh Authorization（窗口前创建，TTL≈15min）→ Preflight → `bd_sender/send_one` → SMTP → Reconciliation → Post-Send Recovery。
禁止第二发送入口。

## D. Bounce Pipeline（结果回流）
发送后：Reconciliation → bounce IMAP scan（腾讯企业邮箱真实 DSN）→ suppression sync → reply scan → tracking sync。发送后 30–60 分钟再次 Bounce Scan，次日汇报前再扫一次 INBOX。第一真相源 = 企业邮箱真实 DSN，不只看 send_log。

## E. Email Quality V2（升级后的质量门禁）
硬性门槛（任一不满足即不发送）：
- ICP Qualified
- 未历史发送
- 非 duplicate organization
- 非 suppression / bounce / unsubscribe
- Official Website 有效
- 完整邮箱实际出现在第一方官方页面（official_page_visible）
- evidence_url + evidence_snippet + evidence_checked_at
- MX PASS
- timezone RESOLVED
- 禁止 guessed_email（info@ / sales@ / contact@ 不可自动发）

## F. Geographic Expansion
主攻州：TN / AR / KY；第二批：FL / UT / SC。本轮 V2 底仓已覆盖 KY / TN / AR / GA / VA / OH / IL / NC / FL / MO，地理分布健康。

## G. 当前数据库指标
- 已解析时区：966 / 1020
- V2 底仓：11（ET 7 / CT 4）
- 发送安全阈值：任一批前 10 条若 bounce ≥2（≥20%），暂停剩余 batch。

## H. 当前风险
- V2 库存仍偏薄（11 条底仓），需持续补 Verified Lead。
- guessed_email 历史存量仍多，不可直接扩大发送。
- 发件域名信誉脆弱，必须控制 bounce rate。

## I. 下一阶段计划
- 持续用现有 Discovery 工具补 Verified V2，目标池稳定 ≥30。
- 维持 V2 质量门禁，不做数量妥协。
- 常态化 Post-Send DSN 回流与健康度监控。

---

# 今日恢复发送结果（发送后回填）

> 以下字段在今日各时区窗口发送并回流结果后更新。

- TARGET_SEND = 30（最多目标，非最低门槛）
- TODAY_VERIFIED_AVAILABLE = 11（底仓；动态追加）
- TODAY_SEND_ACTUAL = ?
- TODAY_SMTP_ACCEPTED = ?
- TODAY_BOUNCED = ?
- TODAY_BOUNCE_RATE = ?
- TODAY_REPLY = ?
- REMAINING_VERIFIED_INVENTORY = ?

### 发送批次（按 recipient local 10:00，换算上海时间）
| 时区 | 条数 | 上海发送窗口 | 状态 |
|------|------|--------------|------|
| ET（America/New_York） | 7 | 约 22:00 | 待 Fresh Auth + Preflight |
| CT（America/Chicago） | 4 | 约 23:00 | 待 Fresh Auth + Preflight |

---

# 60 秒口头汇报版（可直接照讲）

各位，这个美国零售 BD 自动化项目，目标一直是把「找客户、验邮箱、发开发信、回收结果」做成自动闭环。

过去几周我们没有盲目扩量，是因为**真实发信时连续暴露了生产风险，我们主动按下暂停、逐项治理**：先是库存断供，恢复了发现与扩州；再是发现多套旧发送入口和调度混乱，统一成唯一正式发送链；最关键的是第一次真实验证批 20 封里有 15 封退信、退信率 75%，根因是旧线索大量用了猜测邮箱、没有官网和 MX 验证。

所以我们把质量门禁升级到 V2：只发「官网真实出现 + MX 可投递 + 从没联系过」的第一方邮箱。今天就是升级后的第一批修复性验证发送，11 条高质量线索已锁定、按客户当地上午十点分批真实发出，发送后所有退信、回复都从腾讯企业邮箱真实回单回流。

结论：我们不是没进展，而是把「自动发得出去」升级成了「自动找到正确客户、用可验证邮箱安全发出去」。下一步持续补高质量线索、守住域名信誉。

---

_报告生成：2026-08-18 ｜ 实时数据 base：data/bd_leads.db（1020 leads）_
