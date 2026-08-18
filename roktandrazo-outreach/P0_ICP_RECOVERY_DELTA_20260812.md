# P0 — ICP + Lead Recovery · PROJECT DELTA

> 生成：2026-08-12 18:08（Asia/Shanghai）· 项目目录：`roktandrazo-outreach`
> 本轮：P0-A ICP + P0-B Lead Recovery。**CUSTOMER SMTP CONNECTIONS = 0**（全程未发真实邮件）
> 交付物：本文档 + `ICP_V1.md` + `icp_profile.py` + `output/p0_icp_recovery_metrics.json`

---

## 1. ICP_V1（已完成）

**文件**：`ICP_V1.md`（完整文档）+ `icp_profile.py`（规则引擎，含 5 个函数 + 版本常量）

| 项 | 内容 |
|----|------|
| **Route A** | Retail Distributor：game/toy/comic/puzzle/hobby/bookstore/board/card/children/educational 型独立店，核心判断"是否真卖 puzzles/board games/family games/toys/gifts/educational" |
| **Route B** | Custom/Private Label：gift/museum/national park/souvenir/historic/tourist/vintage/visitor center/boutique/specialty 型，核心判断"是否可能有 custom/private label/branded/printing/packaging/souvenir 需求" |
| **P1** | buyer/owner/purchasing/wholesale/manager + store-domain 邮箱（采购决策人）——存量仅 1 条，当前为加分项非门槛 |
| **P2** | info@/hello@/contact@/sales@ 等 + store-domain（**主池**，本轮 2 条） |
| **P3** | 官网公开免费邮箱（gmail/yahoo/aol/hotmail），store 高度符合 ICP（本轮 3 条） |
| **Negative ICP** | 大牌连锁/平台卖家/仅第三方目录邮箱/无官网证据/仅 Facebook/成人用品等（本轮拦截 Record Rack → do_not_contact） |
| **硬要求** | evidence_url + evidence_snippet 必须说明"为什么相信邮箱属于该商户" |

**关键数据事实**（只读核实）：official_page_visible 邮箱退信率 1% vs guessed_email 10% vs unknown 25% → 官网可见邮箱优先；三州 Route A 主体（game/toy/comic 占多数）；Route B 型仅 29 条。

**【业务事实】**：三州主市场是 Route A；官网可见邮箱质量最高；有官网无邮箱 35+ 条是回收目标。
**【当前假设】**：P1 采购决策人回复率高于 P2/P3（无数据）；Route B 定制需求存在（无回复验证）。
**【建议】**：当前阶段 Route A 优先，P2 为主池，P3 可测；不依赖 Google Places（本轮用 WebSearch 验证可行）。

---

## 2. Inventory Root Cause（症状 → 根因 → 证据 → 修改 → 验证）

### 症状
08-08 ~ 08-12 连续 Inventory：target=30，**actual=0**，status=partial/stopped，stop_reason=max_loops_reached，current_step=inventory_start。

### 根因（多因叠加，按影响排序）
1. **【A-决定性】新线索来源断裂**：发现层（Lane A）依赖 Google Places / SerpAPI，`.env` 无任何 API key → provider 全 `configuration_blocked`，每轮 0 请求 0 结果。存量候选耗尽后无新线索。
2. **【D-实际=0 的直接原因】存量候选被历史发送拦截**：官网扫描能找到的邮箱几乎全部 `previously_sent`（08-12 当天 inventory_lane 提交 14 条，14/14 命中 previously_sent）。候选池是"有官网无邮箱"的商店，其邮箱大多属于已发送组织。
3. **【F-空转放大】候选 SQL 无已处理排除**：同一批 35 条被 5 loops × 每天重复扫描，`max_loops_reached` 是空转终止而非产出终止。
4. **【C-次要】curl fallback 无 `--compressed`**：gzip 响应触发 UnicodeDecodeError → 误判 network_retry_pending。
5. **【E-数据毒化】14 条伪邮箱 lead**（`foo@2x.jpg`/sentry hash/`www.` local-part）占用名额且永不 sendable。

### 证据
- `.env` 无 API key；`provider_request_audit` 全 `configuration_blocked`；retail_city_queue Nashville `provider_errors=24`。
- 08-12 `manual_email_submission`：14 条 `previously_sent`（customercare@easternnational.org 等，lead 542/543/625）。
- 25 条官网 dry-run 扫描：0 有效邮箱 / 19 no_email / 4 网络失败 / 2 伪邮箱（修复前）。
- 14 条垃圾邮箱（hygiene 权威判定：`@2x.jpg`、`sentry.io`、`www.kll@`、`xxx@xxx` 等）。

### 修改（已实际完成）
| 文件 | 修改 | 原因 |
|------|------|------|
| `inventory_monitor_executor.py` | curl 加 `--compressed` + binary 解码（utf-8/latin-1 fallback） | 修复 gzip UnicodeDecodeError 误判网络失败 |
| `inventory_monitor_executor.py` | `extract_emails_from_html` 接入权威 `email_hygiene` 过滤伪邮箱 | 图片名/系统邮箱不再被当真实联系 |
| `bd_orchestrator.py` | 候选 SQL 增加 `NOT EXISTS manual_email_submission(inventory_lane)` 排除已提交 | 停止同批 35 条重复空转 |
| `bd_orchestrator.py` | evidence_url 用 `ev_url`（实际找到邮件的页面）而非首页 | 子页邮箱在主页重验失败 |
| `leads` 表 | 清空 12 条真伪邮箱（保留 2 条审计样本：Toys N More/Village Toymaker） | 伪邮箱 lead 回官网扫描池 |
| `leads` 表 + `icp_profile.py` | 新增 icp_route/icp_priority/icp_reason/icp_classified_at/icp_version 字段并回填 | ICP 接入 |

