from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from pathlib import Path
from typing import Optional

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
from shared.schemas import ForgeRequest


def _validate_api_key(provider: str) -> tuple[bool, str]:
    provider = provider.lower()
    key_map = {
        "deepseek": "DEEPSEEK_API_KEY",
        "qwen": "DASHSCOPE_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    env_key = key_map.get(provider)
    if not env_key:
        return False, f"Unknown provider '{provider}'"
    value = (os.getenv(env_key) or "").strip()
    if not value:
        return False, f"Missing {env_key}"
    if not value.isascii():
        return False, f"Invalid {env_key}: contains non-ASCII characters"
    return True, env_key


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single ForgeRequest.")
    parser.add_argument(
        "query",
        nargs="?",
        help="User request to forge into a tool",
    )
    parser.add_argument(
        "-q",
        "--query",
        dest="query_flag",
        help="User request (same as positional)",
    )
    parser.add_argument(
        "--show-schema",
        action="store_true",
        help="Print the generated tool JSON schema",
    )
    parser.add_argument(
        "--show-code",
        action="store_true",
        help="Print the generated source code",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute the generated tool in the sandbox (requires --input or --input-file)",
    )
    parser.add_argument(
        "--input",
        dest="run_input",
        help="JSON string passed to the tool when using --run",
    )
    parser.add_argument(
        "--input-file",
        dest="run_input_file",
        help="Path to a JSON file passed to the tool when using --run",
    )
    parser.add_argument(
        "--bundle-dir",
        dest="bundle_dir",
        default="skills",
        help="Directory to write the skill bundle (default: skills)",
    )
    parser.add_argument(
        "--no-bundle",
        action="store_true",
        help="Do not write the skill bundle to disk",
    )
    return parser.parse_args()


def _resolve_query(args: argparse.Namespace) -> Optional[str]:
    if args.query_flag:
        return args.query_flag.strip()
    if args.query:
        return args.query.strip()
    return None


def _parse_loose_kv(raw: str) -> Optional[dict]:
    text = raw.strip()
    if text.startswith("{") and text.endswith("}"):
        text = text[1:-1].strip()
    if not text:
        return None
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return None
    result: dict = {}
    for part in parts:
        if ":" not in part:
            return None
        key, value = part.split(":", 1)
        key = key.strip().strip('"').strip("'")
        value = value.strip()
        if value.lower() == "true":
            parsed = True
        elif value.lower() == "false":
            parsed = False
        elif value.lower() in {"null", "none"}:
            parsed = None
        else:
            try:
                parsed = int(value)
            except ValueError:
                try:
                    parsed = float(value)
                except ValueError:
                    parsed = value.strip('"').strip("'")
        result[key] = parsed
    return result


def _load_run_payload(args: argparse.Namespace) -> dict:
    if args.run_input_file and args.run_input:
        raise ValueError("Use either --input or --input-file, not both.")

    raw = None
    if args.run_input_file:
        path = Path(args.run_input_file)
        raw = path.read_text(encoding="utf-8").strip()
    elif args.run_input:
        raw = args.run_input.strip()
    else:
        raise ValueError("Missing --input JSON or --input-file for --run.")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            value = ast.literal_eval(raw)
        except Exception as exc:
            loose = _parse_loose_kv(raw)
            if loose is not None:
                return loose
            raise ValueError(f"Invalid JSON for --input: {exc}. Raw={raw!r}") from exc
        if isinstance(value, dict):
            return value
        raise ValueError(f"Invalid JSON for --input: not a dict. Raw={raw!r}")


def main() -> int:
    args = _parse_args()
    query = _resolve_query(args)
    if not query:
        print("Missing query. Example: python scripts/forge_cli.py \"sum two integers\"")
        return 2

    provider = os.getenv("LLM_PROVIDER", "deepseek")
    ok, msg = _validate_api_key(provider)
    if not ok:
        print(f"LLM configuration error: {msg}. Check your .env settings.")
        return 2

    result = run_forge_pipeline(ForgeRequest(query=query))
    print(f"status={result.status} attempts={result.attempts}")
    if result.error:
        print(f"error={result.error}")
    if result.tool:
        print(f"tool.name={result.tool.name}")
        print(f"tool.id={result.tool.tool_id}")
        if not args.no_bundle:
            bundle_path = create_skill_bundle(result.tool, base_dir=args.bundle_dir)
            print(f"bundle.path={bundle_path}")
        if args.show_schema:
            print(json.dumps(result.tool.json_schema, indent=2, ensure_ascii=False))
        if args.show_code:
            print(result.tool.source_code)
        if args.run:
            try:
                run_payload = _load_run_payload(args)
            except ValueError as exc:
                print(str(exc))
                return 2
            from sandbox.executor import execute_code

            exec_result = execute_code(result.tool.source_code, run_payload)
            print(f"run.success={exec_result.success}")
            if exec_result.stdout:
                print(f"run.stdout={exec_result.stdout.strip()}")
            if exec_result.stderr:
                print(f"run.stderr={exec_result.stderr.strip()}")

    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
