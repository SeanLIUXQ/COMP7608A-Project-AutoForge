from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _report_files(results_dir: Path) -> list[Path]:
    return sorted(
        results_dir.glob("eval_report_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def _agent_demo_report_files(results_dir: Path) -> list[Path]:
    return sorted(
        results_dir.glob("agent_demo_report_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def _threshold_report_files(results_dir: Path) -> list[Path]:
    return sorted(
        results_dir.glob("threshold_sweep_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def _load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _report_label(path: Path, report: dict[str, Any]) -> str:
    mode = report.get("mode", "unknown")
    strategy = report.get("strategy", "unknown")
    timestamp = str(report.get("timestamp", ""))[:19]
    return f"{strategy} | {mode} | {timestamp or path.name}"


def _summary_row(path: Path, report: dict[str, Any]) -> dict[str, Any]:
    return {
        "label": _report_label(path, report),
        "file": path.name,
        "mode": report.get("mode", "unknown"),
        "strategy": report.get("strategy", "unknown"),
        "success_rate": report.get("success_rate", 0.0),
        "tool_reuse_rate": report.get("tool_reuse_rate", report.get("trr", 0.0)),
        "error_rate": report.get("error_rate", 0.0),
        "speedup_ratio": report.get("speedup_ratio", 0.0),
        "mean_fast_latency_ms": report.get("mean_fast_latency_ms", 0.0),
        "mean_slow_latency_ms": report.get("mean_slow_latency_ms", 0.0),
        "total_samples": int(report.get("total_samples", 0)),
        "canonical_samples": int(report.get("canonical_samples", 0)),
        "paraphrase_samples": int(report.get("paraphrase_samples", 0)),
    }


def _load_dataset_stats(dataset_path: Path) -> dict[str, Any]:
    if not dataset_path.exists():
        return {}
    rows = json.loads(dataset_path.read_text(encoding="utf-8"))
    difficulty = Counter(str(row.get("difficulty", "unknown")) for row in rows)
    families = Counter(str(row.get("tool_family", "unknown")) for row in rows)
    paraphrases = [len(row.get("paraphrases", [])) for row in rows]
    return {
        "total_samples": len(rows),
        "difficulty_counts": dict(sorted(difficulty.items())),
        "tool_family_counts": dict(sorted(families.items())),
        "average_paraphrases": round(sum(paraphrases) / len(paraphrases), 2) if paraphrases else 0.0,
    }


def _load_demo_queries(project_root: Path) -> list[dict[str, Any]]:
    demo_path = project_root / "evaluation" / "demo_queries.json"
    if not demo_path.exists():
        return []
    return json.loads(demo_path.read_text(encoding="utf-8"))


def _safe_client_payload(client: Any, method_name: str) -> dict[str, Any]:
    if client is None or not hasattr(client, method_name):
        return {}
    try:
        return getattr(client, method_name)()
    except Exception:
        return {}


def _render_backend_summary(client: Any | None = None) -> None:
    st.subheader("Backend summary")
    health = _safe_client_payload(client, "health")
    tools_payload = _safe_client_payload(client, "list_tools")
    tools = tools_payload.get("tools", [])

    cols = st.columns(4)
    cols[0].metric("Status", health.get("status", "unknown"))
    cols[1].metric("Tools", int(health.get("total_tools", len(tools))))
    cols[2].metric("Retrieval", health.get("retrieval_backend", "-"))
    cols[3].metric("Threshold", health.get("similarity_threshold", "-"))

    if tools:
        st.markdown("**Featured tools**")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "name": tool.get("name", "unknown"),
                        "parameters": len(tool.get("parameters", [])),
                        "keywords": ", ".join(tool.get("keywords", [])[:4]),
                        "description": tool.get("description", ""),
                    }
                    for tool in tools[:5]
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
        catalog_df = pd.DataFrame(
            [
                {
                    "tool": tool.get("name", "unknown"),
                    "keywords": len(tool.get("keywords", [])),
                    "parameters": len(tool.get("parameters", [])),
                }
                for tool in tools
            ]
        )
        fig = px.bar(catalog_df, x="tool", y=["keywords", "parameters"], barmode="group", title="Tool catalog profile")
        st.plotly_chart(fig, use_container_width=True)


def _render_dataset_summary() -> None:
    project_root = _project_root()
    dataset_path = project_root / "evaluation" / "benchmark" / "dataset.json"
    stats = _load_dataset_stats(dataset_path)
    st.subheader("Benchmark design")
    if not stats:
        st.info("Benchmark dataset not found.")
        return

    cols = st.columns(4)
    cols[0].metric("Samples", stats["total_samples"])
    cols[1].metric("Difficulty buckets", len(stats["difficulty_counts"]))
    cols[2].metric("Tool families", len(stats["tool_family_counts"]))
    cols[3].metric("Avg paraphrases", stats["average_paraphrases"])

    left, right = st.columns([1, 1], gap="large")
    with left:
        diff_df = pd.DataFrame(
            [{"difficulty": key, "samples": value} for key, value in stats["difficulty_counts"].items()]
        )
        st.plotly_chart(
            px.bar(diff_df, x="difficulty", y="samples", title="Balanced difficulty buckets"),
            use_container_width=True,
        )
    with right:
        fam_df = pd.DataFrame(
            [{"tool_family": key, "samples": value} for key, value in stats["tool_family_counts"].items()]
        ).sort_values("samples", ascending=False)
        st.plotly_chart(
            px.bar(fam_df.head(10), x="tool_family", y="samples", title="Top tool families"),
            use_container_width=True,
        )

    st.caption(f"Dataset: {dataset_path.relative_to(project_root)}")

    demo_queries = _load_demo_queries(project_root)
    if demo_queries:
        st.subheader("Fixed demo query order")
        demo_df = pd.DataFrame(demo_queries).sort_values("order")
        st.dataframe(
            demo_df[["order", "scenario", "strategy", "query", "expected_focus"]],
            hide_index=True,
            use_container_width=True,
        )


def _retrieval_decision(row: dict[str, Any]) -> str:
    trace = row.get("retrieval_trace") or []
    if not trace:
        return "no_trace"
    if any(bool(item.get("accepted")) for item in trace if isinstance(item, dict)):
        return "accepted"
    return "rejected"


def _failure_reason(row: dict[str, Any]) -> str:
    if row.get("error"):
        return str(row["error"])
    return str(row.get("verdict_reason", "mismatch"))


def _render_failure_explorer(failures: list[dict[str, Any]]) -> None:
    st.markdown("**Failure explorer**")
    df = pd.DataFrame(
        [
            {
                **row,
                "failure_reason": _failure_reason(row),
                "retrieval_decision": _retrieval_decision(row),
            }
            for row in failures
        ]
    )

    filter_cols = st.columns(4)
    difficulties = sorted(str(value) for value in df["difficulty"].dropna().unique())
    families = sorted(str(value) for value in df["tool_family"].dropna().unique())
    reasons = sorted(str(value) for value in df["failure_reason"].dropna().unique())
    decisions = sorted(str(value) for value in df["retrieval_decision"].dropna().unique())

    selected_difficulties = filter_cols[0].multiselect("Difficulty", difficulties, default=difficulties)
    selected_families = filter_cols[1].multiselect("Tool family", families, default=families)
    selected_reasons = filter_cols[2].multiselect("Error reason", reasons, default=reasons)
    selected_decisions = filter_cols[3].multiselect("Retrieval", decisions, default=decisions)

    filtered = df[
        df["difficulty"].astype(str).isin(selected_difficulties)
        & df["tool_family"].astype(str).isin(selected_families)
        & df["failure_reason"].astype(str).isin(selected_reasons)
        & df["retrieval_decision"].astype(str).isin(selected_decisions)
    ]

    st.caption(f"Showing {len(filtered)} of {len(df)} failure rows")
    display_columns = [
        "sample_id",
        "protocol_pass",
        "difficulty",
        "tool_family",
        "retrieval_decision",
        "path_taken",
        "tool_name",
        "failure_reason",
        "query",
    ]
    available_columns = [column for column in display_columns if column in filtered.columns]
    st.dataframe(filtered[available_columns].head(100), hide_index=True, use_container_width=True)


def _render_single_report(path: Path, report: dict[str, Any]) -> None:
    st.caption(f"Loaded report: {path.name}")
    cols = st.columns(6)
    cols[0].metric("Success Rate", f"{report.get('success_rate', 0.0):.3f}")
    cols[1].metric("Tool Reuse", f"{report.get('tool_reuse_rate', report.get('trr', 0.0)):.3f}")
    cols[2].metric("Error Rate", f"{report.get('error_rate', 0.0):.3f}")
    cols[3].metric("Speedup", f"{report.get('speedup_ratio', 0.0):.2f}x")
    cols[4].metric("Fast mean", f"{report.get('mean_fast_latency_ms', 0.0):.1f} ms")
    cols[5].metric("Samples", int(report.get("total_samples", 0)))

    path_distribution = report.get("path_distribution", {})
    if path_distribution:
        path_df = pd.DataFrame([{"path_taken": key, "count": value} for key, value in path_distribution.items()])
        st.plotly_chart(px.bar(path_df, x="path_taken", y="count", title="Path Distribution"), use_container_width=True)

    per_pass = report.get("per_pass", {})
    if per_pass:
        pass_df = pd.DataFrame([{"pass": key, **value} for key, value in per_pass.items()])
        st.plotly_chart(
            px.bar(
                pass_df,
                x="pass",
                y=["success_rate", "tool_reuse_rate", "error_rate"],
                barmode="group",
                title="Cold vs warm protocol metrics",
            ),
            use_container_width=True,
        )

    per_difficulty = report.get("per_difficulty", {})
    if per_difficulty:
        diff_df = pd.DataFrame([{"difficulty": key, **value} for key, value in per_difficulty.items()])
        st.plotly_chart(
            px.bar(
                diff_df,
                x="difficulty",
                y=["success_rate", "tool_reuse_rate", "error_rate"],
                barmode="group",
                title="Metrics by difficulty",
            ),
            use_container_width=True,
        )

    per_family = report.get("per_tool_family", {})
    if per_family:
        family_df = pd.DataFrame([{"tool_family": key, **value} for key, value in per_family.items()]).sort_values(
            "success_rate",
            ascending=True,
        )
        st.plotly_chart(
            px.bar(
                family_df,
                x="success_rate",
                y="tool_family",
                orientation="h",
                color="tool_reuse_rate",
                title="Per-family success rate",
            ),
            use_container_width=True,
        )

    results = report.get("results", [])
    failures = [row for row in results if row.get("error") or not row.get("matched", True)]
    if failures:
        _render_failure_explorer(failures)


def _render_report_comparison(loaded_reports: list[tuple[Path, dict[str, Any]]]) -> None:
    st.markdown("**Report comparison**")
    summary_df = pd.DataFrame([_summary_row(path, report) for path, report in loaded_reports])
    st.dataframe(summary_df, hide_index=True, use_container_width=True)
    if summary_df.empty:
        return

    x_axis = "strategy" if summary_df["strategy"].is_unique else "label"
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            px.bar(
                summary_df,
                x=x_axis,
                y=["success_rate", "tool_reuse_rate", "error_rate"],
                barmode="group",
                title="Success / TRR / error rate",
            ),
            use_container_width=True,
        )
    with right:
        st.plotly_chart(
            px.bar(summary_df, x=x_axis, y="speedup_ratio", color="strategy", title="Speedup ratio"),
            use_container_width=True,
        )

    pass_rows = []
    for path, report in loaded_reports:
        label = _report_label(path, report)
        for pass_name, metrics in (report.get("per_pass") or {}).items():
            pass_rows.append(
                {
                    "label": label,
                    "strategy": report.get("strategy", "unknown"),
                    "pass": pass_name,
                    "success_rate": metrics.get("success_rate", 0.0),
                    "tool_reuse_rate": metrics.get("tool_reuse_rate", metrics.get("trr", 0.0)),
                    "error_rate": metrics.get("error_rate", 0.0),
                }
            )
    if pass_rows:
        pass_df = pd.DataFrame(pass_rows)
        st.plotly_chart(
            px.bar(
                pass_df,
                x="strategy",
                y="tool_reuse_rate",
                color="pass",
                barmode="group",
                title="Cold/warm tool reuse by strategy",
            ),
            use_container_width=True,
        )


def _render_agent_demo_reports(root: Path) -> None:
    files = _agent_demo_report_files(root)
    if not files:
        return
    st.subheader("Agent demo reports")
    latest_path = files[0]
    report = _load_report(latest_path)
    st.caption(f"Loaded agent demo report: {latest_path.name}")
    cols = st.columns(4)
    cols[0].metric("Cases", int(report.get("total_cases", 0)))
    cols[1].metric("Cold success", f"{report.get('cold_success_rate', 0.0):.3f}")
    cols[2].metric("Warm success", f"{report.get('warm_success_rate', 0.0):.3f}")
    cols[3].metric("Warm reuse", f"{report.get('warm_reuse_rate', 0.0):.3f}")

    rows = report.get("results", [])
    if rows:
        df = pd.DataFrame(rows)
        display_columns = [
            "id",
            "family",
            "cold_success",
            "warm_success",
            "warm_reused_existing_tool",
            "tool_name",
            "failure_type",
            "forge_trace_id",
            "forge_log_path",
        ]
        available = [column for column in display_columns if column in df.columns]
        st.dataframe(df[available], hide_index=True, use_container_width=True)
        if {"cold_success", "warm_success"}.issubset(df.columns):
            failures = df[(df["cold_success"] == False) | (df["warm_success"] == False)]  # noqa: E712
            if not failures.empty and "failure_type" in failures.columns:
                fail_counts = failures["failure_type"].fillna("unknown").value_counts().reset_index()
                fail_counts.columns = ["failure_type", "count"]
                st.plotly_chart(px.bar(fail_counts, x="failure_type", y="count", title="Agent demo failure types"), use_container_width=True)


def _render_threshold_sweep(root: Path) -> None:
    files = _threshold_report_files(root)
    if not files:
        return
    st.subheader("Threshold sweep")
    latest_path = files[0]
    report = _load_report(latest_path)
    st.caption(f"Loaded threshold sweep: {latest_path.name}")
    rows = report.get("rows", [])
    if not rows:
        return
    flat_rows = []
    for row in rows:
        flat = {key: value for key, value in row.items() if key != "counts"}
        counts = row.get("counts") or {}
        for key, value in counts.items():
            flat[f"count_{key}"] = value
        flat_rows.append(flat)
    df = pd.DataFrame(flat_rows)
    st.dataframe(df, hide_index=True, use_container_width=True)
    if {"threshold", "success_rate", "fast_rate"}.issubset(df.columns):
        st.plotly_chart(
            px.line(df, x="threshold", y=["success_rate", "fast_rate", "fast_incorrect_rate"], markers=True, title="Threshold trade-off"),
            use_container_width=True,
        )


def render_dashboard_page(client: Any | None = None, results_dir: str = "evaluation/results") -> None:
    st.title("Dashboard")
    st.caption("Monitor backend readiness, benchmark coverage, and saved evaluation reports.")

    _render_backend_summary(client)
    _render_dataset_summary()

    st.subheader("Evaluation reports")
    root = Path(results_dir)
    if not root.exists():
        root = _project_root() / "evaluation" / "results"

    _render_agent_demo_reports(root)
    _render_threshold_sweep(root)

    report_files = _report_files(root)
    if not report_files:
        st.info("No evaluation report found yet. Run evaluation to populate this section.")
        return

    loaded_by_label = {_report_label(path, _load_report(path)): (path, _load_report(path)) for path in report_files}
    labels = list(loaded_by_label.keys())
    backend_labels = [label for label, (_, report) in loaded_by_label.items() if report.get("mode") == "backend"]
    default_pool = backend_labels or labels
    default_selection = default_pool[: min(4, len(default_pool))]
    selected_labels = st.multiselect(
        "Choose reports to compare",
        labels,
        default=default_selection,
        key="dashboard_report_compare_selection_v2",
    )
    if not selected_labels:
        st.info("Select at least one report to inspect.")
        return

    selected_reports = [loaded_by_label[label] for label in selected_labels]
    if len(selected_reports) > 1:
        _render_report_comparison(selected_reports)

    detail_label = st.selectbox(
        "Inspect one report in detail",
        selected_labels,
        key="dashboard_report_detail_selection_v2",
    )
    detail_path, detail_report = loaded_by_label[detail_label]
    _render_single_report(detail_path, detail_report)


def main() -> None:
    try:
        from frontend.runtime import build_client
    except ModuleNotFoundError:
        from runtime import build_client

    client = build_client(active_page="Dashboard", page_title="Dashboard")
    render_dashboard_page(client)


if __name__ == "__main__":
    main()
