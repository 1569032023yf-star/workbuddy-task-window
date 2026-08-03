# Roktandrazo BD 自动化采集系统设计

## 系统目标

建立一个端到端的自动化 BD 线索采集系统，实现：
- **自动采集**：按城市和关键词自动寻找线下门店
- **自动验证**：自动找到官网、提取联系信息、保存证据
- **自动评分**：AI 自动判断线索质量（A/B/C）
- **人工审核**：仅审核 A/B 级线索质量，确认发送批次
- **自动发送**：小批量 SMTP 发送，记录状态
- **闭环监控**：自动检测回复/退信/退订，更新状态

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    自动化采集系统                              │
├─────────────────────────────────────────────────────────────┤
│  1. 城市选择器 (City Selector)                               │
│     • 按策略自动选择城市（旅游城市、文化重镇、独立零售密集区）      │
│     • 支持手动指定城市                                        │
│     • 城市候选池管理                                          │
├─────────────────────────────────────────────────────────────┤
│  2. 搜索引擎 (Search Engine)                                 │
│     • WebSearch 工具搜索门店                                  │
│     • 关键词组合：store_type + city + product_keywords         │
│     • 结果过滤和去重                                          │
├─────────────────────────────────────────────────────────────┤
│  3. 官网验证器 (Website Verifier)                             │
│     • 访问官网确认存在                                        │
│     • 提取 contact/wholesale/vendor 页面                      │
│     • 保存 evidence_url                                      │
├─────────────────────────────────────────────────────────────┤
│  4. 联系信息提取器 (Contact Extractor)                        │
│     • 提取公开邮箱（mailto:、页面文本）                        │
│     • 提取 contact form URL                                  │
│     • 提取 wholesale/vendor 页面                              │
│     • 邮箱类型判断（general/owner/buyer/wholesale等）          │
├─────────────────────────────────────────────────────────────┤
│  5. 评分引擎 (Scoring Engine)                                │
│     • 门店类型匹配度（0-40分）                                 │
│     • 联系方式质量（0-30分）                                  │
│     • 官网质量（0-20分）                                      │
│     • 地理位置价值（0-10分）                                  │
│     • 自动分级：A（70+）、B（50-69）、C（<50）                 │
├─────────────────────────────────────────────────────────────┤
│  6. 数据库 (Database)                                        │
│     • SQLite 存储线索、发送日志、屏蔽名单                      │
│     • 去重：domain_hash 唯一约束                              │
│     • 状态管理：new → reviewed → drafted → approved → sent    │
├─────────────────────────────────────────────────────────────┤
│  7. 邮件模板 (Email Template)                                │
│     • 固定模板：圣诞拼图概念                                   │
│     • 纯文本 + HTML 双格式                                    │
│     • 签名 + 退订说明                                        │
├─────────────────────────────────────────────────────────────┤
│  8. 发送引擎 (Sending Engine)                                │
│     • 腾讯企业邮箱 SMTP (465/SSL)                             │
│     • 每日限额控制                                            │
│     • 发送间隔控制                                            │
│     • 状态记录（sent/failed）                                 │
├─────────────────────────────────────────────────────────────┤
│  9. 闭环监控 (Closed-Loop Monitor)                           │
│     • IMAP 检测回复                                          │
│     • 退信检测                                               │
│     • 退订关键词识别                                          │
│     • 自动更新状态                                            │
│     • Suppression list 管理                                   │
├─────────────────────────────────────────────────────────────┤
│ 10. 报告生成器 (Report Generator)                            │
│     • 每周统计：采集数/可发数/发送数/回复数/退信数/退订数        │
│     • HTML 仪表盘                                            │
│     • CSV 导出                                               │
└─────────────────────────────────────────────────────────────┘
```

## 数据流

```
城市选择 → 搜索门店 → 官网验证 → 联系提取 → 自动评分 → 入库
                                                      ↓
                                               人工审核（A/B级）
                                                      ↓
                                               批准发送 → SMTP发送
                                                      ↓
                                               状态更新 → 闭环监控
                                                      ↓
                                               周报输出
