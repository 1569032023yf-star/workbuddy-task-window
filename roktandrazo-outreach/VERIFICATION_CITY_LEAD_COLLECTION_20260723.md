# 城市线索采集链路专项验收报告

## City Lead Collection Pipeline Verification Report

**日期**: 2026-07-23 16:06 CST
**范围**: Nashville TN 线索采集链路静态全量验证
**禁止**: 真实 SMTP 发送、生产 Outreach、Automation 修改

---

## 一、真实采集调用链确认

### 1.1 Inventory 实际调用链

`stage_inventory()` (bd_orchestrator.py:512-653) 调用链：

```
stage_inventory()
 ├─ seed_default_queue(city_conn)          # INSERT OR IGNORE 7 cities into retail_city_queue
 ├─ activate_next_city(city_conn)          # 获取当前 active city（纯 SQLite 状态读取）
 ├─ SELECT COUNT(*) FROM leads WHERE ...   # 统计 Strict A0 数量
 └─ LOOP (max 5):
     ├─ Lane 1: SELECT * FROM leads WHERE status='manual_review_needed' AND confidence_score='B' AND city=? AND state=? LIMIT 20
     ├─ Lane 2: (回退) SELECT * FROM leads WHERE status='contact_form_pool' AND city=? AND state=? LIMIT 20
     ├─ httpx.Client.get(website)           # HTTP fetch 已知官网
     ├─ extract_emails(resp.text)           # 正则提取邮箱
     ├─ is_suppressed(email)                # 检查 suppression_list
     └─ UPDATE leads SET email=?, ... WHERE id=?  # 升级为 A0
```

### 1.2 关键问题逐项回答

| # | 问题 | 答案 | 证据 |
|---|------|------|------|
| 1 | 当前是普通网络搜索、地图搜索，还是只处理已有候选？ | **只处理已有候选** | bd_orchestrator.py:571-577: `SELECT * FROM leads WHERE status='manual_review_needed' ...` — 从已有数据库查询，无任何搜索 API 调用 |
| 2 | 是否真实接入任何地图搜索来源？ | **否，未接入** | bd_orchestrator.py 中无 google_maps/places/maps API 调用痕迹；inventory_recovery_daemon.py:45-57 `auto_search_new_candidates()` 是空桩函数（returns 0） |
| 3 | 如果有，具体来源和调用方式？ | **不存在** | 不适用 |
| 4 | 如果没有，明确说明 | **当前并未实现任何地图搜索** | 见上 |
| 5 | 20 query family 是配置还是已连接搜索执行器？ | **仅为配置，未连接搜索执行器** | retail_city_queue.py 的 `search_queries()` 仅生成字符串列表，但 stage_inventory() 从未调用此函数。bd_orchestrator.py only imports `activate_next_city, seed_default_queue`，not `search_queries` |
| 6 | 城市分页和查询分页保存在哪？ | **未实现分页保存** | retail_city_queue 表有 `active_query_family`、`page_cursor` 列，但 stage_inventory() 从不调用 `checkpoint()`，这些列永远为 NULL |
| 7 | Inventory 下次如何从原游标恢复？ | **无法恢复** | 因为 stage_inventory() 不调用 `checkpoint()`，不写入 `page_cursor` 或 `active_query_family`。城市状态仅 `status` 字段（active/pending/paused） |
| 8 | 新增线索是否全部经过 history_crosscheck？ | **看入口而定（见第二节）** | bd_db.insert_lead() 有 crosscheck；但多个直接 INSERT 路径绕过 |

### 1.3 核心发现

```
stage_inventory 的工作方式:
  输入: 数据库中已有的 B2/manual_review_needed 候选（已有 store_name, city, state, official_website）
  处理: HTTP fetch 已知官网 → 正则提取邮箱 → 升级为 A0
  输出: 0 个新 lead（仅 UPDATE，不 INSERT）
  
  它不做:
  ✗ 不使用 Google/Bing/任何搜索引擎 API
  ✗ 不使用 Google Maps / Places API
  ✗ 不执行 20 个 query family 作为搜索
  ✗ 不发现数据库中不存在的商店
  ✗ 无分页逻辑
  ✗ 不写入 checkpoint/游标
```

