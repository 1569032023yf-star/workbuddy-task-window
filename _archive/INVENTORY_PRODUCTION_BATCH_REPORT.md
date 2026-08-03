# INVENTORY PRODUCTION BATCH REPORT (FINAL)

**Date**: 2026-06-30 13:30  
**Mode**: Inventory Production (no real sending)

---

## 1. 是否真实发送邮件

❌ **否**

## 2. 是否修改生产数据库

✅ **是** — 仅新增线索记录，未修改发送状态

## 3. 本轮处理候选数

| 批次 | 候选数 | 耗时 | 平均耗时 |
|------|--------|------|----------|
| Batch 1 | 30 | 87s | 2.9s |
| Batch 2 | 20 | 68s | 3.4s |
| **合计** | **50** | **155s** | **3.1s** |

## 4. 新增 A0 数

| 批次 | A0 发现 | 有效新增 | 去重后 |
|------|---------|----------|--------|
| Batch 1 | 10 | 7 | 6 |
| Batch 2 | 3 | 2 | 2 |
| **合计** | **13** | **9** | **8** |

## 5. 当前 sendable_pool

**21** ✅ 已达到 20 门槛

## 6. 是否达到 20

✅ **是**

## 7. 是否达到 30

❌ **否** — 差 9

## 8. 是否达到 60

❌ **否** — 差 39

## 9. 新增 C/B2/Invalid 数

| 类别 | Batch 1 | Batch 2 | 合计 |
|------|---------|---------|------|
| C (contact_form) | 1 | 2 | 3 |
| B2 (manual_review) | 19 | 15 | 34 |
| Invalid | 0 | 0 | 0 |

## 10. 新增 A0 代表商家

| 门店 | 城市 | 邮箱 | 批次 |
|------|------|------|------|
| Well Played Board Game Cafe | Asheville, NC | info@wellplayedasheville.com | 1 |
| Game Kastle Greenville | Taylors, SC | greenville@gamekastle.com | 1 |
| Captains Comics and Toys | Charleston, SC | info@captainscomics.com | 1 |
| Red Balloon Toy Store | Salt Lake City, UT | customers@redballoontoystore.com | 1 |
| Vault of Midnight | Ann Arbor, MI | annarbor@vaultofmidnight.com | 1 |
| Mox Mania | Madison, WI | info@moxmania.com | 1 |
| Third Eye Games | Annapolis, MD | info@thirdeyecomics.com | 2 |
| Wildlings Toy Boutique | Phoenix, AZ | hello@wildlingstoys.com | 2 |

## 11. 新增 A0 的 evidence_url 是否完整

✅ 全部有 evidence_url

## 12. 是否可以进入 20 封 Send Live

✅ **是** — sendable_pool=21 >= 20

---

## Send Live Readiness

| 检查项 | 状态 |
|--------|------|
| sendable_pool >= 20 | ✅ 21 |
| 全部 A0/approved_manual_send | ✅ |
| 排除 guessed_email/B/C/suppression/bounced/delivery_issue | ✅ |
| stop-on-risk | ⚠️ 需命令带 --stop-on-risk |
| V4 模板 dry-run preview | ✅ 已通过 |
| 发送窗口 08:30–12:00 | ⚠️ 当前 13:30 已过窗口 |

### 明天 Send Live 建议命令

```bash
# 先 dry-run
python daily_operator_auto.py --dry-run --target-count 20 --allow-topup --stop-on-risk

# 确认后 live（在 08:30-12:00 窗口内执行）
python daily_operator_auto.py --live --target-count 20 --allow-topup --stop-on-risk
```

---

## 性能统计

| 指标 | 值 |
|------|-----|
| 总耗时 | 155s (2.6 min) |
| 平均每条 | 3.1s |
| A0 发现率 | 26% (13/50) |
| 有效 A0 率 | 16% (8/50) |
| 速度 vs Browser Verifier | **19x** (3.1s vs 60s) |

---

*Generated at 2026-06-30 13:30*
