# COMP7608A Project_AutoForge

AutoForge is a self-evolving multi-agent tool system for reusable tool creation, retrieval, sandbox execution, and warm reuse. It first tries to solve a natural-language task by retrieving an existing tool from a registry. If no confident tool is available, the optional LLM agent path can plan, code, verify, package, and register a new Python tool for later reuse.

This repository is a cleaned submission package for TA review. It contains the runnable system, benchmark dataset, tests, final report, result evidence, figures, screenshots, and one-command setup scripts.

## Team

| Name | Student ID | Main Responsibility |
|---|---:|---|
| Liu Xinquan | 3036659637 | Project lead; multi-agent forge pipeline; DeepSeek real-agent experiments; Docker sandbox evidence; final report integration |
| Cheung Yu Lung | 3035477616 | FastAPI backend; Tool-RAG retrieval; query strategies; dynamic tool routes; MCP helper; threshold sweep |
| Lyu Linze | 3036658619 | Streamlit frontend; benchmark organization; dashboard; evaluation metrics; visualization and failure analysis |

## What Is Included

```text
agents/        Planner, Coder, Verifier, Packager, forge pipeline, prompts
backend/       FastAPI backend, query service, tool registry, dynamic API, MCP helper
frontend/      Streamlit app: Home, Chat, Tool Browser, Dashboard
retrieval/     Tool retrieval router and ToolStore facade
sandbox/       Local and Docker sandbox execution backends
shared/        Schemas, constants, LLM factory, shared utilities
evaluation/    320-query benchmark, judge, runner, selected result JSON files
scripts/       Setup, startup, smoke, evaluation, figure-generation scripts
tests/         Unit and integration tests
skills/        Seeded reusable tool bundles used by the app
docs/          Final report, proposal, evidence, figures, screenshots
docker/        Optional Docker backend/sandbox files
```

## Quick Verification For TA

PowerShell, from the repository root:

```powershell
.\setup_and_verify.ps1
```

This command will:

1. Create `.venv`
2. Install `requirements.txt`
3. Create a safe local `.env` if one does not exist
4. Validate the benchmark dataset
5. Run the local smoke test
6. Run the pytest suite
7. Verify MCP helper functions

The default verification path does **not** require an LLM API key.

## Start The Demo App

After setup:

```powershell
.\scripts\start_all.ps1 -VisibleLogs
```

Open:

- Frontend: http://127.0.0.1:8501
- Backend health: http://127.0.0.1:8000/health
- OpenAPI: http://127.0.0.1:8000/docs

Stop managed services:

```powershell
.\scripts\stop_all.ps1
```

## Useful Manual Commands

```powershell
# Activate local venv
.\.venv\Scripts\Activate.ps1

# Validate benchmark
python scripts\benchmark_dataset_tools.py validate

# Run smoke test
python scripts\smoke_test.py

# Run tests
python -m pytest

# Run mock evaluation reports
python -m evaluation.runner --mode mock --strategies full,no_retrieval,registry_only

# Run threshold sweep
python scripts\threshold_sweep.py
```

## Query Strategies

`POST /query` supports:

- `full`: retrieval first, then deterministic fallback on miss.
- `no_retrieval`: skip retrieval and use deterministic fallback.
- `registry_only`: only use retrieved registry tools.
- `agent`: use the real LLM forge path, requiring an API key.

Example request:

```json
{
  "query": "Reverse the text 'streamlit'",
  "strategy": "full"
}
```

## Optional Real LLM Agent Run

The submitted report uses DeepSeek `deepseek-v4-pro` evidence. To run the real LLM agent path yourself:

1. Copy `.env.example` to `.env`.
2. Fill in `DEEPSEEK_API_KEY`.
3. Set `AUTOFORGE_ENABLE_AGENT_SLOW_PATH=1` if you want `full` to forge on retrieval misses, or use `strategy=agent` directly.
4. Run a small agent demo first:

```powershell
python scripts\run_agent_demo_cases.py --limit 1 --skills-dir skills_agent_demo
```

For Docker sandbox evidence, start Docker Desktop and set:

```env
SANDBOX_BACKEND=docker
```

The normal TA verification path remains local and key-free.

## Final Report And Evidence

Key files:

- `docs/Project_Report_Final_EN.pdf`
- `docs/Project_Report_Final_EN.md`
- `docs/Project_Proposal_AutoForge.pdf`
- `docs/report/real_agent_evidence/README.md`
- `evaluation/results/eval_report_backend_full_20260501_060612.json`
- `evaluation/results/agent_demo_report_agent_20260502_074909.json`
- `evaluation/results/threshold_sweep_full_20260430_172632.json`

Figure and screenshot evidence:

- `docs/report/real_agent_evidence/figures/`
- `docs/report/real_agent_evidence/screenshots/`
- `docs/report/real_agent_evidence/docker_sandbox/`

## Notes On Scope

- The default app path is deterministic and can be validated without a paid API key.
- Real agent forging is optional because it consumes tokens and depends on external LLM availability.
- Vector retrieval is disabled by default to avoid first-run model downloads. Enable it with `AUTOFORGE_ENABLE_VECTOR_STORE=1`.
- `.env`, virtual environments, caches, runtime logs, and local ChromaDB state should not be committed.

