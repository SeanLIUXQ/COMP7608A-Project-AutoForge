from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import matplotlib.pyplot as plt


DEFAULT_REPORT = "evaluation/results/agent_demo_report_agent_20260502_074909.json"
DEFAULT_OUTPUT_DIR = "docs/report/real_agent_evidence/figures"


def _load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _rate(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if row.get(key)) / len(rows)


def _latency_seconds(row: dict[str, Any], key: str) -> float:
    value = row.get(key)
    try:
        return float(value or 0.0) / 1000.0
    except Exception:
        return 0.0


def _write_csv(rows: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "trial_index",
        "repeat_index",
        "base_case_id",
        "family",
        "tool_name",
        "cold_success",
        "warm_success",
        "warm_reused_existing_tool",
        "cold_latency_s",
        "warm_latency_s",
        "attempts",
        "failure_type",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            summary = row.get("forge_summary") or {}
            writer.writerow(
                {
                    "trial_index": row.get("trial_index"),
                    "repeat_index": row.get("repeat_index", 1),
                    "base_case_id": row.get("base_case_id") or row.get("id"),
                    "family": row.get("family"),
                    "tool_name": row.get("tool_name"),
                    "cold_success": row.get("cold_success"),
                    "warm_success": row.get("warm_success"),
                    "warm_reused_existing_tool": row.get("warm_reused_existing_tool"),
                    "cold_latency_s": round(_latency_seconds(row, "cold_total_latency_ms"), 3),
                    "warm_latency_s": round(_latency_seconds(row, "warm_total_latency_ms"), 3),
                    "attempts": summary.get("attempts"),
                    "failure_type": row.get("failure_type") or "",
                }
            )


def _save(fig: plt.Figure, output: Path) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return str(output)


def _plot_cumulative_rates(rows: list[dict[str, Any]], output: Path) -> str:
    x: list[int] = []
    cold: list[float] = []
    warm: list[float] = []
    reuse: list[float] = []
    prefix: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: int(item.get("trial_index") or 0)):
        prefix.append(row)
        x.append(len(prefix))
        cold.append(_rate(prefix, "cold_success"))
        warm.append(_rate(prefix, "warm_success"))
        reuse.append(_rate(prefix, "warm_reused_existing_tool"))

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(x, cold, marker="o", linewidth=2, label="Cold forge success")
    ax.plot(x, warm, marker="s", linewidth=2, label="Warm task success")
    ax.plot(x, reuse, marker="^", linewidth=2, label="Warm reuse")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Completed real agent trials")
    ax.set_ylabel("Cumulative rate")
    ax.set_title("Cumulative real-agent success and reuse rates")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="lower left")
    return _save(fig, output)


def _plot_latency_trend(rows: list[dict[str, Any]], output: Path) -> str:
    ordered = sorted(rows, key=lambda item: int(item.get("trial_index") or 0))
    x = [int(row.get("trial_index") or index + 1) for index, row in enumerate(ordered)]
    cold = [_latency_seconds(row, "cold_total_latency_ms") for row in ordered]
    warm = [_latency_seconds(row, "warm_total_latency_ms") for row in ordered]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(x, cold, marker="o", linewidth=1.8, label="Cold forge latency")
    ax.plot(x, warm, marker="s", linewidth=1.8, label="Warm latency")
    ax.set_xlabel("Completed real agent trials")
    ax.set_ylabel("Latency (seconds)")
    ax.set_title("Cold vs warm latency over real-agent trials")
    ax.grid(True, alpha=0.25)
    ax.legend()
    return _save(fig, output)


def _plot_family_rates(rows: list[dict[str, Any]], output: Path) -> str:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("family", "unknown"))].append(row)
    families = sorted(grouped)
    cold = [_rate(grouped[family], "cold_success") for family in families]
    warm = [_rate(grouped[family], "warm_success") for family in families]
    reuse = [_rate(grouped[family], "warm_reused_existing_tool") for family in families]

    positions = list(range(len(families)))
    width = 0.25
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar([pos - width for pos in positions], cold, width=width, label="Cold")
    ax.bar(positions, warm, width=width, label="Warm success")
    ax.bar([pos + width for pos in positions], reuse, width=width, label="Warm reuse")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Rate")
    ax.set_title("Real-agent rates by task family")
    ax.set_xticks(positions)
    ax.set_xticklabels(families, rotation=35, ha="right")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    return _save(fig, output)


