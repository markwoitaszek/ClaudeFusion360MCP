"""Tests for scripts/check_version_sync.py (LT-4 version drift detector)."""

import json
import sys
from pathlib import Path

# Add scripts/ to path so we can import check_version_sync
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import check_version_sync


def _create_version_files(tmp_path, pyproject_version, version_file_version, manifest_version):
    """Create synthetic version source files in tmp_path."""
    # pyproject.toml
    (tmp_path / "pyproject.toml").write_text(f'[project]\nname = "test"\nversion = "{pyproject_version}"\n')
    # VERSION
    (tmp_path / "VERSION").write_text(f"{version_file_version}\n")
    # FusionMCP.manifest
    manifest_dir = tmp_path / "fusion-addin"
    manifest_dir.mkdir()
    (manifest_dir / "FusionMCP.manifest").write_text(json.dumps({"version": manifest_version}))
    # Skill files with mcp_version frontmatter
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    for name in ("SKILL.md", "SPATIAL_AWARENESS.md"):
        (docs_dir / name).write_text(f"---\nmcp_version: {pyproject_version}\ntier: core\n---\n")
    return tmp_path


def test_all_versions_match(tmp_path, monkeypatch):
    """All sources matching returns 0."""
    _create_version_files(tmp_path, "7.2.0", "7.2.0", "7.2.0")
    monkeypatch.setattr(check_version_sync, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        check_version_sync,
        "VERSION_SOURCES",
        {
            "pyproject.toml": tmp_path / "pyproject.toml",
            "VERSION": tmp_path / "VERSION",
            "FusionMCP.manifest": tmp_path / "fusion-addin" / "FusionMCP.manifest",
        },
    )
    monkeypatch.setattr(
        check_version_sync,
        "SKILL_FILES",
        [tmp_path / "docs" / "SKILL.md", tmp_path / "docs" / "SPATIAL_AWARENESS.md"],
    )
    result = check_version_sync.main()
    assert result == 0


def test_version_drift_detected(tmp_path, monkeypatch):
    """Mismatched VERSION file returns 1."""
    _create_version_files(tmp_path, "7.2.0", "7.1.0", "7.2.0")
    monkeypatch.setattr(check_version_sync, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        check_version_sync,
        "VERSION_SOURCES",
        {
            "pyproject.toml": tmp_path / "pyproject.toml",
            "VERSION": tmp_path / "VERSION",
            "FusionMCP.manifest": tmp_path / "fusion-addin" / "FusionMCP.manifest",
        },
    )
    monkeypatch.setattr(
        check_version_sync,
        "SKILL_FILES",
        [tmp_path / "docs" / "SKILL.md", tmp_path / "docs" / "SPATIAL_AWARENESS.md"],
    )
    result = check_version_sync.main()
    assert result == 1


def test_missing_file_returns_error(tmp_path, monkeypatch):
    """Missing pyproject.toml returns 1."""
    monkeypatch.setattr(check_version_sync, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        check_version_sync,
        "VERSION_SOURCES",
        {
            "pyproject.toml": tmp_path / "pyproject.toml",
            "VERSION": tmp_path / "VERSION",
            "FusionMCP.manifest": tmp_path / "fusion-addin" / "FusionMCP.manifest",
        },
    )
    # Don't create any files — all should be missing
    result = check_version_sync.main()
    assert result == 1


def test_regex_fallback_works(tmp_path, monkeypatch):
    """Version parsing works when tomllib is unavailable."""
    import builtins

    _create_version_files(tmp_path, "1.2.3", "1.2.3", "1.2.3")

    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "tomllib":
            raise ImportError("mocked: tomllib unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    version = check_version_sync.read_pyproject_version(tmp_path / "pyproject.toml")
    assert version == "1.2.3"
