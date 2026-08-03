# BD Daily Report — 2026-07-02

---

## [发送摘要]

| 指标 | 数值 |
|------|------|
| 当天目标 | 10 |
| 实际发送 | 0 |
| 缺口 | 10 |
| 状态 | paused |
| 发送失败 | 0 |
| 退信 | 0 |
| 完成率 | 0% |
| 根因 | sendable_inventory_insufficient |

## [送达状态]

| 类型 | 数量 |
|------|------|
| 成功送达 | 0 |
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
| A0 (可发) | 25 | 已验证邮箱，非Exchange |
| A1 (Exchange) | 0 | 已验证邮箱，Exchange MX，高风险 |
| approved_manual | 0 | 人工确认邮箱 |
| B (需人工确认) | 0 | 猜测邮箱，需在CSV中补充 |
| C (contact form) | 35 | 仅contact form |

## [明日可发准备度]

| 指标 | 数值 |
|------|------|
| 明日可发库存 | 25 |
| 明日目标 | 10 |
| 明日缺口 | 0 |
| next_window_needed_count | 0 |
| recovery_pending | false |

## [暂停状态]

| 项 | 值 |
|----|----|
| send_pause | true |
| pause_reason | Total bounce >= 2 (3) |

## [违规/异常]

  * 发送暂停: Total bounce >= 2 (3)
  * 未完成目标 (sent 0/10)

## [建议]

  * send_pause 仍为 true — 如需发送请先解除
  * 下一个 operator window: 明天 08:30-12:00

---
*Generated at 2026-07-02 12:03*
