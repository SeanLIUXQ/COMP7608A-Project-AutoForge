from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from backend.service import AutoForgeBackendService
from backend.tool_registry import RegistrySearchHit, ToolRegistry
from shared.constants import SIMILARITY_THRESHOLD
from shared.schemas import QueryRequest, QueryResponse


@dataclass
class RetrievalDecision:
    hits: list[RegistrySearchHit]
    best_hit: RegistrySearchHit | None
    threshold: float
    retrieval_latency_ms: float

    @property
    def accepted(self) -> bool:
        return bool(self.best_hit and self.best_hit.score >= self.threshold)

    def trace(self) -> list[dict[str, Any]]:
        return [
            {
                "rank": index,
                "tool_id": hit.tool.tool_id,
                "tool_name": hit.tool.name,
                "score": hit.score,
                "threshold": self.threshold,
                "accepted": index == 1 and self.accepted,
                "reason": "accepted" if index == 1 and self.accepted else "below_threshold",
            }
            for index, hit in enumerate(self.hits, start=1)
        ]


def rank_tools(
    query: str,
    registry: ToolRegistry | None = None,
    top_k: int = 5,
    threshold: float = SIMILARITY_THRESHOLD,
) -> RetrievalDecision:
    active_registry = registry or ToolRegistry()
    started = time.monotonic()
    hits = active_registry.search(query, top_k=top_k)
    elapsed_ms = (time.monotonic() - started) * 1000
    return RetrievalDecision(
        hits=hits,
        best_hit=hits[0] if hits else None,
        threshold=threshold,
        retrieval_latency_ms=elapsed_ms,
    )


def retrieve_best_tool(
    query: str,
    registry: ToolRegistry | None = None,
    threshold: float = SIMILARITY_THRESHOLD,
) -> RegistrySearchHit | None:
    decision = rank_tools(query, registry=registry, top_k=1, threshold=threshold)
    return decision.best_hit if decision.accepted else None


def route_query(request: QueryRequest, service: AutoForgeBackendService | None = None) -> QueryResponse:
    active_service = service or AutoForgeBackendService()
    return active_service.handle_query(request)
