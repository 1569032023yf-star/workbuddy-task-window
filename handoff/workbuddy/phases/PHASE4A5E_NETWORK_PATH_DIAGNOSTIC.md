# PHASE 4A.5E — Official-site network path diagnostic (MIRRORED) / 官网网络路径只读诊断（镜像）

> **THIS IS A HANDOFF MIRROR, NOT A LOCAL EXECUTION.** The diagnostic was executed in the
> **development/Codex** repo by mistake; it is reproduced here verbatim-in-substance so the
> production handoff stays complete. Nothing was re-run in the production repo.
>
> | Provenance field | Value |
> |---|---|
> | `SOURCE_EVIDENCE_REPO` | `1569032023yf-star/roktandrazo-outreach-codex` (DEVELOPMENT SOURCE / CODEX HANDOFF) |
> | `SOURCE_EVIDENCE_COMMIT` | `bf32df09688763ab2e25e86fee914023a8d6f33a` — "Diagnose official-site network path" (2026-09-22 23:04:17 +08) |
> | `SOURCE_EVIDENCE_PATH` | `handoff/workbuddy/phases/PHASE4A5E_NETWORK_PATH_DIAGNOSTIC.md` (in that repo) |
> | `MIRROR_TARGET_REPO` | `1569032023yf-star/workbuddy-task-window` (PRODUCTION SOURCE / PRODUCTION HANDOFF) ← this repo |
> | `MIRRORED_AT` | 2026-09-23 (Asia/Shanghai) |
> | **`DIAGNOSTIC_RERUN`** | **false** — no probe, no DNS/TCP/TLS test, no HTTP request, no Chromium launch was performed in this repo |
> | `PHASE_TYPE` | HANDOFF SYNC ONLY |

Date of the original diagnostic / 原诊断日期: 2026-09-22
Scope / 范围: Read-only public-network diagnostics only. No production code, database, scheduler, Inventory, email, or send-path operation was changed or invoked. / 仅执行公开网络只读诊断；未改动或调用生产代码、数据库、调度、Inventory、邮件或发送路径。

---

## Purpose and method / 目的与方法

The remaining `discovery_id=362` blocker was tested at the canonical apex and `www` URLs using isolated, process-scoped routes. The local Windows/Astrill settings were never altered. `as_is` retained the process environment; `explicit_proxy` used only `127.0.0.1:3213`; `direct` installed a no-proxy handler for that process; Chromium had proxy variables cleared only in its diagnostic child process. / 对剩余的 `discovery_id=362` 阻塞项，在 apex 与 `www` 标准 URL 上执行隔离的进程级路径测试。未更改本机 Windows/Astrill 设置。`as_is` 保留进程环境；`explicit_proxy` 仅使用 `127.0.0.1:3213`；`direct` 仅为该进程安装无代理处理器；Chromium 仅在诊断子进程清空代理变量。

Current-process proxy route / 当前进程代理路由: `HTTP_PROXY` and `HTTPS_PROXY` were both present as `127.0.0.1:3213` (no credentials recorded). / `HTTP_PROXY` 与 `HTTPS_PROXY` 均为 `127.0.0.1:3213`（未记录凭据）。

`DNS_RESULT`, `TCP_443`, and `TLS_RESULT` below are independent direct target preflights. They demonstrate DNS/TCP/TLS reachability; the HTTP outcome is the route-specific application-layer result. / 下述 `DNS_RESULT`、`TCP_443`、`TLS_RESULT` 是对目标的独立直连预检，证明 DNS/TCP/TLS 可达；HTTP 结果则是每个路由的应用层结果。

## Sciencenter exact URL probes / Sciencenter 精确 URL 探针

