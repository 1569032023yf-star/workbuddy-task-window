# BD Execution Host 无人值守启动审计报告 / Unattended Boot Audit Report

日期 / Date: 2026-07-29  
范围 / Scope: 仅服务宿主、Poller 安全开关和管理员安装器 / Service host, Poller safety switch, and administrator installer only.

## 审计结论 / Audit findings

| 检查项 / Check | 结论 / Finding |
|---|---|
| SMTP | 服务宿主与安全模式 Poller 均不导入或调用 SMTP。/ The host and safe-mode Poller do not import or call SMTP. |
| Final Send Plan | 原 Poller 的数据库健康任务会读取 `final_send_plan`；服务模式现已不启动该任务。/ The normal Poller health job reads `final_send_plan`; service mode no longer starts it. |
| 客户数据库 / Customer DB | 原 Poller 的回复和退信任务会读写 `data/bd_leads.db`；服务安全模式仅启动 tracking 与 heartbeat 两个线程。/ Normal reply/bounce jobs access the DB; safe service mode starts only tracking and heartbeat. |
| 自动登录、密码、注册表 / Auto Logon, passwords, registry | 未发现 Auto Logon、Windows 密码保存或注册表凭据修改。/ None found. |
| UAC | 安装器使用标准 `RunAs` UAC 提示；未绕过 UAC。/ The installer uses standard `RunAs` elevation and does not bypass UAC. |
| 既有风险 / Existing risk | 旧安装器会对 PID 文件中的 PID 执行 `taskkill /F`。已替换为不使用 `taskkill` 的安装器。/ The old installer force-killed a mutable PID; the replacement does not. |

## 设计与改动原因 / Design and rationale

- 服务从 `Path(__file__).resolve().parent` 获取绝对项目目录，并用服务实际启动的 `sys.executable.resolve()` 作为绝对 Python 路径。/ The host derives absolute project and Python paths from the running service.
- 服务在启动子进程前显式解析项目 `.env`，因为 LocalSystem 不继承交互式用户 shell 环境。值不会写入日志。/ It explicitly parses `.env` before children start; values are never logged.
- 已存在且健康的 Guard、Ops Center 或 Poller 不会被重复启动。/ A healthy existing Guard, Ops Center, or Poller is never duplicated.
- Guard 使用状态心跳，Ops Center 使用 `127.0.0.1:8765` TCP 监听，Poller 同时要求新鲜心跳与成功的 Cloudflare tracking 任务。/ Startup waits for Guard heartbeat, the Ops Center listener, and both Poller heartbeat and successful Cloudflare tracking.
- 仅服务拥有的异常子进程会被停止后重启；外部启动且不健康的进程只报警，避免误启动副本。/ Only service-owned unhealthy children are restarted; unhealthy externally-owned processes are logged without duplication.
- 安装器配置 Automatic、三次 restart recovery（60 秒）及 failure flag。/ The installer configures Automatic startup, three 60-second restart actions, and the failure flag.

## 验证结果 / Verification performed

- `py_compile bd_execution_host_service.py bd_ops_poller.py`：通过 / passed.
- `BD_POLLER_SAFE_UNATTENDED=1` 导入检查：`safe_mode=True`，源文件中无 `smtplib` 导入 / passed: safe mode is true and no `smtplib` import exists.
- 未安装、未启动服务，未进行重启测试；因此 LocalSystem 的真实启动、Astrill 代理和 Cloudflare Worker 必须用下列验收步骤在目标机器验证。/ The service was not installed or started and no reboot was performed; actual LocalSystem, Astrill, and Cloudflare verification remains a manual acceptance test.

## 统一差异 / Unified diffs

```diff
--- a/bd_execution_host_service.py
+++ b/bd_execution_host_service.py
@@
-BASE_DIR = Path(r"C:\\Users\\15690\\WorkBuddy\\2026-06-05-15-31-42\\roktandrazo-outreach").resolve()
-PYTHON_EXE = Path(r"C:\\Users\\15690\\.workbuddy\\binaries\\python\\versions\\3.13.12\\python.exe").resolve()
+BASE_DIR = Path(__file__).resolve().parent
+PYTHON_EXE = Path(sys.executable).resolve()
@@
+        "heartbeat": LOG_DIR / "bd_delivery_guard_status.json",
+        "heartbeat_max_age": 90,
@@
+        "port": 8765,
@@
+        "heartbeat": LOG_DIR / "bd_ops_poller_status.json",
+        "heartbeat_max_age": 150,
@@
+        self._owned = {}
+        self._child_log_handles = {}
+        self._child_env = None
+        self._last_error = None
@@
+    def _load_service_env(self): ...
+    def _heartbeat_is_fresh(self, path, max_age_seconds): ...
+    def _port_is_open(self, port): ...
+    def _component_healthy(self, name): ...
+    def _wait_for_component(self, name, timeout_seconds=90): ...
@@
-                stdout=subprocess.DEVNULL,
-                stderr=subprocess.DEVNULL,
+                env=self._child_env,
+                stdout=child_log,
+                stderr=subprocess.STDOUT,
@@
-            if proc is None or proc.poll() is not None:
-                self.processes[name] = self._start_component(name)
+            if not self._component_healthy(name):
+                # stop/restart only a service-owned child; refuse an external duplicate
+                self.processes[name] = self._start_component(name)
@@
-        PID_FILE.write_text(str(os.getpid()))
+        self._load_service_env()
+        next((BASE_DIR / "data").iterdir(), None)
+        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
@@
-            time.sleep(1)
+            if not self._wait_for_component(name):
+                # stop started children and report service stopped
+                return
@@
-    _create_poller_script()
-    bin_path = f'"{python_path}" "{script_path}"'
+    bin_path = f'"{python_path}" "{script_path}" run'
+    # update an existing service instead of deleting it; configure failureflag=1
```

