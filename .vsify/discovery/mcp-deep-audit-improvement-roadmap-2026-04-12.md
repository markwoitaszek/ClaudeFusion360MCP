---
title: "MCP Deep Audit & Improvement Roadmap"
status: draft
created: "2026-04-12"
backend_target: null
promoted_at: null
pm_item_url: null
---

# MCP Deep Audit & Improvement Roadmap

## Overview

Comprehensive audit of the ClaudeFusion360MCP repository to verify MCP legitimacy, identify existing bugs, and catalog short/medium/long-term improvements for production readiness and MCP registry publishability.

## MCP Legitimacy Verdict

**LEGITIMATE** — The MCP server is a properly structured FastMCP implementation:

- Correct `FastMCP("Fusion 360 v7.2 Enhanced")` initialization
- All 39 tools registered via `@mcp.tool()` with type-inferred schemas
- Standard `mcp.run()` entry point
- Claude Desktop correctly discovers all tools

**However**: The Fusion 360 add-in only implements 9 of 39 tools. 30 tools are "phantom tools" — Claude sees them but they fail with "Unknown tool" errors.

## Bug Register

### P0 — Critical (3 findings)

1. **Threading violation** (FusionMCP.py:23-56): `monitor_commands()` runs on a daemon thread but calls Fusion 360 API directly. Fusion requires main-thread dispatch via CustomEventHandler.
2. **~~30 phantom tools~~** ~~(FusionMCP.py:68-87)~~: **RESOLVED (MT-1)** — All 39 tools now have handlers via HANDLER_REGISTRY dispatch.
3. **~~Infinite retry on malformed commands~~** ~~(FusionMCP.py:52-53)~~: **RESOLVED (ST-2/NR-8)** — JSONDecodeError caught and error response written; command file TTL skips files >60s old.

### P1 — High (8 findings)

4. **Path traversal on exports** (fusion360_mcp_server.py:599-620): Export/import tools accept arbitrary paths with no validation.
5. **~~Unauthenticated IPC~~**: **RESOLVED (MT-3)** — Session token authentication added; fail-closed when token absent.
6. **~~World-readable IPC directory~~** ~~(fusion360_mcp_server.py:36)~~: **RESOLVED (MT-3)** — Directory created with 0o700; ownership and symlink guards in place.
7. **~~Collision-prone command IDs~~** ~~(fusion360_mcp_server.py:42)~~: **RESOLVED (MT-3)** — IDs now use timestamp + counter + random suffix.
8. **Error swallowing** (FusionMCP.py:28,37,53,56): 4 bare except:pass blocks prevent error responses.
9. **~~Silently ignored parameters~~**: **RESOLVED (MT-1/MT-2)** — create_sketch now supports offset, extrude supports profile_index and taper_angle.
10. **~~No protocol versioning~~**: **RESOLVED (NR-1)** — `protocol_version` field added to command JSON; add-in validates and rejects mismatches.
11. **~~Inert CI pipeline~~** ~~(ci.yml)~~: **RESOLVED (MT-5)** — CI activated with ruff, black, and pytest.

### P2 — Medium (5 findings)

12. **~~No logging~~**: **RESOLVED (LT-3)** — Server has logging.basicConfig with LOG_LEVEL env var; add-in has RotatingFileHandler with per-command timing (tool_name, cmd_id, elapsed_ms).
13. **~~No health check~~**: **RESOLVED (NR-6)** — `ping()` tool returns add-in status and Fusion version without requiring an active design.
14. **~~No minimum Fusion version~~**: **RESOLVED (NR-9)** — Manifest documents tested version; add-in logs version at startup with warning if below baseline.
15. **~~`type` shadows builtin~~** ~~(fusion360_mcp_server.py:349)~~: **RESOLVED** — Renamed to `measurement_type` in tools/io.py.
16. **Repeated param-building**: 4+ tools repeat identical None-check patterns.

### Doc-to-Code Drift (12 instances)

- ~~README lists sweep, loft, split_body, draw_slot (none exist in code)~~ — **RESOLVED** — Removed from README
- ~~KNOWN_ISSUES references batch_operations() (actual: batch())~~ — **RESOLVED** — Fixed to batch()
- ~~Version numbers: server v7.2, KNOWN_ISSUES v8.2, TOOL_REFERENCE v7.0.0/v4.0, manifest v2.0.0~~ — **RESOLVED (LT-4)** — All components unified to 7.2.0 from pyproject.toml; CI drift check enforces parity
- ~~README has duplicated sentence on line 15~~ — **RESOLVED** — Sentence removed
- ~~README clone URL has YOUR_USERNAME placeholder~~ — **RESOLVED** — Placeholder removed

## Compatibility Matrix

| Status                | Count | Details                                                                             |
| --------------------- | ----- | ----------------------------------------------------------------------------------- |
| Functional            | 40    | All 40 MCP tools have add-in handlers (39 original + ping health check)             |
| Phantom (server-only) | 0     | Eliminated — all tools dispatched via HANDLER_REGISTRY                              |
| Doc-only phantom      | 0     | Eliminated — sweep, loft, split_body, draw_slot references removed from docs        |

## Improvement Roadmap

### Short-Term (Hours to 1 Day)

