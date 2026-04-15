"""IPC layer: file-based communication between MCP server and Fusion 360 add-in.

Protocol (ADR-D002):
  1. MCP server writes command_{id}.json to COMM_DIR
  2. Add-in polls for command files, executes via Fusion 360 API
  3. Add-in writes response_{id}.json
  4. MCP server polls for response, returns result

Protocol versioning (NR-1):
  Every command includes "protocol_version": PROTOCOL_VERSION. The add-in
  rejects commands with a mismatched version (fail-closed).

Session token (MT-3):
  On startup, the MCP server generates a session token and writes it to
  COMM_DIR/session_token. Every command includes the token. The add-in
  validates the token and rejects commands without a matching token.

Single-process constraint:
  Module-level globals (_session_token, _command_counter, _stats) assume a
  single MCP server process. Multi-process deployments may collide on the
  session token file and stats counters. This is a known limitation
  documented in KNOWN_ISSUES.md.
"""

import json
import logging
import os
import secrets
import stat
import time
from pathlib import Path

from errors import FusionIPCError, FusionTimeoutError

logger = logging.getLogger(__name__)

COMM_DIR = Path.home() / "fusion_mcp_comm"

# IPC protocol version (NR-1): integer, incremented on breaking schema changes.
# The add-in rejects commands with a mismatched version.
PROTOCOL_VERSION = 1

_session_token: str | None = None

# Monotonic counter to prevent command ID collisions within the same process
_command_counter = 0

# Session telemetry counters (REQ-P1-2). Opaque — never includes tokens.
_stats: dict = {
    "commands_sent": 0,
    "commands_succeeded": 0,
    "commands_timed_out": 0,
    "commands_failed": 0,
    "last_error": None,
    "last_tool": None,
}


def get_stats() -> dict:
    """Return a copy of session telemetry counters.

    Security: Explicitly returns only opaque counters. Never includes
    session_token, its hex length, or any derivation.
    """
    return {
        "commands_sent": _stats["commands_sent"],
        "commands_succeeded": _stats["commands_succeeded"],
        "commands_timed_out": _stats["commands_timed_out"],
        "commands_failed": _stats["commands_failed"],
        "last_error": _stats["last_error"],
        "last_tool": _stats["last_tool"],
    }


def _check_comm_dir() -> None:
    """Pre-flight check: verify COMM_DIR exists and is accessible.

    Raises FusionIPCError with diagnostic information if the directory
    is missing, not a directory, or not owned by the current user.
    """
    if not COMM_DIR.exists():
        raise FusionIPCError(
            f"Communication directory does not exist: {COMM_DIR}. "
            "Run the MCP server once to create it, or check that the path is correct.",
            tool_name="",
            remediation="Start the Fusion 360 MCP server to initialize the IPC directory.",
        )
    dir_stat = os.stat(COMM_DIR, follow_symlinks=False)
    if not stat.S_ISDIR(dir_stat.st_mode):
        raise FusionIPCError(
            f"{COMM_DIR} is not a real directory — possible symlink attack.",
            tool_name="",
            remediation="Remove the symlink at the COMM_DIR path and restart the server.",
        )
    if hasattr(os, "getuid") and dir_stat.st_uid != os.getuid():
        raise FusionIPCError(
            f"{COMM_DIR} is not owned by the current user (uid={dir_stat.st_uid}).",
            tool_name="",
            remediation="Verify COMM_DIR ownership matches the MCP server process user.",
        )


