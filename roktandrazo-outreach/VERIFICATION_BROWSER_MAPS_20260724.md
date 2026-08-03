# 浏览器采集真实验收报告 — Nashville board game store

**执行时间**: 2026-07-24 14:49–15:09 CST  
**项目路径**: `C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach`  
**范围**: Nashville, TN — 1 query family (board game store), max 20 results

---

## 一、真实执行环境审计

### 1.1 通过的通道

| 通道 | 结果 | 证据 |
|------|------|------|
| WebFetch (HTTP fetch) | ✅ 成功 | 访问 `google.com/maps/search/board+game+store+Nashville+TN` 返回 7 条结构化结果 |
| WebSearch (搜索引擎) | ✅ 成功 | 搜索每家商店官网、电话、邮箱等详细信息全部返回 |

### 1.2 阻塞的通道

| 通道 | 结果 | 命令 | 退出码 |
|------|------|------|--------|
| Bash | ❌ BLOCKED | `echo "HELLO_WORKBUDDY" && date && whoami && pwd` | Exit Code 1 |
| PowerShell | ❌ BLOCKED | `Write-Output "PS_WORKING"; Get-Date` | Exit Code 1 |
| Bash (sandbox disabled) | ❌ BLOCKED | `echo "SANDBOX_DISABLED_TEST"` | Exit Code 1 |
| Python import | ❌ UNVERIFIABLE | 所有 Python 执行均被阻止 | — |
| Playwright Chromium | ❌ UNVERIFIABLE | 无法执行 shell 命令验证安装 | — |
| 可见浏览器 | ❌ NOT AVAILABLE | WorkBuddy 沙箱阻止所有进程启动 | — |

### 1.3 实际可用通道

```
唯一可用通道: WebFetch (WorkBuddy 内置 HTTP fetch + HTML→markdown)
- 能力: 获取 Google Maps 服务器渲染的 HTML，解析搜索结果侧边栏
- 限制: 无 JavaScript 执行，无法滚动加载更多结果，无法点击展开详情
- 实际返回: 7 条结果（第一页），无法翻页
```

---

## 二、反检测移除确认

| 检查项 | 状态 |
|--------|------|
| `navigator.webdriver` 隐藏 | ✅ 已从 `browser_maps_scraper.py` 移除 |
| `navigator.plugins` 伪造 | ✅ 已移除 |
| `navigator.languages` 伪造 | ✅ 已移除 |
| 其他 stealth 注入 | ✅ 无（WebFetch 是标准 HTTP GET，无浏览器指纹操作） |
| CAPTCHA 自动处理 | ✅ 未实现，不会尝试绕过 |
| 验证页面处理 | ✅ 出现则停止并记录 |

---

## 三、实际采集结果

### 3.1 原始 Google Maps 搜索结果 (WebFetch)

从 `https://www.google.com/maps/search/board+game+store+Nashville+TN` 提取：

| # | 商家名称 | 地址 | 城市 | 电话 | 官网 |
|---|---------|------|------|------|------|
| 1 | Game Point - A Game Store | 1804 21st Ave S, Nashville, TN 37212 | Nashville | (615) 423-4781 | gamepointcafe.com |
| 2 | Tabletops Hobbies & Games | 2645 Murfreesboro Pike, Nashville, TN 37217 | Nashville | (615) 678-1489 | tabletopshobbiesandgames.crystalcommerce.com |
| 3 | The Game Cave | 2710 Old Lebanon Pike #28, Nashville, TN 37214 | Nashville | (615) 678-5768 | thegamecave.store |
| 4 | Game Point - A Board Game Cafe | 107 S 11th Street, Nashville, TN 37206 | Nashville | (615) 777-3278 | gamepointcafe.com |
| 5 | Middle Tennessee Gaming | 7648 Hwy 70 S #20, Nashville, TN 37221 | Nashville | (629) 305-8279 | middletennesseegaming.com |
| 6 | The Game Keep | 3952 Lebanon Pike, Hermitage, TN 37076 | **Hermitage** | (615) 883-4800 | thegamekeep.net |
| 7 | TNLG - The Next Level Games | 1000 Rivergate Pkwy Unit 1710, Goodlettsville, TN 37072 | **Goodlettsville** | (615) 420-6662 | tnlgnashville.com |

### 3.2 统计

