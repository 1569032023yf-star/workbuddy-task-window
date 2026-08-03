# 回信与动作跟踪表 / Reply & Action Tracker
## 2026-07-02

---

## A. 需要我亲自回复

### 🔴 高优先：Great Escape Adventures

| 字段 | 内容 |
|------|------|
| 商家 | Great Escape Adventures |
| 城市 | Ithaca, NY（纽约州伊萨卡） |
| 门店类型 | 桌游/爱好店，**4 家社区门店** |
| 回复人 | Nate（sales@greatescapeadventures.net） |
| 回复时间 | 2026-06-30 15:12 EDT |
| 回复内容 | "Hey Ian! Thank you for taking the time to reach out to us! Do you sell through any distributors, or is it only directly through you guys as wholesale? Thanks, Nate" |
| 回复分类 | **高意向 / Hot reply** |
| 建议回复方向 | 说明分销政策：目前支持直接批发（Direct Wholesale），MOQ 低，DDP 到门。如有分销商渠道需求，可进一步讨论。附上产品目录和价格表。 |
| 需要报价 | ✅ |
| 需要样品 | 可选（如果 Nate 表示兴趣） |
| 需要 catalog | ✅ |
| 需要 Zoom | 暂不需要，先邮件沟通 |
| 需要 follow-up | ✅ 立即回复 |
| 建议回复模板 | 见下方 |

#### 建议回复草稿

```
Subject: Re: Card games & puzzles for Great Escape Adventures — wholesale from Roktandrazo

Hi Nate,

Thank you for getting back to us! Great to hear from a fellow game enthusiast.

To answer your question: we currently sell directly wholesale (not through distributors). This means:
- Low MOQ (minimum order quantity)
- DDP (Delivered Duty Paid) shipping to your door
- Competitive pricing with healthy retail margins

I'd love to send you our product catalog with pricing. We have:
- Premium card games (strategy, party, family)
- Jigsaw puzzles (100-1000 pieces, various themes)

Would you like me to send over the catalog and price list? Happy to set up a quick Zoom call if that's easier.

Best regards,
Ian
Roktandrazo
```

---

### 🟡 中优先：Emerald City Comics（等待 follow-up）

| 字段 | 内容 |
|------|------|
| 商家 | Emerald City Comics |
| 城市 | Clearwater, FL（佛罗里达州克利尔沃特） |
| 门店类型 | 漫画店 |
| 回复人 | Chad |
| 回复时间 | 2026-06-24 19:54 EDT |
| 回复内容 | "Sorry, I am out of the office! I expect to be back on Monday, June 29th." |
| 回复分类 | 自动回复 / Auto-reply (OOO) |
| 建议动作 | **7 月 3 日后 follow-up**：重新发送产品介绍，提及之前邮件 |
| 需要报价 | 暂不需要 |
| 需要 follow-up | ✅ 7 月 3 日后 |

---

### 🟢 低优先：The Red Balloon Toy Store（等待工单处理）

| 字段 | 内容 |
|------|------|
| 商家 | The Red Balloon Toy Store |
| 城市 | 未匹配（reamaze.com 域名无法匹配 leads 表） |
| 门店类型 | 玩具店 |
| 回复时间 | 2026-06-30 10:09 |
| 回复内容 | "Thank you for your email. Our team has been notified and will review your concern as soon as possible. You should expect to hear back from us within 1 business day." |
| 回复分类 | 支持工单自动回复 |
| 建议动作 | 等待人工回复。如果 7 月 3 日前无回复，可 follow-up |
| 需要 follow-up | ⚠️ 观察中 |

---

## B. 系统可自动处理

### 退订：Atomic Empire

| 字段 | 内容 |
|------|------|
| 商家 | Atomic Empire |
| 城市 | Durham, NC（北卡罗来纳州达勒姆） |
| 邮箱 | info@atomicempire.com |
| 回复内容 | "Unsubscribe" |
| 动作 | **加入 suppression_list** |
| SQL | `INSERT INTO suppression_list (email, reason, added_at) VALUES ('info@atomicempire.com', 'unsubscribe_request', datetime('now'))` |

### 自动回复：Great Escape Adventures（系统自动回复）

