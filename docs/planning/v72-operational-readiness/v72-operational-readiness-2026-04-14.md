---
title: "v7.2 Operational Readiness — Tooling, Skills, Documentation, and Developer Experience"
status: implemented
created: "2026-04-14"
implemented_at: "2026-04-14"
backend_target: "github"
promoted_at: null
pm_item_url: "https://github.com/markwoitaszek/ClaudeFusion360MCP/pull/33"
---

# v7.2 Operational Readiness — Optimized Requirements

## Overview

Comprehensive analysis of ClaudeFusion360MCP's readiness for real-world end-to-end usage, covering functional testing validation, documentation completeness, developer tooling, and a tiered MCP skill architecture for AI-guided 3D design.

## Core Goal

Prepare ClaudeFusion360MCP v7.2 for real-world usage through: typed error handling, developer tooling (Makefile + CLI), tiered skill architecture, guided design behavior, golden path workflows, offline design brief mode, and structured telemetry.

## Requirements (Priority Order)

### P0 — Ship Blockers

**REQ-P0-1: Typed Exception Hierarchy** ✅ COMPLETE (PR #33)
- Create `mcp-server/errors.py` with `FusionTimeoutError`, `FusionSessionError`, `FusionIPCError`
- Each exception carries `error_code: str`, `tool_name: str`, and `remediation: str` fields
- Replace bare `Exception(...)` in `ipc.py` lines 121 and 127 with typed raises
- Sanitize exception messages — strip `__cause__` before MCP serialization to prevent internal handler names leaking
- Add `error_code` field to IPC response JSON schema for typed error propagation from add-in

**REQ-P0-2: Ping Fast-Path (5s Timeout)** ✅ COMPLETE (PR #33)
- Add `timeout_s: float = 45.0` parameter to `send_fusion_command()` in `ipc.py`
- Clamp: `timeout_s = max(1.0, min(timeout_s, 60.0))` to prevent zero/negative/extreme values
- Compute poll iterations: `int(timeout_s / 0.05)`
- Update `ping()` in `tools/io.py` to pass `timeout_s=5.0`
- Hardcode the 5s value in `ping()` — do not expose as a tool parameter

### P1 — Core Readiness

**REQ-P1-1: Makefile + CLI Entry Point** ✅ COMPLETE (PR #33)
- Create `Makefile` at project root with 7 targets: `run`, `test`, `lint`, `validate-skills`, `generate-registry`, `check-version`, `clean`
- Add `[project.scripts]` to `pyproject.toml`: `fusion360-mcp = "fusion360_mcp_server:main"`
- Extract `main()` function in `fusion360_mcp_server.py` from `__main__` guard
- CI jobs should invoke Makefile targets to eliminate drift between CI and local dev

**REQ-P1-2: JSON Telemetry + Session Stats** ✅ COMPLETE (PR #33)
- Add `JsonFormatter` class gated on `LOG_FORMAT=json` env var (validate against `{text, json}` set)
- Existing log call sites unchanged — only formatter changes
- Add `logging.Filter` that blocks records containing `session_token` keyword (token scrubbing)
- Add module-level `_stats: dict` in `ipc.py` tracking `commands_sent`, `commands_timed_out`, `last_error`, `last_tool`
- Add `get_session_stats()` MCP tool in `tools/io.py` — offline-safe, returns only opaque counters (explicitly excludes session token)

**REQ-P1-3: VERSION as Single Source of Truth** ✅ COMPLETE (PR #33)
- Switch `pyproject.toml` to `dynamic = ["version"]` with `[tool.setuptools.dynamic] version = {file = "VERSION"}`
- Remove hardcoded `version = "7.2.0"` from pyproject.toml
- Extend `check_version_sync.py` to check `mcp_version` in SKILL.md frontmatter against VERSION

**REQ-P1-4: CI Hardening** ✅ COMPLETE (PR #33)
- Use `pip install -e '.[dev]'` in all CI jobs (lint and test) for consistent installs
- `install.py` should detect missing venv (`sys.prefix != sys.base_prefix`) and warn

### P2 — Quality and Documentation

**REQ-P2-1: Design Brief Mode (Offline Planning)** ✅ COMPLETE (PR #33)
- Create `mcp-server/tools/planning.py` as new FastMCP router
- Tool 1: `plan_design(description: str, manufacturing_process: str) -> dict` — returns suggested operations, dimensions, coordinate notes, warnings
- Tool 2: `estimate_batch_sequence(operations: list) -> dict` — validates proposed batch sequence offline
- Both return `{"success": true, "offline": true, "result": {...}}`
- Both must import and call validators from `validation.py` on all inputs (offline tools must not bypass validation boundary)
- Add `# offline_safe` docstring tag; update `generate_mcp_registry.py` to detect and emit `"offline_safe": true` in mcp.json
- Register via `mcp.include_router(planning_router)` in server entry point

**REQ-P2-2: Skill Tier Metadata + Version Fix** ✅ COMPLETE (PR #33)
- Add `tier: core` to SKILL.md frontmatter
- Add `tier: advanced` to SPATIAL_AWARENESS.md frontmatter
- Fix SKILL.md `mcp_version: 7.0.0` to `7.2.0`
- Fix SPATIAL_AWARENESS.md `companion_skills` reference to correct filename
- Define three tiers: `core` (required for any session), `advanced` (complex work), `specialist` (future domain skills)
- Add "Skill Loading Guide" table to README.md

**REQ-P2-3: Golden Path Workflows** ✅ COMPLETE (PR #33)
- Create `docs/golden-paths.md` with 3 workflows: (1) extruded box, (2) revolved body (demonstrating Z-negation), (3) two-component assembly
- Create `tests/test_golden_paths.py` with 3 `@pytest.mark.integration` tests
- Tests must call tool functions (not `send_fusion_command` directly) to exercise full validation stack
- Each workflow includes exact batch() command sequence and verification steps

**REQ-P2-4: Guided Design Protocol in SKILL.md** ✅ COMPLETE (PR #33)
- Add "Design Intent Clarification Protocol" section following existing ASK USER/STOP AND VERIFY patterns
- Three ambiguity categories: underspecified geometry, missing manufacturing intent, missing assembly context
- Brief-mode override: "just build it" / "brief mode:" trigger phrase skips questions
- Define skip conditions: if prompt contains explicit dimensions AND material intent, proceed without questions

**REQ-P2-5: Graceful Degradation** ✅ COMPLETE (PR #33)
- Pre-flight check in `send_fusion_command()`: if COMM_DIR does not exist, raise `FusionIPCError` immediately
- Enrich timeout error message with 3 diagnostic hints (add-in panel check, session token file check, stuck queue check)
- Add "Error Recovery Protocol" section to SKILL.md mapping error codes to Claude responses
- Document add-in restart recovery sequence in SKILL.md

**REQ-P2-6: Documentation Fixes** ✅ COMPLETE (PR #33)
- Fix CLAUDE.md "TODO: Add test framework" to document actual test commands
- Document session token race condition in KNOWN_ISSUES.md
- Fix broken image references in README (if images do not exist, remove references)
- Update CHANGELOG.md to reflect v7.2.0 changes

### P3 — Governance

**REQ-P3-1: Skill Contribution Template + Validator** ✅ COMPLETE (PR #33)
- Create `docs/SKILL_TEMPLATE.md` with all required frontmatter fields and section stubs
- Create `scripts/validate_skills.py` following `check_version_sync.py` pattern
- Validates: required frontmatter fields, `mcp_version` matches VERSION, `tier` is recognized value
- Must never eval or exec content from docs (static pattern matching only)
- Create ADR-G002 documenting canonical skill frontmatter schema

## Implementation Order (Dependency Graph)

```
REQ-P0-1 (errors.py)
REQ-P0-2 (ping timeout)
  |
  +-- REQ-P2-5 (graceful degradation uses errors.py)
  +-- REQ-P2-1 (planning.py uses errors.py)
  |
REQ-P1-3 (VERSION SSOT)
REQ-P1-4 (CI hardening)
  |
REQ-P1-1 (Makefile + CLI)
  +-- REQ-P2-3 (make smoke-test wraps golden paths)
  |
REQ-P1-2 (telemetry)
  |
REQ-P2-2 (tier metadata) -- REQ-P3-1 (validator validates tiers)
REQ-P2-4 (guided design) -- independent
REQ-P2-6 (doc fixes) -- independent
```

## Scope Boundaries

### In Scope
- Typed exceptions, ping fast-path, Makefile, CLI, telemetry, VERSION SSOT
- Offline planning tools, skill tier metadata, golden path docs+tests
- Guided design protocol, graceful degradation, doc fixes
- Skill template + validator + ADR-G002

### Out of Scope (Deferred)
- Parametric constraint solver (v2 — requires Fusion Parameters API research)
- Split SKILL.md into separate tier files (breaking change to Claude Desktop config)
- MCP Resource delivery of skills (needs ADR-G003 before implementation)
- GUI telemetry dashboard (CLI summary is sufficient for v1)
- Automated live Fusion CI tests (requires macOS runner with Fusion license)
- Skill marketplace/registry
- Multi-language skill files

## Success Metrics

| Metric | Target |
|--------|--------|
| Installation success rate | >90% on first attempt |
| First-attempt geometry correctness | >80% with guided design |
| Test coverage | 70%+ (up from 50% floor) |
| Contributor onboarding | Valid skill PR within 1 hour |
| Timeout error reports | Zero unexplained timeouts |

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Session token collision (multi-process) | Medium | High | Document single-process constraint; add lock file |
| Offline tools bypass validation boundary | Medium | High | Import same validators; add offline_safe checklist |
| JSON telemetry leaks token | Medium | Medium | Log-scrubbing filter blocking session_token |
| SKILL.md version drift invisible | High | Medium | Add frontmatter check to check_version_sync.py |
| Guided design over-asks expert users | Medium | Medium | Brief-mode override + skip conditions |
| install.py into system Python | Medium | Medium | Venv detection warning + documented sequence |
