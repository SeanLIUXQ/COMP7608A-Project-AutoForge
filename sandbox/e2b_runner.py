from __future__ import annotations

from shared.schemas import VerifierOutput


class E2BRunner:
    """Placeholder runner that returns a clear error until E2B support is wired in."""

    def run(self, source_code: str, test_input: dict | None = None) -> VerifierOutput:
        del source_code, test_input
        return VerifierOutput(
            success=False,
            stderr="E2B sandbox is not configured in this repository yet.",
        )
