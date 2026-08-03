# B2 Agent Pass 2 报告

**日期 / Date**: 2026-06-30  
**处理方式 / Method**: fast_lead_discovery.py (HTTP-first + Playwright fallback)  
**输入 / Input**: B2 Top 30 (小城市优先排序)  
**总耗时 / Total Time**: 526s (8.8 min)  
**平均每条 / Avg Per Lead**: 17.5s

---

## 处理结果 / Results

| 分类 | 数量 | 说明 |
|------|------|------|
| A0 升级 | 1 | Toyopolis Santa Fe (但邮箱域名不匹配，需人工确认) |
| B2 仍需人工 | 29 | HTTP + 浏览器均未找到邮箱 |
| C contact_form | 0 | — |
| Invalid | 0 | — |

---

## A0 发现 / A0 Found

| 商家 | 城市 | 邮箱 | 问题 |
|------|------|------|------|
| Toyopolis Santa Fe | Santa Fe, NM | contact@sansoxygen.com | ⚠️ 邮箱域名 sansoxygen.com ≠ 商城域名 toyopolissantafe.com，疑似误抓 |

**结论**: 该 A0 为疑似误抓，不自动升级。需人工确认。

---

## B2 仍需人工审查 (29 条)

这 29 条 B2 线索经过 HTTP 快筛 + Playwright 浏览器验证，均未找到官网可见邮箱。

可能原因：
1. 邮箱通过 JavaScript 动态加载，HTTP 无法提取
2. 邮箱在需要登录才能看到的页面
3. 官网确实不公开展示邮箱
4. 官网只有联系表单

---

## 为什么大多数 B2 无法自动升级

| 原因 | 说明 |
|------|------|
| JS 渲染 | 部分网站使用 React/Vue/Shopify，邮箱在 JS 中动态加载 |
| 反爬保护 | Cloudflare/WAF 保护阻止了自动抓取 |
| 无邮箱 | 官网确实不公开展示邮箱，只提供表单 |
| 邮箱在子页面 | 邮箱可能在 /wholesale、/vendor 等深层页面 |

---

## 建议

1. 对 Top 10 高价值门店，建议人工打开官网查找邮箱
2. 重点关注 /wholesale、/vendor、/partner 页面
3. 如果找不到邮箱，可以通过 contact form 提交合作意向
4. 对于 Provo, UT 的两家门店（Dragon's Keep, Heavy Dice），可以考虑社媒联系

---

*Generated at 2026-06-30 17:30*
