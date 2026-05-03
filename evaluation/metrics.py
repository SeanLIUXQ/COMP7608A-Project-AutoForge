from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any


def _safe_mean(values: list[float]) -> float:
	return mean(values) if values else 0.0


def _path_value(path_taken: Any) -> str:
	value = getattr(path_taken, "value", path_taken)
	return str(value).lower()


def compute_success_rate(results: list[dict[str, Any]]) -> float:
	if not results:
		return 0.0
	hits = sum(1 for item in results if item.get("matched", False))
	return hits / len(results)


def compute_trr(results: list[dict[str, Any]]) -> float:
	if not results:
		return 0.0
	reused_count = 0
	for item in results:
		if "reused_existing_tool" in item:
			reused_count += 1 if bool(item.get("reused_existing_tool")) else 0
		else:
			reused_count += 1 if _path_value(item.get("path_taken", "")) == "fast" else 0
	return reused_count / len(results)


def compute_latency_stats(results: list[dict[str, Any]]) -> dict[str, float]:
	total = [float(item.get("total_latency_ms", 0.0) or 0.0) for item in results]
	fast_total = [
		float(item.get("total_latency_ms", 0.0) or 0.0)
		for item in results
		if _path_value(item.get("path_taken", "")) == "fast"
	]
	slow_total = [
		float(item.get("total_latency_ms", 0.0) or 0.0)
		for item in results
		if _path_value(item.get("path_taken", "")) == "slow"
	]
	forge = [
		float(item.get("forge_latency_ms", 0.0) or 0.0)
		for item in results
		if item.get("forge_latency_ms") is not None
	]
	retrieval = [
		float(item.get("retrieval_latency_ms", 0.0) or 0.0)
		for item in results
		if item.get("retrieval_latency_ms") is not None
	]
	execution = [
		float(item.get("execution_latency_ms", 0.0) or 0.0)
		for item in results
		if item.get("execution_latency_ms") is not None
	]
	return {
		"mean_total_latency_ms": _safe_mean(total),
		"mean_forge_latency_ms": _safe_mean(forge),
		"mean_retrieval_latency_ms": _safe_mean(retrieval),
		"mean_execution_latency_ms": _safe_mean(execution),
		"mean_fast_latency_ms": _safe_mean(fast_total),
		"mean_slow_latency_ms": _safe_mean(slow_total),
		"speedup_ratio": (_safe_mean(slow_total) / _safe_mean(fast_total)) if fast_total and slow_total else 0.0,
	}


def compute_path_distribution(results: list[dict[str, Any]]) -> dict[str, int]:
	counts: dict[str, int] = defaultdict(int)
	for item in results:
		path = _path_value(item.get("path_taken", "unknown"))
		counts[path] += 1
	return dict(sorted(counts.items()))


def compute_error_rate(results: list[dict[str, Any]]) -> float:
	if not results:
		return 0.0
	failures = sum(1 for item in results if item.get("error"))
	return failures / len(results)


def grouped_metrics(results: list[dict[str, Any]], key: str) -> dict[str, dict[str, float]]:
	buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
	for item in results:
		buckets[str(item.get(key, "unknown"))].append(item)

	output: dict[str, dict[str, float]] = {}
	for bucket, group in buckets.items():
		trr = compute_trr(group)
		output[bucket] = {
			"count": len(group),
			"success_rate": compute_success_rate(group),
			"tool_reuse_rate": trr,
			"trr": trr,
			"error_rate": compute_error_rate(group),
			**compute_latency_stats(group),
		}
	return output


def build_report(results: list[dict[str, Any]]) -> dict[str, Any]:
	tool_reuse_rate = compute_trr(results)
	return {
		"total_samples": len(results),
		"canonical_samples": sum(1 for item in results if item.get("protocol_pass") == "cold"),
		"paraphrase_samples": sum(1 for item in results if item.get("protocol_pass") == "warm"),
		"success_rate": compute_success_rate(results),
		"tool_reuse_rate": tool_reuse_rate,
		"trr": tool_reuse_rate,
		"error_rate": compute_error_rate(results),
		"reused_existing_tool_count": sum(1 for item in results if item.get("reused_existing_tool")),
		"path_distribution": compute_path_distribution(results),
		**compute_latency_stats(results),
		"per_pass": grouped_metrics(results, "protocol_pass"),
		"per_difficulty": grouped_metrics(results, "difficulty"),
		"per_tool_family": grouped_metrics(results, "tool_family"),
	}
