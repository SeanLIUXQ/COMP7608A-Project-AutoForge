from __future__ import annotations

from fastapi import APIRouter

from backend.service import AutoForgeBackendService
from shared.schemas import HealthResponse


def create_health_router(service: AutoForgeBackendService) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return service.health()

    return router
