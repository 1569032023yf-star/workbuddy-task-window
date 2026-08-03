# CURRENT_STATUS.md

> **Codex Handoff — Roktandrazo BD Automation**
> Generated: 2026-07-07T11:29+08:00 | Handoff type: Message-ID header fix

---

## 1. Project Snapshot

| Metric | Value |
|--------|-------|
| Production dir | `roktandrazo-outreach/` |
| DB | `data/bd_leads.db` (SQLite, ~537 KB) |
| Total leads | ~190+ |
| Total send_log | 182 |
| Suppression list | 24 |
| SMTP | ianyf@roktandrazo.com (Tencent Enterprise, smtp.exmail.qq.com:465 SSL) |
| Sender name | Ian |
| Active template | V5 (`bd_template.py`) |
| Daily target | 20 emails |
| Send window | 09:00–13:00 Asia/Shanghai |
| Automation | "Roktandrazo BD Daily Orchestrator - 09:00 China Time" (ACTIVE) |

---

## 2. Highest Priority Issue: Message-ID Header Missing → Bounce

### Problem

`bd_sender.py:_build_email()` 构造邮件时 **没有设置 `Message-ID` header**。

```python
# bd_sender.py 第 31-44 行
def _build_email(to_email, subject, body_text, body_html=None):
    msg = MIMEMultipart("alternative")
    msg["From"] = ...
    msg["To"] = ...
    msg["Subject"] = ...
    msg["Reply-To"] = ...
    # ← 没有 msg["Message-ID"] = ...
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    ...
    return msg
```

Python `MIMEMultipart` **不会自动生成 Message-ID**。
当邮件被 SMTP 服务器发出后，接收方邮件服务器（尤其是 Microsoft 365 / Outlook）会因为 **缺少合规的 Message-ID header** 而拒绝投递，产生退信。

### Observed Bounce Pattern

退信诊断码中出现以下信号时，即为 Message-ID 缺失导致的 policy bounce：

```
550 5.4.1 ... Access denied ...
550 ... Message-ID header is missing or malformed ...
```

### Critical Rule

> **⚠️ Missing Message-ID 退信 ≠ hard bounce。**
> **不得加入 suppression_list，不得标为 hard bounce。**

原因：
- 这是发件端的技术缺陷，不是收件地址无效
- 修复 Message-ID 后，同一批收件地址可以正常投递
- 如果错误地加入 suppression，会永久丢失有效客户

### Fix Scope (Codex 实施)

修复位置：`bd_sender.py` → `_build_email()` 函数

```python
# 需要添加：
from email.utils import make_msgid

def _build_email(...):
    ...
    msg["Message-ID"] = make_msgid(domain="roktandrazo.com")
    ...
```

同时需要修改 `agent_bounce_auditor.py` 的 `classify_bounce()` 函数，
在 `policy` 分类中识别 "Message-ID" 相关退信，标记为 `message_id_missing` 子类型，
**不触发 suppression**。

---

## 3. System Architecture (Quick Reference)

```
daily_operator_auto.py          ← 09:00 Asia/Shanghai 触发
  │
  ├─ step_preflight()           ← 检查 SMTP/SPF/DKIM/pool
  ├─ step_lead_factory()        ← B pool 导入 + Browser Verifier
  ├─ step_build_send_plan()     ← 从 bd_db.get_sendable_leads() 取 A0 + AMS
  ├─ step_send_batches()        ← 委托给 daily_session.py
  │     └─ daily_session.py
  │          └─ batch_send()    ← 每批 5 封，间隔 2-5 分钟
  │               └─ bd_sender.send_one(lead)
  │                    └─ _build_email()   ← ⚠️ 这里缺少 Message-ID
  │                    └─ SMTP_SSL.sendmail()
  │                    └─ _save_to_sent()  ← IMAP 保存已发送
  ├─ step_monitor_and_risk()    ← IMAP 扫描 bounce/reply/unsub
  └─ step_daily_report()        ← 生成日报告
```

---

## 4. Pool Status (2026-07-06 end of day)

| Pool | Description | Approx Count |
|------|-------------|-------------|
| A0 | 官网验证邮箱，非 Exchange | ~0 (需补池) |
| approved_manual_send | 人工确认邮箱 | 波动 |
| B | 猜测邮箱 (info@domain.com) | ~150+ |
| C | 仅 contact form | ~29 |

A0 池经常耗尽，需要 Lead Factory 持续补池。

---

## 5. What NOT To Do

1. **不要修改 `.env` 文件** — 含 SMTP/IMAP 密码
2. **不要复制真实数据库** — `data/bd_leads.db` 含真实客户数据
3. **不要发真实邮件** — 本次只做代码修复
4. **不要修改 suppression_list** — 尤其不要把 Message-ID 退信加入
5. **不要批量更新 confidence_score** — 必须逐条浏览器验证
6. **不要创建定时任务** — 本次不注册 automation
