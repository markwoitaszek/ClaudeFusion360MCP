"""Tests for scripts/install.py (LT-2 installer)."""

import platform
import sys
from pathlib import Path

import pytest

# Add scripts/ to path so we can import install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import install


def test_detect_platform_unsupported(monkeypatch):
    """Unsupported OS raises SystemExit."""
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    with pytest.raises(SystemExit):
        install.detect_platform()


def test_detect_platform_darwin(monkeypatch):
    """macOS returns the correct add-in path."""
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    system, addin_dir = install.detect_platform()
    assert system == "Darwin"
    assert "AddIns" in str(addin_dir)
    assert "Autodesk" in str(addin_dir)


def test_check_prerequisites_dry_run(capsys):
    """Dry-run mode reports Python version without exiting."""
    install.check_prerequisites(dry_run=True)
    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out
    assert "Python" in captured.out


def test_check_prerequisites_low_python(monkeypatch):
    """Python version below 3.10 raises SystemExit."""
    monkeypatch.setattr(sys, "version_info", (3, 9, 0))
    monkeypatch.setattr(sys, "version", "3.9.0 (test)")
    with pytest.raises(SystemExit):
        install.check_prerequisites(dry_run=False)


def test_deploy_addin_dry_run(tmp_path, capsys, monkeypatch):
    """Dry-run prints target path but doesn't copy."""
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    target_dir = tmp_path / "AddIns"
    target_dir.mkdir()
    install.deploy_addin(target_dir, dry_run=True)
    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out
    assert not (target_dir / "FusionMCP").exists()


def test_deploy_addin_missing_dir(tmp_path, monkeypatch):
    """Missing add-in directory raises SystemExit with message."""
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    missing_dir = tmp_path / "nonexistent" / "AddIns"
    with pytest.raises(SystemExit):
        install.deploy_addin(missing_dir, dry_run=False)


def test_symlink_safety_rejects_outside_home(tmp_path, monkeypatch):
    """Path resolving outside home directory is rejected."""
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    # Create a directory that exists but make home resolve to somewhere else
    addin_dir = tmp_path / "AddIns"
    addin_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "fake_home")
    (tmp_path / "fake_home").mkdir()

    with pytest.raises(SystemExit):
        install.deploy_addin(addin_dir, dry_run=False)


def test_main_returns_int(monkeypatch, tmp_path):
    """main() returns 0 on successful dry-run."""
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setattr(sys, "argv", ["install.py", "--dry-run"])
    result = install.main()
    assert result == 0


def test_appdata_missing_on_windows(monkeypatch):
    """Windows without APPDATA fails fast."""
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.delenv("APPDATA", raising=False)
    with pytest.raises(SystemExit):
        install._get_addin_dirs()
