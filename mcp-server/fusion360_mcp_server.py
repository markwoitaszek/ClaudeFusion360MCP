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

Architecture: FastMCP with include_router for modular tool registration.
IPC: File-based JSON in ~/fusion_mcp_comm/ with session token (see ipc.py).
"""

try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("fusion360-mcp-server")
except Exception:
    __version__ = "0.0.0-dev"

from ipc import initialize_ipc
from mcp.server.fastmcp import FastMCP
from tools.assembly import router as assembly_router
from tools.features import router as features_router
from tools.io import router as io_router
from tools.sketch import router as sketch_router

mcp = FastMCP(f"Fusion 360 v{__version__}")

# Mount all tool modules — each router's @tool() decorators are registered on the main server
mcp.include_router(sketch_router)
mcp.include_router(features_router)
mcp.include_router(assembly_router)
mcp.include_router(io_router)

if __name__ == "__main__":
    initialize_ipc()
    mcp.run()
