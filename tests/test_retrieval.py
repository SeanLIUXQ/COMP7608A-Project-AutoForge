from __future__ import annotations

import shutil

from backend.tool_registry import ToolRegistry
from retrieval.router import rank_tools, retrieve_best_tool
from retrieval.tool_store import ToolStore
from shared.schemas import ToolParameter, ToolSchema


def _build_registry(tmp_path) -> ToolRegistry:
    registry = ToolRegistry(
        skills_dir=str(tmp_path / "skills"),
        chroma_persist_dir=str(tmp_path / "chroma"),
        enable_vector_store=False,
    )
    registry.sync()
    return registry


def test_registry_sync_seeds_default_tools(tmp_path) -> None:
    registry = _build_registry(tmp_path)
    assert registry.total_tools() == 5
    assert registry.retrieval_backend == "lexical"


def test_registry_search_finds_best_text_tool(tmp_path) -> None:
    registry = _build_registry(tmp_path)
    hits = registry.search("Reverse the text 'streamlit'", top_k=3)
    assert hits
    assert hits[0].tool.name == "text_basic_query_tool"
    assert hits[0].score >= hits[-1].score


def test_registry_search_ignores_payload_noise_for_intent(tmp_path) -> None:
    registry = _build_registry(tmp_path)
    cases = [
        ("Order [5, 1, 9, 2] ascending", "number_list_query_tool"),
        (
            "Filter rows [{'name': 'Kai', 'score': 88}, {'name': 'Li', 'score': 91}] where score >= 90 and return names",
            "structured_data_query_tool",
        ),
        (
            "Given payload {'prices': [10.0, 11.0, 12.0, 13.0]}, compute 3-point moving average",
            "pipeline_query_tool",
        ),
    ]
    for query, tool_name in cases:
        hits = registry.search(query, top_k=3)
        assert hits[0].tool.name == tool_name
        assert hits[0].score >= 0.75


def test_registry_prefers_canonical_bundle_when_duplicate_tool_id_exists(tmp_path) -> None:
    registry = _build_registry(tmp_path)
    canonical = tmp_path / "skills" / "text_basic_query_tool"
    duplicate = tmp_path / "skills" / "text_basic_query_tool__stale"
    shutil.copytree(canonical, duplicate)

    registry.sync()
    found = registry.get_tool("autoforge-text-basic-v1")
    assert found is not None
    _tool, bundle_dir = found
    assert bundle_dir.name == "text_basic_query_tool"


def test_tool_store_saves_and_queries_forged_tool(tmp_path) -> None:
    registry = ToolRegistry(
        skills_dir=str(tmp_path / "skills"),
        chroma_persist_dir=str(tmp_path / "chroma"),
        enable_vector_store=False,
    )
    store = ToolStore(registry=registry)
    store.sync()

    tool = ToolSchema(
        tool_id="custom-slugify-v1",
        name="slugify_text",
        description="Convert plain text into a lowercase hyphenated slug.",
        parameters=[ToolParameter(name="text", type="string", required=True)],
        source_code="def slugify_text(text: str) -> str:\n    return text.lower().replace(' ', '-')\n",
        json_schema={
            "name": "slugify_text",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    )
    store.save_tool(tool, metadata_extra={"keywords": ["slug", "text"]})

    assert store.get_tool("custom-slugify-v1").name == "slugify_text"
    hits = store.query_similar_tools("make a slug from some text", top_k=3)
    assert any(hit_tool.tool_id == "custom-slugify-v1" for hit_tool, _score in hits)


def test_rank_tools_returns_decision_trace(tmp_path) -> None:
    registry = _build_registry(tmp_path)
    decision = rank_tools("Reverse the text 'streamlit'", registry=registry, top_k=2, threshold=0.1)
    assert decision.accepted is True
    trace = decision.trace()
    assert trace[0]["accepted"] is True
    assert retrieve_best_tool("Reverse the text 'streamlit'", registry=registry, threshold=0.1) is not None
