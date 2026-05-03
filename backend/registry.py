from __future__ import annotations

from threading import RLock

from shared.schemas import ToolSchema


class ToolRegistry:
    """In-memory registry of forged tools (rebuilt from Chroma on startup)."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._by_id: dict[str, ToolSchema] = {}

    def upsert(self, tool: ToolSchema) -> None:
        with self._lock:
            self._by_id[tool.tool_id] = tool

    def get(self, tool_id: str) -> ToolSchema | None:
        with self._lock:
            return self._by_id.get(tool_id)

    def list(self) -> list[ToolSchema]:
        with self._lock:
            return list(self._by_id.values())

    def replace_all(self, tools: list[ToolSchema]) -> None:
        with self._lock:
            self._by_id = {t.tool_id: t for t in tools}
