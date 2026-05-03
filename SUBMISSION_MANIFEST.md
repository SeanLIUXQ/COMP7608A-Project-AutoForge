# Submission Manifest

This cleaned repository contains the files needed to run, verify, and review AutoForge.

## Core System

- `agents/`: Planner, Coder, Verifier, Packager, prompts, and forge pipeline.
- `backend/`: FastAPI service, query strategies, tool registry, dynamic routes, MCP helper.
- `frontend/`: Streamlit pages for Home, Chat, Tool Browser, and Dashboard.
- `retrieval/`: Tool-RAG retrieval wrapper.
- `sandbox/`: Local and Docker sandbox execution.
- `shared/`: Shared schemas, constants, LLM factory.
- `skills/`: Seeded tool bundles for key-free deterministic verification.

## Verification

- `setup_and_verify.ps1`: one-command setup and validation.
- `requirements.txt`: Python dependencies.
- `tests/`: pytest suite.
- `scripts/smoke_test.py`: local sandbox and forge smoke test.
- `scripts/verify_mcp_helpers.py`: MCP helper verification.
- `evaluation/benchmark/dataset.json`: 80 canonical tasks and 240 paraphrases.

## Report And Evidence

- `docs/Project_Report_AutoForge.pdf`: final project report.
- `docs/Project_Report_Final_EN.md`: report source text.
- `docs/Project_Proposal_AutoForge.pdf`: original project proposal.
- `evaluation/results/`: selected final benchmark and real-agent result JSON files.
- `docs/report/real_agent_evidence/`: real DeepSeek agent evidence, figures, screenshots, Docker sandbox evidence, and generated-tool traces.

## Not Included

- Real `.env` secrets.
- Virtual environments, caches, local ChromaDB state, runtime logs.
- Older draft notes and temporary debugging folders from development.

