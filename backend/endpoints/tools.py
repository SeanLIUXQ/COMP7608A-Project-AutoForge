from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.dynamic_api import validate_tool_payload
from backend.service import AutoForgeBackendService
from sandbox.executor import execute_code
from shared.schemas import ToolListResponse


class InvokeToolBody(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


def create_tools_router(service: AutoForgeBackendService) -> APIRouter:
    router = APIRouter(tags=["tools"])

    @router.get("/tools", response_model=ToolListResponse)
    def list_tools() -> ToolListResponse:
        return service.list_tools()

    @router.get("/api/v1/tools")
    def list_tools_v1() -> list[dict[str, Any]]:
        return [
            {
                "tool_id": tool.tool_id,
                "name": tool.name,
                "description": tool.description,
                "parameters": [param.model_dump() for param in tool.parameters],
                "keywords": tool.keywords,
            }
            for tool in service.list_tools().tools
        ]

    @router.get("/tools/{tool_id}")
    @router.get("/api/v1/tools/{tool_id}")
    def get_tool(tool_id: str) -> dict:
        payload = service.registry.get_tool(tool_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="Tool not found")
        tool, _bundle_dir = payload
        return {
            "tool_id": tool.tool_id,
            "name": tool.name,
            "description": tool.description,
            "parameters": [param.model_dump() for param in tool.parameters],
            "json_schema": tool.json_schema,
            "source_code": tool.source_code,
        }

    @router.post("/tools/{tool_id}/invoke")
    @router.post("/api/v1/tools/{tool_id}/invoke")
    def invoke_tool(tool_id: str, body: InvokeToolBody) -> dict[str, Any]:
        payload = service.registry.get_tool(tool_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="Tool not found")
        tool, _bundle_dir = payload

        invoke_payload = dict(body.payload)
        validate_tool_payload(tool, invoke_payload)
        invoke_payload.setdefault("__function_name", tool.name)
        result = execute_code(tool.source_code, invoke_payload)
        return {
            "tool_id": tool.tool_id,
            "tool_name": tool.name,
            "success": result.success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time_ms": result.execution_time_ms,
        }

    return router
