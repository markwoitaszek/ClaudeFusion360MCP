"""IPC layer: file-based communication between MCP server and Fusion 360 add-in.

Protocol (ADR-D002):
  1. MCP server writes command_{id}.json to COMM_DIR
  2. Add-in polls for command files, executes via Fusion 360 API
  3. Add-in writes response_{id}.json
  4. MCP server polls for response, returns result

Session token (MT-3):
  On startup, the MCP server generates a session token and writes it to
  COMM_DIR/session_token. Every command includes the token. The add-in
  validates the token and rejects commands without a matching token.
"""

import json
import os
import secrets
import stat
import time
from pathlib import Path

COMM_DIR = Path.home() / "fusion_mcp_comm"

_session_token: str | None = None

# Monotonic counter to prevent command ID collisions within the same process
_command_counter = 0


def initialize_ipc():
    """Create the IPC directory and generate a session token."""
    global _session_token
    COMM_DIR.mkdir(mode=0o700, exist_ok=True)
    os.chmod(COMM_DIR, 0o700)
    # Verify directory is a real directory owned by the current user (TOCTOU guard)
    dir_stat = os.stat(COMM_DIR, follow_symlinks=False)
    if not stat.S_ISDIR(dir_stat.st_mode):
        raise RuntimeError(f"{COMM_DIR} is not a real directory — possible symlink attack")
    if hasattr(os, "getuid") and dir_stat.st_uid != os.getuid():
        raise RuntimeError(f"{COMM_DIR} is not owned by current user")

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


def send_fusion_command(tool_name: str, params: dict) -> dict:
    """Send a command to Fusion 360 via file-based IPC.

    Writes a uniquely-identified JSON command file and polls for the response.
    Includes the session token for authentication.

    Args:
        tool_name: The tool/handler name to invoke.
        params: Parameters dict to pass to the handler.

    Returns:
        The response dict from Fusion 360 (contains 'success' key).

    Raises:
        Exception: If the command fails or times out after 45s.
    """
    global _command_counter
    _command_counter += 1
    # Combine timestamp + counter + random suffix to guarantee uniqueness
    cmd_id = f"{int(time.time() * 1000)}_{_command_counter}_{secrets.token_hex(4)}"
    cmd_file = COMM_DIR / f"command_{cmd_id}.json"
    resp_file = COMM_DIR / f"response_{cmd_id}.json"

    command = {"type": "tool", "name": tool_name, "params": params, "id": cmd_id}
    if _session_token is None:
        # Lazy init: supports multi-process FastMCP workers that import without __main__
        initialize_ipc()
    if _session_token is None:
        raise RuntimeError("IPC initialization failed: session token could not be generated")
    command["session_token"] = _session_token

    # Atomic write: write to .tmp then rename so the add-in never reads partial JSON
    tmp_file = COMM_DIR / f"command_{cmd_id}.tmp"
    fd = os.open(str(tmp_file), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, json.dumps(command).encode())
    finally:
        os.close(fd)
    os.replace(tmp_file, cmd_file)

    # 900 iterations at 50ms = 45s timeout
    try:
        for _ in range(900):
            if resp_file.exists():
                with open(resp_file, "r") as f:
                    result = json.load(f)
                resp_file.unlink(missing_ok=True)
                cmd_file.unlink(missing_ok=True)
                if not result.get("success"):
                    raise Exception(result.get("error", "Unknown error"))
                return result
            time.sleep(0.05)
        raise Exception(f"Timeout after 45s waiting for '{tool_name}' — is Fusion 360 running with FusionMCP add-in?")
    finally:
        cmd_file.unlink(missing_ok=True)
        resp_file.unlink(missing_ok=True)
