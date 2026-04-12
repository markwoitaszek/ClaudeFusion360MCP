---
type: adr
id: "P001"
title: "MCP Tool Registration Pattern"
date_created: "2026-04-11"
date_modified: "2026-04-11"
version: "1.0"
decision_status: accepted
layer: platform
category: architecture
tags: [mcp, tool-registration, decorator-pattern, extensibility]
depends_on: []
impacts: []
jira_epic: null
plugin_artifacts: []
deprecation_status: null
deprecation_date: null
superseded_by_plugin: null
---

# MCP Tool Registration Pattern

**Deciders**: Project maintainer
**Context**: Platform Architecture -- Defining how MCP tools are registered and exposed to Claude AI

## Context

The Model Context Protocol (MCP) provides a standard interface for AI assistants to interact with external systems. This project bridges Claude AI to Autodesk Fusion 360 by exposing Fusion 360 operations as MCP tools. A consistent registration pattern is needed so that:

- New tools can be added without modifying framework plumbing
- Each tool has a predictable signature (name, typed parameters, docstring)
- The server remains a single deployable unit with no plugin discovery overhead

The MCP Python SDK provides FastMCP, a decorator-based framework that maps Python functions directly to MCP tool definitions. This ADR records the decision to adopt FastMCP's decorator pattern as the sole tool registration mechanism.

## Decision

All MCP tools are registered using the `@mcp.tool()` decorator on standalone Python functions in a single server file (`mcp-server/fusion360_mcp_server.py`).

### Key Details

- **Registration mechanism**: The `@mcp.tool()` decorator from FastMCP. Each decorated function becomes an MCP tool whose name matches the function name and whose parameters are inferred from the function signature.
- **Single-file architecture**: All tools live in one file (~628 lines), organized by category comments. No dynamic discovery, no plugin loading, no module imports.
- **Tool categories**: Tools are grouped by functional area (Sketching, 3D Operations, Patterns, Components, Inspection, Joints, Utilities, Export/Import) using comment headers within the file.
- **Parameter conventions**: All functions use typed parameters with defaults. Dimensions are always in centimeters (see ADR-D003). Plane references use string literals (`"XY"`, `"XZ"`, `"YZ"`).
- **Return contract**: Every tool function calls `send_fusion_command()` and returns the result dict (containing `success` boolean and either `result` or `error`).

### Tool Inventory (39 tools)

| Category | Tools | Count |
|----------|-------|-------|
| Sketching | create_sketch, finish_sketch, draw_rectangle, draw_circle, draw_line, draw_arc, draw_polygon, batch | 8 |
| 3D Operations | extrude, revolve, shell, draft, fillet, chamfer, combine | 7 |
| Patterns & Transforms | pattern_rectangular, pattern_circular, mirror | 3 |
| Components & Assembly | create_component, list_components, delete_component, move_component, rotate_component, check_interference, create_revolute_joint, create_slider_joint | 8 |
| Inspection & Measurement | get_design_info, get_body_info, measure, fit_view | 4 |
| Joints & Animation | set_joint_angle, set_joint_distance | 2 |
| Utilities | undo, delete_body, delete_sketch | 3 |
| Export/Import | export_stl, export_step, export_3mf, import_mesh | 4 |

## Consequences

**Positive**:
- Adding a new tool requires only writing a decorated function -- no manifest, no registration boilerplate
- FastMCP auto-generates tool schemas from type annotations, reducing documentation drift
- Single-file layout makes the full tool surface visible at a glance

**Negative**:
- Single-file architecture will become unwieldy beyond ~50 tools; the file is already 628 lines
- No runtime tool isolation -- a bug in one tool function can crash the entire server process
- Tool names are coupled to Python function names, limiting rename flexibility

**Mitigation**:
- If the tool count exceeds 50, split into category modules (e.g., `tools/sketching.py`) and use FastMCP's `include_router` to compose them
- Wrap each tool body in try/except to prevent cascading failures
- Use FastMCP's `name` parameter (`@mcp.tool(name="custom_name")`) if function names need to diverge from tool names

## Alternatives Considered

1. **Multi-file tool modules with auto-discovery**: Scan a `tools/` directory for Python files, import decorated functions dynamically -- more modular but adds discovery complexity and startup time for a small tool set
2. **Manifest-driven registration**: Define tools in a JSON/YAML manifest and generate handler stubs -- provides a single source of truth for tool schemas but adds a code generation step
3. **Class-based tool definitions**: Each tool as a class with `execute()` method -- OOP structure but heavier boilerplate for what are essentially stateless functions

## Related Decisions

- ADR-D001: Technology Stack Selection -- chose FastMCP as the MCP framework
- ADR-D002: File-Based IPC Architecture -- the transport layer that tools dispatch commands through
