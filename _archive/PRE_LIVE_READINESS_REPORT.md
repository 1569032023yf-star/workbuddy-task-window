# PRE-LIVE READINESS REPORT

**Date**: 2026-06-29 18:00  
**Executor**: Pre-live Readiness Gate (只读状态确认，未执行任何发送)

---

## 1. 当前真实项目路径

| 项目 | 路径 |
|------|------|
| 真实项目 | `C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach` |
| 当前工作目录 | `C:\Users\15690\WorkBuddy\2026-06-05-15-31-42` |

---

## 2. 当前数据库路径

| 项目 | 值 |
|------|-----|
| 活动数据库路径 | `roktandrazo-outreach\data\bd_leads.db` |
| 活动数据库大小 | 389,120 bytes (380 KB) |
| 活动数据库修改时间 | 2026-06-29 17:46:49 |
| 活动数据库创建时间 | 2026-06-11 10:10:36 |
| 备份数据库路径 | `roktandrazo-outreach_backup_before_phase2_20260629_1732\data\bd_leads.db` |
| 备份数据库大小 | 389,120 bytes (同大小) |
| 代码读取配置来源 | `bd_db.py` 第12行: `DB_PATH = os.path.join(os.path.dirname(__file__), "data", "bd_leads.db")` |
| 是否存在多个 bd_leads.db | ❌ 否，仅一个 |
| 当前代码实际读取哪个 | `roktandrazo-outreach\data\bd_leads.db` (唯一) |

---

## 3. 当前数据库是否为旧库

✅ **是旧库，数据库连续性正常。**

证据：
- 总线索数: **323 条** (非空库)
- 已发送: **69 条** (有历史发送记录)
- send_log: **101 条** (有完整发送日志)
- suppression_list: **22 条** (有压制名单)
- bounce_log: **12 条** (有退信记录)
- reply_log: **1 条** (有回复记录)
- system_config: **32 条** (有系统配置)
- 数据库创建于 2026-06-11，非 Phase 2 新建

**Phase 2 未指向新空数据库。**

---

## 4. 当前池状态

### 数据库统计

| 指标 | 数量 |
|------|------|
| **Total leads** | **323** |
| status=new | 230 |
| status=sent | 69 |
| status=bounced | 9 |
| status=delivery_issue | 9 |
| status=manual_review_needed | 3 |
| status=contact_form_pool | 2 |
| status=bounce_review | 1 |

### 邮箱来源分布

| email_source_type | 数量 |
|-------------------|------|
| guessed_email | 187 |
| None/空 | 66 |
| official_page_visible | 50 |
| contact_form_only | 11 |
| official_mailto | 4 |
| no_contact_found | 3 |
| unknown | 2 |

### 验证状态

| email_verified_on_official_site | 数量 |
|---------------------------------|------|
| 1 (已验证) | 54 |
| 0 (未验证) | 203 |
| None | 66 |

### 日志表

| 表 | 记录数 |
|----|--------|
| send_log | 101 |
| bounce_log | 12 |
| reply_log | 1 |
| suppression_list | 22 |
| system_config | 32 |

---

## 5. A0=0 的真实原因

### 结论

**A0=0 是因为真实库存耗尽，所有 54 条已验证线索均已消耗完毕，最后 3 条剩余的已验证线索全部在 suppression_list 中。**

### SQL 证据

A0 查询条件（来自 `daily_operator_auto.py` 第84-92行 `get_sendable_inventory()`）：
```sql
SELECT COUNT(*) FROM leads 
WHERE status='new' 
AND confidence_score='A'
AND email_verified_on_official_site=1
AND email_source_type IN ('official_page_visible','official_mailto','wholesale_vendor_page')
AND email IS NOT NULL AND email != ''
AND email NOT IN (SELECT email FROM suppression_list)
AND id NOT IN (SELECT lead_id FROM send_log WHERE status IN ('sent','bounced'))
AND id NOT IN (SELECT lead_id FROM bounce_log)
AND (mx_provider IS NULL OR mx_provider = '' OR ...)
```

