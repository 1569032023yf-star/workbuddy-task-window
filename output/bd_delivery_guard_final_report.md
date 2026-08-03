# BD Delivery Guard — 电源与执行保障系统 最终报告
# BD Delivery Guard — Power & Execution Guarantee System Final Report

**Date/日期**: 2026-07-28
**HP Model/型号**: HP ZHAN 99 Pro 23.8 inch G9 All-in-One Desktop PC
**Windows**: Windows 11 Home (Build 26200)
**BIOS**: U13 Ver. 02.22.01 (2026-05-14)

---

## 1. Exact HP Model / HP 准确型号

**HP ZHAN 99 Pro 23.8 inch G9 All-in-One Desktop PC**
- Product Number: 69C00PC#AB2
- BaseBoard: HP 8958
- BIOS Serial: 8CN***WDQ

---

## 2. Windows Sleep Model / Windows睡眠模型

**Modern Standby (S0 Low Power Idle) / 新型待机 (S0 低电量待机)**

Available states/可用状态:
- Standby (S0 Low Power Idle) Connected ✓
- Hibernate ✓
- Fast Startup ✓

NOT available/不可用: S1, S2, S3, Hybrid Sleep

---

## 3. Modern Standby Exists / Modern Standby是否存在

**YES / 是**

System uses Modern Standby (新型待机), NOT traditional S3 sleep.

---

## 4. State After Screen Off / 关屏后实际进入的状态

**Modern Standby (S0 Low Power Idle) — CRITICAL FINDING / 关键发现**

Event logs show repeated patterns within the last 24 hours:
事件日志显示过去 24 小时内反复出现的模式:

| Time | Event | Trigger |
|------|-------|---------|
| ~10 min after screen off | 506 - Entering Modern Standby | SC_MONITORPOWER |
| Immediately after | 566 - Session transition | SleepButton |
| On mouse/keyboard | 507 - Exiting Modern Standby | Input Mouse/Keyboard |

**The system enters Modern Standby whenever the display turns off**, even though "Sleep after = Never" is set in the visible power plan. This is the hidden "System unattended sleep timeout" behavior of Modern Standby systems.

**系统在显示器关闭时即进入 Modern Standby**，即使可见电源计划中 "Sleep = Never"。这是 Modern Standby 系统隐藏的 "System unattended sleep timeout" 行为。

---

## 5. Recent Sleep Trigger Sources / 最近睡眠触发源

| Trigger / 触发源 | Frequency / 频率 |
|------------------|-------------------|
| SC_MONITORPOWER (screen timeout) | Very High / 极高 — every screen off |
| Idle Timeout | High / 高 |
| 16777220 (system internal) | Medium / 中 — overnight hours |
| Power Button | Low / 低 — user initiated |
| SessionUnlock | Low / 低 |

---

## 6. HP Presence Features Status / HP Presence功能状态

| Feature / 功能 | Installed / 安装 | Running / 运行 | Risk / 风险 |
|----------------|-------------------|----------------|-------------|
| HP Auto Lock and Awake | No | — | None |
| HP Presence Aware | No | — | None |
| HP Command Center | No | — | None |
| HP GlamCam | No | — | None |
| HP Display Control | No | — | None |
| HP System Event Utility | No | — | None |

**Verdict / 结论**: No HP Presence features installed. Sleep entry is purely from Windows Modern Standby, not HP-specific features.

---

## 7. Delivery Guard Status / Delivery Guard状态

| Item / 项目 | Status / 状态 |
|-------------|---------------|
| bd_delivery_guard.py | ✅ Created / 已创建 |
| start_bd_delivery_guard.cmd | ✅ Created |
| stop_bd_delivery_guard.cmd | ✅ Created |
| status_bd_delivery_guard.cmd | ✅ Created |
| Single instance lock | ✅ File lock + PID file |
| Heartbeat (30s) | ✅ |
| Crash restart | ✅ (Poller auto-restart once) |
| Time jump detection | ✅ |
| AC power monitoring | ✅ |
| Status JSON | ✅ output/bd_delivery_guard_status.json |
| Log file | ✅ output/bd_delivery_guard.log |

---

## 8. System Required Status / System Required状态

| Window / 窗口 | Time / 时间 | ES_SYSTEM_REQUIRED |
|---------------|-------------|-------------------|
| Normal / 正常 | 14:45–00:35 CST | ✅ Active |
| Critical / 关键 | 22:15–23:20 CST | ✅ Active |
| Outside / 窗口外 | 00:35–14:45 CST | ❌ Released |

---

## 9. Display Required Status / Display Required状态