```diff
--- a/bd_ops_poller.py
+++ b/bd_ops_poller.py
@@
+SAFE_UNATTENDED_MODE = os.environ.get("BD_POLLER_SAFE_UNATTENDED") == "1"
@@ def _write_heartbeat():
+                "detail": str(j.get("detail", ""))[:200],
@@ def start_poller(daemon=True):
-    threads = [tracking, health, reply, bounce, delivery_guard, heartbeat]
+    threads = [tracking, heartbeat]
+    if not SAFE_UNATTENDED_MODE:
+        threads.extend([health, reply, bounce, delivery_guard])
```

```diff
--- a/install_bd_execution_host_admin.cmd
+++ b/install_bd_execution_host_admin.cmd
@@
-[old inline service creation, taskkill, temporary PowerShell policy bypass]
+net session >nul 2>&1
+if errorlevel 1 powershell -NoProfile -Command "Start-Process ... -Verb RunAs"
+"%PYTHON%" "%SCRIPT%" install
+sc start BDExecutionHost
+[read host status JSON and require all three component health values]
```

## 风险与限制 / Risks and limitations

- LocalSystem 与当前登录用户的 Astrill 代理设置可能不同。Poller 状态 JSON 的 `jobs.tracking.detail` 必须在验收时显示成功 transport；否则服务会在 90 秒内启动失败，而不是伪报健康。/ LocalSystem may not share the user's Astrill proxy. Confirm the successful transport in the Poller status JSON; failure prevents a false healthy startup.
- 服务帐户必须对项目、`.env`、`data` 和 `output` 具有 ACL 权限。启动前置检查会验证 `.env` 读取、`data` 枚举和 `output` 写入，失败即停止服务。/ ACL permissions are required; preflight fails closed.
- 现有正常模式 Poller 保留原有数据库行为，供非服务使用；安全保证仅适用于服务注入 `BD_POLLER_SAFE_UNATTENDED=1` 的子进程。/ Normal interactive Poller behavior remains unchanged; the safety guarantee applies to service-injected safe mode.

## 手工验收清单 / Manual acceptance checklist

1. 以管理员身份运行 `install_bd_execution_host_admin.cmd`。确认 UAC 提示出现并选择 Yes。/ Run the installer as administrator and approve the UAC prompt.
2. 执行 `shutdown /r /t 0` 重启 Windows；不要登录。/ Reboot with `shutdown /r /t 0`; do not sign in.
3. 等待五分钟后登录。/ Wait five minutes, then sign in.
4. 运行 `sc query BDExecutionHost`，必须为 `RUNNING`。/ It must report `RUNNING`.
5. 查看 `output\bd_execution_host_status.json`：三个组件均为 `healthy: true`；`last_heartbeat_at` 早于登录时间。/ All three components must be healthy and the host heartbeat must predate login.
6. 查看 `output\bd_delivery_guard_status.json`：`last_heartbeat_at` 早于登录时间。/ Guard heartbeat must predate login.
7. 访问或使用 `Test-NetConnection 127.0.0.1 -Port 8765` 验证 Ops Center。/ Verify Ops Center on port 8765.
8. 查看 `output\bd_ops_poller_status.json`：`running: true`、tracking 有 `last_success_at`，并检查 `detail` 显示成功 transport（Astrill/curl 系统代理路径如适用）。/ Require Poller running, a successful tracking timestamp, and a successful transport detail.
9. 用 `Get-CimInstance Win32_Process | Where-Object CommandLine -match 'bd_delivery_guard|bd_review_server|_start_poller_inline'` 确认每个组件仅一份。/ Confirm one process for each component.
10. 检查 `bd_execution_host*.log`、`bd_delivery_guard.log` 和 Poller status：不得出现 SMTP；并确认 `data\bd_leads.db` 的时间戳未因服务启动变化，且无 Final Send Plan 生成。/ Check for no SMTP and confirm the database timestamp did not change from service startup or generate a Final Send Plan.
