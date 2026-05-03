# shared/exceptions.py - project-wide exception classes.


class ToolNotFoundError(Exception):
    """Raised when a requested tool cannot be found in the tool store."""


class ToolVersionConflict(Exception):
    """Raised when a tool name already exists with a conflicting version."""


class SandboxTimeoutError(Exception):
    """Raised when sandbox execution times out."""


class ForgeFailedError(Exception):
    """Raised when tool forging still fails after the maximum retry count."""


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
