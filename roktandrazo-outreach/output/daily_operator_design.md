# BD Daily Operator Window — 设计方案

## 一、08:30–12:00 本地发送排程

### 总时间线

```
08:30   ─── 窗口开启，准备当天材料
08:40   ─── Batch 1 发送（5封）
09:00   ─── Batch 1 结束
09:15   ─── Batch 1 后扫描（bounce/reply/unsub/auto_reply）
09:30   ─── Batch 2 发送（5封）
09:50   ─── Batch 2 结束
10:05   ─── Batch 2 后扫描
10:20   ─── Batch 3 发送（5封）
10:40   ─── Batch 3 结束
10:55   ─── Batch 3 后扫描
11:10   ─── Batch 4 发送（5封）
11:30   ─── Batch 4 结束
11:45   ─── Batch 4 后扫描
12:00   ─── 日报输出，窗口关闭
```

### 发送间隔
- 同一批内每封间隔：**3–5 分钟**（随机）
- 第一批后如果触发了暂停规则，后面的批次自动跳过

---

## 二、Day 1 20 封四批计划

当前池状态：
| 池 | 数量 | 说明 |
|---|---|---|
| A0（可发） | **27** | Verified Official Email + 非 Exchange |
| A1（Exchange） | 0 | 无需从 A1 取 |
| B（猜测邮箱） | 186 | 等待人工确认 |
| C（contact form） | 19 | 仅 contact form |

Day 1 只需要从 A0 池取 20 封，不需要 B 池人工审批。

### Batch 1 (08:40–09:00)
5 封，来自 A0 池前 5 条

### Batch 2 (09:30–09:50)
5 封，来自 A0 池第 6–10 条

### Batch 3 (10:20–10:40)
5 封，来自 A0 池第 11–15 条

### Batch 4 (11:10–11:30)
5 封，来自 A0 池第 16–20 条

### 发送顺序优先级（合并后）
1. **A0**: Verified Official Email（官网已验证邮箱，非 Exchange MX）
2. **A1**: High-confidence Official Email（Exchange/Outlook 邮箱，降至次优先）
3. **approved_manual_send**: 你人工确认过的 B 池邮箱（从 CSV 导入后进入此状态）

### 绝对不发
- guessed_email 类型
- B/C 级线索
- contact form 线索
- 已 hard bounce 的邮箱
- delivery_issue 状态的线索
- suppression list 中的邮箱
- 已 sent 的邮箱或域名
- Exchange / Microsoft 365 高风险 MX（除非你手动批准）

---

## 三、B 池 CSV 新字段版本

### 新 CSV 路径
`roktandrazo-outreach/output/b_pool_manual_review.csv`

### 字段列表（旧 → 新）

```
id
store_name
domain
store_type
city
state
official_website
guessed_email (当前邮箱)
evidence_url
contact_form_url
product_fit
mx_status (DNS MX 查询结果)
-- 以下是新增的人工字段 --
manual_found_email       ← 你人工找到的真实邮箱
manual_email_source_url  ← 该邮箱出现在哪个官网页面
manual_email_source_type ← official_page_visible / official_mailto /
                           wholesale_vendor_page / other
manual_decision          ← approve / reject / contact_form / review_later
manual_note              ← 你的备注（可选）
manual_verified_by       ← 默认为 "user"
manual_verified_at       ← 导入时自动填写
```

### 新增字段在数据库中的映射

在 `bd_leads.db.leads` 表新增 7 列：

| 列名 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| manual_found_email | TEXT | NULL | 人工找到的邮箱 |
| manual_email_source_url | TEXT | NULL | 邮箱来源页面 |
| manual_email_source_type | TEXT | NULL | 来源类型枚举 |
| manual_decision | TEXT | NULL | 决策：approve/reject/contact_form/review_later |
| manual_note | TEXT | NULL | 备注 |
| manual_verified_by | TEXT | 'user' | 验证人 |
| manual_verified_at | TIMESTAMP | NULL | 验证时间 |

---

## 四、B 池导入脚本设计

### 脚本路径
`roktandrazo-outreach/b_pool_import.py`

### 执行方式
```bash
python b_pool_import.py --csv output/b_pool_manual_review.csv
```

### 导入规则

#### 规则 A：manual_decision = approve
**前提：** manual_found_email 非空 AND manual_email_source_url 非空

