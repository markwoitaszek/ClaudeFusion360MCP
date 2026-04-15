---
title: "v7.2 Operational Readiness — Decision Rationale"
document_type: decision_rationale
created: "2026-04-14"
related:
  - discovery: "./v72-operational-readiness-2026-04-14.md"
  - optimized_requirements: "./optimized-requirements.md"
  - architecture_constraints: "./architecture-constraints.md"
  - enterprise_review: "./enterprise-review.md"
---

# Decision Rationale

## Creative Divergence Selections (Phase 1B)

### HMW Questions
All 7 "How Might We" questions were confirmed as useful directions:
1. Non-CAD users need natural language to CAD translation
2. First-attempt geometry correctness via verification loops
3. Zero-friction installation for non-developers
4. Community-extensible skill architecture
5. Real-time design state awareness
6. Value even when Fusion is not running (design briefs)
7. Developer experience that encourages first contributions

### SCAMPER Framings Selected
From 6 alternative framings, the user chose a **blend** of:
- **F4 (Robotics Skill Stacks)** — Tiered skill architecture (Foundation, Patterns, Expert)
- **F2 (Design Tutor)** — Claude asks before assuming when intent is ambiguous
- **F6 (Golden Paths)** — Obsessively-documented quick-start workflows

### Framings Deferred
- F1 (Skills-Only Release) — Server works; no reason to strip
- F3 (Parametric Constraint Solver) — 3+ months of work; deferred to v2
- F5 (Dynamic Self-Documenting Skills) — Loses pedagogical value of hand-crafted skills

### Enhancements Approved
All 5 "Yes, And..." enhancements were included:
1. Makefile with standard targets (Low effort)
2. Design operation telemetry dashboard (Medium effort)
3. Skill contribution template + validator (Medium effort)
4. Graceful degradation when Fusion disconnected (Low effort)
5. "Design Brief" mode for offline planning (Medium effort)

## Requirements Optimization Direction (Phase 3)

### Approach: Suggested Blend

The user selected the synthesized blend over pure platform-aligned or ideal-outcome approaches.

### Key Cherry-Pick Decisions

| Area | Platform-Aligned | Ideal-Outcome | Blend Decision | Reasoning |
|------|-----------------|---------------|----------------|-----------|
| Tooling | Makefile only | CLI tool only | **Both** | Makefile for devs, CLI for installed users. Zero-cost addition. |
| Error handling | Extend error strings | Typed exception hierarchy | **IO wins** | Bare Exception is unacceptable for mature server. Three typed classes. |
| Telemetry | JSON formatter only | Full telemetry module + MCP tool | **Hybrid** | PA formatter scope + IO's get_session_stats tool idea |
| Design brief | Basic planning router | Planning + offline_safe tagging | **IO addition** | Lightweight docstring tag costs nothing, enables future tooling |
| Skills tiering | Add tier field to frontmatter | Split into 3 files | **PA wins** | File split breaks Claude Desktop config with no clear benefit at current scale |
| Golden paths | Docs + test file | SKILL.md sections | **PA wins** | Tests provide regression protection that docs cannot |
| Guided design | SKILL.md section | Same + brief-mode override | **IO addition** | Brief-mode costs one sentence, addresses expert-user friction |
| Skill validator | Script only | Script + ADR | **IO wins** | ADR prevents future schema ambiguity |

### Divergence Points

The most significant disagreement between approaches was **error handling**:
- PA argued extending error strings is simpler and sufficient
- IO argued typed exceptions are non-negotiable for production
- **Resolution**: IO wins. The diagnostic helper tool (PA's alternative) is wrong because it requires IPC to work, which is exactly what fails in the scenarios it is meant to diagnose. Typed exceptions carry diagnostic information in the exception itself.

The second major disagreement was **skills tiering**:
- IO proposed splitting SKILL.md into three files with per-tier model_target
- PA proposed keeping the single file with a tier frontmatter field
- **Resolution**: PA wins for now. The file split has concrete breaking costs (Claude Desktop config changes, doc link rerouting) with no clear user-facing benefit at current project scale. The tier field captures the architecture; the split is captured as future scope in ADR-G002.

## Enterprise Review Response (Phase 4)

The enterprise review identified 4 gaps and 8 risks. User chose to address gaps inline:

### P0 Gap Addressed
- `get_session_stats` return schema explicitly specified to exclude session token

### P1 Gaps Addressed
- Offline tools in planning.py required to import validators from validation.py
- CI hardened to use `pip install -e '.[dev]'` for consistent installs
- Golden path tests required to call tool functions, not IPC directly

### Risks Accepted
- Multi-process session token collision documented as known limitation (not fixed in v7.2)
- Token re-read TOCTOU window accepted at current risk level (single-user desktop app)
