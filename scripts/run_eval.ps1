param(
    [ValidateSet("mock", "backend")]
    [string]$Mode = "backend",
    [string]$Strategies = "full,no_retrieval,registry_only",
    [string]$BackendUrl = "http://127.0.0.1:8000"
)

if ($Mode -eq "backend") {
    python -m evaluation.runner --mode $Mode --strategies $Strategies --backend-url $BackendUrl
}
else {
    python -m evaluation.runner --mode $Mode --strategies $Strategies
}
