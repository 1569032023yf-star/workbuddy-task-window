# B2 审查总结 / B2 Review Summary

**日期 / Date**: 2026-06-30

---

## 概览 / Overview

| 指标 / Metric | 值 / Value |
|---------------|-----------|
| B2 总数 / Total B2 | 152 |
| Top 30 已筛选 / Top 30 selected | 30 |
| 筛选逻辑 / Selection logic | 小城市优先 + 门店类型 + 产品匹配 |
| Top 30 中高优先级 / High priority | 10 |
| Top 30 中中优先级 / Medium priority | 10 |
| Top 30 中低优先级 / Low priority | 10 |

---

## 筛选逻辑 / Selection Logic

按以下维度打分排序：

| 维度 / Dimension | 权重 / Weight | 说明 / Description |
|-----------------|--------------|-------------------|
| 城市大小 / City size | 8 | 小城市 +8，中等城市 +4，大城市 +1 |
| 门店类型 / Store type | 5-6 | 桌游店 +6，拼图/玩具店 +5，书店/博物馆 +4 |
| 产品匹配 / Product fit | 2 | 名称含 game/puzzle/toy +2 |
| 已有 A0 降权 / A0 penalty | -2 | 同城市已有 A0 线索 -2 |

---

## Top 30 分布 / Distribution

### 城市分布 / By City

| 城市类型 | 数量 |
|---------|------|
| 小城市（< 10 万人口） | 25 |
| 中等城市 | 3 |
| 大城市 | 2 |

### 门店类型分布 / By Store Type

| 类型 | 数量 |
|------|------|
| 桌游店 / Board game store | 17 |
| 独立玩具店 / Independent toy store | 7 |
| 拼图店 / Puzzle store | 2 |
| 漫画/游戏店 / Comic & game store | 4 |

### 产品适配分布 / By Product Fit

| 适配 | 数量 |
|------|------|
| 卡游 | 21 |
| 两者都适合 | 7 |
| 拼图 | 2 |

---

## 未自动升级 A0 的原因 / Why Not Auto-Upgraded

| 原因 | 数量 | 说明 |
|------|------|------|
| HTTP 快筛未找到邮箱 | 25 | 网站可能需要 JS 渲染或邮箱在子页面 |
| 官网无可见邮箱 | 5 | 邮箱可能通过表单或后台系统处理 |

---

## 建议动作分布 / Recommended Actions

| 动作 | 数量 | 说明 |
|------|------|------|
| 人工找邮箱 | 25 | 去官网 contact/about/wholesale 页面手动查找 |
| 走 contact form | 5 | 通过官网联系表单提交 |

---

## 中文总结

B2 池共 152 条线索，经过小城市优先 + 门店类型 + 产品匹配的多维度筛选，选出 Top 30 值得人工审查的门店。

关键发现：
- Top 30 中 83% 是小城市门店（符合"农村包围城市"策略）
- 57% 是桌游店（核心目标客户）
- 84% 需要人工找邮箱（HTTP 快筛未能自动提取）
- 16% 可通过 contact form 提交

建议 Neil 审查 Top 10 高优先级门店，手动查找邮箱后升级为 A0。

## English Summary

The B2 pool contains 152 leads. After multi-dimensional scoring (small city priority + store type + product fit), we selected Top 30 stores worth manual review.

Key findings:
- 83% are small city stores (aligns with "rural surrounds city" strategy)
- 57% are board game stores (core target customers)
- 84% need manual email lookup (HTTP fast scan couldn't extract)
- 16% can be submitted via contact form

Recommend Neil review Top 10 high-priority stores and manually find emails to upgrade to A0.

---

*Generated at 2026-06-30 15:00*
