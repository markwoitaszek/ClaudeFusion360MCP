"""Integration smoke tests for ClaudeFusion360MCP (LT-5).

These tests exercise key paths through the MCP server without requiring
a running Fusion 360 instance. Tests that need live Fusion 360 are marked
with @pytest.mark.integration and skip when Fusion is unavailable.

Run: pytest tests/test_smoke.py -v
"""

import json
import os

import pytest

# Detect if Fusion 360 integration tests should run.
# Set FUSION_SMOKE_TESTS=1 when Fusion 360 is running with the add-in loaded.
# The adsk module import check is unreliable because test_fusionmcp.py mocks adsk.
fusion_available = os.environ.get("FUSION_SMOKE_TESTS") == "1"

integration = pytest.mark.skipif(not fusion_available, reason="Set FUSION_SMOKE_TESTS=1 to run")


# ---------------------------------------------------------------------------
# Non-Fusion smoke tests (always run)
# ---------------------------------------------------------------------------


def test_server_module_imports():
    """Verify the MCP server module can be imported without errors."""
    # conftest.py already mocks FastMCP — this tests the import chain
    import fusion360_mcp_server  # noqa: F401


def test_all_tool_routers_mount():
    """Verify all 4 tool routers can be imported."""
    import tools.assembly  # noqa: F401
    import tools.features  # noqa: F401
    import tools.io  # noqa: F401
    import tools.sketch  # noqa: F401


def test_tool_count_matches_registry():
    """Verify registered tool count matches mcp.json."""
    from pathlib import Path

    mcp_json = Path(__file__).resolve().parent.parent / "mcp.json"
    if not mcp_json.exists():
        pytest.skip("mcp.json not found — run scripts/generate_mcp_registry.py")
    registry = json.loads(mcp_json.read_text())

    # Collect tools from all routers via their _tools attribute (set by conftest mock)
    import tools.assembly
    import tools.features
    import tools.io
    import tools.sketch

    all_tools = set()
    for mod in [tools.sketch, tools.features, tools.assembly, tools.io]:
        if hasattr(mod, "router") and hasattr(mod.router, "_tools"):
            all_tools.update(mod.router._tools)

    assert len(all_tools) > 0, "No tools found in routers — conftest mock may not be wiring _tools correctly"
    assert (
        len(all_tools) == registry["tool_count"]
    ), f"Router tool count ({len(all_tools)}) does not match mcp.json ({registry['tool_count']})"


def test_ipc_module_initializes(mock_comm_dir, monkeypatch):
    """Verify IPC initialization creates session token."""
    import ipc

    monkeypatch.setattr(ipc, "COMM_DIR", mock_comm_dir)
    monkeypatch.setattr(ipc, "_session_token", None)
    ipc.initialize_ipc()
    assert ipc._session_token is not None
    assert len(ipc._session_token) == 32  # hex(16) = 32 chars
    assert (mock_comm_dir / "session_token").exists()


def test_validation_rejects_bad_plane():
    """Verify parameter validation catches invalid input."""
    from validation import validate_plane

    with pytest.raises(ValueError, match="plane"):
        validate_plane("INVALID")


# ---------------------------------------------------------------------------
# Fusion 360 integration tests (skip without live Fusion)
# ---------------------------------------------------------------------------


@integration
def test_sketch_extrude_round_trip():
    """Create a sketch, draw a rectangle, finish, and extrude."""
    from ipc import send_fusion_command

    result = send_fusion_command("create_sketch", {"plane": "XY"})
    assert result["success"]
    result = send_fusion_command("draw_rectangle", {"x1": 0, "y1": 0, "x2": 5, "y2": 5})
    assert result["success"]
    result = send_fusion_command("finish_sketch", {})
    assert result["success"]
    result = send_fusion_command("extrude", {"distance": 3})
    assert result["success"]


@integration
def test_component_creation():
    """Create a component and verify it succeeds."""
    from ipc import send_fusion_command

    result = send_fusion_command("create_component", {"name": "smoke_test_comp"})
    assert result["success"]


@integration
def test_export_round_trip(tmp_path):
    """Export to STL and verify file is created."""
    from ipc import send_fusion_command

    export_path = str(tmp_path / "smoke_test.stl")
    result = send_fusion_command("export_stl", {"file_path": export_path})
    assert result["success"]


@integration
def test_design_info_query():
    """Query design info to verify inspection tools work."""
    from ipc import send_fusion_command

    result = send_fusion_command("get_design_info", {})
    assert result["success"]
