# City Outreach 40 Handoff / 城市外联 40 交接

## Scope and Recovery / 范围与回滚

- Git: this directory is **not** a Git repository. / Git：该目录**不是** Git 仓库。
- File-level backup: `C:\Users\15690\Documents\线下BD 3\backups\roktandrazo-outreach-pre-city-outreach-40-20260723-144527`.
  / 文件级备份路径如上。
- Code rollback: replace each changed file from that backup. / 代码回滚：从该备份逐个还原变更文件。
- Database rollback: restore the pre-migration database backup made by WorkBuddy before running the migration; this Codex run did not modify the production database.
  / 数据库回滚：使用 WorkBuddy 在迁移前制作的数据库备份；本轮 Codex 未修改生产数据库。

## Confirmed Call Chain / 已确认调用链

Static source evidence: `install_windows_tasks.ps1` defines scheduled actions as:

`WorkBuddy Automation -> python bd_orchestrator.py --stage <stage> --live -> Final Send Plan -> daily_session.execute_final_send_plan -> bd_sender.send_one -> SMTP -> send_log`

`bd_sender.py` is now the sole successful-send `send_log` writer. The old duplicated `log_send()` calls remain in unreachable legacy code inside `stage_outreach`; the active path returns before that block.

The live external Task Scheduler/WorkBuddy Automation configuration could not be read in this environment (`Get-ScheduledTask` returned no usable task data). WorkBuddy must confirm it is actually updated to the commands below. / 本环境无法读取外部任务计划程序的有效配置；WorkBuddy 必须确认已实际更新为以下命令。

## Changed Files / 修改文件

- `outreach_control.py`: Shanghai 23:00 batch-date rules, 40/5 limits, 120/80/40 inventory thresholds, 45–85 second delay bounds, 23:59:30 SMTP cutoff, Strict A0 predicate, and the 20-family city query matrix.
  / 上海批次日期、40/5 限额、120/80/40 库存阈值、延迟与截止时间、Strict A0 和城市检索矩阵。
- `final_send_plan.py`: persists immutable plan entries with all required audit fields.
  / 持久化不可变 Final Send Plan。
- `daily_session.py`: adds plan-only execution; skipped entries are not refilled from candidates.
  / 增加只消费计划的发送执行；跳过项不会从候选库补位。
- `bd_sender.py`, `bd_db.py`: require plan metadata for live sends and write one typed, batch-dated send-log entry per SMTP success.
  / 真实发送必须带计划元数据；每次 SMTP 成功只写一条带类型和批次日期的日志。
- `bd_orchestrator.py`: adds `pre-send`, uses 23:00–23:59:30 Asia/Shanghai, consumes plans only, uses inventory target 120, and locks Inventory to one active city.
  / 新增 pre-send，改为上海 23:00 窗口及只消费计划，库存目标 120，Inventory 锁定单一活动城市。
- `retail_city_queue.py` and migration: persistent one-active-city queue, cursor/checkpoint/resume API, Nashville-first TN -> AR -> KY seed order.
  / 持久化单城市队列、游标/检查点/恢复接口，默认 Nashville 起始并按 TN -> AR -> KY。
- `bd_operations_dashboard.py`: counts only `status='sent' AND message_type='new_outreach'` for the 40 target; Follow-up is separate; exposes `post_send_state='stage_not_run'` when applicable.
  / 仪表盘按新开发口径统计 40，Follow-up 独立，并能区分 post-send 未运行。
- `install_windows_tasks.ps1`: documents the five intended schedules.
  / 更新五个预期调度时间。
- `tests/test_city_outreach_40.py`: 15 non-production tests.
  / 15 个不触碰生产状态的测试。

## Migration / 数据库迁移

Migration script: `migrations\migrate_city_outreach_40.py`.

Use the same Python executable that WorkBuddy Automation uses:

```powershell
$py = 'C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe'
$db = 'C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach\data\bd_leads.db'
& $py migrations\migrate_city_outreach_40.py --db $db --check
```

Formal migration / 正式迁移：

```powershell
& $py migrations\migrate_city_outreach_40.py --db $db
```

Post-migration read-only verification / 迁移后只读验证：

```powershell
& $py migrations\migrate_city_outreach_40.py --db $db --check
```

