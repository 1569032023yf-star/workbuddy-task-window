# BD Daily Report — 2026-07-23

---

## [发送摘要]

| 指标 | 数值 |
|------|------|
| 当天目标 | 20 |
| 实际发送 | 1 |
| 缺口 | 19 |
| 状态 | underfilled |
| 发送失败 | 0 |
| 退信 | 0 |
| 完成率 | 5% |
| 根因 | no_sendable_leads |

## [送达状态]

| 类型 | 数量 |
|------|------|
| 成功送达 | 1 |
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
| A0 (可发) | 6 | 已验证邮箱，非Exchange |
| A1 (Exchange) | 0 | 已验证邮箱，Exchange MX，高风险 |
| approved_manual | 1 | 人工确认邮箱 |
| B (需人工确认) | 0 | 猜测邮箱，需在CSV中补充 |
| C (contact form) | 55 | 仅contact form |

## [明日可发准备度]

| 指标 | 数值 |
|------|------|
| 明日可发库存 | 7 |
| 明日目标 | 20 |
| 明日缺口 | 13 |
| next_window_needed_count | 19 |
| recovery_pending | true |

## [暂停状态]

| 项 | 值 |
|----|----|
| send_pause | false |
| pause_reason | - |

## [违规/异常]

  * 未完成目标 (sent 1/20)

## [建议]

  * A0+approved_manual 仅剩 7 条，建议先运行 Browser Verification 清洗 B 池
  * 今日状态 underfilled，缺口 19 封，需进入 recovery 或 next window
  * 下一个 operator window: 明天 08:30-12:00

---
*Generated at 2026-07-23 09:00*
