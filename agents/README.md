# Member1 (Agents & Sandbox)

This folder contains the core agent logic for AutoForge. The following Member1 tasks from the development guide are completed:

1. Sandbox layer:
   - `sandbox/docker_runner.py` (Docker execution, safety checks, timeouts)
   - `sandbox/executor.py` (public execution entrypoint)
2. Prompts:
   - `agents/prompts/planner_system.txt`
   - `agents/prompts/coder_system.txt`
   - `agents/prompts/verifier_system.txt`
3. Agents:
   - `agents/planner.py`
   - `agents/coder.py`
   - `agents/verifier.py`
   - `agents/packager.py`
4. Pipeline:
   - `agents/forge_pipeline.py` (LangGraph wiring with retry)
   - Forge logs include a `summary` object for report/frontend display.
5. Skill bundle output:
   - Bundles are written to `skills/<name>/` (or `skills/<name>__<id>` if name exists)
   - Includes `tool.py`, `schema.json`, `metadata.json`, `README.md`, `requirements.txt`, `example_input.json`
6. Tests and CLI:
   - `scripts/test_skill_bundle.py`
   - `scripts/test_forge_bundle_integration.py`
   - CLI supports `--run` and auto bundle creation

Quick local verification:

```bash
# Sandbox + pipeline smoke test
python scripts/smoke_test.py

# End-to-end forge + run
python scripts/forge_cli.py "Write a Python function that adds two integers" \
  --run --input '{"a":2,"b":3,"__function_name":"add_two_integers"}'
```

Skill bundle output:

```
skills/<name>/
  tool.py
  schema.json
  metadata.json
  README.md
  requirements.txt
  example_input.json
```

Verification:

```bash
python scripts/smoke_test.py
python scripts/test_skill_bundle.py
python scripts/test_forge_bundle_integration.py
```

Push to your branch (feature/name1-agents):

```bash
git checkout feature/name1-agents
git merge dev
git status
git add .
git commit -m "feat(member1): update agents README"
git push origin feature/name1-agents
```

Then open a PR from `feature/name1-agents` to `dev`. Do not push to `main`.

Notes:
- Docker Desktop must be running for sandbox execution.
- Set your API key in `.env` before running the pipeline.
- `agents/demo_cases.json` contains stable agent demo prompts and example payloads for string, list, JSON rows, CSV text, JSONL, moving average, category aggregation, and URL tasks.
- The verifier now runs multiple generated near-input cases and records per-case results in `VerifierOutput.cases`.
- Sandbox failures expose `failure_type` values such as `unsafe_import`, `unsafe_call`, `missing_required_param`, and `non_json_serializable_output`.