| MODE / 模式 | URL | DNS_RESULT | TCP_443 | TLS_RESULT | HTTP_STATUS | FINAL_URL | RESPONSE_BYTES | ELAPSED_MS | ERROR_TYPE | ERROR_TEXT | visible `Sciencenter` | visible `info@sciencenter.org` |
|---|---|---|---|---|---:|---|---:|---:|---|---|---|---|
| as_is / 保持环境 | https://sciencenter.org/ | 209.87.149.189 | OK | OK: TLSv1.3 | 400 | https://sciencenter.org/ | 226 | 1078.4 | HTTPError | HTTP Error 400: Bad Request | false | false |
| explicit_proxy / 显式代理 | https://sciencenter.org/ | 209.87.149.189 | OK; proxy TCP OK | OK: TLSv1.3 | 400 | https://sciencenter.org/ | 226 | 1004.5 | HTTPError | HTTP Error 400: Bad Request | false | false |
| direct / 进程直连 | https://sciencenter.org/ | 209.87.149.189 | OK | OK: TLSv1.3 | 400 | https://sciencenter.org/ | 226 | 1031.9 | HTTPError | HTTP Error 400: Bad Request | false | false |
| browser_chromium_direct_no_proxy / Chromium 进程直连无代理 | https://sciencenter.org/ | 209.87.149.189 | OK | OK: TLSv1.3 | null | null | 0 | 13476.2 | TimeoutError | official_site_browser_page_timeout:12000ms | false | false |
| as_is / 保持环境 | https://www.sciencenter.org/ | 209.87.149.189 | OK | OK: TLSv1.3 | 400 | https://www.sciencenter.org/ | 226 | 1089.8 | HTTPError | HTTP Error 400: Bad Request | false | false |
| explicit_proxy / 显式代理 | https://www.sciencenter.org/ | 209.87.149.189 | OK; proxy TCP OK | OK: TLSv1.3 | 400 | https://www.sciencenter.org/ | 226 | 914.3 | HTTPError | HTTP Error 400: Bad Request | false | false |
| direct / 进程直连 | https://www.sciencenter.org/ | 209.87.149.189 | OK | OK: TLSv1.3 | 400 | https://www.sciencenter.org/ | 226 | 1070.0 | HTTPError | HTTP Error 400: Bad Request | false | false |
| browser_chromium_direct_no_proxy / Chromium 进程直连无代理 | https://www.sciencenter.org/ | 209.87.149.189 | OK | OK: TLSv1.3 | null | null | 0 | 13491.3 | TimeoutError | official_site_browser_page_timeout:12000ms | false | false |

## Control sites / 对照官网

The following were selected by a production-DB read-only query from recent qualifying official evidence: Cantrip Cards & Games (`lead_discovery_results.id=306`) and Ithaca ReUse Center (`id=383`). The selection query did not write production data. / 以下站点通过生产数据库只读查询，从近期合格官网证据中选取：Cantrip Cards & Games（`lead_discovery_results.id=306`）与 Ithaca ReUse Center（`id=383`）。选择查询未写入生产数据。

| MODE / 模式 | URL | DNS_RESULT | TCP_443 | TLS_RESULT | HTTP_STATUS | FINAL_URL | RESPONSE_BYTES | ELAPSED_MS | ERROR_TYPE | ERROR_TEXT |
|---|---|---|---|---|---:|---|---:|---:|---|---|
| explicit_proxy / 显式代理 | https://cantripcards.com/ | 23.227.38.32 | OK; proxy TCP OK | OK: TLSv1.3 | 200 | https://cantripcards.com/ | 124545 | 1450.2 | null | null |
| direct / 进程直连 | https://cantripcards.com/ | 23.227.38.32 | OK | OK: TLSv1.3 | 200 | https://cantripcards.com/ | 126369 | 1452.0 | null | null |
| explicit_proxy / 显式代理 | https://ithacareuse.org/contact/ | 192.138.189.24 | OK; proxy TCP OK | OK: TLSv1.3 | 200 | https://ithacareuse.org/contact/ | 135065 | 1531.1 | null | null |
| direct / 进程直连 | https://ithacareuse.org/contact/ | 192.138.189.24 | OK | OK: TLSv1.3 | 200 | https://ithacareuse.org/contact/ | 135065 | 3203.5 | null | null |

## Decision / 结论

`ROOT_CAUSE = automation_client/network_fingerprint`.

