---
type: adr
id: "G001"
title: "Automation Safety Boundary"
date_created: "2026-04-11"
date_modified: "2026-04-11"
version: "1.0"
decision_status: accepted
layer: governance
category: operations
tags: [automation, safety, guardrails, fusion360, destructive-operations]
depends_on: []
impacts: []
jira_epic: null
plugin_artifacts: []
deprecation_status: null
deprecation_date: null
superseded_by_plugin: null
---

# Automation Safety Boundary

**Deciders**: Project maintainer
**Context**: Operational Policy -- Defining what Claude AI can and cannot safely do when controlling Fusion 360

## Context

Claude AI controls Autodesk Fusion 360 through MCP tools that create geometry, modify designs, and export files. Unlike a text editor where changes are easily reversible, 3D CAD operations have compounding effects: a fillet changes face indices, an auto-join merges bodies permanently, and a bad extrusion direction can produce geometry that is difficult to diagnose.

Several failure modes have been empirically documented (see `docs/KNOWN_ISSUES.md` v8.2):

- **Face/edge index instability**: After geometry-modifying operations (fillet, chamfer, shell), face and edge indices change unpredictably. Cached indices become stale.
- **Auto-join risk**: Fusion 360 automatically joins overlapping bodies in the same component, which can merge geometry that was intended to remain separate.
- **Unit confusion**: Passing millimeter values when the API expects centimeters produces geometry 10x too large.
- **Coordinate inversion**: Z-axis negation on XZ/YZ sketch planes (see ADR-D004) causes mirrored geometry if not accounted for.

This ADR establishes the safety boundary for automated operations.

## Decision

### Authorized Actions (no approval needed)

- Creating sketches on any plane (XY, XZ, YZ) with offset
- Drawing geometry within sketches (rectangles, circles, lines, arcs, polygons)
- Finishing sketches
- Extruding, revolving profiles with explicit direction and distance
- Adding fillets, chamfers to specified edges
- Creating named components
- Querying design info, body info, and measurements
- Fitting the viewport
- Exporting to STL, STEP, 3MF formats
- Batch operations (multiple sequential commands in one round-trip)

### Gated Actions (require verification before proceeding)

- **After any geometry-modifying operation** (fillet, chamfer, shell, draft): Must re-query `get_body_info` before referencing face/edge indices. Never cache indices across operations.
- **Before combining bodies**: Must verify both bodies exist and are in the expected positions using `get_body_info` with centroid comparison.
- **Before extrusion on XZ/YZ planes**: Must apply Z-axis negation (ADR-D004) and verify sketch coordinates map correctly.
- **Multi-component assemblies**: Must verify component names after creation; always use named references, never positional indices.
- **Dimensions > 50 cm**: Flag as potential millimeter confusion (likely intended as mm, should be divided by 10).

### Prohibited Actions

- Referencing cached face/edge indices after geometry modification without re-querying
- Assuming auto-join behavior -- always create separate components when bodies should remain independent
- Using raw numeric body/face indices across operation boundaries
- Passing dimensions without verifying they are in centimeters

### Escalation Protocol

- When a tool returns `success: false`, report the error to the user and suggest `undo` before retrying
- When geometry appears at unexpected positions, suggest `fit_view` + `get_body_info` to diagnose before modifying further
- When in doubt about coordinate mapping, create a small test sketch first to verify orientation

## Consequences

**Positive**:
- Prevents the most common failure modes documented in KNOWN_ISSUES.md
- Forces re-verification after operations that invalidate cached state
- Unit and coordinate checks catch errors before they compound

**Negative**:
- Verification steps (re-querying body info) add latency to multi-step operations
- The safety boundary requires Claude to understand Fusion 360 API quirks that are not intuitive
- Batch operations that include geometry-modifying steps need careful ordering

**Mitigation**:
- Use batch operations to amortize verification overhead (query body info as part of the batch)
- Document the safety rules prominently in SKILL.md and SPATIAL_AWARENESS.md
- Design tool prompts to remind Claude of verification requirements

## Alternatives Considered

1. **No formal boundary**: Trust Claude's general reasoning to avoid errors -- simplest but the documented failure modes show this is insufficient
2. **Allowlist-only**: Enumerate every permitted sequence of operations -- too restrictive and unmaintainable as tools evolve
3. **Server-side enforcement**: Build safety checks into the MCP server itself -- more robust but adds complexity to a deliberately thin translation layer

## Related Decisions

- ADR-D003: Centimeter Unit Convention -- the unit standard that safety checks enforce
- ADR-D004: Z-Axis Negation on Sketch Planes -- the coordinate inversion that gated actions must account for
