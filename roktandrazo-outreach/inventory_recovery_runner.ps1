# inventory_recovery_runner.ps1
# Hidden background runner for Windows Task Scheduler.
# Survives terminal close, single-instance lock, logs to file.
param([string]$Target = "60")

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$python = "C:\Users\15690\.workbuddy\binaries\python\versions\3.13.12\python.exe"
$lockFile = "$scriptDir\output\.inventory_recovery.lock"
$logDir = "$scriptDir\logs"

# Single-instance lock
if (Test-Path $lockFile) {
    $storedPid = Get-Content $lockFile -ErrorAction SilentlyContinue
    if ($storedPid) {
        $storedPid = $storedPid.Trim()
        try { $proc = Get-Process -Id $storedPid -ErrorAction Stop; Write-Output "Already running PID=$storedPid"; exit 0 }
        catch { Remove-Item $lockFile -Force }
    } else {
        Remove-Item $lockFile -Force
    }
}
$currentPid = [System.Diagnostics.Process]::GetCurrentProcess().Id
New-Item -Force -Path $lockFile -Value $currentPid | Out-Null
New-Item -Force -ItemType Directory -Path $logDir | Out-Null

$logFile = "$logDir\inventory_recovery_$(Get-Date -Format 'yyyyMMdd').log"
$statusFile = "$scriptDir\output\inventory_recovery_status.json"

# Initial status
$initStatus = @{
    run_id = (Get-Date -Format 'yyyyMMdd-HHmmss')
    started_at = (Get-Date -Format 'o')
    updated_at = (Get-Date -Format 'o')
    process_id = $PID
    run_mode = "inventory"
    send_enabled = $false
    target = [int]$Target
    status = "running"
} | ConvertTo-Json -Compress
$initStatus | Out-File $statusFile -Encoding utf8

try {
    & $python "$scriptDir\inventory_recovery_daemon.py" --target $Target `
        2>&1 | Tee-Object -FilePath $logFile -Append
    $exitCode = $LASTEXITCODE

    $finalStatus = @{
        updated_at = (Get-Date -Format 'o')
        exit_code = $exitCode
        status = if ($exitCode -eq 0) { "complete" } else { "partial" }
    } | ConvertTo-Json -Compress
    $finalStatus | Out-File $statusFile -Encoding utf8
}
finally {
    Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
}