**20 query family 处于"僵尸配置"状态**：定义在 outreach_control.py:26-33，由 retail_city_queue.py:36-37 生成查询字符串，但没有任何生产代码消费这些字符串去执行搜索。

---

## 二、所有新增线索入口清单

### 2.1 生产活跃入口（通过 bd_db.insert_lead → 经过 history_crosscheck）

| 文件 | 生产使用 | 创建新 lead | 调用 bd_db.insert_lead | history_crosscheck | 绕过风险 |
|------|---------|------------|----------------------|-------------------|---------|
| `bd_db.py` (insert_lead) | ✅ 是 | ✅ 是 | 自身 | ✅ cross_check() | 无 |
| `agent_lead_collector.py` | ✅ 是 | ✅ 是 | ✅ | ✅ | 无 |
| `auto_collector.py` | ✅ 是 | ✅ 是 | ✅ | ✅ | 无 |
| `import_new_leads.py` | ✅ 是 | ✅ 是 | ✅ | ✅ | 无 |

### 2.2 绕过入口（直接 INSERT INTO leads，绕过 history_crosscheck）

| 文件 | 生产使用 | 创建新 lead | bd_db.insert_lead | history_crosscheck | 绕过风险 |
|------|---------|------------|-------------------|-------------------|---------|
| `db.py` (旧 insert_lead) | ⚠️ LEGACY | ✅ 是 | ❌ 自己实现 | ❌ 仅 domain hash 去重 | **P0 绕过** |
| `pipeline.py` | ⚠️ LEGACY | ✅ 是 | ❌ 调 db.py | ❌ | **P0 绕过** |
| `new_lead_factory.py` | 🔧 手动工具 | ✅ 是 | ❌ 直接 INSERT | ❌ 自己实现简单去重 | **P0 绕过** |
| `import_phase2.py` | 📦 一次性导入 | ✅ 是 | ❌ 直接 INSERT | ❌ | **历史遗留** |
| `import_phase3.py` | 📦 一次性导入 | ✅ 是 | ❌ 直接 INSERT | ❌ | **历史遗留** |
| `import_phase4.py` | 📦 一次性导入 | ✅ 是 | ❌ 直接 INSERT | ❌ | **历史遗留** |
| `import_phase4_b2.py` | 📦 一次性导入 | ✅ 是 | ❌ 直接 INSERT | ❌ | **历史遗留** |
| `import_phase4_b3.py` | 📦 一次性导入 | ✅ 是 | ❌ 直接 INSERT | ❌ | **历史遗留** |
| `import_phase4_b4.py` | 📦 一次性导入 | ✅ 是 | ❌ 直接 INSERT | ❌ | **历史遗留** |
| `push_to_30.py` | 🔧 手动工具 | ✅ 是 | ❌ 直接 INSERT | ❌ | **P0 绕过** |
| `recovery_replay.py` | 🔧 手动工具 | ✅ 是 | ❌ 直接 INSERT | ❌ | **P0 绕过** |
| `scale_to_30.py` | 🔧 手动工具 | ✅ 是 | ❌ 直接 INSERT | ❌ | **P0 绕过** |
| `scale_brand_insert.py` | 🔧 手动工具 | ✅ 是 | ❌ 直接 INSERT | ❌ | **P0 绕过** |
| `brand_candidate_importer.py` | 🔧 手动工具 | ✅ 是 | ❌ 直接 INSERT | ❌ | **P0 绕过** |

### 2.3 不创建新 lead 的入口

| 文件 | 说明 |
|------|------|
| `stage_inventory()` (bd_orchestrator.py) | 仅 UPDATE 已有 lead（升级 email/status） |
| `inventory_recovery_daemon.py` | `auto_search_new_candidates()` 是空桩函数，returns 0 |
| `inventory_recovery_loop.py` | 无 INSERT INTO leads |
| `inventory_expansion_runner.py` | 处理已有候选，不新建 lead |
| `facebook_enrichment/*` | 仅更新已有 lead 的 Facebook 数据 |
| `b_pool_enrichment.py` | 写入 lab_candidates/lab_meta 表（非 leads） |
| `review_workflow.py` | 仅更新 review 状态，写入 review_log |
| `fast_lead_discovery.py` | 无数据库写入（纯 email 提取引擎） |

