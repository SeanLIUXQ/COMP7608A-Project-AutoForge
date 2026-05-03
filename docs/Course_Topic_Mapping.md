# AutoForge Mapping to COMP7608A Course Topics

Last updated: 2026-05-01

## LLM-Powered Agents

AutoForge uses a multi-agent pipeline:

- Planner: decomposes a natural-language request.
- Coder: generates a reusable Python function.
- Verifier: executes generated code in a sandbox with multiple near-input cases.
- Packager: extracts schema and metadata for later tool use.

Course connection:

- autonomous reasoning
- tool use
- code generation
- agentic workflow orchestration

## Retrieval-Augmented Generation

AutoForge uses Tool-RAG rather than document RAG. It retrieves tool capabilities from a registry and decides whether to call an existing tool or forge a new one.

Course connection:

- retrieval as external memory
- semantic/lexical retrieval
- grounding LLM behavior in reusable artifacts

## Training / Instruction Tuning Evidence

AutoForge includes:

- prompt few-shot task-family patterns
- `scripts/generate_instruction_dataset.py`
- `evaluation/llm_instruction_dataset.jsonl`

These artifacts show how planner/coder behavior can be improved with instruction examples.

Course connection:

- instruction-tuning data format
- prompt improvement through examples
- future LoRA/SFT extension

## LLM Evaluation

AutoForge evaluates:

- success rate
- tool reuse rate / TRR
- latency and speedup
- path distribution
- per-family metrics
- failure taxonomy
- threshold sweep

Course connection:

- quantitative evaluation
- ablation and baseline comparison
- error analysis

## Safety and Ethics

AutoForge mitigates generated-code risks through:

- restricted built-ins
- unsafe import/call detection
- timeout
- optional Docker sandbox
- failure type logging

Course connection:

- safe deployment of LLM systems
- risks of autonomous tool use
- accountability through logs and trace IDs

## Deployment and External Tool Use

AutoForge exposes tools through:

- FastAPI
- dynamic routes
- MCP-compatible helpers
- Streamlit dashboard

Course connection:

- deploying LLM-powered systems
- integrating LLMs with APIs and external tools
- real-world agent infrastructure
