from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from evaluation.judge import judge_output
from evaluation.metrics import build_report
from shared.constants import DEFAULT_QUERY_STRATEGY, EVAL_DATASET_PATH, EVAL_RESULTS_DIR


DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"


def _load_dataset(dataset_path: str) -> list[dict[str, Any]]:
	with open(dataset_path, "r", encoding="utf-8") as f:
		data = json.load(f)
	if not isinstance(data, list):
		raise ValueError("Dataset must be a JSON array")
	return data


def _parse_strategies(raw: str | None, default: str = DEFAULT_QUERY_STRATEGY) -> list[str]:
	if not raw:
		return [default]
	items = [item.strip() for item in raw.split(",") if item.strip()]
	return items or [default]


def _mock_query(sample: dict[str, Any], query_text: str, strategy: str = DEFAULT_QUERY_STRATEGY) -> dict[str, Any]:
	seed_source = f"{sample['sample_id']}::{strategy}::{query_text}".encode("utf-8")
	seed = int(hashlib.sha256(seed_source).hexdigest()[:8], 16) % 100
	if strategy == "no_retrieval":
		reused_existing_tool = False
		path_taken = "slow"
		total_latency_ms = 430.0
		retrieval_latency_ms = None
	elif strategy == "agent":
		reused_existing_tool = False
		path_taken = "slow"
		total_latency_ms = 820.0
		retrieval_latency_ms = None
	elif strategy == "registry_only":
		reused_existing_tool = seed >= 35
		path_taken = "fast" if reused_existing_tool else "slow"
		total_latency_ms = 150.0 if reused_existing_tool else 75.0
		retrieval_latency_ms = 35.0 if reused_existing_tool else 28.0
	else:
		reused_existing_tool = seed >= 45
		path_taken = "fast" if reused_existing_tool else "slow"
		total_latency_ms = 145.0 if reused_existing_tool else 360.0
		retrieval_latency_ms = 28.0 if reused_existing_tool else 60.0

	base = {
		"path_taken": path_taken,
		"total_latency_ms": total_latency_ms,
		"forge_latency_ms": 510.0 if strategy == "agent" else None,
		"retrieval_latency_ms": retrieval_latency_ms,
		"execution_latency_ms": 95.0 if path_taken == "fast" else 215.0,
		"reused_existing_tool": reused_existing_tool,
		"tool_id": "mock-registry-tool" if reused_existing_tool else "mock-fallback-tool",
		"tool_name": "mock_registry_tool" if reused_existing_tool else "mock_fallback_tool",
		"search_score": 0.86 if reused_existing_tool else 0.42,
		"retrieval_trace": [
			{
				"rank": 1,
				"tool_id": "mock-registry-tool" if reused_existing_tool else "mock-miss-tool",
				"tool_name": "mock_registry_tool" if reused_existing_tool else "mock_miss_tool",
				"score": 0.86 if reused_existing_tool else 0.42,
				"threshold": 0.75,
				"accepted": reused_existing_tool,
				"reason": "accepted" if reused_existing_tool else "below_threshold",
			}
		],
		"strategy": strategy,
		"error": None,
	}

	if strategy == "registry_only" and not reused_existing_tool:
		return {
			**base,
			"result": None,
			"error": "mock registry_only miss",
		}

	if seed < 8 and strategy != "registry_only":
		return {
			**base,
			"result": None,
			"error": "mock execution error",
		}

	return {
		**base,
		"result": sample["expected_output"],
	}


def _backend_query(
	backend_url: str,
	query_text: str,
	strategy: str = DEFAULT_QUERY_STRATEGY,
	timeout_s: float = 60.0,
) -> dict[str, Any]:
	payload = {"query": query_text, "strategy": strategy}
	with httpx.Client(timeout=timeout_s) as client:
		resp = client.post(f"{backend_url.rstrip('/')}/query", json=payload)
		resp.raise_for_status()
		return resp.json()


def _assert_backend_ready(backend_url: str, timeout_s: float = 10.0) -> None:
	try:
		with httpx.Client(timeout=timeout_s) as client:
			resp = client.get(f"{backend_url.rstrip('/')}/health")
			resp.raise_for_status()
	except Exception as exc:
		raise RuntimeError(
			"Live backend evaluation requires a running AutoForge backend. "
			f"Start it with '.\\scripts\\start_backend.ps1' and verify {backend_url.rstrip('/')}/health."
		) from exc