| 字段 | 内容 |
|------|------|
| 商家 | Great Escape Adventures |
| 回复内容 | "Thank you for being part of the Great Escape Adventures community — a family-run board-game, hobby, and collectible shop with four community locations" |
| 动作 | 无需处理（已有 Nate 的真实回复） |

---

## C. 需要加入 suppression

| 商家 | 邮箱 | 原因 | 状态 |
|------|------|------|------|
| Atomic Empire | info@atomicempire.com | 退订请求 | 待执行 |
| Battleground Games | info@battlegroundgames.com | Hard bounce | 已在 suppression |
| Cat & Mouse Game | info@catandmousegame.com | Domain bounce | 已在 suppression |
| Madness Games | info@madnessgames.com | Hard bounce | 已在 suppression |
| Dice Dojo | info@dicedojo.com | Domain bounce | 已在 suppression |
| Game Parlour | hello@gameparlour.com | Domain bounce | 已在 suppression |
| Dragon's Lair | info@dragonslair.com | Domain bounce | 已在 suppression |
| Comicazi | shipping@comicazi.net | Hard bounce | 已在 suppression |
| Dream Wizards | laurel@dreamwizards.com | Hard bounce | 已在 suppression |

---

## D. 需要后续 follow-up

### 已发送但无回复（7 天内发送，等待中）

以下商家本周已发送，尚在等待回复窗口内（通常 3-7 天）：

| 商家 | 城市 | 州 | 发送日期 | 等待天数 | 建议动作 |
|------|------|-----|----------|----------|----------|
| Eureka Springs Gaming | Eureka Springs | AR | 07-02 | 0 | 等待 7 天 |
| Steadfast Hobbies | Hot Springs | AR | 07-02 | 0 | 等待 7 天 |
| The Deep Comics | Huntsville | AL | 07-02 | 0 | 等待 7 天 |
| Homewood Toy | Birmingham | AL | 07-02 | 0 | 等待 7 天 |
| CM Games | Knoxville | TN | 07-02 | 0 | 等待 7 天 |
| Game On Chattanooga | Chattanooga | TN | 07-02 | 0 | 等待 7 天 |
| Learning Express Franklin | Franklin | TN | 07-02 | 0 | 等待 7 天 |
| Great Rocky Mountain Toy | Bozeman | MT | 07-02 | 0 | 等待 7 天 |
| Vault of Midnight | Ann Arbor | MI | 07-01 | 1 | 等待 6 天 |
| Toys N More | Reno | NV | 07-01 | 1 | 等待 6 天 |
| Twirl Toy Store | Taos | NM | 07-01 | 1 | 等待 6 天 |
| Toy Harbor | Traverse City | MI | 07-01 | 1 | 等待 6 天 |
| Poopsies | Galena | IL | 07-01 | 1 | 等待 6 天 |
| Rocking Horse Toy | Petoskey | MI | 07-01 | 1 | 等待 6 天 |
| Old Fox Books | Annapolis | MD | 07-01 | 1 | 等待 6 天 |

### 已发送超过 7 天无回复（需 follow-up）

| 商家 | 城市 | 州 | 发送日期 | 等待天数 | 建议动作 |
|------|------|-----|----------|----------|----------|
| 多家（Phase 0-3 发送） | 各城市 | 各州 | 06-11 ~ 06-25 | 7-21 | 可考虑第二轮 follow-up 邮件 |

---

## E. 动作优先级汇总

| 优先级 | 动作 | 商家 | 截止时间 |
|--------|------|------|----------|
| 🔴 P0 | 立即回复 | Great Escape Adventures (Nate) | **今天** |
| 🟡 P1 | 加入 suppression | Atomic Empire | 今天 |
| 🟡 P1 | Follow-up | Emerald City Comics (Chad) | 7 月 3 日 |
| 🟢 P2 | 补池到 20+ | New City Lead Factory | 明天 09:00 前 |
| 🟢 P2 | 观察 | The Red Balloon | 7 月 3 日 |

---

*Report generated: 2026-07-02 14:30 GMT+8*
*IMAP scan: read-only, no state changes*
*No emails sent, no inbox modified*
