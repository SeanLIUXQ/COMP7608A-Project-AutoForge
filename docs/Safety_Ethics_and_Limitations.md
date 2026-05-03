# AutoForge Safety, Ethics, and Limitations

Last updated: 2026-05-01

## Safety Risks

AutoForge generates and executes code, so it must handle:

- unsafe imports such as `os`, `sys`, `subprocess`, `socket`, `shutil`, and `pathlib`
- unsafe calls such as `open`, `eval`, `exec`, `compile`, `input`, and `__import__`
- infinite loops
- non-JSON-serializable outputs
- malformed function signatures
- prompt injection attempts that ask the agent to bypass safety constraints

## Current Mitigations

Implemented mitigations:

- local subprocess execution
- timeout via `SANDBOX_TIMEOUT_SECONDS`
- restricted built-ins in the local sandbox
- optional Docker sandbox with a read-only filesystem and no network
- static AST checks for banned imports and calls
- machine-readable `failure_type`
- forge log `summary`
- verification cases in `VerifierOutput.cases`

Failure types include:

- `unsafe_import`
- `unsafe_call`
- `missing_required_param`
- `invalid_param`
- `non_json_serializable_output`
- `timeout`
- `sandbox_internal_error`

## Ethics and Privacy

Potential concerns:

- Forge logs may store user queries and input payloads.
- Generated tools may encode incorrect assumptions from prompts.
- Users may overtrust generated tools because they are exposed as APIs.
- Reused tools can silently produce wrong results if retrieval selects an unsuitable tool.

Recommended safeguards:

- Avoid logging sensitive production data.
- Include trace IDs and tool origins in responses.
- Keep human review for promoted tools.
- Use evaluation reports to monitor false reuse and failures.
- Clearly label generated tools as `forged`.

## Limitations

Current limitations:

- `strategy=agent` depends on external LLM quality and API availability.
- The local sandbox is not a complete security boundary.
- The benchmark focuses on deterministic text/data tasks, not complex external APIs.
- External MCP client verification still requires manual setup.
- Fine-tuning and multimodal extensions are future work unless separately implemented.

## Demo Evidence

Recommended final demo safety case:

```python
def unsafe() -> str:
    return open("README.md").read()
```

Expected result:

- The sandbox rejects the call.
- `failure_type = unsafe_call`.
- Forge/test output includes an explicit failure reason.
