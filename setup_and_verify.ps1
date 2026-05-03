param(
    [string]$Python = "python",
    [string]$VenvPath = ".venv",
    [switch]$SkipInstall,
    [switch]$SkipTests,
    [switch]$SkipSmoke,
    [switch]$SkipMcpCheck,
    [switch]$RunMockEvaluation,
    [switch]$Start,
    [switch]$VisibleLogs,
    [string]$HostName = "127.0.0.1",
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 8501
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-Step {
    param(
        [string]$Title,
        [scriptblock]$Command
    )
    Write-Step $Title
    $global:LASTEXITCODE = 0
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed with exit code ${LASTEXITCODE}: $Title"
    }
}

function Get-VenvPython {
    param([string]$Root, [string]$Path)
    $venvRoot = Join-Path $Root $Path
    $windowsPython = Join-Path $venvRoot "Scripts\python.exe"
    $unixPython = Join-Path $venvRoot "bin\python"
    if (Test-Path $windowsPython) { return $windowsPython }
    if (Test-Path $unixPython) { return $unixPython }
    throw "Cannot find Python executable in virtual environment: $venvRoot"
}

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

Write-Step "AutoForge setup and verification"
Write-Host "Repository: $RepoRoot"

Invoke-Step "Checking Python version >= 3.11" {
    & $Python -c "import sys; print(sys.version); raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
}

if (-not (Test-Path $VenvPath)) {
    Invoke-Step "Creating virtual environment at $VenvPath" {
        & $Python -m venv $VenvPath
    }
}
else {
    Write-Step "Using existing virtual environment at $VenvPath"
}

$VenvPython = Get-VenvPython -Root $RepoRoot -Path $VenvPath
Write-Host "Virtualenv Python: $VenvPython"

if (-not $SkipInstall) {
    Invoke-Step "Upgrading pip" {
        & $VenvPython -m pip install --upgrade pip
    }
    Invoke-Step "Installing dependencies" {
        & $VenvPython -m pip install -r requirements.txt
    }
}
else {
    Write-Step "Skipping dependency installation"
}

if (-not (Test-Path ".env")) {
    Invoke-Step "Creating .env from .env.example" {
        Copy-Item -LiteralPath ".env.example" -Destination ".env"
    }
}
else {
    Write-Step "Keeping existing .env"
}

Invoke-Step "Creating runtime directories" {
    New-Item -ItemType Directory -Force -Path "data\forge_logs", "data\chromadb", "evaluation\results" | Out-Null
}

$env:PYTHONPATH = "."

Invoke-Step "Validating benchmark dataset" {
    & $VenvPython scripts\benchmark_dataset_tools.py validate
}

if (-not $SkipSmoke) {
    Invoke-Step "Running smoke test" {
        & $VenvPython scripts\smoke_test.py
    }
}

if (-not $SkipTests) {
    Invoke-Step "Running pytest suite" {
        & $VenvPython -m pytest
    }
}

if (-not $SkipMcpCheck) {
    Invoke-Step "Verifying MCP helper functions" {
        & $VenvPython scripts\verify_mcp_helpers.py
    }
}

if ($RunMockEvaluation) {
    Invoke-Step "Running mock evaluation reports" {
        & $VenvPython -m evaluation.runner --mode mock --strategies full,no_retrieval,registry_only
    }
    Invoke-Step "Running threshold sweep" {
        & $VenvPython scripts\threshold_sweep.py
    }
}

if ($Start) {
    Invoke-Step "Starting backend and frontend" {
        $startArgs = @(
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "scripts\start_all.ps1",
            "-VenvPath",
            $VenvPath,
            "-HostName",
            $HostName,
            "-BackendPort",
            $BackendPort,
            "-FrontendPort",
            $FrontendPort
        )
        if ($VisibleLogs) {
            $startArgs += "-VisibleLogs"
        }
        & powershell @startArgs
    }
}

Write-Host ""
Write-Host "AutoForge setup and verification completed." -ForegroundColor Green
Write-Host "Backend : http://$HostName`:$BackendPort"
Write-Host "Frontend: http://$HostName`:$FrontendPort"
Write-Host "OpenAPI : http://$HostName`:$BackendPort/docs"