| Window / 窗口 | Time / 时间 | ES_DISPLAY_REQUIRED |
|---------------|-------------|-------------------|
| Normal / 正常 | 14:45–00:35 CST | ❌ Not required |
| Critical / 关键 | 22:15–23:20 CST | ✅ Active + dimmed to 5% |
| Outside / 窗口外 | 00:35–14:45 CST | ❌ Released |

---

## 10. 45-Minute Test Results / 45分钟测试结果

**STATUS: PENDING / 待执行**

The screen-off failure test requires 45 minutes of unattended runtime with no user input. This test should be run AFTER Delivery Guard is started to verify:
关屏故障测试需要 45 分钟无人操作运行，应在 Delivery Guard 启动后执行以验证:

- System does not enter Sleep
- Guard heartbeat uninterrupted
- Ops Center accessible
- Poller continues running
- Worker sync maintains HTTP 200
- Dry-run executes on schedule
- Database zero writes

**RECOMMENDATION**: Critical window (22:15-23:20) should PERMANENTLY use ES_DISPLAY_REQUIRED with minimum brightness, regardless of test results. This is the safest approach for Modern Standby systems.

**建议**: 关键窗口 (22:15-23:20) 应永久使用 ES_DISPLAY_REQUIRED + 最低亮度，无论测试结果如何。对于 Modern Standby 系统这是最安全的方式。

---

## 11. BIOS Power-On Supported / BIOS Power-On是否支持

**YES / 支持** ✅

HP WMI enumeration reveals:
HP WMI 枚举显示:

| Setting / 设置 | Current Value / 当前值 | Configurable / 可配置 |
|----------------|------------------------|----------------------|
| BIOS Power-On Hour | 0 (disabled) | ✅ Yes |
| BIOS Power-On Minute | 0 (disabled) | ✅ Yes |
| Sunday–Saturday | Disable (all days) | ✅ Yes (each day) |
| After Power Loss | Power Off | ✅ Yes |
| Wake On LAN | Boot to Hard Drive | ✅ Yes |
| Power On from Keyboard Ports | Disable | ✅ Yes |

---

## 12. BIOS Auto Power-On Configured / BIOS自动开机是否配置

**NOT YET / 尚未配置** ⚠️

HP WMI allows reading and writing these settings, but the user's instruction specifies:
HP WMI 允许读写这些设置，但用户的指示是:

> "如果BIOS设置必须由用户在F10界面确认：只输出一个一次性操作说明"
> "不得绕过BIOS密码，不得清除BIOS密码，不得刷BIOS"

**Recommended F10 BIOS Configuration / 推荐F10 BIOS设置**:

进入 BIOS Setup (F10 at boot) → Advanced → Boot Options:
1. Set `BIOS Power-On Hour` = 14
2. Set `BIOS Power-On Minute` = 40
3. Enable `Sunday`, `Monday`, `Tuesday`, `Wednesday`, `Thursday`, `Friday`, `Saturday`
4. Set `After Power Loss` = `Power On` or `Previous State`

This ensures the system powers on at 14:40 CST daily — before the 14:45 Delivery Guard normal window and the 15:00 Inventory automation.

这确保系统每天 14:40 CST 开机 — 在 14:45 Delivery Guard 正常窗口和 15:00 Inventory 自动化之前。

---

## 13. Power On after AC Loss Status / Power On after AC Loss状态

| Current / 当前 | Recommended / 推荐 |
|----------------|-------------------|
| **Power Off** (default) | **Power On** or **Previous State** |

Current setting means: power outage → system stays off until manual power-on.
当前设置意味着: 断电 → 系统保持关闭直到手动开机。

This is a single point of failure. Recommend changing to "Previous State" to restore pre-outage state, or "Power On" for guaranteed restart.
这是一个单点故障。建议改为 "Previous State" 恢复断电前状态，或 "Power On" 保证重启。

---

## 14. Ops Center Running Continuously / Ops Center是否持续运行

Poller integration updated:
- start_bd_ops_center.cmd now also starts Delivery Guard
- Poller now checks Delivery Guard health every 60 seconds
- Auto-restart guard once if dead (not repeatedly)

---

## 15. Poller Running Continuously / Poller是否持续运行

bd_ops_poller.py updated with:
- New `poll_delivery_guard()` function
- 60-second guard health check cycle
- Automatic guard restart (max 1 attempt)
- Heartbeat freshness check (120s threshold)

---

## 16. Dry-run Executed on Schedule / dry-run是否按时执行

**PENDING / 待测试**

The 45-minute screen-off test will include a scheduled dry-run verification.

---

## 17. Database Zero Writes / 数据库是否零写入

**CONFIRMED / 已确认** — Delivery Guard never touches the database.
Delivery Guard never accesses customer data. NEVER writes to final_send_plan.
The only files written are: status JSON, log file, PID file, lock file.

---

## 18. SMTP Called / 是否调用SMTP

**NO / 否** ✅

