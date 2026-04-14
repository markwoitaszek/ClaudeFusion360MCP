"""Tests for MCP registry generation (LT-1).

Validates that the ToolIntrospector correctly extracts tool metadata
and that mcp.json is up to date.
"""

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MCP_JSON = PROJECT_ROOT / "mcp.json"


@pytest.fixture
def registry():
    """Load mcp.json as a dict."""
    assert MCP_JSON.exists(), f"mcp.json not found at {MCP_JSON}. Run: python scripts/generate_mcp_registry.py"
    return json.loads(MCP_JSON.read_text())


def test_registry_has_required_fields(registry):
    assert "name" in registry
    assert "version" in registry
    assert "tool_count" in registry
    assert "tools" in registry


def test_registry_tool_count_matches(registry):
    assert registry["tool_count"] == len(
        registry["tools"]
    ), f"tool_count ({registry['tool_count']}) does not match actual tool list length ({len(registry['tools'])})"


def test_registry_has_expected_tool_count(registry):
    assert registry["tool_count"] >= 39, f"Expected at least 39 tools, found {registry['tool_count']}"


def test_each_tool_has_required_fields(registry):
    for tool in registry["tools"]:
        assert "name" in tool, f"Tool missing 'name': {tool}"
        assert "description" in tool, f"Tool {tool.get('name')} missing 'description'"
        assert "parameters" in tool, f"Tool {tool.get('name')} missing 'parameters'"


def test_known_tools_present(registry):
    tool_names = {t["name"] for t in registry["tools"]}
    expected = {"create_sketch", "extrude", "export_stl", "batch", "fillet", "create_component"}
    missing = expected - tool_names
    assert not missing, f"Expected tools missing from registry: {missing}"


def test_tool_descriptions_not_empty(registry):
    empty = [t["name"] for t in registry["tools"] if not t["description"]]
    assert not empty, f"Tools with empty descriptions: {empty}"


def test_registry_version_matches_pyproject(registry):
    import re

    text = (PROJECT_ROOT / "pyproject.toml").read_text()
    try:
        import tomllib

        expected = tomllib.loads(text)["project"]["version"]
    except ImportError:
        match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        expected = match.group(1) if match else None
    assert (
        registry["version"] == expected
    ), f"mcp.json version ({registry['version']}) does not match pyproject.toml ({expected})"
