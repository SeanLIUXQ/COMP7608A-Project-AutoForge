from __future__ import annotations

from typing import Any, TYPE_CHECKING

import pandas as pd
import streamlit as st

if TYPE_CHECKING:
    from frontend.api_client import AutoForgeAPIClient


EXAMPLE_QUERIES = [
    "Reverse the text 'streamlit'",
    "Count vowels in the string 'AutoForge'",
    "Given payload {'prices': [10.0, 11.0, 12.0, 13.0]}, compute 3-point moving average",
]


def _render_result(result: Any) -> None:
    if isinstance(result, (dict, list)):
        st.json(result)
    elif result is None:
        st.write("-")
    else:
        st.write(result)


def _path_chip(response: dict[str, Any]) -> str:
    path = str(response.get("path_taken", "-")).lower()
    if path == "fast":
        return '<span class="af-chip af-chip-ok">fast path</span>'
    if path == "slow":
        return '<span class="af-chip af-chip-warn">slow path</span>'
    return f'<span class="af-chip">{path}</span>'


def _append_history(query: str, response: dict[str, Any]) -> None:
    st.session_state.chat_history.append(
        {
            "query": query,
            "response": response,
        }
    )


def _render_history() -> None:
    history = st.session_state.get("chat_history", [])
    if not history:
        st.info("Run a query to build a local chat history for this session.")
        return

    for index, item in enumerate(reversed(history), start=1):
        response = item["response"]
        with st.expander(f"Request {index}: {item['query']}", expanded=index == 1):
            st.markdown(_path_chip(response), unsafe_allow_html=True)
            cols = st.columns(4)
            cols[0].metric("Path", str(response.get("path_taken", "-")))
            cols[1].metric("Tool", str(response.get("tool_name", "-")))
            cols[2].metric("Latency", f"{float(response.get('total_latency_ms', 0.0) or 0.0):.1f} ms")
            cols[3].metric("Error", "yes" if response.get("error") else "no")
            st.write("Result")
            _render_result(response.get("result"))
            trace = response.get("retrieval_trace") or []
            if trace:
                with st.expander("Retrieval trace", expanded=False):
                    st.dataframe(pd.DataFrame(trace), hide_index=True, use_container_width=True)
            if response.get("error"):
                st.error(str(response["error"]))


def render_chat_page(client: "AutoForgeAPIClient") -> None:
    st.title("AutoForge Chat")
    st.caption("Run a query, inspect reuse behavior, and review retrieval decisions without leaving the workflow.")

    with st.container(border=True):
        st.markdown("**Examples**")
        sample_cols = st.columns(len(EXAMPLE_QUERIES))
        for index, query in enumerate(EXAMPLE_QUERIES):
            if sample_cols[index].button(query, key=f"chat_example_{index}", use_container_width=True):
                st.session_state.chat_query_input = query

    query = st.text_area(
        "Your query",
        key="chat_query_input",
        placeholder="e.g. Reverse the text 'streamlit'",
        height=120,
    )

    action_cols = st.columns([1, 1, 6])
    run_clicked = action_cols[0].button("Run", type="primary", use_container_width=True)
    clear_clicked = action_cols[1].button("Clear history", use_container_width=True)

    if clear_clicked:
        st.session_state.chat_history = []
        st.rerun()

    if run_clicked:
        if not query.strip():
            st.warning("Please enter a query.")
        else:
            with st.spinner("Executing query against the current backend..."):
                try:
                    response = client.query(query=query.strip())
                    _append_history(query.strip(), response)
                    st.success("Query completed.")
                    cols = st.columns(5)
                    cols[0].metric("Path", response.get("path_taken", "-"))
                    cols[1].metric("Tool", response.get("tool_name", "-"))
                    cols[2].metric("Score", f"{float(response.get('search_score', 0.0) or 0.0):.3f}")
                    cols[3].metric("Total", f"{float(response.get('total_latency_ms', 0.0) or 0.0):.1f} ms")
                    cols[4].metric("Reused", "yes" if response.get("reused_existing_tool") else "no")
                except Exception as exc:
                    st.error(f"Request failed: {exc}")

    st.subheader("Recent activity")
    _render_history()


def main() -> None:
    try:
        from frontend.runtime import build_client
    except ModuleNotFoundError:
        from runtime import build_client

    client = build_client(active_page="Chat", page_title="AutoForge Chat")
    render_chat_page(client)


if __name__ == "__main__":
    main()