**54 条已验证线索的消耗路径：**

| 类别 | 数量 | 说明 |
|------|------|------|
| 已发送 (sent) | 49 | 正常消耗 |
| 已退信 (bounced) | 2 | 正常排除 |
| 在 suppression_list 中 | 3 | 被压制，不可发送 |
| **合计** | **54** | 全部消耗完毕 |

**最后 3 条被压制的线索：**

| ID | 门店 | 邮箱 | 压制原因 |
|----|------|------|----------|
| 27 | Thinker Toys (Carmel) | carmel@thinkertoys.com | 在 suppression_list 中（精确匹配） |
| 29 | The Acadia Shops | shop@acadiashops.com | 在 suppression_list 中（精确匹配） |
| 31 | Packrat's Paradise | PackratsParadiseES@gmail.com | 在 suppression_list 中（精确匹配） |

**这 3 条线索为什么被压制？** 需要查看历史记录。可能是之前发送后收到退信/退订/投诉，或者是手动加入的。

### 排除其他原因

| 假设 | 验证结果 |
|------|----------|
| Phase 2 指向新空数据库？ | ❌ 否，数据库有 323 条记录，创建于 2026-06-11 |
| 查询条件变严格？ | ❌ 否，查询条件与历史一致 |
| 字段名/状态迁移？ | ❌ 否，字段名未变 |
| 旧 A0 已 sent/bounced/suppressed？ | ✅ 是，54 条全部消耗 |

---

## 6. 旧 B/C 池是否还在

✅ **旧 B/C 池完整保留。**

### 数据库中的 B/C 池

| 池 | 数量 | 说明 |
|----|------|------|
| guessed_email (B 池) | 187 | 数据库中 `email_source_type='guessed_email'` |
| contact_form_only (C 池) | 11 | 数据库中 `email_source_type='contact_form_only'` |
| B2 manual_review_needed | 3 | 数据库中 `status='manual_review_needed'` |
| contact_form_pool | 2 | 数据库中 `status='contact_form_pool'` |

### Output 目录中的 B 池文件

| 文件 | 存在 | 大小 | 行数 | 修改时间 |
|------|------|------|------|----------|
| b_pool_manual_review.csv | ✅ | 34,361 B | 187 | 2026-06-25 09:51 |
| b2_high_value_manual_review.csv | ✅ | 44,012 B | 217 | 2026-06-26 18:26 |
| b2_guess_candidates.csv | ✅ | 1,334 B | 9 | 2026-06-24 16:57 |
| b_pool_approval.csv | ✅ | 42,545 B | 187 | 2026-06-24 16:19 |
| tier2_cities.json | ✅ | 2,664 B | 43 | 2026-06-26 09:16 |

**结论：B 池 187 条 guessed_email 完整保留在数据库和 CSV 文件中。**

---

## 7. 当前 sendable_pool

**sendable_pool = 0**

| 组成部分 | 数量 |
|----------|------|
| A0 (verified + non-suppressed + non-sent) | 0 |
| approved_manual_send | 0 |
| **Total sendable** | **0** |

sendable_pool 为 0 的原因：所有 54 条已验证线索中，49 条已发送，2 条已退信，3 条在压制名单中。

---

## 8. 发送资格检查

自动发送池的安全链验证：

| 检查项 | 状态 |
|--------|------|
| 只包含 A0 + approved_manual_send | ✅ 是 |
| email_verified_on_official_site=true | ✅ 是 |
| 非 guessed_email | ✅ 是 |
| 非 B/C | ✅ 是 |
| 非 suppression | ✅ 是 |
| 非 sent | ✅ 是 |
| 非 bounced | ✅ 是 |
| 非 delivery_issue | ✅ 是 |
| 非 Exchange/Microsoft 365 MX | ✅ 是 |