### 验证
- import OK；伪邮箱过滤单测 PASS（`infant_and_toddler_235x235@2x.jpg` 被过滤，mailto 保留）。
- 回归测试 34 passed + 32 subtests（compact renderer / business rules / SMTP authority）。
- live inventory 25 分钟验证：扫描在跑、提交链路正常、被 previously_sent 拦截（证实根因 D）；因扫描过慢手动停止并标记 stopped。

---

## 3. 实际代码修复清单

见上表。全部为**正式生产模块**内最小修复，未新增第二 Inventory 系统、未建日期型临时脚本、未改锁定模板、未动 SMTP。

---

## 4. First Recovered Leads（本轮实际入库 11 条，其中 4 条 Broad Ready）

| id | store | city,state | type | website | email | evidence | Route/Pri | 状态 |
|----|-------|-----------|------|---------|-------|----------|-----------|------|
| 774 | Village Tinker | Maryville,TN | gift_shop | villagetinker.com | villagetinker@villagetinker.com | contact page | B/P2 | ✅ Ready |
| 779 | Stoney's Gift & Toy Shoppe | Covington,KY | toy_store | stoneystoys.com | sstonebraker1616@aol.com | official contact | A/P3 | ✅ Ready |
| 780 | Moonlite Comics & Models | Frankfort,KY | comic_book_store | moonlitecomics.com | support@thegamecentre.net | directory | A/UNQUALIFIED | ✅ Ready（第三方域待验） |
| 783 | Legit MTG | Owensboro,KY | game_store | legitmtg.com | sales@legitmtg.com | store domain | A/P2 | ✅ Ready |
| 777 | Collector's Connection | Dyersburg,TN | card_store | — | kaijudogirl@yahoo.com | directory | A/P3 | ❌ shared_domain 拦截 |
| 781 | TTD Cards Frankfort | Frankfort,KY | card_store | — | ttdcardsfrankfort@hotmail.com | directory | A/P3 | ❌ shared_domain 拦截 |
| 775/776/782/784 | 4 条无邮箱（Scruffy/Just Roll/Knight's/Go! Toys） | TN/KY | — | — | NO_EMAIL | directory | A/U | manual_review_needed |
| 778 | Record Rack | Pine Bluff,AR | record_store | recordrack-pb.com | recordrack2801@aol.com | official | U/NEGATIVE | do_not_contact |

> Recovery Gate 1（>0 真实合格 Lead）：✅ **达成**（4 条 Broad Ready + 5 条 qualified new with email）
> Recovery Gate 2（≥10 合格 Lead）：❌ **部分达成**（11 条入库，4 条 Ready；"合格"定义按 Broad Ready=4）——受限于手工人力采集速度，未凑满 10 条 Ready。阻塞原因见下。

---

## 5. Recovery Metrics

```
icp_recovery_leads_imported : 11
with_email                   : 7
P1 / P2 / P3                 : 0 / 2 / 3
UNQUALIFIED                  : 5
NEGATIVE_ICP                 : 1
qualified_new_with_email     : 5
broad_ready_tn_ar_ky (主池)   : 4
website_scan_dryrun          : scanned=25, found_valid=0, no_email=19, network_fail=4
garbage_emails_cleared       : 14
total_leads                  : 749 (738→749, +11)
send_log / smtp_accepted     : 451 / 448
customer_smtp_connections    : 0
today_inventory_submissions  : previously_sent=14
```

**卡在哪一层**：存量官网扫描（provider 有 → 官网可达 → 但 76% 无公开邮箱 + 可找到的邮箱大多 previously_sent）→ 主瓶颈是 **新线索发现能力**（无 Places/SerpAPI key）+ **历史发送覆盖了三州大部分有邮箱商店**。

---

## 6. 结论 / 阻塞

- **Recovery Gate 1 ✅**、**Gate 2 部分**（4 Ready / 需 10）、**Gate 3（30/日）❌**。
- **30/日 不可达的真实原因**（非 KPI 妥协）：① 三州独立零售店存量有限且大部分已被历史发送触达；② 官网直接公开邮箱的比例低（25 条扫描 0 有效）；③ 自动发现层缺 API key。**市场上限需进一步数据证明**——建议下一轮做一次"三州全城市候选店清单 vs 已发送/已覆盖"的饱和分析。
- **矛盾点记录**：`shared_domain_org_history` 把 yahoo/hotmail 免费邮箱视为组织历史拦截（Collector's Connection、TTD Cards 被挡），但用户明确"Gmail 等泛邮箱不是 blocker"。此规则对免费邮箱域判定过严，需复核 `broad_ready.py` 的 shared_domain 逻辑（本轮未改，只记录）。

## 7. 建议下一步（供后续 ChatGPT/Agent）

1. 给 `.env` 配置 Google Places 或 SerpAPI key（或新增无 key 的 WebSearch 采集路径）→ 恢复自动发现层。
2. 复核 `broad_ready.py` 对免费邮箱域的 shared_domain 拦截（与 ICP P3 冲突）。
3. 三州未覆盖城市（Spring Hill/Maryville/Sevierville/Dyersburg/Pine Bluff/Texarkana/Covington/Frankfort/Henderson/Georgetown）用 WebSearch 逐城补齐。
4. 官网扫描加 `--compressed` 后重跑 154 条"有官网无邮箱"候选（先做 35 条限时扫描，避免 25 分钟超时）。
5. 为后续 Supervised Send 准备：把本轮 4 条 Ready 线索走 preflight + authorization 影子链验证。

---
*本轮备份：`backup/p0_icp_recovery_20260812_172846/`（SHA da0a6a9a9dbe5aa6）*
