#!/usr/bin/env python3
"""Validate skill file frontmatter against the canonical schema (ADR-G002).

Checks all .md files in the given directory for:
  1. Valid YAML frontmatter presence
  2. Required fields present and non-empty
  3. mcp_version matches the canonical VERSION file
  4. tier is one of the valid tier names

Usage:
    python scripts/validate_skills.py docs/
    python scripts/validate_skills.py docs/ --check-version  # Also validate mcp_version
"""
import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FIELDS = ["name", "description", "version", "model_target", "mcp_version", "tier"]
VALID_TIERS = {"core", "advanced", "specialist"}


def _parse_frontmatter(text: str) -> dict | None:
    """Parse YAML frontmatter from a markdown file.

    Returns a dict of key-value pairs, or None if no frontmatter found.
    Uses simple regex parsing to avoid PyYAML dependency.
    """
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    fields = {}
    for line in match.group(1).split("\n"):
        kv = re.match(r"^(\w[\w_]*)\s*:\s*(.+)$", line.strip())
        if kv:
            fields[kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
    return fields


def _read_canonical_version() -> str:
    """Read canonical version from VERSION file."""
    version_path = PROJECT_ROOT / "VERSION"
    if not version_path.exists():
        return ""
    return version_path.read_text().strip()


def validate_skill(path: Path, check_version: bool = False) -> list[str]:
    """Validate a single skill file. Returns list of error messages."""
    errors = []
    text = path.read_text()
    fields = _parse_frontmatter(text)

    if fields is None:
        # Not a skill file (no frontmatter) — skip silently
        return []

    # Only validate files that have mcp_version (distinguishes skills from other docs)
    if "mcp_version" not in fields:
        return []

    label = str(path.relative_to(PROJECT_ROOT)) if path.is_relative_to(PROJECT_ROOT) else str(path)

    for field in REQUIRED_FIELDS:
        if field not in fields:
            errors.append(f"  {label}: missing required field '{field}'")
        elif not fields[field]:
            errors.append(f"  {label}: field '{field}' is empty")

    if "tier" in fields and fields["tier"] not in VALID_TIERS:
        errors.append(f"  {label}: invalid tier '{fields['tier']}'. Must be one of: {', '.join(sorted(VALID_TIERS))}")

    if check_version and "mcp_version" in fields:
        canonical = _read_canonical_version()
        if canonical and fields["mcp_version"] != canonical:
            errors.append(
                f"  {label}: mcp_version '{fields['mcp_version']}' " f"does not match VERSION file '{canonical}'"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate skill file frontmatter (ADR-G002)")
    parser.add_argument("directory", help="Directory to scan for skill files")
    parser.add_argument("--check-version", action="store_true", help="Also validate mcp_version against VERSION file")
    args = parser.parse_args()

    docs_dir = Path(args.directory)
    if not docs_dir.is_dir():
        print(f"Error: {docs_dir} is not a directory")
        return 1

    all_errors = []
    skill_count = 0

    for md_file in sorted(docs_dir.glob("**/*.md")):
        errors = validate_skill(md_file, check_version=args.check_version)
        if errors:
            all_errors.extend(errors)
        # Count files that have mcp_version (i.e., are skill files)
        text = md_file.read_text()
        fields = _parse_frontmatter(text)
        if fields and "mcp_version" in fields:
            skill_count += 1

    if all_errors:
        print(f"Skill validation FAILED — {len(all_errors)} error(s) in {skill_count} skill file(s):")
        print("\n".join(all_errors))
        return 1

    print(f"Skill validation OK — {skill_count} skill file(s) validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
