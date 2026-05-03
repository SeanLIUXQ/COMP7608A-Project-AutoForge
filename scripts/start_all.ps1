param(
    [string]$HostName = "127.0.0.1",
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 8501,
    [string]$VenvPath = ".venv",
    [switch]$VisibleLogs,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Quote-PS {
    param([string]$Value)
    return "'" + $Value.Replace("'", "''") + "'"
}

function Resolve-Python {
    param([string]$Root, [string]$Path)
    $venvRoot = Join-Path $Root $Path
    $windowsPython = Join-Path $venvRoot "Scripts\python.exe"
    $unixPython = Join-Path $venvRoot "bin\python"
    if (Test-Path $windowsPython) {
        return (Resolve-Path $windowsPython).Path
    }
    if (Test-Path $unixPython) {
        return (Resolve-Path $unixPython).Path
    }
    return "python"
}

function Start-AutoForgeProcess {
    param(
        [string]$Name,
        [string]$Command
    )

    $args = @("-NoProfile", "-ExecutionPolicy", "Bypass")
    if ($VisibleLogs) {
        $args += "-NoExit"
    }
    $args += @("-Command", $Command)

    if ($DryRun) {
        Write-Host "[$Name] $Command"
        return $null
    }

    $windowStyle = if ($VisibleLogs) { "Normal" } else { "Hidden" }
    return Start-Process -FilePath "powershell" -ArgumentList $args -WindowStyle $windowStyle -PassThru
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$PythonExe = Resolve-Python -Root $RepoRoot -Path $VenvPath

$quotedRoot = Quote-PS $RepoRoot
$quotedPython = Quote-PS $PythonExe
$backendCommand = "Set-Location -LiteralPath $quotedRoot; `$env:PYTHONPATH='.'; & $quotedPython -m uvicorn backend.main:app --host $HostName --port $BackendPort --reload"
$frontendCommand = "Set-Location -LiteralPath $quotedRoot; `$env:PYTHONPATH='.'; & $quotedPython -m streamlit run frontend/app.py --server.address $HostName --server.port $FrontendPort --server.headless true"

Write-Host "Starting AutoForge services..."
Write-Host "Backend : http://$HostName`:$BackendPort"
Write-Host "Frontend: http://$HostName`:$FrontendPort"
Write-Host "OpenAPI : http://$HostName`:$BackendPort/docs"

$backendProcess = Start-AutoForgeProcess -Name "backend" -Command $backendCommand
$frontendProcess = Start-AutoForgeProcess -Name "frontend" -Command $frontendCommand

if (-not $DryRun) {
    $pidFile = Join-Path $RepoRoot ".autoforge_pids.json"
    $payload = [ordered]@{
        backend_pid = $backendProcess.Id
        frontend_pid = $frontendProcess.Id
        backend_url = "http://$HostName`:$BackendPort"
        frontend_url = "http://$HostName`:$FrontendPort"
        openapi_url = "http://$HostName`:$BackendPort/docs"
        visible_logs = [bool]$VisibleLogs
    }
    $payload | ConvertTo-Json | Set-Content -Path $pidFile -Encoding UTF8
    Write-Host "Process IDs written to $pidFile"
    Write-Host "Stop with: .\scripts\stop_all.ps1"
}
