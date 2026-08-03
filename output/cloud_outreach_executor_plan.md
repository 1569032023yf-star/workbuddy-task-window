# Cloud Outreach Executor Plan
## Long-term Cloud Migration Blueprint / 长期云端方案设计文档

### Objective / 目标
Move 23:00 critical send execution to cloud, eliminating dependency on HP PC power state.
将 23:00 关键发送执行迁移到云端，使发送任务不依赖 HP 电脑电源状态。

### Current Bottlenecks / 当前瓶颈
- HP ZHAN 99 Pro G9 AIO uses Modern Standby (S0); system enters Modern Standby on SC_MONITORPOWER even with Sleep=Never
- Depends on Windows SetThreadExecutionState API — not 100% reliable
- WorkBuddy Automation depends on local Python process; power loss or sleep = interruption
- SMTP uses Tencent Enterprise Mail (465/SSL); credentials must be held locally

### Recommended Architecture: Cloudflare Workers + D1 + Queue

```
Local WorkBuddy                Cloudflare Worker (Orchestrator)
  |                                  |
  | POST /send-plan ---------------->| Writes to D1
  |                                  | Enqueues to Queue
  |                                  |
  |                                  | Queue Consumer:
  |                                  | - Reads plan from D1
  |                                  | - Calls external SMTP relay
  | (Worker CANNOT use port 25)      |

  Alternative A: MailChannels (via Workers)
  Alternative B: Tencent Mail API
  Alternative C: Keep local SMTP     <-- CURRENT APPROACH
```

### Phased Migration / 分阶段迁移

**Phase 1: Read-only replica (design only, not implemented)**
- WorkBuddy still sends; cloud Worker as read-only backup
- Local DB -> D1 one-way sync

**Phase 2: Hybrid**
- WorkBuddy prepares plan; Worker executes sends
- Bi-directional sync with conflict detection

**Phase 3: Cloud-first**
- Worker leads send decisions and execution
- WorkBuddy does prep + monitoring only

### Cost Estimate (corrected 2026-07-28) / 成本估算
- Workers Free Tier: 100K requests/day
- D1 Free Tier: 5GB storage
- **Queue Free Tier: 10,000 operations/day** (corrected from 1M/month)
- Total: $0/month (within Free Tier limits)

### Critical Cloudflare Constraints / 关键约束

1. **Workers outbound TCP port 25 is PROHIBITED**
   Cloudflare Workers cannot make outbound connections on port 25.
   Must use SMTPS (465) or SMTP+STARTTLS (587).

2. **Tencent Enterprise Mail 465 must be tested from Worker**
   Do NOT assume Workers can connect to Tencent SMTP.
   Test with a real Worker -> Tencent 465 connection BEFORE migration.

3. **Switching SMTP provider has downstream impact**
   If moving from Tencent to another provider (SendGrid, Mailgun, AWS SES):
   - SPF record update: DNS propagation 24-48h
   - DKIM signature change: new key generation required
   - Deliverability impact: new IP needs warming (2-4 weeks)
   - Historical baseline reset: bounce_rate, open_rate, reputation
   - **Recommendation**: Do NOT switch SMTP provider unless necessary

4. **Cloudflare Email Routing is inbound-only**
   Cannot be used for outbound sending.

### Migration Prerequisites / 迁移前提条件

1. Local pipeline stable for 31+ days (with Delivery Guard)
2. bounce_rate < 3%
3. **Tencent Mail 465 from Worker tested and confirmed working**
4. Worker IP NOT blocked/rate-limited by Tencent
5. SPF/DKIM/DMARC fully verified with new setup

### Risk Assessment / 风险评估

| Risk | Severity | Mitigation |
|------|----------|------------|
| Worker IP blocked by SMTP provider | HIGH | Pre-test with real Worker |
| Workers CPU limit (30s) | MEDIUM | Async Queue pattern |
| D1 latency (~50ms) | LOW | Acceptable for batch sends |
| Eventual consistency with local DB | MEDIUM | Versioned plan entries |
| SPF/DKIM breakage on provider switch | HIGH | Do not switch providers |

### Immediate Decision / 当前决定

**Design only. No implementation. No SMTP provider change.**
Continue using local Delivery Guard + ES_DISPLAY_REQUIRED for send reliability.

### When to Revisit / 何时重新评估

After all of:
- Delivery Guard proven reliable (30 days)
- BIOS Power-On configured and verified
- 901 Games Pilot completed successfully
- 45-minute unattended test passed
