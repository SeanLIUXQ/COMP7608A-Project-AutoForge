from __future__ import annotations

import argparse
import json
import warnings
from collections import Counter
from pathlib import Path
from typing import Any

import plotly.express as px
import plotly.graph_objects as go


DEFAULT_RESULTS_DIR = "evaluation/results"
DEFAULT_OUTPUT_DIR = "docs/report/images"
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*Kaleido.*")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_reports(results_dir: Path, pattern: str) -> list[Path]:
    return sorted(results_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)


def _select_latest_eval_reports(
    results_dir: Path,
    *,
    mode: str,
    strategies: set[str] | None,
) -> list[Path]:
    selected: dict[str, Path] = {}
    for path in _latest_reports(results_dir, "eval_report_*.json"):
        try:
            report = _load_json(path)
        except Exception:
            continue
        if str(report.get("mode", "")) != mode:
            continue
        strategy = str(report.get("strategy", "unknown"))
        if strategies and strategy not in strategies:
            continue
        if strategy not in selected:
            selected[strategy] = path
    return [selected[key] for key in sorted(selected)]


def _write_figure(fig: go.Figure, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            fig.write_image(str(output), scale=2)
    except ValueError as exc:
        raise RuntimeError(
            "Plotly static image export requires kaleido. Install it with: pip install kaleido"
        ) from exc


def _strategy_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        report = _load_json(path)
        rows.append(
            {
                "file": path.name,
                "strategy": report.get("strategy", "unknown"),
                "success_rate": float(report.get("success_rate", 0.0) or 0.0),
                "tool_reuse_rate": float(report.get("tool_reuse_rate", report.get("trr", 0.0)) or 0.0),
                "error_rate": float(report.get("error_rate", 0.0) or 0.0),
                "speedup_ratio": float(report.get("speedup_ratio", 0.0) or 0.0),
                "mean_fast_latency_ms": float(report.get("mean_fast_latency_ms", 0.0) or 0.0),
                "mean_slow_latency_ms": float(report.get("mean_slow_latency_ms", 0.0) or 0.0),
                "total_samples": int(report.get("total_samples", 0) or 0),
            }
        )
    return rows


def _failure_rows(paths: list[Path]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for path in paths:
        report = _load_json(path)
        for row in report.get("results", []):
            if not (row.get("error") or row.get("matched") is False):
                continue
            failures.append(
                {
                    "strategy": report.get("strategy", "unknown"),
                    "sample_id": row.get("sample_id"),
                    "tool_family": row.get("tool_family"),
                    "reason": str(row.get("error") or row.get("verdict_reason") or "mismatch")[:90],
                }
            )
    return failures


def build_report_figures(
    *,
    results_dir: str,
    output_dir: str,
    mode: str,
    strategies: list[str],
) -> dict[str, str]:
    results_path = Path(results_dir)
    output_path = Path(output_dir)
    strategy_filter = {item.strip() for item in strategies if item.strip()} or None
    eval_paths = _select_latest_eval_reports(results_path, mode=mode, strategies=strategy_filter)
    if not eval_paths:
        raise FileNotFoundError(
            f"No eval_report files found for mode={mode}. Run live evaluation first."
        )

    outputs: dict[str, str] = {}
    strategy_rows = _strategy_rows(eval_paths)
    summary_csv = output_path / f"{mode}_strategy_summary.csv"
    output_path.mkdir(parents=True, exist_ok=True)
    summary_csv.write_text(
        "\n".join(
            [
                "file,strategy,success_rate,tool_reuse_rate,error_rate,speedup_ratio,mean_fast_latency_ms,mean_slow_latency_ms,total_samples",
                *[
                    ",".join(str(row[key]) for key in [
                        "file",
                        "strategy",
                        "success_rate",
                        "tool_reuse_rate",
                        "error_rate",
                        "speedup_ratio",
                        "mean_fast_latency_ms",
                        "mean_slow_latency_ms",
                        "total_samples",
                    ])
                    for row in strategy_rows
                ],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    outputs["strategy_summary_csv"] = str(summary_csv)

    comparison_rows: list[dict[str, Any]] = []
    for row in strategy_rows:
        for metric in ("success_rate", "tool_reuse_rate", "error_rate"):
            comparison_rows.append({"strategy": row["strategy"], "metric": metric, "value": row[metric]})
    fig = px.bar(
        comparison_rows,
        x="strategy",
        y="value",
        color="metric",
        barmode="group",
        title=f"Strategy comparison ({mode})",
        text_auto=".3f",
    )
    fig.update_layout(yaxis_title="Rate", xaxis_title="Strategy", legend_title="Metric")
    out = output_path / f"{mode}_strategy_comparison.png"
    _write_figure(fig, out)
    outputs["strategy_comparison_png"] = str(out)

    fig = px.bar(
        strategy_rows,
        x="strategy",
        y="speedup_ratio",
        text="speedup_ratio",
        title=f"Speedup ratio by strategy ({mode})",
    )
    fig.update_traces(texttemplate="%{text:.2f}x")
    fig.update_layout(yaxis_title="Slow mean / fast mean", xaxis_title="Strategy")
    out = output_path / f"{mode}_speedup_ratio.png"
    _write_figure(fig, out)
    outputs["speedup_ratio_png"] = str(out)

    full_path = next(
        (path for path in eval_paths if str(_load_json(path).get("strategy")) == "full"),
        eval_paths[0],
    )
    full_report = _load_json(full_path)
    per_family = full_report.get("per_tool_family") or {}
    family_rows = [
        {
            "tool_family": family,
            "success_rate": float(metrics.get("success_rate", 0.0) or 0.0),
            "tool_reuse_rate": float(metrics.get("tool_reuse_rate", metrics.get("trr", 0.0)) or 0.0),
            "count": int(metrics.get("count", 0) or 0),
        }
        for family, metrics in per_family.items()
    ]
    if family_rows:
        fig = px.bar(
            sorted(family_rows, key=lambda row: row["success_rate"]),
            x="success_rate",
            y="tool_family",
            color="tool_reuse_rate",
            orientation="h",
            title=f"Per-family success rate ({mode}, full)",
        )
        fig.update_layout(xaxis_title="Success rate", yaxis_title="Tool family")
        out = output_path / f"{mode}_per_family_success.png"
        _write_figure(fig, out)
        outputs["per_family_success_png"] = str(out)

    threshold_path = next(iter(_latest_reports(results_path, "threshold_sweep_*.json")), None)
    if threshold_path:
        threshold_report = _load_json(threshold_path)
        threshold_rows = threshold_report.get("rows", [])
        if threshold_rows:
            flat_rows = []
            for row in threshold_rows:
                for metric in ("success_rate", "fast_rate", "fast_incorrect_rate"):
                    flat_rows.append({"threshold": row.get("threshold"), "metric": metric, "value": row.get(metric, 0.0)})
            fig = px.line(
                flat_rows,
                x="threshold",
                y="value",
                color="metric",
                markers=True,
                title="Retrieval threshold trade-off",
            )
            fig.update_layout(yaxis_title="Rate", xaxis_title="Similarity threshold")
            out = output_path / "threshold_tradeoff.png"
            _write_figure(fig, out)
            outputs["threshold_tradeoff_png"] = str(out)

    failures = _failure_rows(eval_paths)
    if failures:
        counts = Counter(row["reason"] for row in failures)
        failure_rows = [{"reason": reason, "count": count} for reason, count in counts.most_common(12)]
        fig = px.bar(failure_rows, x="count", y="reason", orientation="h", title=f"Failure taxonomy ({mode})")
        fig.update_layout(xaxis_title="Count", yaxis_title="Failure reason")
        out = output_path / f"{mode}_failure_taxonomy.png"
        _write_figure(fig, out)
        outputs["failure_taxonomy_png"] = str(out)

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PNG/CSV assets for the final report.")
    parser.add_argument("--results-dir", default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--mode", default="backend", choices=["backend", "mock"])
    parser.add_argument("--strategies", default="full,no_retrieval,registry_only")
    args = parser.parse_args()
    strategies = [item.strip() for item in args.strategies.split(",") if item.strip()]
    outputs = build_report_figures(
        results_dir=args.results_dir,
        output_dir=args.output_dir,
        mode=args.mode,
        strategies=strategies,
    )
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
