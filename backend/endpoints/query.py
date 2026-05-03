from __future__ import annotations

from fastapi import APIRouter

from backend.service import AutoForgeBackendService
from shared.schemas import QueryRequest, QueryResponse


def create_query_router(service: AutoForgeBackendService) -> APIRouter:
    router = APIRouter(tags=["query"])

    @router.post("/query", response_model=QueryResponse)
    @router.post("/api/v1/query", response_model=QueryResponse)
    def query(request: QueryRequest) -> QueryResponse:
        return service.handle_query(request)

    return router
