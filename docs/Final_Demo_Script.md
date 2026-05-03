# AutoForge Final Demo Script

Last updated: 2026-05-01

This script is designed for the COMP7608A final project demonstration. The recommended presentation length is 8-12 minutes.

## 0. Environment Setup

```powershell
cd <path-to-cloned-repository>
$env:PYTHONPATH='.'
python -m pytest
.\scripts\start_backend.ps1
.\scripts\start_frontend.ps1
```

Optional MCP helper verification:

```powershell
$env:PYTHONPATH='.'
python scripts\verify_mcp_helpers.py
```

## 1. Opening: One-Sentence Project Summary

AutoForge is a self-evolving LLM agent system that can forge, verify, package, store, and reuse Python tools.

Core argument:

- A standard LLM often rewrites task-specific code from scratch.
- AutoForge turns successfully generated code into reusable tools.
- Warm queries can use the Tool-RAG fast path, reducing latency and token cost.

## 2. Demo A: Cold Forge

Goal: show that the agent slow path can generate a new reusable tool.

Example query:

```text
Create a reusable function that parses JSON lines and sums a numeric field.
```

Suggested evidence to show:

- Planner steps.
- Generated source code.
- Multi-case verifier output.
- Sandbox execution result.
- Packaged tool schema.
- Forge log `summary`.

Evidence files:

- `data/forge_logs/<trace_id>.json`
- `evaluation/results/agent_demo_report_*.json`

## 3. Demo B: Warm Reuse

Goal: show that a paraphrased query from the same family can reuse the forged tool.

Example query:

```text
Given these JSONL records, total the x field.
```

Suggested evidence to show:

- `path_taken = fast`
- `reused_existing_tool = true`
- `retrieval_trace`
- warm latency lower than cold forge latency

## 4. Demo C: Unsafe Code Rejection

Goal: show that automatic code execution has safety boundaries.

Example unsafe code:

```python
def unsafe() -> str:
    return open("README.md").read()
```

Suggested evidence to show:

- The sandbox rejects the unsafe call.
- `failure_type = unsafe_call`.
- Forge logs or test output include a clear failure reason.

## 5. Demo D: Evaluation Dashboard

Open the Streamlit dashboard and show:

- backend status
- benchmark design
- agent demo reports
- threshold sweep
- evaluation report comparison
- failure explorer

Key metrics to explain:

- success rate
- tool reuse rate / TRR
- error rate
- speedup ratio
- path distribution
- per-family success rate

## 6. Demo E: MCP/API Tool Server

Run:

```powershell
$env:PYTHONPATH='.'
python scripts\verify_mcp_helpers.py
```

Suggested evidence to show:

- catalog is non-empty
- direct invocation returns `tilmaerts`
- natural-language query returns `tilmaerts`

External MCP clients such as Claude Desktop or Cursor can be validated by following `docs/Reproducibility_Checklist.md`.

## 7. Closing: Course Topic Mapping

AutoForge maps to the following COMP7608A topics:

- LLM-powered agents.
- Tool use and API use.
- Retrieval-augmented generation.
- Code generation.
- LLM evaluation.
- Safety and sandboxing.
- Deployment through FastAPI/MCP.

Final conclusion:

AutoForge demonstrates how an LLM agent can evolve from answering one-off queries into building a reusable tool ecosystem.
