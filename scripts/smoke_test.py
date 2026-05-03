from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# Ensure repo root is on sys.path when running as a script.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.forge_pipeline import run_forge_pipeline
from sandbox.executor import execute_code
from shared.schemas import ForgeRequest


def _print_result(title: str, ok: bool, detail: Optional[str] = None) -> None:
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {title}")
    if detail:
        print(f"  {detail}")


def sandbox_smoke_test() -> bool:
    source_code = (
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n"
    )
    result = execute_code(
        source_code,
        {"a": 2, "b": 3, "__function_name": "add"},
    )
    ok = result.success and (result.stdout or "").strip() == "5"
    detail = None
    if not ok:
        detail = f"stdout={result.stdout!r} stderr={result.stderr!r}"
    _print_result("Sandbox execution", ok, detail)
    return ok


def _provider_key_present(provider: str) -> bool:
    provider = provider.lower()
    key_map = {
        "deepseek": "DEEPSEEK_API_KEY",
        "qwen": "DASHSCOPE_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    env_key = key_map.get(provider)
    if not env_key:
        return False
    value = (os.getenv(env_key) or "").strip()
    if not value:
        return False
    if not value.isascii():
        return False
    if "placeholder" in value.lower() or "your_" in value.lower():
        return False
    return True


def pipeline_smoke_test() -> bool:
    provider = os.getenv("LLM_PROVIDER", "deepseek")
    if not _provider_key_present(provider):
        _print_result(
            "Forge pipeline",
            True,
            "Skipped (no LLM API key configured in environment)",
        )
        return True

    request = ForgeRequest(query="Write a Python function that adds two integers.")
    result = run_forge_pipeline(request)
    ok = result.status == "success"
    detail = None
    if not ok:
        detail = f"status={result.status} error={result.error!r}"
    _print_result("Forge pipeline", ok, detail)
    return ok


def main() -> int:
    ok_sandbox = sandbox_smoke_test()
    ok_pipeline = pipeline_smoke_test()
    return 0 if (ok_sandbox and ok_pipeline) else 1


if __name__ == "__main__":
    sys.exit(main())