def _plot_latency_box(rows: list[dict[str, Any]], output: Path) -> str:
    cold = [_latency_seconds(row, "cold_total_latency_ms") for row in rows]
    warm = [_latency_seconds(row, "warm_total_latency_ms") for row in rows]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.boxplot([cold, warm], tick_labels=["Cold forge", "Warm query"], showmeans=True)
    ax.set_ylabel("Latency (seconds)")
    ax.set_title("Latency distribution from raw real-agent trials")
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, output)


def _summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row.get("repeat_index") or 1)].append(row)
    output: list[dict[str, Any]] = []
    for repeat, items in sorted(grouped.items()):
        output.append(
            {
                "repeat_index": repeat,
                "trials": len(items),
                "cold_success_rate": round(_rate(items, "cold_success"), 4),
                "warm_success_rate": round(_rate(items, "warm_success"), 4),
                "warm_reuse_rate": round(_rate(items, "warm_reused_existing_tool"), 4),
                "mean_cold_latency_s": round(mean(_latency_seconds(row, "cold_total_latency_ms") for row in items), 3),
                "mean_warm_latency_s": round(mean(_latency_seconds(row, "warm_total_latency_ms") for row in items), 3),
            }
        )
    return output


def build_agent_demo_figures(*, report_path: str, output_dir: str) -> dict[str, str]:
    report = _load_report(Path(report_path))
    rows = [row for row in report.get("results", []) if isinstance(row, dict)]
    if not rows:
        raise ValueError(f"No result rows found in {report_path}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}

    trial_csv = output_path / "agent_demo_trials_flat.csv"
    _write_csv(rows, trial_csv)
    outputs["trial_csv"] = str(trial_csv)

    repeat_rows = _summary_rows(rows)
    repeat_csv = output_path / "agent_demo_repeat_summary.csv"
    with repeat_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(repeat_rows[0].keys()))
        writer.writeheader()
        writer.writerows(repeat_rows)
    outputs["repeat_summary_csv"] = str(repeat_csv)

    outputs["cumulative_rates_png"] = _plot_cumulative_rates(rows, output_path / "agent_demo_cumulative_rates.png")
    outputs["latency_trend_png"] = _plot_latency_trend(rows, output_path / "agent_demo_latency_trend.png")
    outputs["family_rates_png"] = _plot_family_rates(rows, output_path / "agent_demo_family_rates.png")
    outputs["latency_box_png"] = _plot_latency_box(rows, output_path / "agent_demo_latency_distribution.png")

    summary = {
        "source_report": report_path,
        "total_cases": report.get("total_cases"),
        "base_case_count": report.get("base_case_count"),
        "repeats": report.get("repeats"),
        "cold_success_rate": report.get("cold_success_rate"),
        "cold_example_success_rate": report.get("cold_example_success_rate"),
        "warm_success_rate": report.get("warm_success_rate"),
        "warm_reuse_rate": report.get("warm_reuse_rate"),
        "mean_cold_latency_s": round(mean(_latency_seconds(row, "cold_total_latency_ms") for row in rows), 3),
        "mean_warm_latency_s": round(mean(_latency_seconds(row, "warm_total_latency_ms") for row in rows), 3),
        "duration_minutes": round(float(report.get("duration_seconds") or 0.0) / 60.0, 2),
        "figures": outputs,
    }
    summary_path = output_path / "agent_demo_figure_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    outputs["figure_summary_json"] = str(summary_path)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build matplotlib figures from an AutoForge agent demo report.")
    parser.add_argument("--report", default=DEFAULT_REPORT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    outputs = build_agent_demo_figures(report_path=args.report, output_dir=args.output_dir)
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

