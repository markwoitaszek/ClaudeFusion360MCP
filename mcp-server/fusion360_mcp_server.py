#!/usr/bin/env python3
"""
Fusion 360 MCP Server
===========================
Modular MCP server bridging Claude AI to Autodesk Fusion 360.

Tool modules:
  - tools/sketch.py    : Sketch creation and geometry (12 tools)
  - tools/features.py  : 3D operations, patterns, boolean (10 tools)
  - tools/assembly.py  : Components, joints, positioning (10 tools)
  - tools/io.py        : Export/import, inspection, measurement (8 tools)
  - tools/planning.py  : Offline design brief and batch estimation (2 tools)

Architecture: FastMCP with include_router for modular tool registration.
IPC: File-based JSON in ~/fusion_mcp_comm/ with session token (see ipc.py).
"""

import json
import logging
import os
import time

# ---------------------------------------------------------------------------
# Logging configuration (applies regardless of invocation method)
# ---------------------------------------------------------------------------

_valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
_log_level = _log_level if _log_level in _valid_levels else "INFO"


class JsonFormatter(logging.Formatter):
    """Structured JSON log formatter, activated via LOG_FORMAT=json.

    Produces one JSON object per line with timestamp, level, logger name,
    and message. Suitable for log aggregation pipelines.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


class TokenScrubFilter(logging.Filter):
    """Blocks log records containing 'session_token' to prevent leakage.

    Security (MUST NOT #10): Session token must never appear in telemetry
    logs or structured log output. Checks both the message and exc_info.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if "session_token" in record.getMessage():
            return False
        if record.exc_info and record.exc_info[1] is not None:
            if "session_token" in str(record.exc_info[1]):
                return False
        return True


# Choose formatter based on LOG_FORMAT env var
_log_format = os.environ.get("LOG_FORMAT", "text").lower()
_handler = logging.StreamHandler()
_handler.addFilter(TokenScrubFilter())

if _log_format == "json":
    _handler.setFormatter(JsonFormatter())
else:
    _handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

# Explicitly configure root logger to guarantee TokenScrubFilter is active,
# even if an imported module (e.g., mcp) called basicConfig first.
_root_logger = logging.getLogger()
_root_logger.setLevel(getattr(logging, _log_level, logging.INFO))
_root_logger.handlers = [_handler]

# ---------------------------------------------------------------------------
# Version detection
# ---------------------------------------------------------------------------

try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("fusion360-mcp-server")
except Exception:
    __version__ = "0.0.0-dev"

# ---------------------------------------------------------------------------
# MCP server setup
# ---------------------------------------------------------------------------

from ipc import get_stats, initialize_ipc  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402
from tools.assembly import router as assembly_router  # noqa: E402
from tools.features import router as features_router  # noqa: E402
from tools.io import router as io_router  # noqa: E402
from tools.planning import router as planning_router  # noqa: E402
from tools.sketch import router as sketch_router  # noqa: E402

mcp = FastMCP(f"Fusion 360 v{__version__}")

# Mount all tool modules — each router's @tool() decorators are registered on the main server
mcp.include_router(sketch_router)
mcp.include_router(features_router)
mcp.include_router(assembly_router)
mcp.include_router(io_router)
mcp.include_router(planning_router)


# ---------------------------------------------------------------------------
# Session stats tool (REQ-P1-2)
# ---------------------------------------------------------------------------


@mcp.tool()
def get_session_stats() -> dict:
    """Get MCP server session statistics (commands sent, succeeded, timed out, failed).

    Returns opaque counters only — never includes session token or internal state.
    Safe to call at any time, including when Fusion 360 is not connected.
    """
    stats = get_stats()
    stats["server_version"] = __version__
    stats["uptime_seconds"] = round(time.monotonic() - _start_time, 1) if _start_time else 0
    return stats


# Track server start time for uptime calculation
_start_time: float | None = None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Start the Fusion 360 MCP server.

    Initializes IPC, logs startup info, and runs the MCP event loop.
    Extracted from __main__ to support CLI entry point (pyproject.toml scripts).
    """
    global _start_time
    _start_time = time.monotonic()
    logging.getLogger(__name__).info("Fusion 360 MCP Server v%s starting", __version__)
    initialize_ipc()
    mcp.run()


if __name__ == "__main__":
    main()
