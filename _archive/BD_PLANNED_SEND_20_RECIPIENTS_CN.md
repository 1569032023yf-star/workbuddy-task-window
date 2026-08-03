# 明天计划发送 20 家清单 / Planned Send 20 Recipients
## 2026-07-03

---

## 当前状态 / Current Status

| 指标 | 值 |
|------|-----|
| A0 sendable 剩余 | **10** |
| 今日已发送 | 10 |
| 需补充到 20 | **10** |
| 明天目标 | 20 |

> ⚠️ 当前 sendable_pool = 10，距离明天目标 20 还差 10。需要在明天 09:00 前完成补池。

---

## 当前可用 A0（10 家）/ Currently Available A0

| # | 商家 | 城市/州 | 门店类型 | 产品适配 | 来源 | A0 | 已排除风险 | Domain 重复 | Store 重复 | 邮箱（脱敏） | 中文说明 |
|---|------|---------|----------|----------|------|-----|-----------|-------------|------------|--------------|----------|
| 1 | Eureka Springs Gaming | Eureka Springs, AR | 游戏店 | 卡游+拼图 | New City Lead Factory | ✅ | ✅ | ❌ | ❌ | eur***@gmail.com | 阿肯色旅游城市游戏社区 |
| 2 | Steadfast Hobbies and Games | Hot Springs, AR | 桌游/卡牌店 | 卡游 | New City Lead Factory | ✅ | ✅ | ❌ | ❌ | ste***@gmail.com | 国家公园门户桌游店 |
| 3 | The Deep Comics and Games | Huntsville, AL | 漫画/游戏店 | 卡游 | Manual Search | ✅ | ✅ | ❌ | ❌ | inf***@deepcomics.com | NASA 航天城漫画游戏店 |
| 4 | Mythical Mountain | St. Augustine, FL | 漫画/游戏店 | 卡游+拼图 | Manual Search | ✅ | ✅ | ❌ | ❌ | cus***@mythicalmountain.com | 美国最古老城市游戏店 |
| 5 | Toy Temple | Tempe, AZ | 收藏品店 | 卡游 | Manual Search | ✅ | ✅ | ❌ | ❌ | inf***@thetoytemple.com | 亚利桑那州立大学城 |
| 6 | CM Games | Knoxville, TN | 游戏店 | 卡游 | Manual Search | ✅ | ✅ | ❌ | ❌ | car***@gmail.com | 田纳西大学城游戏店 |
| 7 | Game On Chattanooga | Chattanooga, TN | 游戏店 | 卡游 | Manual Search | ✅ | ✅ | ❌ | ❌ | gam***@gmail.com | 新兴科技城市游戏店 |
| 8 | Homewood Toy and Hobby | Birmingham, AL | 独立玩具店 | 拼图+卡游 | Manual Search | ✅ | ✅ | ❌ | ❌ | hwd***@bellsouth.net | 30 年老牌独立玩具店 |
| 9 | Learning Express Franklin | Franklin, TN | 独立玩具店 | 拼图+卡游 | Manual Search | ✅ | ✅ | ❌ | ❌ | nas***@learningexpress.com | 纳什维尔富人郊区 |
| 10 | Great Rocky Mountain Toy Company | Bozeman, MT | 独立玩具店 | 拼图 | Manual Search | ✅ | ✅ | ❌ | ❌ | sam***@rockymountaintoycompany.com | 黄石公园门户城市 |

---

## 需补充的 10 家（候选）/ Need to Replenish 10 More

以下为补池方向，需在明天 09:00 前完成采集和验证：

### 优先补充方向

| 优先级 | 城市 | 州 | 城市类型 | 预期门店 |
|--------|------|-----|----------|----------|
| 1 | Greenville | SC | 旅游+科技 | 独立玩具店/游戏店 |
| 2 | Savannah | GA | 经典旅游 | 礼品店/玩具店 |
| 3 | Charleston | SC | 高端旅游 | 礼品店/玩具店 |
| 4 | Lexington | KY | 大学城 | 游戏店 |
| 5 | Sedona | AZ | 灵性旅游 | 礼品店 |
| 6 | Park City | UT | 滑雪度假 | 玩具店/礼品店 |
| 7 | St. George | UT | 国家公园门户 | 玩具店 |
| 8 | Madison | WI | 大学城 | 游戏店/玩具店 |
| 9 | Burlington | VT | 大学城 | 玩具店 |
| 10 | Fort Collins | CO | 大学城 | 游戏店 |

---

## 风险检查 / Risk Check

| 检查项 | 状态 |
|--------|------|
| 全部 A0 | ✅ |
| 无 guessed_email | ✅ |
| 无 B/C/B2 | ✅ |
| 无 suppression | ✅ |
| 无 bounced | ✅ |
| 无 delivery_issue | ✅ |
| 无 Exchange/MS365 | ✅（3 个 Exchange 已排除） |
| 无重复 domain（业务域名） | ✅ |
| 无重复 store | ✅ |
| evidence_url 全部存在 | ✅ |

### 已排除的 Exchange/MS365 商家

| 商家 | 城市 | 原因 |
|------|------|------|
| Labyrinth Game Shop | Washington, DC | exchange_mx（已发送） |
| Learning Tree Toys | Prairie Village, KS | exchange_mx（已发送） |
| Museum of Science & Industry Gift Shop | Chicago, IL | exchange_mx（已发送） |

---

## 明天发送时间线 / Tomorrow Send Timeline

| 时间 | 动作 |
|------|------|
| 08:30 CST | 开始补池（如果 sendable_pool < 20） |
| 09:00 CST | Preflight check |
| 09:05 CST | Dry-run |
| 09:10 CST | Live send（20 封，2-3 分钟间隔） |
| ~10:30 CST | Send complete |
| 10:35 CST | Post-send scan（bounce/reply/unsub） |
| 10:40 CST | Inventory Recovery（补池到 30+） |

---

## 今日已发送商家（参考）/ Today's Sent Recipients (Reference)

以下 10 家今日已成功发送，明天不再重复：

| # | 商家 | 城市/州 | 门店类型 | 状态 |
|---|------|---------|----------|------|
| 1 | Labyrinth Game Shop | Washington, DC | 桌游店 | ✅ SENT |
| 2 | Learning Tree Toys | Prairie Village, KS | 独立玩具店 | ✅ SENT |
| 3 | Museum of Science & Industry Gift Shop | Chicago, IL | 博物馆礼品店 | ✅ SENT |
| 4 | Vault of Midnight | Ann Arbor, MI | 漫画/游戏店 | ✅ SENT |
| 5 | Toys N More | Reno, NV | 独立玩具店 | ✅ SENT |
| 6 | Twirl Toy Store | Taos, NM | 独立玩具店 | ✅ SENT |
| 7 | Toy Harbor | Traverse City, MI | 独立玩具店 | ✅ SENT |
| 8 | Poopsies | Galena, IL | 礼品店 | ✅ SENT |
| 9 | The Rocking Horse Toy Company | Petoskey, MI | 独立玩具店 | ✅ SENT |
| 10 | Old Fox Books | Annapolis, MD | 书店 | ✅ SENT |

---

*Report generated: 2026-07-02 13:30 GMT+8*
