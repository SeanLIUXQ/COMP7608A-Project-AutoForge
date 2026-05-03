from __future__ import annotations

import json
import os
from pathlib import Path

from backend.service import AutoForgeBackendService
from backend.tool_registry import ToolRegistry
from evaluation.judge import judge_output
from evaluation import runner as runner_module
from evaluation.metrics import build_report, compute_path_distribution, compute_success_rate, compute_trr
from evaluation.runner import run_benchmark
from scripts.benchmark_dataset_tools import stats_dataset, validate_dataset
from scripts.build_agent_demo_figures import build_agent_demo_figures
from scripts.build_final_report_assets import build_assets
from scripts.generate_instruction_dataset import generate_instruction_dataset
from scripts.run_agent_demo_cases import run_agent_demo_cases
from scripts.threshold_sweep import _path_value, run_sweep
from shared.schemas import PathType
from shared.schemas import QueryRequest


def test_judge_exact_match() -> None:
	verdict = judge_output(actual_output="abc", expected_output="abc", expected_output_type="exact")
	assert verdict.matched is True


def test_judge_exact_match_normalizes_scalar_strings() -> None:
	verdict = judge_output(actual_output=85291234567, expected_output="85291234567", expected_output_type="exact")
	assert verdict.matched is True


def test_judge_numeric_tolerance() -> None:
	verdict = judge_output(actual_output=1.005, expected_output=1.0, expected_output_type="numeric", tolerance=0.01)
	assert verdict.matched is True


def test_success_rate_and_trr() -> None:
	rows = [
		{"matched": True, "path_taken": "fast", "reused_existing_tool": True},
		{"matched": False, "path_taken": "slow", "reused_existing_tool": False},
		{"matched": True, "path_taken": "slow", "reused_existing_tool": True},
	]
	assert compute_success_rate(rows) == 2 / 3
	assert compute_trr(rows) == 2 / 3


def test_metrics_normalize_enum_path_values() -> None:
	rows = [
		{"matched": True, "path_taken": PathType.FAST, "total_latency_ms": 100},
		{"matched": True, "path_taken": PathType.SLOW, "total_latency_ms": 400},
	]
	report = build_report(rows)
	assert compute_path_distribution(rows) == {"fast": 1, "slow": 1}
	assert report["speedup_ratio"] == 4.0


def test_build_report_basics() -> None:
	rows = [
		{
			"matched": True,
			"path_taken": "fast",
			"reused_existing_tool": True,
			"total_latency_ms": 100,
			"retrieval_latency_ms": 50,
			"difficulty": 1,
			"tool_family": "string_ops",
		},
		{
			"matched": False,
			"path_taken": "slow",
			"reused_existing_tool": False,
			"total_latency_ms": 1000,
			"forge_latency_ms": 700,
			"difficulty": 2,
			"tool_family": "csv_processing",
		},
	]
	report = build_report(rows)
	assert report["total_samples"] == 2
	assert "tool_reuse_rate" in report
	assert report["speedup_ratio"] == 10.0
	assert "per_difficulty" in report
	assert "per_tool_family" in report


def test_runner_mock_mode_smoke() -> None:
	report = run_benchmark(dataset_path="evaluation/benchmark/dataset.json", mode="mock")
	assert report["total_samples"] > 0
	assert report["canonical_samples"] == 80
	assert report["paraphrase_samples"] == 240
	assert set(report["per_pass"]) == {"cold", "warm"}
	assert 0.0 <= report["success_rate"] <= 1.0
	assert 0.0 <= report["tool_reuse_rate"] <= 1.0
	assert isinstance(report.get("results"), list)
	assert "retrieval_trace" in report["results"][0]
	assert report["results"][0]["protocol_pass"] == "cold"


def test_runner_mock_agent_strategy_smoke() -> None:
	report = run_benchmark(dataset_path="evaluation/benchmark/dataset.json", mode="mock", strategy="agent")
	assert report["strategy"] == "agent"
	assert report["total_samples"] > 0
	assert report["mean_forge_latency_ms"] > 0


