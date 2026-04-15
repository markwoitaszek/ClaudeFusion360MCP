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
| `pip install -e '.[dev]'` | Install all dependencies (including dev tools) |
| `make run` | Run the MCP server (LOG_LEVEL=DEBUG) |
| `make test` | Run tests with 70% coverage threshold |
| `make lint` | Lint with ruff + black |
| `python mcp-server/fusion360_mcp_server.py` | Run the MCP server directly |

### Prerequisites

- Autodesk Fusion 360 (free for personal use)
- Python 3.10+
- Claude Desktop app with MCP support

---

## Testing

| Command | What it does |
|---------|-------------|
| `make test` | Run pytest with coverage (70% threshold) |
| `make lint` | Run ruff + black format check |
| `python -m pytest tests/ -v` | Run tests without coverage |
| `python -m pytest tests/ -v -m "not integration"` | Skip integration tests (no Fusion required) |

Tests are in `tests/`. Integration tests requiring a live Fusion 360 instance are marked with `@pytest.mark.integration` and gated by the `FUSION_SMOKE_TESTS` environment variable.

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
