# BD Production Orchestrator — Windows Scheduled Tasks 安装脚本
# 
# 以管理员身份在 PowerShell 中运行此脚本。
# 或者手动在「任务计划程序」中创建这 5 个任务。

$pythonPath = "C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe"
$scriptDir = "C:\Users\15690\WorkBuddy\2026-06-05-15-31-42\roktandrazo-outreach"
$orchestrator = "$scriptDir\bd_orchestrator.py"
$logDir = "$scriptDir\logs"

# 创建日志目录
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$tasks = @(
    @{Name="RoktRazo-BD-Inventory"; Time="15:00"; Stage="inventory"},
    @{Name="RoktRazo-BD-PreSend";   Time="22:30"; Stage="pre-send"},
    @{Name="RoktRazo-BD-Outreach";  Time="23:00"; Stage="outreach"},
    @{Name="RoktRazo-BD-PostSend";  Time="00:10"; Stage="post-send"},
    @{Name="RoktRazo-BD-EndOfDay";  Time="00:25"; Stage="end-of-day"}
)

foreach ($task in $tasks) {
    $taskName = $task.Name
    
    # 删除已存在的同名任务
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    
    # 动作
    $action = New-ScheduledTaskAction -Execute $pythonPath `
        -Argument "`"$orchestrator`" --stage $($task.Stage) --live" `
        -WorkingDirectory $scriptDir
    
    # 触发器：每天指定时间
    $trigger = New-ScheduledTaskTrigger -Daily -At $task.Time
    
    # 设置：隐藏窗口、允许电池运行、忽略新实例
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -MultipleInstances IgnoreNew `
        -Hidden
    
    # 以当前用户运行（不弹窗）
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    
    Register-ScheduledTask -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "BD Production Orchestrator v3.1 — $($task.Stage) stage" `
        -Force
    
    Write-Host "[OK] $taskName — $($task.Time) daily"
}

Write-Host ""
Write-Host "=== 验证 ==="
Get-ScheduledTask -TaskName "RoktRazo-BD-*" | Select-Object TaskName, State | Format-Table -AutoSize

Write-Host ""
Write-Host "Done! 5 tasks registered. Open Task Scheduler (taskschd.msc) to verify."
