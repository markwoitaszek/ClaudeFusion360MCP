# CLAUDE.md — ClaudeFusion360MCP

Project memory and behavioral rules for Claude Code sessions in this repository.

---

## Repository Overview

<!-- BEGIN PROJECT DESCRIPTION (user-supplied) -->
Control Autodesk Fusion 360 with Claude AI through the Model Context Protocol (MCP). This MCP server lets Claude AI directly control Fusion 360 to create 3D sketches, extrusions, revolves, sweeps, multi-component assemblies, fillets, chamfers, shells, patterns, and export to STL/STEP/3MF formats.
<!-- END PROJECT DESCRIPTION -->

### Directory Structure

```
fusion-addin/  Fusion 360 Add-in (runs inside Fusion 360's embedded Python)
mcp-server/    MCP server (bridges Claude AI to Fusion 360 via file-based IPC)
docs/          Documentation, skill guides, and spatial awareness reference
examples/      Getting started examples and common prompts
```

---

## Development Workflow

### Branch Strategy

This project uses **GitHub Flow**: a single `main` branch with short-lived feature branches (`feat/*`, `fix/*`). All changes go through pull requests.

### Key Commands

| Command | What it does |
|---------|-------------|
| `pip install mcp` | Install MCP framework dependency |
| `python mcp-server/fusion360_mcp_server.py` | Run the MCP server |

### Prerequisites

- Autodesk Fusion 360 (free for personal use)
- Python 3.10+
- Claude Desktop app with MCP support

---

## Testing

TODO: Add test framework and commands. The project currently has no automated test suite.

---

## Commit Conventions

Use conventional commits:
- `feat:` — new features
- `fix:` — bug fixes
- `docs:` — documentation only
- `test:` — test additions or fixes
- `chore:` — tooling and maintenance

---

## Important Notes

- All MCP dimensions are in **centimeters** (not millimeters)
- The Fusion 360 Add-in communicates with the MCP server via file-based IPC
- When Z is part of the sketch plane (XZ or YZ), the sketch coordinate that maps to World Z is **negated**
