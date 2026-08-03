# CODEX_START_HERE.md — Codex 入口

**Date / 日期**: 2026-07-07 16:30 Asia/Shanghai

---

## 阅读顺序

1. **先读** `CURRENT_TRUTH.md` — 当前唯一事实源
2. **再读** `PROJECT_RULES/` — 项目规则和护栏
3. **再读** `RUNBOOK/` — 运行手册
4. **再读** `EFFECTIVE_ARTIFACT_MANIFEST.md` — 产物清单
5. **不要** 直接读旧 WorkBuddy 全目录
6. **不要** 直接写 WorkBuddy 生产目录

---

## 关键规则

1. **只读原则**: 不得写回本目录中的任何文件
2. **复制原则**: 可以将文件复制到 `D:\CODEX` 作为参考
3. **禁止复制**: `data/bd_leads.db`（生产数据库）
4. **编码原则**: 复制时保持 UTF-8 BOM 编码
5. **事实原则**: 以 `CURRENT_TRUTH.md` 为最高可信源

---

## 当前状态速读

| 项目 | 值 |
|------|-----|
| strict sendable_pool | 10 |
| canary gate | 20 |
| inventory target | 60 |
| send_pause | true |
| 主攻州 | TN, AR, KY |
| 模板 | V5 |
| 每日目标 | 20 |

---

## 下一步

1. 扩池：补 10+ A0 到 canary gate
2. 回填 evidence_snippet：35 条待处理
3. 修复 Message-ID：Codex 正在处理
4. 解除 send_pause：用户确认后

---

## 写回生产

**任何写回生产都需要用户确认。**
