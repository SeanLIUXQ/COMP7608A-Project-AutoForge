from __future__ import annotations

import ast
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents.forge_pipeline import run_forge_pipeline
from backend.default_tools import fallback_solver_schema
from backend.dynamic_api import register_tool_endpoint, validate_tool_payload
from backend.tool_registry import RegistrySearchHit, ToolRegistry
from sandbox.executor import execute_code
from shared.constants import RETRIEVAL_TOP_K, SIMILARITY_THRESHOLD
from shared.schemas import (
    ForgeRequest,
    HealthResponse,
    PathType,
    QueryRequest,
    QueryResponse,
    QueryStrategy,
    ToolListResponse,
    ToolSchema,
)


@dataclass
class _ExecutionAttempt:
    tool: ToolSchema
    result: Any = None
    error: str | None = None
    execution_latency_ms: float | None = None
    forge_latency_ms: float | None = None
    forge_trace_id: str | None = None
    forge_log_path: str | None = None
    forge_summary: dict[str, Any] | None = None
    failure_type: str | None = None


def _parse_execution_output(stdout: str) -> Any:
    text = (stdout or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        return ast.literal_eval(text)
    except Exception:
        return text


def _summarize_error(stderr: str) -> str:
    lines = [line.strip() for line in (stderr or "").splitlines() if line.strip()]
    if not lines:
        return "Execution failed"
    return lines[-1]


def _load_forge_summary(log_path: str | None) -> dict[str, Any] | None:
    if not log_path:
        return None
    try:
        payload = json.loads(Path(log_path).read_text(encoding="utf-8"))
    except Exception:
        return None
    summary = payload.get("summary")
    return summary if isinstance(summary, dict) else None


class AutoForgeBackendService:
    def __init__(
        self,
        registry: ToolRegistry | None = None,
        enable_agent_slow_path: bool | None = None,
        enable_llm_match_verify: bool | None = None,
        similarity_threshold: float | None = None,
    ) -> None:
        self.registry = registry or ToolRegistry()
        self.fallback_tool = fallback_solver_schema()
        if enable_agent_slow_path is None:
            enable_agent_slow_path = os.getenv("AUTOFORGE_ENABLE_AGENT_SLOW_PATH", "0").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        if enable_llm_match_verify is None:
            enable_llm_match_verify = os.getenv("AUTOFORGE_ENABLE_LLM_MATCH_VERIFY", "0").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        self.enable_agent_slow_path = enable_agent_slow_path
        self.enable_llm_match_verify = enable_llm_match_verify
        if similarity_threshold is None:
            similarity_threshold = float(os.getenv("AUTOFORGE_SIMILARITY_THRESHOLD", str(SIMILARITY_THRESHOLD)))
        self.similarity_threshold = float(similarity_threshold)
        self._ready = False

    def sync(self) -> None:
        self.registry.sync()
        self._ready = True

    def _ensure_ready(self) -> None:
        if not self._ready or self.registry.total_tools() == 0:
            self.sync()

    def health(self) -> HealthResponse:
        self._ensure_ready()
        return HealthResponse(
            status="ok",
            total_tools=self.registry.total_tools(),
            retrieval_backend=self.registry.retrieval_backend,
            similarity_threshold=self.similarity_threshold,
            available_strategies=[
                QueryStrategy.FULL,
                QueryStrategy.NO_RETRIEVAL,
                QueryStrategy.REGISTRY_ONLY,
                QueryStrategy.AGENT,
            ],
        )

    def list_tools(self) -> ToolListResponse:
        self._ensure_ready()
        tools = self.registry.list_tools()
        return ToolListResponse(total=len(tools), tools=tools)

    def _execute_tool_with_payload(self, tool: ToolSchema, payload: dict[str, Any], backend: str = "local") -> _ExecutionAttempt:
        invoke_payload = dict(payload)
        invoke_payload.setdefault("__function_name", tool.name)
        try:
            validate_tool_payload(tool, {k: v for k, v in invoke_payload.items() if k != "__function_name"})
        except Exception as exc:
            return _ExecutionAttempt(tool=tool, error=str(exc))
        result = execute_code(tool.source_code, invoke_payload, backend=backend)
        if not result.success:
            return _ExecutionAttempt(
                tool=tool,
                error=_summarize_error(result.stderr or ""),
                execution_latency_ms=result.execution_time_ms,
            )
        return _ExecutionAttempt(
            tool=tool,
            result=_parse_execution_output(result.stdout or ""),
            execution_latency_ms=result.execution_time_ms,
        )

    def _execute_tool(self, tool: ToolSchema, query: str) -> _ExecutionAttempt:
        return self._execute_tool_with_payload(tool, {"query": query}, backend="local")

    def _run_ranked_search(self, query: str) -> tuple[list[RegistrySearchHit], float]:
        started = time.monotonic()
        hits = self.registry.search(query, top_k=RETRIEVAL_TOP_K)
        elapsed_ms = (time.monotonic() - started) * 1000
        return hits, elapsed_ms

    def _trace_hits(self, hits: list[RegistrySearchHit], *, backend_scores: dict[str, dict[str, float]] | None = None) -> list[dict[str, Any]]:
        backend_scores = backend_scores or {}
        lexical = backend_scores.get("lexical", {})
        chroma = backend_scores.get("chroma", {})
        return [
            {
                "rank": index,
                "tool_id": hit.tool.tool_id,
                "tool_name": hit.tool.name,
                "score": hit.score,
                "scores": {"lexical": lexical.get(hit.tool.tool_id), "chroma": chroma.get(hit.tool.tool_id)},
                "retrieval_backend": self.registry.retrieval_backend,
                "threshold": self.similarity_threshold,
                "accepted": False,
                "reason": "not_evaluated",
            }
            for index, hit in enumerate(hits, start=1)
        ]

    def _mark_trace(self, trace: list[dict[str, Any]], tool_id: str, *, accepted: bool, reason: str) -> None:
        for item in trace:
            if item.get("tool_id") == tool_id:
                item["accepted"] = accepted
                item["reason"] = reason
                return

    def _run_fallback(self, query: str) -> _ExecutionAttempt:
        return self._execute_tool(self.fallback_tool, query)

    def _persist_forged_tool(self, tool: ToolSchema) -> None:
        self.registry.save_tool(tool, metadata_extra={"forged": True, "tool_origin": "forged", "tool_status": "active"})
        try:
            register_tool_endpoint(tool)
        except Exception:
            pass

    def _verify_tool_match(self, request: QueryRequest, tool: ToolSchema) -> bool:
        if request.skip_llm_match_verify or not self.enable_llm_match_verify:
            return True
        try:
            from backend.llm_tools import llm_verify_tool_matches_query
        except Exception:
            return False
        try:
            return llm_verify_tool_matches_query(request.query, tool)
        except Exception:
            return False

    def _invoke_tool_from_query(self, tool: ToolSchema, query: str) -> _ExecutionAttempt:
        if any(param.name == "query" for param in tool.parameters):
            return self._execute_tool(tool, query)

        try:
            from backend.llm_tools import extract_invocation_payload
        except Exception as exc:
            return _ExecutionAttempt(tool=tool, error=f"Tool requires structured arguments, but invocation payload extraction is unavailable: {exc}")

        try:
            payload = extract_invocation_payload(query, tool)
        except Exception as exc:
            return _ExecutionAttempt(tool=tool, error=f"Tool could not be invoked from the user query: {exc}")

        return self._execute_tool_with_payload(tool, payload, backend="local")

    def _run_agent_forge(self, query: str) -> _ExecutionAttempt:
        forge_started = time.monotonic()
        forge_result = run_forge_pipeline(ForgeRequest(query=query))
        forge_latency_ms = (time.monotonic() - forge_started) * 1000

        if forge_result.status != "success" or not forge_result.tool:
            summary = _load_forge_summary(forge_result.log_path)
            return _ExecutionAttempt(
                tool=self.fallback_tool,
                error=forge_result.error or "Forge pipeline failed",
                forge_latency_ms=forge_latency_ms,
                forge_trace_id=forge_result.trace_id,
                forge_log_path=forge_result.log_path,
                forge_summary=summary,
                failure_type=str(summary.get("failure_type")) if summary and summary.get("failure_type") else None,
            )

        tool = forge_result.tool
        try:
            self._persist_forged_tool(tool)
        except Exception as exc:
            return _ExecutionAttempt(
                tool=tool,
                error=f"Forged tool was created but could not be persisted: {exc}",
                forge_latency_ms=forge_latency_ms,
                forge_trace_id=forge_result.trace_id,
                forge_log_path=forge_result.log_path,
                forge_summary=_load_forge_summary(forge_result.log_path),
                failure_type="persistence_failed",
            )

        attempt = self._invoke_tool_from_query(tool, query)
        attempt.forge_latency_ms = forge_latency_ms
        attempt.forge_trace_id = forge_result.trace_id
        attempt.forge_log_path = forge_result.log_path
        attempt.forge_summary = _load_forge_summary(forge_result.log_path)
        return attempt

    def _build_response(
        self,
        *,
        request: QueryRequest,
        total_started: float,
        path_taken: PathType,
        attempt: _ExecutionAttempt,
        reused_existing_tool: bool,
        retrieval_latency_ms: float | None,
        search_score: float | None = None,
        retrieval_trace: list[dict[str, Any]] | None = None,
    ) -> QueryResponse:
        total_latency_ms = (time.monotonic() - total_started) * 1000
        return QueryResponse(
            path_taken=path_taken,
            result=attempt.result,
            total_latency_ms=total_latency_ms,
            tool_id=attempt.tool.tool_id,
            tool_name=attempt.tool.name,
            strategy=request.strategy,
            reused_existing_tool=reused_existing_tool,
            retrieval_latency_ms=retrieval_latency_ms,
            forge_latency_ms=attempt.forge_latency_ms,
            execution_latency_ms=attempt.execution_latency_ms,
            search_score=search_score,
            retrieval_trace=retrieval_trace or [],
            forge_trace_id=attempt.forge_trace_id,
            forge_log_path=attempt.forge_log_path,
            forge_summary=attempt.forge_summary,
            failure_type=attempt.failure_type,
            error=attempt.error,
        )

    def handle_query(self, request: QueryRequest) -> QueryResponse:
        total_started = time.monotonic()
        self._ensure_ready()

        query = request.query.strip()
        if not query:
            return QueryResponse(
                path_taken=PathType.SLOW,
                result=None,
                total_latency_ms=(time.monotonic() - total_started) * 1000,
                strategy=request.strategy,
                error="Empty query",
            )

        retrieval_latency_ms: float | None = None
        selected_hit: RegistrySearchHit | None = None
        retrieval_trace: list[dict[str, Any]] = []
        explain_only = bool(getattr(request, "explain_only", False) or getattr(request, "dry_run", False))

        if request.strategy == QueryStrategy.AGENT:
            attempt = self._run_agent_forge(query)
            return self._build_response(
                request=request,
                total_started=total_started,
                path_taken=PathType.SLOW,
                attempt=attempt,
                reused_existing_tool=False,
                retrieval_latency_ms=None,
                retrieval_trace=retrieval_trace,
            )

        if request.strategy == QueryStrategy.NO_RETRIEVAL:
            if self.enable_agent_slow_path:
                attempt = self._run_agent_forge(query)
            else:
                attempt = self._run_fallback(query)
            return self._build_response(
                request=request,
                total_started=total_started,
                path_taken=PathType.SLOW,
                attempt=attempt,
                reused_existing_tool=False,
                retrieval_latency_ms=None,
                retrieval_trace=retrieval_trace,
            )

        hits, retrieval_latency_ms = self._run_ranked_search(query)
        backend_scores = self.registry.debug_scores(query, tool_ids=[hit.tool.tool_id for hit in hits])
        retrieval_trace = self._trace_hits(hits, backend_scores=backend_scores)

        if explain_only:
            planned = None
            if hits:
                best = hits[0]
                planned_payload: dict[str, Any] | None
                if any(param.name == "query" for param in best.tool.parameters):
                    planned_payload = {"query": query}
                else:
                    planned_payload = None
                planned = {
                    "would_use_tool": {"tool_id": best.tool.tool_id, "tool_name": best.tool.name},
                    "threshold": self.similarity_threshold,
                    "above_threshold": best.score >= self.similarity_threshold,
                    "planned_payload": planned_payload,
                    "note": (
                        "Structured-arg tools need payload extraction (LLM) which is skipped in explain_only mode."
                        if planned_payload is None
                        else None
                    ),
                }
            return QueryResponse(
                path_taken=PathType.FAST if hits else PathType.SLOW,
                result=None,
                total_latency_ms=(time.monotonic() - total_started) * 1000,
                tool_id=None,
                tool_name=None,
                strategy=request.strategy,
                reused_existing_tool=False,
                retrieval_latency_ms=retrieval_latency_ms,
                forge_latency_ms=None,
                execution_latency_ms=None,
                search_score=hits[0].score if hits else None,
                retrieval_trace=retrieval_trace,
                explain=planned,
                error=None,
            )
        if hits and hits[0].score >= self.similarity_threshold:
            for hit in hits:
                selected_hit = hit
                if hit.score < self.similarity_threshold:
                    self._mark_trace(retrieval_trace, hit.tool.tool_id, accepted=False, reason="below_threshold")
                    continue
                if not self._verify_tool_match(request, hit.tool):
                    self._mark_trace(retrieval_trace, hit.tool.tool_id, accepted=False, reason="llm_match_rejected")
                    continue
                attempt = self._invoke_tool_from_query(hit.tool, query)
                if attempt.error:
                    self._mark_trace(retrieval_trace, hit.tool.tool_id, accepted=False, reason=f"execution_failed: {attempt.error}")
                    continue
                self._mark_trace(retrieval_trace, hit.tool.tool_id, accepted=True, reason="accepted")
                return self._build_response(
                    request=request,
                    total_started=total_started,
                    path_taken=PathType.FAST,
                    attempt=attempt,
                    reused_existing_tool=True,
                    retrieval_latency_ms=retrieval_latency_ms,
                    search_score=hit.score,
                    retrieval_trace=retrieval_trace,
                )
        elif hits:
            self._mark_trace(retrieval_trace, hits[0].tool.tool_id, accepted=False, reason="below_threshold")

        if request.strategy == QueryStrategy.REGISTRY_ONLY:
            total_latency_ms = (time.monotonic() - total_started) * 1000
            best_score = hits[0].score if hits else None
            return QueryResponse(
                path_taken=PathType.SLOW,
                result=None,
                total_latency_ms=total_latency_ms,
                strategy=request.strategy,
                reused_existing_tool=False,
                retrieval_latency_ms=retrieval_latency_ms,
                forge_latency_ms=None,
                execution_latency_ms=None,
                search_score=best_score,
                retrieval_trace=retrieval_trace,
                error="No registry tool matched the query above the similarity threshold.",
            )

        if self.enable_agent_slow_path:
            attempt = self._run_agent_forge(query)
        else:
            attempt = self._run_fallback(query)
        return self._build_response(
            request=request,
            total_started=total_started,
            path_taken=PathType.SLOW,
            attempt=attempt,
            reused_existing_tool=False,
            retrieval_latency_ms=retrieval_latency_ms,
            search_score=selected_hit.score if selected_hit else (hits[0].score if hits else None),
            retrieval_trace=retrieval_trace,
        )