```

## 模块详细设计

### 1. 城市选择器 (city_selector.py)

**功能：**
- 维护城市候选池（按类型分类：旅游城市、文化重镇、独立零售密集区）
- 按策略自动选择城市（轮询、优先级、随机）
- 支持手动指定城市
- 记录已搜索城市，避免重复

**城市分类：**
- **旅游城市**：Asheville, Bar Harbor, Sedona, Carmel-by-the-Sea, Taos, Eureka Springs, Savannah, Charleston, Stowe, Woodstock, Park City, Bend, Traverse City, Lake Geneva, Portsmouth, Key West, Santa Fe, Jackson Hole, Nashville, Austin, Portland, Boulder, Cape Cod, Williamsburg, San Antonio, New Orleans, Miami Beach, Sausalito, Monterey, Santa Barbara
- **文化重镇**：Seattle, San Francisco, Los Angeles, San Diego, Denver, Chicago, Boston, New York, Philadelphia, Washington DC
- **独立零售密集区**：Portland OR, Austin TX, Asheville NC, Burlington VT, Boulder CO

**搜索关键词组合：**
```python
search_queries = [
    f"independent toy store {city} {state}",
    f"board game store {city} {state}",
    f"puzzle shop {city} {state}",
    f"gift shop {city} {state} toys games",
    f"museum store {city} {state}",
    f"bookstore gifts {city} {state}",
    f"educational toy store {city} {state}",
    f"family activity store {city} {state}",
]
```

### 2. 搜索引擎 (search_engine.py)

**功能：**
- 使用 WebSearch 工具搜索门店
- 过滤结果：只保留有官网的结果
- 去重：同一门店不同搜索结果合并
- 限制每城市搜索数量（10-20家）

**搜索策略：**
1. 先搜索通用关键词（toy store, gift shop）
2. 再搜索细分关键词（puzzle store, board game store）
3. 验证官网存在
4. 提取联系信息

### 3. 官网验证器 (website_verifier.py)

**功能：**
- 访问官网确认存在
- 查找 contact 页面
- 查找 wholesale/vendor 页面
- 保存 evidence_url

**验证逻辑：**
```python
def verify_website(url):
    # 1. 访问首页，确认存在
    # 2. 查找 contact 页面链接
    # 3. 查找 wholesale/vendor 页面链接
    # 4. 返回验证结果
```

### 4. 联系信息提取器 (contact_extractor.py)

**功能：**
- 从官网提取邮箱（mailto:、页面文本）
- 提取 contact form URL
- 判断邮箱类型（general/owner/buyer/wholesale等）
- 保存 evidence_url

**提取逻辑：**
```python
def extract_contact_info(url):
    # 1. 查找 mailto: 链接
    # 2. 查找邮箱文本模式
    # 3. 查找 contact form
    # 4. 判断邮箱类型
    # 5. 返回联系信息
```

### 5. 评分引擎 (scorer.py)

**评分维度：**
1. **门店类型匹配度（0-40分）**
   - 完美匹配（toy store, puzzle store, game store）：40分
   - 良好匹配（gift shop, bookstore, museum store）：30分
   - 一般匹配（其他零售店）：20分

2. **联系方式质量（0-30分）**
   - 有明确邮箱：30分
   - 有通用邮箱（info@, help@）：28分
   - 有免费邮箱（gmail, yahoo）：25分
   - 只有 contact form：15分
   - 无联系方式：0分

3. **官网质量（0-20分）**
   - 有官网：10分
   - 有证据链接：+5分
   - 有专门的 contact/wholesale 页面：+5分

4. **地理位置价值（0-10分）**
   - 旅游城市：10分
   - 非核心旅游城市：5分

**分级标准：**
- A 级（70+分）：官网邮箱明确 + 门店类型高度匹配 + 有实体地址
- B 级（50-69分）：有官网/contact form + 类型匹配
- C 级（<50分）：信息不完整

### 6. 数据库 (bd_db.py)

**表结构：**
- **leads**：线索表
- **suppression_list**：屏蔽名单
- **send_log**：发送日志

**状态流转：**
```
new → reviewed → drafted → approved → queued → sent
                                              ↓
                              replied / bounced / unsubscribed / do_not_contact / failed
```

### 7. 邮件模板 (bd_template.py)

**固定模板：**
```
Subject: A New "One Puzzle a Day" Christmas Puzzle Concept

Hi {{Store Name}} team,

I'm Ian from rokt&razo.

We have over 10 years of experience developing and manufacturing jigsaw puzzles and family card games.

We're currently looking for U.S. retail partners and offer:

• Low opening MOQs
• Competitive door-to-door pricing (hassle free)
• Unique puzzle collections with proven online demand
• Custom and private-label programs

If you're interested, I'd be happy to share our newest Christmas 24 Mini Pack Puzzle Series and wholesale pricing.

Best regards,

Ian
Business Development Specialist
rokt&razo
roktandrazo.com

Play, Learn, Laugh!
Family card games, kids learning toys, jigsaw puzzles & more

