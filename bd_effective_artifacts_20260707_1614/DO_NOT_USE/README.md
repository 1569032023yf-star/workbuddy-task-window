# DO_NOT_USE — 禁用产物说明

**Date / 日期**: 2026-07-07 16:30 Asia/Shanghai

---

## 为什么这些产物不能用

以下产物存在编码问题、事实错误、或已被新版本替代，不应继续使用。

---

## 禁用列表

### 1. LEAD_POOL_RESCUE_AUDIT_REPORT.md (Codex 生成)

- **路径**: `roktandrazo-outreach/LEAD_POOL_RESCUE_AUDIT_REPORT.md`
- **问题**: 中文全部为 `????`，ASCII 编码，不可读
- **替代**: `REPORTS_TRUSTED/LEAD_POOL_RESCUE_BACKFILL_REPORT_UTF8.md`
- **风险**: 中文内容丢失，英文部分可参考但不可信

### 2. 旧日报文件

- **路径**: `BD_DAILY_*_REPORT*.md`, `BD_WEEKLY_*.md`
- **问题**: 过期，不代表当前状态
- **替代**: `CURRENT_TRUTH.md`
- **风险**: 数据已过时

### 3. 旧 B2 处理记录

- **路径**: `B2_*.md`
- **问题**: 使用旧口径（B2 = status='new'），与当前口径冲突
- **替代**: `CURRENT_TRUTH.md` 中的 B2 定义
- **风险**: 统计口径错误

### 4. 旧 Google Maps POC

- **路径**: `GOOGLE_MAPS_*.md`
- **问题**: 实验性质，不代表正式流程
- **替代**: 无（仅供参考）
- **风险**: 数据可能不准确

### 5. "182/183 城市已覆盖" 报告

- **路径**: 任何包含此说法的报告
- **问题**: 事实错误。实际只有 4 个 deep_covered
- **替代**: `CITY_COVERAGE_STATUS_AUDIT.md`
- **风险**: 严重误导

### 6. 旧 send_window 配置

- **问题**: 使用 America/New_York
- **替代**: Asia/Shanghai 09:00-13:00
- **风险**: 发送时间错误

### 7. V4 模板

- **问题**: 已被 V5 替代
- **替代**: `CODE_CURRENT/bd_template.py` (V5)
- **风险**: 邮件内容过时

---

## 安全提醒

这些文件仍保留在原目录中，但不应被 Codex 或 WorkBuddy 作为事实来源引用。
