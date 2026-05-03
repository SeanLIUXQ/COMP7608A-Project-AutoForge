from __future__ import annotations

from backend.tool_registry import ToolRegistry
from shared.schemas import ToolSchema, ToolSummary


class ToolStore:
    """Tool-RAG storage facade backed by AutoForge skill bundles and optional Chroma."""

    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self.registry = registry or ToolRegistry()

    def sync(self) -> None:
        self.registry.sync()

    def save_tool(self, tool: ToolSchema, metadata_extra: dict | None = None):
        return self.registry.save_tool(tool, metadata_extra=metadata_extra)

    def list_tools(self) -> list[ToolSummary]:
        return self.registry.list_tools()

    def all_tools(self) -> list[ToolSchema]:
        return self.registry.all_tools()

    def get_tool(self, tool_id: str) -> ToolSchema | None:
        found = self.registry.get_tool(tool_id)
        return found[0] if found else None

    def get_tool_by_name(self, name: str) -> ToolSchema | None:
        found = self.registry.get_tool_by_name(name)
        return found[0] if found else None

    def search(self, query: str, top_k: int = 5):
        return self.registry.search(query, top_k=top_k)

    def query_similar_tools(self, query: str, top_k: int = 5) -> list[tuple[ToolSchema, float]]:
        return [(hit.tool, hit.score) for hit in self.search(query, top_k=top_k)]
