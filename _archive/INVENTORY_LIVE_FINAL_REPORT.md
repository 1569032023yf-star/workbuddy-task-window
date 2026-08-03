# INVENTORY LIVE FINAL REPORT

**Date**: 2026-06-30 10:15  
**Mode**: Inventory Live (no real sending)

---

## 1. 是否发生真实发送

❌ **否** — 全程未发送任何邮件

## 2. B 池最终处理数量

| 指标 | 处理前 | 处理后 |
|------|--------|--------|
| B 池 guessed_email (status=new) | 169 | **0** |
| Browser Verification 处理 | — | 169 条全部完成 |

## 3. A0 最终数量

| 指标 | 值 |
|------|-----|
| A0 sendable | **13** |
| 其中 Browser Verification 升级 | 12 |
| 其中 Lead Factory 新增 | 4（Noble Knight Games, Haunted Game Cafe, Phoenix Fire Games, Kidstop Toys） |

## 4. sendable_pool 最终数量

**13**（A0=13, approved_manual_send=0）

## 5. 是否达到 20

❌ **否** — 差 7

## 6. 是否达到 60

❌ **否** — 差 47

## 7. 若未达到 20，还差多少

**差 7 条 A0**

## 8. 是否已自动启动新城市补池

✅ **部分完成** — 通过 WebSearch 手动采集了 4 个新城市的线索：
- Noble Knight Games (Fitchburg, WI)
- The Haunted Game Cafe (Fort Collins, CO)
- Phoenix Fire Games (Meridian, ID)
- Kidstop Toys & Books (Scottsdale, AZ)

**但手动采集效率低，建议使用自动化采集脚本继续补池。**

## 9. 模板 V4 dry-run preview 是否通过

✅ **通过** — 3 个样例均无未替换变量

样例：
1. Kidstop Toys & Books — Subject 正确渲染
2. Phoenix Fire Games — Subject 正确渲染
3. The Haunted Game Cafe — Subject 正确渲染

## 10. 明天是否建议进入 20 封 Send Live

⚠️ **不建议** — 当前 sendable_pool=13，未达 20 门槛

## 11. 明天 Send Live 建议命令

```bash
# 先运行 dry-run 确认
python daily_operator_auto.py --dry-run --target-count 20 --allow-topup --stop-on-risk

# 确认后 live 发送
python daily_operator_auto.py --live --target-count 20 --allow-topup --stop-on-risk
```

## 12. stop-on-risk 是否必须开启

✅ **必须** — 发送命令必须带 `--stop-on-risk`

---

## 数据库变更记录

### 新增线索（Lead Factory）
| ID | 门店 | 城市 | 邮箱 | 来源 |
|----|------|------|------|------|
| 330 | Noble Knight Games | Fitchburg, WI | bena@nobleknight.com | nobleknight.com |
| 331 | The Haunted Game Cafe | Fort Collins, CO | customer_service@hauntedgamecafe.com | hauntedgamecafe.com |
| 332 | Phoenix Fire Games | Meridian, ID | info@phoenixfiregames.com | phoenixfiregames.com |
| 333 | Kidstop Toys & Books | Scottsdale, AZ | info@kidstoptoys.com | kidstoptoys.com |

### Browser Verification 结果
| 类别 | 数量 |
|------|------|
| B→A0 升级 | 12 |
| B→C (contact_form_pool) | 29 |
| B→B2 (manual_review_needed) | 152 |
| B→Invalid | 0 |

### 模板更新
| 项目 | 旧 (V3) | 新 (V4) |
|------|---------|---------|
| Subject | Premium card games & puzzles for {store} (Low MOQ / DDP options) | Premium puzzles & card games for {store} (Low MOQ / DDP) |
| 已更新 leads | 17 | 17 |

---

## B2 Top 30 摘要

**B2 总数**: 152 条  
**Top 30 已导出**: `roktandrazo-outreach/output/B2_top30_review.csv`

Top 30 全部为核心品类（玩具/拼图/桌游店），值得人工审查是否有隐藏的官网邮箱。

---

## 后续建议

### 补池到 20 的方法
1. **自动化采集** — 使用 `collection_pipeline.py` 对优先城市（Asheville, Charleston, Savannah 等）执行批量采集
2. **B2 人工审查** — 从 152 条 B2 中人工挑选高价值门店，手动查找邮箱后升级 A0
3. **Browser Verifier 再跑一次** — 新采集的 B 池线索可能包含可升级的 A0

### 阻塞点
- sendable_pool=13，差 7 条到 20
- 手动采集效率低，需要自动化采集脚本

---

*Generated at 2026-06-30 10:15*