The migration is transactional and idempotent. It adds `send_log.message_type`, `outreach_batch_date`, `plan_entry_id`, `final_send_plan`, and `retail_city_queue`; it does not alter historical `send_log` rows or delete legacy search state. It was run twice successfully against a copied production database, never against the original.

迁移使用事务且可重复执行。它不改写历史 `send_log`，不删除旧检索状态；已在生产库副本上成功连续演练两次，未在原库执行。

## Required Automation / 必须修改的 Automation

All times are Asia/Shanghai. WorkBuddy must update real task triggers; do **not** run `install_windows_tasks.ps1` until the migration and acceptance checks pass.

| Time | Task | Exact command |
|---|---|---|
| 15:00 | Inventory | `& $py bd_orchestrator.py --stage inventory --live` |
| 22:30 | Pre-Send | `& $py bd_orchestrator.py --stage pre-send --live` |
| 23:00 | Outreach | `& $py bd_orchestrator.py --stage outreach --live` |
| 00:10 | Post-Send | `& $py bd_orchestrator.py --stage post-send --live` |
| 00:25 | End-of-Day | `& $py bd_orchestrator.py --stage end-of-day --live` |

## WorkBuddy Run Order / WorkBuddy 严格执行顺序

1. Make a recoverable copy of `data\bd_leads.db` and record its path. / 先备份并记录生产数据库。
2. Run pre-check, migration, then post-check above. / 执行迁移前检查、迁移、迁移后检查。
3. Run only read-only acceptance SQL or the supplied check command; confirm the new columns/tables and only one active city. / 只读验收新字段、新表和单一 active city。
4. At 15:00 run Inventory once. It must report Nashville, TN as the active city unless an existing city was paused; it must not switch city automatically. / 15:00 首次运行 Inventory，确认城市恢复逻辑。
5. At 22:30 run Pre-Send and verify `final_send_plan` contains only Strict A0 New Outreach (up to 40) plus Follow-up (up to 5). / 22:30 生成并验收计划。
6. At 23:00 run Outreach. Do not run it without a plan. / 23:00 仅在计划存在时执行 Outreach。
7. At 00:10 and 00:25 run Post-Send and End-of-Day; both must retain the previous night’s `outreach_batch_date`. / 跨零点阶段仍归属上一晚批次。

## Risks and Acceptance Boundaries / 风险与验收边界

- The external scheduler was not readable here, so real trigger replacement remains a WorkBuddy task.
  / 外部调度未能读取，真实触发时间替换仍由 WorkBuddy 完成。
- The existing Inventory implementation enriches already-stored candidates; the queue now prevents city switching, but source-specific search execution and pagination workers still need WorkBuddy runtime validation.
  / 现有 Inventory 主要处理已有候选；队列已阻止切城，但各来源搜索与分页仍需 WorkBuddy 运行验收。
- Existing historical send logs have null `message_type` and `outreach_batch_date`; they are intentionally not backfilled, so new 40-target reporting begins after the migration.
  / 历史日志不回填新字段，因此新的 40 口径从迁移后开始。
- No SMTP connection, customer email, production DB migration, Inventory run, daemon, suppression/bounce/reply update, or WorkBuddy Automation change was executed by Codex.
  / Codex 未执行 SMTP、真实邮件、生产迁移、Inventory、daemon、状态更新或 Automation 改动。

## Manual Review Convergence / 人工审核通道收敛

### Implemented Code / 已修改代码

- `bd_review_server.py` and `bd_review_cli.py` now use the single database workflow in `review_workflow.py`.
  / `bd_review_server.py` 与 `bd_review_cli.py` 现共用 `review_workflow.py` 的单一数据库工作流。
- `approve_auto` reruns the production adapter and full Strict A0 Lead Hygiene gate. It only marks an eligible lead as `auto_sendable=1`; it does not create a Final Send Plan or send email.
  / `approve_auto` 会重新执行生产适配器与完整 Strict A0 Lead Hygiene 门禁；仅标记合格线索为 `auto_sendable=1`，不会创建 Final Send Plan 或发送邮件。
- `approve_manual` creates/updates `manual_send_queue` and sets `manual_sendable=1`; automatic candidate retrieval excludes this queue entirely.
  / `approve_manual` 创建/更新 `manual_send_queue` 并设置 `manual_sendable=1`；自动候选检索已完全排除该队列。