### 2.4 绕过历史交叉核验的关键文件

**必须修复的 P0 绕过路径**：

1. **`new_lead_factory.py`** (line 207-224): 直接 `INSERT INTO leads`，仅做简单 store_name+city+state 和 domain_hash 去重，**不调用 history_crosscheck**。
   - 修复：将 `c.execute("INSERT INTO leads ...")` 替换为 `bd_db.insert_lead(lead)`

2. **`db.py` insert_lead()** (line 115-155): 旧版 insert_lead，仅使用 `INSERT OR IGNORE` + domain_hash 去重，**不调用 history_crosscheck**。被 `pipeline.py` 调用。
   - 修复：废弃 db.py 的 insert_lead，统一使用 bd_db.insert_lead()

3. **`recovery_replay.py`** (line 108): 直接 INSERT，**不调用 history_crosscheck**。

4. **`push_to_30.py`, `scale_to_30.py`, `scale_brand_insert.py`, `brand_candidate_importer.py`**: 手动工具脚本，直接 INSERT。

---

## 三、Nashville 安全测试数据库验证

### ⚠️ 执行状态

由于当前 WorkBuddy 沙箱环境限制，**Python 运行时无法执行**（所有 Bash/PowerShell 命令返回 Exit Code 1，包括 `echo hello`）。基于生产数据库副本的受控 Nashville 测试无法在本轮执行。

### 静态代码分析替代结果

基于对 `stage_inventory()` 源代码的完整审查：

| 指标 | 预期值 | 说明 |
|------|--------|------|
| 实际搜索来源 | **无** | 无搜索引擎 API 调用 |
| 实际请求方式 | httpx GET 已知网站 | 仅 fetch 已有 official_website |
| 搜索结果总数 | **0** | 不会产生搜索结果 |
| 新发现商家数量 | **0** | 不会创建新 lead |
| unique domain 数量 | **0** | 不会发现新 domain |
| 官方网站数量 | N/A | 仅使用数据库中已有的 URL |
| 找到邮箱数量 | 取决于已有 B2 候选的网站 | HTTP fetch 已有 URL 后提取 |
| Strict A0 数量 | 取决于 Lane 1/2 升级数 | 通过 UPDATE 升级已有 lead |
| Manual Review 数量 | 无变化 | 仅升级/不变 |
| Contact Form 数量 | 无变化 | 仅升级/不变 |
| Duplicate 数量 | 0 | 不创建新 lead |
| Previously Sent 数量 | 0 | 不检查 send_log（仅检查 suppression） |
| Reject 数量 | 0 | 不写入 rejection |
| 当前分页游标 | **NULL** | checkpoint() 从未被调用 |
| 下一次恢复位置 | **不可恢复** | 无状态写入 |

### 正式声明

```
city queue implemented, source discovery not implemented
```

- **city queue**: ✅ retail_city_queue 表结构完整，7 城市已 seeded，单城市锁机制通过唯一部分索引实现
- **source discovery**: ❌ 无任何搜索引擎/地图 API 调用，20 query family 为死配置，`auto_search_new_candidates()` 为空桩

---

## 四、单城市锁验证

### 4.1 锁机制分析

`retail_city_queue` 表通过 SQLite 唯一部分索引实现单城市锁：

```sql
CREATE UNIQUE INDEX idx_retail_city_only_one_active 
ON retail_city_queue(status) WHERE status='active'
```

### 4.2 激活逻辑

`activate_next_city()` (retail_city_queue.py:20-33):
1. 如果已有 active 城市 → 直接返回（不切换）
2. 检查 paused_by_runtime_limit 城市 → 恢复
3. 选择 priority 最小 pending 城市
4. 无 pending → 抛 RuntimeError

