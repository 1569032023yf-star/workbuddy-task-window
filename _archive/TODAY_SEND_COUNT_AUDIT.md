# 今日发送审计 / Today's Send Count Audit

**日期 / Date**: 2026-07-01  
**审计时间 / Audit Time**: 09:39

---

## 今日发送记录 (2026-07-01)

| # | send_log ID | 商家 | 邮箱 | 状态 | 时间 | 来源 |
|---|-------------|------|------|------|------|------|
| 1 | 118 | Well Played Board Game Cafe | info@wellplayedasheville.com | ❌ FAILED | 00:37:37 | 10-email batch (06-30 18:05) |
| 2 | 119 | Kidstop Toys & Books | info@kidstoptoys.com | ✅ SENT | 00:38:41 | 10-email batch (06-30 18:05) |
| 3 | 120 | Phoenix Fire Games | info@phoenixfiregames.com | ✅ SENT | 00:39:41 | 10-email batch (06-30 18:05) |
| 4 | 121 | RIW Hobbies & Games | riwhobbies@gmail.com | ✅ SENT | 01:24:55 | 10-email batch (tail) |

**总计**: 4 条记录（3 SENT + 1 FAILED）

---

## 审计结论

| 问题 | 答案 |
|------|------|
| 今日是否真实发送了？ | ✅ 是，3 封成功，1 封失败 |
| 发送来源 | 2026-06-30 18:05 启动的 10-email timing test batch |
| 是否来自今天 09:00 正式任务？ | ❌ 否，来自昨天 18:05 的手动测试 |
| 是否走了 --stop-on-risk？ | ❌ 否，手动测试绕过了 daily_operator 的窗口检查 |
| 是否为 A0？ | ✅ 全部为 A0 (official_page_visible) |
| 是否有 guessed_email / B / C 风险？ | ❌ 否 |
| 为什么 daily_operator summary 显示"已发 2"？ | 因为 daily_operator 只扫描了 IMAP 收件箱中的 2 条新记录，不是 send_log 的完整统计 |

---

## 为什么 Summary 显示"已发 2"

daily_operator_auto.py 的 IMAP 扫描逻辑只检查收件箱中的新邮件（退信、回复等），而不是查询 send_log 数据库。它检测到 2 条 PostMaster 退信，推断"已发 2"，但实际 send_log 中有 4 条记录。

**根本原因**: daily_operator 的"已发 N"统计逻辑与 send_log 不一致。

---

*Generated at 2026-07-01 09:39*