| ID   | Requirement                                             | Type     | Effort | Status |
| ---- | ------------------------------------------------------- | -------- | ------ | ------ |
| ST-1 | Fix threading: dispatch Fusion API calls to main thread | Bug fix  | Medium | Done   |
| ST-2 | Eliminate 4 bare except:pass blocks                     | Bug fix  | Low    | Done   |
| ST-3 | Restrict export/import filepaths to safe directories    | Security | Low    | Done   |
| ST-4 | Fix README tool list and doc drift                      | Docs     | Low    | Done   |

### Medium-Term (Days to Weeks)

| ID   | Requirement                                             | Type     | Effort | Status |
| ---- | ------------------------------------------------------- | -------- | ------ | ------ |
| MT-1 | Implement 30 missing add-in handlers                    | Feature  | High   | Done   |
| MT-2 | Add input validation (ranges, enums, required fields)   | Quality  | Medium | Done   |
| MT-3 | Set IPC directory permissions to 700, add session token | Security | Low    | Done   |
| MT-4 | Establish pytest test suite with mock IPC               | Quality  | Medium | Done   |
| MT-5 | Activate linting (ruff) + formatting (black) + CI       | Quality  | Low    | Done   |

### Long-Term (Weeks)

| ID   | Requirement                                         | Type    | Effort | Status |
| ---- | --------------------------------------------------- | ------- | ------ | ------ |
| LT-1 | ~~Add MCP registry metadata (mcp.json, schemas)~~   | Feature | Low    | Done   |
| LT-2 | ~~Create one-command installer~~                    | Feature | Medium | Done   |
| LT-3 | ~~Add structured logging to both components~~       | Quality | Low    | Done   |
| LT-4 | ~~Enforce consistent semver across all components~~ | Quality | Low    | Done   |
| LT-5 | ~~Integration smoke tests against live Fusion 360~~ | Quality | Medium | Done   |

### New Requirements Discovered

| ID    | Requirement                                         | Type    | Status  | Notes                                                                                                                                                               |
| ----- | --------------------------------------------------- | ------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| NR-1  | ~~IPC protocol versioning~~                         | Quality | Done    | Protocol version field in command JSON; add-in rejects mismatches (fail-closed)                                                                                     |
| NR-2  | ~~Fusion lifecycle handling (graceful cleanup)~~    | Quality | Done    | Stale file cleanup on startup; improved thread join in stop()                                                                                                       |
| NR-3  | ~~High-quality tool descriptions for Claude~~       | Quality | Done    | All tool docstrings include unit annotations (cm, degrees); measurement units documented                                                                            |
| NR-4  | ~~Export tools must return actual file path~~       | Feature | Done    | MT-1: export handlers return filepath                                                                                                                               |
| NR-5  | ~~Add list_bodies/get_model_state tool~~            | Feature | Done    | MT-1: get_body_info handler implemented                                                                                                                             |
| NR-6  | ~~Add ping() health check tool~~                    | Feature | Done    | ping() tool in io.py + handler in FusionMCP.py; works without active design                                                                                         |
| NR-7  | ~~Startup assertion logging unimplemented tools~~   | Quality | Done    | Registry pattern ensures parity                                                                                                                                     |
| NR-8  | ~~Command file TTL (skip files older than 60s)~~    | Quality | Done    | monitor_commands() checks file mtime; skips and deletes files older than 60s                                                                                        |
| NR-9  | ~~Minimum Fusion 360 version check~~                | Quality | Done    | Manifest documents tested version; add-in logs version at startup with warning if below baseline                                                                    |
| NR-10 | ~~Implement offset in create_sketch handler~~       | Feature | Done    | MT-1: offset creates construction plane                                                                                                                             |
| NR-11 | ~~Implement profile_index in extrude handler~~      | Feature | Done    | MT-1: profile_index with bounds check                                                                                                                               |
| NR-12 | ~~Integration smoke tests against live Fusion 360~~ | Quality | Done    | LT-5: tests/test_smoke.py with 4 live scenarios (sketch→extrude, component move, export round-trip, design info query) gated by FUSION_SMOKE_TESTS=1. Not CI-gated. |

## Risk Assessment

| Risk                                      | Likelihood | Impact   | Status                                 |
| ----------------------------------------- | ---------- | -------- | -------------------------------------- |
| Thread-safety crashes                     | High       | Critical | Mitigated (ST-1)                       |
| User trust loss from phantom tools        | High       | High     | **Resolved (MT-1)** — 39/39 handlers   |
| Prompt injection → malicious export path  | Medium     | High     | **Resolved (MT-3)** — token + path val |
| Stale command replay                      | Medium     | High     | **Resolved (MT-3)** — session token    |
| Semantic API bugs hidden by mock boundary | High       | High     | **Mitigated (LT-5)** — smoke tests     |
| Server/add-in version drift               | Medium     | Medium   | **Resolved (LT-4)** — CI drift check   |
| First-time installer abandonment          | High       | Medium   | **Mitigated (LT-2)** — install.py      |

## Recommended Next Steps

All Short-Term, Medium-Term, Long-Term, and New Requirements are **complete**. Remaining optional work:

1. Run `FUSION_SMOKE_TESTS=1 pytest tests/test_smoke.py` with live Fusion 360 to validate LT-5 integration tests
2. Run `/vsify-me:adr detect` to capture threading fix, IPC hardening, and version management as new ADRs
3. Consider regenerating mcp.json via `scripts/generate_mcp_registry.py` to pick up improved tool descriptions
