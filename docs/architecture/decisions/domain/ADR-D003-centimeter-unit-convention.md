---
type: adr
id: "D003"
title: "Centimeter Unit Convention"
date_created: "2026-04-11"
date_modified: "2026-04-11"
version: "1.0"
decision_status: accepted
layer: domain
category: architecture
tags: [units, centimeters, dimensions, fusion360-api]
depends_on: ["D001"]
impacts: ["D004"]
jira_epic: null
plugin_artifacts: []
deprecation_status: null
deprecation_date: null
superseded_by_plugin: null
---

# Centimeter Unit Convention

**Deciders**: Project maintainer
**Context**: API Design -- Standardizing the unit system for all MCP tool dimensions

## Context

Fusion 360's internal API uses **centimeters** as the base unit for all linear dimensions. This is a non-obvious choice -- most mechanical engineering contexts use millimeters, and many users instinctively think in millimeters.

This mismatch has been a documented source of errors (see `docs/KNOWN_ISSUES.md`):

- A user requesting a "10mm box" gets a 10cm (100mm) box if the value is passed without conversion
- Dimensions greater than 50 in any tool parameter are suspicious -- a 50cm object is 500mm, which is unusually large for most desktop designs
- The Fusion 360 UI can display any unit system, but the API always operates in centimeters regardless of the UI setting

The MCP server must adopt a consistent unit convention and communicate it clearly to Claude AI.

## Decision

All MCP tool dimensions are in **centimeters**. No unit conversion is performed by the MCP server or add-in -- values are passed directly to the Fusion 360 API.

### Key Details

- **Conversion rule**: millimeters / 10 = centimeters (e.g., 25mm = 2.5cm)
- **Red flag threshold**: Any dimension > 50 should be flagged as potential millimeter confusion
- **Documentation**: Every tool docstring states "All dimensions in centimeters"
- **No unit parameter**: Tools do not accept a `unit` parameter. The convention is fixed at centimeters to prevent ambiguity.
- **Angular values**: Angles are in **degrees** (not radians), consistent with Fusion 360's API

### Common Reference Values

| Object | Millimeters | Centimeters (MCP value) |
|--------|------------|------------------------|
| M3 screw head | 5.5mm | 0.55 |
| USB-C port width | 8.25mm | 0.825 |
| Credit card width | 85.6mm | 8.56 |
| Phone case length | 150mm | 15.0 |

## Consequences

**Positive**:
- Eliminates ambiguity -- one unit system, no conversion logic needed
- Matches the Fusion 360 API exactly, so values pass through without transformation
- The red flag threshold (>50) catches the most common error (mm vs cm confusion)

**Negative**:
- Users and Claude AI must remember to convert from millimeters, which is the more natural unit in mechanical engineering
- Small features (sub-millimeter) require very small centimeter values (e.g., 0.05 cm = 0.5 mm), which are easy to mistype
- The convention cannot be changed without updating all tool docstrings, documentation, and user expectations

**Mitigation**:
- SKILL.md and SPATIAL_AWARENESS.md prominently document the centimeter convention
- Getting-started examples use realistic centimeter values with mm equivalents in comments
- Claude's system prompt includes the centimeter rule as a key constraint

## Alternatives Considered

1. **Accept millimeters and convert server-side**: Add a conversion layer in the MCP server (mm -> cm) -- more intuitive for users but introduces a hidden transformation that makes debugging harder
2. **Accept a `unit` parameter on each tool**: Let users specify "mm" or "cm" per call -- flexible but error-prone (forgetting the parameter defaults to the wrong unit)
3. **Use millimeters throughout**: Override Fusion 360's internal unit by multiplying all inputs by 0.1 -- consistent user experience but diverges from the API and adds a conversion that could break with API changes

## Related Decisions

- ADR-D001: Technology Stack Selection -- Fusion 360's API dictates the centimeter base unit
- ADR-G001: Automation Safety Boundary -- the >50cm red flag is a safety check derived from this convention
