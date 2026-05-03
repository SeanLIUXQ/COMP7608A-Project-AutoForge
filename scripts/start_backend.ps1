param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000,
    [string]$VenvPath = ".venv"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $RepoRoot

$venvPython = Join-Path $RepoRoot "$VenvPath\Scripts\python.exe"
$pythonExe = if (Test-Path $venvPython) { $venvPython } else { "python" }
$env:PYTHONPATH = "."

& $pythonExe -m uvicorn backend.main:app --host $HostName --port $Port --reload