**结论：发送资格检查逻辑正确，无误发风险。**

---

## 9. 是否建议先 Inventory Live

✅ **是，强烈建议先进入 Inventory Live（库存生产模式），不进入 Send Live。**

原因：
- A0=0，无法发送
- B 池有 187 条 guessed_email 待 Browser Verifier 验证
- 需要通过 Lead Factory 采集新城市线索
- 需要通过 Browser Verifier 将 B 池升级为 A0

---

## 10. 是否满足 20 封 Send Live

❌ **不满足。**

### 验收条件检查

| 条件 | 状态 | 说明 |
|------|------|------|
| sendable_pool >= 20 | ❌ | 当前为 0 |
| 新增 A0 均有 evidence_url | N/A | 无新增 A0 |
| 新增 A0 均不是 guessed_email | N/A | 无新增 A0 |
| Browser Verifier 没有错升 | N/A | 尚未运行 |
| suppression/bounced/delivery_issue 被排除 | ✅ | 已排除 |
| dry-run 计划显示 20 封以内 | N/A | 无可发送 |
| stop-on-risk 已开启 | ❌ | 当前为 DISABLED |
| 当前时间在发送窗口内 | ❌ | 当前 18:00，窗口 08:30-12:00 |

---

## 11. 阻塞点

1. **A0 库存为 0** — 所有 54 条已验证线索已消耗（49 发送 + 2 退信 + 3 压制）
2. **sendable_pool = 0** — 无可发送线索
3. **B 池 187 条未验证** — 需要 Browser Verifier 处理
4. **stop-on-risk 未开启** — 需要配置
5. **当前时间 18:00** — 已过发送窗口 08:30-12:00

---

## 12. 风险检查

| 风险项 | 状态 |
|--------|------|
| guessed_email 误发风险 | ❌ 无（sendable_pool=0，不可能发送） |
| B/C 误发风险 | ❌ 无（B/C 不在 sendable 逻辑中） |
| suppression 误发风险 | ❌ 无（已被排除） |
| bounced 误发风险 | ❌ 无（已被排除） |
| delivery_issue 误发风险 | ❌ 无（已被排除） |

---

## 13. 建议下一步

### Inventory Live 操作清单

1. **Browser Verifier 批量验证 B 池**
   - 目标：从 187 条 guessed_email 中提取官网真实邮箱
   - 预期升级：根据 Phase 2 测试，约 10-20% 可升级为 A0
   - 命令：`python browser_verifier.py --batch 50 --timeout 15`

2. **Lead Factory 新城市采集**
   - 可用城市：20 个（tier2_cities.json 中未覆盖的）
   - 建议采集：5 个城市
   - 目标：每个城市 5-10 个新线索

3. **Suppression List 审查**
   - 当前 22 条压制记录
   - 检查 3 条被压制的已验证线索是否可以解除压制

4. **配置 stop-on-risk**
   - 命令：`python daily_operator_auto.py --stop-on-risk`

### 进入 20 封 Send Live 的条件

- sendable_pool >= 20
- stop-on-risk 已开启
- 当前时间在 08:30-12:00 窗口内
- dry-run 验证通过

---

## 14. 最终结论

| 指标 | 值 |
|------|-----|
| 数据库连续性是否正常 | ✅ 是 |
| 旧线索池是否还在 | ✅ 是（323 条，B 池 187 条完整） |
| A0=0 的真实原因 | 54 条已验证线索全部消耗：49 发送 + 2 退信 + 3 压制 |
| 是否建议 Inventory Live | ✅ 是 |
| 是否可以进入 20 封真实发送 | ❌ 否 |
| 缺什么 | A0 库存（需 Browser Verifier + Lead Factory 补充） |

---

**⚠️ 重要提醒：本报告为只读状态确认，未执行任何发送、修改或删除操作。**

*Generated at 2026-06-29 18:00*