- Contact Form / Custom C cannot be approved for either automatic or manual email. Recheck Official Site, Recheck Facebook, Defer, and Reject remain available.
  / Contact Form / Custom C 不能批准自动或手动邮件；仍可执行官网复核、Facebook 复核、延期和拒绝。
- Reject requires a reason and persists status plus audit trail. Defer requires `next_review_at` and a reason. Rechecks are recorded as low-priority pending rechecks; they do not perform web requests from the review UI.
  / 拒绝必须填写原因并持久化状态和审计记录。延期必须填写 `next_review_at` 与原因。复核会记录为待复核，不会由审核 UI 发起网页请求。
- Every action writes `review_log` with lead ID, previous/new status, action, reviewer, time, reason, evidence URL, hygiene result, source channel, and auto/manual sendability flags.
  / 每次操作都会写入 `review_log`，包含 lead ID、前后状态、操作、审核人、时间、原因、证据 URL、Hygiene 结果、来源通道及自动/手动可发送标记。
- Dashboard manual-review cards read persisted `leads` and `review_log` data, including pending, B1, B2, contact form, recovery, deferred, approvals, rejected, recheck pending, reviewed today, and newly produced Strict A0.
  / Dashboard 人工审核卡片从持久化的 `leads` 和 `review_log` 读取待审、B1、B2、Contact Form、Recovery、延期、批准、拒绝、待复核、今日审核和审核后新增 Strict A0。

### Verified Existing Relationships / 已核验真实调用关系

1. `bd_review_server.py` reads `leads`, `review_log`, and `fb_enrichment_queue`; action writes now go through the shared workflow. / 网页读取 `leads`、`review_log` 和 `fb_enrichment_queue`；写操作现经由共享工作流。
2. `bd_review_cli.py` uses the same workflow and database rules as the webpage. / CLI 与网页使用相同工作流和数据库规则。
3. The old direct `grade=A0/status=new` bypass in both web and CLI approval handlers has been removed. / 网页和 CLI 原有直接改为 `A0/new` 的绕过路径已移除。
4. Approval reruns strict hygiene; suppression, hard-bounce, already-sent, duplicate, evidence, official-site, social-only, and contact-form gates are enforced. / 批准会重跑严格 Hygiene，执行 suppression、硬退信、已发送、重复、证据、官网、社交唯一和联系表单门禁。
5. Post-review automatic delivery still requires immutable `final_send_plan`; approval itself cannot enter SMTP. / 审核后自动发送仍需要不可变 `final_send_plan`；批准本身不能进入 SMTP。

### Verification Performed / 已执行验证

- Static compilation passed for review server, CLI, workflow, dashboard, migration, and Final Send Plan modules. / 审核服务器、CLI、工作流、Dashboard、迁移和 Final Send Plan 已通过静态编译。
- Temporary SQLite tests: 12 manual-review cases plus 15 City Outreach cases passed (`27/27`). No SMTP, network, server, or production DB was used. / 临时 SQLite 测试：12 项人工审核加 15 项 City Outreach，`27/27` 通过；未使用 SMTP、网络、服务器或生产数据库。
- The migration ran twice successfully against `C:\Users\15690\Documents\线下BD 3\migration-test\bd_leads_review_copy.db`, a disposable copy of the production DB. / 迁移已在生产库的一次性副本 `C:\Users\15690\Documents\线下BD 3\migration-test\bd_leads_review_copy.db` 上连续成功执行两次。

### Production Acceptance Still Required / 尚待生产验收

1. WorkBuddy must back up and migrate the real database, then start the existing local review server and inspect its buttons. / WorkBuddy 必须备份并迁移真实数据库，然后启动既有本地审核服务器并检查按钮。
2. Use test leads to verify each action and query `review_log`, `manual_send_queue`, and `final_send_plan`. / 使用测试线索验证每个操作，并查询 `review_log`、`manual_send_queue` 和 `final_send_plan`。
3. Confirm the real scheduler cannot consume `approved_manual_send`; it must only consume immutable Final Send Plan entries. / 确认真实调度不能消费 `approved_manual_send`，只能消费不可变 Final Send Plan 条目。
4. Production review-page acceptance was not performed by Codex because the server was not started and no production records were touched. / Codex 未启动服务器且未操作生产记录，因此尚未完成生产审核页面验收。

