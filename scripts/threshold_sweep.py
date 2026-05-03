from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.service import AutoForgeBackendService
from backend.tool_registry import ToolRegistry
from evaluation.judge import judge_output
from shared.schemas import QueryRequest


def _path_value(path_taken: Any) -> str:
    value = getattr(path_taken, "value", path_taken)
    return str(value).lower()


def _load_dataset(dataset_path: str) -> list[dict[str, Any]]:
    data = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Dataset must be a JSON array")
    return data


@dataclass
class SweepRow:
    threshold: float
    total: int
    success: int
    fast: int
    slow: int
    registry_only_miss: int
    fast_incorrect: int
    fast_error: int

    def to_dict(self) -> dict[str, Any]:
        total = max(1, self.total)
        return {
            "threshold": self.threshold,
            "total": self.total,
            "success_rate": round(self.success / total, 4),
            "fast_rate": round(self.fast / total, 4),
            "slow_rate": round(self.slow / total, 4),
            "fast_incorrect_rate": round(self.fast_incorrect / total, 4),
            "fast_error_rate": round(self.fast_error / total, 4),
            "registry_only_miss_rate": round(self.registry_only_miss / total, 4),
            "counts": {
                "success": self.success,
                "fast": self.fast,
                "slow": self.slow,
                "fast_incorrect": self.fast_incorrect,
                "fast_error": self.fast_error,
                "registry_only_miss": self.registry_only_miss,
            },
        }


def run_sweep(
    *,
    dataset_path: str,
    thresholds: list[float],
    include_paraphrases: bool,
    strategy: str,
) -> dict[str, Any]:
    dataset = _load_dataset(dataset_path)

    rows: list[SweepRow] = []
    for thr in thresholds:
        registry = ToolRegistry(enable_vector_store=False)
        service = AutoForgeBackendService(registry=registry, similarity_threshold=thr)
        service.sync()

        row = SweepRow(
            threshold=thr,
            total=0,
            success=0,
            fast=0,
            slow=0,
            registry_only_miss=0,
            fast_incorrect=0,
            fast_error=0,
        )

        for sample in dataset:
            queries = [sample["query"]]
            if include_paraphrases:
                queries.extend(sample.get("paraphrases", []) or [])
            for query_text in queries:
                row.total += 1
                resp = service.handle_query(QueryRequest(query=query_text, strategy=strategy))
                verdict = judge_output(
                    actual_output=resp.result,
                    expected_output=sample["expected_output"],
                    expected_output_type=sample["expected_output_type"],
                )
                if verdict.matched:
                    row.success += 1
                if _path_value(resp.path_taken) == "fast":
                    row.fast += 1
                    if resp.error:
                        row.fast_error += 1
                    elif not verdict.matched:
                        row.fast_incorrect += 1
                else:
                    row.slow += 1
                if strategy == "registry_only" and resp.error:
                    row.registry_only_miss += 1

        rows.append(row)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_path": dataset_path,
        "strategy": strategy,
        "include_paraphrases": include_paraphrases,
        "thresholds": thresholds,
        "rows": [r.to_dict() for r in rows],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Threshold sweep for AutoForge lexical retrieval")
    parser.add_argument("--dataset", default="evaluation/benchmark/dataset.json", help="Dataset JSON path")
    parser.add_argument("--thresholds", default="0.55,0.65,0.75,0.85", help="Comma-separated thresholds")
    parser.add_argument("--strategy", default="full", choices=["full", "registry_only"], help="Query strategy")
    parser.add_argument("--include-paraphrases", action="store_true", help="Include paraphrases in sweep")
    parser.add_argument("--output", default="", help="Optional output JSON path")
    parser.add_argument("--output-dir", default="evaluation/results", help="Directory for default output path")
    args = parser.parse_args()

    thresholds = [float(item.strip()) for item in args.thresholds.split(",") if item.strip()]
    report = run_sweep(
        dataset_path=args.dataset,
        thresholds=thresholds,
        include_paraphrases=bool(args.include_paraphrases),
        strategy=args.strategy,
    )
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output = args.output
    if not output:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output = str(Path(args.output_dir) / f"threshold_sweep_{args.strategy}_{ts}.json")
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(text, encoding="utf-8")
        print(f"saved_to={output}")
    print(text)


if __name__ == "__main__":
    main()

