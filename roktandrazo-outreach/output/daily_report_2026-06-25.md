# BD Daily Report — 2026-06-25

> **DRY RUN** — no real emails were sent

---

## [发送摘要]

| 指标 | 数值 |
|------|------|
| 当天目标 | 20 |
| 实际发送 | 20 |
| 发送失败 | 0 |
| 退信 | 0 |
| 完成率 | 100% |

## [送达状态]

| 类型 | 数量 |
|------|------|
| 成功送达 | 20 |
| Hard Bounce | 2 |
| Policy Bounce | 0 |

  **Bounce触发批暂停**


## [回复摘要]

| 类型 | 数量 |
|------|------|
| 新回复 | 1 |
| 自动回复 | 0 (需IMAP扫描) |
| 退订 | 0 |

## [池剩余]

| 池 | 数量 | 说明 |
|---|------|------|
| A0 (可发) | 10 | 已验证邮箱，非Exchange |
| A1 (Exchange) | 0 | 已验证邮箱，Exchange MX，高风险 |
| approved_manual | 0 | 人工确认邮箱 |
| B (需人工确认) | 186 | 猜测邮箱，需在CSV中补充 |
| C (contact form) | 19 | 仅contact form |

## [暂停状态]

| 项 | 值 |
|----|----|
| send_pause | true |
| pause_reason | awaiting_next_operator_window_approval |

## [违规/异常]

  * Hard bounce (2) — 已自动加入 suppression

## [建议]

  * B 池有 186 条猜测邮箱待确认，运行 pool_analysis.py 生成审查 CSV
  * send_pause 仍为 true — 如需发送请先解除
  * 下一个 operator window: 明天 08:30-12:00

---
*Generated at 2026-06-25 14:42*
