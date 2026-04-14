#!/usr/bin/env python3
"""Generate mcp.json from FastMCP tool introspection.

Imports each tool module with a transparent FastMCP mock, inspects function
signatures and docstrings, and writes mcp.json with tool metadata.

Usage:
    python scripts/generate_mcp_registry.py           # Generate mcp.json
    python scripts/generate_mcp_registry.py --check    # Validate freshness (CI mode)
"""
import inspect
import json
import os
import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER_DIR = PROJECT_ROOT / "mcp-server"
OUTPUT_PATH = PROJECT_ROOT / "mcp.json"


# ---------------------------------------------------------------------------
# ToolIntrospector — captures tool metadata via a transparent FastMCP mock
# ---------------------------------------------------------------------------


class ToolIntrospector:
    """Introspect FastMCP tool modules to extract metadata without running the server."""

    def __init__(self):
        self._tools: list[dict] = []
        self._mock_installed = False

    def _install_mock(self):
        """Install a transparent FastMCP mock into sys.modules."""
        if self._mock_installed:
            return

        introspector = self

        class _CapturingFastMCP:
            def __init__(self, name="mock"):
                self.name = name

            def tool(self):
                def decorator(fn):
                    introspector._register_tool(fn)
                    return fn

                return decorator

            def include_router(self, router):
                pass

            def run(self):
                pass

        mcp_mock = types.ModuleType("mcp")
        mcp_server_mock = types.ModuleType("mcp.server")
        mcp_fastmcp_mock = types.ModuleType("mcp.server.fastmcp")
        mcp_fastmcp_mock.FastMCP = _CapturingFastMCP
        mcp_mock.server = mcp_server_mock
        mcp_server_mock.fastmcp = mcp_fastmcp_mock
        sys.modules["mcp"] = mcp_mock
        sys.modules["mcp.server"] = mcp_server_mock
        sys.modules["mcp.server.fastmcp"] = mcp_fastmcp_mock

        if str(MCP_SERVER_DIR) not in sys.path:
            sys.path.insert(0, str(MCP_SERVER_DIR))

        self._mock_installed = True

    def _register_tool(self, fn):
        """Extract metadata from a decorated tool function."""
        sig = inspect.signature(fn)
        params = {}
        for name, param in sig.parameters.items():
            param_info: dict = {"type": _python_type_to_json(param.annotation)}
            if param.default is not inspect.Parameter.empty:
                param_info["default"] = param.default
            params[name] = param_info

        doc = inspect.getdoc(fn) or ""
        summary = doc.split("\n\n")[0].strip() if doc else ""

        self._tools.append(
            {
                "name": fn.__name__,
                "description": summary,
                "parameters": params,
            }
        )

    def extract_tools(self) -> list[dict]:
        """Import all tool modules and return extracted tool metadata."""
        self._install_mock()

        # Import tool modules — the decorators fire and register tools
        import tools.assembly  # noqa: F401
        import tools.features  # noqa: F401
        import tools.io  # noqa: F401
        import tools.sketch  # noqa: F401

        return sorted(self._tools, key=lambda t: t["name"])

    def generate_registry(self) -> dict:
        """Generate the full mcp.json registry object."""
        tools = self.extract_tools()
        version = _read_version()

        return {
            "name": "fusion360-mcp-server",
            "version": version,
            "description": "Control Autodesk Fusion 360 with Claude AI through the Model Context Protocol",
            "tool_count": len(tools),
            "tools": tools,
        }


def _python_type_to_json(annotation) -> str:
    """Map Python type annotations to JSON schema type strings."""
    if annotation is inspect.Parameter.empty:
        return "string"
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }
    return type_map.get(annotation, "string")


def _read_version() -> str:
    """Read version from pyproject.toml."""
    import re

    text = (PROJECT_ROOT / "pyproject.toml").read_text()
    try:
        import tomllib

        return tomllib.loads(text)["project"]["version"]
    except ImportError:
        match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        return match.group(1) if match else "0.0.0"


def main():
    check_mode = "--check" in sys.argv

    introspector = ToolIntrospector()
    registry = introspector.generate_registry()
    generated = json.dumps(registry, indent=2) + "\n"

    if check_mode:
        if not OUTPUT_PATH.exists():
            print(f"FAIL: {OUTPUT_PATH} does not exist. Run without --check to generate.")
            return 1
        existing = OUTPUT_PATH.read_text()
        if existing == generated:
            print(f"OK: {OUTPUT_PATH} is up to date ({registry['tool_count']} tools)")
            return 0
        else:
            print(f"FAIL: {OUTPUT_PATH} is stale. Regenerate with: python scripts/generate_mcp_registry.py")
            return 1

    OUTPUT_PATH.write_text(generated)
    print(f"Generated {OUTPUT_PATH} with {registry['tool_count']} tools")
    return 0


if __name__ == "__main__":
    # Suppress ipc module side-effects during introspection
    os.environ.setdefault("MCP_REGISTRY_MODE", "1")
    sys.exit(main())
