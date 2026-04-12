---
title: "MCP Deep Audit — Decision Rationale"
document_type: decision_rationale
created: "2026-04-12"
primary_doc: ".vsify/discovery/mcp-deep-audit-improvement-roadmap-2026-04-12.md"
---

# Decision Rationale

## Phase 1A: Input Type Classification

The user's request ("deep analysis to verify it is a legit functioning MCP with low risk, and identify existing bugs, and potential short, medium, and long term improvements") was classified as a **high-level idea / stakeholder request** for a comprehensive audit. The scope was immediately clear from the request — no clarification needed.

## Phase 1B: Creative Divergence

### How Might We Direction
6 HMW questions were generated. The user confirmed all were valuable. Key user input: "Requiring Fusion 360 running for e2e testing is acceptable."

### SCAMPER Alternative Framings
6 alternative framings were generated across 3 SCAMPER lenses:
1. Risk-Only Audit (Substitute + Eliminate)
2. Gap Audit / Roadmap (Substitute + Eliminate)
3. Audit + Quality Baseline (Combine + Adapt)
4. MCP Maturity Scorecard (Combine + Adapt)
5. User-Failure-First (Reverse + Modify)
6. Deep Core Audit (Reverse + Modify)

**User's decision**: Original framing is best — full audit across legitimacy, bugs, and improvements. The alternative framings surfaced useful considerations but didn't change the scope.

### Enhancement Selection
5 incremental enhancements were proposed:
1. Tool-by-tool compatibility matrix (E1) — included
2. Doc-to-code drift register (E2) — included
3. IPC race condition analysis (E3) — included
4. Security surface map (E4) — included
5. Recommended test harness sketch (E5) — included

**User's decision**: Include all 5.

## Phase 3: Optimization Direction

Two optimization approaches were generated:
- **Platform-Aligned**: Maximize reuse, ship fast, personal-use quality
- **Ideal-Outcome**: Production quality, MCP registry publishable

Key differences:
- Ideal-outcome flagged threading violation as P0 (platform-aligned did not)
- Ideal-outcome discovered 5 new requirements (IPC versioning, lifecycle handling, tool descriptions, export path returns, model state tool)
- Ideal-outcome targets MCP registry publishability
- Platform-aligned proposes IPC replacement long-term; ideal-outcome hardens existing IPC

**User's decision**: Ideal outcome — prioritize production quality and MCP registry publishability, accept architectural evolution.

## Key Technical Decisions

### Tool Count Correction
Initial analysis stated 33 tools. Careful @mcp.tool() counting revealed **39 tools**. The difference was carried forward as a doc-to-code drift instance (the project's own documentation understates the tool count).

### Threading Assessment
The daemon thread calling Fusion API directly was classified as P0 based on:
- Fusion 360's documented requirement for main-thread API access
- Risk of data corruption and crashes
- The fact that this affects ALL 9 working tools, not just edge cases

However, the code appears to work in practice — suggesting either Fusion's Python bridge is more thread-safe than documented, or the failures are intermittent and haven't manifested yet. The P0 classification was maintained because correctness violations that "seem to work" are the most dangerous bugs.

### Phantom Tool Naming
The term "phantom tool" was coined during this audit to describe a tool that:
1. Is registered in the MCP server (Claude sees it)
2. Has no implementation in the add-in
3. Returns "Unknown tool" at runtime

This is worse than the tool not existing at all — Claude wastes the user's time attempting it.

### Silently Ignored Parameters
A distinct category from phantom tools: parameters that are declared in the MCP tool signature, accepted by the server, passed through IPC, but never read by the add-in handler. Examples: `offset` in create_sketch, `profile_index` in extrude. These produce wrong output with no error.
