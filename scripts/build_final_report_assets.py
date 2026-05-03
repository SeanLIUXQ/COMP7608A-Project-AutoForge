from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_reports(results_dir: Path, pattern: str) -> list[Path]:
    return sorted(results_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)


def _report_matches(report: dict[str, Any], *, mode: str | None, strategies: set[str] | None) -> bool:
    if mode and str(report.get("mode", "")) != mode:
        return False
    if strategies and str(report.get("strategy", "")) not in strategies:
        return False
    return True


def _select_latest_eval_reports(paths: list[Path], *, mode: str | None, strategies: set[str] | None) -> list[Path]:
    selected: dict[tuple[str, str], Path] = {}
    for path in paths:
        try:
            report = _load_json(path)
        except Exception:
            continue
        if not _report_matches(report, mode=mode, strategies=strategies):
            continue
        key = (str(report.get("mode", "unknown")), str(report.get("strategy", "unknown")))
        if key not in selected:
            selected[key] = path
    return list(selected.values())


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows available._\n"
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join([header, sep, *body]) + "\n"


def _evaluation_summary(report_path: Path) -> dict[str, Any]:
    report = _load_json(report_path)
    return {
        "file": report_path.name,
        "mode": report.get("mode", "unknown"),
        "strategy": report.get("strategy", "unknown"),
        "success_rate": round(float(report.get("success_rate", 0.0) or 0.0), 4),
        "tool_reuse_rate": round(float(report.get("tool_reuse_rate", report.get("trr", 0.0)) or 0.0), 4),
        "error_rate": round(float(report.get("error_rate", 0.0) or 0.0), 4),
        "speedup_ratio": round(float(report.get("speedup_ratio", 0.0) or 0.0), 4),
        "total_samples": report.get("total_samples", 0),
        "total_cases": "",
    }


def _agent_summary(report_path: Path) -> dict[str, Any]:
    report = _load_json(report_path)
    return {
        "file": report_path.name,
        "mode": report.get("mode", "unknown"),
        "strategy": "agent_demo",
        "total_samples": "",
        "total_cases": report.get("total_cases", 0),
        "cold_success_rate": report.get("cold_success_rate", 0.0),
        "warm_success_rate": report.get("warm_success_rate", 0.0),
        "warm_reuse_rate": report.get("warm_reuse_rate", 0.0),
        "duration_seconds": report.get("duration_seconds", 0.0),
    }


def _failure_type(row: dict[str, Any]) -> str:
    if row.get("failure_type"):
        return str(row["failure_type"])
    if row.get("error"):
        return str(row["error"]).splitlines()[0][:80]
    if row.get("cold_error"):
        return str(row["cold_error"]).splitlines()[0][:80]
    if row.get("warm_error"):
        return str(row["warm_error"]).splitlines()[0][:80]
    if row.get("matched") is False:
        return str(row.get("verdict_reason", "mismatch"))
    if row.get("cold_success") is False:
        return "cold_agent_failed"
    if row.get("warm_success") is False:
        return "warm_reuse_failed"
    return "unknown"


def _collect_failure_rows(paths: list[Path]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for path in paths:
        report = _load_json(path)
        for row in report.get("results", []):
            is_failure = bool(row.get("error")) or row.get("matched") is False
            is_failure = is_failure or row.get("cold_success") is False or row.get("warm_success") is False
            if is_failure:
                failures.append(
                    {
                        "source_file": path.name,
                        "sample_id": row.get("sample_id") or row.get("id"),
                        "family": row.get("tool_family") or row.get("family"),
                        "query": row.get("query") or row.get("cold_query"),
                        "path_taken": row.get("path_taken") or row.get("cold_path_taken"),
                        "tool_name": row.get("tool_name"),
                        "failure_type": _failure_type(row),
                        "log_path": row.get("forge_log_path"),
                    }
                )
    return failures


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def build_assets(
    results_dir: str,
    output_dir: str,
    *,
    mode: str | None = None,
    strategies: list[str] | None = None,
) -> dict[str, str]:
    results_path = Path(results_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    strategy_filter = {item.strip() for item in strategies or [] if item.strip()} or None
    eval_reports = _select_latest_eval_reports(
        _latest_reports(results_path, "eval_report_*.json"),
        mode=mode,
        strategies=strategy_filter,
    )
    agent_reports = _latest_reports(results_path, "agent_demo_report_*.json")
    threshold_reports = _latest_reports(results_path, "threshold_sweep_*.json")

    metric_rows = [_evaluation_summary(path) for path in eval_reports]
    metric_rows.extend(_agent_summary(path) for path in agent_reports[:4])
    metrics_md = "# Final Metrics Table\n\n" + _markdown_table(
        metric_rows,
        [
            "file",
            "mode",
            "strategy",
            "success_rate",
            "tool_reuse_rate",
            "error_rate",
            "speedup_ratio",
            "total_samples",
            "total_cases",
            "cold_success_rate",
            "warm_success_rate",
            "warm_reuse_rate",
        ],
    )
    metrics_file = output_path / "final_metrics_table.md"
    metrics_file.write_text(metrics_md, encoding="utf-8")

    failures = _collect_failure_rows([*eval_reports, *agent_reports[:4]])
    counts = Counter(row["failure_type"] for row in failures)
    taxonomy_rows = [{"failure_type": key, "count": value} for key, value in sorted(counts.items())]
    taxonomy_md = "# Failure Taxonomy\n\n" + _markdown_table(taxonomy_rows, ["failure_type", "count"])
    taxonomy_file = output_path / "failure_taxonomy.md"
    taxonomy_file.write_text(taxonomy_md, encoding="utf-8")

    representative_md = "# Representative Cases\n\n" + _markdown_table(
        failures[:10],
        ["source_file", "sample_id", "family", "path_taken", "tool_name", "failure_type", "log_path", "query"],
    )
    representative_file = output_path / "representative_cases.md"
    representative_file.write_text(representative_md, encoding="utf-8")

    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "python": sys.version,
        "platform": platform.platform(),
        "results_dir": str(results_path),
        "mode_filter": mode,
        "strategy_filter": sorted(strategy_filter) if strategy_filter else None,
        "evaluation_reports": [str(path) for path in eval_reports],
        "agent_demo_reports": [str(path) for path in agent_reports[:4]],
        "threshold_reports": [str(path) for path in threshold_reports[:4]],
        "generated_assets": {
            "metrics": str(metrics_file),
            "failure_taxonomy": str(taxonomy_file),
            "representative_cases": str(representative_file),
        },
    }
    manifest_file = output_path / "final_run_manifest.json"
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "metrics": str(metrics_file),
        "failure_taxonomy": str(taxonomy_file),
        "representative_cases": str(representative_file),
        "manifest": str(manifest_file),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build final report assets from saved AutoForge results.")
    parser.add_argument("--results-dir", default="evaluation/results", help="Directory containing result JSON files")
    parser.add_argument("--output-dir", default="evaluation/results", help="Directory for markdown/manifest outputs")
    parser.add_argument("--mode", choices=["mock", "backend"], default=None, help="Optional evaluation mode filter")
    parser.add_argument("--strategies", default="", help="Optional comma-separated strategy filter")
    args = parser.parse_args()
    strategies = [item.strip() for item in args.strategies.split(",") if item.strip()]
    outputs = build_assets(args.results_dir, args.output_dir, mode=args.mode, strategies=strategies)
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
