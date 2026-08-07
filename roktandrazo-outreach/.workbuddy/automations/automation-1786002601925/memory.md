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
