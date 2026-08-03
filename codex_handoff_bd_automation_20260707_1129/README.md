# Codex Handoff Package — Roktandrazo BD Automation

> **Purpose**: Message-ID header fix handoff
> **Generated**: 2026-07-07T11:29+08:00
> **Scope**: Code fix only — no live sends, no DB changes, no credential exposure

---

## Package Contents

| Document | Purpose |
|----------|---------|
| [CURRENT_STATUS.md](CURRENT_STATUS.md) | 项目现状、最高优先级问题 (Message-ID) |
| [ARCHITECTURE_MAP.md](ARCHITECTURE_MAP.md) | 系统架构图、邮件构造链路、数据库 schema |
| [RUNBOOK.md](RUNBOOK.md) | 分步修复指南 (3 个文件、~10 行代码) |
| [GUARDRAILS.md](GUARDRAILS.md) | 绝对禁止事项、安全操作白名单 |
| [FILE_MANIFEST.md](FILE_MANIFEST.md) | 生产目录完整文件清单 |
| [SENSITIVE_EXCLUSION_AUDIT.md](SENSITIVE_EXCLUSION_AUDIT.md) | 敏感信息排除审计 |

---

## Quick Start (Codex)

1. Read `CURRENT_STATUS.md` — understand the Message-ID issue
2. Read `ARCHITECTURE_MAP.md` — understand the email construction chain
3. Follow `RUNBOOK.md` — fix 3 files (~10 lines total)
4. Respect `GUARDRAILS.md` — no live sends, no DB changes
5. Verify with dry-run: `python daily_session.py --dry-run`

---

## The Bug (One Sentence)

`bd_sender.py:_build_email()` does not set `Message-ID` header → recipient servers (especially Microsoft 365) reject the message → bounce is classified as `hard` or `policy` → valid customer emails get permanently suppressed.

## The Fix (One Sentence)

Add `msg["Message-ID"] = make_msgid(domain="roktandrazo.com")` in `_build_email()`, and add `message_id_missing` bounce subtype that explicitly does NOT trigger suppression.

---

## Lab Directory

`roktandrazo-outreach_codex_lab_20260707/` — empty, ready for Codex test scripts and mock data.

---

## Excluded (Not Present)

- `.env` (SMTP/IMAP passwords)
- `data/bd_leads.db` (real customer data)
- Any cookies/profiles
- Any real email addresses from the database
