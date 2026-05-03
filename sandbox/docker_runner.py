from __future__ import annotations

import ast
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from shared.constants import SANDBOX_TIMEOUT_SECONDS
from shared.schemas import VerifierOutput


_BANNED_IMPORTS = {"os", "sys", "subprocess", "socket", "shutil", "pathlib"}
_BANNED_CALLS = {"open", "eval", "exec", "compile", "input", "__import__"}


def _detect_function_name(tree: ast.AST) -> Optional[str]:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            return node.name
    return None


def _find_banned_import(tree: ast.AST) -> Optional[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base = alias.name.split(".")[0]
                if base in _BANNED_IMPORTS:
                    return base
        elif isinstance(node, ast.ImportFrom) and node.module:
            base = node.module.split(".")[0]
            if base in _BANNED_IMPORTS:
                return base
    return None


def _find_banned_call(tree: ast.AST) -> Optional[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in _BANNED_CALLS:
                return func.id
    return None


def _parse_source(source_code: str) -> tuple[Optional[ast.AST], Optional[str]]:
    try:
        tree = ast.parse(source_code)
        return tree, None
    except SyntaxError as exc:
        return None, f"SyntaxError: {exc.msg} (line {exc.lineno})"


def _build_runner_script(function_name: Optional[str]) -> str:
    resolved_name = function_name or ""
    resolved_literal = repr(resolved_name)
    return (
        "import json\n"
        "import sys\n"
        "\n"
        "def _load_params():\n"
        "    try:\n"
        "        with open('input.json', 'r', encoding='utf-8') as f:\n"
        "            return json.load(f)\n"
        "    except FileNotFoundError:\n"
        "        return None\n"
        "\n"
        "def _resolve_function(params):\n"
        f"    default_name = {resolved_literal}\n"
        "    if isinstance(params, dict) and '__function_name' in params:\n"
        "        return params.pop('__function_name')\n"
        "    return default_name\n"
        "\n"
        "def _call(func, params):\n"
        "    if params is None:\n"
        "        return func()\n"
        "    if isinstance(params, dict):\n"
        "        if 'args' in params or 'kwargs' in params:\n"
        "            args = params.get('args', [])\n"
        "            kwargs = params.get('kwargs', {})\n"
        "            return func(*args, **kwargs)\n"
        "        return func(**params)\n"
        "    return func(params)\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    params = _load_params()\n"
        "    name = _resolve_function(params)\n"
        "    if not name:\n"
        "        print('No function name resolved', file=sys.stderr)\n"
        "        sys.exit(1)\n"
        "    func = globals().get(name)\n"
        "    if not callable(func):\n"
        "        print('No callable function found', file=sys.stderr)\n"
        "        sys.exit(1)\n"
        "    try:\n"
        "        result = _call(func, params)\n"
        "    except Exception:\n"
        "        import traceback\n"
        "        traceback.print_exc()\n"
        "        sys.exit(1)\n"
        "    if result is not None:\n"
        "        try:\n"
        "            json.dumps(result, ensure_ascii=False)\n"
        "        except TypeError as exc:\n"
        "            print(f'Non JSON serializable output: {exc}', file=sys.stderr)\n"
        "            sys.exit(1)\n"
        "        print(result)\n"
    )


class DockerRunner:
    def run(self, source_code: str, test_input: dict | None = None) -> VerifierOutput:
        tree, error = _parse_source(source_code)
        if error:
            return VerifierOutput(success=False, stderr=error, failure_type="syntax")

        banned = _find_banned_import(tree)
        if banned:
            return VerifierOutput(
                success=False,
                stderr=f"Security warning: '{banned}' is not allowed",
                failure_type="unsafe_import",
            )
        banned_call = _find_banned_call(tree)
        if banned_call:
            return VerifierOutput(
                success=False,
                stderr=f"Security warning: call to '{banned_call}' is not allowed",
                failure_type="unsafe_call",
            )

        function_name = _detect_function_name(tree)
        image = os.getenv("SANDBOX_DOCKER_IMAGE", "python:3.11-slim")

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                script_path = temp_path / "script.py"
                input_path = temp_path / "input.json"

                script_content = source_code
                if test_input is not None:
                    script_content = f"{source_code}\n\n{_build_runner_script(function_name)}"
                    try:
                        payload = json.dumps(test_input, ensure_ascii=False)
                    except TypeError as exc:
                        return VerifierOutput(
                            success=False,
                            stderr=f"Input JSON error: {exc}",
                            failure_type="non_json_serializable_input",
                        )
                    input_path.write_text(payload, encoding="utf-8")

                script_path.write_text(script_content, encoding="utf-8")

                result = subprocess.run(
                    [
                        "docker",
                        "run",
                        "--rm",
                        "--cpus",
                        "1.0",
                        "--memory",
                        "512m",
                        "--pids-limit",
                        "256",
                        "--read-only",
                        "-e",
                        "PYTHONUNBUFFERED=1",
                        "--network",
                        "none",
                        "-v",
                        f"{temp_path}:/tmp/autoforge",
                        "-w",
                        "/tmp/autoforge",
                        image,
                        "python",
                        "script.py",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=SANDBOX_TIMEOUT_SECONDS,
                )
                success = result.returncode == 0
                stderr = result.stderr or ""
                failure_type = None
                if not success:
                    lowered = stderr.lower()
                    if "missing" in lowered and "required positional argument" in lowered:
                        failure_type = "missing_required_param"
                    elif "unexpected keyword argument" in lowered:
                        failure_type = "invalid_param"
                    elif "non json serializable output" in lowered:
                        failure_type = "non_json_serializable_output"
                    else:
                        failure_type = "runtime"
                return VerifierOutput(
                    success=success,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    failure_type=failure_type,
                )
        except subprocess.TimeoutExpired:
            return VerifierOutput(success=False, stderr="Execution timed out", failure_type="timeout")
        except Exception as exc:  # pragma: no cover - safety net
            return VerifierOutput(success=False, stderr=str(exc), failure_type="sandbox_internal_error")
