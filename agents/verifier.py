from __future__ import annotations

import ast
import json
from typing import Any

from sandbox.executor import execute_code
from shared.schemas import CoderOutput, VerifierOutput


def _annotation_name(node: ast.AST | None) -> str:
    if node is None:
        return "str"
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Constant) and node.value is None:
        return "None"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = _annotation_name(node.left)
        return _annotation_name(node.right) if left == "None" else left
    if isinstance(node, ast.Subscript):
        return _annotation_name(node.value)
    return "str"


def _sample_value(annotation: ast.AST | None) -> Any:
    name = _annotation_name(annotation).lower()
    if name in {"int", "integer"}:
        return 1
    if name in {"float", "number"}:
        return 1.0
    if name in {"bool", "boolean"}:
        return True
    if name in {"list", "sequence", "tuple", "set"}:
        return [1, 2, 3]
    if name in {"dict", "mapping"}:
        return {"value": 1}
    return "example"


def _variant_values(annotation: ast.AST | None) -> list[Any]:
    name = _annotation_name(annotation).lower()
    if name in {"int", "integer"}:
        return [1, 2, 0]
    if name in {"float", "number"}:
        return [1.0, 2.5, 0.0]
    if name in {"bool", "boolean"}:
        return [True, False, True]
    if name in {"list", "sequence", "tuple", "set"}:
        return [[1, 2, 3], [3, 1, 2], [0]]
    if name in {"dict", "mapping"}:
        return [{"value": 1}, {"items": [1, 2]}, {"value": 0}]
    return ["example", "nearby input", ""]


def _variant_values_for_arg(arg_name: str, annotation: ast.AST | None) -> list[Any]:
    """Generate verifier inputs that are generic but plausible for common tool arguments."""
    name = arg_name.lower()
    if "csv" in name:
        return [
            "name,score\nAda,91\nBen,72\nCy,88",
            "name,score\nA,1\nB,3",
            "name,score\nZero,0",
        ]
    if name in {"lines", "json_lines", "jsonl_lines"} or "jsonl" in name:
        return [
            ['{"x": 1}', '{"x": 2}', '{"x": 4}'],
            ['{"score": 2}', '{"score": 5}'],
            ['{"amt": 3}', '{"amt": 7}'],
        ]
    if name in {"rows", "records", "items"} or "rows" in name or "records" in name:
        return [
            [
                {"name": "Ada", "score": 91, "cat": "infra", "amt": 18, "category": "infra", "amount": 18},
                {"name": "Ben", "score": 72, "cat": "ml", "amt": 32, "category": "ml", "amount": 32},
                {"name": "Cy", "score": 88, "cat": "infra", "amt": 22, "category": "infra", "amount": 22},
            ],
            [
                {"name": "A", "score": 1, "cat": "ops", "amt": 1, "category": "ops", "amount": 1},
                {"name": "B", "score": 3, "cat": "ops", "amt": 2, "category": "ops", "amount": 2},
            ],
            [],
        ]
    if name in {"values", "numbers", "series", "data"} or "values" in name or "numbers" in name:
        return [[5, 1, 9, 2], [1, 2, 2, 3, 1, 4], [10.0, 11.0, 12.0, 13.0]]
    if name in {"iterable", "sequence"}:
        return [[1, 2, 2, 3, 1, 4], ["a", "b", "a"], []]
    if name in {"window", "window_size", "period"}:
        return [3, 2, 1]
    if "threshold" in name:
        return [80, 1, 0]
    if name in {"field", "field_name", "value_field"}:
        return ["x", "score", "amt"]
    if name in {"category_field", "group_field"}:
        return ["cat", "category", "group"]
    if name in {"name_field"}:
        return ["name", "label", "id"]
    if name in {"score_field"}:
        return ["score", "value", "points"]
    if name in {"amount_field"}:
        return ["amt", "amount", "value"]
    if name == "text" or "text" in name:
        return ["AutoForge", "streamlit dashboard", ""]
    if name == "url" or "url" in name:
        return [
            "https://demo.org/report?day=mon&owner=alex&status=open",
            "https://demo.org/search?page=2&sort=desc",
            "https://demo.org/",
        ]
    return _variant_values(annotation)


def _extract_function(source_code: str, function_name: str | None) -> ast.FunctionDef | None:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and (function_name is None or node.name == function_name):
            return node
    return None


def _required_args(func: ast.FunctionDef) -> list[ast.arg]:
    positional_args = [arg for arg in func.args.args if arg.arg != "self"]
    defaults_offset = len(positional_args) - len(func.args.defaults)
    required = [
        arg
        for index, arg in enumerate(positional_args)
        if index < defaults_offset
    ]
    required.extend(arg for arg, default in zip(func.args.kwonlyargs, func.args.kw_defaults) if default is None)
    return required


def build_verification_inputs(coder_output: CoderOutput, case_count: int = 3) -> list[dict[str, Any]]:
    func = _extract_function(coder_output.source_code, coder_output.function_name)
    if not func:
        return []

    required = _required_args(func)
    inputs: list[dict[str, Any]] = []
    for case_index in range(max(1, case_count)):
        payload: dict[str, Any] = {"__function_name": func.name}
        for arg in required:
            variants = _variant_values_for_arg(arg.arg, arg.annotation)
            payload[arg.arg] = variants[case_index % len(variants)]
        inputs.append(payload)
    return inputs


def build_verification_input(coder_output: CoderOutput) -> dict[str, Any] | None:
    inputs = build_verification_inputs(coder_output, case_count=1)
    return inputs[0] if inputs else None


def _json_load_output(stdout: str | None) -> Any:
    text = (stdout or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return text


def run_verifier(coder_output: CoderOutput) -> VerifierOutput:
    verification_inputs = build_verification_inputs(coder_output, case_count=3)
    if not verification_inputs:
        return VerifierOutput(
            success=False,
            stderr="No function found for verification",
            failure_type="missing_function",
        )

    cases: list[dict[str, Any]] = []
    total_time = 0.0
    for index, verification_input in enumerate(verification_inputs, start=1):
        result = execute_code(coder_output.source_code, verification_input)
        total_time += result.execution_time_ms or 0.0
        case_payload = {
            "case": index,
            "input": verification_input,
            "success": result.success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "failure_type": result.failure_type,
            "result": _json_load_output(result.stdout),
        }
        cases.append(case_payload)
        if not result.success:
            return VerifierOutput(
                success=False,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time_ms=total_time,
                failure_type=result.failure_type or "runtime",
                cases=cases,
            )

    last = cases[-1]
    return VerifierOutput(
        success=True,
        stdout=last.get("stdout") or "",
        stderr="",
        execution_time_ms=total_time,
        cases=cases,
    )
