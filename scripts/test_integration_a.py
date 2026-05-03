from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.service import AutoForgeBackendService
from backend.tool_registry import ToolRegistry
from shared.schemas import QueryRequest


def main() -> int:
    registry = ToolRegistry(
        skills_dir=str(REPO_ROOT / "skills_integration_a"),
        chroma_persist_dir=str(REPO_ROOT / "data" / "chroma_integration_a"),
        enable_vector_store=False,
    )
    service = AutoForgeBackendService(registry=registry)
    service.sync()

    response = service.handle_query(
        QueryRequest(query="Reverse the text 'streamlit'", strategy="full")
    )
    if response.result != "tilmaerts" or response.path_taken.value != "fast":
        print(f"FAIL: unexpected response={response.model_dump(mode='json')}")
        return 1

    print("OK: integration A passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
