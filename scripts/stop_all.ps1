param(
    [string]$PidFile = ".autoforge_pids.json"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
Set-Location $RepoRoot

if (-not (Test-Path $PidFile)) {
    Write-Host "No AutoForge PID file found: $PidFile"
    return
}

$payload = Get-Content -Path $PidFile -Encoding UTF8 | ConvertFrom-Json
$ids = @($payload.backend_pid, $payload.frontend_pid) | Where-Object { $_ }

foreach ($id in $ids) {
    $process = Get-Process -Id $id -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "Stopping process $id ($($process.ProcessName))"
        Stop-Process -Id $id -Force
    }
    else {
        Write-Host "Process $id is not running"
    }
}

Remove-Item -Path $PidFile -ErrorAction SilentlyContinue
Write-Host "AutoForge managed services stopped."
