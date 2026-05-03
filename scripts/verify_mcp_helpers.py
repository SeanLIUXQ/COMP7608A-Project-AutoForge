from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.mcp.server import call_mcp_tool, mcp_autoforge_query, mcp_tool_catalog
from backend.service import AutoForgeBackendService


def verify_mcp_helpers(output: str) -> dict:
    service = AutoForgeBackendService()
    service.sync()
    catalog = mcp_tool_catalog(service)
    direct = call_mcp_tool(
        service,
        "text_basic_query_tool",
        {"query": "Reverse the text 'streamlit'"},
    )
    query = mcp_autoforge_query(service, "Reverse the text 'streamlit'", strategy="full")
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "catalog_count": len(catalog),
        "catalog_sample": catalog[:3],
        "direct_invoke": direct,
        "natural_language_query": query,
        "checks": {
            "catalog_nonempty": len(catalog) > 0,
            "direct_invoke_success": direct.get("success") is True and direct.get("result") == "tilmaerts",
            "query_success": query.get("result") == "tilmaerts",
        },
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify MCP helper catalog/direct invoke/query locally.")
    parser.add_argument("--output", default="evaluation/results/mcp_helper_verification.json")
    args = parser.parse_args()
    report = verify_mcp_helpers(args.output)
    print(f"MCP helper verification saved to {args.output}")
    print(json.dumps(report["checks"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