### 4.3 验证结论

| 检查项 | 结果 | 证据 |
|--------|------|------|
| active city 只有 Nashville | ✅ | activate_next_city 永远返回当前 active（不切换） |
| 测试后仍是 Nashville | ✅ | stage_inventory 不调用 complete_if_exhausted() |
| 未切换 Memphis | ✅ | 不存在自动切城逻辑 |
| 未切换 Arkansas | ✅ | 不存在自动切��逻辑 |
| 未切换 Kentucky | ✅ | 不存在自动切城逻辑 |
| 运行结束后状态 | active | 不调用 checkpoint(paused=True) |
| query family 未完成时不能标记 exhausted | ✅ | complete_if_exhausted() 从未被调用 |

⚠️ **注意**: `stage_inventory()` 不使用 `checkpoint()` 和 `complete_if_exhausted()`，所以城市状态仅有 `active`/`pending` 两个实际值。

---

## 五、历史交叉核验验证

### 5.1 history_crosscheck.py 交叉检查逻辑

`cross_check()` 函数（history_crosscheck.py:33-74）执行以下检查：

1. **email 规范化**: `normalize_email()` → 小写 + RFC 验证
2. **leads 表匹配**: 同时检查 exact_email、business_identity（店名+城市+州）、same_site（域名+身份）
3. **send_log 检查**: `SELECT FROM send_log WHERE email=? AND status='sent'`
4. **bounce_log 检查**: `SELECT FROM bounce_log WHERE email=? AND bounce_type IN ('hard','policy')`
5. **suppression_list 检查**: `SELECT FROM suppression_list WHERE email=?`
6. **reply_log 检查**: 如果 reply_log 表存在

### 5.2 场景预期结果

| 场景 | 预期结果 | cross_check 返回值 |
|------|---------|-------------------|
| 全新商家 | new_candidate | `{'result': 'new_candidate'}` → INSERT 允许 |
| 相同邮箱历史已存在 | exact_duplicate | `{'result': 'exact_duplicate'}` → INSERT 阻止，更新已有 lead 的 notes |
| 相同商家不同邮箱 | identity_duplicate_new_email | `{'result': 'identity_duplicate_new_email'}` → INSERT 阻止 |
| 历史已发送 | previously_sent | `{'result': 'previously_sent'}` → INSERT 阻止 |
| hard bounce | bounced | `{'result': 'bounced'}` → INSERT 阻止 |
| suppression | suppressed_or_unsubscribed | `{'result': 'suppressed_or_unsubscribed'}` → INSERT 阻止 |
| 同 domain 不同真实门店 | related_location_not_duplicate | ⚠️ 需验证：当前逻辑中 same_site 要求 `same_identity AND same_site`，仅同 domain 不同店名不触发 |

### 5.3 ⚠️ 潜在问题：同 domain 不同门店

`cross_check()` 的 same_site 条件为：
```python
same_site = bool(website_host and website_host == host(item.get('official_website', '')) and same_identity)
```

**`same_identity` 要求店名+城市+州完全匹配**。如果两个不同门店共享同一域名（如连锁店），仅域名相同不会触发匹配。这是**有意设计**（CODEX_HANDOFF 第 34 行注释：`Same domain alone is not an identity duplicate`），但需要确认是否符合业务预期。

---

## 六、最终结论

### 逐条回答

