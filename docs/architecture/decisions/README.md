# Architecture Decision Records

## ADR Index

### Platform

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-P001](platform/ADR-P001-mcp-tool-registration-pattern.md) | MCP Tool Registration Pattern | Accepted | 2026-04-11 |

### Governance

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-G001](governance/ADR-G001-automation-safety-boundary.md) | Automation Safety Boundary | Accepted | 2026-04-11 |

### Domain

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-D001](domain/ADR-D001-technology-stack-selection.md) | Technology Stack Selection | Accepted | 2026-04-11 |
| [ADR-D002](domain/ADR-D002-file-based-ipc-architecture.md) | File-Based IPC Architecture | Accepted | 2026-04-11 |
| [ADR-D003](domain/ADR-D003-centimeter-unit-convention.md) | Centimeter Unit Convention | Accepted | 2026-04-11 |
| [ADR-D004](domain/ADR-D004-z-axis-negation-sketch-planes.md) | Z-Axis Negation on Sketch Planes | Accepted | 2026-04-11 |

## Decision Map

```
D001 (Technology Stack)
 ├── impacts ──> D002 (File-Based IPC)
 ├── impacts ──> D003 (Centimeter Convention)
 └── impacts ──> D004 (Z-Axis Negation)

D003 (Centimeter Convention)
 └── impacts ──> D004 (Z-Axis Negation)
```

Cross-layer references (P001, G001 ↔ Domain ADRs) are documented in each ADR's Related Decisions section but not modeled as hard dependencies.

### Cross-Reference Summary

| ADR | Depends On | Impacts |
|-----|-----------|---------|
| P001 | -- | -- |
| G001 | -- | -- |
| D001 | -- | D002, D003, D004 |
| D002 | D001 | -- |
| D003 | D001 | D004 |
| D004 | D001, D003 | -- |

## Superseded Decisions

*(None)*
