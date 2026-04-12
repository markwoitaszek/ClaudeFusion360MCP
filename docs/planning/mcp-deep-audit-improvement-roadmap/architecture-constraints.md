---
title: "MCP Deep Audit — Architecture Constraints"
document_type: architecture_constraints
created: "2026-04-12"
primary_doc: ".vsify/discovery/mcp-deep-audit-improvement-roadmap-2026-04-12.md"
---

# Architecture Constraints

## Fit Assessment

**Overall Fit: Medium** — The project is a legitimate MCP server with sound architectural decisions documented in ADRs, but the implementation has significant gaps between what's advertised and what actually works.

## ADR Constraint Table

### MUST (6 constraints)

| # | Constraint | Confidence | Source | Pattern |
|---|-----------|------------|--------|---------|
| 1 | All MCP dimensions must be in centimeters | **HIGH** | ADR-D003 | formal_rfc |
| 2 | Sketch coordinates mapping to World Z must be negated on XZ/YZ planes | **HIGH** | ADR-D004 | formal_rfc |
| 3 | After geometry-modifying operations, face/edge indices must be re-queried | **HIGH** | ADR-G001 | formal_rfc |
| 4 | Bodies must not be auto-joined without explicit verification | **HIGH** | ADR-G001 | formal_rfc |
| 5 | IPC uses timestamped JSON files in ~/fusion_mcp_comm/ | **HIGH** | ADR-D002 | formal_rfc |
| 6 | Each MCP tool dispatches through send_fusion_command() | **HIGH** | ADR-P001 | formal_rfc |

### SHOULD (4 constraints)

| # | Constraint | Confidence | Source | Pattern |
|---|-----------|------------|--------|---------|
| 7 | Use batch operations for multi-step workflows (5-10x faster) | MEDIUM | ADR-D002 | nat_lang |
| 8 | Dimensions > 50cm should be flagged as potential mm confusion | MEDIUM | ADR-G001 | nat_lang |
| 9 | Named component references preferred over positional indices | MEDIUM | ADR-G001 | nat_lang |
| 10 | Test sketches should be created to verify orientation when in doubt | MEDIUM | ADR-G001 | nat_lang |

### MUST NOT (3 constraints)

| # | Constraint | Confidence | Source | Pattern |
|---|-----------|------------|--------|---------|
| 11 | Must NOT reference cached face/edge indices after geometry modification | **HIGH** | ADR-G001 | formal_rfc |
| 12 | Must NOT assume auto-join behavior | **HIGH** | ADR-G001 | formal_rfc |
| 13 | Must NOT pass dimensions without verifying centimeter units | **HIGH** | ADR-G001 | formal_rfc |

> 13 constraints from 6 sources | Patterns: formal_rfc, nat_lang | Confidence filter: none (0 filtered) | methodology: ADR framework

## Conflict Analysis

### Constraint vs Implementation Conflicts

1. **ADR-D002 states 100ms add-in polling** but code uses `time.sleep(0.1)` on the polling thread which calls Fusion API directly — the polling thread violates Fusion's single-threaded API requirement.

2. **ADR-P001 states each tool dispatches through send_fusion_command()** — this is true on the server side, but the add-in's execute_command() only routes 9 of 39 tool names, breaking the end-to-end dispatch chain.

3. **ADR-G001 defines safety boundaries** but enforcement is purely behavioral (relies on Claude following rules). No code-level enforcement exists.

4. **ADR-D002 acknowledges "no authentication"** as a negative consequence but lists "OS-level file permissions" as mitigation — this is insufficient since any same-user process can read/write.

## Patterns Observed

- **Thin translation layer**: MCP server is intentionally minimal — each tool just serializes params to JSON. All complexity lives in the add-in.
- **Consistent tool shape**: Every server tool follows @mcp.tool() + send_fusion_command(name, params) with no exceptions.
- **Sequential processing**: Add-in processes commands one at a time (no concurrency), which simplifies Fusion API state management.
- **Implicit contract**: The IPC JSON schema is described in prose (ADR-D002) but not formally validated by either side.
