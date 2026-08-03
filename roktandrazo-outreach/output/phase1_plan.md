# Roktandrazo 美国线下 BD 线索收集系统 — 第一阶段规划

## 业务背景
- 品牌：roktandrazo
- 联系人：Ian
- 主营：家庭桌游、卡牌游戏、教育卡游、拼图
- 定位：不只是单次批发，而是**长期合作**（批发 + 定制设计/生产/供应链）

## 合作模式
1. **批发现有卡游** — Capybara Squad, Math Dinos, Recipe Rush, What&Why? 等
2. **批发现有拼图** — 24 National Parks, Butterfly Symphony 等
3. **定制设计/生产** — 如果门店有自己的卡牌/拼图想法，可提供设计→开发→生产→包装→供应链全链路支持
4. **长期拓展** — 玩具店、桌游店、书店、礼品店、博物馆、教育门店

## 系统架构

### 数据模型 (SQLite)
```
leads 表:
- store_name, store_type, city, state
- official_website, contact_page, wholesale_or_vendor_page
- email, email_type (general/owner/buyer/wholesale/vendor/support/unknown)
- contact_form_url, evidence_url, source_keyword
- fit_reason, product_fit (card_games/puzzles/both/custom_production)
- confidence_score (A/B/C)
- status (new/reviewed/drafted/sent/replied/bounced/unsubscribed/do_not_contact)
- notes, collected_at, last_checked_at
```

### 工作流
```
选择城市 → 搜索门店 → 回到官网确认 → 提取联系方式 → 评分 → 入库 → 人工审核
```

### 评分规则
| 等级 | 条件 |
|------|------|
| A | 官网存在 + 类型高度匹配 + 有公开商务邮箱或 wholesale/vendor/contact 表单 + 有实体地址 + 适合卡游/拼图/定制 |
| B | 官网存在 + 类型匹配 + 只有 contact form 或 general email + 需人工审核 |
| C | 信息不完整 / 只有社媒 / 第三方平台 / 不进入发信池 |

### 排除条件
- 纯线上店铺
- 大型连锁总部邮箱不明确
- 与儿童/家庭/游戏/礼品/拼图/教育完全无关
- 无官网/contact page/公开联系方式
- 已发过/退订/退信/明确拒绝

### 试点计划：3 个城市
| 城市 | 州 | 选择理由 |
|------|-----|---------|
| Portland | OR | 独立零售文化强，gift shops 多，桌游文化活跃 |
| Asheville | NC | 旅游城市，独立小店密集，手工/艺术氛围 |
| Santa Fe | NM | 博物馆/画廊密集，旅游+艺术，gift shop 需求强 |

### 每个城市搜索策略
1. WebSearch: "independent toy store {city}" / "board game store {city}" / "gift shop {city} puzzles"
2. 对每个结果：访问官网 → 确认实体地址 → 找 contact/wholesale/vendor 页面 → 提取邮箱
3. 如果官网无法访问或无联系方式 → 排除
4. 证据链接 = 官网实际展示邮箱/contact form 的页面 URL

### 输出
- CSV/表格：所有线索 + 评分 + 产品适配建议
- 分析报告：A 级清单 / 卡游主推 / 拼图主推 / 定制合作候选 / 需人工确认

### 扩展到每周 20 城市
- 建立城市候选池（按州分布、旅游热度、独立零售密度排序）
- 每周轮换 20 个城市
- 每个城市目标 10-20 家门店
- 每周新增 200-400 条线索
- AI 自动评分 + 人工审核后进入发信池
