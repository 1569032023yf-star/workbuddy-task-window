# INVENTORY RECOVERY REPORT
## 2026-07-02

### 执行时间
- 开始：11:35 GMT+8
- 结束：11:40 GMT+8
- 模式：New City Lead Factory（Stage 3）

### 补池前状态

| 指标 | 值 |
|------|-----|
| A0 sendable | 19 |
| Gap to 20 | 1 |
| Gap to 30 | 11 |

### 补池策略

**Stage 1: Existing Pool Recovery** — 跳过（无异常）

**Stage 2: B2 Agent Pass** — 跳过（之前已扫描 50 条无邮箱）

**Stage 3: New City Lead Factory** — 执行

### 搜索方向

- 旅游小镇
- 大学城
- 国家公园门户
- 沿海小城市
- 富人郊区

### 城市覆盖

| 城市 | 州 | 新增 A0 |
|------|-----|---------|
| Hot Springs | AR | 1 (Steadfast Hobbies) |
| Eureka Springs | AR | 1 (Eureka Springs Gaming) |
| Huntsville | AL | 1 (The Deep Comics) |
| St. Augustine | FL | 1 (Mythical Mountain) |
| Tempe | AZ | 1 (Toy Temple) |
| Knoxville | TN | 1 (CM Games) |
| Chattanooga | TN | 1 (Game On) |
| Birmingham | AL | 1 (Homewood Toy) |
| Franklin | TN | 1 (Learning Express) |
| Bozeman | MT | 1 (Great Rocky Mountain Toy) |
| Annapolis | MD | 1 (Old Fox Books) |
| Petoskey | MI | 1 (Rocking Horse Toy) |
| Galena | IL | 1 (Poopsies) |
| Traverse City | MI | 1 (Toy Harbor) |
| Taos | NM | 1 (Twirl Toy Store) |
| Reno | NV | 1 (Toys N More) |
| Ann Arbor | MI | 1 (Vault of Midnight) |

### 补池后状态

| 指标 | 值 |
|------|-----|
| A0 sendable | **21** ✅ |
| Gap to 20 | 0 |
| Gap to 30 | 9 |
| 今日新增 A0 | 18 |

### 新增 A0 商家清单

| # | 商家 | 城市 | 州 | 邮箱 |
|---|------|------|-----|------|
| 1 | Steadfast Hobbies and Games | Hot Springs | AR | steadfasthobbies@gmail.com |
| 2 | Eureka Springs Gaming | Eureka Springs | AR | eurekasgaming@gmail.com |
| 3 | The Deep Comics and Games | Huntsville | AL | info@deepcomics.com |
| 4 | Mythical Mountain | St. Augustine | FL | customercare@mythicalmountain.com |
| 5 | Toy Temple | Tempe | AZ | info@thetoytemple.com |
| 6 | CM Games | Knoxville | TN | cardmonstergames@gmail.com |
| 7 | Game On Chattanooga | Chattanooga | TN | gameonchatt@gmail.com |
| 8 | Homewood Toy and Hobby | Birmingham | AL | hwdtoy@bellsouth.net |
| 9 | Learning Express Franklin | Franklin | TN | nashville@learningexpress.com |
| 10 | Great Rocky Mountain Toy Company | Bozeman | MT | sam@rockymountaintoycompany.com |
| 11 | Old Fox Books | Annapolis | MD | jinny@oldfoxbooks.com |
| 12 | The Rocking Horse Toy Company | Petoskey | MI | rockinghorsetoy@gmail.com |
| 13 | Poopsies | Galena | IL | info@poopsies.com |
| 14 | Toy Harbor | Traverse City | MI | toyharbortc@gmail.com |
| 15 | Old Fox Books | Annapolis | MD | booksrock@oldfoxbooks.com |
| 16 | Twirl Toy Store | Taos | NM | twirl@twirltaos.org |
| 17 | Toys N More | Reno | NV | webmaster@toysnmoreofreno.com |
| 18 | Vault of Midnight | Ann Arbor | MI | detroit@vaultofmidnight.com |

### 质量说明

- 全部 18 个 A0 均满足升级条件
- 官网可访问，邮箱出现在官网页面
- evidence_url 存在
- email_verified_on_official_site=true
- 不在 suppression_list
- 非 Exchange/MS365

### 结论

✅ 补池成功。sendable_pool 从 19 提升到 21，超过 20 封目标。
明天（2026-07-03）09:00 可正常执行 20 封发送。
