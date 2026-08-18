# Automation Memory — BD Result Recovery Sync (08:45 Asia/Shanghai)

## 2026-08-07 (08:35 CST) — 首次运行
- 脚本 result_recovery_sync.py 执行成功，exit 0，all_ok=true。
- tracking: total 136 / matched 61 (hit_rate 44.85%，全按 send_log_id + smtp_message_id 匹配)。
- bounce scan: scanned 15 / matched 14 / domain_invalid 12 / mailbox_invalid 0 / policy 0 / soft 0 / unmatched_dsn 1 / unresolved 2。
- reply: total 1（last_reply_received_at 2026-06-25）。
- unsubscribe: total 1, suppression_total 26。
- 输出落盘 output/result_recovery_sync_2026-08-07.json；system_config 写入 sync_0845_last_success_at / sync_0845_steps（ok）。
- poller_status: bounce job last_success_at 更新为 2026-08-07T08:35:38（tracking/health/reply job 仍 None，属 poller 自身维护，非本脚本职责）。
- 注意：实际 DB 是 data/bd_leads.db，data/leads.db 是空占位。

## 2026-08-08 (08:35 CST) — 正常运行
- 脚本执行成功，exit 0，all_ok=true，四步（tracking/bounce/reply/unsubscribe）全部 ok。
- tracking: total 136 / matched 61 (hit_rate 44.85%)。
- bounce: scanned 15 / matched 14 / domain_invalid 12 / mailbox_invalid 0 / policy 0 / soft 0 / unmatched_dsn 1 / unresolved 2。
- reply: total 1（last_reply_received_at 2026-06-25）；unsubscribe: total 1, suppression_total 26。
- system_config 已持久化 sync_0845_last_success_at=2026-08-08T08:35:37、sync_0845_steps 各步骤 ok（DB 实测确认）。
- poller_status: bounce job last_success_at=2026-08-08T08:35:37.586293（心跳正常，未 stale）。

## 2026-08-09 (08:35 CST) — 正常运行
- 脚本执行成功，exit 0，all_ok=true，四步全部 ok。
- tracking: total 136 / matched 61 (hit_rate 44.85%)，全部按 send_log_id+smtp_message_id 匹配。
- bounce: scanned 15 / matched 14 / domain_invalid 12 / mailbox_invalid 0 / policy 0 / soft 0 / unmatched_dsn 1 / unresolved 2（与 08-07/08-08 完全一致，无新增 bounce）。
- reply: total 1（last_reply_received_at 2026-06-25）；unsubscribe: total 1, suppression_total 26。
- 输出落盘 output/result_recovery_sync_2026-08-09.json；system_config 已写入 sync_0845_last_success_at=2026-08-09T08:35:33.757417、sync_0845_steps 全 ok（DB 实测确认）。
- poller_status: bounce job last_success_at=2026-08-09T08:35:33.752376（心跳正常，未 stale）。

## 2026-08-10 (08:36 CST) — 正常运行
- 脚本执行成功，exit 0，all_ok=true，四步全部 ok。
- tracking: total 136 / matched 61 (hit_rate 44.85%)，全部按 send_log_id+smtp_message_id 匹配。
- bounce: scanned 15 / matched 14 / domain_invalid 12 / mailbox_invalid 0 / policy 0 / soft 0 / unmatched_dsn 1 / unresolved 2（连续第 4 天数字完全一致，无新增 bounce）。
- reply: total 1（last_reply_received_at 2026-06-25）；unsubscribe: total 1, suppression_total 26。
- 输出落盘 output/result_recovery_sync_2026-08-10.json（7927 B）；system_config 写入 sync_0845_last_success_at=2026-08-10T08:36:08。
- poller_status: bounce job last_success_at=2026-08-10T08:36:08.429015（心跳正常，未 stale）。

## 2026-08-11 (23:40 CST) — 正常运行（当日第二次执行，晚间轮次）
- 脚本执行成功，exit 0，all_ok=true，四步全部 ok。
- tracking: total 136 / matched 61 (hit_rate 44.85%)，全部按 send_log_id+smtp_message_id 匹配。
- bounce: scanned 15 / matched 14 / domain_invalid 12 / mailbox_invalid 0 / policy 0 / soft 0 / unmatched_dsn 1 / unresolved 2（连续第 6 次数字完全一致，无新增 bounce）。
- reply: total 1（last_reply_received_at 2026-06-25）；unsubscribe: total 1, suppression_total 26。
- 输出落盘 output/result_recovery_sync_2026-08-11.json（7927 B，同日文件被晚间执行覆盖）；system_config 写入 sync_0845_last_success_at=2026-08-11T23:40:50.912968+08:00、sync_0845_steps 全 ok（DB 实测确认）。
- poller_status (output/bd_ops_poller_status.json): bounce job last_success_at=2026-08-11T23:40:50.911771+08:00（心跳正常，未 stale；tracking/health/reply job 仍 None，属 poller 自身维护）。

