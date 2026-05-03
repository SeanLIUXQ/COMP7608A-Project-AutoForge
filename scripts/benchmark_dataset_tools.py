from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.schemas import BenchmarkSample


def _load_dataset(dataset_path: Path) -> list[dict]:
    return json.loads(dataset_path.read_text(encoding="utf-8"))


def validate_dataset(dataset_path: Path) -> tuple[bool, list[str], dict[str, int]]:
    rows = _load_dataset(dataset_path)
    errors: list[str] = []
    seen_ids: set[str] = set()
    difficulty_counts: Counter[int] = Counter()

    for index, row in enumerate(rows, start=1):
        try:
            sample = BenchmarkSample.model_validate(row)
        except Exception as exc:
            errors.append(f"row {index}: {exc}")
            continue

        if sample.sample_id in seen_ids:
            errors.append(f"duplicate sample_id: {sample.sample_id}")
        seen_ids.add(sample.sample_id)

        if len(sample.paraphrases) < 3 or len(sample.paraphrases) > 5:
            errors.append(f"{sample.sample_id}: paraphrases must be 3-5 items")

        difficulty_counts[sample.difficulty] += 1

    expected_difficulties = {1, 2, 3, 4}
    missing = expected_difficulties - set(difficulty_counts.keys())
    for difficulty in sorted(missing):
        errors.append(f"missing difficulty bucket: L{difficulty}")
    if not missing:
        bucket_sizes = set(difficulty_counts.values())
        if len(bucket_sizes) != 1:
            errors.append(f"difficulty buckets must be balanced: {dict(sorted(difficulty_counts.items()))}")

    return len(errors) == 0, errors, {str(key): value for key, value in sorted(difficulty_counts.items())}


def stats_dataset(dataset_path: Path) -> dict:
    rows = _load_dataset(dataset_path)
    difficulty_counts: Counter[int] = Counter()
    tool_family_counts: Counter[str] = Counter()
    paraphrase_lengths: list[int] = []

    for row in rows:
        sample = BenchmarkSample.model_validate(row)
        difficulty_counts[sample.difficulty] += 1
        tool_family_counts[sample.tool_family] += 1
        paraphrase_lengths.append(len(sample.paraphrases))

    avg_paraphrases = sum(paraphrase_lengths) / len(paraphrase_lengths) if paraphrase_lengths else 0.0
    return {
        "total_samples": len(rows),
        "cold_queries": len(rows),
        "warm_queries": sum(paraphrase_lengths),
        "total_eval_queries": len(rows) + sum(paraphrase_lengths),
        "difficulty_counts": {str(key): value for key, value in sorted(difficulty_counts.items())},
        "tool_family_counts": dict(sorted(tool_family_counts.items())),
        "average_paraphrases": round(avg_paraphrases, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or inspect the benchmark dataset.")
    parser.add_argument(
        "command",
        choices=["validate", "stats"],
        help="Which dataset utility to run",
    )
    parser.add_argument(
        "--dataset",
        default="evaluation/benchmark/dataset.json",
        help="Path to dataset JSON",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if args.command == "validate":
        ok, errors, difficulty_counts = validate_dataset(dataset_path)
        print(f"dataset={dataset_path}")
        print(f"difficulty_counts={difficulty_counts}")
        if not ok:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print("validation=ok")
        return 0

    print(json.dumps(stats_dataset(dataset_path), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
