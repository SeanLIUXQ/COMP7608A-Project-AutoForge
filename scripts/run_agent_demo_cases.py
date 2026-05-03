from __future__ import annotations

import argparse
import ast
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.service import AutoForgeBackendService
from backend.tool_registry import ToolRegistry
from sandbox.executor import execute_code
from shared.schemas import QueryRequest


def _load_cases(path: str) -> list[dict[str, Any]]:
    cases = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError("Agent demo cases must be a JSON array")
    return cases


def _write_report(
    *,
    path: Path,
    mode: str,
    cases_path: str,
    rows: list[dict[str, Any]],
    started: float,
    base_case_count: int,
    repeats: int,
    partial: bool = False,
) -> dict[str, Any]:
    total = max(1, len(rows))
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "cases_path": cases_path,
        "base_case_count": base_case_count,
        "repeats": repeats,
        "total_cases": len(rows),
        "cold_success_count": sum(1 for row in rows if row["cold_success"]),
        "cold_example_success_count": sum(1 for row in rows if row["cold_example_success"]),
        "warm_success_count": sum(1 for row in rows if row["warm_success"]),
        "warm_reuse_count": sum(1 for row in rows if row["warm_reused_existing_tool"]),
        "cold_success_rate": round(sum(1 for row in rows if row["cold_success"]) / total, 4),
        "cold_example_success_rate": round(sum(1 for row in rows if row["cold_example_success"]) / total, 4),
        "warm_success_rate": round(sum(1 for row in rows if row["warm_success"]) / total, 4),
        "warm_reuse_rate": round(sum(1 for row in rows if row["warm_reused_existing_tool"]) / total, 4),
        "duration_seconds": round(time.monotonic() - started, 3),
        "partial": partial,
        "results": rows,
        "report_path": str(path),
    }
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def _load_checkpoint_rows(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    checkpoint_path = Path(path)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Resume checkpoint not found: {checkpoint_path}")
    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    rows = payload.get("results", [])
    if not isinstance(rows, list):
        raise ValueError(f"Resume checkpoint has no result rows: {checkpoint_path}")
    return [row for row in rows if isinstance(row, dict)]


def _case_payload(case: dict[str, Any], *, function_name: str | None = None) -> dict[str, Any]:
    payload = dict(case.get("example_payload") or {})
    if function_name:
        payload["__function_name"] = function_name
    return payload


def _payload_without_function(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "__function_name"}


def _warm_query(case: dict[str, Any], *, tool_name: str | None = None) -> str:
    payload = _payload_without_function(_case_payload(case))
    function_name = tool_name or str(case.get("example_payload", {}).get("__function_name") or "generated_tool")
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # Keep the generated function name as the only intent token before the JSON payload.
    # Retrieval strips JSON literals, so this makes warm reuse focus on the forged tool name.
    return f"{function_name}: {payload_json}"


def _mock_response(case: dict[str, Any], *, phase: str) -> dict[str, Any]:
    tool_name = str(case.get("example_payload", {}).get("__function_name") or f"{case.get('family', 'demo')}_tool")
    trace_id = f"mock_{case['id']}_{phase}"
    if phase == "cold":
        return {
            "path_taken": "slow",
            "result": case.get("expected_output"),
            "tool_id": f"mock-{case['id']}",
            "tool_name": tool_name,
            "strategy": "agent",
            "reused_existing_tool": False,
            "forge_latency_ms": 500.0,
            "execution_latency_ms": 20.0,
            "total_latency_ms": 540.0,
            "forge_trace_id": trace_id,
            "forge_log_path": f"data/forge_logs/{trace_id}.json",
            "forge_summary": {
                "status": "success",
                "function_name": tool_name,
                "verification_case_count": 3,
                "failure_type": None,
            },
            "error": None,
        }
    return {
        "path_taken": "fast",
        "result": case.get("expected_output"),
        "tool_id": f"mock-{case['id']}",
        "tool_name": tool_name,
        "strategy": "full",
        "reused_existing_tool": True,
        "retrieval_latency_ms": 8.0,
        "execution_latency_ms": 12.0,
        "total_latency_ms": 25.0,
        "search_score": 0.91,
        "retrieval_trace": [
            {
                "rank": 1,
                "tool_id": f"mock-{case['id']}",
                "tool_name": tool_name,
                "score": 0.91,
                "accepted": True,
                "reason": "accepted",
            }
        ],
        "error": None,
    }


def _service_response(service: AutoForgeBackendService, query: str, strategy: str) -> dict[str, Any]:
    response = service.handle_query(QueryRequest(query=query, strategy=strategy))
    return response.model_dump(mode="json")


def _is_success(payload: dict[str, Any], expected: Any) -> bool:
    return payload.get("error") is None and payload.get("result") == expected


def _parse_stdout(stdout: str | None) -> Any:
    text = (stdout or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        return ast.literal_eval(text)
    except Exception:
        return text


def _verify_forged_tool_example(
    service: AutoForgeBackendService,
    *,
    tool_id: str | None,
    case: dict[str, Any],
    expected: Any,
) -> dict[str, Any]:
    if not tool_id:
        return {"success": False, "result": None, "error": "No forged tool_id returned"}
    lookup = service.registry.get_tool(tool_id)
    if not lookup:
        return {"success": False, "result": None, "error": f"Forged tool {tool_id} was not found in registry"}

    tool, _bundle_dir = lookup
    payload = _case_payload(case, function_name=tool.name)
    started = time.monotonic()
    execution = execute_code(tool.source_code, payload)
    latency_ms = (time.monotonic() - started) * 1000
    actual = _parse_stdout(execution.stdout)
    error = execution.stderr if not execution.success else None
    return {
        "success": execution.success and actual == expected,
        "result": actual,
        "error": error,
        "execution_success": execution.success,
        "execution_latency_ms": latency_ms,
        "failure_type": execution.failure_type,
        "payload": payload,
    }


def run_agent_demo_cases(
    *,
    cases_path: str,
    output_dir: str,
    mock: bool = False,
    limit: int | None = None,
    skills_dir: str = "skills",
    checkpoint_interval: int = 0,
    repeats: int = 1,
    resume_from: str | None = None,
) -> dict[str, Any]:
    if repeats < 1:
        raise ValueError("repeats must be at least 1")

    cases = _load_cases(cases_path)
    if limit is not None:
        cases = cases[:limit]
    base_case_count = len(cases)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    mode = "mock" if mock else "agent"
    checkpoint_path = output_path / f"agent_demo_report_{mode}_checkpoint.json"

    service: AutoForgeBackendService | None = None
    if not mock:
        registry = ToolRegistry(skills_dir=skills_dir, enable_vector_store=False)
        service = AutoForgeBackendService(registry=registry, enable_agent_slow_path=True)
        service.sync()

    started = time.monotonic()
    rows: list[dict[str, Any]] = _load_checkpoint_rows(resume_from)
    trial_index = len(rows)
    for repeat_index in range(1, repeats + 1):
        for case in cases:
            if trial_index >= repeat_index * base_case_count:
                continue
            trial_index += 1
            row = _run_single_case(
                case=case,
                service=service,
                mock=mock,
            )
            row["base_case_id"] = case.get("id")
            row["id"] = f"{case.get('id')}__r{repeat_index:02d}" if repeats > 1 else case.get("id")
            row["repeat_index"] = repeat_index
            row["trial_index"] = trial_index
            rows.append(row)

            if checkpoint_interval > 0 and len(rows) % checkpoint_interval == 0:
                _write_report(
                    path=checkpoint_path,
                    mode=mode,
                    cases_path=cases_path,
                    rows=rows,
                    started=started,
                    base_case_count=base_case_count,
                    repeats=repeats,
                    partial=True,
                )

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_file = output_path / f"agent_demo_report_{mode}_{ts}.json"
    return _write_report(
        path=out_file,
        mode=mode,
        cases_path=cases_path,
        rows=rows,
        started=started,
        base_case_count=base_case_count,
        repeats=repeats,
        partial=False,
    )


def _run_single_case(
    *,
    case: dict[str, Any],
    service: AutoForgeBackendService | None,
    mock: bool,
) -> dict[str, Any]:
    cold_query = str(case["query"])
    expected = case.get("expected_output")

    if mock:
        warm_query = _warm_query(case)
        cold = _mock_response(case, phase="cold")
        warm = _mock_response(case, phase="warm")
        forge_success = _is_success(cold, expected)
        cold_example = {
            "success": _is_success(cold, expected),
            "result": cold.get("result"),
            "error": cold.get("error"),
            "payload": _case_payload(case),
        }
    else:
        assert service is not None
        cold = _service_response(service, cold_query, "agent")
        forge_summary = cold.get("forge_summary") or {}
        forge_success = (
            forge_summary.get("status") == "success"
            and bool(forge_summary.get("verification_passed"))
        )
        cold_example = _verify_forged_tool_example(
            service,
            tool_id=cold.get("tool_id"),
            case=case,
            expected=expected,
        )
        warm_query = _warm_query(case, tool_name=str(cold.get("tool_name") or "generated_tool"))
        warm = _service_response(service, warm_query, "full")

    return {
        "id": case.get("id"),
        "family": case.get("family"),
        "cold_query": cold_query,
        "warm_query": warm_query,
        "expected_output": expected,
        "cold_success": bool(forge_success),
        "cold_example_success": bool(cold_example.get("success")),
        "cold_example_result": cold_example.get("result"),
        "cold_example_error": cold_example.get("error"),
        "cold_example_payload": cold_example.get("payload"),
        "warm_success": _is_success(warm, expected),
        "warm_reused_existing_tool": bool(warm.get("reused_existing_tool")),
        "cold_path_taken": cold.get("path_taken"),
        "warm_path_taken": warm.get("path_taken"),
        "tool_id": cold.get("tool_id") or warm.get("tool_id"),
        "tool_name": cold.get("tool_name") or warm.get("tool_name"),
        "forge_trace_id": cold.get("forge_trace_id"),
        "forge_log_path": cold.get("forge_log_path"),
        "forge_summary": cold.get("forge_summary"),
        "failure_type": cold.get("failure_type")
        or (cold.get("forge_summary") or {}).get("failure_type")
        or warm.get("failure_type"),
        "cold_error": cold.get("error"),
        "warm_error": warm.get("error"),
        "cold_total_latency_ms": cold.get("total_latency_ms"),
        "warm_total_latency_ms": warm.get("total_latency_ms"),
        "cold_response": cold,
        "warm_response": warm,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AutoForge agent demo cases and save a cold/warm report.")
    parser.add_argument("--cases", default="agents/demo_cases.json", help="Agent demo cases JSON path")
    parser.add_argument("--output-dir", default="evaluation/results", help="Output directory")
    parser.add_argument("--mock", action="store_true", help="Generate deterministic local mock report without LLM")
    parser.add_argument("--limit", type=int, default=None, help="Optional max cases to run")
    parser.add_argument("--skills-dir", default="skills", help="Skill registry directory for real agent runs")
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=0,
        help="Write a partial checkpoint report every N completed cases",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Repeat the selected case set N times; --limit 10 --repeats 5 yields 50 trials",
    )
    parser.add_argument(
        "--resume-from",
        default=None,
        help="Resume from an existing agent demo checkpoint/report JSON and append remaining trials",
    )
    args = parser.parse_args()

    report = run_agent_demo_cases(
        cases_path=args.cases,
        output_dir=args.output_dir,
        mock=args.mock,
        limit=args.limit,
        skills_dir=args.skills_dir,
        checkpoint_interval=args.checkpoint_interval,
        repeats=args.repeats,
        resume_from=args.resume_from,
    )
    print(f"Agent demo report saved to {report['report_path']}")
    print(f"Cold success: {report['cold_success_count']}/{report['total_cases']}")
    print(f"Cold example success: {report['cold_example_success_count']}/{report['total_cases']}")
    print(f"Warm reuse: {report['warm_reuse_count']}/{report['total_cases']}")


if __name__ == "__main__":
    main()