def initialize_ipc():
    """Create the IPC directory and generate a session token."""
    global _session_token
    COMM_DIR.mkdir(mode=0o700, exist_ok=True)
    os.chmod(COMM_DIR, 0o700)
    # Verify directory is a real directory owned by the current user (TOCTOU guard)
    _check_comm_dir()

    _session_token = secrets.token_hex(16)
    token_path = COMM_DIR / "session_token"
    tmp_path = COMM_DIR / "session_token.tmp"
    # Write with restricted permissions atomically (no race window)
    fd = os.open(str(tmp_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, _session_token.encode())
    finally:
        os.close(fd)
    os.replace(tmp_path, token_path)
    logger.info("IPC initialized: COMM_DIR=%s", COMM_DIR)


def send_fusion_command(tool_name: str, params: dict, *, timeout_s: float = 45.0) -> dict:
    """Send a command to Fusion 360 via file-based IPC.

    Writes a uniquely-identified JSON command file and polls for the response.
    Includes the session token for authentication.

    Args:
        tool_name: The tool/handler name to invoke.
        params: Parameters dict to pass to the handler.
        timeout_s: Maximum seconds to wait for response (default 45.0, clamped to [1.0, 60.0]).

    Returns:
        The response dict from Fusion 360 (contains 'success' key).

    Raises:
        FusionTimeoutError: If the command times out.
        FusionIPCError: If the response is invalid or COMM_DIR is missing.
    """
    global _command_counter

    # Clamp timeout to safe range
    timeout_s = max(1.0, min(timeout_s, 60.0))

    # Pre-flight: verify COMM_DIR is accessible
    _check_comm_dir()

    _command_counter += 1

    # Combine timestamp + counter + random suffix to guarantee uniqueness
    cmd_id = f"{int(time.time() * 1000)}_{_command_counter}_{secrets.token_hex(4)}"
    cmd_file = COMM_DIR / f"command_{cmd_id}.json"
    resp_file = COMM_DIR / f"response_{cmd_id}.json"

    command = {"type": "tool", "name": tool_name, "params": params, "id": cmd_id, "protocol_version": PROTOCOL_VERSION}
    if _session_token is None:
        # Lazy init: supports multi-process FastMCP workers that import without __main__
        initialize_ipc()
    command["session_token"] = _session_token

    # Atomic write: write to .tmp then rename so the add-in never reads partial JSON
    tmp_file = COMM_DIR / f"command_{cmd_id}.tmp"
    fd = os.open(str(tmp_file), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, json.dumps(command).encode())
    finally:
        os.close(fd)
    os.replace(tmp_file, cmd_file)

    # Increment counters only after successful dispatch
    _stats["commands_sent"] += 1
    _stats["last_tool"] = tool_name
    logger.debug("Command sent: tool=%s cmd_id=%s timeout_s=%.1f", tool_name, cmd_id, timeout_s)
    start_time = time.monotonic()

    # Calculate polling iterations: timeout_s / 0.05s per iteration
    max_iterations = int(timeout_s / 0.05)
    midpoint = max_iterations // 2

    try:
        for i in range(max_iterations):
            if resp_file.exists():
                elapsed_ms = (time.monotonic() - start_time) * 1000
                try:
                    with open(resp_file, "r") as f:
                        result = json.load(f)
                except (json.JSONDecodeError, OSError) as e:
                    _stats["commands_failed"] += 1
                    _stats["last_error"] = f"Malformed response for {tool_name}"
                    raise FusionIPCError(
                        f"Malformed response from Fusion 360: {e}",
                        tool_name=tool_name,
                        remediation="The add-in may have written a partial response. Retry the command.",
                    ) from None  # Strip __cause__ chain
                resp_file.unlink(missing_ok=True)
                cmd_file.unlink(missing_ok=True)
                logger.debug("Response received: tool=%s cmd_id=%s elapsed_ms=%.1f", tool_name, cmd_id, elapsed_ms)
                if not result.get("success"):
                    _stats["commands_failed"] += 1
                    error_msg = result.get("error", "Unknown error")
                    _stats["last_error"] = error_msg
                    raise FusionIPCError(
                        error_msg,
                        tool_name=tool_name,
                        remediation="Check the Fusion 360 add-in logs for details.",
                    )
                _stats["commands_succeeded"] += 1
                _stats["last_error"] = None
                return result
            if i == midpoint:
                logger.warning(
                    "Still waiting for '%s' (cmd_id=%s) after %.1fs",
                    tool_name,
                    cmd_id,
                    timeout_s / 2,
                )
            time.sleep(0.05)

        _stats["commands_timed_out"] += 1
        _stats["last_error"] = f"Timeout after {timeout_s}s for {tool_name}"
        logger.error("Timeout after %.1fs: tool=%s cmd_id=%s", timeout_s, tool_name, cmd_id)
        raise FusionTimeoutError(
            f"Timeout after {timeout_s:.0f}s waiting for '{tool_name}' — check that Fusion 360 is running, "
            "the FusionMCP add-in is loaded and active, and the comm directory is accessible.",
            tool_name=tool_name,
            remediation=(
                "1. Verify Fusion 360 is running and responsive. "
                "2. Check the FusionMCP add-in is loaded (Utilities > ADD-INS). "
                "3. Try ping() to test basic connectivity."
            ),
        )
    finally:
        cmd_file.unlink(missing_ok=True)
        resp_file.unlink(missing_ok=True)
