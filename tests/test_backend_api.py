from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.service as service_module
from backend.dynamic_api import bind_app, register_all_tools
from backend.mcp.server import call_mcp_tool, mcp_autoforge_query, mcp_tool_catalog
from backend.endpoints import (
    create_dashboard_router,
    create_health_router,
    create_query_router,
    create_tools_router,
)
from backend.service import AutoForgeBackendService
from backend.tool_registry import ToolRegistry
from scripts.verify_mcp_helpers import verify_mcp_helpers
from shared.schemas import ForgeResult, QueryRequest, ToolParameter, ToolSchema


def _build_service(tmp_path) -> AutoForgeBackendService:
    registry = ToolRegistry(
        skills_dir=str(tmp_path / "skills"),
        chroma_persist_dir=str(tmp_path / "chroma"),
        enable_vector_store=False,
    )
    service = AutoForgeBackendService(registry=registry)
    service.sync()
    return service


def _build_client(tmp_path) -> TestClient:
    service = _build_service(tmp_path)
    app = FastAPI()
    bind_app(app)
    app.include_router(create_dashboard_router(service))
    app.include_router(create_health_router(service))
    app.include_router(create_tools_router(service))
    app.include_router(create_query_router(service))
    register_all_tools(service.registry.all_tools())
    return TestClient(app)


def test_backend_health_and_tools_contract(tmp_path) -> None:
    service = _build_service(tmp_path)
    health_payload = service.health().model_dump(mode="json")
    assert health_payload["status"] == "ok"
    assert health_payload["total_tools"] == 5
    assert health_payload["similarity_threshold"] > 0
    assert "full" in health_payload["available_strategies"]

    tools_payload = service.list_tools().model_dump(mode="json")
    assert tools_payload["total"] == 5
    assert any(tool["name"] == "text_basic_query_tool" for tool in tools_payload["tools"])


def test_backend_query_full_strategy_reuses_registry_tool(tmp_path) -> None:
    service = _build_service(tmp_path)
    payload = service.handle_query(
        QueryRequest(query="Reverse the text 'streamlit'", strategy="full")
    ).model_dump(mode="json")
    assert payload["result"] == "tilmaerts"
    assert payload["path_taken"] == "fast"
    assert payload["reused_existing_tool"] is True
    assert payload["tool_name"] == "text_basic_query_tool"
    assert payload["retrieval_trace"]
    assert payload["retrieval_trace"][0]["accepted"] is True


def test_backend_query_explain_only_returns_plan_without_execution(tmp_path) -> None:
    service = _build_service(tmp_path)
    payload = service.handle_query(
        QueryRequest(query="Reverse the text 'streamlit'", strategy="full", explain_only=True)
    ).model_dump(mode="json")
    assert payload["result"] is None
    assert payload["error"] is None
    assert payload["retrieval_trace"]
    assert payload["explain"]
    assert payload["explain"]["would_use_tool"]["tool_name"] == "text_basic_query_tool"
    assert payload["explain"]["planned_payload"] == {"query": "Reverse the text 'streamlit'"}


def test_backend_query_no_retrieval_uses_slow_fallback(tmp_path) -> None:
    service = _build_service(tmp_path)
    payload = service.handle_query(
        QueryRequest(
            query="Given payload {'prices': [10.0, 11.0, 12.0, 13.0]}, compute 3-point moving average",
            strategy="no_retrieval",
        )
    ).model_dump(mode="json")
    assert payload["result"] == [11.0, 12.0]
    assert payload["path_taken"] == "slow"
    assert payload["reused_existing_tool"] is False


def test_backend_fallback_handles_benchmark_paraphrases(tmp_path) -> None:
    service = _build_service(tmp_path)
    cases = [
        ("Order [5, 1, 9, 2] ascending", [1, 2, 5, 9]),
        ("Keep first occurrences only from [1, 2, 2, 3, 1, 4]", [1, 2, 3, 4]),
        ("Add [1.0, 2.5, 3.5] and keep 1 decimal", 7.0),
        ("List the keys in {'name': 'Ada', 'age': 20, 'city': 'HK'} alphabetically", ["age", "city", "name"]),
        ("Check key 'b' inside '{\"a\":1,\"b\":2}'", True),
        (
            "Compute category totals for [{'cat': 'infra', 'amt': 18}, {'cat': 'ml', 'amt': 32}, {'cat': 'infra', 'amt': 22}]",
            {"infra": 40, "ml": 32},
        ),
    ]

    for query, expected in cases:
        payload = service.handle_query(QueryRequest(query=query, strategy="no_retrieval")).model_dump(mode="json")
        assert payload["error"] is None
        assert payload["result"] == expected


def test_backend_optional_llm_match_verify_can_skip_false_positive(tmp_path, monkeypatch) -> None:
    import backend.llm_tools as llm_tools

    registry = ToolRegistry(
        skills_dir=str(tmp_path / "skills"),
        chroma_persist_dir=str(tmp_path / "chroma"),
        enable_vector_store=False,
    )
    service = AutoForgeBackendService(registry=registry, enable_llm_match_verify=True)
    service.sync()

    monkeypatch.setattr(llm_tools, "llm_verify_tool_matches_query", lambda _query, _tool: False)

    payload = service.handle_query(
        QueryRequest(query="Reverse the text 'streamlit'", strategy="full")
    ).model_dump(mode="json")
    assert payload["path_taken"] == "slow"
    assert payload["reused_existing_tool"] is False
    assert payload["result"] == "tilmaerts"


