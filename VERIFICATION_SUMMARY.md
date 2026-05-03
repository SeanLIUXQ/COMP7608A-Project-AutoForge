# Verification Summary

This clean submission repository was verified on Windows PowerShell from the repository root after the final GitHub packaging cleanup.

## Commands Run

```powershell
python scripts\benchmark_dataset_tools.py validate
python scripts\smoke_test.py
python -m pytest
python scripts\verify_mcp_helpers.py
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_and_verify.ps1
```

## Results

| Check | Result |
| --- | --- |
| Benchmark dataset validation | Passed; 80 queries with balanced difficulty levels L1-L4 |
| Smoke test | Passed for sandbox execution and deterministic forge path |
| Unit/integration tests | Passed; 50 tests |
| MCP helper verification | Passed; catalog loading, direct invocation, and query integration were all available |
| One-command setup script | Passed; created a virtual environment, installed dependencies, and reran verification |

The default verification path does not require a real LLM API key. Real DeepSeek-based agent evidence, generated figures, Docker sandbox traces, and curated generated tool bundles are included under `docs/report/real_agent_evidence/` and `evaluation/results/`.

Final packaging checks also passed: no real `.env`, no `.venv`, no token-like secrets, no local absolute paths, and no Chinese/garbled text were found in trackable files.

