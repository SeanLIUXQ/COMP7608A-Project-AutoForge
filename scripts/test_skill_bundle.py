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

from agents.packager import create_skill_bundle, run_packager
from shared.schemas import CoderOutput


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test skill bundle generation.")
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the generated bundle directory after the test",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    base_dir = REPO_ROOT / "skills_test"
    if base_dir.exists():
        shutil.rmtree(base_dir)

    source_code = (
        "def add_two_integers(a: int, b: int) -> int:\n"
        "    \"\"\"Return the sum of two integers.\"\"\"\n"
        "    return a + b\n"
    )

    coder_output = CoderOutput(source_code=source_code, function_name="add_two_integers")
    tool = run_packager(coder_output)
    bundle_path = create_skill_bundle(tool, base_dir=str(base_dir))

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
        print("FAIL: Missing bundle files")
        return 1

    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    tool_text = tool_file.read_text(encoding="utf-8")

    checks = [
        schema.get("name") == tool.name,
        meta.get("name") == tool.name,
        meta.get("tool_id") == tool.tool_id,
        "def add_two_integers" in tool_text,
    ]

    if not all(checks):
        print("FAIL: Bundle content validation failed")
        return 1

    print(f"OK: bundle created at {bundle_path}")

    if not args.keep:
        shutil.rmtree(base_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
