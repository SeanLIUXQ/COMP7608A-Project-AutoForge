from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.service import AutoForgeBackendService
from backend.tool_registry import ToolRegistry
from evaluation import runner as runner_module
from evaluation.runner import run_benchmark
from shared.schemas import QueryRequest


def main() -> int:
    registry = ToolRegistry(
        skills_dir=str(REPO_ROOT / "skills_integration_b"),
        chroma_persist_dir=str(REPO_ROOT / "data" / "chroma_integration_b"),
        enable_vector_store=False,
    )
    service = AutoForgeBackendService(registry=registry)
    service.sync()

    dataset = [
        {
            "sample_id": "L1_001",
            "difficulty": 1,
            "query": "Given payload {'prices': [10.0, 11.0, 12.0, 13.0]}, compute 3-point moving average",
            "paraphrases": [
                "Return the 3-point moving average for {'prices': [10.0, 11.0, 12.0, 13.0]}",
                "Compute 3-point moving average from {'prices': [10.0, 11.0, 12.0, 13.0]}",
                "Calculate 3-point moving average using {'prices': [10.0, 11.0, 12.0, 13.0]}",
            ],
            "expected_output": [11.0, 12.0],
            "expected_output_type": "exact",
            "tool_family": "timeseries_pipeline",
        }
    ]
    dataset_path = REPO_ROOT / "evaluation" / "results" / "integration_b_dataset.json"
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")

    def _fake_backend_query(
        backend_url: str,
        query_text: str,
        strategy: str = "full",
        timeout_s: float = 60.0,
    ) -> dict:
        del backend_url, timeout_s
        response = service.handle_query(QueryRequest(query=query_text, strategy=strategy))
        return response.model_dump(mode="json")

    runner_module._backend_query = _fake_backend_query
    report = run_benchmark(
        dataset_path=str(dataset_path),
        mode="backend",
        backend_url="http://testserver",
        strategy="no_retrieval",
    )
    if report["success_rate"] != 1.0:
        print(f"FAIL: unexpected report={report}")
        return 1

    print("OK: integration B passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
