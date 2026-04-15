---
title: "v7.2 Operational Readiness — Architecture Constraints"
document_type: architecture_constraints
created: "2026-04-14"
related:
  - discovery: "./v72-operational-readiness-2026-04-14.md"
  - optimized_requirements: "./optimized-requirements.md"
  - enterprise_review: "./enterprise-review.md"
  - decision_rationale: "./decision-rationale.md"
---

# Architecture Constraints

## Fit Assessment

**Overall Fit: High** — 6 of 8 proposed requirements have zero architectural friction. Two (design brief mode, graceful degradation) need targeted extensions.

## Constraint Table

### MUST (5 constraints)

| # | Constraint | Confidence | Source | Impact |
|---|-----------|------------|--------|--------|
| 1 | All Fusion-interacting tools dispatch through `send_fusion_command()` | **HIGH** | ADR-D002 | High — design brief mode must use a separate code path |
| 2 | IPC directory permissions remain 0o700 (owner-only) | **HIGH** | MT-3 security fix | Low — no new features change directory permissions |
| 3 | Protocol version is fail-closed on mismatch | **HIGH** | NR-1 implementation | Medium — telemetry metadata must stay backward-compatible within v1 |
| 4 | All dimensions in centimeters | **HIGH** | ADR-D003 | Low — planning tools must document cm convention |
| 5 | Offline tools must validate inputs using validation.py | **HIGH** | Enterprise review P1 | High — offline tools bypass IPC security boundary |

### SHOULD (4 constraints)

| # | Constraint | Confidence | Source | Impact |
|---|-----------|------------|--------|--------|
| 6 | New scripts follow argparse + main()->int convention | MEDIUM | Existing pattern (check_version_sync.py) | Low — convention, not enforcement |
| 7 | New tool routers register via mcp.include_router() | MEDIUM | ADR-P001 | Low — established pattern |
| 8 | Skills remain as Claude Project files (not MCP resources) | MEDIUM | Architecture audit finding | Medium — MCP resource delivery deferred to v8.0 |
| 9 | Skill frontmatter uses canonical schema (ADR-G002) | MEDIUM | Enterprise review P3 | Low — governance, not technical constraint |

### MUST NOT (2 constraints)

| # | Constraint | Confidence | Source | Impact |
|---|-----------|------------|--------|--------|
| 10 | Session token must not appear in telemetry logs or session stats | **HIGH** | Security review P0 | High — logging.Filter required for token scrubbing |
| 11 | Typed exception __cause__ chains must not leak to MCP responses | **HIGH** | Security review P2 | Medium — sanitize before serialization |

## ADR Constraints

| ADR | Constraint | Requirement Impact |
|-----|-----------|-------------------|
| ADR-D001 (Tech Stack) | Python only, stdlib preferred | All new scripts/modules are Python |
| ADR-D002 (File-based IPC) | Commands via JSON files in COMM_DIR | Design brief bypasses IPC cleanly via separate router |
| ADR-D003 (Centimeter Units) | All dimensions in cm | Planning tools must document and validate cm |
| ADR-D004 (Z-axis Negation) | Z negated on XZ/YZ planes | Golden path GP2 demonstrates this explicitly |
| ADR-P001 (MCP Tool Registration) | All tools via FastMCP include_router | Planning tools follow this pattern |
| ADR-G001 (Automation Safety) | Verify before destructive operations | Guided design protocol extends this to ambiguous prompts |

## Architectural Extensions Required

1. **errors.py module** — New file introducing typed exception hierarchy. Additive change, no existing code refactored. Callers catching bare `Exception` remain compatible.
2. **timeout_s parameter** — Backward-compatible signature change to `send_fusion_command()`. Default 45.0 preserves existing behavior.
3. **tools/planning.py router** — First tool module that does not use IPC. Establishes the "offline tool" architectural pattern.
4. **JsonFormatter class** — Inline in fusion360_mcp_server.py, gated on env var. No dependency additions.
5. **main() extraction** — Moving `__main__` logic into an importable `main()` function for CLI entry point.