## Historical Cross-Check and Manual Official Email / 历史交叉验证与人工补充官方邮箱

### Flow / 流程

- New leads passing through `bd_db.insert_lead` and `agent_lead_collector.py` now call `history_crosscheck.py` before insertion. It distinguishes exact-email/identity matches, historical send, hard bounce, suppression, reply, and review state. A matched candidate is not inserted as a second sender; the existing lead receives a history-check note and refreshed check time.
  / 经过 `bd_db.insert_lead` 和 `agent_lead_collector.py` 的新线索会先调用 `history_crosscheck.py`。它区分精确邮箱/身份匹配、历史发送、硬退信、抑制、回复和审核状态。命中历史时不会新增第二个发送对象，而是更新既有线索的核验时间和历史标记。
- The existing review page has an `Email` action per lead. The modal accepts email, evidence URL, evidence snippet, evidence method, contact role, and notes; it posts to `/api/manual-email`.
  / 既有审核页面每条线索新增 `Email` 操作。弹窗接收邮箱、证据 URL、证据片段、证据方法、联系人角色和备注，并提交至 `/api/manual-email`。
- The submitted email is normalized as exactly one lowercase RFC-style address. It is then checked against leads, send, bounce, reply, suppression, review, and related identity records before any promotion.
  / 提交邮箱会规范化为单个小写 RFC 风格地址，然后与 leads、发送、退信、回复、抑制、审核和关联身份记录交叉检查，之后才可能升级。
- Promotion requires same official host, fetched official page containing both the email and supplied snippet, allowed evidence method, and full Strict A0 Hygiene. Missing/unreachable evidence remains `pending_official_verification`; it cannot become A0.
  / 升级要求证据 URL 与官网同主机、抓取的官网页面同时包含邮箱与所填片段、证据方法合法且完整 Strict A0 Hygiene 通过。证据缺失或不可访问时保持 `pending_official_verification`，不能成为 A0。
- The previous address is stored in `lead_email_history`; every submission and final result is stored in `manual_email_submission` and `review_log`. No email is physically deleted.
  / 原邮箱会保存于 `lead_email_history`；每次提交和最终结果写入 `manual_email_submission` 与 `review_log`。不会物理删除邮箱。

### Migration / 迁移

The existing idempotent migration now creates `lead_email_history` and `manual_email_submission`, and adds `leads.evidence_method` and `primary_outreach_email` when absent. WorkBuddy must run it only on a backed-up production database; Codex did not run it on production.

现有幂等迁移现会创建 `lead_email_history` 与 `manual_email_submission`，并在缺失时添加 `leads.evidence_method` 和 `primary_outreach_email`。WorkBuddy 只能在已备份的生产数据库上执行；Codex 未对生产库执行迁移。

### Verification / 验证

Temporary SQLite tests passed: official Contact Form email may be promoted only with verified official-page evidence; previously sent, suppressed, and hard-bounced emails are blocked; missing evidence cannot promote; old email is preserved and audited. Combined regression: `32/32` passed, with no server startup, network request, production DB write, or email send.

临时 SQLite 测试通过：Contact Form 的官方邮箱仅在官网页面证据验证后可升级；历史已发、抑制和硬退信邮箱会被拦截；缺失证据不能升级；旧邮箱会保留并审计。合并回归 `32/32` 通过，未启动服务器、未访问网络、未写生产库、未发邮件。

## Single-City Discovery Collector / 单城市线索采集器

### Implemented Architecture / 已实现架构

- Added provider-neutral discovery modules under `discovery/`: `models.py`, `normalizer.py`, `discovery_service.py`, and providers `google_places.py`, `serpapi_maps.py`, and `mock_provider.py`.
  / 新增 provider 中立的 `discovery/` 模块：`models.py`、`normalizer.py`、`discovery_service.py`，以及 `google_places.py`、`serpapi_maps.py`、`mock_provider.py`。
- `stage_inventory()` now runs Lane A New Place Discovery for the active city before the existing website/email recovery lane. The old lane is preserved, but official-site email upgrades now call `manual_email_workflow.submit_manual_email()` instead of directly setting A0 fields.
  / `stage_inventory()` 现在会先对 active city 执行 Lane A 新商家发现，然后保留既有官网/邮箱恢复 Lane。旧 Lane 未删除，但官网邮箱升级已改为调用 `manual_email_workflow.submit_manual_email()`，不再直接改 A0 字段。
