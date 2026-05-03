from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import streamlit as st


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
for _path in (str(PROJECT_ROOT), str(CURRENT_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

try:
    from frontend.api_client import AutoForgeAPIClient
except ModuleNotFoundError:
    from api_client import AutoForgeAPIClient


DEFAULT_BACKEND_URL = os.getenv("AUTOFORGE_BACKEND_URL", "http://127.0.0.1:8000")
DEFAULT_FRONTEND_MODE = os.getenv("AUTOFORGE_FRONTEND_MODE", "backend").strip().lower()


def _default_mode() -> str:
    return "mock" if DEFAULT_FRONTEND_MODE == "mock" else "backend"


def ensure_frontend_state() -> None:
    if "backend_url" not in st.session_state or not str(st.session_state.backend_url or "").strip():
        st.session_state.backend_url = DEFAULT_BACKEND_URL
    if "mode" not in st.session_state:
        st.session_state.mode = _default_mode()
    if "strategy" not in st.session_state:
        st.session_state.strategy = "full"
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "selected_tool_id" not in st.session_state:
        st.session_state.selected_tool_id = None


def _safe_health(client: AutoForgeAPIClient) -> dict[str, Any] | None:
    try:
        return client.health()
    except Exception:
        return None


def inject_theme_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --af-ink: #17202a;
          --af-muted: #617182;
          --af-line: #d8e0e8;
          --af-soft: #f6f8fb;
          --af-accent: #277c6f;
          --af-warn: #ad6b1f;
          --af-danger: #a63d40;
        }
        .block-container {
          padding-top: 2rem;
          padding-bottom: 3rem;
          max-width: 1280px;
        }
        div[data-testid="stMetric"] {
          background: #ffffff;
          border: 1px solid var(--af-line);
          border-radius: 8px;
          padding: 0.85rem 1rem;
          box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        div[data-testid="stMetric"] label {
          color: var(--af-muted);
        }
        .af-panel {
          border: 1px solid var(--af-line);
          border-radius: 8px;
          background: #ffffff;
          padding: 1rem;
          margin-bottom: 1rem;
        }
        .af-kicker {
          color: var(--af-accent);
          font-size: 0.82rem;
          font-weight: 700;
          letter-spacing: 0;
          margin-bottom: 0.25rem;
        }
        .af-subtle {
          color: var(--af-muted);
          font-size: 0.92rem;
        }
        .af-chip {
          display: inline-block;
          border: 1px solid var(--af-line);
          border-radius: 999px;
          padding: 0.16rem 0.55rem;
          margin: 0 0.25rem 0.25rem 0;
          background: var(--af-soft);
          font-size: 0.82rem;
          color: var(--af-ink);
        }
        .af-chip-ok {
          border-color: #b9dbd3;
          background: #edf8f5;
          color: #176458;
        }
        .af-chip-warn {
          border-color: #ead1a8;
          background: #fff7e8;
          color: var(--af-warn);
        }
        .af-chip-danger {
          border-color: #efc0c0;
          background: #fff0f0;
          color: var(--af-danger);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def build_client(active_page: str, page_title: str) -> AutoForgeAPIClient:
    st.set_page_config(page_title=page_title, layout="wide")
    inject_theme_css()
    ensure_frontend_state()

    with st.sidebar:
        st.title("AutoForge")
        st.caption(f"Workspace: {active_page}")
        st.selectbox("Mode", options=["backend", "mock"], key="mode")
        st.selectbox(
            "Strategy",
            options=["full", "no_retrieval", "registry_only", "agent"],
            key="strategy",
        )
        st.text_input("Backend URL", key="backend_url")
        if not str(st.session_state.backend_url or "").strip():
            st.session_state.backend_url = DEFAULT_BACKEND_URL

        client = AutoForgeAPIClient(
            backend_url=st.session_state.backend_url or DEFAULT_BACKEND_URL,
            mode=st.session_state.mode,
            strategy=st.session_state.strategy,
        )

        health = _safe_health(client)
        st.divider()
        st.caption("Session status")
        if health:
            if client.mode == "mock":
                st.warning("Status: mock/demo mode")
            else:
                st.success(f"Status: {health.get('status', 'ok')}")
            st.write(f"Mode: `{client.mode}`")
            st.write(f"Tools: `{health.get('total_tools', '-')}`")
            st.write(f"Retrieval: `{health.get('retrieval_backend', '-')}`")
        else:
            st.error("Backend check failed. Start the live backend, or explicitly switch Mode to mock for demo-only use.")
            st.code(r".\scripts\start_backend.ps1", language="powershell")
            st.stop()

        if hasattr(st, "page_link"):
            st.divider()
            st.caption("Navigate")
            st.page_link("app.py", label="Home")
            st.page_link("pages/chat.py", label="Chat")
            st.page_link("pages/tool_browser.py", label="Tool Browser")
            st.page_link("pages/dashboard.py", label="Dashboard")

    return client