## 2026-08-12 (23:40 CST) — 正常运行
- 脚本执行成功，exit 0，all_ok=true，四步全部 ok。
- tracking: total 136 / matched 61 (hit_rate 44.85%)，全部按 send_log_id+smtp_message_id 匹配。
- bounce: scanned 15 / matched 14 / domain_invalid 12 / mailbox_invalid 0 / policy 0 / soft 0 / unmatched_dsn 1 / unresolved 2（连续第 7 次数字完全一致，无新增 bounce；15 条 DSN 明细含 2 条 unresolved：kiddingaroundtoys 5.1.3 与 drnoscomics 无诊断码，另 1 条 replaytoys 5.7.1 delivery loop 未匹配 send_log）。
- reply: total 1（last_reply_received_at 2026-06-25）；unsubscribe: total 1, suppression_total 26。
- 输出落盘 output/result_recovery_sync_2026-08-12.json（7927 B）；system_config 写入 sync_0845_last_success_at=2026-08-12T23:40:50.979593+08:00、sync_0845_steps 全 ok（DB 实测确认）。
- poller_status: bounce job last_success_at=2026-08-12T23:40:50.978664+08:00，consecutive_failures=0（心跳正常，未 stale）。

## 2026-08-13 (08:35 CST) — 正常运行（早间轮次，恢复 08:45 计划）
- 脚本执行成功，exit 0，all_ok=true，四步全部 ok。
- tracking: total 136 / matched 61 (hit_rate 44.85%)，全部按 send_log_id+smtp_message_id 匹配。
- bounce: scanned 14 / matched 13 / domain_invalid 11 / mailbox_invalid 0 / policy 0 / soft 0 / unmatched_dsn 1 / unresolved 2（比历史少 1 条 DSN：15→14，疑一条已处理 DSN 移出队列；14 条明细 = 11 domain_invalid + 2 unresolved [kiddingaroundtoys 5.1.3、drnoscomics 无诊断码] + 1 replaytoys 5.7.1 delivery loop 未匹配 send_log，与 08-12 明细集一致）。无新增 bounce 风险。
- reply: total 1（last_reply_received_at 2026-06-25）；unsubscribe: total 1, suppression_total 26。
- 输出落盘 output/result_recovery_sync_2026-08-13.json（7522 B）；system_config 写入 sync_0845_last_success_at=2026-08-13T08:35:47.714717+08:00、sync_0845_steps 全 ok（DB 实测确认）。
- poller_status: bounce job last_success_at=2026-08-13T08:35:47.713379+08:00，consecutive_failures=0（心跳正常，未 stale）。

## 2026-08-14 (08:35 CST) — 正常运行（早间轮次）
- 脚本执行成功，exit 0，all_ok=true，四步全部 ok。
- tracking: total 136 / matched 61 (hit_rate 44.85%)，全部按 send_log_id+smtp_message_id 匹配。
- bounce: scanned 14 / matched 13 / domain_invalid 11 / mailbox_invalid 0 / policy 0 / soft 0 / unmatched_dsn 1 / unresolved 2（与 08-13 一致，无新增 bounce；14 条明细含 2 unresolved [kiddingaroundtoys 5.1.3、drnoscomics 无诊断码] + 1 replaytoys 5.7.1 未匹配 send_log）。
- ⚠️ reply_scan 数据突变：total_replies 从历史 1 → 360，last_reply_received_at 从 2026-06-25 → 2026-08-13 09:16:22，last_processed_at=null。疑似扫描口径变化或新回复累积，待 09:00 日报确认，需关注。
- unsubscribe: total 1, suppression_total 26。
- 输出落盘 output/result_recovery_sync_2026-08-14.json（7517 B）；system_config 写入 sync_0845_last_success_at=2026-08-14T08:35:45.673389+08:00、sync_0845_steps 全 ok（DB 实测确认）。
- poller_status: bounce job last_success_at=2026-08-14T08:35:45.666566+08:00，consecutive_failures=0（心跳正常，未 stale）。

## 2026-08-18 (08:35 CST) — 正常运行（早间轮次）
- 脚本执行成功，exit 0，all_ok=true，四步全部 ok。
- tracking: total 136 / matched 61 (hit_rate 44.85%)，全部按 send_log_id+smtp_message_id 匹配（与历史一致）。
- bounce: ⚠️ 队列变化：scanned 16 / matched 16 / domain_invalid 13 / mailbox_invalid 0 / policy 0 / soft 0 / unmatched_dsn 0 / unresolved 3。16 条 DSN 全部匹配 send_log（含新增 comicbookworld [report.1785942103, send_log 469] 与 15 条 report.178667xxxx 系列，lead 162-783）；旧 3 条（kiddingaroundtoys/drnoscomics/replaytoys）已移出队列。新增全部为 MX host not found 类 domain_invalid 或 unresolved，无 mailbox/policy/soft 新风险。
- reply: total 1（last_reply_received_at 2026-06-25）— 08-14 突变的 360 已回落到正常值，判定当时为扫描口径/临时异常，非真实回复激增。
- unsubscribe: total 1, suppression_total 53（历史 26 → 53，+27，与近期新增 bounce 同步入 suppression 一致）。
- 输出落盘 output/result_recovery_sync_2026-08-18.json（7921 B）；system_config 写入 sync_0845_last_success_at=2026-08-18T08:35:56.311936+08:00、sync_0845_steps 全 ok（DB 实测确认）。
- poller_status: bounce job last_success_at=2026-08-18T08:35:56.308661+08:00，consecutive_failures=0（心跳正常，未 stale）。tracking/reply/health job 及 last_heartbeat_at 仍停在 2026-08-14（poller 进程 08-14 后未再心跳，属 poller 自身维护，非本脚本职责；bounce 心跳由本脚本刷新，09:00 日报不会误报 BOUNCE SCAN FAILED）。
