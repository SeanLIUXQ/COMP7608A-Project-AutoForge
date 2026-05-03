from __future__ import annotations

import ast
import json
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from typing import TypedDict

from langgraph.graph import END, StateGraph

from agents.coder import run_coder
from agents.packager import run_packager
from agents.planner import run_planner
from agents.verifier import run_verifier
from shared.constants import MAX_FORGE_RETRIES
from shared.schemas import CoderOutput, ForgeRequest, ForgeResult, PlannerOutput, ToolSchema, VerifierOutput


class ErrorType(str, Enum):
    MISSING_CODE = "missing_code"
    SYNTAX = "syntax"
    MISSING_FUNCTION = "missing_function"
    RUNTIME = "runtime"
    TIMEOUT = "timeout"
    UNSAFE_IMPORT = "unsafe_import"
    UNSAFE_CALL = "unsafe_call"
    MISSING_REQUIRED_PARAM = "missing_required_param"
    NON_JSON_SERIALIZABLE_OUTPUT = "non_json_serializable_output"
    INVALID_PARAM = "invalid_param"
    SANDBOX_INTERNAL_ERROR = "sandbox_internal_error"


class ForgeState(TypedDict, total=False):
    request: ForgeRequest
    plan: PlannerOutput
    code: CoderOutput
    verify: VerifierOutput
    tool: ToolSchema | None
    error: str | None
    retries: int
    error_type: ErrorType | None


def _planner_node(state: ForgeState) -> ForgeState:
    plan = run_planner(state["request"])
    return {"plan": plan}


def _coder_node(state: ForgeState) -> ForgeState:
    plan: PlannerOutput = state["plan"]
    previous_error = state.get("error")
    code = run_coder(plan, previous_error=previous_error)
    return {"code": code}


def _format_verification_error(error_type: ErrorType, message: str) -> str:
    return (
        f"error_type: {error_type.value}\n"
        f"message:\n{message.strip() or 'Verification failed'}\n\n"
        "Repair guidance:\n"
        "- Preserve the planned function name and signature intent.\n"
        "- Return a plain Python value instead of printing.\n"
        "- Avoid side effects and banned imports/calls.\n"
        "- Add input validation only where it improves clarity."
    )


def _verifier_node(state: ForgeState) -> ForgeState:
    code = state.get("code")
    if not code:
        retries = state.get("retries", 0) + 1
        return {
            "verify": VerifierOutput(success=False, stderr="Missing code in state"),
            "error": _format_verification_error(ErrorType.MISSING_CODE, "Missing code in state"),
            "retries": retries,
            "error_type": ErrorType.MISSING_CODE,
        }

    try:
        tree = ast.parse(code.source_code)
    except SyntaxError as exc:
        retries = state.get("retries", 0) + 1
        return {
            "verify": VerifierOutput(success=False, stderr=f"SyntaxError: {exc.msg} (line {exc.lineno})"),
            "error": _format_verification_error(
                ErrorType.SYNTAX,
                f"SyntaxError: {exc.msg} (line {exc.lineno})",
            ),
            "retries": retries,
            "error_type": ErrorType.SYNTAX,
        }

    if code.function_name:
        has_named = any(
            isinstance(node, ast.FunctionDef) and node.name == code.function_name for node in tree.body
        )
        if not has_named:
            retries = state.get("retries", 0) + 1
            return {
                "verify": VerifierOutput(
                    success=False,
                    stderr=f"Missing function '{code.function_name}' in generated code",
                ),
                "error": _format_verification_error(
                    ErrorType.MISSING_FUNCTION,
                    f"Missing function '{code.function_name}' in generated code",
                ),
                "retries": retries,
                "error_type": ErrorType.MISSING_FUNCTION,
            }

    result = run_verifier(code)
    updates = {"verify": result, "error": None}
    if not result.success:
        updates["retries"] = state.get("retries", 0) + 1
        raw_failure_type = result.failure_type or ""
        try:
            error_type = ErrorType(raw_failure_type)
        except ValueError:
            if result.stderr and "timed out" in result.stderr.lower():
                error_type = ErrorType.TIMEOUT
            else:
                error_type = ErrorType.RUNTIME
        updates["error_type"] = error_type
        updates["error"] = _format_verification_error(error_type, result.stderr or "Verification failed")
    return updates


