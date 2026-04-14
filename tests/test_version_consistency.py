"""Tests for version consistency across all components (LT-4).

These tests verify that pyproject.toml, VERSION, and FusionMCP.manifest
all declare the same version string.
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _read_pyproject_version() -> str:
    text = (PROJECT_ROOT / "pyproject.toml").read_text()
    try:
        import tomllib

        return tomllib.loads(text)["project"]["version"]
    except ImportError:
        match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        assert match, "Could not parse version from pyproject.toml"
        return match.group(1)


def test_version_file_matches_pyproject():
    expected = _read_pyproject_version()
    actual = (PROJECT_ROOT / "VERSION").read_text().strip()
    assert actual == expected, f"VERSION file ({actual}) does not match pyproject.toml ({expected})"


def test_manifest_version_matches_pyproject():
    expected = _read_pyproject_version()
    manifest = json.loads((PROJECT_ROOT / "fusion-addin" / "FusionMCP.manifest").read_text(encoding="utf-8-sig"))
    actual = manifest["version"]
    assert actual == expected, f"FusionMCP.manifest ({actual}) does not match pyproject.toml ({expected})"


def test_version_is_valid_semver():
    version = _read_pyproject_version()
    assert re.match(r"^\d+\.\d+\.\d+$", version), f"Version {version} is not valid semver (X.Y.Z)"
