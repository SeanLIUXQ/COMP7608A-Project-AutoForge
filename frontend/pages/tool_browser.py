from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st

if TYPE_CHECKING:
    from frontend.api_client import AutoForgeAPIClient


def _select_tool(tools: list[dict]) -> str | None:
    if not tools:
        return None

    options = {f"{tool['name']} ({tool['tool_id']})": tool["tool_id"] for tool in tools}
    current = st.session_state.get("selected_tool_id")
    if current not in options.values():
        current = next(iter(options.values()))
        st.session_state.selected_tool_id = current

    labels = list(options.keys())
    default_index = next(
        (index for index, label in enumerate(labels) if options[label] == current),
        0,
    )
    selected_label = st.radio("Available tools", labels, index=default_index, label_visibility="collapsed")
    selected_tool_id = options[selected_label]
    st.session_state.selected_tool_id = selected_tool_id
    return selected_tool_id


def _render_invoke_panel(client: "AutoForgeAPIClient", tool: dict) -> None:
    st.markdown("**Direct invoke**")
    query_default = f"Try {tool['name']} with a natural-language query"
    query_text = st.text_area(
        "Natural-language input",
        value="",
        placeholder=query_default,
        key=f"invoke_query_{tool['tool_id']}",
        height=100,
    )

    raw_payload = st.text_area(
        "Optional raw JSON payload",
        value="",
        placeholder="""{"query": "Reverse the text 'streamlit'"}""",
        key=f"invoke_payload_{tool['tool_id']}",
        height=100,
    )

    if st.button("Invoke tool", key=f"invoke_button_{tool['tool_id']}", type="primary"):
        payload: dict
        if raw_payload.strip():
            try:
                payload = json.loads(raw_payload)
                if not isinstance(payload, dict):
                    raise ValueError("Payload must be a JSON object.")
            except Exception as exc:
                st.error(f"Invalid JSON payload: {exc}")
                return
        else:
            payload = {"query": query_text.strip()} if query_text.strip() else {}

        try:
            response = client.invoke_tool(tool["tool_id"], payload)
            if response.get("success"):
                st.success("Invocation succeeded.")
                st.code((response.get("stdout") or "").strip() or "(empty output)")
            else:
                st.error(response.get("stderr") or "Invocation failed.")
        except Exception as exc:
            st.error(f"Invoke failed: {exc}")


def render_tool_browser_page(client: "AutoForgeAPIClient") -> None:
    st.title("Tool Browser")
    st.caption("Inspect registry entries, schemas, source code, and sandbox invocation behavior.")

    payload = client.list_tools()
    tools = payload.get("tools", [])
    cols = st.columns(3)
    cols[0].metric("Total tools", int(payload.get("total", len(tools))))
    cols[1].metric("Mode", client.mode)
    cols[2].metric("Strategy", client.strategy)
    if not tools:
        st.info("No tools available yet.")
        return

    search = st.text_input("Filter tools", placeholder="Search by name, description, or keyword")
    filtered = [
        tool
        for tool in tools
        if not search.strip()
        or search.lower() in tool.get("name", "").lower()
        or search.lower() in tool.get("description", "").lower()
        or any(search.lower() in keyword.lower() for keyword in tool.get("keywords", []))
    ]
    if not filtered:
        st.warning("No tools matched the current filter.")
        return

    overview_df = pd.DataFrame(
        [
            {
                "name": tool.get("name", "unknown"),
                "parameters": len(tool.get("parameters", [])),
                "keywords": ", ".join(tool.get("keywords", [])[:4]),
                "description": tool.get("description", ""),
            }
            for tool in filtered
        ]
    )
    st.dataframe(overview_df, hide_index=True, use_container_width=True)

    left, right = st.columns([1.0, 1.4], gap="large")
    with left:
        st.markdown("**Select tool**")
        selected_tool_id = _select_tool(filtered)

    if not selected_tool_id:
        return

    tool = client.get_tool(selected_tool_id)

    with right:
        st.subheader(tool.get("name", "unknown"))
        st.caption(tool.get("description", ""))

        overview_tab, invoke_tab, source_tab = st.tabs(["Overview", "Invoke", "Source"])
        with overview_tab:
            info_cols = st.columns(2)
            info_cols[0].metric("Tool ID", tool.get("tool_id", "-"))
            info_cols[1].metric("Parameters", len(tool.get("parameters", [])))
            st.markdown("**Parameters**")
            params = tool.get("parameters", [])
            if params:
                st.dataframe(pd.DataFrame(params), hide_index=True, use_container_width=True)
            else:
                st.info("This tool declares no parameters.")
            st.markdown("**JSON schema**")
            st.json(tool.get("json_schema", {}))

        with invoke_tab:
            _render_invoke_panel(client, tool)

        with source_tab:
            st.code(tool.get("source_code", ""), language="python")


def main() -> None:
    try:
        from frontend.runtime import build_client
    except ModuleNotFoundError:
        from runtime import build_client

    client = build_client(active_page="Tool Browser", page_title="Tool Browser")
    render_tool_browser_page(client)


if __name__ == "__main__":
    main()
