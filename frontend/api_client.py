from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class AutoForgeAPIClient:
    backend_url: str = "http://127.0.0.1:8000"
    mode: str = "backend"  # backend | mock
    strategy: str = "full"
    timeout_s: float = 30.0

    def _url(self, path: str) -> str:
        return f"{self.backend_url.rstrip('/')}{path}"

    def _mock_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "tool_id": "mock-001",
                "name": "count_vowels",
                "description": "Count vowels in input text.",
                "parameters": [{"name": "text", "type": "string", "required": True}],
                "keywords": ["text", "vowel"],
                "json_schema": {
                    "name": "count_vowels",
                    "parameters": {
                        "type": "object",
                        "properties": {"text": {"type": "string"}},
                        "required": ["text"],
                    },
                },
                "source_code": (
                    "def count_vowels(text: str) -> int:\n"
                    "    return sum(1 for char in text.lower() if char in 'aeiou')\n"
                ),
            },
            {
                "tool_id": "mock-002",
                "name": "sum_numbers",
                "description": "Return the sum of a number list.",
                "parameters": [{"name": "numbers", "type": "array", "required": True}],
                "keywords": ["numbers", "sum"],
                "json_schema": {
                    "name": "sum_numbers",
                    "parameters": {
                        "type": "object",
                        "properties": {"numbers": {"type": "array"}},
                        "required": ["numbers"],
                    },
                },
                "source_code": (
                    "def sum_numbers(numbers: list[float]) -> float:\n"
                    "    return sum(numbers)\n"
                ),
            },
        ]

    def health(self) -> dict[str, Any]:
        if self.mode == "mock":
            return {
                "status": "ok",
                "mode": "mock",
                "total_tools": len(self._mock_tools()),
                "retrieval_backend": "mock",
                "similarity_threshold": 0.75,
                "available_strategies": ["full", "no_retrieval", "registry_only", "agent"],
            }
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.get(self._url("/health"))
            response.raise_for_status()
            return response.json()

    def query(self, query: str, strategy: str | None = None) -> dict[str, Any]:
        strategy_name = strategy or self.strategy
        if self.mode == "mock":
            return {
                "path_taken": "fast",
                "result": f"[MOCK] Executed query: {query}",
                "total_latency_ms": 140.0,
                "tool_id": "mock-tool-v1",
                "tool_name": "mock_query_tool",
                "strategy": strategy_name,
                "reused_existing_tool": True,
                "retrieval_latency_ms": 25.0,
                "forge_latency_ms": None,
                "execution_latency_ms": 115.0,
                "search_score": 0.88,
                "retrieval_trace": [
                    {
                        "rank": 1,
                        "tool_id": "mock-tool-v1",
                        "tool_name": "mock_query_tool",
                        "score": 0.88,
                        "threshold": 0.75,
                        "accepted": True,
                        "reason": "accepted",
                    }
                ],
                "error": None,
            }

        payload = {"query": query, "strategy": strategy_name}
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(self._url("/query"), json=payload)
            response.raise_for_status()
            return response.json()

    def list_tools(self) -> dict[str, Any]:
        if self.mode == "mock":
            tools = self._mock_tools()
            return {
                "total": len(tools),
                "tools": [
                    {
                        "tool_id": tool["tool_id"],
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                        "keywords": tool["keywords"],
                    }
                    for tool in tools
                ],
            }

        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.get(self._url("/api/v1/tools"))
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, list):
                return {"total": len(payload), "tools": payload}
            return payload

    def get_tool(self, tool_id: str) -> dict[str, Any]:
        if self.mode == "mock":
            for tool in self._mock_tools():
                if tool["tool_id"] == tool_id:
                    return tool
            raise KeyError(f"Unknown mock tool: {tool_id}")

        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.get(self._url(f"/api/v1/tools/{tool_id}"))
            response.raise_for_status()
            return response.json()

    def invoke_tool(self, tool_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self.mode == "mock":
            if tool_id == "mock-001":
                text = str(payload.get("text") or payload.get("query") or "")
                value = sum(1 for char in text.lower() if char in "aeiou")
                return {"success": True, "stdout": f"{value}\n", "stderr": "", "execution_time_ms": 12.0}
            if tool_id == "mock-002":
                numbers = payload.get("numbers", [])
                value = sum(numbers) if isinstance(numbers, list) else 0
                return {"success": True, "stdout": f"{value}\n", "stderr": "", "execution_time_ms": 9.0}
            return {"success": False, "stdout": "", "stderr": "Mock tool not found", "execution_time_ms": 0.0}

        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(
                self._url(f"/api/v1/tools/{tool_id}/invoke"),
                json={"payload": payload},
            )
            response.raise_for_status()
            return response.json()

    def dashboard_summary(self) -> dict[str, Any]:
        if self.mode == "mock":
            return {
                "health": self.health(),
                "tools": self.list_tools(),
                "featured_tools": self.list_tools()["tools"],
            }

        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.get(self._url("/api/v1/dashboard/summary"))
                response.raise_for_status()
                return response.json()
        except Exception:
            tools = self.list_tools()
            return {
                "health": self.health(),
                "tools": tools,
                "featured_tools": tools.get("tools", [])[:5],
            }
