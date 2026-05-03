from __future__ import annotations

import json
from pathlib import Path

import agents.forge_pipeline as forge_pipeline
from agents.verifier import build_verification_input, build_verification_inputs, run_verifier
from agents.packager import run_packager
from shared.schemas import CoderOutput, ForgeRequest, PlannerOutput


def test_run_packager_extracts_function_signature() -> None:
    coder_output = CoderOutput(
        source_code=(
            "def add_two_integers(a: int, b: int = 1) -> int:\n"
            "    \"\"\"Return the sum of two integers.\"\"\"\n"
            "    return a + b\n"
        ),
        function_name="add_two_integers",
    )
    tool = run_packager(coder_output)
    assert tool.name == "add_two_integers"
    assert tool.description == "Return the sum of two integers."
    assert [param.name for param in tool.parameters] == ["a", "b"]
    assert [param.required for param in tool.parameters] == [True, False]


def test_run_packager_handles_modern_type_annotations() -> None:
    coder_output = CoderOutput(
        source_code=(
            "def normalize(values: list[int], label: str | None = None) -> dict:\n"
            "    \"\"\"Normalize a list of integer values.\"\"\"\n"
            "    return {'label': label, 'values': values}\n"
        ),
        function_name="normalize",
    )
    tool = run_packager(coder_output)
    assert [param.name for param in tool.parameters] == ["values", "label"]
    assert [param.type for param in tool.parameters] == ["array", "string"]
    assert [param.required for param in tool.parameters] == [True, False]


def test_verifier_builds_sample_input_from_signature() -> None:
    coder_output = CoderOutput(
        source_code=(
            "def summarize(values: list[int], label: str) -> dict:\n"
            "    \"\"\"Summarize values with a label.\"\"\"\n"
            "    return {'label': label, 'count': len(values)}\n"
        ),
        function_name="summarize",
    )
    payload = build_verification_input(coder_output)
    assert payload == {"__function_name": "summarize", "values": [5, 1, 9, 2], "label": "example"}
    result = run_verifier(coder_output)
    assert result.success is True
    assert len(result.cases) == 3
    assert all(case["success"] is True for case in result.cases)


def test_verifier_builds_nearby_inputs_from_signature() -> None:
    coder_output = CoderOutput(
        source_code=(
            "def normalize_count(values: list[int], label: str) -> dict:\n"
            "    \"\"\"Return a reusable count payload.\"\"\"\n"
            "    return {'label': label, 'count': len(values)}\n"
        ),
        function_name="normalize_count",
    )
    payloads = build_verification_inputs(coder_output)
    assert len(payloads) == 3
    assert {payload["label"] for payload in payloads} == {"example", "nearby input", ""}
    assert payloads[0]["values"] != payloads[1]["values"]


def test_forge_pipeline_writes_trace_log(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AUTOFORGE_FORGE_LOG_DIR", str(tmp_path / "forge_logs"))

    monkeypatch.setattr(
        forge_pipeline,
        "run_planner",
        lambda _request: PlannerOutput(
            steps=["Validate text", "Reverse text", "Return result"],
            suggested_function_name="reverse_text",
        ),
    )
    monkeypatch.setattr(
        forge_pipeline,
        "run_coder",
        lambda _plan, previous_error=None: CoderOutput(
            source_code=(
                "def reverse_text(text: str) -> str:\n"
                "    \"\"\"Return the input text reversed.\"\"\"\n"
                "    return text[::-1]\n"
            ),
            function_name="reverse_text",
        ),
    )

    result = forge_pipeline.run_forge_pipeline(ForgeRequest(query="Reverse text"))
    assert result.status == "success"
    assert result.trace_id
    assert result.log_path

    payload = json.loads((tmp_path / "forge_logs" / f"{result.trace_id}.json").read_text(encoding="utf-8"))
    assert payload["status"] == "success"
    assert payload["attempts"] == 1
    assert payload["function_name"] == "reverse_text"
    assert payload["verification"]["success"] is True
    assert payload["summary"]["status"] == "success"
    assert payload["summary"]["verification_case_count"] == 3
    assert payload["summary"]["function_name"] == "reverse_text"


def test_forge_pipeline_log_summary_captures_failure_type(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AUTOFORGE_FORGE_LOG_DIR", str(tmp_path / "forge_logs"))
    monkeypatch.setattr(
        forge_pipeline,
        "run_planner",
        lambda _request: PlannerOutput(
            steps=["Create unsafe function"],
            suggested_function_name="unsafe_read",
        ),
    )
    monkeypatch.setattr(
        forge_pipeline,
        "run_coder",
        lambda _plan, previous_error=None: CoderOutput(
            source_code=(
                "def unsafe_read(text: str) -> str:\n"
                "    \"\"\"Try to read a file unsafely.\"\"\"\n"
                "    return open(text).read()\n"
            ),
            function_name="unsafe_read",
        ),
    )

    result = forge_pipeline.run_forge_pipeline(ForgeRequest(query="Read a file"))
    assert result.status == "failed"
    assert result.log_path
    payload = json.loads(Path(result.log_path).read_text(encoding="utf-8"))
    assert payload["summary"]["status"] == "failed"
    assert payload["summary"]["failure_type"] == "unsafe_call"
    assert payload["verification"]["failure_type"] == "unsafe_call"


def test_agent_demo_cases_cover_required_families() -> None:
    demo_cases = json.loads(Path("agents/demo_cases.json").read_text(encoding="utf-8"))
    families = {case["family"] for case in demo_cases}
    assert len(demo_cases) >= 8
    assert {
        "string",
        "list",
        "json_rows",
        "csv_text",
        "jsonl",
        "moving_average",
        "category_aggregation",
    }.issubset(families)
    assert all("query" in case and "example_payload" in case for case in demo_cases)
