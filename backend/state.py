from __future__ import annotations

from threading import Lock

from .query_service import QueryService
from .registry import ToolRegistry
from .tool_rag import ToolRAG

_lock = Lock()
_rag: ToolRAG | None = None
_registry: ToolRegistry | None = None
_service: QueryService | None = None


def get_tool_rag() -> ToolRAG:
    global _rag
    with _lock:
        if _rag is None:
            _rag = ToolRAG()
        return _rag


def get_registry() -> ToolRegistry:
    global _registry
    with _lock:
        if _registry is None:
            _registry = ToolRegistry()
        return _registry


def get_query_service() -> QueryService:
    global _service
    with _lock:
        if _service is None:
            rag = get_tool_rag()
            reg = get_registry()
            reg.replace_all(rag.load_all_tools())
            _service = QueryService(rag, reg)
        return _service


def reset_singletons_for_tests() -> None:
    global _rag, _registry, _service
    with _lock:
        _rag = None
        _registry = None
        _service = None