Both direct and proxy static requests returned the same HTTP 400 for both Sciencenter host forms, while both controls returned HTTP 200 through both routes. Chromium with proxy disabled for only its diagnostic process timed out on both host forms after its normal 12-second page deadline. DNS, TCP 443, and TLS each succeeded. Therefore this is not a general proxy-path failure and is not a general local egress failure. It is consistent with Sciencenter rejecting or not completing automated client traffic from this environment after transport/TLS succeeds. The diagnosis does not establish a source-code defect and makes no code change. / 对两个 Sciencenter 主机形式，直连与代理静态请求均返回相同的 HTTP 400；两个对照站点则在两条路径上均返回 HTTP 200。仅为 Chromium 诊断进程禁用代理后，两个主机形式都在正常 12 秒页面期限后超时。DNS、TCP 443、TLS 均成功。因此这不是通用代理路径问题，也不是通用本地出口故障；结果符合该站点在传输/TLS 成功后拒绝或无法完成本环境自动化客户端流量。该诊断未证明源码缺陷，未作代码更改。

## Safety and operational state / 安全与运行状态

- `CODE_CHANGES = 0`; `DB_WRITES = 0`; `SMTP = 0`; `IMAP = 0`; `FSP = 0`; `INVENTORY_RUNS = 0`.
- `PRODUCTION_FILES_CHANGED = 0`; `PRODUCTION_DB_WRITES = 0`; `SCHEDULER_CHANGES = 0`.
- No system proxy, Astrill setting, WorkBuddy automation, Windows Task, or service was changed. / 未更改系统代理、Astrill 设置、WorkBuddy 自动化、Windows 任务或服务。
- Inventory, PreSend/Preflight/Outreach were not resumed by this phase; recovery was not altered. / 本阶段未恢复 Inventory、PreSend/Preflight/Outreach；未改动 recovery。

## Next action / 后续动作

STOP. This phase authorizes no remediation, deployment, Inventory, sending, or scheduler resume. A separate approval is required for any targeted mitigation of the site-specific automation-client reachability block. / 停止。本阶段不授权修复、部署、Inventory、发送或恢复调度。任何针对该站点自动化客户端可达性阻塞的定向缓解均需另行授权。

---

## Mirror notes / 镜像说明（production-host specific）

- This file is a **handoff mirror only**. The diagnostic process itself was executed inside the
  development/Codex repo; the production repo performed **no** network probe, no Chromium launch,
  no DB read, and no write of any kind.
- 本文件仅为交接镜像。诊断过程本身在开发/Codex 仓库内执行；生产仓库**未**执行任何网络探测、
  未启动 Chromium、未读取数据库、未做任何写入。
- The original evidence file lives in the Codex repo at `handoff/workbuddy/phases/PHASE4A5E_NETWORK_PATH_DIAGNOSTIC.md`
  (note: the Codex repo keeps `CURRENT_STATUS.md` / `LATEST_RESULT.json` / `CHANGELOG.md` at `handoff/`,
  whereas this production repo keeps them at `handoff/workbuddy/`).
- 原始证据文件位于 Codex 仓库的 `handoff/workbuddy/phases/PHASE4A5E_NETWORK_PATH_DIAGNOSTIC.md`
  （注意：Codex 仓库把 `CURRENT_STATUS.md` / `LATEST_RESULT.json` / `CHANGELOG.md` 放在 `handoff/`，
  而本生产仓库放在 `handoff/workbuddy/`）。
- **Repository separation was violated in the source event**: a diagnostic intended for the
  production workflow was executed in the Codex repo. No production artefact was altered by that
  mistake; this mirror restores the production handoff's completeness. The separation rule
  (production handoff written only to `workbuddy-task-window`) remains in force.
- **源事件违反了仓库分工**：一次本应属于生产流程的诊断在 Codex 仓库中被误执行。该失误未改动任何
  生产产物；本镜像用于恢复生产交接记录的完整性。分工规则（生产 handoff 只写 `workbuddy-task-window`）
  依然有效。
- `DIAGNOSTIC_RERUN = false`. No section of this mirror was produced by re-executing anything.
- `DIAGNOSTIC_RERUN = false`。本镜像的任何部分均非通过重新执行产生。