def test_runner_backend_mode_smoke(tmp_path, monkeypatch) -> None:
	registry = ToolRegistry(
		skills_dir=str(tmp_path / "skills"),
		chroma_persist_dir=str(tmp_path / "chroma"),
		enable_vector_store=False,
	)
	service = AutoForgeBackendService(registry=registry)
	service.sync()

	dataset = [
		{
			"sample_id": "L1_001",
			"difficulty": 1,
			"query": "Reverse the text 'streamlit'",
			"paraphrases": [
				"Return the reverse of 'streamlit'",
				"Write 'streamlit' backwards",
				"Reverse 'streamlit'",
			],
			"expected_output": "tilmaerts",
			"expected_output_type": "exact",
			"tool_family": "string_ops",
		}
	]
	dataset_path = tmp_path / "dataset.json"
	dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")

	def _fake_backend_query(
		backend_url: str,
		query_text: str,
		strategy: str = "full",
		timeout_s: float = 60.0,
	) -> dict:
		del backend_url, timeout_s
		response = service.handle_query(QueryRequest(query=query_text, strategy=strategy))
		return response.model_dump(mode="json")

	monkeypatch.setattr(runner_module, "_backend_query", _fake_backend_query)

	report = run_benchmark(
		dataset_path=str(dataset_path),
		mode="backend",
		backend_url="http://testserver",
		strategy="full",
	)
	assert report["success_rate"] == 1.0
	assert report["tool_reuse_rate"] > 0.0
	assert report["strategy"] == "full"


def test_benchmark_dataset_is_balanced_and_reports_protocol_counts() -> None:
	dataset_path = Path("evaluation/benchmark/dataset.json")
	ok, errors, difficulty_counts = validate_dataset(dataset_path)
	assert ok, errors
	assert difficulty_counts == {"1": 20, "2": 20, "3": 20, "4": 20}

	stats = stats_dataset(dataset_path)
	assert stats["total_samples"] == 80
	assert stats["cold_queries"] == 80
	assert stats["warm_queries"] == 240
	assert stats["total_eval_queries"] == 320


def test_demo_query_sequence_covers_required_scenarios() -> None:
	demo_path = Path("evaluation/demo_queries.json")
	demo_queries = json.loads(demo_path.read_text(encoding="utf-8"))
	scenarios = {item["scenario"] for item in demo_queries}
	assert {
		"cold_forge",
		"warm_reuse",
		"registry_miss",
		"fallback_success",
		"mcp_invocation",
	}.issubset(scenarios)


def test_agent_demo_runner_mock_report(tmp_path) -> None:
	report = run_agent_demo_cases(
		cases_path="agents/demo_cases.json",
		output_dir=str(tmp_path),
		mock=True,
		limit=2,
	)
	assert report["total_cases"] == 2
	assert report["base_case_count"] == 2
	assert report["repeats"] == 1
	assert report["cold_success_count"] == 2
	assert report["warm_reuse_count"] == 2
	assert Path(report["report_path"]).exists()


def test_agent_demo_runner_mock_repeats(tmp_path) -> None:
	report = run_agent_demo_cases(
		cases_path="agents/demo_cases.json",
		output_dir=str(tmp_path),
		mock=True,
		limit=2,
		repeats=3,
	)
	assert report["total_cases"] == 6
	assert report["base_case_count"] == 2
	assert report["repeats"] == 3
	assert {row["repeat_index"] for row in report["results"]} == {1, 2, 3}
	assert [row["trial_index"] for row in report["results"]] == list(range(1, 7))
	assert report["results"][0]["base_case_id"] == "agent_demo_01_text_reverse"


def test_agent_demo_runner_mock_resume(tmp_path) -> None:
	first = run_agent_demo_cases(
		cases_path="agents/demo_cases.json",
		output_dir=str(tmp_path),
		mock=True,
		limit=2,
		repeats=1,
	)
	resumed = run_agent_demo_cases(
		cases_path="agents/demo_cases.json",
		output_dir=str(tmp_path),
		mock=True,
		limit=2,
		repeats=3,
		resume_from=first["report_path"],
	)
	assert resumed["total_cases"] == 6
	assert [row["trial_index"] for row in resumed["results"]] == list(range(1, 7))
	assert [row["repeat_index"] for row in resumed["results"]] == [1, 1, 2, 2, 3, 3]


def test_build_agent_demo_figures_from_mock_report(tmp_path) -> None:
	report = run_agent_demo_cases(
		cases_path="agents/demo_cases.json",
		output_dir=str(tmp_path),
		mock=True,
		limit=2,
		repeats=2,
	)
	outputs = build_agent_demo_figures(report_path=report["report_path"], output_dir=str(tmp_path / "figures"))
	assert Path(outputs["trial_csv"]).exists()
	assert Path(outputs["repeat_summary_csv"]).exists()
	assert Path(outputs["cumulative_rates_png"]).exists()
	assert Path(outputs["latency_trend_png"]).exists()
	assert Path(outputs["family_rates_png"]).exists()
	assert Path(outputs["latency_box_png"]).exists()
	assert Path(outputs["figure_summary_json"]).exists()