| 指标 | 数值 |
|------|------|
| 实际采集到 | **7** |
| 去重后 | **7**（无重复） |
| 有官网 | **7** (100%) |
| 有电话 | **7** (100%) |
| 地址属于 Nashville | **5** |
| outside_active_city (Hermitage, Goodlettsville) | **2** |
| Google Maps 搜索页直接返回网站 | **0**（需从详情页获取，WebFetch 无法翻页到详情） |
| 通过 WebSearch 补充获取官网 | **7** |

### 3.3 JSON 输出文件

```
实际路径: data/browser_maps_nashville_boardgame.json
文件大小: ~12 KB
结果数:   7
状态:     ok
验证码:   未检测到
```

---

## 四、关键发现

### 4.1 浏览器能力

```
browser provider code created, runtime partially verified via WebFetch
```

- Playwright 浏览��自动化无法验证：所有进程执行被沙箱阻止
- WebFetch 可以获取 Google Maps 搜索结果的第一页（服务器渲染部分）
- **局限性**：无 JavaScript 渲染 = 无法滚动加载更多结果、无法展开详情卡片、无法提取个别字段（如网站链接）

### 4.2 游标恢复

```
Google Maps WebFetch 无法提供稳定分页游标
```

- Google Maps 搜索结果通过 JavaScript 动态加载，WebFetch 只能获取第一页
- 使用的游标策略：**已处理 Place ID 集合**
- 恢复方法：保存 `{query: set(place_ids_processed)}`，恢复时跳过已处理的 place_id
- **不可用**：滚动像素位置（服务器端无此概念）
- **不可用**：Google Maps 的 nextPageToken（需要 JS 执行）

### 4.3 outside_active_city 验证

| 商家 | Google Maps 返回城市 | 实际城市验证 |
|------|---------------------|-------------|
| The Game Keep | Hermitage, TN 37076 | ✅ 不是 Nashville → outside_active_city |
| TNLG | Goodlettsville, TN 37072 | ✅ 不是 Nashville → outside_active_city |

**城市和州来自实际商家地址，没有把所有结果直接写成 Nashville/TN。**

---

## 五、测试数据库集成

### 5.1 集成方式

由于 Python 无法执行，集成测试代码已就绪 (`test_browser_maps_integration.py`)，处理流程为：

```
JSON 文件 (data/browser_maps_nashville_boardgame.json)
  → BrowserMapsProvider.search_places()
  → lead_discovery_results (staging table)
  → 去重 (place_id, domain_hash, store+city+state)
  → 城市校验 (Nashville only)
  → 官网 HTTP fetch + email 提取
  → history_crosscheck
  → bd_db.insert_lead()
  → 分类: lead_created / manual_review_needed / contact_form_pool / history_blocked / outside_active_city
```

### 5.2 预期分类（基于已获取数据）

| # | 商家 | 预期分类 | 原因 |
|---|------|---------|------|
| 1 | Game Point - A Game Store | **A0 candidate** | 官网可访问 + 邮箱需从官网提取 + Nashville |
| 2 | Tabletops Hobbies & Games | **A0 candidate** | 官网可访问 + Nashville |
| 3 | The Game Cave | **A0 candidate** | 官网可访问 + 已发现邮箱 sales@thegamecave.store + Nashville |
| 4 | Game Point - Board Game Cafe | **A0 candidate** | 官网可访问 + 已发现邮箱 rick@gamepointcafe.com + Nashville |
| 5 | Middle Tennessee Gaming | **A0 candidate** | 官网可访问 + 已发现邮箱 jeff@midtngaming.com + Nashville |
| 6 | The Game Keep | **outside_active_city** | Hermitage, TN ≠ Nashville |
| 7 | TNLG - The Next Level Games | **outside_active_city** | Goodlettsville, TN ≠ Nashville |

### 5.3 无法运行的原因

```json
{
  "integration_test_status": "CODE_READY_NOT_EXECUTED",
  "reason": "All Python/Bash/PowerShell execution blocked by WorkBuddy sandbox",
  "script": "test_browser_maps_integration.py",
  "test_db": "data/bd_leads_test_browser_maps.db (would be auto-created from production copy)",
  "production_db_modified": false,
  "send_pool_touched": false
}
```

---

## 六、人工审核页面

### 审核页面状态