| # | 问题 | 答案 |
|---|------|------|
| 1 | 当前系统是否真正具备网络搜索？ | **❌ 不具备。** 无任何搜索引擎 API (Google/Bing/SerpAPI) 集成。`stage_inventory()` 仅从数据库查询已有候选并通过 HTTP fetch 已知网站提取邮箱。 |
| 2 | 当前系统是否真正具备地图搜索？ | **❌ 不具备。** 无 Google Maps / Places API 调用。`inventory_recovery_daemon.auto_search_new_candidates()` 是空桩函数 (returns 0)。 |
| 3 | 当前系统是否只是城市队列加已有候选处理�� | **✅ 是。** `retail_city_queue` 管理 7 个城市的激活状态，但 `stage_inventory()` 仅处理数据库中已有的 B2/manual_review_needed 和 contact_form_pool 候选。不产生任何新发现。 |
| 4 | Nashville 第一个 query family 是否真实执行？ | **❌ 未执行且无法执行。** `search_queries()` 可生成 `"board game store Nashville Tennessee"` 字符串，但没有任何搜索执行器消费这个字符串。沙箱限制也阻止了实际测试。 |
| 5 | 搜索分页和城市游标是否真实可恢复？ | **❌ 不可恢复。** `checkpoint()`/`complete_if_exhausted()` 函数完整，但 `stage_inventory()` 不调用它们。`page_cursor`、`active_query_family` 等列永远为 NULL。 |
| 6 | 所有真实新增入口是否已接入历史交叉核验？ | **⚠️ 部分。** `bd_db.insert_lead()` → ✅ 已接入。但 `new_lead_factory.py`、`recovery_replay.py`、`db.py`、`push_to_30.py`、`scale_*.py`、`brand_candidate_importer.py` 等直接 INSERT 路径绕过 history_crosscheck。 |
| 7 | 当前是否具备继续让 Codex 完善城市采集器的条件？ | **✅ 是。** 基础设施已就位：retail_city_queue 状态管理完整、单城市锁机制正确、20 query family 配置就绪、checkpoint/恢复 API 已实现、history_crosscheck 逻辑正确。缺乏的是：将 query family 连接到真实搜索 API 的**搜索执行器**。 |
| 8 | 当前是否可以执行生产数据库迁移？ | **⏸️ 条件性可以。** 迁移脚本 (migrate_city_outreach_40.py) 已在生产库副本上两次成功执行。但建议在迁移前：(a) 确保有生产库完整备份；(b) 确认 WorkBuddy Automation 已更新为正确调度时间。 |

---

## 七、Codex 修复所需工作清单

### P0 - 必须修复（阻止数据完整性）

1. **统一 INSERT 入口**: 废弃所有直接 `INSERT INTO leads` 路径，统一到 `bd_db.insert_lead()`
   - `new_lead_factory.py:207` → 改为 `bd_db.insert_lead()`
   - `db.py:115` → 标记为废弃，重定向到 `bd_db.insert_lead()`
   - `recovery_replay.py:108`, `push_to_30.py:36`, `scale_to_30.py:65`, `scale_brand_insert.py:41`, `brand_candidate_importer.py:154` → 同上

### P1 - 必须实现（城市采集核心能力缺失）

2. **搜索执行器**: 实现将 query family 字符串发给搜索 API 的执行器
   - 需要接入: Google Custom Search API / SerpAPI / Bing Search API
   - 需要实现: 从搜索结果提取商家名称��地址、官网 URL
   - 需要实现: 将提取结果通过 `bd_db.insert_lead()` (含 history_crosscheck) 写入

3. **在 stage_inventory 中连接搜索执行器**:
   - 调用 `retail_city_queue.search_queries()` 获取 query strings
   - 调用搜索执行器获取结果
   - 每个 query family 完成后调用 `checkpoint()` 保存游标

4. **分页恢复**: `checkpoint()` 已实现但未被调用，需要在 stage_inventory 中集成

### P2 - 建议改进

5. `stage_inventory` 中的直接 `UPDATE leads` 操作（line 610-615）绕过了 `history_crosscheck`。虽然此处是升级已有 lead（不是新建），但升级时也应检查该邮箱是否已被 suppression/send_log 覆盖（已通过 `is_suppressed()` 检查了 suppression，但未检查 send_log bounce）。

---

## 八、验证限制说明

- **沙箱限制**: 当前 WorkBuddy 会话无法执行 Python/Bash/PowerShell 命令，无法进行动态测试
- **数据库验证**: 生产库 `bd_leads.db` 存在但无法通过 SQLite 读取内容
- **静态分析完整性**: 所有 Python 源码已完整阅读审查，结论基于源码静态分析
- **测试脚本**: `_test_nashville.py` 和 `_simple_check.py` 已准备好，环境恢复后可立即执行
