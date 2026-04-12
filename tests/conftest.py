"""Shared test fixtures for the MCP server test suite.

Provides mocked MCP and IPC layers so tests run without Fusion 360 or the mcp package.
"""

import os
import sys
import types

import pytest


# Create a mock FastMCP class whose .tool() decorator is transparent
# (returns the original function unchanged). This allows tests to call
# the actual tool functions while mocking only the IPC layer.
class _TransparentFastMCP:
    """Mock FastMCP that registers tools without wrapping them."""

    def __init__(self, name="mock"):
        self.name = name
        self._tools = []

    def tool(self):
        """Return a no-op decorator that preserves the original function."""

        def decorator(fn):
            self._tools.append(fn.__name__)
            return fn

        return decorator

    def include_router(self, router):
        pass

    def run(self):
        pass


# Mock the mcp package before any server modules are imported.
# This allows tests to run without `pip install mcp`.
mcp_mock = types.ModuleType("mcp")
mcp_server_mock = types.ModuleType("mcp.server")
mcp_fastmcp_mock = types.ModuleType("mcp.server.fastmcp")
mcp_fastmcp_mock.FastMCP = _TransparentFastMCP
mcp_mock.server = mcp_server_mock
mcp_server_mock.fastmcp = mcp_fastmcp_mock
sys.modules["mcp"] = mcp_mock
sys.modules["mcp.server"] = mcp_server_mock
sys.modules["mcp.server.fastmcp"] = mcp_fastmcp_mock

# Add mcp-server to Python path so modules can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))


@pytest.fixture
def mock_comm_dir(tmp_path):
    """Provide a temporary COMM_DIR for IPC tests."""
    comm_dir = tmp_path / "fusion_mcp_comm"
    comm_dir.mkdir(mode=0o700)
    return comm_dir


@pytest.fixture
def session_token():
    """Provide a fixed session token for testing."""
    return "test_session_token_abc123"