def _packager_node(state: ForgeState) -> ForgeState:
    code = state.get("code")
    if not code:
        return {"tool": None, "error": "Missing code for packaging"}
    tool: ToolSchema = run_packager(code)
    return {"tool": tool, "error": None}


def _should_retry(state: ForgeState) -> str:
    verify = state.get("verify")
    if verify and verify.success:
        return "packager"
    if state.get("error_type") == ErrorType.TIMEOUT:
        return "fail"
    if state.get("retries", 0) >= MAX_FORGE_RETRIES:
        return "fail"
    return "coder"


def _fail_node(state: ForgeState) -> ForgeState:
    return {"tool": None}


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _build_log_summary(final_state: ForgeState, status: str, attempts: int) -> dict[str, Any]:
    plan = final_state.get("plan")
    code = final_state.get("code")
    verify = final_state.get("verify")
    tool = final_state.get("tool")
    verification_cases = verify.cases if verify else []
    failed_case = next((case for case in verification_cases if not case.get("success")), None)
    error_type = final_state.get("error_type")
    function_name = code.function_name if code else None
    if tool:
        function_name = tool.name

    if status == "success":
        headline = f"Forge succeeded for {function_name or 'generated tool'} after {attempts} attempt(s)."
    else:
        label = error_type.value if isinstance(error_type, ErrorType) else str(error_type or "unknown")
        headline = f"Forge failed after {attempts} attempt(s): {label}."

    return {
        "headline": headline,
        "function_name": function_name,
        "status": status,
        "attempts": attempts,
        "step_count": len(plan.steps) if plan else 0,
        "plan_steps": plan.steps if plan else [],
        "verification_case_count": len(verification_cases),
        "verification_passed": bool(verify and verify.success),
        "failure_type": _jsonable(error_type),
        "failure_message": final_state.get("error"),
        "failed_case": failed_case,
    }


def _write_forge_log(trace_id: str, request: ForgeRequest, final_state: ForgeState, status: str, attempts: int) -> str | None:
    log_dir = Path(os.getenv("AUTOFORGE_FORGE_LOG_DIR", "data/forge_logs"))
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "attempts": attempts,
            "summary": _build_log_summary(final_state, status, attempts),
            "request": request.model_dump(mode="json"),
            "plan": _jsonable(final_state.get("plan")),
            "source_code": final_state.get("code").source_code if final_state.get("code") else None,
            "function_name": final_state.get("code").function_name if final_state.get("code") else None,
            "verification": _jsonable(final_state.get("verify")),
            "error_type": _jsonable(final_state.get("error_type")),
            "error": final_state.get("error"),
            "tool": _jsonable(final_state.get("tool")),
        }
        path = log_dir / f"{trace_id}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)
    except Exception:
        return None


def run_forge_pipeline(request: ForgeRequest) -> ForgeResult:
    trace_id = uuid.uuid4().hex
    graph = StateGraph(ForgeState)
    graph.add_node("planner", _planner_node)
    graph.add_node("coder", _coder_node)
    graph.add_node("verifier", _verifier_node)
    graph.add_node("packager", _packager_node)
    graph.add_node("fail", _fail_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "coder")
    graph.add_edge("coder", "verifier")
    graph.add_conditional_edges("verifier", _should_retry)
    graph.add_edge("packager", END)
    graph.add_edge("fail", END)

    app = graph.compile()
    try:
        final_state = app.invoke({"request": request, "retries": 0})
    except Exception as exc:
        error_state: ForgeState = {"request": request, "error": str(exc), "retries": 0}
        log_path = _write_forge_log(trace_id, request, error_state, "failed", 0)
        return ForgeResult(status="failed", tool=None, error=str(exc), attempts=0, trace_id=trace_id, log_path=log_path)

    tool = final_state.get("tool")
    attempts = final_state.get("retries", 0) + 1 if tool else final_state.get("retries", 0)
    if tool:
        log_path = _write_forge_log(trace_id, request, final_state, "success", attempts)
        return ForgeResult(status="success", tool=tool, attempts=attempts, trace_id=trace_id, log_path=log_path)
    log_path = _write_forge_log(trace_id, request, final_state, "failed", attempts)
    return ForgeResult(
        status="failed",
        tool=None,
        error=final_state.get("error") or "Forge pipeline failed",
        attempts=attempts,
        trace_id=trace_id,
        log_path=log_path,
    )
