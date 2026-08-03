# BD Daily Report — 2026-07-06

> **DRY RUN** — no real emails were sent

---

## [发送摘要]

| 指标 | 数值 |
|------|------|
| 当天目标 | 20 |
| 实际发送 | 3 |
| 缺口 | 17 |
| 状态 | underfilled |
| 发送失败 | 0 |
| 退信 | 0 |
| 完成率 | 15% |
| 根因 | sendable_inventory_insufficient |

## [送达状态]

| 类型 | 数量 |
|------|------|
| 成功送达 | 3 |
| Hard Bounce | 0 |
| Policy Bounce | 0 |

## [回复摘要]

| 类型 | 数量 |
|------|------|
| 新回复 | 0 |
| 自动回复 | 0 (需IMAP扫描) |
| 退订 | 0 |

## [池剩余]

| 池 | 数量 | 说明 |
|---|------|------|
| A0 (可发) | 15 | 已验证邮箱，非Exchange |
| A1 (Exchange) | 0 | 已验证邮箱，Exchange MX，高风险 |
| approved_manual | 0 | 人工确认邮箱 |
| B (需人工确认) | 0 | 猜测邮箱，需在CSV中补充 |
| C (contact form) | 39 | 仅contact form |

## [明日可发准备度]

| 指标 | 数值 |
|------|------|
| 明日可发库存 | 15 |
| 明日目标 | 20 |
| 明日缺口 | 5 |
| next_window_needed_count | 17 |
| recovery_pending | true |

## [暂停状态]

| 项 | 值 |
|----|----|
| send_pause | true |
| pause_reason | Manual stop by operator at 10:04 CST |

## [违规/异常]

  * 未完成目标 (sent 3/20)

## [建议]

  * A0+approved_manual 仅剩 15 条，建议先运行 Browser Verification 清洗 B 池
  * send_pause 仍为 true — 如需发送请先解除
  * 今日状态 underfilled，缺口 17 封，需进入 recovery 或 next window
  * 下一个 operator window: 明天 08:30-12:00

---
*Generated at 2026-07-06 10:31*
