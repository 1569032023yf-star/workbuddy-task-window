# ARCHITECTURE_MAP.md

> **Roktandrazo BD Automation — Full Architecture Map**
> Focus: 邮件构造链路 + Message-ID 缺失定位

---

## 1. System Layers

```
┌─────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                    │
│  daily_operator_auto.py (主入口, 09:00 触发)              │
│  ├─ Preflight → Lead Factory → Send Plan → Send → Report │
└──────────────────────┬──────────────────────────────────┘
                       │ 委托发送
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    SESSION LAYER                          │
│  daily_session.py (批次管理 + 扫描)                       │
│  ├─ batch_send() → 每批 5 封, 间隔 2-5 分钟              │
│  ├─ scan_bounce_and_reply() → IMAP 扫描                   │
│  └─ should_pause_after_scan() → 风控决策                  │
└──────────────────────┬──────────────────────────────────┘
                       │ 调用发送
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    SENDING LAYER                          │
│  bd_sender.py (SMTP 发信 + IMAP 存档)                     │
│  ├─ _build_email()  ← ⚠️ MESSAGE-ID MISSING HERE         │
│  ├─ _create_connection() → SMTP_SSL(465)                 │
│  ├─ sendmail() → [actual_to, sender_email] (BCC-to-self) │
│  └─ _save_to_sent() → IMAP "Sent Messages"               │
└──────────────────────┬──────────────────────────────────┘
                       │ 数据操作
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    DATA LAYER                             │
│  bd_db.py (SQLite CRUD + 池查询 + 安全检查)               │
│  ├─ get_sendable_leads() → A0 > AMS 优先级               │
│  ├─ update_lead_status() / log_send()                    │
│  ├─ add_to_suppression() / is_suppressed()               │
│  └─ check_bounce_history() / check_mx_provider()         │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Email Construction Chain (Critical Path)

```
bd_template.py                  bd_db.py
  │ get_email_for_lead()          │ get_sendable_leads()
  │ → subject, body_text,         │ → lead dict with email,
  │   body_html                   │   store_name, id, ...
  ▼                               ▼
         ┌──────────────────────────┐
         │  daily_session.py        │
         │  batch_send()            │
         │  对每个 lead:             │
         │  1. is_suppressed()      │
         │  2. check_sent_log()     │
         │  3. check_bounce_history │
         │  4. check_mx_provider()  │
         │  5. bd_sender.send_one() │
         └───────────┬──────────────┘
                     │
                     ▼
         ┌──────────────────────────┐
         │  bd_sender.py            │
         │  send_one(lead)          │
         │                          │
         │  _build_email():         │
         │    msg["From"]    = ✅   │
         │    msg["To"]      = ✅   │
         │    msg["Subject"] = ✅   │
         │    msg["Reply-To"]= ✅   │
         │    msg["Message-ID"] = ❌ MISSING ← 🔴 BUG
         │                          │
         │  _create_connection():   │
         │    SMTP_SSL(:465)        │
         │    ehlo + login          │
         │                          │
         │  server.sendmail():      │
         │    TO: [recipient, self] │ ← BCC-to-self
         │                          │
         │  _save_to_sent():        │
         │    IMAP append           │
         └──────────────────────────┘
```

---

## 3. File Dependency Graph

### Core Chain (邮件发送)
```
bd_template.py ──────────┐
                         │
env_loader.py ───────────┤
  └─ .env (SMTP creds)   │
                         │
bd_db.py ────────────────┤
  └─ data/bd_leads.db    │
                         ▼
              bd_sender.py ← 🔴 Message-ID fix location
                         ▲
                         │
              daily_session.py
                         ▲
                         │
              daily_operator_auto.py ← automation trigger
```

### Monitoring Chain (退信/回复)
```
agent_bounce_auditor.py  ← bounce classification
agent_reply_monitor.py   ← reply/unsub classification
  └─ env_loader.py → IMAP creds
  └─ bd_db.py → write bounce_log, suppression_list
