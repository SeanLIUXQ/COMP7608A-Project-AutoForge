from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from sandbox.executor import execute_code
from shared.schemas import ToolSchema


class InvokeBody(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class RegisteredRoute:
    tool_id: str
    name: str
    path: str


_lock = RLock()
_app: FastAPI | None = None
_registered_by_tool_id: dict[str, RegisteredRoute] = {}


def bind_app(app: FastAPI) -> None:
    """Bind the running FastAPI app so tools can be registered at runtime."""
    global _app
    global _registered_by_tool_id
    with _lock:
        if _app is not app:
            _registered_by_tool_id = {}
        _app = app


def _ensure_app() -> FastAPI:
    with _lock:
        if _app is None:
            raise RuntimeError("FastAPI app not bound. Call bind_app(app) during startup.")
        return _app


def _validate_payload(tool: ToolSchema, payload: dict[str, Any]) -> None:
    required = []
    try:
        required = list((tool.json_schema or {}).get("parameters", {}).get("required", []) or [])
    except Exception:
        required = []
    missing = [k for k in required if k not in payload]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required parameters: {missing}")


def validate_tool_payload(tool: ToolSchema, payload: dict[str, Any]) -> None:
    _validate_payload(tool, payload)


def _build_handler(tool: ToolSchema) -> Callable[[InvokeBody], dict[str, Any]]:
    def _handler(body: InvokeBody) -> dict[str, Any]:
        payload = dict(body.payload or {})
        _validate_payload(tool, payload)
        payload.setdefault("__function_name", tool.name)
        result = execute_code(tool.source_code, payload)
        return {
            "tool_id": tool.tool_id,
            "tool_name": tool.name,
            "success": result.success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time_ms": result.execution_time_ms,
        }

    return _handler


def register_tool_endpoint(tool: ToolSchema) -> RegisteredRoute:
    """
    Create a tool-specific invoke endpoint on the running FastAPI app.

    Path shape (stable, human-friendly):
      POST /api/v1/skills/{tool.name}
    """
    app = _ensure_app()

    with _lock:
        existing = _registered_by_tool_id.get(tool.tool_id)
        if existing is not None:
            return existing

        # Name-based path for humans; allow duplicates via tool_id suffix.
        base = f"/api/v1/skills/{tool.name}"
        path = base
        if any(r.path == base for r in _registered_by_tool_id.values()):
            path = f"{base}__{tool.tool_id[:8]}"

        handler = _build_handler(tool)
        handler.__name__ = f"invoke__{tool.name}__{tool.tool_id[:8]}"

        app.add_api_route(
            path,
            handler,
            methods=["POST"],
            response_model=dict[str, Any],
            tags=["dynamic-tools"],
            name=f"invoke:{tool.name}",
            description=tool.description,
        )
        app.openapi_schema = None

        rr = RegisteredRoute(tool_id=tool.tool_id, name=tool.name, path=path)
        _registered_by_tool_id[tool.tool_id] = rr
        return rr


def register_all_tools(tools: list[ToolSchema]) -> list[RegisteredRoute]:
    out: list[RegisteredRoute] = []
    for t in tools:
        try:
            out.append(register_tool_endpoint(t))
        except Exception:
            continue
    return out


def list_registered_routes() -> list[RegisteredRoute]:
    with _lock:
        return sorted(_registered_by_tool_id.values(), key=lambda item: item.path)

