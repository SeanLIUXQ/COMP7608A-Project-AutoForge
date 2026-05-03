from __future__ import annotations

import os
import time

from sandbox.docker_runner import DockerRunner
from sandbox.local_runner import LocalRunner
from shared.constants import SANDBOX_BACKEND
from shared.schemas import VerifierOutput


def execute_code(source_code: str, test_input: dict | None = None, backend: str | None = None) -> VerifierOutput:
    start_time = time.monotonic()
    backend_name = (backend or os.getenv("SANDBOX_BACKEND", SANDBOX_BACKEND)).lower()

    if backend_name == "docker":
        runner = DockerRunner()
        result = runner.run(source_code, test_input)
    elif backend_name == "local":
        runner = LocalRunner()
        result = runner.run(source_code, test_input)
    else:
        result = VerifierOutput(success=False, stderr=f"Unsupported sandbox backend: {backend_name}")

    result.execution_time_ms = (time.monotonic() - start_time) * 1000
    return result
