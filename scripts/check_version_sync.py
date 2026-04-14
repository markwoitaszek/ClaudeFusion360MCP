#!/usr/bin/env python3
"""Check that version strings are consistent across all components.

Reads the canonical version from pyproject.toml and verifies that VERSION
and FusionMCP.manifest match. Exits non-zero on drift.

Usage:
    python scripts/check_version_sync.py
"""
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

VERSION_SOURCES = {
    "pyproject.toml": PROJECT_ROOT / "pyproject.toml",
    "VERSION": PROJECT_ROOT / "VERSION",
    "FusionMCP.manifest": PROJECT_ROOT / "fusion-addin" / "FusionMCP.manifest",
}


def read_pyproject_version(path: Path) -> str:
    """Read version from pyproject.toml using tomllib (3.11+) or regex fallback."""
    text = path.read_text()
    try:
        import tomllib

        data = tomllib.loads(text)
        return data["project"]["version"]
    except ImportError:
        match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if not match:
            raise ValueError(f"Could not parse version from {path}")
        return match.group(1)


def read_version_file(path: Path) -> str:
    return path.read_text().strip()


def read_manifest_version(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data["version"]


READERS = {
    "pyproject.toml": read_pyproject_version,
    "VERSION": read_version_file,
    "FusionMCP.manifest": read_manifest_version,
}


def main() -> int:
    canonical_source = "pyproject.toml"
    versions: dict[str, str] = {}
    errors: list[str] = []

    for name, path in VERSION_SOURCES.items():
        if not path.exists():
            errors.append(f"  {name}: file not found at {path}")
            continue
        try:
            versions[name] = READERS[name](path)
        except Exception as e:
            errors.append(f"  {name}: failed to read — {e}")

    if errors:
        print("Version sync FAILED — could not read sources:")
        print("\n".join(errors))
        return 1

    if canonical_source not in versions:
        print(f"Version sync FAILED — canonical source {canonical_source} could not be read")
        return 1

    canonical = versions[canonical_source]
    drift: list[str] = []
    for name, version in versions.items():
        status = "OK" if version == canonical else "DRIFT"
        if status == "DRIFT":
            drift.append(f"  {name}: {version} (expected {canonical})")
        print(f"  {name}: {version} [{status}]")

    if drift:
        print(f"\nVersion sync FAILED — {len(drift)} source(s) diverge from {canonical_source} ({canonical}):")
        print("\n".join(drift))
        return 1

    print(f"\nVersion sync OK — all sources match {canonical}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