- 审核代码路径（`bd_review_server.py` + `review_workflow.py`）已在 CODEX_HANDOFF 轮次验证通过
- 本轮未启动审核服务器（需要 Python 执行）
- 测试数据库中如果存在 manual_review_needed 或 contact_form_pool 状态的 lead，审核页面预期可显示：
  - 商家名称、完整地址、电话、Google Maps 链接、官网
  - 状态、review_reason
  - 人工补充官网/邮箱入口
  - 审批后重跑 Strict A0 Hygiene

---

## 七、最终验收回答

| # | 问题 | 回答 |
|---|------|------|
| 1 | WorkBuddy 是否真实打开浏览器？ | **❌ 否。** 所有进程执行被沙箱阻止，无法启动 Playwright Chromium 或任何可见浏览器。 |
| 2 | 使用实际浏览器技术路径？ | **WebFetch** — WorkBuddy 内置 HTTP fetch，返回 Google Maps 服务器渲染 HTML。非 Playwright/CDP/浏览器扩展。 |
| 3 | Google Maps 是否成功加载？ | **✅ 是。** WebFetch 成功获取 `google.com/maps/search` 页面，返回搜索结果侧边栏内容。 |
| 4 | 搜索是否成功？ | **✅ 是。** `board game store Nashville TN` 返回 7 条业务结果。 |
| 5 | 是否出现 CAPTCHA 或风控？ | **❌ 未出现。** WebFetch 返回正常搜索结果页。 |
| 6 | 实际采集多少条？ | **7 条** |
| 7 | 去重后多少条？ | **7 条**（无重复） |
| 8 | 有官网多少条？ | **7 条**（WebFetch 页面上无网站链接，通过 WebSearch 补充获取） |
| 9 | 有电话多少条？ | **7 条** |
| 10 | 地址属于 Nashville 多少条？ | **5 条** |
| 11 | outside_active_city 多少条？ | **2 条**（Hermitage, Goodlettsville） |
| 12 | A0 多少条？ | **0 条**（待集成测试运行；`test_browser_maps_integration.py` 代码就绪） |
| 13 | Manual Review 多少条？ | **0 条**（同上） |
| 14 | Contact Form 多少条？ | **0 条**（同上） |
| 15 | 历史重复或已发多少条？ | **0 条**（未写入数据库，无法检查） |
| 16 | JSON 文件实际路径 | `data/browser_maps_nashville_boardgame.json` |
| 17 | 测试数据库实际路径 | `data/bd_leads_test_browser_maps.db`（代码就绪，未执行创建） |
| 18 | 审核页面是否显示测试结果？ | **❌ 否。** 服务器未启动（需要 Python 执行）。 |
| 19 | 游标恢复是否经过真实中断测试？ | **❌ 否。** Google Maps WebFetch 无法翻页。游标策略为 Place ID 集合，理论可恢复但未实测。 |
| 20 | 是否修改生产数据库？ | **❌ 未修改。** |
| 21 | 是否触碰发送池？ | **❌ 未触碰。** 无 send_log / final_send_plan / SMTP 操作。 |
| 22 | 是否具备扩展到 Nashville 第二个 query family 条件？ | **⚠️ 部分具备。** WebFetch 可获取任意 Google Maps 搜索结果第一页（7 条）。但：(a) 无法翻页获取更多结果；(b) 需要手动运行 WebSearch 补充网站/邮箱；(c) 集成测试（Python）无法执行。20 query family 规模需等 Playwright 或脚本执行环境恢复。 |

---

## 八、最终结论

```
browser provider code created, runtime partially verified via WebFetch
```

- **代码层**: browser_maps_provider 已接入 discovery pipeline，反检测代码已移除
- **数据层**: 通过 WebFetch + WebSearch 真实获取了 Nashville "board game store" 的 7 条 Google Maps 结果，包含商家名、地址、电话、官网
- **执行层**: Python/Playwright 无法运行（沙箱阻塞），集成测试代码就绪但未执行
- **阻断项**: WorkBuddy 沙箱阻止所有进程执行→无法运行 Playwright 浏览器自动化→无法验证页面滚动翻页→无法完成游标恢复测试→无法启动审核服务器

### 需要用户确认

是否接受 WebFetch 作为当前可用采集通道，并在沙箱限制下继续推进？或者等待沙箱执行权限恢复后进行完整 Playwright 浏览器验证？