```
1. 把 manual_found_email → leads.email
2. 把 email_source_type → "manual_verified_official"
3. 把 email_verified_on_official_site → 1 (true)
4. 把 evidence_url → manual_email_source_url
5. 把 manual_email_source_type → 对应值
6. 把 status → "approved_manual_send"
7. 写入 manual_verified_by / manual_verified_at
```

导入后**后续检查**：
- ✅ MX 检查（无 MX 记录则降级为 C，不发送）
- ✅ suppression_list 检查（有则跳过）
- ✅ sent_log 检查（已发过则跳过）
- ✅ bounce_log 检查（曾退信则跳过）
- ✅ 同一 domain 已 sent 过则跳过

全部通过后进入 `approved_manual_send` 可发送池。

#### 规则 B：manual_decision = reject
```
1. status → "rejected"
2. 写入 manual_note 和 manual_decision
3. 不进入发送池
```

#### 规则 C：manual_decision = contact_form
```
1. status → "contact_form_pool"
2. email 类型标记为 contact_form_only
3. 不进入发送池
```

#### 规则 D：manual_decision = review_later
```
1. status → "manual_review_needed"
2. 保留在待定区，不发送
```

---

## 五、approved_manual_send 的发送规则

### 优先级位置
在 A0/A1 之后，B/C 之前：
```
优先级: A0 > A1 > approved_manual_send > (B/C 不发)
```

### 检查链（每次发送前逐项检查）
```
1. email 非空 → 通过
2. MX 存在（免费邮箱跳过）→ 通过
3. 不在 suppression_list → 通过
4. lead_id 不在 send_log (status='sent') → 通过
5. domain 未出现在已发送记录中 → 通过（避免多发同一门店）
6. 无 hard_bounce 历史 → 通过
7. 无 delivery_issue 历史 → 通过
```

### 发送行为
- 与 A0 相同的模板和发送间隔
- 计入当天 20 封限额
- 跟随 Batch 发送排程

---

## 六、当天 12:00 前日报格式

### 脚本路径
`roktandrazo-outreach/agent_daily_report.py`

### 输出格式

```
========================================
BD Daily Report — 2026-06-25
========================================

[发送摘要]
  当天目标:        20 / 20 ✅
  实际发送:        20
  Batch 1 (08:40): 5/5 ✅
  Batch 2 (09:30): 5/5 ✅
  Batch 3 (10:20): 5/5 ✅
  Batch 4 (11:10): 5/5 ✅

[送达状态]
  成功送达:        18
  Hard Bounce:     1 ← 已加入 suppression
  Policy Bounce:   0
  Soft Bounce:     1

[回复摘要]
  新回复:          0
  高意向回复:      0
  自动回复:        1 (OOO: John at Toy Store)
  退订:            0

[池剩余]
  A0 (可发):       7
  A1 (Exchange):   0
  approved_manual: 0
  B (需人工确认):   186
  C (contact form):19

[暂停状态]
  send_pause:      false
  pause_reason:    -

[违规/异常]
  模板变量未替换:   无
  重复发送:        无
  Suppression写入失败: 无
  Bounce分类失败:   无

[建议]
  • A0 剩余 7 封，明天全部发送后 A0 耗尽
  • 建议补充 B 池人工审批 CSV，用 manual_decision 导入
  • 下一个 A 级线索采集计划：待定

========================================
```

### 输出位置
`roktandrazo-outreach/output/daily_report_YYYY-MM-DD.md`

---

## 实施文件清单

| # | 文件 | 类型 | 说明 |
|---|---|---|---|
| 1 | `output/daily_operator_design.md` | 设计文档 | 本文档 |
| 2 | `b_pool_import.py` | 新脚本 | B 池 CSV 一键导入 |
| 3 | `daily_session.py` | 新脚本 | 操作员会话：发送+扫描+日报 |
| 4 | `output/b_pool_manual_review.csv` | 新文件 | 含 7 个人工字段的 B 池 CSV |
| 5 | `bd_db.py` | 修改 | 新增 7 列 + approved_manual_send 查询 |
| 6 | `pool_analysis.py` | 修改 | 输出新格式 B 池 CSV |
| 7 | `agent_daily_report.py` | 新脚本 | 12:00 日报生成 |

