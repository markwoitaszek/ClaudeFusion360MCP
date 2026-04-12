"""Tests for validate_filepath() — the security-critical path validation function."""

import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Mock the mcp package before importing the server module.
# The server depends on mcp.server.fastmcp.FastMCP which may not be installed
# in the test environment. We only need validate_filepath and SAFE_EXPORT_DIRS.
mcp_mock = types.ModuleType("mcp")
mcp_server_mock = types.ModuleType("mcp.server")
mcp_fastmcp_mock = types.ModuleType("mcp.server.fastmcp")
mcp_fastmcp_mock.FastMCP = MagicMock()
mcp_mock.server = mcp_server_mock
mcp_server_mock.fastmcp = mcp_fastmcp_mock
sys.modules["mcp"] = mcp_mock
sys.modules["mcp.server"] = mcp_server_mock
sys.modules["mcp.server.fastmcp"] = mcp_fastmcp_mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))
from validation import SAFE_EXPORT_DIRS, validate_filepath


class TestValidateFilepath:
    """Test suite for validate_filepath()."""

    # --- Valid paths ---

    def test_valid_desktop_path(self, tmp_path):
        """A path within ~/Desktop should pass validation."""
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            pytest.skip("~/Desktop does not exist on this system")
        filepath = str(desktop / "test_model.stl")
        result = validate_filepath(filepath, allowed_extensions=[".stl"])
        assert result == (desktop / "test_model.stl").resolve()

    def test_valid_downloads_path(self):
        """A path within ~/Downloads should pass validation."""
        downloads = Path.home() / "Downloads"
        if not downloads.exists():
            pytest.skip("~/Downloads does not exist on this system")
        filepath = str(downloads / "export.step")
        result = validate_filepath(filepath, allowed_extensions=[".step", ".stp"])
        assert result == (downloads / "export.step").resolve()

    def test_valid_documents_path(self):
        """A path within ~/Documents should pass validation."""
        docs = Path.home() / "Documents"
        if not docs.exists():
            pytest.skip("~/Documents does not exist on this system")
        filepath = str(docs / "model.3mf")
        result = validate_filepath(filepath, allowed_extensions=[".3mf"])
        assert result == (docs / "model.3mf").resolve()

    def test_tilde_expansion(self):
        """Tilde paths should be expanded correctly."""
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            pytest.skip("~/Desktop does not exist on this system")
        result = validate_filepath("~/Desktop/test.stl", allowed_extensions=[".stl"])
        assert result == (desktop / "test.stl").resolve()

    def test_no_extension_filter(self):
        """When no allowed_extensions, any extension should pass."""
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            pytest.skip("~/Desktop does not exist on this system")
        result = validate_filepath(str(desktop / "anything.xyz"))
        assert result.name == "anything.xyz"

    # --- Invalid paths: path traversal ---

    def test_path_traversal_absolute(self):
        """Absolute paths outside safe dirs should be rejected."""
        with pytest.raises(ValueError, match="outside allowed directories"):
            validate_filepath("/etc/passwd")

    def test_path_traversal_relative(self):
        """Relative paths that escape safe dirs should be rejected."""
        with pytest.raises(ValueError, match="outside allowed directories"):
            validate_filepath("../../etc/passwd")

    def test_path_traversal_via_dotdot(self):
        """Desktop/../../../etc/passwd should be rejected after resolution."""
        desktop = Path.home() / "Desktop"
        traversal = str(desktop / ".." / ".." / ".." / "etc" / "passwd")
        with pytest.raises(ValueError, match="outside allowed directories"):
            validate_filepath(traversal)

    def test_path_outside_home(self):
        """Paths outside home directory should be rejected."""
        with pytest.raises(ValueError, match="outside allowed directories"):
            validate_filepath("/tmp/evil.stl", allowed_extensions=[".stl"])

    # --- Invalid paths: empty and null ---

    def test_empty_string(self):
        """Empty string should be rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_filepath("")

    def test_whitespace_only(self):
        """Whitespace-only string should be rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_filepath("   ")

    def test_null_byte(self):
        """Paths with null bytes should be rejected."""
        with pytest.raises(ValueError, match="null bytes"):
            validate_filepath("/Users/test\x00/file.stl")

    def test_null_byte_in_filename(self):
        """Null bytes in filename should be rejected."""
        desktop = Path.home() / "Desktop"
        with pytest.raises(ValueError, match="null bytes"):
            validate_filepath(str(desktop / "test\x00.stl"))

    # --- Invalid paths: wrong extension ---

    def test_wrong_extension(self):
        """Wrong file extension should be rejected."""
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            pytest.skip("~/Desktop does not exist on this system")
        with pytest.raises(ValueError, match="not allowed"):
            validate_filepath(str(desktop / "model.obj"), allowed_extensions=[".stl"])

    def test_no_extension(self):
        """File with no extension should be rejected when extensions are required."""
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            pytest.skip("~/Desktop does not exist on this system")
        with pytest.raises(ValueError, match="not allowed"):
            validate_filepath(str(desktop / "model"), allowed_extensions=[".stl"])

    def test_case_insensitive_extension(self):
        """Extension matching should be case-insensitive."""
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            pytest.skip("~/Desktop does not exist on this system")
        # .STL should match .stl (extension is lowered before comparison)
        result = validate_filepath(str(desktop / "model.STL"), allowed_extensions=[".stl"])
        assert result.suffix.lower() == ".stl"

    def test_step_stp_both_allowed(self):
        """Both .step and .stp should be accepted for STEP files."""
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            pytest.skip("~/Desktop does not exist on this system")
        validate_filepath(str(desktop / "model.step"), allowed_extensions=[".step", ".stp"])
        validate_filepath(str(desktop / "model.stp"), allowed_extensions=[".step", ".stp"])

    # --- Edge cases ---

    def test_nested_subdirectory(self):
        """Paths in subdirectories of safe dirs should pass."""
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            pytest.skip("~/Desktop does not exist on this system")
        result = validate_filepath(str(desktop / "projects" / "fusion" / "model.stl"), allowed_extensions=[".stl"])
        assert "projects" in str(result)

    def test_safe_export_dirs_are_resolved(self):
        """SAFE_EXPORT_DIRS should be pre-resolved Path objects."""
        for safe_dir in SAFE_EXPORT_DIRS:
            # Resolved paths should not contain ~ or relative components
            assert "~" not in str(safe_dir)
            assert safe_dir.is_absolute()