```

### Lead Factory Chain (采集)
```
city_selector.py → search_engine.py → contact_extractor.py
  → website_verifier.py → browser_verifier.py
  → scorer_v2.py → collection_pipeline.py
  → bd_db.py (insert_lead)
```

---

## 4. Database Schema (Key Tables)

### leads (主表)
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| store_name | TEXT | |
| email | TEXT | |
| email_source_type | TEXT | official_page_visible / guessed_email / ... |
| email_verified_on_official_site | INTEGER | 0/1 |
| confidence_score | TEXT | A / B / C |
| status | TEXT | new / sent / bounced / approved_manual_send |
| mx_provider | TEXT | exchange / google / other |
| email_subject / email_body | TEXT | 模板渲染后的邮件内容 |
| email_body_html | TEXT | HTML 版本 (在部分行中) |
| domain_hash | TEXT | 去重用 |

### send_log
| Column | Type |
|--------|------|
| lead_id | INTEGER FK |
| email | TEXT |
| subject | TEXT |
| status | TEXT (sent / bounced / failed) |
| error_message | TEXT |
| sent_at | TIMESTAMP |

### bounce_log
| Column | Type |
|--------|------|
| lead_id | INTEGER FK |
| email | TEXT |
| bounce_type | TEXT (hard / policy / soft / domain / unknown) |
| status_code | TEXT |
| diag | TEXT |
| bounce_received_at | TEXT |

### suppression_list
| Column | Type |
|--------|------|
| email | TEXT UNIQUE |
| reason | TEXT (hard_bounce / unsub / bounced / ...) |
| added_at | TIMESTAMP |

### system_config
| Key | Description |
|-----|-------------|
| send_pause | true/false |
| pause_reason | 文本 |
| auto_send_enabled | true/false |
| daily_run_status | completed / underfilled / paused / failed |
| daily_run_target | 目标数 |
| daily_run_actual | 实际数 |
| daily_run_gap | 缺口 |

---

## 5. Two Sender Modules (Legacy vs Active)

| Module | Status | Notes |
|--------|--------|-------|
| `bd_sender.py` | **ACTIVE** | 当前生产使用，直接 SMTP |
| `sender.py` | LEGACY | 旧版，使用 `config.py` + `db.py`，也缺 Message-ID |

两个模块都缺少 Message-ID。但 `sender.py` 已不在活跃链路中。
本次修复只需改 `bd_sender.py`。

---

## 6. Template System

| File | Purpose |
|------|---------|
| `bd_template.py` | **V5 活跃模板** — "puzzle and family card game brand" |
| `drafter.py` | 旧版个性化草稿器，使用 `config.py` 常量 |
| `templates/` | 空目录 |

V5 模板通过 `bd_template.get_email_for_lead(lead)` 生成:
- `subject`: `"Premium puzzles & card games for {store_name} (Low MOQ / DDP)"`
- `body_text`: 4 bullet points + catalogue mention
- `body_html`: HTML 版本

邮件内容写入 leads 表的 `email_subject` / `email_body` 字段。
`bd_sender.send_one()` 从 lead dict 直接读取这些字段。

---

## 7. Bounce Classification (Current)

`agent_bounce_auditor.py:classify_bounce()` 分类逻辑:

| Type | Signals | Action |
|------|---------|--------|
| **hard** | 5.1.0, 5.1.1, "user unknown", "mailbox not found" | → suppression |
| **domain** | "domain not found", "dns error" | → suppression |
| **policy** | 5.4.1, 5.7.1, "access denied", "blocked" | → **当前可能误判** |
| **soft** | 4.x.x, "temporary failure", "mailbox full" | → retry |
| **unknown** | 无法识别 | → manual review |

**问题**: Message-ID 缺失导致的退信走 `policy` 分类，
但当前 `daily_session.py:scan_bounce_and_reply()` 对 `hard` 类型自动调用 `add_to_suppression()`。
如果 bounce 被错误分类为 `hard` 而非 `policy`（或 `policy` 也被自动 suppression），
就会导致有效客户被永久拉黑。

需要确认: 当前 `policy` 类型是否也会触发 suppression。