def test_generate_instruction_dataset(tmp_path) -> None:
	output = tmp_path / "instructions.jsonl"
	count = generate_instruction_dataset(
		demo_cases_path="agents/demo_cases.json",
		benchmark_path="evaluation/benchmark/dataset.json",
		output_path=str(output),
		benchmark_limit=3,
	)
	assert count > 3
	lines = output.read_text(encoding="utf-8").strip().splitlines()
	assert len(lines) == count
	assert json.loads(lines[0])["task"] in {"planner", "coder"}


def test_build_final_report_assets(tmp_path) -> None:
	report = run_agent_demo_cases(
		cases_path="agents/demo_cases.json",
		output_dir=str(tmp_path),
		mock=True,
		limit=1,
	)
	eval_report = {
		"mode": "mock",
		"strategy": "full",
		"success_rate": 1.0,
		"tool_reuse_rate": 0.5,
		"error_rate": 0.0,
		"speedup_ratio": 2.0,
		"total_samples": 1,
		"results": [],
	}
	(tmp_path / "eval_report_mock_full_test.json").write_text(json.dumps(eval_report), encoding="utf-8")
	outputs = build_assets(results_dir=str(tmp_path), output_dir=str(tmp_path))
	assert Path(outputs["metrics"]).exists()
	metrics_text = Path(outputs["metrics"]).read_text(encoding="utf-8")
	assert "total_samples" in metrics_text
	assert "| eval_report_mock_full_test.json | mock | full | 1.0 | 0.5 | 0.0 | 2.0 | 1 |" in metrics_text
	assert Path(outputs["failure_taxonomy"]).exists()
	assert Path(outputs["representative_cases"]).exists()
	assert Path(outputs["manifest"]).exists()
	assert Path(report["report_path"]).exists()


def test_build_final_report_assets_filters_latest_by_mode_and_strategy(tmp_path) -> None:
	old_report = {
		"mode": "mock",
		"strategy": "full",
		"success_rate": 0.1,
		"tool_reuse_rate": 0.1,
		"error_rate": 0.9,
		"speedup_ratio": 1.0,
		"total_samples": 1,
		"results": [],
	}
	new_report = {
		"mode": "mock",
		"strategy": "full",
		"success_rate": 1.0,
		"tool_reuse_rate": 0.5,
		"error_rate": 0.0,
		"speedup_ratio": 2.0,
		"total_samples": 2,
		"results": [],
	}
	backend_report = {
		"mode": "backend",
		"strategy": "full",
		"success_rate": 0.2,
		"tool_reuse_rate": 0.2,
		"error_rate": 0.8,
		"speedup_ratio": 1.0,
		"total_samples": 3,
		"results": [],
	}
	old_path = tmp_path / "eval_report_mock_full_old.json"
	new_path = tmp_path / "eval_report_mock_full_new.json"
	backend_path = tmp_path / "eval_report_backend_full_new.json"
	old_path.write_text(json.dumps(old_report), encoding="utf-8")
	new_path.write_text(json.dumps(new_report), encoding="utf-8")
	backend_path.write_text(json.dumps(backend_report), encoding="utf-8")

	old_time = 1_000_000_000
	os.utime(old_path, (old_time, old_time))
	os.utime(new_path, (old_time + 10, old_time + 10))
	os.utime(backend_path, (old_time + 20, old_time + 20))

	outputs = build_assets(
		results_dir=str(tmp_path),
		output_dir=str(tmp_path),
		mode="mock",
		strategies=["full"],
	)
	metrics_text = Path(outputs["metrics"]).read_text(encoding="utf-8")
	assert "eval_report_mock_full_new.json" in metrics_text
	assert "eval_report_mock_full_old.json" not in metrics_text
	assert "eval_report_backend_full_new.json" not in metrics_text


def test_threshold_sweep_counts_fast_enum_paths(tmp_path) -> None:
	dataset = [
		{
			"sample_id": "L1_001",
			"difficulty": 1,
			"query": "Reverse the text 'streamlit'",
			"paraphrases": [],
			"expected_output": "tilmaerts",
			"expected_output_type": "exact",
			"tool_family": "string_ops",
		}
	]
	dataset_path = tmp_path / "dataset.json"
	dataset_path.write_text(json.dumps(dataset, ensure_ascii=False), encoding="utf-8")

	report = run_sweep(
		dataset_path=str(dataset_path),
		thresholds=[0.75],
		include_paraphrases=False,
		strategy="full",
	)

	assert _path_value(PathType.FAST) == "fast"
	assert report["rows"][0]["counts"]["fast"] == 1
	assert report["rows"][0]["fast_rate"] == 1.0
