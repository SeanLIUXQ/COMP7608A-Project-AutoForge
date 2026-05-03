from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _snake(text: str) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    name = "_".join(words[:6]) or "generated_tool"
    if name[0].isdigit():
        name = f"tool_{name}"
    return name[:60]


def _planner_pair(query: str, function_name: str) -> dict[str, Any]:
    return {
        "task": "planner",
        "messages": [
            {
                "role": "user",
                "content": f"Plan a reusable AutoForge tool for this request: {query}",
            },
            {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "steps": [
                            "Identify reusable input arguments",
                            "Validate argument types and required fields",
                            "Perform deterministic task-family logic",
                            "Return a JSON-serializable value",
                        ],
                        "suggested_function_name": function_name,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }


def _coder_pair(query: str, function_name: str) -> dict[str, Any]:
    return {
        "task": "coder",
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Write one reusable Python function named {function_name} for this task family: {query}. "
                    "Use type hints, validate inputs, avoid side effects, and return JSON-serializable output."
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "```python\n"
                    f"def {function_name}(query: str):\n"
                    f"    \"\"\"Reusable tool scaffold for: {query}\"\"\"\n"
                    "    if not isinstance(query, str) or not query.strip():\n"
                    "        raise ValueError('query must be a non-empty string')\n"
                    "    raise NotImplementedError('Fill in deterministic task-family logic')\n"
                    "```"
                ),
            },
        ],
    }


def _load_demo_cases(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _load_benchmark(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = json.loads(path.read_text(encoding="utf-8"))
    return rows[:limit]


def generate_instruction_dataset(
    *,
    demo_cases_path: str,
    benchmark_path: str,
    output_path: str,
    benchmark_limit: int,
) -> int:
    examples: list[dict[str, Any]] = []
    for case in _load_demo_cases(Path(demo_cases_path)):
        payload = case.get("example_payload") or {}
        function_name = str(payload.get("__function_name") or _snake(case.get("query", "generated tool")))
        query = str(case.get("query", ""))
        examples.append(_planner_pair(query, function_name))
        examples.append(_coder_pair(query, function_name))

    for row in _load_benchmark(Path(benchmark_path), benchmark_limit):
        function_name = _snake(f"{row.get('tool_family', 'tool')} {row.get('sample_id', '')}")
        query = str(row.get("query", ""))
        examples.append(_planner_pair(query, function_name))

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(json.dumps(example, ensure_ascii=False) for example in examples) + "\n",
        encoding="utf-8",
    )
    return len(examples)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate lightweight instruction examples for AutoForge prompts.")
    parser.add_argument("--demo-cases", default="agents/demo_cases.json")
    parser.add_argument("--benchmark", default="evaluation/benchmark/dataset.json")
    parser.add_argument("--benchmark-limit", type=int, default=40)
    parser.add_argument("--output", default="evaluation/llm_instruction_dataset.jsonl")
    args = parser.parse_args()
    count = generate_instruction_dataset(
        demo_cases_path=args.demo_cases,
        benchmark_path=args.benchmark,
        output_path=args.output,
        benchmark_limit=args.benchmark_limit,
    )
    print(f"Wrote {count} instruction examples to {args.output}")


if __name__ == "__main__":
    main()
