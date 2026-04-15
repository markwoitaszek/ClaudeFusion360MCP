"""Typed exception hierarchy for Fusion 360 MCP server.

Each exception carries structured diagnostic information:
  - error_code: machine-readable identifier (e.g., F360_TIMEOUT)
  - tool_name: the MCP tool that triggered the error
  - remediation: human-readable suggestion for resolution

Security constraint: sanitize() strips __cause__ chains to prevent
internal handler names from leaking to the LLM via MCP responses.
"""


class FusionError(Exception):
    """Base exception for all Fusion 360 MCP errors."""

    error_code: str = "F360_ERROR"

    def __init__(self, message: str, *, tool_name: str = "", remediation: str = ""):
        self.tool_name = tool_name
        self.remediation = remediation
        super().__init__(message)

    def sanitize(self) -> dict:
        """Return a sanitized error dict safe for MCP serialization.

        Strips __cause__ chain and internal details. Only exposes
        error_code, message, tool_name, and remediation.
        """
        return {
            "error_code": self.error_code,
            "error": str(self),
            "tool_name": self.tool_name,
            "remediation": self.remediation,
        }


class FusionTimeoutError(FusionError):
    """Raised when Fusion 360 does not respond within the timeout period."""

    error_code: str = "F360_TIMEOUT"


class FusionSessionError(FusionError):
    """Raised when the session token does not match the add-in."""

    error_code: str = "F360_SESSION_INVALID"


class FusionIPCError(FusionError):
    """Raised when the IPC communication directory or response is invalid."""

    error_code: str = "F360_IPC_ERROR"
