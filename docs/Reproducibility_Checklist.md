# AutoForge Reproducibility Checklist

Last updated: 2026-05-01

## Environment

- Python 3.11+ is recommended.
- Run commands from the repository root.
- Set `PYTHONPATH=.` before tests/scripts on Windows PowerShell.
- Copy `.env.example` to `.env`.
- Keep `SANDBOX_BACKEND=local` for default MVP checks.
- Optional: set an LLM API key for real `strategy=agent` runs.

## Baseline Verification

```powershell
cd <path-to-cloned-repository>
$env:PYTHONPATH='.'
python -m pytest
```

Expected result: all tests pass.

## Generate Mock Agent Demo Report

This command does not require an LLM key:

```powershell
$env:PYTHONPATH='.'
python scripts\run_agent_demo_cases.py --mock
```

Output:

- `evaluation/results/agent_demo_report_mock_*.json`

## Generate Real Agent Demo Report

This command requires an LLM key and a configured provider:

```powershell
$env:PYTHONPATH='.'
python scripts\run_agent_demo_cases.py --limit 1 --skills-dir skills_report_llm
python scripts\run_agent_demo_cases.py --limit 10 --repeats 5 --skills-dir skills_report_llm_50 --checkpoint-interval 5
```

Output:

- `evaluation/results/agent_demo_report_agent_*.json`
- `data/forge_logs/*.json`
- `skills_report_llm/`

## Run Evaluation Reports

```powershell
$env:PYTHONPATH='.'
python -m evaluation.runner --mode mock --strategies full,no_retrieval,registry_only
```

Optional live backend run:

```powershell
.\scripts\start_backend.ps1
$env:PYTHONPATH='.'
python -m evaluation.runner --mode backend --strategies full,registry_only --backend-url http://127.0.0.1:8000
```

Output:

- `evaluation/results/eval_report_*.json`

## Run Threshold Sweep

```powershell
$env:PYTHONPATH='.'
python scripts\threshold_sweep.py --include-paraphrases
```

Output:

- `evaluation/results/threshold_sweep_*.json`

## Verify MCP Helpers

```powershell
$env:PYTHONPATH='.'
python scripts\verify_mcp_helpers.py
```

Output:

- `evaluation/results/mcp_helper_verification.json`

## Build Final Report Assets

```powershell
$env:PYTHONPATH='.'
python scripts\build_final_report_assets.py
```

Output:

- `evaluation/results/final_metrics_table.md`
- `evaluation/results/failure_taxonomy.md`
- `evaluation/results/representative_cases.md`
- `evaluation/results/final_run_manifest.json`

## Start UI

```powershell
.\scripts\start_backend.ps1
.\scripts\start_frontend.ps1
```

Open:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:8501`
- OpenAPI: `http://127.0.0.1:8000/docs`

## External MCP Client

Manual validation target:

```powershell
python -m backend.mcp.server
```

Validate with Claude Desktop, Cursor, or another MCP-compatible client:

- catalog/list tools
- direct tool invocation
- natural-language `autoforge_query`

Save screenshots or exported JSON in `evaluation/results/` or `docs/`.
