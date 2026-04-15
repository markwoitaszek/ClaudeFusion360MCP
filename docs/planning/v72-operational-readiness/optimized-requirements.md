---
title: "v7.2 Operational Readiness — Optimized Requirements"
document_type: requirements
created: "2026-04-14"
status: implemented
implemented_at: "2026-04-14"
implemented_pr: "https://github.com/markwoitaszek/ClaudeFusion360MCP/pull/33"
related:
  - discovery: "./v72-operational-readiness-2026-04-14.md"
  - architecture_constraints: "./architecture-constraints.md"
  - enterprise_review: "./enterprise-review.md"
  - decision_rationale: "./decision-rationale.md"
---

# v7.2 Operational Readiness — Optimized Requirements

## Summary

16 requirements across 4 priority tiers, addressing typed error handling, developer tooling, tiered skills, guided design, offline planning, telemetry, and documentation. Produced via 5-phase ideation analysis with 15 parallel agents across architecture audit, requirements optimization, and enterprise review.

**Status: All 13 requirements implemented in PR #33 (2026-04-14).** 190 tests passing, lint clean, all ADR constraints satisfied.

## P0 — Ship Blockers (2 requirements)

### REQ-P0-1: Typed Exception Hierarchy

**Files**: `mcp-server/errors.py` (new), `mcp-server/ipc.py` (modify)

Create three typed exception classes replacing bare `Exception(...)`:

| Exception | Error Code | Trigger |
|-----------|------------|---------|
| `FusionTimeoutError` | `F360_TIMEOUT` | 45s elapsed, no Fusion response |
| `FusionSessionError` | `F360_SESSION_INVALID` | Token mismatch with add-in |
| `FusionIPCError` | `F360_IPC_ERROR` | COMM_DIR missing, malformed response |

Each carries: `error_code: str`, `tool_name: str`, `remediation: str`.

Security constraint: Sanitize exception messages before MCP serialization. Strip `__cause__` chain to prevent internal handler names from leaking to the LLM.

### REQ-P0-2: Ping Fast-Path (5s Timeout)

**Files**: `mcp-server/ipc.py` (modify), `mcp-server/tools/io.py` (modify)

- Add `timeout_s: float = 45.0` parameter to `send_fusion_command()`
- Clamp: `timeout_s = max(1.0, min(timeout_s, 60.0))`
- `ping()` hardcodes `timeout_s=5.0` — not exposed as a tool parameter
- Enables fast connectivity probing without 45s wall-clock wait

## P1 — Core Readiness (4 requirements)

### REQ-P1-1: Makefile + CLI Entry Point

**Files**: `Makefile` (new), `pyproject.toml` (modify), `mcp-server/fusion360_mcp_server.py` (modify)

Makefile targets:

| Target | Command |
|--------|---------|
| `make run` | `LOG_LEVEL=DEBUG python mcp-server/fusion360_mcp_server.py` |
| `make test` | `python -m pytest tests/ -v --cov=mcp-server --cov-fail-under=70` |
| `make lint` | `ruff check . && black --check .` |
| `make validate-skills` | `python scripts/validate_skills.py docs/` |
| `make generate-registry` | `python scripts/generate_mcp_registry.py` |
| `make check-version` | `python scripts/check_version_sync.py` |
| `make clean` | Remove `__pycache__`, `.pytest_cache`, stale IPC files |

CLI entry point: `fusion360-mcp = "fusion360_mcp_server:main"` via `[project.scripts]`.

### REQ-P1-2: JSON Telemetry + Session Stats

**Files**: `mcp-server/fusion360_mcp_server.py` (modify), `mcp-server/ipc.py` (modify), `mcp-server/tools/io.py` (modify)

- `JsonFormatter` class gated on `LOG_FORMAT=json` env var
- `logging.Filter` blocking records containing `session_token` (token scrubbing)
- Module-level `_stats` dict in `ipc.py`: `commands_sent`, `commands_timed_out`, `last_error`, `last_tool`
- `get_session_stats()` MCP tool — offline-safe, returns only opaque counters

Security constraint: `get_session_stats` must explicitly exclude session token, its hex length, and any derivation.

### REQ-P1-3: VERSION as Single Source of Truth

**Files**: `pyproject.toml` (modify), `scripts/check_version_sync.py` (modify)

- `dynamic = ["version"]` with `[tool.setuptools.dynamic] version = {file = "VERSION"}`
- Extend `check_version_sync.py` to validate SKILL.md `mcp_version` against VERSION

### REQ-P1-4: CI Hardening

**Files**: `.github/workflows/ci.yml` (modify), `scripts/install.py` (modify)

- All CI jobs use `pip install -e '.[dev]'`
- `install.py` warns when no venv detected

## P2 — Quality and Documentation (6 requirements)

### REQ-P2-1: Design Brief Mode (Offline Planning)

**Files**: `mcp-server/tools/planning.py` (new), `mcp-server/fusion360_mcp_server.py` (modify), `scripts/generate_mcp_registry.py` (modify)

Two offline-safe tools:
- `plan_design(description, manufacturing_process)` — structured design brief
- `estimate_batch_sequence(operations)` — offline batch validation

Security constraint: Import validators from `validation.py` on all inputs. Offline does not mean unvalidated.

### REQ-P2-2: Skill Tier Metadata + Version Fix

**Files**: `docs/SKILL.md` (modify), `docs/SPATIAL_AWARENESS.md` (modify), `README.md` (modify)

- Add `tier: core` / `tier: advanced` to frontmatter
- Fix `mcp_version: 7.0.0` to `7.2.0`
- Three tiers: core, advanced, specialist (specialist reserved for future domain skills)

### REQ-P2-3: Golden Path Workflows

**Files**: `docs/golden-paths.md` (new), `tests/test_golden_paths.py` (new)

Three workflows: extruded box, revolved body (Z-negation), two-component assembly. Tests call tool functions (not `send_fusion_command` directly) to exercise full validation.

### REQ-P2-4: Guided Design Protocol

**Files**: `docs/SKILL.md` (modify)

"Design Intent Clarification Protocol" section with three ambiguity categories and brief-mode override.

### REQ-P2-5: Graceful Degradation

**Files**: `mcp-server/ipc.py` (modify), `docs/SKILL.md` (modify)

Pre-flight COMM_DIR check, enriched timeout diagnostics, Error Recovery Protocol section in SKILL.md.

### REQ-P2-6: Documentation Fixes

**Files**: `CLAUDE.md`, `KNOWN_ISSUES.md`, `README.md`, `CHANGELOG.md`

Fix stale testing TODO, document token race condition, fix broken image refs, update changelog.

## P3 — Governance (1 requirement)

### REQ-P3-1: Skill Contribution Template + Validator

**Files**: `docs/SKILL_TEMPLATE.md` (new), `scripts/validate_skills.py` (new), `docs/architecture/decisions/governance/ADR-G002-skill-file-schema-governance.md` (new)

Template + validator + ADR for canonical skill frontmatter schema.
