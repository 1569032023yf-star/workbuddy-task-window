# File Manifest / 文件清单

## Scope / 范围

中文：
本清单覆盖 BD 自动化关键文件、数据库、模板和报告，标注作用、风险等级、是否可修改、是否涉及发信、是否涉及 DB 写入、是否涉及敏感配置、是否建议备份。

English:
This manifest covers key BD automation files, database, templates, and reports, noting purpose, risk level, whether editable, whether it sends email, whether it writes DB, whether it touches sensitive config, and whether backup is recommended.

| File / 文件 | Purpose / 作用 | Risk / 风险 | Editable / 可修改 | Sends Email / 涉及发信 | DB Write / DB 写入 | Sensitive Config / 敏感配置 | Backup Recommended / 建议备份 |
|---|---|---|---|---|---|---|---|
| bd_sender.py | Builds and sends SMTP messages / 构造并发送 SMTP 邮件 | High / 高 | Yes, controlled / 可受控修改 | Yes / 是 | Yes via send status / 间接写入发送状态 | Reads SMTP config / 读取 SMTP 配置 | Yes / 是 |
| daily_session.py | Manual daily send session / 人工日常发信会话 | High / 高 | Yes, controlled / 可受控修改 | Yes / 是 | Yes / 是 | No direct secrets / 不直接含密钥 | Yes / 是 |
| daily_operator_auto.py | Orchestrated daily workflow / 日常编排流程 | High / 高 | Yes, controlled / 可受控修改 | Yes / 是 | Yes / 是 | No direct secrets / 不直接含密钥 | Yes / 是 |
| bd_db.py | Database access and migrations / 数据库访问与迁移 | High / 高 | Yes, controlled / 可受控修改 | No direct send / 不直接发信 | Yes / 是 | No direct secrets / 不直接含密钥 | Yes / 是 |
| agent_bounce_auditor.py | Bounce parsing and classification / 退信解析与分类 | Medium / 中 | Yes, controlled / 可受控修改 | No / 否 | Possible via caller / 由调用方写入 | Reads IMAP config / 读取 IMAP 配置 | Yes / 是 |
| fast_lead_discovery.py | Website email discovery / 官网邮箱发现 | Medium / 中 | Yes, controlled / 可受控修改 | No / 否 | Writes output JSON only / 输出 JSON | No / 否 | Optional / 可选 |
| templates / 模板目录 | Email template assets / 邮件模板资产 | Medium / 中 | Yes / 可修改 | Affects send content / 影响发信内容 | No / 否 | No / 否 | Yes / 是 |
| data/bd_leads.db | Production lead database / 生产线索数据库 | Critical / 极高 | Only via migration / 仅迁移修改 | No direct send / 不直接发信 | Yes / 是 | Contains customer data / 含客户数据 | Always / 必须 |
| .env | SMTP/IMAP and runtime secrets / SMTP/IMAP 与运行密钥 | Critical / 极高 | No unless explicitly authorized / 未授权不改 | Enables send / 支撑发信 | No / 否 | Yes / 是 | Do not print / 不输出 |
| reports / 报告 | Execution and audit records / 执行和审计记录 | Low-Medium / 低到中 | Yes / 可修改 | No / 否 | No / 否 | Must be sanitized / 必须脱敏 | Optional / 可选 |
