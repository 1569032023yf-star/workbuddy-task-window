# BD Daily Report — 2026-07-20

---

## [发送摘要]

| 指标 | 数值 |
|------|------|
| 当天目标 | 20 |
| 实际发送 | 19 |
| 缺口 | 1 |
| 状态 | paused |
| 发送失败 | 0 |
| 退信 | 0 |
| 完成率 | 95% |
| 根因 | sendable_inventory_insufficient |

## [送达状态]

| 类型 | 数量 |
|------|------|
| 成功送达 | 19 |
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
| A0 (可发) | 7 | 已验证邮箱，非Exchange |
| A1 (Exchange) | 0 | 已验证邮箱，Exchange MX，高风险 |
| approved_manual | 0 | 人工确认邮箱 |
| B (需人工确认) | 4 | 猜测邮箱，需在CSV中补充 |
| C (contact form) | 55 | 仅contact form |

## [明日可发准备度]

| 指标 | 数值 |
|------|------|
| 明日可发库存 | 7 |
| 明日目标 | 20 |
| 明日缺口 | 13 |
| next_window_needed_count | 0 |
| recovery_pending | false |

## [暂停状态]

| 项 | 值 |
|----|----|
| send_pause | true |
| pause_reason | Total bounce >= 2 (6) |

## [违规/异常]

  * 发送暂停: Total bounce >= 2 (6)
  * 未完成目标 (sent 19/20)

## [建议]

  * A0+approved_manual 仅剩 7 条，建议先运行 Browser Verification 清洗 B 池
  * B 池有 4 条待浏览器验证，不建议直接交给人工全量确认
  * send_pause 仍为 true — 如需发送请先解除
  * 下一个 operator window: 明天 08:30-12:00

---
*Generated at 2026-07-20 09:14*
