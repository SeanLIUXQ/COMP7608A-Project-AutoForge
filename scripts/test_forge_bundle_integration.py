from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

# Ensure repo root is on sys.path when running as a script.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

from agents.forge_pipeline import run_forge_pipeline
from agents.packager import create_skill_bundle
from sandbox.executor import execute_code
from shared.schemas import ForgeRequest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Integration test: forge -> bundle -> sandbox run.")
    parser.add_argument(
        "--query",
        default=(
            "Write a Python function named add_two_integers(a: int, b: int) -> int "
            "that returns a + b."
        ),
        help="Forge request sent to the pipeline",
    )
    parser.add_argument(
        "--input-file",
        dest="run_input_file",
        help="Path to JSON input for sandbox execution",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the generated bundle directory after the test",
    )
    return parser.parse_args()


def _load_input_payload(path: Path | None, function_name: str) -> dict:
    if path:
        raw = path.read_text(encoding="utf-8").strip()
        return json.loads(raw)
    return {"a": 2, "b": 3, "__function_name": function_name}


def main() -> int:
    args = _parse_args()
    base_dir = REPO_ROOT / "skills_test_llm"
    if base_dir.exists():
        shutil.rmtree(base_dir)

    result = run_forge_pipeline(ForgeRequest(query=args.query))
    if result.status != "success" or not result.tool:
        print(f"FAIL: forge pipeline status={result.status} error={result.error}")
        return 1

    bundle_path = create_skill_bundle(result.tool, base_dir=str(base_dir))
    tool_file = bundle_path / "tool.py"
    schema_file = bundle_path / "schema.json"
    meta_file = bundle_path / "metadata.json"
    readme_file = bundle_path / "README.md"
    requirements_file = bundle_path / "requirements.txt"
    example_file = bundle_path / "example_input.json"

    if not (
        tool_file.exists()
        and schema_file.exists()
        and meta_file.exists()
        and readme_file.exists()
        and requirements_file.exists()
        and example_file.exists()
    ):
        print("FAIL: bundle files missing")
        return 1

    payload = _load_input_payload(
        Path(args.run_input_file) if args.run_input_file else None,
        result.tool.name,
    )
    exec_result = execute_code(result.tool.source_code, payload)
    print(f"run.success={exec_result.success}")
    if exec_result.stdout:
        print(f"run.stdout={exec_result.stdout.strip()}")
    if exec_result.stderr:
        print(f"run.stderr={exec_result.stderr.strip()}")

    if not exec_result.success:
        return 1

    print(f"OK: bundle created at {bundle_path}")

    if not args.keep:
        shutil.rmtree(base_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
