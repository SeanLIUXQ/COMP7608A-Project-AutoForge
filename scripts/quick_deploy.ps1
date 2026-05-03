param(
    [string]$Python = "python",
    [string]$VenvPath = ".venv",
    [switch]$SkipInstall,
    [switch]$SkipTests,
    [switch]$SkipSmoke,
    [switch]$SkipMcpCheck,
    [switch]$RunEvaluation,
    [switch]$Start,
    [switch]$VisibleLogs,
    [switch]$ForceEnv,
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

function Get-VenvPython {
    param([string]$Root, [string]$Path)
    $venvRoot = Join-Path $Root $Path
    $windowsPython = Join-Path $venvRoot "Scripts\python.exe"
    $unixPython = Join-Path $venvRoot "bin\python"
    if (Test-Path $windowsPython) {
        return $windowsPython
    }
    if (Test-Path $unixPython) {
        return $unixPython
    }
    throw "Cannot find Python executable in virtual environment: $venvRoot"
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

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $RepoRoot

Write-Step "AutoForge quick deployment"
Write-Host "Repository: $RepoRoot"

Invoke-Step "Checking Python version >= 3.11" {
    & $Python -c "import sys; print(sys.version); raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
}

$venvRoot = Join-Path $RepoRoot $VenvPath
if (-not (Test-Path $venvRoot)) {
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
    Invoke-Step "Installing project dependencies" {
        & $VenvPython -m pip install -r requirements.txt
    }
}
else {
    Write-Step "Skipping dependency installation"
}

$envPath = Join-Path $RepoRoot ".env"
if ($ForceEnv -or -not (Test-Path $envPath)) {
    Invoke-Step "Writing local .env defaults" {
        $envText = @"
# AutoForge local deployment defaults.
# Add a real LLM key only when running strategy=agent or forge CLI.

LLM_PROVIDER=deepseek

# DEEPSEEK_API_KEY=
# DASHSCOPE_API_KEY=
# OPENAI_API_KEY=

SANDBOX_BACKEND=local
AUTOFORGE_ENABLE_VECTOR_STORE=0
AUTOFORGE_SIMILARITY_THRESHOLD=0.75
AUTOFORGE_ENABLE_LLM_MATCH_VERIFY=0
AUTOFORGE_ENABLE_AGENT_SLOW_PATH=0
AUTOFORGE_FORGE_LOG_DIR=./data/forge_logs
"@
        Set-Content -Path $envPath -Value $envText -Encoding UTF8
    }
}
else {
    Write-Step "Keeping existing .env"
}

Invoke-Step "Creating runtime output directories" {
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
else {
    Write-Step "Skipping smoke test"
}

if (-not $SkipTests) {
    Invoke-Step "Running unit tests" {
        & $VenvPython -m pytest
    }
}
else {
    Write-Step "Skipping unit tests"
}

if (-not $SkipMcpCheck) {
    Invoke-Step "Verifying MCP helper functions" {
        & $VenvPython scripts\verify_mcp_helpers.py
    }
}
else {
    Write-Step "Skipping MCP helper verification"
}

if ($RunEvaluation) {
    Invoke-Step "Running mock evaluation reports" {
        & $VenvPython -m evaluation.runner --mode mock --strategies full,no_retrieval,registry_only
    }
    Invoke-Step "Running threshold sweep" {
        & $VenvPython scripts\threshold_sweep.py
    }
    Invoke-Step "Building final report assets" {
        & $VenvPython scripts\build_final_report_assets.py --mode mock --strategies full,no_retrieval,registry_only
    }
}

if ($Start) {
    Invoke-Step "Starting backend and frontend" {
        $startScript = Join-Path $RepoRoot "scripts\start_all.ps1"
        $startArgs = @(
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            $startScript,
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
Write-Host "AutoForge deployment completed." -ForegroundColor Green
Write-Host "Backend URL : http://$HostName`:$BackendPort"
Write-Host "Frontend URL: http://$HostName`:$FrontendPort"
Write-Host "OpenAPI URL : http://$HostName`:$BackendPort/docs"
Write-Host ""
Write-Host "Start later with:"
Write-Host "  .\scripts\start_all.ps1 -VisibleLogs"
Write-Host "Stop hidden/managed servers with:"
Write-Host "  .\scripts\stop_all.ps1"
