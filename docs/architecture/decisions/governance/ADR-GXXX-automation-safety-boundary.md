---
type: adr
id: "GXXX"
title: "Automation Safety Boundary"
date_created: "2026-04-11"
date_modified: "2026-04-11"
version: "1.0"
decision_status: proposed
layer: governance
category: operations
tags: [automation, safety, guardrails, policy]
depends_on: []
impacts: []
jira_epic: null
plugin_artifacts: []
deprecation_status: null
deprecation_date: null
superseded_by_plugin: null
---

# Automation Safety Boundary

**Deciders**: TODO: Development Team / Operations
**Context**: TODO: Operational Policy -- Defining what automated tools can and cannot do

## Context

Automated tools (CI/CD pipelines, code generators, AI assistants, scripts) operate on the codebase and infrastructure. Without explicit boundaries, automation can take actions that are difficult to reverse, affect shared resources, or bypass safety checks that human operators would respect.

Governance-layer decisions constrain automation behavior to prevent unintended consequences. This ADR establishes the safety boundary -- what automated processes are authorized to do, what requires human approval, and what is prohibited.

TODO: Customize this context for your project's specific automation landscape.

## Decision

TODO: Define your automation safety boundary. Consider these categories:

### Authorized Actions (no approval needed)
- TODO: e.g., Running tests, linting, formatting, building artifacts
- TODO: e.g., Reading configuration, scanning for issues, generating reports

### Gated Actions (require human approval)
- TODO: e.g., Deploying to staging/production, modifying infrastructure
- TODO: e.g., Creating/closing issues, sending notifications, publishing releases

### Prohibited Actions
- TODO: e.g., Force-pushing to protected branches, deleting production data
- TODO: e.g., Modifying access controls, bypassing security checks

### Escalation Protocol
- TODO: When automation encounters an ambiguous situation, how should it escalate?
- TODO: What is the fallback when the approval authority is unavailable?

## Consequences

**Positive**:
- Clear boundaries prevent automation from taking unintended destructive actions
- Human oversight is preserved for high-impact operations
- New automation can be evaluated against a documented policy rather than ad-hoc judgment

**Negative**:
- Overly restrictive boundaries slow down workflows that could be safely automated
- The boundary must be maintained as new tools and capabilities are introduced
- Enforcement depends on each tool respecting the policy -- not all tools have built-in governance

**Mitigation**:
- Review boundaries quarterly and relax restrictions that have proven unnecessary
- Implement enforcement at the platform level where possible (e.g., branch protection rules, CI pipeline gates)
- Document exceptions with rationale so they can be evaluated later

## Alternatives Considered

1. **No formal boundary**: Trust each tool's defaults and team judgment -- simplest but highest risk of unintended actions
2. **Allowlist-only**: Enumerate every permitted action -- most secure but high maintenance cost
3. **Denylist-only**: Enumerate only prohibited actions -- lower maintenance but may miss new risky actions

## Related Decisions

- TODO: Link to platform ADRs that implement the enforcement mechanism
- TODO: Link to domain ADRs that define tool-specific constraints
