from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except Exception:
    pass


def _parse_stdout(stdout: str | None) -> Any:
    text = (stdout or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        return ast.literal_eval(text)
    except Exception:
        return text


def mcp_tool_catalog(service) -> list[dict[str, Any]]:
    service.sync()
    output: list[dict[str, Any]] = []
    for tool in service.registry.all_tools():
        output.append(
            {
                "name": tool.name,
                "tool_id": tool.tool_id,
                "description": tool.description,
                "inputSchema": tool.json_schema.get("parameters", {"type": "object", "properties": {}}),
            }
        )
    return sorted(output, key=lambda item: item["name"])


def _find_tool(service, name_or_id: str):
    found = service.registry.get_tool(name_or_id)
    if found is not None:
        return found[0]
    found = service.registry.get_tool_by_name(name_or_id)
    if found is not None:
        return found[0]
    return None


def call_mcp_tool(service, name_or_id: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    service.sync()
    tool = _find_tool(service, name_or_id)
    if tool is None:
        return {"success": False, "error": f"Tool not found: {name_or_id}"}

    from backend.dynamic_api import validate_tool_payload
    from sandbox.executor import execute_code

    payload = dict(arguments or {})
    try:
        validate_tool_payload(tool, payload)
    except Exception as exc:
        return {"success": False, "tool_id": tool.tool_id, "tool_name": tool.name, "error": str(exc)}

    payload.setdefault("__function_name", tool.name)
    result = execute_code(tool.source_code, payload)
    return {
        "success": result.success,
        "tool_id": tool.tool_id,
        "tool_name": tool.name,
        "result": _parse_stdout(result.stdout),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "execution_time_ms": result.execution_time_ms,
    }


def mcp_autoforge_query(service, user_query: str, strategy: str = "full") -> dict[str, Any]:
    """MCP-friendly helper: return the same payload as POST /query."""
    from shared.schemas import QueryRequest

    service.sync()
    response = service.handle_query(QueryRequest(query=user_query, strategy=strategy))
    return response.model_dump(mode="json")


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "The 'mcp' package is required. Install with: pip install mcp\n"
            f"Import error: {exc}"
        ) from exc

    from backend.service import AutoForgeBackendService
    from shared.schemas import QueryRequest

    service = AutoForgeBackendService()
    service.sync()
    mcp = FastMCP("AutoForge")

    @mcp.tool()
    def autoforge_query(user_query: str, strategy: str = "full") -> str:
        """Run a natural-language query through the AutoForge backend service."""
        return json.dumps(mcp_autoforge_query(service, user_query, strategy=strategy), ensure_ascii=False)

    @mcp.tool()
    def list_forged_tools() -> str:
        """List AutoForge tools with MCP-compatible input schemas."""
        return json.dumps(mcp_tool_catalog(service), ensure_ascii=False)

    @mcp.tool()
    def invoke_forged_tool(name_or_id: str, payload_json: str = "{}") -> str:
        """Invoke a registered AutoForge tool by name or id with a JSON object payload."""
        try:
            payload = json.loads(payload_json or "{}")
        except json.JSONDecodeError as exc:
            return json.dumps({"success": False, "error": f"Invalid payload JSON: {exc}"})
        if not isinstance(payload, dict):
            return json.dumps({"success": False, "error": "payload_json must be a JSON object"})

        return json.dumps(call_mcp_tool(service, name_or_id, payload), ensure_ascii=False)

    mcp.run()


if __name__ == "__main__":
    main()
