---
type: adr
id: "D001"
title: "Technology Stack Selection"
date_created: "2026-04-11"
date_modified: "2026-04-11"
version: "1.0"
decision_status: accepted
layer: domain
category: architecture
tags: [tech-stack, python, mcp, fusion360, fastmcp]
depends_on: []
impacts: ["D002", "D003", "D004"]
jira_epic: null
plugin_artifacts: []
deprecation_status: null
deprecation_date: null
superseded_by_plugin: null
---

# Technology Stack Selection

**Deciders**: Project maintainer
**Context**: Project Foundation -- Choosing the core technologies for ClaudeFusion360MCP

## Context

This project enables Claude AI to control Autodesk Fusion 360 for 3D modeling tasks. The technology choices are constrained by two fixed endpoints:

1. **Fusion 360 Add-in API**: Fusion 360 exposes its API through an embedded Python runtime (CPython). Add-ins must be written in Python and use the `adsk.core`, `adsk.fusion`, and `adsk.cam` modules.
2. **Claude Desktop MCP**: Claude AI communicates with external tools through the Model Context Protocol (MCP). The MCP server must implement the MCP specification.

The bridge between these two endpoints needs to be simple, debuggable, and deployable without additional infrastructure.

## Decision

### Core Language & Runtime

- **Language**: Python 3.10+
- **Runtime**: System Python for the MCP server; Fusion 360's embedded CPython for the add-in
- **Rationale**: Python is the only language supported by both Fusion 360's add-in API and the MCP Python SDK. Using the same language on both sides eliminates serialization complexity.

### Framework & Libraries

- **MCP Framework**: FastMCP (from the `mcp` Python package)
- **Key Libraries**: None beyond `mcp` -- the project uses only Python standard library (`json`, `time`, `pathlib`) plus the MCP SDK
- **Rationale**: FastMCP provides decorator-based tool registration (`@mcp.tool()`) with automatic schema generation from type annotations. The minimal dependency footprint reduces install friction -- users only need `pip install mcp`.

### Data & Storage

- **Primary Storage**: Filesystem-based JSON files for IPC (see ADR-D002)
- **No Database**: The project is stateless between sessions; Fusion 360 itself is the data store for 3D designs
- **Rationale**: A database would add deployment complexity for zero benefit. The MCP server translates commands; it does not persist state.

### Infrastructure & Deployment

- **Hosting**: Local machine (both MCP server and Fusion 360 run on the user's workstation)
- **CI/CD**: Not yet established (testing infrastructure is a known gap)
- **Configuration**: Claude Desktop's `claude_desktop_config.json` points to the MCP server script
- **Rationale**: Fusion 360 is a desktop application with no remote API. The MCP server must run on the same machine to access the shared filesystem IPC channel.

## Consequences

**Positive**:
- Single language (Python) across the entire stack reduces cognitive overhead
- One external dependency (`mcp`) makes installation trivial
- No infrastructure to manage -- everything runs locally
- FastMCP's decorator pattern makes adding new tools straightforward (see ADR-P001)

**Negative**:
- Fusion 360's embedded Python is a specific CPython version that may lag behind system Python
- No automated testing infrastructure yet -- the add-in can only be tested inside a running Fusion 360 instance
- Local-only deployment means no remote or collaborative use cases

**Mitigation**:
- Keep add-in code compatible with Python 3.10 (Fusion 360's minimum) even if system Python is newer
- Investigate Fusion 360's headless mode or API mocking for future test automation
- Consider a WebSocket bridge for remote scenarios if the need arises

## Alternatives Considered

1. **TypeScript MCP server + Python add-in**: Use the MCP TypeScript SDK for the server and communicate with a Python add-in -- adds a language boundary and complicates the IPC protocol
2. **gRPC-based communication**: Use gRPC instead of file-based IPC -- more robust but requires protobuf compilation and adds deployment dependencies
3. **Fusion 360 Web API (if available)**: Use Fusion 360's cloud API instead of the desktop add-in -- would remove the local-only constraint but the web API does not expose the full modeling surface

## Related Decisions

- ADR-P001: MCP Tool Registration Pattern -- how tools are registered using FastMCP decorators
- ADR-D002: File-Based IPC Architecture -- the IPC mechanism chosen given this stack
- ADR-D003: Centimeter Unit Convention -- the unit standard dictated by Fusion 360's API
- ADR-D004: Z-Axis Negation on Sketch Planes -- a Fusion 360 API behavior that impacts all sketch tools
