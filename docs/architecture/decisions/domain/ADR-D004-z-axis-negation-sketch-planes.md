---
type: adr
id: "D004"
title: "Z-Axis Negation on Sketch Planes"
date_created: "2026-04-11"
date_modified: "2026-04-11"
version: "1.0"
decision_status: accepted
layer: domain
category: architecture
tags: [coordinates, z-axis, sketch-planes, spatial-awareness, empirical]
depends_on: ["D001", "D003"]
impacts: []
jira_epic: null
plugin_artifacts: []
deprecation_status: null
deprecation_date: null
superseded_by_plugin: null
---

# Z-Axis Negation on Sketch Planes

**Deciders**: Project maintainer
**Context**: Spatial Accuracy -- Documenting the empirically verified Z-axis inversion on XZ and YZ sketch planes

## Context

When creating sketches on Fusion 360's construction planes, the 2D sketch coordinate system maps to 3D world coordinates differently depending on which plane is used. On the XY plane, the mapping is intuitive (sketch X = world X, sketch Y = world Y). However, on the XZ and YZ planes, the sketch coordinate that maps to world Z is **negated**.

This behavior was discovered empirically through repeated trial and error. It is not documented in Fusion 360's official API reference but has been verified across multiple Fusion 360 versions on both macOS and Windows. The root cause appears to be how Fusion 360 constructs the sketch coordinate frame using cross-product conventions.

The impact is significant: without accounting for this negation, geometry placed via XZ or YZ sketches appears mirrored along the Z axis.

## Decision

All MCP tools and documentation account for Z-axis negation on XZ and YZ sketch planes. The coordinate mapping rules are:

### Coordinate Mapping Table

| Sketch Plane | Sketch X -> World | Sketch Y -> World | Notes |
|-------------|-------------------|-------------------|-------|
| **XY** | X | Y | Direct mapping -- no inversion |
| **XZ** | X | **-Z** (negated) | Sketch Y maps to negative world Z |
| **YZ** | **-Z** (negated) | Y | Sketch X maps to negative world Z |

### Practical Rule

To position geometry at world Z from A to B on an XZ or YZ plane: use sketch coordinates from **-B to -A** (negate and swap the bounds).

### Key Details

- **Extrusion direction follows the same pattern**:
  - XY: +distance = +Z (up), -distance = -Z (down)
  - XZ: +distance = +Y (toward viewer), -distance = -Y (away)
  - YZ: +distance = +X (right), -distance = -X (left)
- **This applies to all sketch geometry tools**: draw_rectangle, draw_circle, draw_line, draw_arc, draw_polygon
- **The `create_sketch` offset parameter is NOT negated** -- only the in-sketch coordinates are affected
- **Verification protocol**: The SPATIAL_AWARENESS.md document includes test cases for verifying this behavior

### Example

To draw a rectangle spanning world X=[0,5], Z=[0,3] on the XZ plane:

```
# World coordinates desired: X from 0 to 5, Z from 0 to 3
# XZ plane mapping: Sketch X -> World X (direct), Sketch Y -> World -Z (negated)
# Therefore: Sketch X from 0 to 5, Sketch Y from -3 to 0
draw_rectangle(x_min=0, y_min=-3, x_max=5, y_max=0)
```

## Consequences

**Positive**:
- Formally documents a non-obvious API behavior that previously caused repeated debugging cycles
- The coordinate mapping table provides a quick reference for all three planes
- The practical rule (negate and swap bounds) gives a simple mental model

**Negative**:
- Every sketch operation on XZ/YZ planes requires the caller to remember the negation
- The behavior is an implementation quirk, not a design choice -- it could change in a future Fusion 360 update
- Error messages from Fusion 360 do not indicate when geometry is mirrored due to incorrect coordinate mapping

**Mitigation**:
- SPATIAL_AWARENESS.md prominently documents the negation rules with examples
- ADR-G001 mandates verification steps before extrusion on XZ/YZ planes
- The KNOWN_ISSUES.md "XZ plane Y-axis inversion" entry cross-references this ADR
- If Fusion 360 changes this behavior in a future version, this ADR should be updated and all sketch tools re-verified

## Alternatives Considered

1. **Server-side coordinate transformation**: Automatically negate Z coordinates in the MCP server when the plane is XZ or YZ -- hides the complexity but makes debugging harder and introduces a divergence between what the user specifies and what Fusion 360 receives
2. **Wrapper tool with world coordinates**: Create a `draw_rectangle_world(x_min, y_min, z_min, ...)` tool that translates to sketch coordinates internally -- cleaner API but adds a layer of abstraction that obscures the underlying plane behavior
3. **Document but don't enforce**: Rely on Claude's knowledge of the negation without formal enforcement -- insufficient, as the behavior is counterintuitive and easily forgotten

## Related Decisions

- ADR-D001: Technology Stack Selection -- Fusion 360's API is the source of this behavior
- ADR-D003: Centimeter Unit Convention -- coordinates use centimeters, and the negation applies to the centimeter values
- ADR-G001: Automation Safety Boundary -- mandates verification before XZ/YZ plane operations