Delivery Guard is purely a Windows power management utility. It:
- Does NOT import any email libraries
- Does NOT access SMTP credentials
- Does NOT access IMAP credentials
- Does NOT access Cloudflare tokens
- Does NOT send any network requests (except Ops Center health probes via Poller)

---

## 19. Auto-Enable Pre-Send/Outreach Conditions / 自动启用Pre-Send/Outreach条件

Current status / 当前状态:

| Automation / 自动化 | Time / 时间 | Status / 状态 |
|---------------------|-------------|---------------|
| Pre-Send | 22:30 CST | PAUSED (Pilot control) |
| Outreach | 23:00 CST | PAUSED (Pilot control) |
| Post-Send | 00:10 CST | PAUSED |
| End-of-Day | 00:25 CST | Not deployed |

**Conditions to auto-enable / 自动启用条件**:
1. ✅ Delivery Guard code ready
2. ⏳ 45-minute screen-off test PASSED
3. ⏳ BIOS Power-On configured (F10 manual step)
4. ⏳ Power settings hardened (Sleep=Never verified persists)
5. ⏳ After Power Loss = Previous State or Power On

**Cannot auto-enable until item 2 passes.**

---

## 20. Remaining Single Points of Failure / 仍有哪些单点故障

| # | Failure Point / 故障点 | Severity / 严重性 | Mitigation / 缓解措施 |
|---|----------------------|-------------------|----------------------|
| 1 | **Power outage** | HIGH | BIOS After Power Loss → Power On (requires F10) |
| 2 | **Windows crash/BSOD** | MEDIUM | BIOS scheduled power-on at 14:40 daily |
| 3 | **Modern Standby bypassing ES_SYSTEM_REQUIRED** | HIGH | ES_DISPLAY_REQUIRED in critical window |
| 4 | **Astrill VPN failure** | MEDIUM | Worker uses Cloudflare (direct), not VPN-dependent |
| 5 | **WorkBuddy process crash** | MEDIUM | Poller auto-restart; BIOS power-on as cold restart |
| 6 | **Network outage** | LOW | Tasks will queue; Network Guard detects and alerts |
| 7 | **SMTP provider rate limit** | LOW | Daily cap of 20 emails well below limits |
| 8 | **Disk full** | LOW | Log rotation needed (future enhancement) |

---

## Deliverables / 交付物

| File / 文件 | Description / 描述 |
|-------------|-------------------|
| `roktandrazo-outreach/bd_delivery_guard.py` | Core guard daemon / 核心守护进程 |
| `roktandrazo-outreach/start_bd_delivery_guard.cmd` | Start script / 启动脚本 |
| `roktandrazo-outreach/stop_bd_delivery_guard.cmd` | Stop script / 停止脚本 |
| `roktandrazo-outreach/status_bd_delivery_guard.cmd` | Status script / 状态脚本 |
| `roktandrazo-outreach/restore_original_power_settings.cmd` | Power restore / 电源恢复 |
| `output/power_diagnostics/original_power_scheme_backup.pow` | Power scheme backup / 电源计划备份 |
| `output/power_diagnostics/*.txt` | Diagnostic reports / 诊断报告 |
| `output/cloud_outreach_executor_plan.md` | Cloud migration plan / 云端方案 |
| `roktandrazo-outreach/bd_ops_poller.py` | Updated with guard check / 新增守护检查 |
| `roktandrazo-outreach/start_bd_ops_center.cmd` | Updated to start guard / 更新为同时启动守护 |
| `output/power_diagnostics/bios_power_values.txt` | BIOS power settings dump / BIOS电源设置导出 |

---

## Next Steps / 下一步

1. **User REQUIRED / 需用户操作**: Enter BIOS F10 to configure Power-On schedule and After Power Loss
2. **User**: Start Delivery Guard (`start_bd_delivery_guard.cmd`)
3. **Test**: Run 45-minute screen-off test
4. **If test passes**: Auto-enable Pre-Send, Outreach, Post-Send, End-of-Day automations
5. **If test fails**: Critical window permanently uses ES_DISPLAY_REQUIRED

---

## Success Criteria / 成功标准

| Criteria / 标准 | Status / 状态 |
|-----------------|---------------|
| 屏幕关闭时系统不休眠 | ⏳ Requires Delivery Guard running |
| Delivery Guard 持续心跳 | ⏳ Requires Delivery Guard running |
| Ops Center 与 Poller 持续运行 | ✅ Ready (updated code) |
| BIOS Power-On 可用并完成固件兜底 | ⚠️ Requires F10 configuration |
| 发送任务不依赖用户手动保持屏幕活动 | ⏳ Requires 45-min test pass |

---
*Generated by WorkBuddy BD Delivery Guard System 2026-07-28*
