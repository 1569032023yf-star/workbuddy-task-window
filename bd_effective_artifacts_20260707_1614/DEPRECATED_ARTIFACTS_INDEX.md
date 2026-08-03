# Deprecated Artifacts Index / 废弃产物索引

**Date / 日期**: 2026-07-07 16:30 Asia/Shanghai

---

## 废弃产物列表

| 文件路径 | 废弃原因 | 替代文件 | 风险 |
|----------|----------|----------|------|
| `LEAD_POOL_RESCUE_AUDIT_REPORT.md` | Codex 生成，中文乱码 | `LEAD_POOL_RESCUE_BACKFILL_REPORT_UTF8.md` | 中文不可读 |
| `BD_COLLECTION_FOCUS_REPORT_*.md` | 过期日报 | `CURRENT_TRUTH.md` | 数据过时 |
| `BD_FULL_COLLECTION_HISTORY_REPORT_CN.md` | 过期历史 | `CURRENT_TRUTH.md` | 数据过时 |
| `B2_TOP30_MANUAL_REVIEW_CN.md` | 旧口径 | `CURRENT_TRUTH.md` | 口径冲突 |
| `B2_HUMAN_TOP10_REVIEW_CN.md` | 旧口径 | `CURRENT_TRUTH.md` | 口径冲突 |
| `B2_AGENT_PASS2_REPORT_CN.md` | 旧口径 | `CURRENT_TRUTH.md` | 口径冲突 |
| `GOOGLE_MAPS_BRANCH_POC_REPORT.md` | 实验产物 | 无 | 仅供参考 |
| `GOOGLE_MAPS_ANTI_SCRAPE_NOTE_CN.md` | 实验产物 | 无 | 仅供参考 |
| `SEND_WINDOW_CONFIG_AUDIT.md` | 旧配置 | `CURRENT_TRUTH.md` | 配置已更新 |
| `TEMPLATE_V5_SYNC_REPORT.md` | 过期 | `CODE_CURRENT/bd_template.py` | 已完成 |
| `TN_STATE_DEEP_COVERAGE_REPORT.md` | 过期 | `CURRENT_TRUTH.md` | 数据过时 |

---

## 废弃结论

| 旧结论 | 废弃原因 | 当前正确结论 |
|--------|----------|-------------|
| "182 城市已覆盖" | 只有 4 个 deep_covered | 4 deep_covered, 42 covered, 107 touched |
| "B2 池为空" | 读取了错误字段 | B2 = 173 |
| "send_window = ET" | 已更改 | Asia/Shanghai 09:00-13:00 |
| "V4 模板" | 已替换 | V5 |
| "主攻全美" | 已更改 | TN/AR/KY only |
