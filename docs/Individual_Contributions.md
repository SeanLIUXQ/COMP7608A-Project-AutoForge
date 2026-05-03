# AutoForge Individual Contributions

Last updated: 2026-05-01

This document summarizes the main responsibilities of each member in the COMP7608A group project.

## Liu Xinquan: Project Lead, Agent Logic, and Algorithms

Responsible modules:

- `agents/planner.py`
- `agents/coder.py`
- `agents/verifier.py`
- `agents/packager.py`
- `agents/forge_pipeline.py`
- `agents/prompts/`
- `agents/demo_cases.json`
- `sandbox/local_runner.py`
- `sandbox/docker_runner.py`
- `tests/test_agents.py`
- `tests/test_sandbox.py`

Main contributions:

- Led the overall project integration and coordinated the real LLM agent experiment design.
- Designed the Planner/Coder/Verifier/Packager multi-agent tool-forging pipeline.
- Added benchmark- and fallback-oriented task-family patterns to the agent prompts.
- Implemented multi-case verification and recorded `VerifierOutput.cases`.
- Added sandbox `failure_type` coverage for unsafe imports/calls, missing parameters, non-JSON-serializable outputs, and timeouts.
- Added readable `summary` fields to forge logs.
- Prepared stable agent demo cases and real DeepSeek-based agent evidence.

Report materials:

- agent architecture
- cold forge / warm reuse sequence
- Docker sandbox evidence
- sandbox safety analysis
- failure type analysis
- representative forge logs

## Cheung Yu Lung: Backend, Tool-RAG, and MCP

Responsible modules:

- `backend/service.py`
- `backend/tool_registry.py`
- `backend/dynamic_api.py`
- `backend/endpoints/`
- `backend/mcp/server.py`
- `retrieval/`
- `scripts/threshold_sweep.py`
- `scripts/verify_mcp_helpers.py`
- `tests/test_backend_api.py`
- `tests/test_retrieval.py`

Main contributions:

- Implemented query strategies: `full`, `no_retrieval`, `registry_only`, and `agent`.
- Implemented Tool-RAG retrieval and `retrieval_trace`.
- Exposed tool lifecycle metadata, including seeded/forged status and versioning.
- Supported `explain_only` and `dry_run` query modes.
- Implemented MCP-compatible catalog, direct invocation, and natural-language query helpers.
- Produced threshold-sweep and MCP helper verification evidence.

Report materials:

- Tool-RAG design
- threshold sweep table
- retrieval trace examples
- MCP integration evidence
- backend API design

## Lyu Linze: Frontend, Data, and Evaluation

Responsible modules:

- `frontend/app.py`
- `frontend/pages/chat.py`
- `frontend/pages/tool_browser.py`
- `frontend/pages/dashboard.py`
- `evaluation/benchmark/dataset.json`
- `evaluation/runner.py`
- `evaluation/metrics.py`
- `evaluation/judge.py`
- `scripts/benchmark_dataset_tools.py`
- `scripts/build_final_report_assets.py`
- `tests/test_evaluation.py`

Main contributions:

- Built the Streamlit UI, including Chat, Tool Browser, and Dashboard views.
- Maintained the benchmark dataset with 80 canonical samples, 240 paraphrases, and 17 tool families.
- Implemented cold/warm protocol evaluation.
- Implemented report comparison, failure explorer, agent demo report, and threshold sweep dashboard views.
- Generated final report assets, including the metrics table, failure taxonomy, representative cases, and run manifest.

Report materials:

- benchmark design
- evaluation protocol
- dashboard screenshots
- strategy comparison charts
- failure analysis

## Final Integration Contributions

The team jointly completed:

- final demo script
- reproducibility checklist
- final report writing
- live demo rehearsal
- results interpretation
- limitations and future-work discussion
