# BD DAILY OPERATIONS

**Date:** 2026-08-18
**System Freeze:** true (no system development; operations only)

| Metric | Value |
|--------|-------|
| Verified V2 Start | 11 |
| New Verified V2 (today, canonical gate-PASS) | **23**（ids 1056–1078，全部 2026-08-18 入库） |
| Sent | 1 (Canary — Game Cafe id=1055, SEND_WINDOW_OVERRIDE validation send) |
| SMTP Accepted | 1 |
| Bounce | 0 |
| Bounce Rate | 0% |
| Real Reply | 0 |
| **Verified V2 Inventory (unsent, CANONICAL worker scan)** | **32** (ET 15 / CT 9 / MT 1 / PT 7) — North Star ≥30 ✅；已排除 id=802（SEND_HOLD） |
| Queued, not yet auto-sent | **9**（FSP 174–183 中 175 已 HOLD 取消，余 9） |
| Duplicate Hold | 1（id=802 Grand Adventures = id=701 已发送，同一商户） |
| Production Bug | false（执行器暂停属平台配置，非代码 bug） |

### 今日新增 Verified V2（4 批，共 23 条，全部经正式 Canonical 门控 PASS，MX Worker 已验证）
- 早班：ids 1056–1057（2 条）The Wyvern's Tale NC / Mage's Comics IN
- 批次 a：ids 1058–1068（11 条）Village Meeple MO / MGU MO / Ye Gamer's Guild IN / Hobby Hole AL / Hobby Knights WI / Gnome Games WI / The Last Square WI / LionHeart Hobby TX / Mimic's Market PA / Drawbridge PA / The Dancing Bear Toys NC
- 批次 c：ids 1069–1073（5 条）Blue Bridge MI / Total Escape CO / The Portland Game Store OR / Time Warp NJ / Red Castle OR
- 批次 e：ids 1074–1078（5 条）The Comics Keep / Phantom Zone / Subspace / Arcane / Outsider（WA，PT）
- 拦截记录（cross_check 正确工作）：Guardian Games(id=86 sent)、Card Kingdom(id=76 delivery_issue)、Blue Highway(id=216 delivery_issue)、Game Goblins(id=412 sent)、Sci-Fi City(id=521 sent)、Grand Adventures Comics(id=701 sent)、Comic Book World(id=771 **bounced**) — 全部未重复插入

### Queued, not yet auto-sent
- **9** V2 leads 已有 Final Send Plan（FSP 174,176–183；175 已因重复商户 HOLD 取消）。
- **Auto-send executor is PAUSED** (`BD Production Outreach` automation-1785804421539, ExecutionHost未验证) → 今晚 22:00/23:00 上海不会自动飞出，需用户取消暂停或授权窗口手动发送。

### 17:00 运营复核（恢复 OPERATE THE SYSTEM）
- Canonical V2 扫描（Worker 正常）：**CAMPAIGN_ELIGIBLE_V2 = 33**（ET15/CT10/MT1/PT7，含新增 id=19 Building Blocks Toy Store），≥30 ✅
- 今日真实发送 = 1（Canary tom@playgamecafe.com），**Canary 退信 = 0**；回复 = 0
- 今日 3 条新 bounce_log（08:35 恢复扫描）为 8/14 批次已知退信的重复扫描（gigabitescafe/deepcomics/gamedaymiami，bounce_type=unresolved、无诊断码）——观察项：恢复扫描疑似缺按 lead+email 去重，仅记录不修改
- 执行器仍 PAUSED → 今晚 9 条需用户决策（取消暂停 or 授权窗口手动正式链发送）

---

### 今天发生了什么？
确认 V2 门禁 + Canonical 发信链在生产跑通（Canary 真实发出、0 退信）；按"只收集、不改系统"指令新增 4 批共 **23 条**第一方验证合格线索。**MX Worker 已恢复**，正式 Canonical 全库扫描确认未发送 Verified V2 库存 = **32**（ET 15 / CT 9 / MT 1 / PT 7，已排除 HOLD 的 id=802），≥30 目标达成。

### 有没有风险？
1. **发送执行器暂停**（平台配置问题，非代码 bug）：9 条已建计划的合格线索今晚不会自动飞出。
2. **数据重复已处理**：id=802 "Grand Adventures"（gmail）与 id=701（已发送）为同一商户（Murfreesboro TN 同一官网），已执行 SEND_HOLD——FSP 175 取消 + 抑制名单 + auto_sendable=0，不会进入任何发送计划；未改动去重逻辑。
3. 注意：id=727（Hard Knox KY）、id=814/815/839/883/923/1018、id=1053/1054 为 8/17 及更早入库，非今日新增；今日新增严格为 1056–1078 共 23 条。

### 明天最重要的一件事是什么？
恢复发送执行器（取消暂停 + 校验，或授权我在窗口手动按正式链发出这 10 条积压线索）；同时维持 Verified V2 库存 ≥30。
