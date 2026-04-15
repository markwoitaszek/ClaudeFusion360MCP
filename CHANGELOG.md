# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [7.2.0] - 2026-04-14

### Added

- Typed exception hierarchy (`FusionTimeoutError`, `FusionSessionError`, `FusionIPCError`) replacing bare `Exception` raises
- Ping fast-path with 5-second timeout for quick connectivity probing
- `Makefile` with standard development targets (`run`, `test`, `lint`, `clean`, etc.)
- CLI entry point: `fusion360-mcp` via `pyproject.toml` `[project.scripts]`
- JSON structured logging via `LOG_FORMAT=json` environment variable
- `TokenScrubFilter` to prevent session token leakage in logs
- `get_session_stats()` MCP tool for opaque session telemetry counters
- `plan_design()` offline tool for structured design briefs (no Fusion connection needed)
- `estimate_batch_sequence()` offline tool for operation sequence validation
- Skill tier metadata (`tier: core` / `tier: advanced`) in SKILL.md frontmatter
- Design Intent Clarification Protocol in SKILL.md
- Error Recovery Protocol with typed error codes in SKILL.md
- Golden path workflow documentation with three reference workflows
- Known Issues documentation (`KNOWN_ISSUES.md`)
- SKILL.md `mcp_version` validation in `check_version_sync.py`
- ADR-G002: Skill File Schema Governance
- Skill contribution template (`docs/SKILL_TEMPLATE.md`)

### Changed

- `send_fusion_command()` now accepts `timeout_s` parameter (default 45s, clamped to [1, 60])
- `send_fusion_command()` raises typed exceptions instead of bare `Exception`
- Pre-flight COMM_DIR check before every IPC command for better diagnostics
- CI uses `pip install -e '.[dev]'` instead of separate dep installs
- Coverage threshold raised from 50% to 70%
- `mcp_version` updated from 7.0.0 to 7.2.0 in SKILL.md and SPATIAL_AWARENESS.md
- MCP badge in README updated from 1.0 to 7.2
- `install.py` warns when no virtual environment is detected

### Fixed

- `mcp_version: 7.0.0` drift in SKILL.md (now validated by CI)
- Testing TODO in CLAUDE.md replaced with actual test commands

## [0.1.0] - 2026-04-11

### Added

- Fusion 360 Add-in with file-based IPC communication
- MCP server bridging Claude AI to Fusion 360
- Sketch tools: rectangle, circle, line, arc, polygon
- 3D operations: extrude, revolve, sweep, fillet, chamfer, shell
- Multi-component assembly support with move/rotate
- Export to STL, STEP, and 3MF formats
- Spatial awareness and geometric verification skill
- Comprehensive tool reference documentation
- GitHub Actions CI workflow (template)
- ADR framework with three-layer taxonomy
