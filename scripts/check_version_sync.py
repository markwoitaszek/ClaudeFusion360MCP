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

# Skill files with mcp_version frontmatter that must match the canonical version.
SKILL_FILES = [
    PROJECT_ROOT / "docs" / "SKILL.md",
    PROJECT_ROOT / "docs" / "SPATIAL_AWARENESS.md",
]


def read_pyproject_version(path: Path) -> str:
    """Read version from pyproject.toml using tomllib (3.11+) or regex fallback."""
    text = path.read_text()
    try:
        import tomllib

        data = tomllib.loads(text)
        return data["project"]["version"]
    except ImportError:
        import warnings

        warnings.warn(
            "tomllib unavailable (Python < 3.11); using regex fallback which may "
            "match a version= line outside [project] if one exists",
            stacklevel=2,
        )
        match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if not match:
            raise ValueError(f"Could not parse version from {path}")
        return match.group(1)


def read_version_file(path: Path) -> str:
    """Read version from a plain VERSION file (strips whitespace)."""
    return path.read_text().strip()


def read_manifest_version(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data["version"]


READERS = {
    "pyproject.toml": read_pyproject_version,
    "VERSION": read_version_file,
    "FusionMCP.manifest": read_manifest_version,
}


def _extract_python_constant(path: Path, name: str) -> str | None:
    """Extract a Python constant assignment (e.g., PROTOCOL_VERSION = 1) from a file."""
    pattern = rf"^{re.escape(name)}\s*=\s*(.+?)$"
    text = path.read_text()
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        return None
    raw = match.group(1).strip().strip('"').strip("'")
    return raw


# Cross-runtime constants that must match between mcp-server and fusion-addin.
# Each entry: (constant_name, [(label, file_path), ...])
PARITY_CHECKS: list[tuple[str, list[tuple[str, Path]]]] = [
    (
        "PROTOCOL_VERSION",
        [
            ("mcp-server/ipc.py", PROJECT_ROOT / "mcp-server" / "ipc.py"),
            ("fusion-addin/FusionMCP.py", PROJECT_ROOT / "fusion-addin" / "FusionMCP.py"),
        ],
    ),
    (
        "ADDIN_VERSION",
        [
            ("fusion-addin/FusionMCP.py", PROJECT_ROOT / "fusion-addin" / "FusionMCP.py"),
        ],
    ),
]


def check_skill_mcp_versions(canonical_version: str) -> list[str]:
    """Check that SKILL.md files have mcp_version matching the canonical version."""
    drift: list[str] = []
    for skill_path in SKILL_FILES:
        label = str(skill_path.relative_to(PROJECT_ROOT))
        if not skill_path.exists():
            drift.append(f"  mcp_version in {label}: file not found")
            continue
        text = skill_path.read_text()
        match = re.search(r"^mcp_version:\s*(.+)$", text, re.MULTILINE)
        if not match:
            print(f"  mcp_version in {label}: not found [SKIP]")
            continue
        mcp_ver = match.group(1).strip().strip('"').strip("'")
        status = "OK" if mcp_ver == canonical_version else "DRIFT"
        print(f"  mcp_version in {label}: {mcp_ver} [{status}]")
        if status == "DRIFT":
            drift.append(f"  mcp_version in {label}: {mcp_ver} (expected {canonical_version})")
    return drift


def check_parity(canonical_version: str) -> list[str]:
    """Check cross-runtime constant parity. Returns list of drift messages."""
    drift: list[str] = []
    for const_name, sources in PARITY_CHECKS:
        values: dict[str, str] = {}
        for label, path in sources:
            if not path.exists():
                drift.append(f"  {const_name} in {label}: file not found")
                continue
            val = _extract_python_constant(path, const_name)
            if val is None:
                drift.append(f"  {const_name} in {label}: constant not found")
                continue
            values[label] = val

        if not values:
            continue

        # For ADDIN_VERSION, check against canonical product version
        if const_name == "ADDIN_VERSION":
            for label, val in values.items():
                status = "OK" if val == canonical_version else "DRIFT"
                print(f"  {const_name} in {label}: {val} [{status}]")
                if status == "DRIFT":
                    drift.append(f"  {const_name} in {label}: {val} (expected {canonical_version})")
        else:
            # For other constants, check all sources match each other
            unique = set(values.values())
            if len(unique) > 1:
                for label, val in values.items():
                    drift.append(f"  {const_name} in {label}: {val}")
                    print(f"  {const_name} in {label}: {val} [DRIFT]")
            else:
                for label, val in values.items():
                    print(f"  {const_name} in {label}: {val} [OK]")
    return drift


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

    # Skill file mcp_version checks
    print("\nSkill file mcp_version checks:")
    drift.extend(check_skill_mcp_versions(canonical))

    # Cross-runtime constant parity checks
    print("\nCross-runtime parity checks:")
    drift.extend(check_parity(canonical))

    if drift:
        print(f"\nVersion sync FAILED — {len(drift)} source(s) diverge from {canonical_source} ({canonical}):")
        print("\n".join(drift))
        return 1

    print(f"\nVersion sync OK — all sources match {canonical}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
