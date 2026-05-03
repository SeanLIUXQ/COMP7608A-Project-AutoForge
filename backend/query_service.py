from __future__ import annotations

import time
from typing import Any

from agents.forge_pipeline import run_forge_pipeline
from agents.packager import create_skill_bundle

from .llm_tools import extract_invocation_payload, llm_verify_tool_matches_query
from .dynamic_api import register_tool_endpoint
from .registry import ToolRegistry
from .tool_rag import ToolRAG
from sandbox.executor import execute_code
from shared.constants import SIMILARITY_THRESHOLD
from shared.schemas import ForgeRequest, PathType, QueryRequest, QueryResponse, ToolSchema


class QueryService:
    def __init__(self, rag: ToolRAG, registry: ToolRegistry) -> None:
        self._rag = rag
        self._registry = registry

    def warm_path_invoke(self, tool: ToolSchema, query: str) -> tuple[Any | None, str | None]:
        try:
            payload = extract_invocation_payload(query, tool)
        except Exception as exc:
            return None, f"Parameter extraction failed: {exc}"
        exec_result = execute_code(tool.source_code, payload)
        if not exec_result.success:
            return None, exec_result.stderr or "Sandbox execution failed"
        out = exec_result.stdout
        if out is not None and isinstance(out, str):
            out = out.strip()
        return out, None

    def slow_path_forge_and_invoke(self, query: str) -> tuple[ToolSchema | None, Any | None, str | None]:
        forge = run_forge_pipeline(ForgeRequest(query=query))
        if forge.status != "success" or not forge.tool:
            return None, None, forge.error or "Forge pipeline failed"
        tool = forge.tool
        self._registry.upsert(tool)
        self._rag.upsert_tool(tool)
        try:
            register_tool_endpoint(tool)
        except Exception:
            pass
        try:
            create_skill_bundle(tool)
        except Exception:
            pass
        result, err = self.warm_path_invoke(tool, query)
        return tool, result, err

    def handle(self, request: QueryRequest) -> QueryResponse:
        t0 = time.perf_counter()
        query = request.query.strip()
        if not query:
            return QueryResponse(
                path_taken=PathType.SLOW,
                result=None,
                total_latency_ms=(time.perf_counter() - t0) * 1000,
                error="Empty query",
            )

        skip_verify = getattr(request, "skip_llm_match_verify", False)
        hit = self._rag.retrieve_best(query)
        if hit and hit.similarity >= SIMILARITY_THRESHOLD:
            tool = hit.tool
            if not skip_verify and not llm_verify_tool_matches_query(query, tool):
                tool_schema, result, err = self.slow_path_forge_and_invoke(query)
                ms = (time.perf_counter() - t0) * 1000
                if err:
                    return QueryResponse(
                        path_taken=PathType.SLOW,
                        result=result,
                        total_latency_ms=ms,
                        tool_id=tool_schema.tool_id if tool_schema else None,
                        error=err,
                    )
                return QueryResponse(
                    path_taken=PathType.SLOW,
                    result=result,
                    total_latency_ms=ms,
                    tool_id=tool_schema.tool_id if tool_schema else None,
                    error=None,
                )

            result, err = self.warm_path_invoke(tool, query)
            ms = (time.perf_counter() - t0) * 1000
            if err:
                return QueryResponse(
                    path_taken=PathType.FAST,
                    result=None,
                    total_latency_ms=ms,
                    tool_id=tool.tool_id,
                    error=err,
                )
            return QueryResponse(
                path_taken=PathType.FAST,
                result=result,
                total_latency_ms=ms,
                tool_id=tool.tool_id,
                error=None,
            )

        tool_schema, result, err = self.slow_path_forge_and_invoke(query)
        ms = (time.perf_counter() - t0) * 1000
        if err:
            return QueryResponse(
                path_taken=PathType.SLOW,
                result=result,
                total_latency_ms=ms,
                tool_id=tool_schema.tool_id if tool_schema else None,
                error=err,
            )
        return QueryResponse(
            path_taken=PathType.SLOW,
            result=result,
            total_latency_ms=ms,
            tool_id=tool_schema.tool_id if tool_schema else None,
            error=None,
        )
