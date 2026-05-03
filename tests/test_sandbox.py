from __future__ import annotations

import sandbox.local_runner as local_runner
from sandbox.executor import execute_code


def test_execute_code_defaults_to_local_backend(monkeypatch) -> None:
    monkeypatch.delenv("SANDBOX_BACKEND", raising=False)
    result = execute_code(
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n",
        {"a": 2, "b": 3, "__function_name": "add"},
    )
    assert result.success is True
    assert (result.stdout or "").strip() == "5"


def test_execute_code_without_input_only_validates_script(monkeypatch) -> None:
    monkeypatch.delenv("SANDBOX_BACKEND", raising=False)
    result = execute_code(
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n"
    )
    assert result.success is True
    assert (result.stdout or "") == ""


def test_execute_code_rejects_dangerous_builtin_calls(monkeypatch) -> None:
    monkeypatch.delenv("SANDBOX_BACKEND", raising=False)
    result = execute_code(
        "def unsafe() -> str:\n"
        "    return open('README.md').read()\n",
        {"__function_name": "unsafe"},
    )
    assert result.success is False
    assert "not allowed" in (result.stderr or "")
    assert result.failure_type == "unsafe_call"


def test_execute_code_rejects_dangerous_imports(monkeypatch) -> None:
    monkeypatch.delenv("SANDBOX_BACKEND", raising=False)
    result = execute_code(
        "import os\n\n"
        "def unsafe() -> str:\n"
        "    return os.getcwd()\n",
        {"__function_name": "unsafe"},
    )
    assert result.success is False
    assert result.failure_type == "unsafe_import"


def test_execute_code_reports_missing_required_param(monkeypatch) -> None:
    monkeypatch.delenv("SANDBOX_BACKEND", raising=False)
    result = execute_code(
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n",
        {"a": 1, "__function_name": "add"},
    )
    assert result.success is False
    assert result.failure_type == "missing_required_param"


def test_execute_code_reports_non_json_serializable_output(monkeypatch) -> None:
    monkeypatch.delenv("SANDBOX_BACKEND", raising=False)
    result = execute_code(
        "def make_set() -> set:\n"
        "    return {1, 2, 3}\n",
        {"__function_name": "make_set"},
    )
    assert result.success is False
    assert result.failure_type == "non_json_serializable_output"


def test_local_sandbox_times_out_infinite_loop(monkeypatch) -> None:
    monkeypatch.delenv("SANDBOX_BACKEND", raising=False)
    monkeypatch.setattr(local_runner, "SANDBOX_TIMEOUT_SECONDS", 1)
    result = execute_code(
        "def spin() -> int:\n"
        "    while True:\n"
        "        pass\n",
        {"__function_name": "spin"},
    )
    assert result.success is False
    assert "timed out" in (result.stderr or "").lower()
    assert result.failure_type == "timeout"
