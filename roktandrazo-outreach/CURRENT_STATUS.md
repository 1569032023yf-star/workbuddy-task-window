# Current Status / 当前状态

## Project / 项目

中文：
当前项目是 Roktandrazo / rokt&razo US retail BD automation，用于受控推进美国零售 BD 邮件触达、退信监控、候选池补充和报告生成。

English:
The current project is Roktandrazo / rokt&razo US retail BD automation, used for controlled US retail BD email outreach, bounce monitoring, candidate pool rebuilding, and report generation.

## Highest Priority / 当前最高优先级

中文：
当前最高优先级是继续恢复合规 sendable_pool，并在所有 gate 通过后完成受控 daily send。不得为了追数量绕过 evidence_url + evidence_snippet、suppression、bounce、duplicate domain 或发送窗口 gate。

English:
The highest priority is to continue restoring a compliant sendable_pool and complete a controlled daily send only after all gates pass. Quantity targets must not bypass evidence_url + evidence_snippet, suppression, bounce, duplicate-domain, or send-window gates.

## Message-ID Status / Message-ID 状态

中文：
Message-ID header fix 已完成，并已通过生产语法检查、header-only dry-run、唯一性验证和自有邮箱测试。

English:
The Message-ID header fix is complete and has passed production syntax check, header-only dry-run, uniqueness verification, and owner-controlled inbox testing.

## Today Send Status / 今日发信状态

中文：
今日 controlled live send 仍未由本轮任务执行。本轮之前数据库今日已有 sent 记录 2 条，但不是当前 Codex 任务新增。send_pause 当前为 false，但这不代表可以自动群发。

English:
Today's controlled live send still has not been performed by this run. Before this run, the database already had 2 sent records today, but they were not added by the current Codex task. send_pause is currently false, but that does not mean automated bulk sending may proceed.

## Inventory Status / 库存状态

中文：
evidence_snippet schema 已新增。原 13 条 evidence_url 候选已审计：4 条回填并保留 A0，9 条降为 B2。随后 TN/AR/KY B2 官网验证净新增 4 条 A0。当前严格 sendable_pool 为 5，仍低于 daily target 20 和 inventory target 60。

English:
The evidence_snippet schema has been added. The original 13 evidence_url candidates were audited: 4 were backfilled and kept as A0, and 9 were downgraded to B2. A later TN/AR/KY B2 official-site verification added a net 4 A0 records. Current strict sendable_pool is 5, still below daily target 20 and inventory target 60.

## Primary States / 主攻州

中文：
主攻州仅限 Tennessee / TN / 田纳西州、Arkansas / AR / 阿肯色州、Kentucky / KY / 肯塔基州。不得随机跨州或全美泛扫。

English:
Primary states are limited to Tennessee / TN, Arkansas / AR, and Kentucky / KY. Random cross-state processing or nationwide broad scanning is not allowed.

## Windows / 时间窗口

中文：
客户发信窗口是 Asia/Shanghai 09:00-13:00。库存补池窗口是 Asia/Shanghai 13:30-17:30。窗口外不得执行客户 live send。

English:
The customer send window is Asia/Shanghai 09:00-13:00. The inventory rebuild window is Asia/Shanghai 13:30-17:30. Customer live send is not allowed outside the send window.

## Pool Definitions / 池口径

中文：
A0 是可发送候选，必须有官方来源邮箱、evidence_url 和 evidence_snippet。B2/manual_review_needed 只用于人工审核，不自动发送。C/contact_form_pool 只用于表单池，不发邮件。suppression、hard bounce、delivery_issue、unsubscribe、reply pool 均不得进入发送池。

English:
A0 is the sendable candidate class and must have an official-source email, evidence_url, and evidence_snippet. B2/manual_review_needed is for manual review only and must not be auto-sent. C/contact_form_pool is for contact-form handling and must not be emailed. suppression, hard bounce, delivery_issue, unsubscribe, and reply pools must not enter the send pool.