---
If this isn't relevant, just reply "unsubscribe" and I won't follow up.
```

### 8. 发送引擎 (bd_sender.py)

**功能：**
- 腾讯企业邮箱 SMTP (465/SSL)
- 每日限额控制（默认30封）
- 发送间隔控制（默认60秒）
- 状态记录（sent/failed）
- Test Mode 支持

**发送规则：**
1. 只发送 approved 状态的线索
2. 必须有 email
3. 不能在 suppression list 中
4. 同一 domain 未发过
5. 每次最多发送 5 封测试邮件
6. 测试通过后调整到每天 30-50 封

### 9. 闭环监控 (closed_loop_monitor.py)

**功能：**
- IMAP 检测回复
- 退信检测
- 退订关键词识别
- 自动更新状态
- Suppression list 管理

**监控逻辑：**
1. 如果收到回复 → status=replied，停止 follow-up
2. 如果邮件退信 → status=bounced，加入 suppression list
3. 如果对方回复 unsubscribe / remove me / not interested / don't contact → status=unsubscribed 或 do_not_contact，加入 suppression list
4. 所有 suppression email/domain 后续不得再发
5. follow-up 只对 sent 且未 replied / bounced / unsubscribed 的线索触发

### 10. 报告生成器 (report_generator.py)

**功能：**
- 每周统计：采集数/可发数/发送数/回复数/退信数/退订数
- HTML 仪表盘
- CSV 导出

**报告内容：**
- 本周新增线索数
- A/B/C 级线索分布
- 已发送邮件数
- 回复率/退信率/退订率
- 下周计划

## 配置管理

### 环境变量 (.env)
```bash
# SMTP Configuration
BD_SMTP_HOST=smtp.exmail.qq.com
BD_SMTP_PORT=465
BD_SMTP_SSL=true
BD_SMTP_USER=ianyf@roktandrazo.com
BD_SMTP_PASS=***

# Sender Identity
BD_FROM_NAME=Ian
BD_FROM_EMAIL=ianyf@roktandrazo.com

# IMAP Configuration
BD_IMAP_HOST=imap.exmail.qq.com
BD_IMAP_PORT=993
BD_IMAP_SSL=true
BD_IMAP_USER=ianyf@roktandrazo.com
BD_IMAP_PASS=***

# Sending Limits
BD_MAX_PER_BATCH=5
BD_MAX_PER_DAY=30
BD_DELAY_SECONDS=60

# Test Mode
BD_TEST_MODE=false
BD_TEST_EMAIL=ianyf@roktandrazo.com
```

## 部署和运行

### 初始化
```bash
# 1. 创建 .env 文件
# 2. 初始化数据库
python bd_db.py

# 3. 测试 SMTP 连接
python bd_main.py test-send
```

### 日常运行
```bash
# 1. 自动采集新线索
python auto_collector.py --cities 3

# 2. 查看系统状态
python bd_main.py status

# 3. 批准 A/B 级线索
python bd_main.py approve-all

# 4. Dry-run 预览
python bd_main.py dry-run

# 5. 实际发送
python bd_main.py send

# 6. 生成报告
python report_generator.py
```

## 人工审核范围

**人工只负责：**
1. 审核 A/B 级线索质量
2. 确认 dry-run 批次是否可以发送
3. 处理异常情况（退信、投诉等）

**人工不负责：**
1. 一个个找邮箱
2. 手动复制门店资料
3. 手动发送邮件

## 质量保证

### 发送前检查
1. Subject 无 `[TEST→]` 标签
2. 正文无 `TEST STORE`、`{{Store Name}}`、`undefined`、`None`、`null`
3. 每封使用真实门店名
4. 邮箱不在 suppression list 中
5. 同一 domain 未发过
6. From: Ian <ianyf@roktandrazo.com>
7. Reply-To: ianyf@roktandrazo.com
8. 签名 + 退订说明正常

### 发送后监控
1. 记录 sent_at 和 status
2. 检测回复、退信、退订
3. 自动更新状态
4. 加入 suppression list（如需要）

## 扩展计划

### 第一阶段（当前）
- 3 个试点城市
- 每城市 10-20 家门店
- 目标总线索 100-200 条

### 第二阶段
- 10 个美国城市
- 每城市 10-20 家门店
- 目标总线索 200-400 条

### 第三阶段
- 每周 20 个美国城市
- 自动化采集流程
- 每周输出报告

## 验收标准

系统闭环成功的标准：
1. ✅ 能自动收集线索
2. ✅ 能自动生成草稿
3. ✅ 能人工审核
4. ✅ 能进入发送队列
5. ✅ 能通过企微邮箱发送
6. ✅ 能记录 sent
7. ✅ 能识别失败
8. ✅ 能记录 replied / bounced / unsubscribed
9. ✅ 能防止重复发送
10. ✅ 能停止对已回复、已退信、已退订线索的跟进