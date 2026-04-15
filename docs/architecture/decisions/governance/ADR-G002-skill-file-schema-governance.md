---
type: adr
id: "G002"
title: "Skill File Schema Governance"
date_created: "2026-04-14"
date_modified: "2026-04-14"
version: "1.0"
decision_status: accepted
layer: governance
category: documentation
tags: [skills, schema, validation]
depends_on: []
impacts: [G001]
jira_epic: null
plugin_artifacts: [docs/SKILL_TEMPLATE.md, scripts/validate_skills.py]
deprecation_status: null
deprecation_date: null
superseded_by_plugin: null
---

# Skill File Schema Governance

**Deciders**: Project maintainers
**Context**: v7.2 Operational Readiness — Skill tier metadata and validation

## Context

Skill files (`docs/SKILL.md`, `docs/SPATIAL_AWARENESS.md`) use YAML frontmatter to declare metadata consumed by Claude Desktop and other MCP clients. Without a canonical schema, frontmatter fields drift (e.g., `mcp_version: 7.0.0` was stale for months). Contributors have no template and no validation to catch schema violations before merge.

## Decision

Establish a canonical YAML frontmatter schema for skill files, enforced by a validator script in CI.

### Key Details

**Required frontmatter fields** (all skill files must include):

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Kebab-case identifier (e.g., `fusion360-mcp`) |
| `description` | string | One-line description of the skill's purpose |
| `version` | string | Semver document version (e.g., `1.0.0`) |
| `model_target` | string | Target Claude model (e.g., `any-claude-model`, `claude-opus-4-5`) |
| `mcp_version` | string | MCP server version this skill is compatible with |
| `tier` | string | One of: `core`, `advanced`, `specialist` |

**Optional fields**: `companion_skills`, `last_updated`, `tags`

**Tier definitions**:
- `core`: Essential skills loaded in every session (e.g., main CAD operations)
- `advanced`: Domain-specific skills loaded on demand (e.g., spatial awareness)
- `specialist`: Future — reserved for highly specialized domain skills

**Validation**: `scripts/validate_skills.py` checks all `.md` files in `docs/` for:
1. Valid YAML frontmatter presence
2. All required fields present and non-empty
3. `mcp_version` matches the canonical VERSION file
4. `tier` is one of the valid tier names

**Future scope**: Splitting SKILL.md into per-tier files is deferred. The single-file approach works at current project scale. The tier field captures the architecture for future splitting if needed.

## Consequences

**Positive**:
- Version drift caught automatically in CI
- Contributors have a clear template to follow
- Tier metadata enables future tooling for skill management

**Negative**:
- Adds a validation step to CI (small overhead)
- Existing skill files must be updated to include new fields

**Mitigation**:
- Validator runs fast (pure Python, no external deps)
- This PR updates all existing skill files to comply

## Alternatives Considered

1. **No schema enforcement**: Rely on PR review to catch frontmatter issues. Rejected because the `mcp_version: 7.0.0` drift proves manual review is insufficient.
2. **Split skills into per-tier files immediately**: Move core/advanced/specialist skills to separate files. Rejected for now — file split has concrete breaking costs (Claude Desktop config changes, doc link rerouting) with no clear user-facing benefit at current scale.

## Related Decisions

- ADR-G001: Automation Safety Boundary — guided design protocol extends G001 to ambiguous prompts