- New discovery results first enter `lead_discovery_results`; repeated hits are stored in `lead_discovery_hits`; provider calls are written to `provider_request_audit`; per-query cursor and counters are stored in `lead_discovery_query_state` and mirrored to `retail_city_queue`.
  / 新发现结果先进入 `lead_discovery_results`；重复命中记录在 `lead_discovery_hits`；provider 请求写入 `provider_request_audit`；每个 query 的 cursor 与计数写入 `lead_discovery_query_state` 并同步到 `retail_city_queue`。
- Lead creation is allowed only after suitability, website/email evidence when present, and `history_crosscheck.cross_check()`. The only write path for new leads is `bd_db.insert_lead()`.
  / 只有完成适配性、官网/邮箱证据和 `history_crosscheck.cross_check()` 后才允许创建 lead。新 lead 唯一写入路径是 `bd_db.insert_lead()`。

### Provider Configuration / Provider 配置

- Default provider is `google_places`. Set `GOOGLE_MAPS_API_KEY` for real Google Places Text Search. Missing key returns `provider_not_configured`; it does not scrape uncontrolled web pages and does not mark the query completed.
  / 默认 provider 是 `google_places`。真实 Google Places Text Search 需要设置 `GOOGLE_MAPS_API_KEY`。缺少 Key 时返回 `provider_not_configured`，不会抓取非受控网页，也不会把 query 标记为完成。
- Optional provider: `serpapi_maps`, selected with `WORKBUDDY_DISCOVERY_PROVIDER=serpapi_maps` and `SERPAPI_API_KEY`. It uses the same normalized output model.
  / 可选 provider：`serpapi_maps`，通过 `WORKBUDDY_DISCOVERY_PROVIDER=serpapi_maps` 与 `SERPAPI_API_KEY` 启用，输出同一标准模型。
- Offline test provider: `WORKBUDDY_DISCOVERY_PROVIDER=mock`. This is the only provider used by Codex tests.
  / 离线测试 provider：`WORKBUDDY_DISCOVERY_PROVIDER=mock`。Codex 测试只使用该 provider。
- Limit one Inventory discovery batch with `WORKBUDDY_DISCOVERY_MAX_PAGES=1` for a controlled Nashville smoke run.
  / 可用 `WORKBUDDY_DISCOVERY_MAX_PAGES=1` 将 Inventory discovery 限制为一个分页批次，用于 Nashville 受控冒烟测试。

### Migration / 迁移

The idempotent migration now adds:

幂等迁移现新增：

- `lead_discovery_results`
- `lead_discovery_hits`
- `lead_discovery_query_state`
- `provider_request_audit`
- `city_discovery_reports`
- discovery checkpoint columns on `retail_city_queue`
- address/phone location columns on `leads` to avoid globally blocking different locations under the same domain

WorkBuddy must run migration only after backing up production DB. Codex generated and tested the migration on temporary databases only.

WorkBuddy 必须先备份生产数据库，再执行迁移。Codex 只在临时数据库上生成并测试迁移。

### Nashville One-Query Smoke / Nashville 单查询冒烟

After migration and with a real key configured, WorkBuddy can run one Inventory discovery batch:

完成迁移并配置真实 Key 后，WorkBuddy 可运行一个 Inventory discovery 批次：

```powershell
$env:WORKBUDDY_DISCOVERY_PROVIDER='google_places'
$env:GOOGLE_MAPS_API_KEY='<configured outside source code>'
$env:WORKBUDDY_DISCOVERY_MAX_PAGES='1'
& $py bd_orchestrator.py --stage inventory --live
```

Check staging without touching send pools:

只读检查 staging，不触碰发送池：

```sql
SELECT provider, query_family, business_name, validation_status, history_crosscheck_result, linked_lead_id
FROM lead_discovery_results
WHERE active_city_id = (SELECT id FROM retail_city_queue WHERE city='Nashville' AND state='TN')
ORDER BY id DESC
LIMIT 25;

SELECT active_query_family, active_provider, page_cursor, pages_processed, results_seen,
       new_unique_places, duplicate_places, provider_errors, resume_state
FROM retail_city_queue
WHERE city='Nashville' AND state='TN';
```

