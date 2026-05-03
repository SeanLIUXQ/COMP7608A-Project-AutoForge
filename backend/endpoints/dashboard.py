from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.service import AutoForgeBackendService


def create_dashboard_router(service: AutoForgeBackendService) -> APIRouter:
    router = APIRouter(tags=["dashboard"])

    @router.get("/api/v1/dashboard/summary")
    def dashboard_summary() -> dict[str, Any]:
        health = service.health().model_dump(mode="json")
        tools_payload = service.list_tools().model_dump(mode="json")
        tools = tools_payload.get("tools", [])
        return {
            "health": health,
            "tools": tools_payload,
            "featured_tools": tools[:5],
        }

    return router