def run_benchmark(
	dataset_path: str,
	mode: str,
	backend_url: str | None = None,
	strategy: str = DEFAULT_QUERY_STRATEGY,
) -> dict[str, Any]:
	dataset = _load_dataset(dataset_path)
	started = time.time()
	results: list[dict[str, Any]] = []

	for sample in dataset:
		queries = [
			("cold", sample["query"], None),
			*[
				("warm", paraphrase, paraphrase_index)
				for paraphrase_index, paraphrase in enumerate(sample.get("paraphrases", []), start=1)
			],
		]
		for protocol_pass, query_text, paraphrase_index in queries:
			if mode == "backend":
				if not backend_url:
					raise ValueError("backend_url is required when mode=backend")
				model_resp = _backend_query(
					backend_url=backend_url,
					query_text=query_text,
					strategy=strategy,
				)
			else:
				model_resp = _mock_query(sample=sample, query_text=query_text, strategy=strategy)

			verdict = judge_output(
				actual_output=model_resp.get("result"),
				expected_output=sample["expected_output"],
				expected_output_type=sample["expected_output_type"],
			)

			results.append(
				{
					"sample_id": sample["sample_id"],
					"difficulty": sample["difficulty"],
					"tool_family": sample["tool_family"],
					"query": query_text,
					"canonical_query": sample["query"],
					"protocol_pass": protocol_pass,
					"is_canonical": protocol_pass == "cold",
					"paraphrase_index": paraphrase_index,
					"expected_output": sample["expected_output"],
					"actual_output": model_resp.get("result"),
					"matched": verdict.matched,
					"verdict_reason": verdict.reason,
					"path_taken": str(model_resp.get("path_taken", "unknown")).lower(),
					"total_latency_ms": float(model_resp.get("total_latency_ms", 0.0) or 0.0),
					"forge_latency_ms": model_resp.get("forge_latency_ms"),
					"retrieval_latency_ms": model_resp.get("retrieval_latency_ms"),
					"execution_latency_ms": model_resp.get("execution_latency_ms"),
					"reused_existing_tool": bool(model_resp.get("reused_existing_tool", False)),
					"tool_id": model_resp.get("tool_id"),
					"tool_name": model_resp.get("tool_name"),
					"search_score": model_resp.get("search_score"),
					"retrieval_trace": model_resp.get("retrieval_trace", []),
					"strategy": str(model_resp.get("strategy", strategy)),
					"error": model_resp.get("error"),
				}
			)

	report = build_report(results)
	report["timestamp"] = datetime.now(timezone.utc).isoformat()
	report["mode"] = mode
	report["strategy"] = strategy
	report["duration_seconds"] = round(time.time() - started, 3)
	report["results"] = results
	return report


def run_strategy_matrix(
	dataset_path: str,
	mode: str,
	strategies: list[str],
	backend_url: str | None = None,
) -> list[dict[str, Any]]:
	reports: list[dict[str, Any]] = []
	for strategy in strategies:
		reports.append(
			run_benchmark(
				dataset_path=dataset_path,
				mode=mode,
				backend_url=backend_url,
				strategy=strategy,
			)
		)
	return reports


def save_report(report: dict[str, Any], output_dir: str) -> str:
	out_dir = Path(output_dir)
	out_dir.mkdir(parents=True, exist_ok=True)
	ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
	mode = str(report.get("mode", "unknown")).replace("-", "_")
	strategy = str(report.get("strategy", DEFAULT_QUERY_STRATEGY)).replace("-", "_")
	out_path = out_dir / f"eval_report_{mode}_{strategy}_{ts}.json"
	out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
	return str(out_path)


def main() -> None:
	parser = argparse.ArgumentParser(description="Run AutoForge evaluation benchmark")
	parser.add_argument("--dataset", default=EVAL_DATASET_PATH, help="Path to benchmark dataset JSON")
	parser.add_argument("--mode", choices=["mock", "backend"], default="backend", help="Execution mode")
	parser.add_argument(
		"--strategy",
		choices=["full", "no_retrieval", "registry_only", "agent"],
		default=DEFAULT_QUERY_STRATEGY,
		help="Single query strategy to evaluate",
	)
	parser.add_argument(
		"--strategies",
		help="Comma-separated strategy list for comparison runs, e.g. full,no_retrieval",
	)
	parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL, help="Backend URL for mode=backend")
	parser.add_argument("--output-dir", default=EVAL_RESULTS_DIR, help="Directory to write report JSON")
	args = parser.parse_args()

	strategies = _parse_strategies(args.strategies, default=args.strategy)
	if args.mode == "backend":
		try:
			_assert_backend_ready(args.backend_url)
		except RuntimeError as exc:
			parser.exit(2, f"{exc}\n")
	reports = run_strategy_matrix(
		dataset_path=args.dataset,
		mode=args.mode,
		strategies=strategies,
		backend_url=args.backend_url,
	)
	for report in reports:
		out_path = save_report(report, output_dir=args.output_dir)
		print(
			f"Evaluation completed. mode={report['mode']} strategy={report['strategy']} saved_to={out_path}"
		)
		print(f"Success Rate: {report['success_rate']:.3f}")
		print(f"Tool Reuse Rate: {report['tool_reuse_rate']:.3f}")
		print(f"Error Rate: {report['error_rate']:.3f}")


if __name__ == "__main__":
	main()