Confirm no send-pool write happened:

确认没有写入发送池：

```sql
SELECT COUNT(*) FROM final_send_plan WHERE created_at >= datetime('now','-1 hour');
SELECT COUNT(*) FROM send_log WHERE sent_at >= datetime('now','-1 hour');
```

### Legacy Entry Guard / 旧入口保护

`db.py`, `phase1_db.py`, `new_lead_factory.py`, `recovery_replay.py`, `push_to_30.py`, `scale_to_30.py`, `scale_brand_insert.py`, and `brand_candidate_importer.py` no longer independently insert leads; they route new candidates through `bd_db.insert_lead()` where applicable.

`db.py`、`phase1_db.py`、`new_lead_factory.py`、`recovery_replay.py`、`push_to_30.py`、`scale_to_30.py`、`scale_brand_insert.py` 与 `brand_candidate_importer.py` 已不再独立插入 lead；可运行入口会转到 `bd_db.insert_lead()`。

Deprecated one-off imports `import_phase2.py`, `import_phase3.py`, `import_phase4.py`, `import_phase4_b2.py`, `import_phase4_b3.py`, and `import_phase4_b4.py` now require `WORKBUDDY_ALLOW_LEGACY_LEAD_INSERT=YES_I_UNDERSTAND_HISTORY_BYPASS`. They remain archival scripts, not production discovery paths.

一次性历史导入 `import_phase2.py`、`import_phase3.py`、`import_phase4.py`、`import_phase4_b2.py`、`import_phase4_b3.py` 与 `import_phase4_b4.py` 现在必须设置 `WORKBUDDY_ALLOW_LEGACY_LEAD_INSERT=YES_I_UNDERSTAND_HISTORY_BYPASS` 才能运行。它们仅作为归档脚本保留，不是生产 discovery 路径。

### Verification / 验证

- Static compilation passed for discovery modules, providers, migration, city queue, orchestrator, DB, and new tests.
  / discovery 模块、provider、迁移、城市队列、编排器、数据库入口和新测试均通过静态编译。
- Temporary SQLite + Mock Provider regression passed: `44/44`.
  / 临时 SQLite + Mock Provider 回归通过：`44/44`。
- Tests covered Nashville mock results, discovery staging, provider/result dedupe, query-family hit merging, page cursor persistence, resume from cursor, no city switch before completion, centralized `bd_db.insert_lead`, historical sent/suppression/hard-bounce blocks, identity review, same-domain different-location handling, closed-store rejection, website lookup pending, provider fail-closed, timeout checkpointing, no SMTP reference in Inventory, city completion with web-directory pending, and static detection of unauthorized direct `INSERT INTO leads`.
  / 测试覆盖 Nashville Mock 结果、staging、provider/result 去重、query family 命中合并、分页 cursor 持久化、从 cursor 恢复、城市未完成不切换、统一 `bd_db.insert_lead`、历史已发/suppression/硬退信阻断、identity review、同域不同地点处理、关闭商家拒绝、官网待查、provider fail-closed、timeout checkpoint、Inventory 不引用 SMTP、Web Directory 未配置时城市不能完整耗尽，以及未授权直接 `INSERT INTO leads` 静态检测。

### Boundaries / 边界

- Codex did not call Google Places, SerpAPI, SMTP, WorkBuddy Automation, or production DB.
  / Codex 未调用 Google Places、SerpAPI、SMTP、WorkBuddy Automation 或生产数据库。
- Web Directory has only the interface and fail-closed status in this round; no real directory provider is configured. A city with Places complete but Web Directory missing is `places_matrix_completed_web_pending`, not `search_matrix_exhausted`.
  / 本轮 Web Directory 只有接口和 fail-closed 状态；未配置真实目录 provider。Places 完成但 Web Directory 缺失的城市状态为 `places_matrix_completed_web_pending`，不是 `search_matrix_exhausted`。
- Rollback is code rollback plus database restore from the pre-migration backup. If migration was run, do not manually drop production tables unless a database backup restore has been chosen.
  / 回滚方式为代码回滚加迁移前数据库备份恢复。如已执行迁移，不要手工删除生产表，除非已决定从备份恢复数据库。
