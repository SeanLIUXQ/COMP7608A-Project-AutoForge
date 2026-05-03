from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
for _path in (str(PROJECT_ROOT), str(CURRENT_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

try:
    from frontend.runtime import build_client
except ModuleNotFoundError:
    from runtime import build_client


def _render_home() -> None:
    client = build_client(active_page="Home", page_title="AutoForge")
    summary = client.dashboard_summary()
    health = summary.get("health", {})
    tools_payload = summary.get("tools", {})
    tools = tools_payload.get("tools", [])

    st.title("AutoForge")
    st.caption("Experiment control surface for Tool-RAG reuse, agent forging, and benchmark analysis.")

    metric_cols = st.columns(4)
    metric_cols[0].metric("Backend", health.get("status", "unknown"))
    metric_cols[1].metric("Mode", client.mode)
    metric_cols[2].metric("Tools", int(health.get("total_tools", len(tools))))
    metric_cols[3].metric("Retrieval", health.get("retrieval_backend", "-"))

    st.markdown(
        """
        <div class="af-panel">
          <div class="af-kicker">Current operating loop</div>
          <div class="af-subtle">
            Query enters Tool-RAG, candidates are scored, compatible tools execute in the sandbox,
            and misses can fall back to deterministic solving or the experimental forge pipeline.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.25, 1.0], gap="large")
    with left:
        st.subheader("Workflow")
        workflow_df = pd.DataFrame(
            [
                {"step": "1. Chat", "purpose": "Submit task queries and inspect path, latency, and retrieval trace."},
                {"step": "2. Tool Browser", "purpose": "Review schemas, source, parameters, and direct invocation behavior."},
                {"step": "3. Dashboard", "purpose": "Track benchmark coverage, reports, path distribution, and failure cases."},
            ]
        )
        st.dataframe(workflow_df, hide_index=True, use_container_width=True)
        if hasattr(st, "page_link"):
            nav_cols = st.columns(3)
            nav_cols[0].page_link("pages/chat.py", label="Open Chat")
            nav_cols[1].page_link("pages/tool_browser.py", label="Open Tool Browser")
            nav_cols[2].page_link("pages/dashboard.py", label="Open Dashboard")

    with right:
        st.subheader("Strategies")
        strategies = health.get("available_strategies", [])
        for name in strategies:
            if name == "full":
                st.markdown('<span class="af-chip af-chip-ok">full: retrieve then fallback</span>', unsafe_allow_html=True)
            elif name == "agent":
                st.markdown('<span class="af-chip af-chip-warn">agent: forge pipeline</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="af-chip">{name}</span>', unsafe_allow_html=True)
        st.caption("Use the sidebar to switch mode and strategy before opening Chat.")

    if tools:
        st.subheader("Tool catalog profile")
        chart_df = pd.DataFrame(
            [
                {
                    "tool": tool.get("name", "unknown"),
                    "keywords": len(tool.get("keywords", [])),
                    "parameters": len(tool.get("parameters", [])),
                }
                for tool in tools
            ]
        )
        fig = px.bar(
            chart_df,
            x="tool",
            y=["keywords", "parameters"],
            barmode="group",
            title=None,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Featured tools")
        featured = pd.DataFrame(
            [
                {
                    "name": tool.get("name", "unknown"),
                    "description": tool.get("description", ""),
                    "keywords": ", ".join(tool.get("keywords", [])[:5]),
                }
                for tool in summary.get("featured_tools", [])[:5]
            ]
        )
        if not featured.empty:
            st.dataframe(featured, hide_index=True, use_container_width=True)


def main() -> None:
    _render_home()


if __name__ == "__main__":
    main()
