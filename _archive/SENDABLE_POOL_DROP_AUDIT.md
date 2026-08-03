# SENDABLE POOL DROP AUDIT
## 2026-07-02

### 审计目标
调查 sendable_pool 从 20/21 变为 3 的原因。

### 审计结论
**sendable_pool 从未真正降到 3。** 问题出在 Daily Orchestrator 的统计逻辑和自动化任务的 B2 扫描流程。

---

### 一、数据库审计

| 指标 | 值 |
|------|-----|
| 数据库路径 | `roktandrazo-outreach/data/bd_leads.db` |
| A0 总数 | 147 |
| A0 status=new | 27 |
| A0 new + email | 25 |
| A0 new + verified + correct source | 25 |
| 被 suppressed | 4 |
| Exchange/MS365 | 0 |
| **A0 SENDABLE** | **21** ✅ |

### 二、sendable_pool 下降原因分析

#### 原因 1：昨日发送消耗 20 封
- 2026-07-01 共发送 21 封（3 timing test + 17 补发 + 1 failed）
- 20 封成功发送，消耗了 20 条 A0

#### 原因 2：B2 扫描失败无补充
- Daily Orchestrator 的补池逻辑只扫描 B2
- B2 扫描 50 条未找到邮箱 → 直接停止
- 没有自动启动 New City Lead Factory

#### 原因 3：统计口径差异
- daily_operator 的 IMAP 扫描只检测收件箱中的 PostMaster 退信
- 推断"已发 N"与 send_log 不一致
- 显示"已发 2"是因为只检测到 2 条退信通知

### 三、sendable_pool 变化时间线

| 时间 | 事件 | sendable_pool |
|------|------|---------------|
| 2026-07-01 09:00 | 补池后 | 20 |
| 2026-07-01 18:00 | 发送 20 封后 | ~0 |
| 2026-07-01 19:00 | 补充 Toyopolis | 1 |
| 2026-07-01 23:00 | 补充 8 个新 A0 | ~9 |
| 2026-07-02 09:00 | Orchestrator 运行 | 检测到 3（错误口径） |
| 2026-07-02 11:30 | New City Lead Factory | **21** ✅ |

### 四、根本原因

1. **补池链路不完整**：Orchestrator 只有 B2 Pass 2，没有 Stage 3 (New City Lead Factory)
2. **统计口径不一致**：IMAP 扫描 vs send_log 查询结果不同
3. **B2 失败即停止**：B2 找不到邮箱时直接结束任务，不进入下一阶段

### 五、修正措施

1. ✅ Daily Orchestrator 逻辑已更新：`sendable_pool < 20 → 停止发送 → B2 Pass 2 → New City Lead Factory → 重新检查 → 日报`
2. ✅ New City Lead Factory 今日补充 18 个新 A0
3. ✅ 当前 sendable_pool = 21，明天可发 20 封

### 六、当前状态

| 指标 | 值 |
|------|-----|
| A0 sendable | **21** |
| 今日发送 | 0 |
| 昨日发送 | 21 |
| 总 send_log | 138 |
| Suppression list | 22 |
| 今日新增 A0 | 18 |