def test_backend_v1_tool_listing_and_invoke(tmp_path) -> None:
    client = _build_client(tmp_path)

    list_resp = client.get("/api/v1/tools")
    assert list_resp.status_code == 200
    tools = list_resp.json()
    assert any(tool["name"] == "text_basic_query_tool" for tool in tools)

    dashboard_resp = client.get("/api/v1/dashboard/summary")
    assert dashboard_resp.status_code == 200
    assert dashboard_resp.json()["health"]["status"] == "ok"
    assert dashboard_resp.json()["tools"]["total"] == 5

    tool_id = next(tool["tool_id"] for tool in tools if tool["name"] == "text_basic_query_tool")
    detail_resp = client.get(f"/api/v1/tools/{tool_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["tool_id"] == tool_id
    assert detail_resp.json()["json_schema"]["name"] == "text_basic_query_tool"

    invoke_resp = client.post(
        f"/api/v1/tools/{tool_id}/invoke",
        json={"payload": {"query": "Reverse the text 'streamlit'"}},
    )
    assert invoke_resp.status_code == 200
    assert invoke_resp.json()["tool_id"] == tool_id
    assert invoke_resp.json()["success"] is True
    assert invoke_resp.json()["stdout"].strip() == "tilmaerts"

    bad_invoke_resp = client.post(
        f"/api/v1/tools/{tool_id}/invoke",
        json={"payload": {}},
    )
    assert bad_invoke_resp.status_code == 422


def test_dynamic_skill_route_registered(tmp_path) -> None:
    client = _build_client(tmp_path)
    openapi = client.app.openapi()
    assert "/api/v1/skills/text_basic_query_tool" in openapi["paths"]
    response = client.post(
        "/api/v1/skills/text_basic_query_tool",
        json={"payload": {"query": "Reverse the text 'streamlit'"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["stdout"].strip() == "tilmaerts"


def test_mcp_catalog_and_tool_invocation(tmp_path) -> None:
    service = _build_service(tmp_path)
    catalog = mcp_tool_catalog(service)
    tools_payload = service.list_tools().model_dump(mode="json")
    assert len(catalog) == tools_payload["total"]
    assert any(item["name"] == "text_basic_query_tool" for item in catalog)
    tool = next(item for item in catalog if item["name"] == "text_basic_query_tool")
    assert tool["inputSchema"]["type"] == "object"
    assert set(tool.keys()) >= {"name", "tool_id", "description", "inputSchema"}

    result = call_mcp_tool(
        service,
        "text_basic_query_tool",
        {"query": "Reverse the text 'streamlit'"},
    )
    assert result["success"] is True
    assert result["result"] == "tilmaerts"

    query_payload = mcp_autoforge_query(service, "Reverse the text 'streamlit'", strategy="full")
    assert query_payload["path_taken"] == "fast"
    assert query_payload["result"] == "tilmaerts"


def test_verify_mcp_helpers_script(tmp_path) -> None:
    output = tmp_path / "mcp_report.json"
    report = verify_mcp_helpers(str(output))
    assert output.exists()
    assert report["checks"]["catalog_nonempty"] is True
    assert report["checks"]["direct_invoke_success"] is True
    assert report["checks"]["query_success"] is True


def test_backend_agent_strategy_uses_forge_pipeline(tmp_path, monkeypatch) -> None:
    registry = ToolRegistry(
        skills_dir=str(tmp_path / "skills"),
        chroma_persist_dir=str(tmp_path / "chroma"),
        enable_vector_store=False,
    )
    service = AutoForgeBackendService(registry=registry, enable_agent_slow_path=True)
    service.sync()

    forged_tool = ToolSchema(
        tool_id="forged-tool-001",
        name="echo_query_tool",
        description="Return the user query with a forged marker.",
        parameters=[ToolParameter(name="query", type="string", required=True)],
        source_code=(
            "def echo_query_tool(query: str) -> str:\n"
            "    return f'FORGED::{query}'\n"
        ),
        json_schema={
            "name": "echo_query_tool",
            "description": "Return the user query with a forged marker.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "User query"}},
                "required": ["query"],
            },
        },
    )

    log_path = tmp_path / "forge_log.json"
    log_path.write_text(
        json.dumps(
            {
                "summary": {
                    "status": "success",
                    "function_name": "echo_query_tool",
                    "verification_case_count": 3,
                    "failure_type": None,
                }
            }
        ),
        encoding="utf-8",
    )

    def _fake_forge(_request):
        return ForgeResult(
            status="success",
            tool=forged_tool,
            error=None,
            attempts=1,
            trace_id="trace-001",
            log_path=str(log_path),
        )

    monkeypatch.setattr(service_module, "run_forge_pipeline", _fake_forge)

    payload = service.handle_query(QueryRequest(query="forge this request", strategy="agent")).model_dump(mode="json")
    assert payload["path_taken"] == "slow"
    assert payload["tool_id"] == "forged-tool-001"
    assert payload["tool_name"] == "echo_query_tool"
    assert payload["result"] == "FORGED::forge this request"
    assert payload["forge_latency_ms"] is not None
    assert payload["forge_trace_id"] == "trace-001"
    assert payload["forge_log_path"] == str(log_path)
    assert payload["forge_summary"]["function_name"] == "echo_query_tool"

    bundle_dir = Path(tmp_path / "skills")
    assert any(path.name == "metadata.json" for path in bundle_dir.rglob("metadata.json"))
