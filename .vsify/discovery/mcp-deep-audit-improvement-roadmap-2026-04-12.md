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
2. **30 phantom tools** (FusionMCP.py:68-87): MCP server registers 39 tools, add-in handles 9. Claude attempts tools that can't work.
3. **Infinite retry on malformed commands** (FusionMCP.py:52-53): Bare `except: pass` means bad command files are re-read every 100ms forever.

### P1 — High (8 findings)

4. **Path traversal on exports** (fusion360_mcp_server.py:599-620): Export/import tools accept arbitrary paths with no validation.
5. **Unauthenticated IPC**: Any local process can inject commands into ~/fusion_mcp_comm/.
6. **World-readable IPC directory** (fusion360_mcp_server.py:36): COMM_DIR created with default umask.
7. **Collision-prone command IDs** (fusion360_mcp_server.py:42): Millisecond timestamps can collide.
8. **Error swallowing** (FusionMCP.py:28,37,53,56): 4 bare except:pass blocks prevent error responses.
9. **Silently ignored parameters**: create_sketch ignores offset, extrude ignores profile_index and taper_angle.
10. **No protocol versioning**: No version field in IPC JSON.
11. **Inert CI pipeline** (ci.yml): All steps commented out.

### P2 — Medium (5 findings)

12. **No logging**: Neither component logs anything.
13. **No health check**: No way to verify add-in is running.
14. **No minimum Fusion version**: Manifest missing minimumVersion.
15. **`type` shadows builtin** (fusion360_mcp_server.py:349): measure(type: str) shadows Python builtin.
16. **Repeated param-building**: 4+ tools repeat identical None-check patterns.

### Doc-to-Code Drift (12 instances)

- README lists sweep, loft, split_body, draw_slot (none exist in code)
- KNOWN_ISSUES references batch_operations() (actual: batch())
- Version numbers: server v7.2, KNOWN_ISSUES v8.2, TOOL_REFERENCE v7.0.0/v4.0, manifest v2.0.0
- README has duplicated sentence on line 15
- README clone URL has YOUR_USERNAME placeholder

## Compatibility Matrix

| Status                | Count | Details                                                                                                        |
| --------------------- | ----- | -------------------------------------------------------------------------------------------------------------- |
| Functional            | 9     | create_sketch, finish_sketch, draw_rectangle, draw_circle, extrude, revolve, fillet, fit_view, get_design_info |
| Phantom (server-only) | 30    | All other tools — registered in MCP server, missing from add-in                                                |
| Doc-only phantom      | 4     | sweep, loft, split_body, draw_slot — not even in server code                                                   |

## Improvement Roadmap

### Short-Term (Hours to 1 Day)

| ID   | Requirement                                             | Type     | Effort |
| ---- | ------------------------------------------------------- | -------- | ------ |
| ST-1 | Fix threading: dispatch Fusion API calls to main thread | Bug fix  | Medium |
| ST-2 | Eliminate 4 bare except:pass blocks                     | Bug fix  | Low    |
| ST-3 | Restrict export/import filepaths to safe directories    | Security | Low    |
| ST-4 | Fix README tool list and doc drift                      | Docs     | Low    |

### Medium-Term (Days to Weeks)

| ID   | Requirement                                             | Type     | Effort |
| ---- | ------------------------------------------------------- | -------- | ------ |
| MT-1 | Implement 30 missing add-in handlers                    | Feature  | High   |
| MT-2 | Add input validation (ranges, enums, required fields)   | Quality  | Medium |
| MT-3 | Set IPC directory permissions to 700, add session token | Security | Low    |
| MT-4 | Establish pytest test suite with mock IPC               | Quality  | Medium |
| MT-5 | Activate linting (ruff) + formatting (black) + CI       | Quality  | Low    |

### Long-Term (Weeks)

| ID   | Requirement                                     | Type    | Effort |
| ---- | ----------------------------------------------- | ------- | ------ |
| LT-1 | Add MCP registry metadata (mcp.json, schemas)   | Feature | Low    |
| LT-2 | Create one-command installer                    | Feature | Medium |
| LT-3 | Add structured logging to both components       | Quality | Low    |
| LT-4 | Enforce consistent semver across all components | Quality | Low    |

### New Requirements Discovered

- NR-1: IPC protocol versioning
- NR-2: Fusion lifecycle handling (graceful cleanup)
- NR-3: High-quality tool descriptions for Claude's tool selection
- NR-4: Export tools must return actual file path written
- NR-5: Add list_bodies/get_model_state tool
- NR-6: Add ping() health check tool
- NR-7: Startup assertion logging unimplemented tools
- NR-8: Command file TTL (skip files older than 60s)
- NR-9: Minimum Fusion 360 version check
- NR-10: Implement offset in create_sketch handler
- NR-11: Implement profile_index in extrude handler

## Risk Assessment

| Risk                                     | Likelihood | Impact   |
| ---------------------------------------- | ---------- | -------- |
| Thread-safety crashes                    | High       | Critical |
| User trust loss from phantom tools       | High       | High     |
| Prompt injection → malicious export path | Medium     | High     |
| Stale command replay                     | Medium     | High     |
| Server/add-in version drift              | Medium     | Medium   |
| First-time installer abandonment         | High       | Medium   |

## Recommended Next Steps

1. Run `/vsify-me:feature-design` with ST-1 through ST-4 to implement critical fixes
2. Use Context7 MCP (/ipendle/autodesk-fusion-api-documentation) for MT-1 implementation reference
3. Run `/vsify-me:adr detect` to capture threading fix and IPC hardening as new ADRs
4. Run `/vsify-me:ux-design` if a configuration UI is planned for export path allowlisting
