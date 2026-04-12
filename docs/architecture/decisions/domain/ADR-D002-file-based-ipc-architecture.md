---
type: adr
id: "D002"
title: "File-Based IPC Architecture"
date_created: "2026-04-11"
date_modified: "2026-04-11"
version: "1.0"
decision_status: accepted
layer: domain
category: architecture
tags: [ipc, file-based, json, polling, communication]
depends_on: ["D001"]
impacts: []
jira_epic: null
plugin_artifacts: []
deprecation_status: null
deprecation_date: null
superseded_by_plugin: null
---

# File-Based IPC Architecture

**Deciders**: Project maintainer
**Context**: Core Architecture -- How the MCP server communicates with the Fusion 360 add-in

## Context

The MCP server and the Fusion 360 add-in run as separate processes:

- The **MCP server** runs as a standard Python process, launched by Claude Desktop
- The **Fusion 360 add-in** runs inside Fusion 360's embedded Python runtime, in a daemon thread

These two processes need a communication channel. The key constraints are:

1. **No shared memory**: Fusion 360's embedded Python runs in a sandboxed environment with limited access to system APIs
2. **No network listeners**: The add-in cannot easily open TCP/UDP sockets within Fusion 360's process
3. **Cross-platform**: Must work on both macOS and Windows
4. **Low latency**: Interactive 3D modeling sessions need sub-second command round-trips
5. **Debuggable**: Developers should be able to inspect in-flight commands

The filesystem is the one resource reliably accessible from both processes on both platforms.

## Decision

Communication uses timestamped JSON files in a shared directory (`~/fusion_mcp_comm/`).

### Protocol

1. **MCP server writes** a command file: `command_{timestamp}.json`
   ```json
   {"type": "tool", "name": "create_sketch", "params": {"plane": "XY"}, "id": "1712345678"}
   ```
2. **Add-in polls** the directory every 100ms for `command_*.json` files
3. **Add-in executes** the command via Fusion 360 API
4. **Add-in writes** a response file: `response_{timestamp}.json`
   ```json
   {"success": true, "result": {"sketch_name": "Sketch1"}}
   ```
5. **MCP server polls** for the matching `response_{timestamp}.json` (up to 900 iterations x 50ms = 45-second timeout)
6. **Files are cleaned up** after successful exchange

### Key Details

- **Directory**: `~/fusion_mcp_comm/` (created by both sides on startup if absent)
- **File format**: JSON with four fields: `type`, `name`, `params`, `id`
- **Polling intervals**: Add-in polls at 100ms; MCP server polls at 50ms
- **Timeout**: 45 seconds per command (configurable via poll count)
- **Batch operations**: The `batch` tool sends multiple commands in a single file, reducing round-trip overhead for complex workflows (5-10 commands per batch)
- **Ordering**: Commands are processed sequentially by the add-in; no concurrent execution
- **Error handling**: Failed commands return `{"success": false, "error": "message"}`

## Consequences

**Positive**:
- Works on both macOS and Windows with zero platform-specific code
- Commands and responses are human-readable JSON -- easy to debug by inspecting the directory
- No network configuration, no port conflicts, no firewall issues
- The filesystem acts as a natural buffer -- if one side is slow, files queue up

**Negative**:
- Polling introduces latency (50-100ms per poll cycle, plus filesystem I/O)
- No built-in notification mechanism -- both sides must poll continuously
- File cleanup failures can leave stale command/response files
- No authentication or access control on the communication directory

**Mitigation**:
- The 50ms/100ms polling intervals keep latency under 200ms for typical operations, which is acceptable for interactive modeling
- Both sides create the directory on startup, ensuring it exists
- Stale files from previous sessions are harmless (timestamps prevent collisions)
- The communication directory is in the user's home directory, inheriting OS-level file permissions

## Alternatives Considered

1. **Named pipes / Unix domain sockets**: Lower latency and event-driven -- but platform-specific (named pipes on Windows, Unix sockets on macOS) and harder to debug
2. **HTTP/REST server in add-in**: Add-in runs a local HTTP server -- cleaner protocol but opening a port inside Fusion 360's process is unreliable and may conflict with other add-ins
3. **WebSocket bridge**: Persistent bidirectional connection -- lowest latency but adds a dependency (websocket library) and Fusion 360's embedded Python may not support it
4. **Shared memory / memory-mapped files**: Fastest IPC mechanism -- but complex to implement correctly cross-platform and overkill for JSON command payloads

## Related Decisions

- ADR-D001: Technology Stack Selection -- chose Python + filesystem as the common ground between both processes
- ADR-P001: MCP Tool Registration Pattern -- each registered tool dispatches through `send_fusion_command()` which implements this IPC protocol
