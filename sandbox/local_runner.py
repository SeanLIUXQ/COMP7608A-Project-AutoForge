from __future__ import annotations

import builtins
import json
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

from sandbox.docker_runner import _detect_function_name, _find_banned_call, _find_banned_import, _parse_source
from shared.constants import SANDBOX_TIMEOUT_SECONDS
from shared.schemas import VerifierOutput


_SAFE_BUILTIN_NAMES = {
    "abs",
    "all",
    "any",
    "bool",
    "dict",
    "enumerate",
    "filter",
    "float",
    "int",
    "isinstance",
    "len",
    "list",
    "map",
    "max",
    "min",
    "pow",
    "print",
    "range",
    "round",
    "set",
    "sorted",
    "str",
    "sum",
    "tuple",
    "zip",
    "ValueError",
    "TypeError",
    "Exception",
}
_BANNED_IMPORT_MODULES = {"os", "sys", "subprocess", "socket", "shutil", "pathlib"}


def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    base = str(name).split(".", 1)[0]
    if base in _BANNED_IMPORT_MODULES:
        raise ImportError(f"Import '{base}' is not allowed")
    return builtins.__import__(name, globals, locals, fromlist, level)


def _safe_builtins() -> dict:
    safe = {name: getattr(builtins, name) for name in _SAFE_BUILTIN_NAMES}
    safe["__import__"] = _restricted_import
    return safe


def _resolve_function_name(default_name: str | None, params: dict | None) -> str | None:
    if isinstance(params, dict) and "__function_name" in params:
        return str(params["__function_name"])
    return default_name


def _strip_meta_params(params: dict | None) -> dict | None:
    if not isinstance(params, dict):
        return params
    payload = dict(params)
    payload.pop("__function_name", None)
    return payload


def _call(func, params):
    if params is None:
        return func()
    if isinstance(params, dict):
        if "args" in params or "kwargs" in params:
            args = params.get("args", [])
            kwargs = params.get("kwargs", {})
            return func(*args, **kwargs)
        return func(**params)
    return func(params)


def _build_local_runner_script(function_name: str | None) -> str:
    safe_names = sorted(_SAFE_BUILTIN_NAMES)
    banned_modules = sorted(_BANNED_IMPORT_MODULES)
    resolved_name = function_name or ""
    return (
        "import builtins\n"
        "import json\n"
        "import sys\n"
        "import traceback\n"
        "\n"
        f"SAFE_NAMES = {safe_names!r}\n"
        f"BANNED_MODULES = {banned_modules!r}\n"
        f"DEFAULT_FUNCTION_NAME = {resolved_name!r}\n"
        "\n"
        "def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):\n"
        "    base = str(name).split('.', 1)[0]\n"
        "    if base in BANNED_MODULES:\n"
        "        raise ImportError(f\"Import '{base}' is not allowed\")\n"
        "    return builtins.__import__(name, globals, locals, fromlist, level)\n"
        "\n"
        "def _safe_builtins():\n"
        "    safe = {name: getattr(builtins, name) for name in SAFE_NAMES}\n"
        "    safe['__import__'] = _restricted_import\n"
        "    return safe\n"
        "\n"
        "def _load_params():\n"
        "    try:\n"
        "        with open('input.json', 'r', encoding='utf-8') as f:\n"
        "            return json.load(f)\n"
        "    except FileNotFoundError:\n"
        "        return None\n"
        "\n"
        "def _resolve_function(params):\n"
        "    if isinstance(params, dict) and '__function_name' in params:\n"
        "        return params.pop('__function_name')\n"
        "    return DEFAULT_FUNCTION_NAME\n"
        "\n"
        "def _call(func, params):\n"
        "    if params is None:\n"
        "        return func()\n"
        "    if isinstance(params, dict):\n"
        "        if 'args' in params or 'kwargs' in params:\n"
        "            return func(*params.get('args', []), **params.get('kwargs', {}))\n"
        "        return func(**params)\n"
        "    return func(params)\n"
        "\n"
        "def main():\n"
        "    source = open('source.py', 'r', encoding='utf-8').read()\n"
        "    params = _load_params()\n"
        "    scope = {'__builtins__': _safe_builtins(), '__name__': '__autoforge_tool__'}\n"
        "    exec(compile(source, filename='<autoforge-local-runner>', mode='exec'), scope, scope)\n"
        "    if params is None:\n"
        "        return 0\n"
        "    name = _resolve_function(params)\n"
        "    if not name:\n"
        "        print('No function name resolved', file=sys.stderr)\n"
        "        return 1\n"
        "    func = scope.get(name)\n"
        "    if not callable(func):\n"
        "        print(f'No callable function found: {name}', file=sys.stderr)\n"
        "        return 1\n"
        "    result = _call(func, params)\n"
        "    if result is not None:\n"
        "        try:\n"
        "            json.dumps(result, ensure_ascii=False)\n"
        "        except TypeError as exc:\n"
        "            print(f'Non JSON serializable output: {exc}', file=sys.stderr)\n"
        "            return 1\n"
        "        print(result)\n"
        "    return 0\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    try:\n"
        "        raise SystemExit(main())\n"
        "    except Exception:\n"
        "        traceback.print_exc()\n"
        "        raise SystemExit(1)\n"
    )


class LocalRunner:
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
        resolved_name = _resolve_function_name(function_name, test_input)
        payload = _strip_meta_params(test_input)

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                (temp_path / "source.py").write_text(source_code, encoding="utf-8")
                (temp_path / "runner.py").write_text(_build_local_runner_script(resolved_name), encoding="utf-8")
                if test_input is not None:
                    try:
                        (temp_path / "input.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                    except TypeError as exc:
                        return VerifierOutput(
                            success=False,
                            stderr=f"Input JSON error: {exc}",
                            failure_type="non_json_serializable_input",
                        )

                result = subprocess.run(
                    [sys.executable, "runner.py"],
                    cwd=str(temp_path),
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
        except Exception:  # pragma: no cover - mirrors docker fallback safety net
            return VerifierOutput(success=False, stderr=traceback.format_exc(), failure_type="sandbox_internal_error")
